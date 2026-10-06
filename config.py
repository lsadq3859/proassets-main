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
    
    # قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///proassets.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # جلسات المستخدم
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # سيتغير إلى True في الإنتاج
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # الملفات المرفوعة
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    UPLOAD_FOLDER = os.path.abspath(os.environ.get('UPLOAD_FOLDER') or os.path.join(BASE_DIR, 'private_storage'))
    
    # العملات والعمولة
    DEFAULT_CURRENCY = 'USD'
    PLATFORM_COMMISSION = 0.20  # 20% للمنصة
    CREATOR_SHARE = 0.80  # 80% للمنشئ
    
    # الدعم متعدد اللغات
    LANGUAGES = ['en', 'ar']
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # الدفع
    PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER') or 'TEST'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    
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
    """إعدادات الإنتاج (على PythonAnywhere)"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY must be configured in production')


class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# اختر الإعداد بناءً على البيئة
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
