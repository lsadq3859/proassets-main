# -*- coding: utf-8 -*-
"""
ProAssets - تطبيق Flask الرئيسي
Global Digital Assets Marketplace
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, current_app, has_app_context
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import math
import re
import secrets
from urllib.parse import urlsplit
from config import config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ===== إعدادات التطبيق =====
ALLOWED_EXTENSIONS = {'pdf', 'epub', 'docx', 'xlsx', 'pptx', 'zip', 'png', 'jpg', 'jpeg', 'svg'}
MAX_AVATAR_UPLOAD_BYTES = 2 * 1024 * 1024
AVATAR_FORMATS = {
    'png': ('image/png', b'\x89PNG\r\n\x1a\n'),
    'jpeg': ('image/jpeg', b'\xff\xd8\xff'),
    'webp': ('image/webp', b'RIFF'),
}

def allowed_file(filename):
    """التحقق من امتداد الملف"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """فتح اتصال SQLite من مسار موحّد يدعم قرص Render الدائم."""
    if has_app_context():
        configured_path = current_app.config.get('DATABASE_PATH')
    else:
        configured_path = os.environ.get('DATABASE_PATH')
    db_path = configured_path or os.path.join(BASE_DIR, 'proassets.db')
    if not os.path.isabs(db_path):
        db_path = os.path.join(BASE_DIR, db_path)
    db_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = sqlite3.connect(db_path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('PRAGMA busy_timeout = 30000')
    return db

def init_db(app):
    """تهيئة قاعدة البيانات"""
    with app.app_context():
        db = get_db()
        with open(os.path.join(BASE_DIR, 'schema.sql'), 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        user_columns = {row['name'] for row in db.execute('PRAGMA table_info(users)').fetchall()}
        if 'auth_version' not in user_columns:
            db.execute('ALTER TABLE users ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 0')
        db.commit()
        db.close()

def _raster_image_dimensions(content, image_format):
    """Read raster dimensions from common image headers without trusting MIME metadata."""
    if image_format == 'png':
        if len(content) < 24 or content[12:16] != b'IHDR':
            return None
        return int.from_bytes(content[16:20], 'big'), int.from_bytes(content[20:24], 'big')

    if image_format == 'webp':
        if len(content) < 30 or content[8:12] != b'WEBP':
            return None
        chunk = content[12:16]
        if chunk == b'VP8X':
            return 1 + int.from_bytes(content[24:27], 'little'), 1 + int.from_bytes(content[27:30], 'little')
        if chunk == b'VP8L' and len(content) >= 25 and content[20] == 0x2F:
            width = 1 + content[21] + ((content[22] & 0x3F) << 8)
            height = 1 + (content[22] >> 6) + (content[23] << 2) + ((content[24] & 0x0F) << 10)
            return width, height
        if chunk == b'VP8 ' and len(content) >= 30 and content[23:26] == b'\x9d\x01\x2a':
            width = int.from_bytes(content[26:28], 'little') & 0x3FFF
            height = int.from_bytes(content[28:30], 'little') & 0x3FFF
            return width, height
        return None

    if image_format == 'jpeg' and content.startswith(b'\xff\xd8'):
        offset = 2
        start_of_frame = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
        while offset + 4 <= len(content):
            if content[offset] != 0xFF:
                offset += 1
                continue
            while offset < len(content) and content[offset] == 0xFF:
                offset += 1
            if offset >= len(content):
                break
            marker = content[offset]
            offset += 1
            if marker in {0xD8, 0xD9, 0x01, *range(0xD0, 0xD8)}:
                continue
            if offset + 2 > len(content):
                break
            segment_length = int.from_bytes(content[offset:offset + 2], 'big')
            if segment_length < 2 or offset + segment_length > len(content):
                break
            if marker in start_of_frame and segment_length >= 7:
                height = int.from_bytes(content[offset + 3:offset + 5], 'big')
                width = int.from_bytes(content[offset + 5:offset + 7], 'big')
                return width, height
            if marker == 0xDA:
                break
            offset += segment_length
    return None


def _safe_local_redirect_target(target):
    """Accept only local absolute paths as post-login redirect targets."""
    if not isinstance(target, str) or not target.startswith('/') or target.startswith('//') or '\\' in target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or any(ord(char) < 32 for char in target):
        return None
    return target


def _session_user():
    """Load the active user and authoritative role from the database."""
    user_id = session.get('user_id')
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        session.clear()
        return None

    db = get_db()
    try:
        user = db.execute(
            'SELECT id, username, email, role, is_active, auth_version FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
    finally:
        db.close()

    if user is None or not user['is_active']:
        session.clear()
        return None
    try:
        session_auth_version = int(session.get('auth_version'))
    except (TypeError, ValueError):
        session.clear()
        return None
    if session_auth_version != int(user['auth_version']):
        session.clear()
        return None
    return user


def login_required(f):
    """Require a valid, active database user and preserve safe post-login intent."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _session_user() is None:
            next_path = request.full_path.rstrip('?')
            return redirect(url_for('login', next=next_path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Check the admin role from SQLite, never from the client session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = _session_user()
        if user is None:
            next_path = request.full_path.rstrip('?')
            return redirect(url_for('login', next=next_path))
        if user['role'] != 'admin':
            return render_template('errors/403.html'), 403
        return f(*args, **kwargs)
    return decorated_function


def creator_required(f):
    """Check creator/admin access using the authoritative database role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = _session_user()
        if user is None:
            next_path = request.full_path.rstrip('?')
            return redirect(url_for('login', next=next_path))
        if user['role'] not in ('creator', 'admin'):
            return render_template('errors/403.html'), 403
        return f(*args, **kwargs)
    return decorated_function

def create_app(config_name=None):
    """إنشاء تطبيق Flask"""
    
    if config_name is None:
        config_name = (os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV') or '').strip().lower()
        if not config_name:
            is_render = (os.environ.get('RENDER') or '').strip().lower() == 'true'
            config_name = 'production' if (is_render or os.environ.get('PORT')) else 'development'
    if config_name not in config:
        raise ValueError(f'Unknown application environment: {config_name}')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_name == 'production':
        config[config_name].validate()

    @app.context_processor
    def site_contact_context():
        return {
            'contact_phone': app.config.get('CONTACT_PHONE', ''),
            'contact_email': app.config.get('CONTACT_EMAIL', ''),
            'ad_image_url': app.config.get('AD_IMAGE_URL', '/static/images/dhfa-banner.png'),
        }

    @app.context_processor
    def csrf_context():
        return {'csrf_token': lambda: session.setdefault('_csrf_token', secrets.token_urlsafe(32))}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        if config_name == 'production':
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000')
        return response
    
    # إنشاء مجلدات مهمة
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # تهيئة قاعدة البيانات عند البداية
    with app.app_context():
        init_db(app)
    
    # ===== إيقاف المسارات غير الآمنة =====
    @app.before_request
    def block_payments():
        """Keep payout mutation routes disabled until real manual settlement is implemented."""
        blocked_endpoints = {"creator_withdraw"}
        
        if request.endpoint in blocked_endpoints and request.method == 'POST':
            return jsonify({
                "status": "disabled",
                "message": "Creator payouts are disabled in this version; no transfer was made."
            }), 503

    @app.before_request
    def enforce_csrf():
        """Require a session-bound CSRF token for every state-changing request."""
        if request.endpoint == 'account_avatar' and request.method == 'POST':
            request.max_content_length = MAX_AVATAR_UPLOAD_BYTES + 64 * 1024
            request.max_form_memory_size = 64 * 1024
            request.max_form_parts = 4
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return None
        payload = request.get_json(silent=True)
        provided = (
            request.headers.get('X-CSRF-Token')
            or request.form.get('csrf_token')
            or (payload.get('csrf_token') if isinstance(payload, dict) else None)
        )
        expected = session.get('_csrf_token')
        if not provided or not expected or not secrets.compare_digest(str(provided), str(expected)):
            return jsonify({
                'status': 'error',
                'message': 'Your form session expired. Refresh the page and try again.'
            }), 400
        return None

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
            payload = request.get_json(silent=True)
            data = payload if isinstance(payload, dict) else request.form
            subject_value = data.get('subject')
            message_value = data.get('message')
            if not isinstance(subject_value, str) or not isinstance(message_value, str):
                return jsonify({'status': 'error', 'message': 'Subject and message must be text.'}), 400
            subject = subject_value.strip()
            message = message_value.strip()
            if not subject or not message or len(subject) > 160 or len(message) > 5000:
                return jsonify({
                    'status': 'error',
                    'message': 'Subject and message are required (maximum 160 and 5,000 characters).'
                }), 400
            active_user = _session_user() if session.get('user_id') is not None else None
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO messages (sender_id, subject, message) VALUES (?, ?, ?)',
                    (active_user['id'] if active_user else None, subject, message)
                )
                db.commit()
            finally:
                db.close()
            return jsonify({'status': 'success', 'message': 'Message sent successfully'}), 201
        return render_template('contact.html', title='Contact Us')
    
    # ===== المصادقة - AUTHENTICATION =====
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """تسجيل حساب جديد"""
        if request.method == 'POST':
            payload = request.get_json(silent=True)
            data = payload if isinstance(payload, dict) else request.form
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            user_type = data.get('user_type', 'customer')

            if any(not isinstance(value, str) for value in (username, email, password, first_name, last_name, user_type)):
                return jsonify({'status': 'error', 'message': 'Registration fields must be text'}), 400
            username = username.strip()
            email = email.strip().lower()
            first_name = first_name.strip()
            last_name = last_name.strip()
            if not username or not email or not password:
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            if not re.fullmatch(r'[\w.-]{3,32}', username, flags=re.UNICODE):
                return jsonify({'status': 'error', 'message': 'Username must be 3 to 32 letters, numbers, dots, hyphens or underscores'}), 400
            if len(email) > 254 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
                return jsonify({'status': 'error', 'message': 'Enter a valid email address'}), 400
            if len(password) < 8 or len(password) > 256:
                return jsonify({'status': 'error', 'message': 'Password must be between 8 and 256 characters'}), 400
            if len(first_name) > 100 or len(last_name) > 100:
                return jsonify({'status': 'error', 'message': 'Names must be 100 characters or fewer'}), 400
            if user_type not in {'customer', 'creator'}:
                return jsonify({'status': 'error', 'message': 'Choose a valid account type'}), 400

            role = 'creator' if user_type == 'creator' else 'customer'
            db = get_db()
            try:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT id FROM users WHERE lower(email) = ?', (email,)).fetchone():
                    db.rollback()
                    return jsonify({'status': 'error', 'message': 'Email already registered'}), 400
                if db.execute('SELECT id FROM users WHERE lower(username) = lower(?)', (username,)).fetchone():
                    db.rollback()
                    return jsonify({'status': 'error', 'message': 'Username already taken'}), 400
                cursor = db.execute(
                    'INSERT INTO users (username, email, password_hash, first_name, last_name, role) VALUES (?, ?, ?, ?, ?, ?)',
                    (username, email, generate_password_hash(password), first_name or None, last_name or None, role)
                )
                user_id = cursor.lastrowid
                if role == 'creator':
                    db.execute(
                        'INSERT INTO wallets (creator_id, balance, total_earnings) VALUES (?, 0, 0)',
                        (user_id,)
                    )
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Email or username already registered'}), 400
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
            return jsonify({'status': 'success', 'message': 'Account created successfully'}), 201
        
        return render_template('register.html', title='Create Account')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """تسجيل الدخول"""
        if request.method == 'POST':
            payload = request.get_json(silent=True)
            data = payload if isinstance(payload, dict) else request.form
            email = data.get('email')
            password = data.get('password')
            if not isinstance(email, str) or not isinstance(password, str):
                return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
            email = email.strip().lower()
            if not email or not password or len(email) > 254 or len(password) > 256:
                return jsonify({'status': 'error', 'message': 'Email or password is invalid'}), 400

            db = get_db()
            try:
                user = db.execute('SELECT * FROM users WHERE lower(email) = ?', (email,)).fetchone()
            finally:
                db.close()
            
            if user is None or not check_password_hash(user['password_hash'], password):
                return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
            if not user['is_active']:
                return jsonify({'status': 'error', 'message': 'Account is disabled'}), 403
            
            anonymous_cart = []
            cart_value = session.get('cart', [])
            if isinstance(cart_value, list):
                for item in cart_value:
                    try:
                        product_id = int(item.get('id'))
                    except (AttributeError, TypeError, ValueError):
                        continue
                    if product_id > 0 and product_id not in anonymous_cart:
                        anonymous_cart.append(product_id)
                    if len(anonymous_cart) >= 100:
                        break
            session.clear()
            if anonymous_cart:
                session['cart'] = [{'id': product_id} for product_id in anonymous_cart]
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            session['auth_version'] = int(user['auth_version'])
            session.permanent = True

            redirect_target = _safe_local_redirect_target(data.get('next') or request.args.get('next'))
            if redirect_target and redirect_target.startswith('/admin') and user['role'] != 'admin':
                redirect_target = None
            if redirect_target and redirect_target.startswith('/creator') and user['role'] not in ('creator', 'admin'):
                redirect_target = None
            if redirect_target is None:
                redirect_target = url_for('admin_dashboard') if user['role'] == 'admin' else url_for('customer_dashboard')

            return jsonify({
                'status': 'success',
                'message': 'Logged in successfully',
                'redirect': redirect_target
            }), 200
        
        return render_template('login.html', title='Login', next_url=_safe_local_redirect_target(request.args.get('next')) or '')
    
    @app.route('/logout', methods=['POST'])
    def logout():
        """تسجيل الخروج"""
        session.clear()
        return redirect(url_for('home'))
    
    # ===== المنتجات والتصفح - PRODUCTS =====
    
    @app.route('/products')
    def products():
        """قائمة المنتجات مع البحث والتصفية"""
        category = request.args.get('category')
        search = (request.args.get('search', '') or '').strip()[:100]
        page = max(request.args.get('page', 1, type=int) or 1, 1)
        per_page = 12
        
        db = get_db()
        query = (
            'SELECT p.*, c.name_en AS category_name_en, c.name_ar AS category_name_ar '
            'FROM products p LEFT JOIN categories c ON c.id = p.category_id '
            'WHERE p.status = "published"'
        )
        params = []
        
        if category:
            query += ' AND category_id = ?'
            params.append(category)
        
        if search:
            query += ' AND (title_en LIKE ? OR title_ar LIKE ? OR description_en LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        total = db.execute(f'SELECT COUNT(*) FROM ({query})', params).fetchone()[0]
        total_pages = max(1, math.ceil(total / per_page))
        page = min(page, total_pages)
        
        query += ' ORDER BY p.created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        products_list = db.execute(query, params).fetchall()
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        
        db.close()
        
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
        """Render valid cart products with separate subtotals for each currency."""
        cart_items = session.get('cart', [])
        product_ids = []
        if isinstance(cart_items, list):
            for item in cart_items:
                try:
                    product_id = int(item.get('id'))
                except (AttributeError, TypeError, ValueError):
                    continue
                if product_id > 0 and product_id not in product_ids:
                    product_ids.append(product_id)
        db = get_db()
        products = []
        if product_ids:
            placeholders = ','.join('?' for _ in product_ids)
            rows = db.execute(
                f'SELECT * FROM products WHERE id IN ({placeholders}) AND status = "published"',
                product_ids
            ).fetchall()
            by_id = {row['id']: row for row in rows}
            products = [by_id[product_id] for product_id in product_ids if product_id in by_id]
        db.close()

        totals_by_currency = {}
        for product in products:
            currency = product['currency'] or 'USD'
            try:
                price = float(product['price'])
            except (TypeError, ValueError):
                continue
            if math.isfinite(price) and price >= 0:
                totals_by_currency[currency] = totals_by_currency.get(currency, 0) + price
        totals_by_currency = {currency: round(total, 2) for currency, total in totals_by_currency.items()}
        return render_template(
            'cart.html', title='Shopping Cart', products=products,
            totals_by_currency=totals_by_currency
        )
    
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

        cart_items = session.get('cart', [])
        if not isinstance(cart_items, list):
            cart_items = []
        for item in cart_items:
            try:
                existing_id = int(item.get('id'))
            except (AttributeError, TypeError, ValueError):
                continue
            if existing_id == product_id:
                session['cart'] = cart_items
                return jsonify({'status': 'success', 'message': 'Product already in cart', 'already_in_cart': True}), 200
        if len(cart_items) >= 100:
            return jsonify({'status': 'error', 'message': 'Your cart has reached the 100-item limit'}), 400
        cart_items.append({'id': product_id})
        session['cart'] = cart_items
        session.modified = True
        
        return jsonify({'status': 'success', 'message': 'Added to cart'})
    
    @app.route('/cart/remove/<int:product_id>', methods=['POST'])
    def remove_from_cart(product_id):
        """إزالة منتج من السلة"""
        cart_items = session.get('cart', [])
        if isinstance(cart_items, list):
            remaining = []
            for item in cart_items:
                try:
                    item_id = int(item.get('id'))
                except (AttributeError, TypeError, ValueError):
                    continue
                if item_id != product_id:
                    remaining.append({'id': item_id})
            session['cart'] = remaining
            session.modified = True
        
        return jsonify({'status': 'success'})
    
    # ===== الدفع - CHECKOUT =====
    
    @app.route('/checkout', methods=['GET', 'POST'])
    @login_required
    def checkout():
        """إنشاء طلبات شراء يدوية معلّقة دون تحصيل أموال آلي."""
        if request.method == 'POST':
            cart_items = session.get('cart', [])
            if not cart_items:
                return jsonify({'status': 'error', 'message': 'Your cart is empty'}), 400

            contact_phone = app.config.get('CONTACT_PHONE', '').strip()
            contact_email = app.config.get('CONTACT_EMAIL', '').strip()
            manual_support_available = bool(contact_phone or contact_email)

            # Normalize and deduplicate IDs from the signed cart session.
            product_ids = []
            for item in cart_items:
                try:
                    product_id = int(item.get('id'))
                except (AttributeError, TypeError, ValueError):
                    continue
                if product_id > 0 and product_id not in product_ids:
                    product_ids.append(product_id)
            if not product_ids:
                return jsonify({'status': 'error', 'message': 'No valid products in your cart'}), 400

            db = get_db()
            created = 0
            pending_created = 0
            free_completed = 0
            skipped = 0
            customer_id = int(session['user_id'])
            try:
                db.execute('BEGIN IMMEDIATE')
                for product_id in product_ids:
                    product = db.execute(
                        'SELECT id, creator_id, price, currency FROM products '
                        'WHERE id = ? AND status = "published"',
                        (product_id,)
                    ).fetchone()
                    if product is None or product['creator_id'] == customer_id:
                        skipped += 1
                        continue
                    prior_purchase = db.execute(
                        '''SELECT 1 FROM user_library WHERE customer_id = ? AND product_id = ?
                           UNION ALL
                           SELECT 1 FROM orders WHERE customer_id = ? AND product_id = ?
                             AND payment_status IN ('pending', 'completed')
                           LIMIT 1''',
                        (customer_id, product['id'], customer_id, product['id'])
                    ).fetchone()
                    if prior_purchase:
                        skipped += 1
                        continue

                    raw_price = float(product['price'])
                    if not math.isfinite(raw_price) or raw_price < 0:
                        skipped += 1
                        continue
                    price = round(raw_price, 2)
                    if price == 0:
                        db.execute(
                            '''INSERT INTO orders
                               (customer_id, product_id, price, currency, payment_method,
                                payment_status, platform_commission, creator_earnings)
                               VALUES (?, ?, 0, ?, 'free', 'completed', 0, 0)''',
                            (customer_id, product['id'], product['currency'])
                        )
                        db.execute(
                            'INSERT OR IGNORE INTO user_library (customer_id, product_id) VALUES (?, ?)',
                            (customer_id, product['id'])
                        )
                        db.execute(
                            'UPDATE products SET sales_count = COALESCE(sales_count, 0) + 1 WHERE id = ?',
                            (product['id'],)
                        )
                        free_completed += 1
                    else:
                        if not manual_support_available:
                            db.rollback()
                            return jsonify({
                                'status': 'error',
                                'message': 'Configure a support phone number or email before sending paid purchase requests.'
                            }), 400
                        commission = round(price * config[config_name].PLATFORM_COMMISSION, 2)
                        creator_earnings = round(price - commission, 2)
                        db.execute(
                            '''INSERT INTO orders
                               (customer_id, product_id, price, currency, payment_method,
                                payment_status, platform_commission, creator_earnings)
                               VALUES (?, ?, ?, ?, 'manual_contact', 'pending', ?, ?)''',
                            (customer_id, product['id'], price, product['currency'],
                             commission, creator_earnings)
                        )
                        pending_created += 1
                    created += 1

                if created == 0:
                    db.rollback()
                    return jsonify({
                        'status': 'error',
                        'message': 'No purchasable products were found. Creators cannot purchase their own products.'
                    }), 400
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

            session['cart'] = []
            session.modified = True
            if pending_created and free_completed:
                message = 'Manual payment requested for paid products; free products are now in your library.'
            elif pending_created:
                message = 'Purchase request submitted. Contact support to complete manual payment.'
            else:
                message = 'Free products have been added to your library.'
            return jsonify({
                'status': 'success',
                'message': message,
                'orders_created': created,
                'pending_orders_created': pending_created,
                'free_orders_completed': free_completed,
                'unavailable_items': skipped,
            }), 201

        cart_ids = []
        for item in session.get('cart', []):
            try:
                product_id = int(item.get('id'))
            except (AttributeError, TypeError, ValueError):
                continue
            if product_id > 0 and product_id not in cart_ids:
                cart_ids.append(product_id)
        db = get_db()
        products = []
        if cart_ids:
            placeholders = ','.join('?' for _ in cart_ids)
            products = db.execute(
                f'''SELECT p.id, p.title_en, p.title_ar, p.price, p.currency FROM products p
                    WHERE p.id IN ({placeholders}) AND p.status = 'published'
                      AND p.creator_id != ?
                      AND NOT EXISTS (SELECT 1 FROM user_library ul
                                      WHERE ul.customer_id = ? AND ul.product_id = p.id)
                      AND NOT EXISTS (SELECT 1 FROM orders o
                                      WHERE o.customer_id = ? AND o.product_id = p.id
                                        AND o.payment_status IN ('pending', 'completed'))
                    ORDER BY p.created_at DESC''',
                cart_ids + [int(session['user_id']), int(session['user_id']), int(session['user_id'])]
            ).fetchall()
        db.close()
        currencies = {product['currency'] or config[config_name].DEFAULT_CURRENCY for product in products}
        total_price = round(sum(float(product['price']) for product in products), 2) if len(currencies) == 1 else None
        total_currency = next(iter(currencies)) if len(currencies) == 1 else None
        has_paid_items = any(float(product['price']) > 0 for product in products)
        return render_template(
            'checkout.html',
            title='Manual Checkout',
            products=products,
            total_price=total_price,
            total_currency=total_currency,
            has_paid_items=has_paid_items,
        )

    @app.route('/download/<int:product_id>')
    @login_required
    def download_product(product_id):
        """تنزيل ملف بعد التحقق من وجوده في مكتبة المستخدم."""
        user_id = session['user_id']
        db = get_db()
        product = db.execute(
            '''SELECT p.file_url FROM products p
               JOIN user_library ul ON ul.product_id = p.id
               WHERE p.id = ? AND ul.customer_id = ? ''',
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
        """Show lifetime order statistics and a separate completed-spend subtotal per currency."""
        user_id = int(session['user_id'])
        db = get_db()
        try:
            user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            purchases = db.execute(
                'SELECT o.*, p.title_en, p.title_ar, p.slug, p.status AS product_status FROM orders o '
                'JOIN products p ON o.product_id = p.id '
                'WHERE o.customer_id = ? ORDER BY o.created_at DESC, o.id DESC LIMIT 10',
                (user_id,)
            ).fetchall()
            purchase_count = db.execute(
                'SELECT COUNT(*) FROM orders WHERE customer_id = ?', (user_id,)
            ).fetchone()[0]
            completed_count = db.execute(
                "SELECT COUNT(*) FROM orders WHERE customer_id = ? AND payment_status = 'completed'",
                (user_id,)
            ).fetchone()[0]
            spent_by_currency = db.execute(
                '''SELECT COALESCE(currency, 'USD') AS currency, ROUND(SUM(price), 2) AS total
                   FROM orders WHERE customer_id = ? AND payment_status = 'completed'
                   GROUP BY COALESCE(currency, 'USD') ORDER BY currency''',
                (user_id,)
            ).fetchall()
        finally:
            db.close()

        return render_template(
            'customer/dashboard.html', title='My Dashboard', user=user, purchases=purchases,
            purchase_count=purchase_count, completed_count=completed_count,
            spent_by_currency=spent_by_currency
        )
    
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
        """Render account details and the saved notification/display preferences."""
        user_id = int(session['user_id'])
        db = get_db()
        try:
            user = db.execute(
                '''SELECT u.*, COALESCE(pref.email_notifications, 0) AS email_notifications,
                          COALESCE(pref.marketing_emails, 0) AS marketing_emails,
                          COALESCE(pref.order_updates, 0) AS order_updates,
                          COALESCE(pref.currency, 'USD') AS preferred_currency
                   FROM users u LEFT JOIN user_preferences pref ON pref.user_id = u.id
                   WHERE u.id = ?''',
                (user_id,)
            ).fetchone()
        finally:
            db.close()

        return render_template('customer/account.html', title='Account Settings', user=user)

    @app.route('/account/update', methods=['POST'])
    @login_required
    def update_account():
        """Update a user's editable profile fields with explicit length limits."""
        user_id = int(session['user_id'])
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = request.form
        first_name_value = data.get('first_name', '')
        last_name_value = data.get('last_name', '')
        bio_value = data.get('bio', '')
        if any(not isinstance(value, str) for value in (first_name_value, last_name_value, bio_value)):
            return jsonify({'status': 'error', 'message': 'Profile fields must be text'}), 400
        first_name = first_name_value.strip()
        last_name = last_name_value.strip()
        bio = bio_value.strip()
        if len(first_name) > 100 or len(last_name) > 100 or len(bio) > 500:
            return jsonify({'status': 'error', 'message': 'Names must be 100 characters or fewer and bio 500 characters or fewer'}), 400

        db = get_db()
        try:
            db.execute(
                'UPDATE users SET first_name = ?, last_name = ?, bio = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (first_name or None, last_name or None, bio or None, user_id)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return jsonify({'status': 'success', 'message': 'Account updated'})

    @app.route('/account/security', methods=['POST'])
    @login_required
    def update_password():
        """Change password only after verifying the current password, then end the session."""
        user_id = int(session['user_id'])
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = request.form
        current_password = data.get('current_password') or ''
        new_password = data.get('new_password') or ''
        confirm_password = data.get('confirm_password') or ''
        if any(not isinstance(value, str) for value in (current_password, new_password, confirm_password)):
            return jsonify({'status': 'error', 'message': 'Password fields must be text'}), 400
        if not current_password or not new_password or not confirm_password:
            return jsonify({'status': 'error', 'message': 'Complete all password fields'}), 400
        if len(new_password) < 8 or len(new_password) > 256:
            return jsonify({'status': 'error', 'message': 'Password must be between 8 and 256 characters'}), 400
        if new_password != confirm_password:
            return jsonify({'status': 'error', 'message': 'Passwords do not match'}), 400

        db = get_db()
        try:
            user = db.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()
            if user is None or not check_password_hash(user['password_hash'], current_password):
                return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 403
            db.execute(
                'UPDATE users SET password_hash = ?, auth_version = auth_version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (generate_password_hash(new_password), user_id)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        # Flask's default session is a signed client cookie, so clear it to force re-authentication.
        session.clear()
        return jsonify({'status': 'success', 'message': 'Password changed. Please sign in again.'})

    @app.route('/account/preferences', methods=['POST'])
    @login_required
    def update_preferences():
        """Save the user's notification choices and preferred price-display currency."""
        user_id = int(session['user_id'])
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = request.form
        currency_value = data.get('currency') or 'USD'
        if not isinstance(currency_value, str):
            return jsonify({'status': 'error', 'message': 'Choose a supported currency'}), 400
        currency = currency_value.upper()
        if currency not in {'USD', 'EUR', 'GBP', 'AED'}:
            return jsonify({'status': 'error', 'message': 'Choose a supported currency'}), 400

        def enabled(name):
            return 1 if str(data.get(name, '')).lower() in {'1', 'true', 'on', 'yes'} else 0

        db = get_db()
        try:
            db.execute(
                '''INSERT INTO user_preferences
                   (user_id, email_notifications, marketing_emails, order_updates, currency, updated_at)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(user_id) DO UPDATE SET
                     email_notifications=excluded.email_notifications,
                     marketing_emails=excluded.marketing_emails,
                     order_updates=excluded.order_updates,
                     currency=excluded.currency,
                     updated_at=CURRENT_TIMESTAMP''',
                (user_id, enabled('email_notifications'), enabled('marketing_emails'),
                 enabled('order_updates'), currency)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return jsonify({'status': 'success', 'message': 'Preferences saved'})

    @app.route('/account/avatar', methods=['GET', 'POST'])
    @login_required
    def account_avatar():
        """Upload or privately serve the signed-in user's raster avatar."""
        user_id = int(session['user_id'])
        avatar_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        if request.method == 'POST':
            uploaded = request.files.get('avatar')
            if uploaded is None or not uploaded.filename:
                return jsonify({'status': 'error', 'message': 'Choose an image to upload'}), 400
            content = uploaded.stream.read(MAX_AVATAR_UPLOAD_BYTES + 1)
            if not content:
                return jsonify({'status': 'error', 'message': 'The image file is empty'}), 400
            if len(content) > MAX_AVATAR_UPLOAD_BYTES:
                return jsonify({'status': 'error', 'message': 'Avatar images must be 2 MB or smaller'}), 413

            detected = None
            for image_format, (mime_type, signature) in AVATAR_FORMATS.items():
                if image_format == 'webp':
                    if content.startswith(signature) and len(content) >= 12 and content[8:12] == b'WEBP':
                        detected = (image_format, mime_type)
                        break
                elif content.startswith(signature):
                    detected = (image_format, mime_type)
                    break
            if detected is None:
                return jsonify({'status': 'error', 'message': 'Upload a valid PNG, JPEG, or WebP image'}), 400

            extension, _mime_type = detected
            dimensions = _raster_image_dimensions(content, extension)
            if dimensions is None:
                return jsonify({'status': 'error', 'message': 'The image header is invalid or unsupported'}), 400
            width, height = dimensions
            if not (1 <= width <= 4096 and 1 <= height <= 4096 and width * height <= 16777216):
                return jsonify({'status': 'error', 'message': 'Image dimensions must be no larger than 4,096 by 4,096 pixels'}), 400
            filename = f'user-{user_id}-{secrets.token_hex(16)}.{extension}'
            file_path = os.path.join(avatar_dir, filename)
            db = get_db()
            old_filename = None
            try:
                current = db.execute('SELECT profile_image FROM users WHERE id = ?', (user_id,)).fetchone()
                old_filename = current['profile_image'] if current else None
                with open(file_path, 'xb') as avatar_file:
                    avatar_file.write(content)
                db.execute(
                    'UPDATE users SET profile_image = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (filename, user_id)
                )
                db.commit()
            except Exception:
                db.rollback()
                if os.path.isfile(file_path):
                    os.remove(file_path)
                raise
            finally:
                db.close()

            if old_filename and os.path.basename(old_filename) == old_filename and old_filename.startswith(f'user-{user_id}-'):
                old_path = os.path.join(avatar_dir, old_filename)
                if os.path.abspath(old_path) != os.path.abspath(file_path) and os.path.isfile(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        current_app.logger.warning('Unable to remove replaced avatar for user %s', user_id)
            return jsonify({'status': 'success', 'message': 'Avatar updated', 'url': url_for('account_avatar')})

        db = get_db()
        try:
            user = db.execute('SELECT profile_image FROM users WHERE id = ?', (user_id,)).fetchone()
        finally:
            db.close()
        if user is None or not user['profile_image']:
            return jsonify({'status': 'error', 'message': 'No profile image is set'}), 404
        filename = user['profile_image']
        if os.path.basename(filename) != filename or not filename.startswith(f'user-{user_id}-'):
            return jsonify({'status': 'error', 'message': 'Profile image is unavailable'}), 404
        extension = filename.rsplit('.', 1)[-1].lower()
        mime_type = AVATAR_FORMATS.get(extension)
        if mime_type is None:
            return jsonify({'status': 'error', 'message': 'Profile image is unavailable'}), 404
        file_path = os.path.join(avatar_dir, filename)
        if not os.path.isfile(file_path):
            return jsonify({'status': 'error', 'message': 'Profile image is unavailable'}), 404
        response = send_file(file_path, mimetype=mime_type[0], conditional=True, max_age=3600)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'private, max-age=3600'
        return response

    @app.route('/account/delete', methods=['POST'])
    @login_required
    def delete_account():
        """Anonymize an account while retaining essential order records and audit integrity."""
        user_id = int(session['user_id'])
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = request.form
        password = data.get('current_password') or ''
        confirmation_value = data.get('confirmation') or ''
        if not isinstance(password, str) or not isinstance(confirmation_value, str):
            return jsonify({'status': 'error', 'message': 'Confirmation fields must be text'}), 400
        confirmation = confirmation_value.strip()
        if not password or confirmation != 'DELETE':
            return jsonify({'status': 'error', 'message': 'Enter your password and type DELETE to confirm'}), 400

        db = get_db()
        old_avatar = None
        try:
            db.execute('BEGIN IMMEDIATE')
            user = db.execute(
                'SELECT id, role, password_hash, profile_image FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            if user is None:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Account not found'}), 404
            if user['role'] == 'admin':
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Administrator accounts cannot be self-deleted'}), 403
            if not check_password_hash(user['password_hash'], password):
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 403

            pending_order = db.execute(
                "SELECT 1 FROM orders WHERE customer_id = ? AND payment_status = 'pending' LIMIT 1",
                (user_id,)
            ).fetchone()
            if pending_order:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Resolve pending purchase requests before deleting your account'}), 409

            if user['role'] == 'creator':
                has_products = db.execute('SELECT 1 FROM products WHERE creator_id = ? LIMIT 1', (user_id,)).fetchone()
                has_withdrawals = db.execute('SELECT 1 FROM withdrawals WHERE creator_id = ? LIMIT 1', (user_id,)).fetchone()
                wallet = db.execute(
                    'SELECT balance, total_earnings FROM wallets WHERE creator_id = ?', (user_id,)
                ).fetchone()
                has_wallet_value = wallet and (float(wallet['balance'] or 0) != 0 or float(wallet['total_earnings'] or 0) != 0)
                if has_products or has_withdrawals or has_wallet_value:
                    db.rollback()
                    return jsonify({'status': 'error', 'message': 'Creator accounts with products or payout history must contact support before deletion'}), 409

            old_avatar = user['profile_image']
            db.execute('DELETE FROM user_preferences WHERE user_id = ?', (user_id,))
            db.execute('DELETE FROM notifications WHERE user_id = ?', (user_id,))
            if user['role'] == 'creator':
                db.execute(
                    'DELETE FROM wallets WHERE creator_id = ? AND COALESCE(balance, 0) = 0 AND COALESCE(total_earnings, 0) = 0',
                    (user_id,)
                )
            db.execute('DELETE FROM reviews WHERE customer_id = ?', (user_id,))
            db.execute('DELETE FROM user_library WHERE customer_id = ?', (user_id,))
            db.execute('UPDATE messages SET sender_id = NULL WHERE sender_id = ?', (user_id,))
            anonymized_username = f'deleted-user-{user_id}-{secrets.token_hex(4)}'
            anonymized_email = f'deleted-{user_id}-{secrets.token_hex(8)}@invalid.local'
            db.execute(
                '''UPDATE users SET username = ?, email = ?, password_hash = ?, first_name = NULL,
                   last_name = NULL, bio = NULL, profile_image = NULL, is_active = 0,
                   is_verified = 0, role = 'customer', auth_version = auth_version + 1,
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
                (anonymized_username, anonymized_email, generate_password_hash(secrets.token_urlsafe(48)), user_id)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        avatar_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
        if old_avatar and os.path.basename(old_avatar) == old_avatar and old_avatar.startswith(f'user-{user_id}-'):
            old_path = os.path.join(avatar_dir, old_avatar)
            if os.path.isfile(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    current_app.logger.warning('Unable to remove deleted avatar for user %s', user_id)
        session.clear()
        return jsonify({'status': 'success', 'message': 'Account deleted. Essential order records are retained in anonymized form.'})
    
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
            'SELECT o.*, p.title_en, p.title_ar, p.slug FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'WHERE p.creator_id = ? AND o.payment_status = \'completed\' '
            'ORDER BY o.created_at DESC LIMIT 5',
            (user_id,)
        ).fetchall()
        sales_stats = db.execute(
            '''SELECT COUNT(*) AS total_sales
               FROM orders o JOIN products p ON o.product_id = p.id
               WHERE p.creator_id = ? AND o.payment_status = 'completed' ''',
            (user_id,)
        ).fetchone()
        sales_by_currency = db.execute(
            '''SELECT COALESCE(o.currency, 'USD') AS currency,
                      ROUND(SUM(o.price), 2) AS gross_revenue,
                      ROUND(SUM(COALESCE(o.creator_earnings, ROUND(o.price * (1 - ?), 2))), 2) AS creator_earnings
               FROM orders o JOIN products p ON o.product_id = p.id
               WHERE p.creator_id = ? AND o.payment_status = 'completed'
               GROUP BY COALESCE(o.currency, 'USD') ORDER BY currency''',
            (config[config_name].PLATFORM_COMMISSION, user_id)
        ).fetchall()

        db.close()

        return render_template('creator/dashboard.html',
                             title='Creator Dashboard',
                             user=user,
                             wallet=wallet,
                             products=products,
                             sales=sales,
                             sales_stats=sales_stats,
                             sales_by_currency=sales_by_currency)
    
    @app.route('/creator/products')
    @creator_required
    def creator_products():
        """منتجات المنشئ"""
        user_id = session['user_id']
        db = get_db()
        
        products = db.execute(
            '''SELECT p.*, c.name_en AS category_name_en, c.name_ar AS category_name_ar,
                      CASE WHEN EXISTS (SELECT 1 FROM orders o WHERE o.product_id = p.id)
                             OR EXISTS (SELECT 1 FROM user_library ul WHERE ul.product_id = p.id)
                             OR EXISTS (SELECT 1 FROM reviews r WHERE r.product_id = p.id)
                           THEN 1 ELSE 0 END AS has_history
               FROM products p JOIN categories c ON p.category_id = c.id
            '''
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
            user_id = int(session['user_id'])
            title_en = (request.form.get('title_en') or '').strip()
            title_ar = (request.form.get('title_ar') or '').strip()
            description_en = (request.form.get('description_en') or '').strip()
            description_ar = (request.form.get('description_ar') or '').strip()
            product_type = (request.form.get('product_type') or '').strip().lower()
            try:
                category_id = int(request.form.get('category_id', ''))
                price = float(request.form.get('price', ''))
            except (TypeError, ValueError):
                return jsonify({'status': 'error', 'message': 'Choose a category and enter a valid price'}), 400

            if not title_en or not title_ar or len(title_en) > 140 or len(title_ar) > 140:
                return jsonify({'status': 'error', 'message': 'English and Arabic product names are required (maximum 140 characters)'}), 400
            if not math.isfinite(price) or not 0 <= price <= 999999:
                return jsonify({'status': 'error', 'message': 'Price must be between 0 and 999,999 USD'}), 400
            if len(description_en) > 3000 or len(description_ar) > 3000:
                return jsonify({'status': 'error', 'message': 'Descriptions must be 3,000 characters or fewer'}), 400
            if product_type not in {'ebook', 'template', 'design', 'software', 'course', 'other'}:
                return jsonify({'status': 'error', 'message': 'Choose a valid product type'}), 400
            if 'file' not in request.files:
                return jsonify({'status': 'error', 'message': 'No file provided'}), 400

            uploaded_file = request.files['file']
            safe_original_name = secure_filename(uploaded_file.filename or '')
            if not safe_original_name or not allowed_file(safe_original_name):
                return jsonify({'status': 'error', 'message': 'Invalid file type or filename'}), 400

            db = get_db()
            file_path = None
            try:
                category = db.execute(
                    'SELECT id FROM categories WHERE id = ? AND is_active = 1',
                    (category_id,)
                ).fetchone()
                if category is None:
                    return jsonify({'status': 'error', 'message': 'Choose an active product category'}), 400

                filename = f"{secrets.token_hex(12)}_{safe_original_name}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                file_size = os.path.getsize(file_path)
                slug = f"{secure_filename(title_en).lower().replace('_', '-')[:80] or 'digital-product'}-{secrets.token_hex(5)}"

                db.execute(
                    '''INSERT INTO products
                       (creator_id, category_id, title_en, title_ar, slug, description_en,
                        description_ar, price, product_type, file_url, file_size, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')''',
                    (user_id, category_id, title_en, title_ar, slug, description_en,
                     description_ar, round(price, 2), product_type, file_path, file_size)
                )
                db.commit()
            except Exception:
                db.rollback()
                if file_path and os.path.isfile(file_path):
                    os.remove(file_path)
                raise
            finally:
                db.close()

            return jsonify({'status': 'success', 'message': 'Product uploaded successfully'}), 201
        
        db = get_db()
        categories = db.execute('SELECT * FROM categories WHERE is_active = 1').fetchall()
        db.close()
        
        return render_template('creator/upload.html',
                             title='Upload Product',
                             categories=categories)

    @app.route('/creator/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @creator_required
    def edit_creator_product(product_id):
        """Edit a creator-owned listing; listing changes go back to moderation."""
        creator_id = int(session['user_id'])
        db = get_db()
        try:
            product = db.execute(
                '''SELECT p.*, c.name_en AS category_name_en, c.name_ar AS category_name_ar
                   FROM products p LEFT JOIN categories c ON c.id = p.category_id
                   WHERE p.id = ? AND p.creator_id = ?''',
                (product_id, creator_id)
            ).fetchone()
            if product is None:
                return render_template('errors/404.html'), 404
            categories = db.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY name_en').fetchall()

            if request.method == 'GET':
                return render_template(
                    'creator/edit_product.html', title='Edit Product', product=product,
                    categories=categories, error=None, updated=request.args.get('updated') == '1'
                )

            title_en = (request.form.get('title_en') or '').strip()
            title_ar = (request.form.get('title_ar') or '').strip()
            description_en = (request.form.get('description_en') or '').strip()
            description_ar = (request.form.get('description_ar') or '').strip()
            product_type = (request.form.get('product_type') or '').strip().lower()
            try:
                category_id = int(request.form.get('category_id', ''))
                price = float(request.form.get('price', ''))
            except (TypeError, ValueError):
                return render_template(
                    'creator/edit_product.html', title='Edit Product', product=product,
                    categories=categories, error='Choose a category and enter a valid price', updated=False
                ), 400

            error = None
            if not title_en or not title_ar or len(title_en) > 140 or len(title_ar) > 140:
                error = 'English and Arabic product names are required (maximum 140 characters)'
            elif not math.isfinite(price) or not 0 <= price <= 999999:
                error = 'Price must be between 0 and 999,999 USD'
            elif len(description_en) > 3000 or len(description_ar) > 3000:
                error = 'Descriptions must be 3,000 characters or fewer'
            elif product_type not in {'ebook', 'template', 'design', 'software', 'course', 'other'}:
                error = 'Choose a valid product type'
            elif db.execute(
                'SELECT id FROM categories WHERE id = ? AND is_active = 1', (category_id,)
            ).fetchone() is None:
                error = 'Choose an active product category'
            if error:
                return render_template(
                    'creator/edit_product.html', title='Edit Product', product=product,
                    categories=categories, error=error, updated=False
                ), 400

            next_status = 'pending' if product['status'] in {'published', 'rejected'} else product['status']
            db.execute(
                '''UPDATE products SET category_id = ?, title_en = ?, title_ar = ?,
                   description_en = ?, description_ar = ?, price = ?, product_type = ?,
                   status = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND creator_id = ?''',
                (category_id, title_en, title_ar, description_en, description_ar,
                 round(price, 2), product_type, next_status, product_id, creator_id)
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return redirect(url_for('edit_creator_product', product_id=product_id, updated='1'))

    @app.route('/creator/product/<int:product_id>/delete', methods=['POST'])
    @creator_required
    def delete_creator_product(product_id):
        """Permanently delete only listings with no purchase or library history."""
        creator_id = int(session['user_id'])
        db = get_db()
        file_path = None
        try:
            db.execute('BEGIN IMMEDIATE')
            product = db.execute(
                'SELECT id, file_url FROM products WHERE id = ? AND creator_id = ?',
                (product_id, creator_id)
            ).fetchone()
            if product is None:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Product not found'}), 404
            has_sales_records = db.execute('SELECT 1 FROM orders WHERE product_id = ? LIMIT 1', (product_id,)).fetchone()
            has_library_records = db.execute('SELECT 1 FROM user_library WHERE product_id = ? LIMIT 1', (product_id,)).fetchone()
            has_reviews = db.execute('SELECT 1 FROM reviews WHERE product_id = ? LIMIT 1', (product_id,)).fetchone()
            if has_sales_records or has_library_records or has_reviews:
                db.rollback()
                return jsonify({
                    'status': 'error',
                    'message': 'This product has purchase or customer history and cannot be permanently deleted. Contact support if it must be removed.'
                }), 409
            file_path = os.path.abspath(product['file_url'] or '')
            upload_root = os.path.abspath(app.config['UPLOAD_FOLDER'])
            if not file_path.startswith(upload_root + os.sep):
                file_path = None
            db.execute('DELETE FROM products WHERE id = ? AND creator_id = ?', (product_id, creator_id))
            if file_path and db.execute(
                'SELECT 1 FROM products WHERE file_url = ? LIMIT 1', (product['file_url'],)
            ).fetchone():
                file_path = None
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        if file_path and os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError:
                current_app.logger.warning('Unable to remove product file for product %s', product_id)
        return jsonify({'status': 'success', 'message': 'Product deleted'})
    
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
            'message': 'Creator payouts are disabled in this version; no transfer was made.'
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
            'completed_orders': db.execute('SELECT COUNT(*) FROM orders WHERE payment_status = "completed"').fetchone()[0],
            'pending_products': db.execute('SELECT COUNT(*) FROM products WHERE status = "pending"').fetchone()[0],
            'pending_orders': db.execute('SELECT COUNT(*) FROM orders WHERE payment_status = "pending"').fetchone()[0],
            'open_messages': db.execute('SELECT COUNT(*) FROM messages WHERE status = "open"').fetchone()[0],
        }
        
        sales_by_currency = db.execute(
            '''SELECT COALESCE(currency, 'USD') AS currency, ROUND(SUM(price), 2) AS total
               FROM orders WHERE payment_status = 'completed'
               GROUP BY COALESCE(currency, 'USD') ORDER BY currency'''
        ).fetchall()

        recent_orders = db.execute(
            'SELECT o.*, p.title_en, p.title_ar, p.slug, u.username FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'JOIN users u ON o.customer_id = u.id '
            'ORDER BY o.created_at DESC LIMIT 10'
        ).fetchall()
        
        db.close()
        
        return render_template('admin/dashboard.html',
                             title='Admin Dashboard',
                             stats=stats,
                             sales_by_currency=sales_by_currency,
                             recent_orders=recent_orders)

    @app.route('/admin/messages')
    @admin_required
    def admin_messages():
        """List customer support messages for an administrator."""
        status = request.args.get('status', 'open').lower()
        if status not in {'open', 'closed', 'all'}:
            status = 'open'
        page = max(request.args.get('page', 1, type=int) or 1, 1)
        page_size = 50
        db = get_db()
        try:
            where_clause = ' WHERE status = ?' if status != 'all' else ''
            status_params = [status] if status != 'all' else []
            total_messages = db.execute(
                'SELECT COUNT(*) FROM messages' + where_clause, status_params
            ).fetchone()[0]
            total_pages = max(1, math.ceil(total_messages / page_size))
            page = min(page, total_pages)
            query = (
                'SELECT m.*, u.username AS sender_username, u.email AS sender_email '
                'FROM messages m LEFT JOIN users u ON u.id = m.sender_id'
            )
            if status != 'all':
                query += ' WHERE m.status = ?'
            query += ' ORDER BY m.created_at DESC, m.id DESC LIMIT ? OFFSET ?'
            messages = db.execute(query, status_params + [page_size, (page - 1) * page_size]).fetchall()
            open_count = db.execute('SELECT COUNT(*) FROM messages WHERE status = "open"').fetchone()[0]
        finally:
            db.close()
        return render_template(
            'admin/messages.html', title='Support Messages', messages=messages,
            current_status=status, open_count=open_count, page=page, total_pages=total_pages,
            total_messages=total_messages
        )

    @app.route('/admin/message/<int:message_id>/close', methods=['POST'])
    @admin_required
    def close_message(message_id):
        """Mark one support message as closed."""
        db = get_db()
        try:
            updated = db.execute(
                "UPDATE messages SET status = 'closed' WHERE id = ? AND status = 'open'",
                (message_id,)
            )
            db.commit()
            if updated.rowcount != 1:
                exists = db.execute('SELECT id FROM messages WHERE id = ?', (message_id,)).fetchone()
                if exists is None:
                    return jsonify({'status': 'error', 'message': 'Message not found'}), 404
                return jsonify({'status': 'error', 'message': 'Message is already closed'}), 409
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return jsonify({'status': 'success', 'message': 'Message marked as closed'})

    @app.route('/admin/orders')
    @admin_required
    def admin_orders():
        """قائمة طلبات الشراء وحالاتها."""
        status = request.args.get('status', 'pending').lower()
        if status not in {'pending', 'completed', 'rejected', 'all'}:
            status = 'pending'

        db = get_db()
        query = (
            'SELECT o.*, p.title_en, p.title_ar, p.slug, cu.username AS customer_username, '
            'cu.email AS customer_email, creator.username AS creator_username '
            'FROM orders o '
            'JOIN products p ON o.product_id = p.id '
            'JOIN users cu ON o.customer_id = cu.id '
            'JOIN users creator ON p.creator_id = creator.id'
        )
        params = []
        if status != 'all':
            query += ' WHERE o.payment_status = ?'
            params.append(status)
        query += ' ORDER BY o.created_at DESC, o.id DESC LIMIT 250'
        orders = db.execute(query, params).fetchall()
        pending_count = db.execute(
            'SELECT COUNT(*) FROM orders WHERE payment_status = "pending"'
        ).fetchone()[0]
        db.close()

        return render_template(
            'admin/orders.html',
            title='Manage Orders',
            orders=orders,
            current_status=status,
            pending_count=pending_count,
        )

    @app.route('/admin/order/<int:order_id>/confirm', methods=['POST'])
    @admin_required
    def confirm_order(order_id):
        """Confirm a manually verified payment and fulfill it exactly once."""
        payload = request.get_json(silent=True) or request.form
        transaction_id = (payload.get('transaction_id') or '').strip()
        if len(transaction_id) > 160:
            return jsonify({'status': 'error', 'message': 'Transaction reference is too long'}), 400

        db = get_db()
        try:
            db.execute('BEGIN IMMEDIATE')
            order = db.execute(
                '''SELECT o.*, p.creator_id, p.status AS product_status
                   FROM orders o JOIN products p ON p.id = o.product_id
                   WHERE o.id = ?''',
                (order_id,)
            ).fetchone()
            if order is None:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Order not found'}), 404
            if order['payment_status'] == 'completed':
                db.commit()
                return jsonify({'status': 'success', 'message': 'Order was already confirmed', 'already_completed': True})
            if order['payment_status'] != 'pending':
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Only pending orders can be confirmed'}), 409
            if order['product_status'] != 'published':
                db.rollback()
                return jsonify({'status': 'error', 'message': 'The product is not currently available'}), 409
            if order['creator_id'] == order['customer_id']:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'A creator cannot purchase their own product'}), 409

            order_currency = order['currency'] or config[config_name].DEFAULT_CURRENCY
            wallet = db.execute(
                'SELECT currency FROM wallets WHERE creator_id = ?', (order['creator_id'],)
            ).fetchone()
            wallet_currency = (wallet['currency'] if wallet and wallet['currency'] else config[config_name].DEFAULT_CURRENCY)
            if order_currency != wallet_currency:
                db.rollback()
                return jsonify({
                    'status': 'error',
                    'message': 'Order currency does not match the creator ledger currency; manual reconciliation is required.'
                }), 409

            gross_price = round(float(order['price']), 2)
            commission = (
                round(float(order['platform_commission']), 2)
                if order['platform_commission'] is not None
                else round(gross_price * config[config_name].PLATFORM_COMMISSION, 2)
            )
            creator_earnings = (
                round(float(order['creator_earnings']), 2)
                if order['creator_earnings'] is not None
                else round(gross_price - commission, 2)
            )

            updated = db.execute(
                '''UPDATE orders SET payment_status = 'completed', transaction_id = ?
                   WHERE id = ? AND payment_status = 'pending' ''',
                (transaction_id or None, order_id)
            )
            if updated.rowcount != 1:
                db.rollback()
                return jsonify({'status': 'error', 'message': 'Order status changed; refresh and try again'}), 409

            db.execute(
                'INSERT OR IGNORE INTO user_library (customer_id, product_id) VALUES (?, ?)',
                (order['customer_id'], order['product_id'])
            )
            db.execute(
                '''INSERT INTO wallets (creator_id, balance, total_earnings)
                   VALUES (?, ?, ?)
                   ON CONFLICT(creator_id) DO UPDATE SET
                       balance = COALESCE(wallets.balance, 0) + excluded.balance,
                       total_earnings = COALESCE(wallets.total_earnings, 0) + excluded.total_earnings,
                       updated_at = CURRENT_TIMESTAMP''',
                (order['creator_id'], creator_earnings, creator_earnings)
            )
            db.execute('UPDATE products SET sales_count = COALESCE(sales_count, 0) + 1 WHERE id = ?',
                       (order['product_id'],))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        return jsonify({
            'status': 'success',
            'message': 'Payment confirmed; the product was added to the customer library.',
            'order_id': order_id,
        })

    @app.route('/admin/order/<int:order_id>/reject', methods=['POST'])
    @admin_required
    def reject_order(order_id):
        """Reject a pending manual purchase request without granting access."""
        db = get_db()
        try:
            updated = db.execute(
                "UPDATE orders SET payment_status = 'rejected' WHERE id = ? AND payment_status = 'pending'",
                (order_id,)
            )
            db.commit()
            if updated.rowcount != 1:
                exists = db.execute('SELECT id, payment_status FROM orders WHERE id = ?', (order_id,)).fetchone()
                if exists is None:
                    return jsonify({'status': 'error', 'message': 'Order not found'}), 404
                return jsonify({'status': 'error', 'message': 'Only pending orders can be rejected'}), 409
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return jsonify({'status': 'success', 'message': 'Purchase request rejected', 'order_id': order_id})
    
    @app.route('/admin/products')
    @admin_required
    def admin_products():
        """مراجعة المنتجات"""
        db = get_db()
        
        status = request.args.get('status', 'pending')
        products = db.execute(
            'SELECT p.*, u.username, c.name_en AS category_name_en, c.name_ar AS category_name_ar FROM products p '
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
    
    def _review_pending_product(product_id, new_status):
        db = get_db()
        try:
            updated = db.execute(
                'UPDATE products SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = ?',
                (new_status, product_id, 'pending')
            )
            if updated.rowcount != 1:
                db.rollback()
                product = db.execute('SELECT id FROM products WHERE id = ?', (product_id,)).fetchone()
                if product is None:
                    return jsonify({'status': 'error', 'message': 'Product not found'}), 404
                return jsonify({'status': 'error', 'message': 'Only pending products can be reviewed'}), 409
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return None

    @app.route('/admin/product/<int:product_id>/approve', methods=['POST'])
    @admin_required
    def approve_product(product_id):
        """Approve a listing only while it is pending review."""
        response = _review_pending_product(product_id, 'published')
        return response if response else jsonify({'status': 'success', 'message': 'Product approved'})
    
    @app.route('/admin/product/<int:product_id>/reject', methods=['POST'])
    @admin_required
    def reject_product(product_id):
        """Reject a listing only while it is pending review."""
        response = _review_pending_product(product_id, 'rejected')
        return response if response else jsonify({'status': 'success', 'message': 'Product rejected'})
    
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
        processed_by_currency = db.execute(
            '''SELECT COALESCE(currency, 'USD') AS currency, ROUND(SUM(amount), 2) AS total
               FROM withdrawals WHERE status = 'completed'
               GROUP BY COALESCE(currency, 'USD') ORDER BY currency'''
        ).fetchall()
        
        db.close()
        
        return render_template('admin/withdrawals.html',
                             title='Manage Withdrawals',
                             withdrawals=withdrawals,
                             processed_by_currency=processed_by_currency)
    
    @app.route('/admin/withdrawal/<int:withdrawal_id>/process', methods=['POST'])
    @admin_required
    def process_withdrawal(withdrawal_id):
        """Read-only payout safety guard; no withdrawal status can be marked paid here."""
        return jsonify({
            'status': 'disabled',
            'message': 'Creator payouts are disabled in this version; no transfer was made.'
        }), 503
    
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
