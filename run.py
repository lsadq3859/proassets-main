import os

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

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
