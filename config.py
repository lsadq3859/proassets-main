# -*- coding: utf-8 -*-
"""
ProAssets - إعدادات التطبيق
Global Digital Assets Marketplace
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """الإعدادات الأساسية"""
    
    # المفتاح السري (غيّره لاحقاً!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-change-me'
    
    # قاعدة SQLite؛ اضبط DATABASE_PATH على نقطة تركيب قرص Render الدائم في الإنتاج.
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'proassets.db'
    if not os.path.isabs(DATABASE_PATH):
        DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_PATH)
    
    # جلسات المستخدم
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # سيتغير إلى True في الإنتاج
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # الملفات المرفوعة
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 500 * 1024 * 1024)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'private_storage'
    if not os.path.isabs(UPLOAD_FOLDER):
        UPLOAD_FOLDER = os.path.join(BASE_DIR, UPLOAD_FOLDER)
    UPLOAD_FOLDER = os.path.abspath(UPLOAD_FOLDER)
    
    # العملات والعمولة
    DEFAULT_CURRENCY = 'USD'
    PLATFORM_COMMISSION = 0.20  # 20% للمنصة
    CREATOR_SHARE = 0.80  # 80% للمنشئ
    
    # الدعم متعدد اللغات
    LANGUAGES = ['en', 'ar']
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # البيئة
    DEBUG = False
    TESTING = False

    # بيانات التواصل والدفع اليدوي — تُضبط كأسرار/متغيرات بيئة في Render
    CONTACT_PHONE = os.environ.get('CONTACT_PHONE', '')
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', '')
    PAYMENT_MODE = os.environ.get('PAYMENT_MODE', 'manual')
    AD_IMAGE_URL = os.environ.get('AD_IMAGE_URL', '/static/images/dhfa-banner.png')


class DevelopmentConfig(Config):
    """إعدادات التطوير (على جهازك)"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production settings; deployment-specific persistent paths are validated at startup."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        secret = os.environ.get('SECRET_KEY', '')
        if len(secret) < 32 or secret in {'dev-only-change-me', 'your-secret-key-here-change-in-production'}:
            raise RuntimeError('Production requires a unique SECRET_KEY of at least 32 characters')

        # Require explicit absolute paths in all production deployments. On Render,
        # these must point inside the attached persistent disk mount (for example /var/data).
        database_path = os.environ.get('DATABASE_PATH', '').strip()
        upload_folder = os.environ.get('UPLOAD_FOLDER', '').strip()
        if not database_path or not os.path.isabs(database_path):
            raise RuntimeError('Production requires an absolute DATABASE_PATH on persistent storage')
        if not upload_folder or not os.path.isabs(upload_folder):
            raise RuntimeError('Production requires an absolute UPLOAD_FOLDER on persistent storage')
        if not (cls.CONTACT_PHONE.strip() or cls.CONTACT_EMAIL.strip()):
            raise RuntimeError('Production requires CONTACT_PHONE or CONTACT_EMAIL for manual purchase support')


class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True


# اختر الإعداد بناءً على البيئة
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
