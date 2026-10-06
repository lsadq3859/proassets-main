#!/usr/bin/env python3
"""Create the first ProAssets admin from secret environment variables.

Required environment variables:
  BOOTSTRAP_ADMIN_USERNAME
  BOOTSTRAP_ADMIN_EMAIL
  BOOTSTRAP_ADMIN_PASSWORD

The operation is intentionally one-time and idempotent: if any admin already
exists, it exits successfully without changing users or passwords.
"""

import os
import re
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "proassets.db"))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    username = required("BOOTSTRAP_ADMIN_USERNAME")
    email = required("BOOTSTRAP_ADMIN_EMAIL").lower()
    password = required("BOOTSTRAP_ADMIN_PASSWORD")

    if len(username) < 3 or len(username) > 50:
        raise SystemExit("BOOTSTRAP_ADMIN_USERNAME must be 3-50 characters")
    if not EMAIL_RE.match(email):
        raise SystemExit("BOOTSTRAP_ADMIN_EMAIL is not a valid email address")
    if len(password) < 12:
        raise SystemExit("BOOTSTRAP_ADMIN_PASSWORD must be at least 12 characters")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        # Do not change an existing admin or silently elevate an ordinary user.
        if db.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
            print("An admin already exists; no changes made.")
            return 0

        conflict = db.execute(
            "SELECT username, email, role FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if conflict:
            raise SystemExit(
                "Username or email already belongs to a non-admin account; "
                "choose new bootstrap values."
            )

        db.execute(
            """INSERT INTO users
               (username, email, password_hash, first_name, last_name, role,
                is_active, is_verified)
               VALUES (?, ?, ?, ?, ?, 'admin', 1, 1)""",
            (username, email, generate_password_hash(password), "", ""),
        )
        db.commit()
        print(f"Admin created successfully for {email}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except sqlite3.Error as exc:
        print(f"Database error: {exc}", file=sys.stderr)
        raise SystemExit(1)
