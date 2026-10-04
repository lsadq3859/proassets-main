# -*- coding: utf-8 -*-
"""
ProAssets - Database Migrations
تهيئة قاعدة البيانات والبيانات الأساسية
"""

import sqlite3
from datetime import datetime

def get_db():
    """الاتصال بقاعدة البيانات"""
    db = sqlite3.connect('proassets.db')
    db.row_factory = sqlite3.Row
    return db

def init_database():
    """تهيئة قاعدة البيانات"""
    db = get_db()
    cursor = db.cursor()
    
    # قراءة ملف schema.sql
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()
    
    # تنفيذ schema
    cursor.executescript(schema)
    db.commit()
    
    # إضافة البيانات الأساسية
    seed_reference_data(db)
    
    db.close()
    print("✅ Database initialized successfully!")

def seed_reference_data(db):
    """إضافة البيانات الأساسية"""
    cursor = db.cursor()
    
    # الأقسام الأساسية (تم إضافتها في schema.sql)
    # لكن نتأكد من وجودها
    
    categories = [
        (1, 'Books & Ebooks', 'الكتب والكتب الإلكترونية', 'books', 
         'Digital books and publications', 'الكتب والمنشورات الرقمية', '📚', 1),
        (2, 'Templates', 'القوالب', 'templates', 
         'Ready-made templates for business and design', 'قوالس جاهزة للأعمال والتصميم', '📋', 1),
        (3, 'Graphics & Design', 'الجرافيكس والتصميم', 'graphics', 
         'Design assets and graphics', 'أصول التصميم والرسوميات', '🎨', 1),
        (4, 'Code & Dev Tools', 'الأكواد والأدوات البرمجية', 'code', 
         'Code snippets and developer tools', 'مقاطع أكواد وأدوات المطورين', '💻', 1),
        (5, 'Courses & Training', 'الدورات والتدريب', 'courses', 
         'Educational courses and training materials', 'الدورات التعليمية والمواد التدريبية', '🎓', 1),
        (6, 'Audio & Music', 'الصوت والموسيقى', 'audio', 
         'Music, sound effects and audio files', 'الموسيقى والمؤثرات الصوتية والملفات الصوتية', '🎵', 1),
    ]
    
    for category in categories:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO categories 
                (id, name_en, name_ar, slug, description_en, description_ar, icon, is_active) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                category
            )
        except Exception as e:
            print(f"⚠️ Category error: {e}")
    
    db.commit()
    print("✅ Reference data seeded successfully!")

def create_admin_user():
    """إنشاء حساب مدير اختباري"""
    from werkzeug.security import generate_password_hash
    
    db = get_db()
    cursor = db.cursor()
    
    # التحقق من وجود مدير
    cursor.execute('SELECT id FROM users WHERE role = "admin"')
    if cursor.fetchone():
        print("⚠️ Admin user already exists")
        db.close()
        return
    
    # إنشاء حساب مدير
    admin_data = {
        'username': 'admin',
        'email': 'admin@proassets.test',
        'password_hash': generate_password_hash('Admin@123456'),
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin',
        'is_active': 1,
        'is_verified': 1
    }
    
    try:
        cursor.execute(
            '''INSERT INTO users 
            (username, email, password_hash, first_name, last_name, role, is_active, is_verified) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (admin_data['username'], admin_data['email'], admin_data['password_hash'],
             admin_data['first_name'], admin_data['last_name'], admin_data['role'],
             admin_data['is_active'], admin_data['is_verified'])
        )
        db.commit()
        print("✅ Admin user created successfully!")
        print("   Email: admin@proassets.test")
        print("   Password: Admin@123456")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    
    db.close()

def create_test_creator():
    """إنشاء حساب منشئ اختباري"""
    from werkzeug.security import generate_password_hash
    
    db = get_db()
    cursor = db.cursor()
    
    # التحقق من وجود منشئ اختباري
    cursor.execute('SELECT id FROM users WHERE email = "creator@proassets.test"')
    if cursor.fetchone():
        print("⚠️ Test creator already exists")
        db.close()
        return
    
    # إنشاء حساب منشئ
    creator_data = {
        'username': 'testcreator',
        'email': 'creator@proassets.test',
        'password_hash': generate_password_hash('Creator@123456'),
        'first_name': 'Test',
        'last_name': 'Creator',
        'role': 'creator',
        'is_active': 1,
        'is_verified': 1
    }
    
    try:
        cursor.execute(
            '''INSERT INTO users 
            (username, email, password_hash, first_name, last_name, role, is_active, is_verified) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (creator_data['username'], creator_data['email'], creator_data['password_hash'],
             creator_data['first_name'], creator_data['last_name'], creator_data['role'],
             creator_data['is_active'], creator_data['is_verified'])
        )
        
        # الحصول على ID المنشئ
        creator_id = cursor.lastrowid
        
        # إنشاء محفظة للمنشئ
        cursor.execute(
            'INSERT INTO wallets (creator_id, balance, total_earnings) VALUES (?, ?, ?)',
            (creator_id, 0, 0)
        )
        
        db.commit()
        print("✅ Test creator created successfully!")
        print("   Email: creator@proassets.test")
        print("   Password: Creator@123456")
    except Exception as e:
        print(f"❌ Error creating test creator: {e}")
    
    db.close()

def create_test_customer():
    """إنشاء حساب عميل اختباري"""
    from werkzeug.security import generate_password_hash
    
    db = get_db()
    cursor = db.cursor()
    
    # التحقق من وجود عميل اختباري
    cursor.execute('SELECT id FROM users WHERE email = "customer@proassets.test"')
    if cursor.fetchone():
        print("⚠️ Test customer already exists")
        db.close()
        return
    
    # إنشاء حساب عميل
    customer_data = {
        'username': 'testcustomer',
        'email': 'customer@proassets.test',
        'password_hash': generate_password_hash('Customer@123456'),
        'first_name': 'Test',
        'last_name': 'Customer',
        'role': 'customer',
        'is_active': 1,
        'is_verified': 1
    }
    
    try:
        cursor.execute(
            '''INSERT INTO users 
            (username, email, password_hash, first_name, last_name, role, is_active, is_verified) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (customer_data['username'], customer_data['email'], customer_data['password_hash'],
             customer_data['first_name'], customer_data['last_name'], customer_data['role'],
             customer_data['is_active'], customer_data['is_verified'])
        )
        
        db.commit()
        print("✅ Test customer created successfully!")
        print("   Email: customer@proassets.test")
        print("   Password: Customer@123456")
    except Exception as e:
        print(f"❌ Error creating test customer: {e}")
    
    db.close()

if __name__ == '__main__':
    print("🚀 Starting database migrations...\n")
    
    init_database()
    create_admin_user()
    create_test_creator()
    create_test_customer()
    
    print("\n✅ All migrations completed!")
    print("\n📝 Test Accounts:")
    print("   Admin: admin@proassets.test / Admin@123456")
    print("   Creator: creator@proassets.test / Creator@123456")
    print("   Customer: customer@proassets.test / Customer@123456")
