// ===== ProAssets - Main JavaScript =====

// ===== Utility Functions =====

/**
 * إظهار رسالة نجاح
 */
function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success fade-in';
    alert.textContent = '✅ ' + message;
    
    document.body.insertBefore(alert, document.body.firstChild);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

/**
 * إظهار رسالة خطأ
 */
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger fade-in';
    alert.textContent = '❌ ' + message;
    
    document.body.insertBefore(alert, document.body.firstChild);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

/**
 * إظهار رسالة تحذير
 */
function showWarning(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-warning fade-in';
    alert.textContent = '⚠️ ' + message;
    
    document.body.insertBefore(alert, document.body.firstChild);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

/**
 * تحويل البيانات إلى JSON آمن
 */
function safeJsonify(data) {
    try {
        return JSON.stringify(data);
    } catch (e) {
        console.error('JSON stringify error:', e);
        return null;
    }
}

/**
 * إرسال طلب API
 */
async function apiRequest(url, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
            options.headers['X-CSRF-Token'] = csrfToken;
        }
        
        if (data) {
            options.body = safeJsonify(data);
        }
        
        const response = await fetch(url, options);
        const result = await response.json();
        
        return {
            ok: response.ok,
            status: response.status,
            data: result
        };
    } catch (error) {
        console.error('API request error:', error);
        return {
            ok: false,
            status: 0,
            data: { message: 'Network error' }
        };
    }
}

// ===== Cart Functions =====

/**
 * إضافة منتج للسلة
 */
async function addToCart(productId) {
    const response = await apiRequest(`/cart/add/${productId}`, 'POST');
    
    if (response.ok) {
        showSuccess('Product added to cart!');
    } else {
        showError(response.data.message || 'Failed to add to cart');
    }
}

/**
 * إزالة منتج من السلة
 */
async function removeFromCart(productId) {
    if (!confirm('Remove this item from cart?')) {
        return;
    }
    
    const response = await apiRequest(`/cart/remove/${productId}`, 'POST');
    
    if (response.ok) {
        showSuccess('Item removed');
        location.reload();
    } else {
        showError('Failed to remove item');
    }
}

// ===== Product Functions =====

/**
 * تحميل المنتج
 */
function downloadProduct(productId) {
    const id = Number(productId);
    if (!Number.isSafeInteger(id) || id <= 0) {
        showError('This download link is invalid.');
        return;
    }
    // The server enforces sign-in and library entitlement before sending the private file.
    window.location.assign(`/download/${id}`);
}

// ===== Search & Filter =====

/**
 * البحث عن المنتجات
 */
function searchProducts() {
    const query = document.getElementById('searchInput')?.value || '';
    if (query.length > 2) {
        window.location.href = `/products?search=${encodeURIComponent(query)}`;
    }
}

/**
 * تصفية المنتجات حسب الفئة
 */
function filterByCategory(categoryId) {
    if (categoryId) {
        window.location.href = `/products?category=${categoryId}`;
    }
}

// ===== Form Validation =====

/**
 * التحقق من صيغة البريد
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * التحقق من قوة كلمة المرور
 */
function getPasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    return strength;
}

// ===== User Session =====

/**
 * تسجيل الخروج
 */
async function logout() {
    if (!confirm('Are you sure you want to logout?')) return;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        showError('Refresh the page and try again.');
        return;
    }
    try {
        const response = await fetch('/logout', {method: 'POST', headers: {'X-CSRF-Token': csrfToken}});
        if (!response.ok) throw new Error('Unable to log out. Please try again.');
        window.location.assign('/');
    } catch (error) {
        showError(error.message || 'Network error. Please try again.');
    }
}

// ===== UI Helpers =====

/**
 * التبديل بين التبويبات
 */
function switchTab(tabName) {
    // إخفاء جميع التبويبات
    document.querySelectorAll('[data-tab-content]').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // إظهار التبويب المختار
    const tab = document.querySelector(`[data-tab-content="${tabName}"]`);
    if (tab) {
        tab.style.display = 'block';
    }
    
    // تحديث الأزرار النشطة
    document.querySelectorAll('[data-tab-btn]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelector(`[data-tab-btn="${tabName}"]`)?.classList.add('active');
}

/**
 * فتح/إغلاق Modal
 */
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    }
}

/**
 * تنسيق السعر
 */
function formatPrice(price, currency = 'USD') {
    const amount = Number(price);
    const currencyCode = String(currency || 'USD').toUpperCase();
    if (!Number.isFinite(amount)) return `${currencyCode} 0.00`;
    try {
        return new Intl.NumberFormat(document.documentElement.lang || 'en', {
            style: 'currency', currency: currencyCode, currencyDisplay: 'code'
        }).format(amount);
    } catch (_) {
        return `${currencyCode} ${amount.toFixed(2)}`;
    }
}

/**
 * تنسيق التاريخ
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// ===== Event Listeners =====

document.addEventListener('DOMContentLoaded', function() {
    // إغلاق الـ Modals عند الضغط خارجها
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
    
    // البحث عند الضغط على Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchProducts();
            }
        });
    }
});

// ===== Debug =====

function debug(message, data = null) {
    if (console) {
        console.log(`[ProAssets] ${message}`, data || '');
    }
}
