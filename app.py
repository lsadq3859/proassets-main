# -*- coding: utf-8 -*-
"""
ProAssets - تطبيق Flask الرئيسي
Global Digital Assets Marketplace
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import json
from datetime import datetime, timedelta
from config import config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ===== إعدادات التطبيق =====
ALLOWED_EXTENSIONS = {'pdf', 'epub', 'docx', 'xlsx', 'pptx', 'zip', 'png', 'jpg', 'jpeg', 'svg'}

def allowed_file(filename):
    """التحقق من امتداد الملف"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """الاتصال بقاعدة البيانات"""
    db = sqlite3.connect(os.path.join(BASE_DIR, 'proassets.db'))
    db.row_factory = sqlite3.Row
    return db

def init_db(app):
    """تهيئة قاعدة البيانات"""
    with app.app_context():
        db = get_db()
        with open(os.path.join(BASE_DIR, 'schema.sql'), 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()
        db.close()

def login_required(f):
    """ديكوريتور للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """ديكوريتور للتحقق من صلاحيات الإدارة"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def creator_required(f):
    """ديكوريتور للتحقق من صلاحيات المنشئ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['creator', 'admin']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def create_app(config_name=None):
    """إنشاء تطبيق Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_name == 'production':
        config[config_name].validate()
    
    # إنشاء مجلدات مهمة
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # تهيئة قاعدة البيانات عند البداية
    with app.app_context():
        init_db(app)
    
    # ===== إيقاف المسارات غير الآمنة =====
    @app.before_request
    def block_payments():
        """إيقاف مسارات الدفع والسحب حتى يتم ربطها بشكل آمن"""
        blocked_endpoints = {
            "checkout",
            "creator_withdraw",
            "process_withdrawal",
        }
        
        if request.endpoint in blocked_endpoints and request.method == 'POST':
            return jsonify({
                "status": "disabled",
                "message": "Payments and withdrawals are disabled during development"
            }), 503

    # ===== الصفحات العامة - PUBLIC PAGES =====
    
    @app.route('/')
    def home():
        """الصفحة الرئيسية"""
        db = get_db()
        featured = db.execute(
            'SELECT * FROM products WHERE status = "published" AND is_featured = 1 LIMIT 8'
        ).fetchall()
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        db.close()
        return render_template('home.html', 
                             title='ProAssets - Global Digital Assets',
                             featured_products=featured,
                             categories=categories)
    
    @app.route('/about')
    def about():
        """صفحة من نحن"""
        return render_template('about.html', title='About ProAssets')
    
    @app.route('/privacy')
    def privacy():
        """سياسة الخصوصية"""
        return render_template('privacy.html', title='Privacy Policy')
    
    @app.route('/terms')
    def terms():
        """شروط الاستخدام"""
        return render_template('terms.html', title='Terms of Service')
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """صفحة التواصل"""
        if request.method == 'POST':
            data = request.get_json() or request.form
            subject = (data.get('subject') or '').strip()
            message = (data.get('message') or '').strip()
            if not subject or not message:
                return jsonify({'status': 'error', 'message': 'Subject and message are required'}), 400
            db = get_db()
            db.execute(
                'INSERT INTO messages (sender_id, subject, message) VALUES (?, ?, ?)',
                (session.get('user_id'), subject, message)
            )
            db.commit()
            db.close()
            return jsonify({'status': 'success', 'message': 'Message sent successfully'})
        return render_template('contact.html', title='Contact Us')
    
    # ===== المصادقة - AUTHENTICATION =====
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """تسجيل حساب جديد"""
        if request.method == 'POST':
            data = request.get_json() or request.form
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            user_type = data.get('user_type', 'customer')
            
            if not username or not email or not password:
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            
            if len(password) < 8:
                return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400
            
            db = get_db()
            error = None
            
            if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
                error = 'Email already registered'
            elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                error = 'Username already taken'
            
            if error:
                db.close()
                return jsonify({'status': 'error', 'message': error}), 400
            
            role = 'creator' if user_type == 'creator' else 'customer'
            db.execute(
                'INSERT INTO users (username, email, password_hash, first_name, last_name, role) VALUES (?, ?, ?, ?, ?, ?)',
                (username, email, generate_password_hash(password), first_name, last_name, role)
            )
            db.commit()
            
            if role == 'creator':
                user_id = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()['id']
                db.execute(
                    'INSERT INTO wallets (creator_id, balance, total_earnings) VALUES (?, 0, 0)',
                    (user_id,)
                )
                db.commit()
            
            db.close()
            return jsonify({'status': 'success', 'message': 'Account created successfully'}), 201
        
        return render_template('register.html', title='Create Account')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """تسجيل الدخول"""
        if request.method == 'POST':
            data = request.get_json() or request.form
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'status': 'error', 'message': 'Missing email or password'}), 400
            
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            db.close()
            
            if user is None or not check_password_hash(user['password_hash'], password):
                return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
            if not user['is_active']:
                return jsonify({'status': 'error', 'message': 'Account is disabled'}), 403
            
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True
            
            return jsonify({
                'status': 'success',
                'message': 'Logged in successfully',
                'redirect': url_for('customer_dashboard')
            }), 200
        
        return render_template('login.html', title='Login')
    
    @app.route('/logout')
    def logout():
        """تسجيل الخروج"""
        session.clear()
        return redirect(url_for('home'))
    
    # ===== المنتجات والتصفح - PRODUCTS =====
    
    @app.route('/products')
    def products():
        """قائمة المنتجات مع البحث والتصفية"""
        category = request.args.get('category')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        db = get_db()
        query = 'SELECT * FROM products WHERE status = "published"'
        params = []
        
        if category:
            query += ' AND category_id = ?'
            params.append(category)
        
        if search:
            query += ' AND (title_en LIKE ? OR title_ar LIKE ? OR description_en LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        total = db.execute(f'SELECT COUNT(*) FROM ({query})').fetchone()[0]
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        products_list = db.execute(query, params).fetchall()
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        
        db.close()
        
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('products.html',
                             title='Browse Products',
                             products=products_list,
                             categories=categories,
                             current_category=category,
                             search_query=search,
                             current_page=page,
                             total_pages=total_pages)
    
    @app.route('/product/<slug>')
    def product_detail(slug):
        """صفحة المنتج الواحد"""
        db = get_db()
        product = db.execute(
            'SELECT p.*, u.username, u.first_name, u.last_name, c.name_en, c.name_ar FROM products p '
            'JOIN users u ON p.creator_id = u.id '
            'JOIN categories c ON p.category_id = c.id '
            'WHERE p.slug = ? AND p.status = "published"',
            (slug,)
        ).fetchone()
        
        if product is None:
            db.close()
            return render_template('errors/404.html'), 404
        
        reviews = db.execute(
            'SELECT r.*, u.username FROM reviews r '
            'JOIN users u ON r.customer_id = u.id '
            'WHERE r.product_id = ? ORDER BY r.created_at DESC',
            (product['id'],)
        ).fetchall()
        
        other_products = db.execute(
            'SELECT * FROM products WHERE creator_id = ? AND id != ? AND status = "published" LIMIT 4',
            (product['creator_id'], product['id'])
        ).fetchall()
        
        db.close()
        
        return render_template('product_detail.html',
                             title=product['title_en'],
                             product=product,
                             reviews=reviews,
                             other_products=other_products)
    
    # ===== سلة التسوق - SHOPPING CART =====
    
    @app.route('/cart')
    def cart():
        """عرض سلة التسوق"""
        cart_items = session.get('cart', [])
        db = get_db()
        
        products = []
        total = 0
        
        for item in cart_items:
            product = db.execute(
                'SELECT * FROM products WHERE id = ? AND status = "published"',
                (item['id'],)
            ).fetchone()
            if product:
                products.append(product)
                total += product['price']
        
        db.close()
        
        return render_template('cart.html',
                             title='Shopping Cart',
                             products=products,
                             total=total)
    
    @app.route('/cart/add/<int:product_id>', methods=['POST'])
    def add_to_cart(product_id):
        """إضافة منتج للسلة"""
        db = get_db()
        product = db.execute(
            'SELECT id FROM products WHERE id = ? AND status = "published"',
            (product_id,)
        ).fetchone()
        db.close()
        if product is None:
            return jsonify({'status': 'error', 'message': 'Product is not available'}), 404

        if 'cart' not in session:
            session['cart'] = []
        
        for item in session['cart']:
            if item['id'] == product_id:
                return jsonify({'status': 'error', 'message': 'Product already in cart'}), 400
        
        session['cart'].append({'id': product_id})
        session.modified = True
        
        return jsonify({'status': 'success', 'message': 'Added to cart'})
    
    @app.route('/cart/remove/<int:product_id>', methods=['POST'])
    def remove_from_cart(product_id):
        """إزالة منتج من السلة"""
        if 'cart' in session:
            session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
            session.modified = True
        
        return jsonify({'status': 'success'})
    
    # ===== الدفع - CHECKOUT =====
    
    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        """صفحة الدفع"""
        if request.method == 'POST':
            return jsonify({
                'status': 'error',
                'message': 'Checkout is disabled during development'
            }), 503
        
        return render_template('checkout_disabled.html', title='Checkout')

    @app.route('/download/<int:product_id>')
    @login_required
    def download_product(product_id):
        """تنزيل ملف بعد التحقق من وجوده في مكتبة المستخدم."""
        user_id = session['user_id']
        db = get_db()
        product = db.execute(
            '''SELECT p.file_url FROM products p
               JOIN user_library ul ON ul.product_id = p.id
               WHERE p.id = ? AND ul.customer_id = ? AND p.status = 'published' ''',
            (product_id, user_id)
        ).fetchone()
        db.close()
        if product is None:
            return render_template('errors/403.html'), 403
        file_path = os.path.abspath(product['file_url'] or '')
        upload_root = os.path.abspath(app.config['UPLOAD_FOLDER'])
        if not file_path.startswith(upload_root + os.sep) or not os.path.isfile(file_path):
            return render_template('errors/404.html'), 404
        return send_file(file_path, as_attachment=True)
    
    # ===== لوحة التحكم - العميل - CUSTOMER DASHBOARD =====
    
    @app.route('/dashboard')
    @login_required
    def customer_dashboard():
        """لوحة تحكم العميل"""
        user_id = session['user_id']
        db = get_db()
        
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        purchases = db.execute(
            'SELECT o.*, p.title_en, p.slug FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'WHERE o.customer_id = ? ORDER BY o.created_at DESC LIMIT 10',
            (user_id,)
        ).fetchall()
        
        db.close()
        
        return render_template('customer/dashboard.html',
                             title='My Dashboard',
                             user=user,
                             purchases=purchases)
    
    @app.route('/library')
    @login_required
    def my_library():
        """مكتبتي - المنتجات المشتراة"""
        user_id = session['user_id']
        db = get_db()
        
        products = db.execute(
            'SELECT p.* FROM products p '
            'JOIN user_library ul ON p.id = ul.product_id '
            'WHERE ul.customer_id = ? ORDER BY ul.purchase_date DESC',
            (user_id,)
        ).fetchall()
        
        db.close()
        
        return render_template('customer/library.html',
                             title='My Library',
                             products=products)
    
    @app.route('/account')
    @login_required
    def account_settings():
        """إعدادات الحساب"""
        user_id = session['user_id']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()
        
        return render_template('customer/account.html',
                             title='Account Settings',
                             user=user)
    
    @app.route('/account/update', methods=['POST'])
    @login_required
    def update_account():
        """تحديث بيانات الحساب"""
        user_id = session['user_id']
        data = request.get_json() or request.form
        
        db = get_db()
        db.execute(
            'UPDATE users SET first_name = ?, last_name = ?, bio = ? WHERE id = ?',
            (data.get('first_name'), data.get('last_name'), data.get('bio'), user_id)
        )
        db.commit()
        db.close()
        
        return jsonify({'status': 'success', 'message': 'Account updated'})
    
    # ===== لوحة التحكم - المنشئ - CREATOR DASHBOARD =====
    
    @app.route('/creator/dashboard')
    @creator_required
    def creator_dashboard():
        """لوحة تحكم المنشئ"""
        user_id = session['user_id']
        db = get_db()
        
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        wallet = db.execute('SELECT * FROM wallets WHERE creator_id = ?', (user_id,)).fetchone()
        
        products = db.execute(
            'SELECT * FROM products WHERE creator_id = ? ORDER BY created_at DESC LIMIT 5',
            (user_id,)
        ).fetchall()
        
        sales = db.execute(
            'SELECT o.*, p.title_en FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'WHERE p.creator_id = ? ORDER BY o.created_at DESC LIMIT 5',
            (user_id,)
        ).fetchall()
        
        db.close()
        
        return render_template('creator/dashboard.html',
                             title='Creator Dashboard',
                             user=user,
                             wallet=wallet,
                             products=products,
                             sales=sales)
    
    @app.route('/creator/products')
    @creator_required
    def creator_products():
        """منتجات المنشئ"""
        user_id = session['user_id']
        db = get_db()
        
        products = db.execute(
            'SELECT p.*, c.name_en FROM products p '
            'JOIN categories c ON p.category_id = c.id '
            'WHERE p.creator_id = ? ORDER BY p.created_at DESC',
            (user_id,)
        ).fetchall()
        
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        
        db.close()
        
        return render_template('creator/products.html',
                             title='My Products',
                             products=products,
                             categories=categories)
    
    @app.route('/creator/upload', methods=['GET', 'POST'])
    @creator_required
    def creator_upload():
        """رفع منتج جديد"""
        if request.method == 'POST':
            user_id = session['user_id']
            
            title_en = request.form.get('title_en')
            title_ar = request.form.get('title_ar')
            category_id = request.form.get('category_id')
            price = request.form.get('price', type=float)
            description_en = request.form.get('description_en')
            description_ar = request.form.get('description_ar')
            product_type = request.form.get('product_type')
            
            if 'file' not in request.files:
                return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({'status': 'error', 'message': 'Invalid file'}), 400
            
            filename = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            slug = f"{title_en.lower().replace(' ', '-')}-{int(datetime.now().timestamp())}"
            
            db = get_db()
            db.execute(
                'INSERT INTO products (creator_id, category_id, title_en, title_ar, slug, description_en, description_ar, price, product_type, file_url, file_size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, category_id, title_en, title_ar, slug, description_en, description_ar, price, product_type, file_path, file_size, 'pending')
            )
            db.commit()
            db.close()
            
            return jsonify({'status': 'success', 'message': 'Product uploaded successfully'})
        
        db = get_db()
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        db.close()
        
        return render_template('creator/upload.html',
                             title='Upload Product',
                             categories=categories)
    
    @app.route('/creator/earnings')
    @creator_required
    def creator_earnings():
        """الأرباح والمحفظة"""
        user_id = session['user_id']
        db = get_db()
        
        wallet = db.execute('SELECT * FROM wallets WHERE creator_id = ?', (user_id,)).fetchone()
        withdrawals = db.execute(
            'SELECT * FROM withdrawals WHERE creator_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        
        db.close()
        
        return render_template('creator/earnings.html',
                             title='My Earnings',
                             wallet=wallet,
                             withdrawals=withdrawals)
    
    @app.route('/creator/withdraw', methods=['POST'])
    @creator_required
    def creator_withdraw():
        """طلب سحب أرباح"""
        return jsonify({
            'status': 'error',
            'message': 'Withdrawals are disabled during development'
        }), 503
    
    # ===== لوحة التحكم - الإدارة - ADMIN DASHBOARD =====
    
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """لوحة تحكم الإدارة"""
        db = get_db()
        
        stats = {
            'total_users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'total_products': db.execute('SELECT COUNT(*) FROM products').fetchone()[0],
            'total_sales': db.execute('SELECT SUM(price) FROM orders WHERE payment_status = "completed"').fetchone()[0] or 0,
            'pending_products': db.execute('SELECT COUNT(*) FROM products WHERE status = "pending"').fetchone()[0],
        }
        
        recent_orders = db.execute(
            'SELECT o.*, p.title_en, u.username FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'JOIN users u ON o.customer_id = u.id '
            'ORDER BY o.created_at DESC LIMIT 10'
        ).fetchall()
        
        db.close()
        
        return render_template('admin/dashboard.html',
                             title='Admin Dashboard',
                             stats=stats,
                             recent_orders=recent_orders)
    
    @app.route('/admin/products')
    @admin_required
    def admin_products():
        """مراجعة المنتجات"""
        db = get_db()
        
        status = request.args.get('status', 'pending')
        products = db.execute(
            'SELECT p.*, u.username, c.name_en FROM products p '
            'JOIN users u ON p.creator_id = u.id '
            'JOIN categories c ON p.category_id = c.id '
            'WHERE p.status = ? ORDER BY p.created_at DESC',
            (status,)
        ).fetchall()
        
        db.close()
        
        return render_template('admin/products.html',
                             title='Review Products',
                             products=products,
                             current_status=status)
    
    @app.route('/admin/product/<int:product_id>/approve', methods=['POST'])
    @admin_required
    def approve_product(product_id):
        """الموافقة على منتج"""
        db = get_db()
        db.execute('UPDATE products SET status = ? WHERE id = ?', ('published', product_id))
        db.commit()
        db.close()
        return jsonify({'status': 'success', 'message': 'Product approved'})
    
    @app.route('/admin/product/<int:product_id>/reject', methods=['POST'])
    @admin_required
    def reject_product(product_id):
        """رفض منتج"""
        db = get_db()
        db.execute('UPDATE products SET status = ? WHERE id = ?', ('rejected', product_id))
        db.commit()
        db.close()
        return jsonify({'status': 'success', 'message': 'Product rejected'})
    
    @app.route('/admin/users')
    @admin_required
    def admin_users():
        """إدارة المستخدمين"""
        db = get_db()
        
        users = db.execute(
            'SELECT * FROM users ORDER BY created_at DESC'
        ).fetchall()
        
        db.close()
        
        return render_template('admin/users.html',
                             title='Manage Users',
                             users=users)
    
    @app.route('/admin/withdrawals')
    @admin_required
    def admin_withdrawals():
        """إدارة طلبات السحب"""
        db = get_db()
        
        withdrawals = db.execute(
            'SELECT w.*, u.username FROM withdrawals w '
            'JOIN users u ON w.creator_id = u.id '
            'ORDER BY w.created_at DESC'
        ).fetchall()
        
        db.close()
        
        return render_template('admin/withdrawals.html',
                             title='Manage Withdrawals',
                             withdrawals=withdrawals)
    
    @app.route('/admin/withdrawal/<int:withdrawal_id>/process', methods=['POST'])
    @admin_required
    def process_withdrawal(withdrawal_id):
        """معالجة طلب السحب"""
        db = get_db()
        db.execute(
            'UPDATE withdrawals SET status = ?, processed_at = ? WHERE id = ?',
            ('completed', datetime.now(), withdrawal_id)
        )
        db.commit()
        db.close()
        return jsonify({'status': 'success', 'message': 'Withdrawal processed'})
    
    # ===== معالجة الأخطاء - ERROR HANDLING =====
    
    @app.errorhandler(404)
    def not_found(error):
        """صفحة غير موجودة"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """خطأ في الخادم"""
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """وصول مرفوع"""
        return render_template('errors/403.html'), 403
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
