import os

from bootstrap_admin import bootstrap_admin
from app import create_app


# إنشاء أول مدير تلقائيًا إذا كانت متغيرات BOOTSTRAP_ADMIN_ موجودة.
# العملية آمنة: إذا كان هناك مدير مسبقًا فلن يتم تغيير أي شيء.
if all(
    os.getenv(name, "").strip()
    for name in (
        "BOOTSTRAP_ADMIN_USERNAME",
        "BOOTSTRAP_ADMIN_EMAIL",
        "BOOTSTRAP_ADMIN_PASSWORD",
    )
):
    bootstrap_admin()


app = create_app(os.getenv("FLASK_ENV", "development"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
    )
