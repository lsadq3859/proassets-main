#!/usr/bin/env python3
"""Initialize the ProAssets SQLite schema without creating default accounts.

Use DATABASE_PATH to point at the same database file used by the web process.
First-admin creation is handled separately by bootstrap_admin.py.
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
_db_path = Path(os.getenv("DATABASE_PATH", "proassets.db"))
DB_PATH = _db_path if _db_path.is_absolute() else BASE_DIR / _db_path
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA busy_timeout = 30000")
        db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        user_columns = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "auth_version" not in user_columns:
            db.execute("ALTER TABLE users ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 0")
        db.commit()
    finally:
        db.close()
    print(f"Database schema initialized at {DB_PATH}.")
    print("No default administrator or test accounts were created.")
    print("Use bootstrap_admin.py with one-time BOOTSTRAP_ADMIN_* variables to create an admin.")


if __name__ == "__main__":
    init_database()
