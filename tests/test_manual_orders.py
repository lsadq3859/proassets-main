import os
import re
import shutil
import sqlite3
import struct
import tempfile
import zlib
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

TEST_ROOT = tempfile.mkdtemp(prefix="proassets-tests-")
os.environ["DATABASE_PATH"] = str(Path(TEST_ROOT) / "test.db")
os.environ["UPLOAD_FOLDER"] = str(Path(TEST_ROOT) / "uploads")

from app import create_app  # noqa: E402

DB_PATH = Path(os.environ["DATABASE_PATH"])
UPLOAD_PATH = Path(os.environ["UPLOAD_FOLDER"])


class ManualOrderFlowTests(unittest.TestCase):
    def setUp(self):
        if DB_PATH.exists():
            DB_PATH.unlink()
        shutil.rmtree(UPLOAD_PATH, ignore_errors=True)
        self.app = create_app("testing")
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-session-secret-for-proassets",
            CONTACT_EMAIL="support@example.test",
            CONTACT_PHONE="+9999999999",
        )
        self.client = self.app.test_client()
        self._seed_users_and_products()

    def tearDown(self):
        self.client = None

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ROOT, ignore_errors=True)

    def _db(self):
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        return db

    def _seed_users_and_products(self):
        self.upload_file = UPLOAD_PATH / "premium-demo.txt"
        self.upload_file.write_text("downloadable test content", encoding="utf-8")
        db = self._db()
        db.execute(
            "INSERT INTO users (username,email,password_hash,role,is_active) VALUES (?,?,?,?,1)",
            ("admin-test", "admin@example.test", generate_password_hash("admin-password-123"), "admin"),
        )
        db.execute(
            "INSERT INTO users (username,email,password_hash,role,is_active) VALUES (?,?,?,?,1)",
            ("creator-test", "creator@example.test", generate_password_hash("creator-password-123"), "creator"),
        )
        db.execute(
            "INSERT INTO users (username,email,password_hash,role,is_active) VALUES (?,?,?,?,1)",
            ("buyer-one", "buyer1@example.test", generate_password_hash("buyer-password-123"), "customer"),
        )
        db.execute(
            "INSERT INTO users (username,email,password_hash,role,is_active) VALUES (?,?,?,?,1)",
            ("buyer-two", "buyer2@example.test", generate_password_hash("buyer-password-456"), "customer"),
        )
        creator_id = db.execute("SELECT id FROM users WHERE username='creator-test'").fetchone()[0]
        db.execute("INSERT INTO wallets (creator_id,balance,total_earnings) VALUES (?,0,0)", (creator_id,))
        db.execute(
            """INSERT INTO products
               (creator_id,category_id,title_en,title_ar,slug,price,currency,product_type,
                file_url,file_size,status)
               VALUES (?,1,'Premium Demo','منتج تجريبي','premium-demo',100,'USD','template',?,?, 'published')""",
            (creator_id, str(self.upload_file), self.upload_file.stat().st_size),
        )
        db.execute(
            """INSERT INTO products
               (creator_id,category_id,title_en,title_ar,slug,price,currency,product_type,
                file_url,file_size,status)
               VALUES (?,1,'Free Demo','منتج مجاني','free-demo',0,'USD','ebook',?,?, 'published')""",
            (creator_id, str(self.upload_file), self.upload_file.stat().st_size),
        )
        db.commit()
        db.close()

    def _csrf(self, response):
        page = response.get_data(as_text=True)
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page)
        if match is None:
            match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', page)
        self.assertIsNotNone(match, "Rendered page should contain a CSRF token")
        return match.group(1)

    def _login(self, client, email, password):
        response = client.get("/login")
        token = self._csrf(response)
        response = client.post(
            "/login",
            json={"email": email, "password": password},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response

    def _add_to_cart(self, client, product_id):
        page = client.get(f"/product/{'premium-demo' if product_id == 1 else 'free-demo'}")
        token = self._csrf(page)
        response = client.post(f"/cart/add/{product_id}", headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return token

    def test_manual_confirmation_fulfills_once_and_download_is_authorized(self):
        buyer = self.app.test_client()
        self._login(buyer, "buyer1@example.test", "buyer-password-123")
        self._add_to_cart(buyer, 1)
        checkout_page = buyer.get("/checkout")
        token = self._csrf(checkout_page)

        rejected_without_csrf = buyer.post("/checkout", json={})
        self.assertEqual(rejected_without_csrf.status_code, 400)

        response = buyer.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["pending_orders_created"], 1)

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        orders_page = admin.get("/admin/orders")
        admin_token = self._csrf(orders_page)
        self.assertIn(b"Premium Demo", orders_page.data)

        db = self._db()
        order_id = db.execute("SELECT id FROM orders WHERE payment_status='pending'").fetchone()[0]
        db.close()

        missing_token = admin.post(f"/admin/order/{order_id}/confirm", json={})
        self.assertEqual(missing_token.status_code, 400)

        confirmed = admin.post(
            f"/admin/order/{order_id}/confirm",
            json={"transaction_id": "manual-receipt-001"},
            headers={"X-CSRF-Token": admin_token},
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.get_data(as_text=True))
        self.assertEqual(confirmed.get_json()["status"], "success")

        # Repeating the action must never credit the seller or increment sales twice.
        repeated = admin.post(
            f"/admin/order/{order_id}/confirm",
            json={},
            headers={"X-CSRF-Token": admin_token},
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertTrue(repeated.get_json()["already_completed"])

        db = self._db()
        order = db.execute("SELECT payment_status,transaction_id FROM orders WHERE id=?", (order_id,)).fetchone()
        library_count = db.execute("SELECT COUNT(*) FROM user_library WHERE customer_id=3 AND product_id=1").fetchone()[0]
        wallet = db.execute("SELECT balance,total_earnings FROM wallets WHERE creator_id=2").fetchone()
        sales_count = db.execute("SELECT sales_count FROM products WHERE id=1").fetchone()[0]
        db.close()
        self.assertEqual(order["payment_status"], "completed")
        self.assertEqual(order["transaction_id"], "manual-receipt-001")
        self.assertEqual(library_count, 1)
        self.assertEqual(float(wallet["balance"]), 80.0)
        self.assertEqual(float(wallet["total_earnings"]), 80.0)
        self.assertEqual(sales_count, 1)

        download = buyer.get("/download/1")
        self.assertEqual(download.status_code, 200)
        self.assertIn(b"downloadable test content", download.data)
        download.close()

        unauthorized = self.app.test_client().get("/download/1")
        self.assertIn(unauthorized.status_code, (302, 403))

        other_buyer = self.app.test_client()
        self._login(other_buyer, "buyer2@example.test", "buyer-password-456")
        self.assertEqual(other_buyer.get("/download/1").status_code, 403)

        # Product titles are escaped as HTML data, never interpolated into inline JavaScript.
        malicious_title = '</div><img src=x onerror=alert(1)>'
        db = self._db()
        db.execute("UPDATE products SET title_en=? WHERE id=1", (malicious_title,))
        db.commit()
        db.close()
        library_page = buyer.get("/library")
        self.assertEqual(library_page.status_code, 200)
        self.assertNotIn(malicious_title.encode(), library_page.data)
        self.assertNotIn(b'onclick="downloadProduct', library_page.data)
        self.assertIn(b'href="/download/1"', library_page.data)

    def test_rejected_payment_does_not_grant_library_access(self):
        buyer = self.app.test_client()
        self._login(buyer, "buyer2@example.test", "buyer-password-456")
        self._add_to_cart(buyer, 1)
        token = self._csrf(buyer.get("/checkout"))
        response = buyer.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 201)

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        admin_token = self._csrf(admin.get("/admin/orders"))
        db = self._db()
        order_id = db.execute("SELECT id FROM orders WHERE customer_id=4 AND product_id=1").fetchone()[0]
        db.close()
        response = admin.post(
            f"/admin/order/{order_id}/reject",
            json={},
            headers={"X-CSRF-Token": admin_token},
        )
        self.assertEqual(response.status_code, 200)

        db = self._db()
        status = db.execute("SELECT payment_status FROM orders WHERE id=?", (order_id,)).fetchone()[0]
        library_count = db.execute("SELECT COUNT(*) FROM user_library WHERE customer_id=4 AND product_id=1").fetchone()[0]
        db.close()
        self.assertEqual(status, "rejected")
        self.assertEqual(library_count, 0)

    def test_free_product_is_fulfilled_without_manual_payment(self):
        buyer = self.app.test_client()
        self._login(buyer, "buyer1@example.test", "buyer-password-123")
        self._add_to_cart(buyer, 2)
        token = self._csrf(buyer.get("/checkout"))
        response = buyer.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["free_orders_completed"], 1)
        db = self._db()
        status = db.execute("SELECT payment_status FROM orders WHERE product_id=2").fetchone()[0]
        library_count = db.execute("SELECT COUNT(*) FROM user_library WHERE customer_id=3 AND product_id=2").fetchone()[0]
        db.close()
        self.assertEqual(status, "completed")
        self.assertEqual(library_count, 1)

    def test_paid_checkout_post_is_blocked_without_support_contact(self):
        locked_app = create_app("testing")
        locked_app.config.update(
            TESTING=True,
            SECRET_KEY="test-session-secret-for-proassets",
            CONTACT_EMAIL="",
            CONTACT_PHONE="",
        )
        buyer = locked_app.test_client()
        self._login(buyer, "buyer1@example.test", "buyer-password-123")
        self._add_to_cart(buyer, 1)
        token = self._csrf(buyer.get("/checkout"))
        response = buyer.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self.assertIn("Configure a support", response.get_json()["message"])

    def test_free_checkout_still_works_without_support_contact(self):
        locked_app = create_app("testing")
        locked_app.config.update(
            TESTING=True,
            SECRET_KEY="test-session-secret-for-proassets",
            CONTACT_EMAIL="",
            CONTACT_PHONE="",
        )
        buyer = locked_app.test_client()
        self._login(buyer, "buyer1@example.test", "buyer-password-123")
        self._add_to_cart(buyer, 2)
        token = self._csrf(buyer.get("/checkout"))
        response = buyer.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["free_orders_completed"], 1)

    def test_creator_cannot_purchase_own_product(self):
        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        self._add_to_cart(creator, 1)
        token = self._csrf(creator.get("/checkout"))
        response = creator.post("/checkout", json={}, headers={"X-CSRF-Token": token})
        self.assertEqual(response.status_code, 400)
        self.assertIn("own products", response.get_json()["message"])

    def test_product_upload_validates_fields_and_keeps_file_private(self):
        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        token = self._csrf(creator.get("/creator/upload"))
        fields = {
            "title_en": "Secure Test Asset",
            "title_ar": "أصل تجريبي آمن",
            "category_id": "1",
            "price": "24.50",
            "description_en": "A small test package.",
            "description_ar": "حزمة اختبار صغيرة.",
            "product_type": "template",
            "file": (BytesIO(b"private upload"), "test-asset.zip"),
        }
        response = creator.post(
            "/creator/upload",
            data=fields,
            headers={"X-CSRF-Token": token},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        db = self._db()
        product = db.execute("SELECT status,file_url,slug FROM products WHERE title_en='Secure Test Asset'").fetchone()
        db.close()
        self.assertIsNotNone(product)
        self.assertEqual(product["status"], "pending")
        self.assertTrue(product["file_url"].startswith(str(UPLOAD_PATH) + os.sep))
        self.assertTrue(Path(product["file_url"]).is_file())
        self.assertNotIn("Secure Test Asset", product["slug"])

        invalid_fields = dict(fields)
        invalid_fields["price"] = "-5"
        invalid_fields["file"] = (BytesIO(b"should not save"), "negative-price.zip")
        invalid = creator.post(
            "/creator/upload",
            data=invalid_fields,
            headers={"X-CSRF-Token": token},
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(any(UPLOAD_PATH.glob("*negative-price.zip")))

    def test_admin_product_review_transitions_only_pending_listings(self):
        db = self._db()
        db.executemany(
            """INSERT INTO products (creator_id,category_id,title_en,title_ar,slug,price,currency,product_type,status)
               VALUES (2,1,?,?,?,5,'USD','template','pending')""",
            [("Review Approve", "مراجعة موافقة", "review-approve"), ("Review Reject", "مراجعة رفض", "review-reject")],
        )
        db.commit()
        approve_id = db.execute("SELECT id FROM products WHERE slug='review-approve'").fetchone()[0]
        reject_id = db.execute("SELECT id FROM products WHERE slug='review-reject'").fetchone()[0]
        db.close()

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        csrf = self._csrf(admin.get("/admin/products?status=pending"))
        self.assertEqual(admin.post(f"/admin/product/{approve_id}/approve").status_code, 400)
        approved = admin.post(f"/admin/product/{approve_id}/approve", headers={"X-CSRF-Token": csrf})
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(admin.post(f"/admin/product/{approve_id}/approve", headers={"X-CSRF-Token": csrf}).status_code, 409)
        self.assertEqual(admin.post(f"/admin/product/{approve_id}/reject", headers={"X-CSRF-Token": csrf}).status_code, 409)
        self.assertEqual(admin.post(f"/admin/product/99999/approve", headers={"X-CSRF-Token": csrf}).status_code, 404)
        rejected = admin.post(f"/admin/product/{reject_id}/reject", headers={"X-CSRF-Token": csrf})
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(admin.post(f"/admin/product/{reject_id}/reject", headers={"X-CSRF-Token": csrf}).status_code, 409)
        db = self._db()
        statuses = {row["slug"]: row["status"] for row in db.execute("SELECT slug,status FROM products WHERE id IN (?,?)", (approve_id, reject_id)).fetchall()}
        db.close()
        self.assertEqual(statuses, {"review-approve": "published", "review-reject": "rejected"})

    def test_public_customer_creator_and_admin_pages_render(self):
        public_paths = [
            "/", "/products", "/about", "/contact", "/privacy", "/terms",
            "/login", "/register", "/cart", "/product/premium-demo",
        ]
        for path in public_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, f"{path}: {response.get_data(as_text=True)[:300]}")
                self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
                self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        product_detail = self.client.get("/product/premium-demo")
        self.assertNotIn(b"None None", product_detail.data)
        self.assertIn(b"creator-test", product_detail.data)

        customer = self.app.test_client()
        self._login(customer, "buyer1@example.test", "buyer-password-123")
        for path in ("/dashboard", "/library", "/account", "/checkout"):
            with self.subTest(path=path):
                self.assertEqual(customer.get(path).status_code, 200)

        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        for path in ("/creator/dashboard", "/creator/products", "/creator/earnings", "/creator/upload", "/creator/product/1/edit"):
            with self.subTest(path=path):
                self.assertEqual(creator.get(path).status_code, 200)

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        for path in ("/admin", "/admin/orders", "/admin/messages", "/admin/products", "/admin/users", "/admin/withdrawals"):
            with self.subTest(path=path):
                self.assertEqual(admin.get(path).status_code, 200)

        for name in self.app.jinja_env.list_templates():
            with self.subTest(template=name):
                self.app.jinja_env.get_template(name)

        token = self._csrf(customer.get("/account"))
        self.assertEqual(customer.get("/logout").status_code, 405)
        self.assertEqual(customer.post("/logout").status_code, 400)
        self.assertEqual(customer.post("/logout", data={"csrf_token": token}).status_code, 302)
        self.assertEqual(customer.get("/library").status_code, 302)


    def test_support_inbox_paginates_and_clamps_requested_page(self):
        db = self._db()
        db.executemany(
            "INSERT INTO messages (sender_id,subject,message) VALUES (NULL,?,?)",
            [(f"Support message {index}", f"Body {index}") for index in range(51)],
        )
        db.commit()
        db.close()

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        first = admin.get("/admin/messages?status=all&page=1")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data.count(b'class="message"'), 50)
        self.assertIn(b"Page 1 of 2", first.data)
        second = admin.get("/admin/messages?status=all&page=2")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data.count(b'class="message"'), 1)
        self.assertIn(b"Page 2 of 2", second.data)
        clamped = admin.get("/admin/messages?status=all&page=999")
        self.assertEqual(clamped.status_code, 200)
        self.assertIn(b"Page 2 of 2", clamped.data)

    def test_registration_validation_normalization_and_creator_wallet_creation(self):
        visitor = self.app.test_client()
        page = visitor.get("/register")
        csrf = self._csrf(page)
        missing_csrf = visitor.post("/register", json={
            "username": "creator-three", "email": "creator3@example.test", "password": "valid-password-123", "user_type": "creator"
        })
        self.assertEqual(missing_csrf.status_code, 400)

        base = {"username": "Creator.Three", "email": "Creator3@Example.Test", "password": "valid-password-123", "user_type": "creator"}
        for invalid in (
            {**base, "username": "x"},
            {**base, "email": "not-an-email"},
            {**base, "password": "short"},
            {**base, "user_type": "admin"},
            {**base, "first_name": ["not", "text"]},
        ):
            response = visitor.post("/register", json=invalid, headers={"X-CSRF-Token": csrf})
            self.assertEqual(response.status_code, 400, response.get_data(as_text=True))

        created = visitor.post("/register", json=base, headers={"X-CSRF-Token": csrf})
        self.assertEqual(created.status_code, 201, created.get_data(as_text=True))
        self.assertEqual(visitor.get("/creator/dashboard").status_code, 302)  # Registration does not silently sign users in.

        db = self._db()
        user = db.execute("SELECT id,username,email,role FROM users WHERE lower(username)=lower(?)", (base["username"],)).fetchone()
        wallet = db.execute("SELECT creator_id,balance,total_earnings,currency FROM wallets WHERE creator_id=?", (user["id"],)).fetchone()
        db.close()
        self.assertEqual(user["email"], "creator3@example.test")
        self.assertEqual(user["role"], "creator")
        self.assertEqual(wallet["creator_id"], user["id"])
        self.assertEqual(float(wallet["balance"]), 0.0)
        self.assertEqual(wallet["currency"], "USD")

        duplicate_name = visitor.post(
            "/register", json={**base, "username": "creator.three", "email": "another@example.test"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(duplicate_name.status_code, 400)
        duplicate_email = visitor.post(
            "/register", json={**base, "username": "creator-four"}, headers={"X-CSRF-Token": csrf}
        )
        self.assertEqual(duplicate_email.status_code, 400)

    def test_creator_wallet_currency_guard_prevents_mixed_currency_ledger_credits(self):
        db = self._db()
        db.execute(
            "INSERT INTO orders (customer_id,product_id,price,currency,payment_status) VALUES (3,1,15,'EUR','pending')"
        )
        db.commit()
        order_id = db.execute("SELECT id FROM orders WHERE currency='EUR'").fetchone()[0]
        db.close()

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        csrf = self._csrf(admin.get("/admin/orders"))
        response = admin.post(
            f"/admin/order/{order_id}/confirm", json={"transaction_id": "manual-eur"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("currency does not match", response.get_json()["message"])

        db = self._db()
        order_status = db.execute("SELECT payment_status FROM orders WHERE id=?", (order_id,)).fetchone()[0]
        wallet = db.execute("SELECT balance,total_earnings FROM wallets WHERE creator_id=2").fetchone()
        library_count = db.execute("SELECT COUNT(*) FROM user_library WHERE customer_id=3 AND product_id=1").fetchone()[0]
        sales = db.execute("SELECT sales_count FROM products WHERE id=1").fetchone()[0]
        db.close()
        self.assertEqual(order_status, "pending")
        self.assertEqual(float(wallet["balance"]), 0.0)
        self.assertEqual(float(wallet["total_earnings"]), 0.0)
        self.assertEqual(library_count, 0)
        self.assertEqual(sales, 0)

    def test_withdrawal_ledger_displays_currency_and_mutations_remain_disabled(self):
        db = self._db()
        db.executemany(
            "INSERT INTO withdrawals (creator_id,amount,currency,withdrawal_method,status) VALUES (2,?,?,?,'completed')",
            [(17.25, "USD", "bank_transfer"), (9.50, "EUR", "wise")],
        )
        db.execute(
            "INSERT INTO withdrawals (creator_id,amount,currency,withdrawal_method,status) VALUES (2,4.00,'USD','wise','pending')"
        )
        db.commit()
        pending_id = db.execute("SELECT id FROM withdrawals WHERE status='pending'").fetchone()[0]
        before_count = db.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        db.close()

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        page = admin.get("/admin/withdrawals")
        self.assertIn(b"USD 17.25", page.data)
        self.assertIn(b"EUR 9.50", page.data)
        self.assertIn(b"no approve, reject, or transfer action", page.data)
        csrf = self._csrf(page)
        blocked_process = admin.post(
            f"/admin/withdrawal/{pending_id}/process", json={}, headers={"X-CSRF-Token": csrf}
        )
        self.assertEqual(blocked_process.status_code, 503)

        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        creator_csrf = self._csrf(creator.get("/account"))
        blocked_request = creator.post("/creator/withdraw", json={}, headers={"X-CSRF-Token": creator_csrf})
        self.assertEqual(blocked_request.status_code, 503)

        db = self._db()
        status = db.execute("SELECT status FROM withdrawals WHERE id=?", (pending_id,)).fetchone()[0]
        count = db.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        db.close()
        self.assertEqual(status, "pending")
        self.assertEqual(count, before_count)

    def _png_1x1(self):
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
            + chunk(b"IEND", b"")
        )

    def test_contact_inbox_validates_escapes_and_closes_messages(self):
        guest = self.app.test_client()
        csrf = self._csrf(guest.get("/contact"))
        self.assertEqual(guest.post("/contact", json={"subject": "Missing token", "message": "No token"}).status_code, 400)
        self.assertEqual(
            guest.post("/contact", json=["not", "an", "object"], headers={"X-CSRF-Token": csrf}).status_code,
            400,
        )
        self.assertEqual(
            guest.post(
                "/contact", json={"subject": "S" * 161, "message": "Too long"},
                headers={"X-CSRF-Token": csrf},
            ).status_code,
            400,
        )
        sent = guest.post(
            "/contact",
            json={"subject": "<script>alert(1)</script>", "message": "<img src=x onerror=alert(2)>"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(sent.status_code, 201, sent.get_data(as_text=True))

        db = self._db()
        message_id = db.execute("SELECT id FROM messages ORDER BY id DESC LIMIT 1").fetchone()[0]
        db.close()
        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        inbox = admin.get("/admin/messages")
        self.assertEqual(inbox.status_code, 200)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", inbox.data)
        self.assertIn(b"&lt;img src=x onerror=alert(2)&gt;", inbox.data)
        self.assertEqual(admin.post(f"/admin/message/{message_id}/close", json={}).status_code, 400)
        admin_csrf = self._csrf(inbox)
        closed = admin.post(
            f"/admin/message/{message_id}/close", json={}, headers={"X-CSRF-Token": admin_csrf}
        )
        self.assertEqual(closed.status_code, 200, closed.get_data(as_text=True))
        self.assertEqual(admin.post(
            f"/admin/message/{message_id}/close", json={}, headers={"X-CSRF-Token": admin_csrf}
        ).status_code, 409)
        self.assertNotIn(b"<script>alert(1)</script>", admin.get("/admin/messages?status=open").data)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", admin.get("/admin/messages?status=closed").data)
        self.assertEqual(admin.post(
            "/admin/message/99999/close", json={}, headers={"X-CSRF-Token": admin_csrf}
        ).status_code, 404)

        customer = self.app.test_client()
        self._login(customer, "buyer1@example.test", "buyer-password-123")
        self.assertEqual(customer.get("/admin/messages").status_code, 403)

    def test_account_profile_password_preferences_avatar_and_anonymized_deletion(self):
        customer = self.app.test_client()
        self._login(customer, "buyer1@example.test", "buyer-password-123")
        other_session = self.app.test_client()
        self._login(other_session, "buyer1@example.test", "buyer-password-123")
        account_page = customer.get("/account")
        csrf = self._csrf(account_page)

        invalid_profile = customer.post(
            "/account/update", json={"first_name": ["not", "text"]}, headers={"X-CSRF-Token": csrf}
        )
        self.assertEqual(invalid_profile.status_code, 400)
        updated = customer.post(
            "/account/update", json={"first_name": "Buyer", "last_name": "One", "bio": "Updated bio"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(updated.status_code, 200)

        invalid_preferences = customer.post(
            "/account/preferences", json={"currency": "XYZ"}, headers={"X-CSRF-Token": csrf}
        )
        self.assertEqual(invalid_preferences.status_code, 400)
        saved_preferences = customer.post(
            "/account/preferences",
            json={"email_notifications": True, "marketing_emails": False, "order_updates": True, "currency": "EUR"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(saved_preferences.status_code, 200)
        db = self._db()
        preferences = db.execute("SELECT * FROM user_preferences WHERE user_id=3").fetchone()
        db.close()
        self.assertEqual((preferences["email_notifications"], preferences["marketing_emails"], preferences["order_updates"], preferences["currency"]), (1, 0, 1, "EUR"))

        invalid_avatar = customer.post(
            "/account/avatar", data={"avatar": (BytesIO(b"<svg onload=alert(1) />"), "bad.svg")},
            headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
        )
        self.assertEqual(invalid_avatar.status_code, 400)
        invalid_avatar.close()
        with patch("app.MAX_AVATAR_UPLOAD_BYTES", 64):
            too_large = customer.post(
                "/account/avatar", data={"avatar": (BytesIO(b"x" * 65), "large.png")},
                headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
            )
            oversized_request = customer.post(
                "/account/avatar", data={"avatar": (BytesIO(b"x" * 70000), "request-too-large.png")},
                headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
            )
        self.assertEqual(too_large.status_code, 413)
        too_large.close()
        self.assertEqual(oversized_request.status_code, 413)
        oversized_request.close()
        uploaded = customer.post(
            "/account/avatar", data={"avatar": (BytesIO(self._png_1x1()), "avatar.png")},
            headers={"X-CSRF-Token": csrf}, content_type="multipart/form-data",
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.get_data(as_text=True))
        uploaded.close()
        avatar = customer.get("/account/avatar")
        self.assertEqual(avatar.status_code, 200)
        self.assertEqual(avatar.mimetype, "image/png")
        self.assertEqual(avatar.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn("private", avatar.headers.get("Cache-Control", ""))
        avatar.close()
        db = self._db()
        avatar_name = db.execute("SELECT profile_image FROM users WHERE id=3").fetchone()[0]
        db.close()
        avatar_path = UPLOAD_PATH / "avatars" / avatar_name
        self.assertTrue(avatar_path.is_file())

        wrong_password = customer.post(
            "/account/security",
            json={"current_password": "wrong-password", "new_password": "new-password-123", "confirm_password": "new-password-123"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(wrong_password.status_code, 403)
        mismatch = customer.post(
            "/account/security",
            json={"current_password": "buyer-password-123", "new_password": "new-password-123", "confirm_password": "different-password"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(mismatch.status_code, 400)
        changed = customer.post(
            "/account/security",
            json={"current_password": "buyer-password-123", "new_password": "new-password-123", "confirm_password": "new-password-123"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertIn("sign in again", changed.get_json()["message"])
        self.assertEqual(customer.get("/account").status_code, 302)
        # The auth-version change invalidates every older signed cookie, not just the current browser.
        self.assertEqual(other_session.get("/account").status_code, 302)
        old_login_page = customer.get("/login")
        old_login = customer.post(
            "/login", json={"email": "buyer1@example.test", "password": "buyer-password-123"},
            headers={"X-CSRF-Token": self._csrf(old_login_page)},
        )
        self.assertEqual(old_login.status_code, 401)
        self._login(customer, "buyer1@example.test", "new-password-123")

        db = self._db()
        db.execute(
            "INSERT INTO orders (customer_id,product_id,price,currency,payment_status) VALUES (3,1,100,'USD','completed')"
        )
        db.execute("INSERT INTO user_library (customer_id,product_id) VALUES (3,1)")
        db.commit()
        db.close()
        delete_page = customer.get("/account")
        delete_csrf = self._csrf(delete_page)
        failed_delete = customer.post(
            "/account/delete", json={"current_password": "wrong-password", "confirmation": "DELETE"},
            headers={"X-CSRF-Token": delete_csrf},
        )
        self.assertEqual(failed_delete.status_code, 403)
        deleted = customer.post(
            "/account/delete", json={"current_password": "new-password-123", "confirmation": "DELETE"},
            headers={"X-CSRF-Token": delete_csrf},
        )
        self.assertEqual(deleted.status_code, 200, deleted.get_data(as_text=True))
        self.assertFalse(avatar_path.exists())
        self.assertEqual(customer.get("/account").status_code, 302)
        db = self._db()
        deleted_user = db.execute("SELECT username,email,first_name,last_name,bio,is_active FROM users WHERE id=3").fetchone()
        order_count = db.execute("SELECT COUNT(*) FROM orders WHERE customer_id=3").fetchone()[0]
        library_count = db.execute("SELECT COUNT(*) FROM user_library WHERE customer_id=3").fetchone()[0]
        db.close()
        self.assertTrue(deleted_user["username"].startswith("deleted-user-3-"))
        self.assertTrue(deleted_user["email"].endswith("@invalid.local"))
        self.assertIsNone(deleted_user["first_name"])
        self.assertIsNone(deleted_user["last_name"])
        self.assertIsNone(deleted_user["bio"])
        self.assertEqual(deleted_user["is_active"], 0)
        self.assertEqual(order_count, 1)  # Financial history remains for audit.
        self.assertEqual(library_count, 0)
        login_after_delete = self.app.test_client()
        login_page = login_after_delete.get("/login")
        login_response = login_after_delete.post(
            "/login", json={"email": "buyer1@example.test", "password": "new-password-123"},
            headers={"X-CSRF-Token": self._csrf(login_page)},
        )
        self.assertEqual(login_response.status_code, 401)

    def test_account_deletion_guards_pending_orders_creator_assets_and_admins(self):
        buyer = self.app.test_client()
        self._login(buyer, "buyer2@example.test", "buyer-password-456")
        token = self._csrf(buyer.get("/account"))
        db = self._db()
        db.execute(
            "INSERT INTO orders (customer_id,product_id,price,currency,payment_status) VALUES (4,1,100,'USD','pending')"
        )
        db.commit()
        db.close()
        pending = buyer.post(
            "/account/delete", json={"current_password": "buyer-password-456", "confirmation": "DELETE"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(pending.status_code, 409)

        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        creator_token = self._csrf(creator.get("/account"))
        creator_delete = creator.post(
            "/account/delete", json={"current_password": "creator-password-123", "confirmation": "DELETE"},
            headers={"X-CSRF-Token": creator_token},
        )
        self.assertEqual(creator_delete.status_code, 409)

        admin = self.app.test_client()
        self._login(admin, "admin@example.test", "admin-password-123")
        admin_token = self._csrf(admin.get("/account"))
        admin_delete = admin.post(
            "/account/delete", json={"current_password": "admin-password-123", "confirmation": "DELETE"},
            headers={"X-CSRF-Token": admin_token},
        )
        self.assertEqual(admin_delete.status_code, 403)

    def test_creator_can_edit_own_listing_and_delete_only_without_history(self):
        db = self._db()
        db.execute(
            "INSERT INTO orders (customer_id,product_id,price,currency,payment_status) VALUES (3,1,100,'USD','completed')"
        )
        db.execute("INSERT INTO user_library (customer_id,product_id) VALUES (3,1)")
        db.execute(
            """INSERT INTO products
               (creator_id,category_id,title_en,title_ar,slug,price,currency,product_type,file_url,file_size,status)
               VALUES (2,1,'Disposable Test','منتج قابل للحذف','disposable-test',5,'USD','template',?,24,'draft')""",
            (str(self.upload_file),),
        )
        db.execute(
            "INSERT INTO users (username,email,password_hash,role,is_active) VALUES (?,?,?,?,1)",
            ("creator-two", "creator2@example.test", generate_password_hash("creator2-password-123"), "creator"),
        )
        db.commit()
        disposable_id = db.execute("SELECT id FROM products WHERE slug='disposable-test'").fetchone()[0]
        db.close()

        creator = self.app.test_client()
        self._login(creator, "creator@example.test", "creator-password-123")
        edit_page = creator.get("/creator/product/1/edit")
        self.assertEqual(edit_page.status_code, 200)
        token = self._csrf(edit_page)
        edit = creator.post(
            "/creator/product/1/edit",
            data={
                "title_en": "Revised Premium Demo", "title_ar": "منتج تجريبي محدث",
                "description_en": "Updated description", "description_ar": "وصف محدث",
                "category_id": "1", "price": "120.50", "product_type": "template",
                "csrf_token": token,
            },
            follow_redirects=True,
        )
        self.assertEqual(edit.status_code, 200)
        self.assertIn(b"pending administrator review", edit.data)
        db = self._db()
        edited = db.execute("SELECT status,title_en,price,file_url FROM products WHERE id=1").fetchone()
        db.close()
        self.assertEqual(edited["status"], "pending")
        self.assertEqual(edited["title_en"], "Revised Premium Demo")
        self.assertEqual(float(edited["price"]), 120.5)
        self.assertEqual(edited["file_url"], str(self.upload_file))

        buyer = self.app.test_client()
        self._login(buyer, "buyer1@example.test", "buyer-password-123")
        self.assertEqual(buyer.get("/product/premium-demo").status_code, 404)
        download = buyer.get("/download/1")
        self.assertEqual(download.status_code, 200)
        download.close()

        creator_page = creator.get("/creator/products")
        self.assertIn(b"History protected", creator_page.data)
        delete_response = creator.post(
            "/creator/product/1/delete", headers={"X-CSRF-Token": self._csrf(creator_page)}
        )
        self.assertEqual(delete_response.status_code, 409)

        other_creator = self.app.test_client()
        self._login(other_creator, "creator2@example.test", "creator2-password-123")
        self.assertEqual(other_creator.get("/creator/product/1/edit").status_code, 404)
        other_page = other_creator.get("/creator/products")
        self.assertEqual(other_creator.post(
            f"/creator/product/{disposable_id}/delete", headers={"X-CSRF-Token": self._csrf(other_page)}
        ).status_code, 404)

        missing_csrf = creator.post(f"/creator/product/{disposable_id}/delete")
        self.assertEqual(missing_csrf.status_code, 400)
        delete_token = self._csrf(creator_page)
        removed = creator.post(
            f"/creator/product/{disposable_id}/delete", headers={"X-CSRF-Token": delete_token}
        )
        self.assertEqual(removed.status_code, 200, removed.get_data(as_text=True))
        db = self._db()
        self.assertIsNone(db.execute("SELECT id FROM products WHERE id=?", (disposable_id,)).fetchone())
        db.close()
        self.assertTrue(self.upload_file.is_file())  # Shared fixture file is not unlinked.

    def test_cart_add_is_idempotent_totals_respect_currency_and_login_returns_to_checkout(self):
        db = self._db()
        db.execute(
            """INSERT INTO products
               (creator_id,category_id,title_en,title_ar,slug,price,currency,product_type,file_url,file_size,status)
               VALUES (2,1,'Euro Asset','أصل باليورو','euro-asset',12.5,'EUR','template',?,24,'published')""",
            (str(self.upload_file),),
        )
        db.commit()
        euro_id = db.execute("SELECT id FROM products WHERE slug='euro-asset'").fetchone()[0]
        db.close()

        visitor = self.app.test_client()
        product_page = visitor.get("/product/premium-demo")
        token = self._csrf(product_page)
        first_add = visitor.post("/cart/add/1", headers={"X-CSRF-Token": token})
        duplicate_add = visitor.post("/cart/add/1", headers={"X-CSRF-Token": token})
        euro_add = visitor.post(f"/cart/add/{euro_id}", headers={"X-CSRF-Token": token})
        self.assertEqual(first_add.status_code, 200)
        self.assertEqual(duplicate_add.status_code, 200)
        self.assertTrue(duplicate_add.get_json()["already_in_cart"])
        self.assertEqual(euro_add.status_code, 200)
        cart_page = visitor.get("/cart")
        self.assertIn(b"USD 100.00", cart_page.data)
        self.assertIn(b"EUR 12.50", cart_page.data)

        checkout_redirect = visitor.get("/checkout")
        self.assertEqual(checkout_redirect.status_code, 302)
        self.assertIn("next=", checkout_redirect.headers["Location"])
        login_page = visitor.get(checkout_redirect.headers["Location"])
        self.assertIn(b'name="next" value="/checkout"', login_page.data)
        login_token = self._csrf(login_page)
        login = visitor.post(
            "/login", json={"email": "buyer1@example.test", "password": "buyer-password-123", "next": "/checkout"},
            headers={"X-CSRF-Token": login_token},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()["redirect"], "/checkout")
        checkout_page = visitor.get(login.get_json()["redirect"])
        self.assertEqual(checkout_page.status_code, 200)
        self.assertIn(b"Premium Demo", checkout_page.data)
        self.assertIn(b"Euro Asset", checkout_page.data)
        self.assertIn(b"support@example.test", checkout_page.data)
        self.assertNotIn(b'type="button" disabled', checkout_page.data)

        locked_app = create_app("testing")
        locked_app.config.update(
            TESTING=True,
            SECRET_KEY="test-session-secret-for-proassets",
            CONTACT_EMAIL="",
            CONTACT_PHONE="",
        )
        locked_client = locked_app.test_client()
        self._login(locked_client, "buyer1@example.test", "buyer-password-123")
        product_page = locked_client.get("/product/premium-demo")
        locked_token = self._csrf(product_page)
        locked_client.post("/cart/add/1", headers={"X-CSRF-Token": locked_token})
        locked_page = locked_client.get("/checkout")
        self.assertIn(b"Paid orders are unavailable because this deployment has no configured support contact", locked_page.data)
        self.assertIn(b'id="submitOrder" type="button" disabled', locked_page.data)

        external_client = self.app.test_client()
        external_login_page = external_client.get("/login")
        external_token = self._csrf(external_login_page)
        external = external_client.post(
            "/login", json={"email": "buyer1@example.test", "password": "buyer-password-123", "next": "https://evil.example"},
            headers={"X-CSRF-Token": external_token},
        )
        self.assertEqual(external.status_code, 200)
        self.assertEqual(external.get_json()["redirect"], "/dashboard")
        detail_js = Path("templates/product_detail.html").read_text(encoding="utf-8")
        self.assertIn("async function buyNow", detail_js)
        self.assertIn("await addToCart(productId, false)", detail_js)
        self.assertNotIn("setTimeout(() => {\\n                window.location.href = '/checkout'", detail_js)


if __name__ == "__main__":
    unittest.main()
