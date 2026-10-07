# ProAssets — Project Notes

## Current state
- **Version:** 1.0.0 Alpha
- **Deployment target:** Render
- **Backend:** Flask + direct SQLite (`DATABASE_PATH`); unused SQLAlchemy/PAYMENT_PROVIDER settings have been removed from the active code.
- **Uploads:** stored in private `UPLOAD_FOLDER`, not `static/`; production must keep this and the SQLite file on persistent storage.
- **Languages:** Arabic/English switch persists in browser local storage, sets RTL/LTR, and covers the home screen plus shared legacy screens. Product/category fields prefer Arabic fields where present. Native-speaker review remains necessary.
- **Marketplace split:** current logic records 20% platform commission / 80% creator share for paid orders. This is ledger accounting, not a payout.
- **Payments:** paid requests are manual only. No card/PayPal collection or automatic creator disbursement is enabled.

## Implemented flows and safeguards
- Passwords use Werkzeug hashes; public registration allows only `customer` and `creator`; creator creation and wallet setup share a transaction.
- Production startup requires a unique `SECRET_KEY` of at least 32 characters, absolute database/upload paths, and a configured support contact. Mount persistent storage on Render and retain/backup it across deploys.
- Protected routes re-check active state, auth version, and role in SQLite. Password changes and anonymized account deletion invalidate older sessions. Administrators cannot self-delete; creator listings/payout history and pending purchase requests are guarded during deletion.
- Every POST/PUT/PATCH/DELETE requires a session-bound CSRF token. Responses set `nosniff`, same-origin framing, referrer and permissions policies; HSTS is enabled for the production configuration.
- Checkout creates pending requests for paid products and fulfills free products immediately. Paid POST requests are blocked server-side when no support phone/email is configured, not only by disabling the UI button. Admin confirmation is transactional and idempotent, verifies order/wallet currency compatibility, records creator earnings, updates sales, and grants customer-library access only after confirmation. Rejections do not grant access.
- Product files have randomized stored names and remain private; download URLs require library entitlement. Avatar uploads are restricted to small raster images with signature and dimension checks. Account avatar writes have a per-request body limit.
- Creator listing edits return published/rejected products to review. Admin review only transitions pending listings. Product deletion is blocked when financial, library, or review history exists.
- Public contact submissions are validated and stored in an admin inbox with pagination and close-only state changes. The app does not send automatic email replies/notifications.
- Withdrawal routes are deliberately blocked and the admin withdrawal screen is read-only. Currency totals remain grouped; no exchange-rate conversion is claimed.
- Privacy/terms pages describe the current manual-payment alpha and flag missing operator/legal details for pre-launch review.

## Verification (local)
- `./.venv/bin/python -m unittest discover -s tests -v` — **18 tests pass**.
- `node --check static/js/home.js`, `node --check static/js/site-i18n.js`, and `node --check static/js/main.js` — pass.
- `./.venv/bin/python -m compileall -q app.py config.py run.py bootstrap_admin.py migrations.py tests` — pass.
- `git diff --check` — clean at the latest recorded check.
- Integration tests cover manual order fulfillment/rejection and idempotency, currency safeguards, CSRF, registration, uploads/private download authorization, account/password/preferences/avatar/deletion flows, support inbox pagination, moderation transitions, withdrawal shutdown, security headers, and representative rendered pages/templates.

## Open work / release risks
- **Not pushed or deployed:** these changes are local to the workspace. GitHub/Render credentials and service settings were not modified in this session.
- **Public Git history:** review historical commits for credentials. Removing a secret from the working tree does not remove it from history; rotate any credentials that were ever live.
- **Render operations:** attach a persistent disk, set `APP_ENV=production`, `SECRET_KEY`, absolute paths and monitored support contact; verify backups and restore procedures before launch.
- **Manual payment operations:** support contact must be monitored and administrators must independently verify every payment before confirming an order. No payout processing exists; ledger balances are not paid funds.
- **Remaining product gaps:** login/contact rate limiting, email verification, password recovery, outbound email, real payment/payout providers, multi-currency conversion, and a production legal/compliance review are not implemented.
- **Localization:** broad Arabic/English coverage and RTL/LTR behavior are present, but native-speaker QA of every screen and creator-supplied translation is still needed.
- **Production checks:** local tests do not validate Render configuration, domain/TLS behavior, persistent-disk semantics, backups, or real payment operations.

## Setup
See `README.md` for local setup, first-admin bootstrap, Render configuration, manual order handling, tests, and release limits.
