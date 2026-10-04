# -*- coding: utf-8 -*-
"""
ProAssets - تشغيل التطبيق
"""

import os
from app import create_app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
