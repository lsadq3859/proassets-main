(() => {
    const copy = {
        ar: {
            nav_home: 'الرئيسية', nav_market: 'المتجر', nav_categories: 'التصنيفات', nav_about: 'من نحن', nav_contact: 'تواصل معنا', nav_account: 'حسابي', nav_login: 'تسجيل الدخول', nav_signup: 'إنشاء حساب',
            hero_eyebrow: 'مرحباً بك في ProAssets', hero_line1: 'أصول رقمية حقيقية', hero_line2: 'لنجاح أكبر',
            hero_description: 'اكتشف منتجات رقمية مختارة من منشئين مستقلين — من القوالب والكتب إلى أدوات التصميم والعمل.',
            hero_primary: 'تصفح المتجر', hero_secondary: 'اعرف المزيد', trust_1: 'ملفات رقمية محمية', trust_2: 'تصفح سهل وسريع', trust_3: 'واجهة عربية وإنجليزية',
            benefit_1_title: 'أصول رقمية متنوعة', benefit_1_copy: 'منتجات لمختلف احتياجاتك', benefit_2_title: 'تجربة بسيطة', benefit_2_copy: 'تصفح واكتشف بسهولة', benefit_3_title: 'دعم المنشئين', benefit_3_copy: 'سوق يربط المبدعين بالعملاء', benefit_4_title: 'بالعربية والإنجليزية', benefit_4_copy: 'اختر اللغة المناسبة لك',
            featured_title: 'أحدث المنتجات', featured_subtitle: 'اكتشف إضافات جديدة إلى مكتبتك الرقمية', view_all: 'عرض الكل', featured_badge: 'مختار', empty_products_title: 'قريباً: منتجات مميزة', empty_products_copy: 'نعمل على تجهيز مكتبة من الأصول الرقمية المفيدة.',
            categories_title: 'تسوق حسب التصنيف', categories_subtitle: 'ابدأ من المجال الذي تبحث عنه', cta_title: 'هل أنت منشئ منتجات رقمية؟', cta_copy: 'اعرض أعمالك على ProAssets وابدأ ببناء جمهورك.', cta_button: 'ابدأ البيع', footer_rights: 'جميع الحقوق محفوظة.', footer_privacy: 'الخصوصية', footer_terms: 'الشروط',
            page_title: 'ProAssets — سوق الأصول الرقمية', menu_open: 'فتح القائمة', menu_close: 'إغلاق القائمة', cart_label: 'سلة التسوق',
        },
        en: {
            nav_home: 'Home', nav_market: 'Marketplace', nav_categories: 'Categories', nav_about: 'About', nav_contact: 'Contact', nav_account: 'Account', nav_login: 'Sign in', nav_signup: 'Create account',
            hero_eyebrow: 'Welcome to ProAssets', hero_line1: 'Real digital assets', hero_line2: 'for greater success',
            hero_description: 'Discover hand-picked digital products from independent creators — from templates and ebooks to tools for design and work.',
            hero_primary: 'Explore marketplace', hero_secondary: 'Learn more', trust_1: 'Protected digital files', trust_2: 'Easy, quick browsing', trust_3: 'Arabic and English',
            benefit_1_title: 'A range of digital assets', benefit_1_copy: 'Useful products for many needs', benefit_2_title: 'A simple experience', benefit_2_copy: 'Browse and discover with ease', benefit_3_title: 'Support creators', benefit_3_copy: 'Connecting makers and customers', benefit_4_title: 'Arabic and English', benefit_4_copy: 'Choose the language that suits you',
            featured_title: 'Latest products', featured_subtitle: 'Find a new addition to your digital library', view_all: 'View all', featured_badge: 'Featured', empty_products_title: 'Featured products coming soon', empty_products_copy: 'We are preparing a library of useful digital assets.',
            categories_title: 'Shop by category', categories_subtitle: 'Start with the area you need', cta_title: 'Create digital products?', cta_copy: 'Showcase your work on ProAssets and start growing your audience.', cta_button: 'Start selling', footer_rights: 'All rights reserved.', footer_privacy: 'Privacy', footer_terms: 'Terms',
            page_title: 'ProAssets — Digital Assets Marketplace', menu_open: 'Open menu', menu_close: 'Close menu', cart_label: 'Shopping cart',
        }
    };

    function applyLanguage(language) {
        const lang = language === 'en' ? 'en' : 'ar';
        const direction = lang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.lang = lang;
        document.documentElement.dir = direction;
        document.title = copy[lang].page_title;
        document.querySelectorAll('[data-t]').forEach((node) => {
            const key = node.dataset.t;
            if (copy[lang][key]) node.textContent = copy[lang][key];
        });
        document.querySelectorAll('[data-en][data-ar]').forEach((node) => {
            node.textContent = node.dataset[lang] || node.dataset.en || '';
        });
        const toggle = document.getElementById('languageToggle');
        if (toggle) {
            toggle.textContent = lang === 'ar' ? 'English' : 'العربية';
            toggle.setAttribute('aria-label', lang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية');
        }
        const cart = document.querySelector('.pa-icon-link');
        if (cart) { cart.title = copy[lang].cart_label; cart.setAttribute('aria-label', copy[lang].cart_label); }
        const menuButton = document.getElementById('menuToggle');
        if (menuButton) menuButton.setAttribute('aria-label', copy[lang].menu_open);
        try { localStorage.setItem('proassets-language', lang); } catch (_) { /* storage may be disabled */ }
    }

    document.addEventListener('DOMContentLoaded', () => {
        let saved = 'ar';
        try { saved = localStorage.getItem('proassets-language') || 'ar'; } catch (_) { /* storage may be disabled */ }
        applyLanguage(saved);

        const languageToggle = document.getElementById('languageToggle');
        languageToggle?.addEventListener('click', () => {
            const next = document.documentElement.lang === 'ar' ? 'en' : 'ar';
            applyLanguage(next);
        });

        const menuButton = document.getElementById('menuToggle');
        const menu = document.getElementById('primaryMenu');
        menuButton?.addEventListener('click', () => {
            const open = menu.classList.toggle('is-open');
            menuButton.setAttribute('aria-expanded', String(open));
            menuButton.setAttribute('aria-label', copy[document.documentElement.lang][open ? 'menu_close' : 'menu_open']);
        });
        menu?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
            menu.classList.remove('is-open');
            menuButton?.setAttribute('aria-expanded', 'false');
        }));
    });
})();
