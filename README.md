# ProAssets

Flask marketplace for digital products. **Paid checkout is manual only**: the app creates a pending purchase request; it does not charge a card or PayPal account. An administrator must verify an independently arranged payment before granting paid access. Creator balances are ledger records only; payouts are disabled.

## Local setup

```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
python run.py
```

`setup.sh` initializes the SQLite schema but does not seed fixed administrator or test credentials. Customers and creators can register through the application. Review `.env` before running locally. Paid checkout is unavailable in a local deployment without a configured support contact; free products can still be fulfilled.

## Create the first administrator safely

Set these values temporarily in the local `.env` or the Render service environment:

- `BOOTSTRAP_ADMIN_USERNAME` — 3–50 characters
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD` — at least 12 characters; use a unique password

Run `python bootstrap_admin.py` once. The script will not elevate an existing account or change an existing administrator. Remove the three `BOOTSTRAP_ADMIN_*` values immediately afterwards.

## Render production configuration

Configure the following environment values before deploying:

```text
APP_ENV=production
SECRET_KEY=<unique random secret, at least 32 characters>
DATABASE_PATH=/var/data/proassets.db
UPLOAD_FOLDER=/var/data/uploads
CONTACT_EMAIL=<monitored support email>
# Or configure CONTACT_PHONE instead of CONTACT_EMAIL
```

Generate a random secret with `python -c "import secrets; print(secrets.token_hex(32))"`. Attach a persistent disk mounted at `/var/data`; point both the database and private uploads to it, and retain it across deploys. Production startup fails closed if the secret, absolute storage paths, or a manual-payment support contact is missing. Keep `CONTACT_EMAIL` monitored: the app does not send outbound email notifications.

This repository uses Python's direct `sqlite3` API. It does **not** connect to PostgreSQL through `DATABASE_URL`; a PostgreSQL deployment requires a separate database-layer migration. Back up the persistent database and uploaded files before upgrades.

## Manual order lifecycle

1. A signed-in customer submits an order. Paid items remain `pending`; no money is collected by the application, and paid POST requests are rejected server-side when no support phone/email is configured. Free items are fulfilled immediately.
2. The customer contacts support outside the application to arrange payment.
3. An administrator independently verifies receipt and confirms the pending order in `/admin/orders`.
4. Confirmation is transactional and idempotent: the app completes the order, records the creator's 80% share, increments sales, and adds the product to the customer's library. Downloads then work through the protected library route.

Do not confirm an order before verifying actual payment. Stripe/PayPal checkout, automatic collection, creator withdrawal requests, and automatic payouts are not enabled. Totals are grouped by currency; no currency conversion is performed.

## Language, identity, and responsive UI

The selected white-and-violet ProAssets wordmark on the dark indigo background is shared across the site, with a separate favicon mark. The Arabic/English switch is persistent in the browser and updates `lang` and page direction (`RTL`/`LTR`); bilingual product/category fields switch where translations are available. Financial values are isolated as LTR text in Arabic layouts, and wide tables scroll on narrow screens. Some legacy/runtime text may still need human proofreading; perform a native Arabic/English review before launch.

## Account and support features

- Registration validates fields, normalizes email, restricts public roles to customer/creator, and creates creator ledgers transactionally.
- Account settings support profile edits, password changes with session invalidation, private PNG/JPEG/WebP avatars, saved notification preferences (no email is sent), and guarded profile anonymization.
- Creators can edit listings; edits return published/rejected listings to moderation. Permanent deletion is blocked when customer or financial history exists.
- The public contact form records messages in the administrator inbox. Replies are not sent automatically; the inbox must be checked by an administrator.
- Product review transitions only allow pending listings to be approved or rejected.

## Security and operational limits

State-changing requests require a session-bound CSRF token. Protected routes verify the active account and role against SQLite; uploaded product files are kept outside `static/` and downloads require library entitlement. Responses include basic browser security headers. Login and contact rate limiting, email verification, password recovery, outbound email, payment gateway integration, automatic payouts, and a production legal/compliance review remain outside this build. A public repository history review is also required: removing old credentials from the current working tree does not remove them from Git history.

## Tests and local checks

From the repository root:

```bash
python -m unittest discover -s tests -v
node --check static/js/home.js
node --check static/js/site-i18n.js
node --check static/js/main.js
python -m compileall -q app.py config.py run.py bootstrap_admin.py migrations.py tests
```

The Flask integration suite covers manual order fulfillment/rejection, currency safeguards, CSRF, registration, upload validation and private downloads, account/password/avatar flows, support inbox pagination, product review/edit/delete rules, withdrawal shutdown, security headers, and representative page/template rendering. These local checks do not replace production deployment checks or native-speaker/legal review.
