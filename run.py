import os

from dotenv import load_dotenv

# Load local .env before importing config.py/app.py. Render's dashboard variables
# take precedence because python-dotenv does not override existing environment.
load_dotenv()

from app import create_app


def runtime_environment():
    configured = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "").strip().lower()
    if configured:
        return configured
    # Render supplies PORT; use production settings by default for deployed workers.
    if os.getenv("RENDER", "").strip().lower() == "true" or os.getenv("PORT"):
        return "production"
    return "development"


app = create_app(runtime_environment())

if all(
    os.getenv(name, "").strip()
    for name in (
        "BOOTSTRAP_ADMIN_USERNAME",
        "BOOTSTRAP_ADMIN_EMAIL",
        "BOOTSTRAP_ADMIN_PASSWORD",
    )
):
    from bootstrap_admin import bootstrap_admin
    bootstrap_admin()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
    )
