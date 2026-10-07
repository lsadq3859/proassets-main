(() => {
    const pairs = [
        // Shared navigation and actions
        ['Home', 'الرئيسية'], ['Products', 'المنتجات'], ['About', 'من نحن'], ['Contact', 'تواصل معنا'],
        ['Login', 'تسجيل الدخول'], ['Sign in', 'تسجيل الدخول'], ['Logout', 'تسجيل الخروج'],
        ['Dashboard', 'لوحة التحكم'], ['My Products', 'منتجاتي'], ['Earnings', 'الأرباح'], ['Account', 'الحساب'],
        ['Orders', 'الطلبات'], ['Users', 'المستخدمون'], ['Withdrawals', 'طلبات السحب'], ['Admin', 'الإدارة'],
        ['Library', 'المكتبة'], ['My Library', 'مكتبتي'], ['Shop', 'المتجر'], ['Cart', 'السلة'],
        ['About ProAssets', 'عن ProAssets'], ['Privacy Policy', 'سياسة الخصوصية'], ['Terms of Service', 'شروط الاستخدام'],
        ['Browse Products', 'تصفح المنتجات'], ['Browse products', 'تصفح المنتجات'], ['Browse the marketplace to find digital products.', 'تصفح السوق للعثور على منتجات رقمية.'],
        ['Search', 'بحث'], ['Search products...', 'ابحث عن منتجات...'], ['View', 'عرض'], ['View All →', 'عرض الكل ←'],
        ['Back to Home', 'العودة إلى الرئيسية'], ['Back to home', 'العودة إلى الرئيسية'], ['Go Home', 'العودة إلى الرئيسية'],
        ['Cancel', 'إلغاء'], ['Save Changes', 'حفظ التغييرات'], ['Download', 'تنزيل'], ['Remove', 'إزالة'], ['Edit', 'تعديل'], ['Delete', 'حذف'],
        ['Your form session expired. Refresh the page and try again.', 'انتهت صلاحية الجلسة. حدّث الصفحة ثم حاول مرة أخرى.'],
        ['Total purchase requests', 'إجمالي طلبات الشراء'], ['Completed Orders', 'الطلبات المكتملة'], ['Recent Purchases', 'طلبات الشراء الأخيرة'], ['Total Purchases', 'إجمالي المشتريات'], ['No Purchases Yet', 'لا توجد مشتريات بعد'], ['Start exploring our amazing products and make your first purchase!', 'اكتشف منتجاتنا وابدأ أول عملية شراء لك!'], ['Completed spend by currency', 'الإنفاق المكتمل حسب العملة'], ['Order currency does not match the creator ledger currency; manual reconciliation is required.', 'عملة الطلب لا تطابق عملة سجل المنشئ؛ يلزم إجراء تسوية يدوية.'],
        ['© 2026 ProAssets. All rights reserved. | Admin Panel', '© 2026 ProAssets. جميع الحقوق محفوظة. | لوحة الإدارة'], ['© 2026 ProAssets.', '© 2026 ProAssets.'], ['All rights reserved.', 'جميع الحقوق محفوظة.'], ['All orders', 'كل الطلبات'], ['Contact Us', 'تواصل معنا'], ['My Dashboard', 'لوحة التحكم'], ['Edit Product', 'تعديل المنتج'], ['Upload Product — ProAssets', 'رفع منتج — ProAssets'], ['Course', 'دورة'], ['Design', 'تصميم'], ['Ebook', 'كتاب إلكتروني'], ['Software', 'برنامج'], ['Template', 'قالب'], ['Other', 'أخرى'], ['اسم المنتج (بالعربية) *', 'Product name (Arabic) *'], ['الوصف (بالعربية)', 'Description (Arabic)'], ['. Published or rejected listings return to review after edits; existing buyers retain authorized downloads.', '. بعد تعديل القوائم المنشورة أو المرفوضة، تعود إلى المراجعة؛ ويظل التنزيل المصرح به متاحاً للمشترين السابقين.'], ['PNG, JPEG or WebP; maximum 2 MB.', 'PNG أو JPEG أو WebP؛ بحد أقصى 2 ميغابايت.'], ['Recorded balances summarize confirmed orders. They are not paid funds, and this version does not provide a withdrawal or automatic payout function.', 'تلخص الأرصدة المسجلة الطلبات المؤكدة، لكنها ليست أموالاً مدفوعة. لا يتيح هذا الإصدار السحب أو صرف الأرباح آلياً.'], ['Send us your question or feedback. Messages are delivered to the ProAssets support inbox for administrator review.', 'أرسل سؤالك أو ملاحظاتك. تصل الرسائل إلى صندوق دعم ProAssets لمراجعتها من الإدارة.'], ['⭐ N/A', '⭐ غير متاح'], ['⭐ Not rated', '⭐ لم يُقيّم بعد'],
        ['Your cart is empty', 'سلتك فارغة'], ['No valid products in your cart', 'لا توجد منتجات صالحة في سلتك'],
        ['No purchasable products were found. Creators cannot purchase their own products.', 'لم نعثر على منتجات قابلة للشراء. لا يمكن للمنشئ شراء منتجاته الخاصة.'],
        ['Purchase request submitted. Contact support to complete manual payment.', 'تم إرسال طلب الشراء. تواصل مع الدعم لإتمام الدفع اليدوي.'],
        ['Manual payment requested for paid products; free products are now in your library.', 'تم إرسال طلب الدفع للمنتجات المدفوعة، وأُضيفت المنتجات المجانية إلى مكتبتك.'],
        ['Free products have been added to your library.', 'أُضيفت المنتجات المجانية إلى مكتبتك.'],
        ['Payment confirmed; the product was added to the customer library.', 'تم تأكيد الدفع وإضافة المنتج إلى مكتبة العميل.'],
        ['Purchase request rejected', 'تم رفض طلب الشراء'], ['Order was already confirmed', 'سبق تأكيد هذا الطلب'],
        ['Only pending orders can be confirmed', 'يمكن تأكيد الطلبات المعلقة فقط'], ['Only pending orders can be rejected', 'يمكن رفض الطلبات المعلقة فقط'],
        ['The product is not currently available', 'المنتج غير متاح حالياً'], ['Order not found', 'لم يتم العثور على الطلب'],
        ['Transaction reference is too long', 'مرجع المعاملة أطول من المسموح'], ['Order status changed; refresh and try again', 'تغيرت حالة الطلب. حدّث الصفحة ثم حاول مرة أخرى'],
        ['Invalid credentials', 'بيانات الدخول غير صحيحة'], ['Email already registered', 'البريد الإلكتروني مسجل بالفعل'], ['Username already taken', 'اسم المستخدم مستخدم بالفعل'],
        ['Registration fields must be text', 'يجب أن تكون حقول التسجيل نصية'], ['Username must be 3 to 32 letters, numbers, dots, hyphens or underscores', 'يجب أن يتراوح اسم المستخدم بين 3 و32 حرفاً أو رقماً أو نقطة أو شرطة أو شرطة سفلية'], ['Enter a valid email address', 'أدخل عنوان بريد إلكتروني صالحاً'], ['Password must be between 8 and 256 characters', 'يجب أن تتراوح كلمة المرور بين 8 و256 حرفاً'], ['Names must be 100 characters or fewer', 'يجب ألا يتجاوز طول الاسم 100 حرف'], ['Choose a valid account type', 'اختر نوع حساب صالحاً'], ['Email or username already registered', 'البريد الإلكتروني أو اسم المستخدم مسجل بالفعل'],
        ['Account is disabled', 'الحساب معطل'], ['Missing required fields', 'يرجى تعبئة الحقول المطلوبة'], ['Password must be at least 8 characters', 'يجب ألا تقل كلمة المرور عن 8 أحرف'],
        ['Account created successfully', 'تم إنشاء الحساب بنجاح'], ['Logged in successfully', 'تم تسجيل الدخول بنجاح'], ['Product added to cart', 'تمت إضافة المنتج إلى السلة'],
        ['Product already in cart', 'المنتج موجود في السلة بالفعل'], ['Product uploaded successfully', 'تم رفع المنتج بنجاح'],
        ['Product added to cart! 🎉', 'تمت إضافة المنتج إلى السلة! 🎉'], ['Product approved.', 'تمت الموافقة على المنتج.'], ['Product rejected.', 'تم رفض المنتج.'],
        ['Unable to update product status', 'تعذر تحديث حالة المنتج'], ['Product not found', 'لم يتم العثور على المنتج'], ['Only pending products can be reviewed', 'يمكن مراجعة المنتجات المعلقة فقط'], ['A network error occurred. Please try again.', 'حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.'],
        ['First', 'الأولى'], ['Previous', 'السابقة'], ['Next', 'التالية'], ['Last', 'الأخيرة'],
        ['All Status', 'كل الحالات'], ['All Categories', 'كل التصنيفات'], ['All Types', 'كل الأنواع'],
        ['Pending Review', 'بانتظار المراجعة'], ['Published', 'منشور'], ['Rejected', 'مرفوض'], ['Draft', 'مسودة'],
        ['Pending', 'معلّق'], ['Completed', 'مكتمل'], ['Processing', 'قيد المعالجة'], ['Active', 'نشط'], ['Inactive', 'غير نشط'],
        ['Customer', 'العميل'], ['Creator', 'المنشئ'], ['Product', 'المنتج'], ['Product Name', 'اسم المنتج'],
        ['Category', 'التصنيف'], ['Price', 'السعر'], ['Amount', 'المبلغ'], ['Status', 'الحالة'], ['Actions', 'الإجراءات'],
        ['Date', 'التاريخ'], ['Joined', 'تاريخ الانضمام'], ['Sales', 'المبيعات'], ['Rating', 'التقييم'],
        ['Description', 'الوصف'], ['Creator:', 'المنشئ:'], ['Payment reference (optional)', 'مرجع الدفع (اختياري)'],
        ['© 2024 ProAssets. All rights reserved.', '© 2026 ProAssets. جميع الحقوق محفوظة.'],
        ['© 2026 ProAssets. All rights reserved.', '© 2026 ProAssets. جميع الحقوق محفوظة.'],

        // Additional server response strings
        ['A creator cannot purchase their own product', 'لا يمكن للمنشئ شراء منتجه الخاص'], ['Account not found', 'لم يتم العثور على الحساب'], ['Account updated', 'تم تحديث الحساب'], ['Added to cart', 'تمت الإضافة إلى السلة'], ['Configure a support phone number or email before sending paid purchase requests.', 'اضبط رقم هاتف الدعم أو البريد الإلكتروني قبل إرسال طلبات الشراء المدفوعة.'], ['Confirmation fields must be text', 'يجب أن تكون حقول التأكيد نصية'], ['Email and password are required', 'البريد الإلكتروني وكلمة المرور مطلوبان'], ['Email or password is invalid', 'البريد الإلكتروني أو كلمة المرور غير صالحين'], ['Invalid file type or filename', 'نوع الملف أو اسمه غير صالح'], ['Message is already closed', 'الرسالة مغلقة بالفعل'], ['Message not found', 'لم يتم العثور على الرسالة'], ['No file provided', 'لم يتم تقديم ملف'], ['No profile image is set', 'لم يتم تعيين صورة للملف الشخصي'], ['Password fields must be text', 'يجب أن تكون حقول كلمة المرور نصية'], ['Product approved', 'تمت الموافقة على المنتج'], ['Product rejected', 'تم رفض المنتج'], ['Product is not available', 'المنتج غير متاح'], ['Profile image is unavailable', 'صورة الملف الشخصي غير متاحة'], ['Your cart has reached the 100-item limit', 'وصلت سلتك إلى الحد الأقصى وهو 100 منتج'], ['Item removed', 'تمت إزالة المنتج'], ['Failed to add to cart', 'تعذرت إضافة المنتج إلى السلة'], ['Failed to remove item', 'تعذرت إزالة المنتج'], ['This download link is invalid.', 'رابط التنزيل غير صالح.'], ['Are you sure you want to logout?', 'هل أنت متأكد من تسجيل الخروج؟'], ['Remove this item from cart?', 'هل تريد إزالة هذا المنتج من السلة؟'], ['Unable to log out. Please try again.', 'تعذر تسجيل الخروج. يرجى المحاولة مرة أخرى.'], ['Refresh the page and try again.', 'حدّث الصفحة ثم حاول مرة أخرى.'], ['Network error. Please try again.', 'حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.'],

        // Public pages
        ['Empowering creators and connecting buyers with digital excellence', 'تمكين المنشئين وربطهم بالمشترين عبر منتجات رقمية متميزة'],
        ['Our Story', 'قصتنا'],
        ['ProAssets was founded with a simple mission: to create a global marketplace where creative professionals can share their work and earn fairly.', 'تأسست ProAssets بهدف بسيط: إنشاء سوق عالمي يتيح للمحترفين المبدعين عرض أعمالهم وتحقيق دخل عادل.'],
        ["We believe that digital creators deserve a platform that respects their work, protects their interests, and provides them with the tools to succeed.", 'نؤمن بأن منشئي المنتجات الرقمية يستحقون منصة تحترم أعمالهم وتحمي مصالحهم وتوفر لهم أدوات النجاح.'],
        ["Whether you're a writer, designer, developer, or entrepreneur, ProAssets is your gateway to a worldwide audience of buyers looking for quality digital assets.", 'سواء كنت كاتباً أو مصمماً أو مطوراً أو رائد أعمال، تمنحك ProAssets فرصة الوصول إلى مشترين حول العالم يبحثون عن أصول رقمية عالية الجودة.'],
        ['Our Mission', 'رسالتنا'],
        ['To build a fair, transparent, and secure marketplace that empowers creators to monetize their digital assets while providing buyers with access to high-quality products at reasonable prices.', 'بناء سوق عادل وشفاف وآمن يمكّن المنشئين من تحقيق دخل من أصولهم الرقمية، ويوفر للمشترين منتجات عالية الجودة بأسعار مناسبة.'],
        ['Why Choose ProAssets?', 'لماذا تختار ProAssets؟'], ['Arabic & English', 'العربية والإنجليزية'], ['Browse and manage products in Arabic or English; listing prices retain the seller-set currency', 'تصفح وأدر المنتجات بالعربية أو الإنجليزية؛ وتبقى الأسعار بعملة البائع المحددة'],
        ['Fair Commission', 'عمولة عادلة'], ['Creator earnings are recorded at 80% after commission; payouts are currently disabled and balances are not paid funds', 'تُسجّل أرباح المنشئ بنسبة 80٪ بعد العمولة؛ الصرف متوقف حالياً والأرصدة ليست أموالاً مدفوعة'],
        ['Protected Downloads', 'تنزيلات محمية'], ['Product files are stored privately; authorized downloads require a library entitlement', 'تُخزن ملفات المنتجات بشكل خاص؛ ويتطلب التنزيل المصرح به استحقاقاً في المكتبة'],
        ['Sales Records', 'سجلات المبيعات'], ['Review completed sales and recorded earnings from your creator dashboard', 'راجع المبيعات المكتملة والأرباح المسجلة من لوحة المنشئ'],
        ['Clear Delivery Status', 'حالة تسليم واضحة'], ['Free products are delivered immediately; paid requests remain pending until manual payment is verified by an administrator', 'تُتاح المنتجات المجانية فوراً؛ وتبقى الطلبات المدفوعة معلقة حتى يتحقق المشرف من الدفع اليدوي'],
        ['Manual Payment Support', 'دعم الدفع اليدوي'], ['Paid orders are completed outside the app after you contact support; no online payment gateway is enabled', 'تُستكمل الطلبات المدفوعة خارج التطبيق بعد التواصل مع الدعم؛ ولا توجد بوابة دفع إلكترونية مفعلة'], ['Our Core Values', 'قيمنا الأساسية'],
        ['Integrity', 'النزاهة'], ['We operate with transparency and honesty in all our dealings', 'نعمل بشفافية وصدق في جميع تعاملاتنا'],
        ['Quality', 'الجودة'], ['We maintain high standards for all products on our platform', 'نحافظ على معايير عالية لجميع المنتجات في منصتنا'],
        ['Innovation', 'الابتكار'], ['We constantly improve our platform with new features and tools', 'نطوّر منصتنا باستمرار بميزات وأدوات جديدة'],
        ['Community', 'المجتمع'], ['We foster a supportive community of creators and buyers', 'نعزز مجتمعاً داعماً من المنشئين والمشترين'],
        ['How the marketplace works', 'كيف يعمل السوق'], ['1. Creators submit products', '1. يرسل المنشئون منتجاتهم'], ['Creators provide product details in English and Arabic. Listings are reviewed before publication.', 'يقدم المنشئون بيانات المنتجات بالإنجليزية والعربية. وتُراجع القوائم قبل النشر.'], ['2. Customers submit requests', '2. يرسل العملاء طلبات الشراء'], ['Free products are added to a library immediately. Paid products create a pending request; the app does not collect money.', 'تُضاف المنتجات المجانية إلى المكتبة فوراً. أما المنتجات المدفوعة فتنشئ طلباً معلقاً؛ ولا يجمع التطبيق أي أموال.'], ['3. Admins verify manual payment', '3. يتحقق المشرفون من الدفع اليدوي'], ['An administrator confirms receipt before a paid product is added to the customer library. Creator payouts are not enabled.', 'يؤكد المشرف استلام المبلغ قبل إضافة المنتج المدفوع إلى مكتبة العميل. صرف أرباح المنشئين غير مفعل.'],
        ['Ready to Join Us?', 'هل أنت مستعد للانضمام؟'], ['Start selling or buying digital assets today', 'ابدأ اليوم ببيع الأصول الرقمية أو شرائها'], ['Get Started', 'ابدأ الآن'],
        ['Contact us', 'تواصل معنا'], ['Send us your question or feedback.', 'أرسل إلينا سؤالك أو ملاحظاتك.'], ['Subject', 'الموضوع'], ['Message', 'الرسالة'], ['Send message', 'إرسال الرسالة'], ['Back to home', 'العودة إلى الرئيسية'],

        // Login, registration, cart and checkout
        ['Email Address', 'البريد الإلكتروني'], ['Password', 'كلمة المرور'], ['Username', 'اسم المستخدم'], ['First Name', 'الاسم الأول'], ['Last Name', 'اسم العائلة'],
        ["Don't have an account?", 'ليس لديك حساب؟'], ['Sign up here', 'سجّل من هنا'], ['Already have an account?', 'لديك حساب بالفعل؟'], ['Login here', 'سجّل الدخول من هنا'],
        ['Create Account', 'إنشاء حساب'], ['💎 Create Account', '💎 إنشاء حساب'], ['Must be at least 8 characters', 'يجب ألا تقل كلمة المرور عن 8 أحرف'],
        ['Account Type', 'نوع الحساب'], ['Customer (Buy Products)', 'عميل (شراء المنتجات)'], ['Creator (Sell Products)', 'منشئ (بيع المنتجات)'],
        ['Shopping Cart', 'سلة التسوق'], ['Total:', 'الإجمالي:'], ['Continue to checkout', 'متابعة إلى إتمام الطلب'], ['Your cart is empty', 'سلتك فارغة'],
        ['Manual Checkout', 'إتمام الطلب يدوياً'], ['Manual purchase request', 'طلب شراء يدوي'],
        ['طلب شراء يدوي', 'Manual purchase request'], ['لا يتم تحصيل أي مبلغ تلقائيًا. اضغط إرسال الطلب لإنشاء طلب معلّق، ثم تواصل معنا عبر الأيقونات لإتمام الدفع يدويًا.', 'No money is collected automatically. Submit a request, then contact us using the icons to complete payment manually.'],
        ['إرسال طلب الشراء', 'Submit purchase request'], ['تم إرسال الطلب', 'Request submitted'], ['تعذر إرسال الطلب. حاول مرة أخرى.', 'Unable to submit the request. Please try again.'], ['العودة إلى السلة', 'Return to cart'], ['اتصال', 'Call'], ['واتساب', 'WhatsApp'], ['بريد إلكتروني', 'Email'],
        ['Use 0.00 for a free product. Payments are currently handled manually.', 'استخدم 0.00 للمنتج المجاني. تُعالج المدفوعات حالياً يدوياً.'],

        // Product marketplace and reviews
        ['Browse Products', 'تصفح المنتجات'], ['Search:', 'بحث:'], ['Category filter active', 'تم تفعيل تصفية التصنيف'], ['No Products Found', 'لم يتم العثور على منتجات'],
        ['Try adjusting your search or filters', 'جرّب تعديل البحث أو عوامل التصفية'], ['View All Products', 'عرض جميع المنتجات'], ['Add to Cart 🛒', 'أضف إلى السلة 🛒'], ['Buy Now', 'اشترِ الآن'],
        ['Customer Reviews (', 'تقييمات العملاء ('], ['More from this Creator', 'المزيد من هذا المنشئ'], ['Rating', 'التقييم'], ['Not rated', 'لا يوجد تقييم بعد'], ['N/A', 'غير متاح'],
        ['All Categories', 'كل التصنيفات'], ['Ebook / document', 'كتاب إلكتروني / مستند'], ['Template', 'قالب'], ['Design asset', 'عنصر تصميم'], ['Code / software', 'كود / برنامج'], ['Course / training', 'دورة / تدريب'], ['Other', 'أخرى'],

        // Customer area
        ['Welcome back,', 'مرحباً بعودتك،'], ['Manage your purchases and account settings', 'أدر مشترياتك وإعدادات حسابك'], ['Browse More', 'تصفح المزيد'], ['Settings', 'الإعدادات'],
        ['Access all your purchases', 'الوصول إلى جميع مشترياتك'], ['Continue Shopping', 'متابعة التسوق'], ['Find more products', 'اكتشف المزيد من المنتجات'],
        ['Total Purchases', 'إجمالي المشتريات'], ['Total Spent', 'إجمالي الإنفاق'], ['Completed Orders', 'الطلبات المكتملة'], ['Recent Purchases', 'أحدث المشتريات'],
        ['No Purchases Yet', 'لا توجد مشتريات بعد'], ['Start exploring our amazing products and make your first purchase!', 'ابدأ استكشاف منتجاتنا واشترِ منتجك الأول!'],
        ['📚 My Library', '📚 مكتبتي'], ['All your purchased products in one place', 'جميع المنتجات التي اشتريتها في مكان واحد'], ['Items', 'منتجات'],
        ['Books', 'كتب'], ['Templates', 'قوالب'], ['Graphics', 'رسوميات'], ['Code', 'برمجيات'], ['Newest First', 'الأحدث أولاً'], ['Oldest First', 'الأقدم أولاً'], ['Title A-Z', 'العنوان أ-ي'],
        ['Your Library is Empty 😔', 'مكتبتك فارغة 😔'], ["You haven't purchased any products yet. Start exploring and find amazing digital assets!", 'لم تشترِ أي منتجات بعد. ابدأ التصفح واكتشف أصولاً رقمية مميزة!'],
        ['⚙️ Account Settings', '⚙️ إعدادات الحساب'], ['Manage your account and preferences', 'أدر حسابك وتفضيلاتك'], ['👤 Profile', '👤 الملف الشخصي'], ['🔐 Security', '🔐 الأمان'], ['⚙️ Preferences', '⚙️ التفضيلات'], ['⚠️ Danger Zone', '⚠️ منطقة الخطر'],
        ['Profile Information', 'معلومات الملف الشخصي'], ['📷 Upload Avatar', '📷 رفع صورة شخصية'], ['Email Address', 'البريد الإلكتروني'], ['Email cannot be changed', 'لا يمكن تغيير البريد الإلكتروني'], ['Bio', 'نبذة شخصية'], ['Max 500 characters', 'حد أقصى 500 حرف'],
        ['Security Settings', 'إعدادات الأمان'], ['ℹ️ Keep your account secure by updating your password regularly', 'ℹ️ حافظ على أمان حسابك بتغيير كلمة المرور بانتظام'], ['Current Password *', 'كلمة المرور الحالية *'], ['New Password *', 'كلمة المرور الجديدة *'], ['At least 8 characters', '8 أحرف على الأقل'], ['Confirm New Password *', 'تأكيد كلمة المرور الجديدة *'], ['🔐 Update Password', '🔐 تحديث كلمة المرور'], ['Active Sessions', 'الجلسات النشطة'],
        ['You are currently logged in on this device.', 'أنت مسجل الدخول حالياً على هذا الجهاز.'], ['Log out of this device', 'تسجيل الخروج من هذا الجهاز'],
        ['📧 Email me about new products', '📧 أرسل إليّ بريداً عن المنتجات الجديدة'], ['🎉 Send me special offers and promotions', '🎉 أرسل إليّ العروض والتخفيضات'], ['📦 Notify me about order updates', '📦 أبلغني بتحديثات الطلبات'], ['Preferred Currency', 'العملة المفضلة'], ['USD - US Dollar', 'USD - دولار أمريكي'], ['EUR - Euro', 'EUR - يورو'], ['GBP - British Pound', 'GBP - جنيه إسترليني'], ['AED - UAE Dirham', 'AED - درهم إماراتي'],
        ['These actions are irreversible. Please proceed with caution.', 'هذه الإجراءات لا يمكن التراجع عنها. يُرجى المتابعة بحذر.'], ['Delete Account', 'حذف الحساب'], ['🗑️ Delete My Account', '🗑️ حذف حسابي'],
        ['Saved notification choices are recorded, but this app does not currently send email alerts. Currency is a preference only; prices remain in the currency shown on each listing (no conversion is performed).', 'يتم حفظ تفضيلات الإشعارات، لكن التطبيق لا يرسل تنبيهات بريدية حالياً. العملة تفضيل فقط؛ وتبقى الأسعار بعملة كل قائمة دون تحويل.'],
        ['Deletion disables your sign-in and anonymizes profile details. Essential order records are retained in anonymized form. Creator accounts with listings or payout history and accounts with pending purchase requests must contact support first. Administrator accounts cannot self-delete.', 'يؤدي الحذف إلى تعطيل تسجيل الدخول وإخفاء بيانات الملف الشخصي. تُحتفظ بسجلات الطلبات الأساسية بعد إخفاء الهوية. يجب على المنشئين ذوي القوائم أو سجلات الصرف، وأصحاب الطلبات المعلقة، التواصل مع الدعم أولاً. لا يمكن للمشرفين حذف حساباتهم ذاتياً.'],
        ['Current password', 'كلمة المرور الحالية'], ['Type DELETE to confirm', 'اكتب DELETE للتأكيد'],
        ['Password changed. Please sign in again.', 'تم تغيير كلمة المرور. يرجى تسجيل الدخول مجدداً.'], ['Preferences saved', 'تم حفظ التفضيلات'], ['Avatar updated', 'تم تحديث الصورة الشخصية'],
        ['Profile updated successfully.', 'تم تحديث الملف الشخصي بنجاح.'], ['Enter your password and type DELETE to confirm', 'أدخل كلمة المرور واكتب DELETE للتأكيد'],
        ['Names must be 100 characters or fewer and bio 500 characters or fewer', 'يجب ألا يتجاوز كل اسم 100 حرف والنبذة 500 حرف'], ['Profile fields must be text', 'يجب أن تكون حقول الملف الشخصي نصية'], ['Complete all password fields', 'يرجى تعبئة جميع حقول كلمة المرور'], ['Password must be between 8 and 256 characters', 'يجب أن تتراوح كلمة المرور بين 8 و256 حرفاً'], ['Passwords do not match', 'كلمتا المرور غير متطابقتين'], ['Current password is incorrect', 'كلمة المرور الحالية غير صحيحة'],
        ['Choose a supported currency', 'اختر عملة مدعومة'], ['Choose an image to upload', 'اختر صورة لرفعها'], ['The image file is empty', 'ملف الصورة فارغ'], ['Avatar images must be 2 MB or smaller', 'يجب ألا يتجاوز حجم الصورة الشخصية 2 ميغابايت'], ['Upload a valid PNG, JPEG, or WebP image', 'ارفع صورة PNG أو JPEG أو WebP صالحة'], ['The image header is invalid or unsupported', 'ترويسة الصورة غير صالحة أو غير مدعومة'], ['Image dimensions must be no larger than 4,096 by 4,096 pixels', 'يجب ألا تتجاوز أبعاد الصورة 4096 في 4096 بكسل'],
        ['Resolve pending purchase requests before deleting your account', 'يرجى تسوية طلبات الشراء المعلقة قبل حذف الحساب'], ['Creator accounts with products or payout history must contact support before deletion', 'يجب على حسابات المنشئين التي لديها منتجات أو سجل صرف التواصل مع الدعم قبل الحذف'], ['Administrator accounts cannot be self-deleted', 'لا يمكن للمشرفين حذف حساباتهم ذاتياً'],
        ['Subject and message must be text.', 'يجب أن يكون الموضوع والرسالة نصاً.'], ['Subject and message are required (maximum 160 and 5,000 characters).', 'الموضوع والرسالة مطلوبان (بحد أقصى 160 و5000 حرف).'], ['Message sent successfully', 'تم إرسال الرسالة بنجاح'],

        // Creator area
        ['Manage your products and earnings', 'أدر منتجاتك وأرباحك'], ['📤 Upload New Product', '📤 رفع منتج جديد'], ['View Products', 'عرض المنتجات'], ['Available Balance', 'الرصيد المتاح'], ['Total Earnings:', 'إجمالي الأرباح:'], ['💰 View Details', '💰 عرض التفاصيل'], ['💳 Request Withdrawal', '💳 طلب سحب'],
        ['Total Products', 'إجمالي المنتجات'], ['Total Sales', 'إجمالي المبيعات'], ['Revenue (Before Commission)', 'الإيرادات (قبل العمولة)'], ['Your Earnings (80%)', 'أرباحك (80٪)'], ['📚 Recent Products', '📚 أحدث المنتجات'], ['Action', 'الإجراء'], ['View All →', 'عرض الكل ←'],
        ['No products yet. Start uploading!', 'لا توجد منتجات بعد. ابدأ برفعها!'], ['Upload Product', 'رفع منتج'], ['💰 Recent Sales', '💰 أحدث المبيعات'], ['No sales yet. Upload products to start earning!', 'لا توجد مبيعات بعد. ارفع منتجاتك لبدء الربح!'],
        ['📚 My Products', '📚 منتجاتي'], ['Manage all your uploaded products', 'أدر جميع منتجاتك المرفوعة'], ['All Categories', 'كل التصنيفات'], ['Product Name', 'اسم المنتج'], ['Sales', 'المبيعات'],
        ['No Products Yet 😔', 'لا توجد منتجات بعد 😔'], ['Start uploading your first digital product today!', 'ابدأ برفع أول منتج رقمي لك اليوم!'], ['📤 Upload Your First Product', '📤 ارفع أول منتج لك'],
        ['Creator earnings', 'أرباح المنشئ'], ['Withdrawals are temporarily disabled until payment processing is configured.', 'طلبات السحب متوقفة مؤقتاً إلى حين إعداد معالجة المدفوعات.'], ['Withdrawal history', 'سجل طلبات السحب'], ['No withdrawal requests yet.', 'لا توجد طلبات سحب بعد.'], ['Back to dashboard', 'العودة إلى لوحة التحكم'],
        ['Upload a digital product', 'ارفع منتجاً رقمياً'], ['Complete the details below. Your product will be reviewed before it is published.', 'أكمل البيانات أدناه. ستتم مراجعة منتجك قبل نشره.'], ['Product name (English) *', 'اسم المنتج (بالإنجليزية) *'], ['اسم المنتج (العربية) *', 'Product name (Arabic) *'], ['Choose a category', 'اختر تصنيفاً'], ['Product type *', 'نوع المنتج *'], ['Choose a type', 'اختر النوع'], ['Price (USD) *', 'السعر (USD) *'], ['Description (English)', 'الوصف (بالإنجليزية)'], ['الوصف (العربية)', 'Description (Arabic)'], ['Product file *', 'ملف المنتج *'], ['Allowed: PDF, EPUB, Office files, ZIP, PNG, JPG, SVG. Maximum upload size: 500 MB.', 'الصيغ المسموحة: PDF وEPUB وOffice وZIP وPNG وJPG وSVG. الحد الأقصى: 500 ميغابايت.'], ['No file selected.', 'لم يتم اختيار ملف.'], ['Submit for review', 'إرسال للمراجعة'],

        // Administration
        ['Admin Dashboard', 'لوحة الإدارة'], ['Platform overview and management', 'نظرة عامة على المنصة وإدارتها'], ['Total Users', 'إجمالي المستخدمين'], ['Total Products', 'إجمالي المنتجات'], ['Total Sales', 'إجمالي المبيعات'], ['Pending Review', 'بانتظار المراجعة'], ['Pending Purchase Requests', 'طلبات الشراء المعلقة'], ['📋 Recent Orders', '📋 أحدث الطلبات'], ['No orders yet', 'لا توجد طلبات بعد'], ['⚡ Quick Actions', '⚡ إجراءات سريعة'],
        ['products awaiting approval', 'منتجات بانتظار الموافقة'], ['manual purchase requests awaiting payment verification', 'طلبات شراء يدوية بانتظار التحقق من الدفع'], ['🧾 Review Purchase Requests', '🧾 مراجعة طلبات الشراء'], ['✅ Review Products', '✅ مراجعة المنتجات'], ['👥 Manage Users', '👥 إدارة المستخدمين'], ['💳 Process Withdrawals', '💳 معالجة طلبات السحب'], ['💳 View Withdrawals (payouts disabled)', '💳 عرض طلبات السحب (الصرف متوقف)'], ['💬 Messages', '💬 الرسائل'], ['🔧 System Status', '🔧 حالة النظام'], ['Database', 'قاعدة البيانات'], ['Connected', 'متصل'], ['File Storage', 'تخزين الملفات'], ['Payment Gateway', 'بوابة الدفع'], ['Test Mode', 'وضع الاختبار'], ['Email Service', 'خدمة البريد'], ['Configured', 'مهيأ'], ['Admin Panel', 'لوحة الإدارة'],
        ['Manual purchase requests', 'طلبات الشراء اليدوية'], ['Verify payment independently before confirming. Confirmation grants the customer library access and credits creator earnings.', 'تحقق من استلام الدفع بشكل مستقل قبل التأكيد. يمنح التأكيد العميل حق الوصول إلى مكتبته ويضيف الأرباح للمنشئ.'], ['pending', 'معلّق'], ['Order', 'الطلب'], ['Product / creator', 'المنتج / المنشئ'], ['Submitted', 'تاريخ الإرسال'], ['Confirm & fulfill', 'تأكيد وإتاحة المنتج'], ['Reject', 'رفض'], ['No action available', 'لا يوجد إجراء متاح'], ['No orders found for this status.', 'لا توجد طلبات بهذه الحالة.'], ['No orders found', 'لم يتم العثور على طلبات'],
        ['📋 Product Review', '📋 مراجعة المنتجات'], ['Approve or reject submitted products', 'وافق على المنتجات المرسلة أو ارفضها'], ['All Status', 'كل الحالات'], ['Product Name', 'اسم المنتج'], ['Creator', 'المنشئ'], ['No Products Found', 'لم يتم العثور على منتجات'], ['No products to review at the moment', 'لا توجد منتجات للمراجعة حالياً'], ['Reject Product', 'رفض المنتج'], ['This will keep the product unpublished in the marketplace.', 'سيبقى المنتج غير منشور في السوق.'],
        ['👥 User Management', '👥 إدارة المستخدمين'], ['View and manage all platform users', 'عرض جميع مستخدمي المنصة وإدارتهم'], ['👥 User Directory', '👥 دليل المستخدمين'], ['View registered platform users. Account suspension and activation controls are not enabled.', 'عرض مستخدمي المنصة المسجلين. أدوات تعليق الحسابات وتفعيلها غير مفعلة.'], ['Creators', 'المنشئون'], ['Customers', 'العملاء'], ['All Roles', 'كل الأدوار'], ['Admins', 'المشرفون'], ['All Status', 'كل الحالات'], ['User', 'المستخدم'], ['Role', 'الدور'], ['No Users Found', 'لم يتم العثور على مستخدمين'], ['Suspend', 'تعليق'], ['Activate', 'تفعيل'],
        ['💳 Withdrawal Management', '💳 إدارة طلبات السحب'], ['Process and manage creator withdrawal requests', 'معالجة وإدارة طلبات سحب أرباح المنشئين'], ['Total Requests', 'إجمالي الطلبات'], ['Total Processed', 'إجمالي ما تمت معالجته'], ['All Methods', 'كل الطرق'], ['Bank Transfer', 'تحويل بنكي'], ['PayPal', 'PayPal'], ['Wise', 'Wise'], ['Requested', 'تاريخ الطلب'], ['No Withdrawals', 'لا توجد طلبات سحب'], ['No withdrawal requests at the moment', 'لا توجد طلبات سحب حالياً'], ['Withdrawal Details', 'تفاصيل طلب السحب'], ['Close', 'إغلاق'],

        // Page titles, additional controls, and runtime feedback
        ['Manage Orders', 'إدارة الطلبات'], ['Manage Users', 'إدارة المستخدمين'], ['Manage Withdrawals', 'إدارة طلبات السحب'],
        ['Creator withdrawal requests are read-only while payout processing is disabled.', 'طلبات سحب المنشئين للعرض فقط بينما معالجة الصرف متوقفة.'],
        ['Payouts are disabled in this version. Do not treat wallet balances as paid funds; no approve, reject, or transfer action is available here.', 'الصرف متوقف في هذا الإصدار. لا تعتبر أرصدة المحافظ أموالاً مدفوعة؛ ولا تتوفر هنا إجراءات موافقة أو رفض أو تحويل.'], ['View details', 'عرض التفاصيل'],
        ['About ProAssets 💎', 'عن ProAssets 💎'], ['👨‍💼 Admin Dashboard', '👨‍💼 لوحة الإدارة'],
        ['✓ Approve', '✓ موافقة'], ['✗ Reject', '✗ رفض'], ['✗ Reject Product', '✗ رفض المنتج'],
        ['Method', 'طريقة الدفع'], ['Amount:', 'المبلغ:'], ['Method:', 'الطريقة:'], ['Status:', 'الحالة:'],
        ['Available balance', 'الرصيد المتاح'], ['My products', 'منتجاتي'], ['Category *', 'التصنيف *'],
        ['💾 Save Changes', '💾 حفظ التغييرات'], ['💾 Save Preferences', '💾 حفظ التفضيلات'], ['Preferences', 'التفضيلات'],
        ['🛒 Cart', '🛒 السلة'], ['View →', 'عرض ←'], ['« First', '« الأولى'], ['‹ Previous', '‹ السابقة'], ['Next ›', 'التالية ›'], ['Last »', 'الأخيرة »'], ['✕', '✕'],
        ['Review Products', 'مراجعة المنتجات'], ['Create Account', 'إنشاء حساب'], ['Manual Checkout', 'إتمام الطلب يدوياً'],
        ['Customer Dashboard', 'لوحة العميل'], ['Creator Dashboard', 'لوحة المنشئ'], ['My Earnings', 'أرباحي'], ['Account Settings', 'إعدادات الحساب'],
        ['Support inbox', 'صندوق رسائل الدعم'], ['Support Messages', 'رسائل الدعم'], ['Messages', 'الرسائل'], ['Read messages submitted through the public contact form. Replies are not sent automatically; use the sender’s email client if provided.', 'اقرأ الرسائل المرسلة عبر نموذج التواصل العام. لا تُرسل الردود تلقائياً؛ استخدم برنامج البريد لدى المرسل إن توفر.'],
        ['Open', 'مفتوحة'], ['Closed', 'مغلقة'], ['All messages', 'كل الرسائل'], ['No messages in this view.', 'لا توجد رسائل في هذا العرض.'], ['Mark closed', 'تحديد كمغلقة'], ['Message marked as closed', 'تم تحديد الرسالة كمغلقة'], ['Open Support Messages', 'رسائل الدعم المفتوحة'], ['support messages need review', 'رسائل دعم بحاجة إلى مراجعة'], ['💬 Review Support Messages', '💬 مراجعة رسائل الدعم'],
        ['Manual contact and admin verification only; no online gateway', 'التواصل اليدوي والتحقق الإداري فقط؛ لا توجد بوابة دفع إلكترونية'], ['Not configured; no automated emails are sent', 'غير مهيأ؛ لا تُرسل رسائل بريدية تلقائية'], ['Creator Payouts', 'صرف أرباح المنشئين'], ['Disabled; no automatic disbursements', 'معطل؛ لا توجد تحويلات آلية'], ['Payment Handling', 'آلية الدفع'], ['Email Delivery', 'إرسال البريد الإلكتروني'],
        ['Edit product listing', 'تعديل قائمة المنتج'], ['Update the bilingual listing details and price. The uploaded product file is unchanged.', 'حدّث بيانات القائمة باللغتين والسعر. لن يتغير ملف المنتج المرفوع.'], ['Current status:', 'الحالة الحالية:'], ['Published or rejected listings return to review after edits; existing buyers retain authorized downloads.', 'تعود القوائم المنشورة أو المرفوضة إلى المراجعة بعد التعديل؛ ويحتفظ المشترون الحاليون بحق التنزيل.'], ['Listing saved. If it was published or rejected, the revised listing is now pending administrator review.', 'تم حفظ القائمة. إذا كانت منشورة أو مرفوضة، فستنتظر النسخة المعدلة مراجعة المشرف.'], ['Maximum 3,000 characters.', 'الحد الأقصى ٣٠٠٠ حرف.'], ['Price (USD) *', 'السعر (USD) *'], ['Paid purchases continue to use the price saved on each order. Free products are delivered immediately.', 'تظل المشتريات المدفوعة مرتبطة بالسعر المسجل في كل طلب. وتُتاح المنتجات المجانية فوراً.'], ['Save listing', 'حفظ القائمة'], ['History protected', 'السجل محفوظ'], ['Listing unavailable', 'القائمة غير متاحة'], ['This product has purchase or customer history and cannot be permanently deleted. Contact support if it must be removed.', 'لهذا المنتج سجل مشتريات أو عملاء، لذلك لا يمكن حذفه نهائياً. تواصل مع الدعم عند ضرورة إزالته.'], ['Product deleted', 'تم حذف المنتج'],
        ['Product not found', 'لم يتم العثور على المنتج'], ['Product name must be between 3 and 32 letters, numbers, dots, hyphens or underscores', 'يجب أن يتراوح اسم المستخدم بين 3 و32 حرفاً أو رقماً أو نقطة أو شرطة أو شرطة سفلية'], ['Choose a category and enter a valid price', 'اختر تصنيفاً وأدخل سعراً صالحاً'], ['English and Arabic product names are required (maximum 140 characters)', 'اسم المنتج بالإنجليزية والعربية مطلوب (بحد أقصى 140 حرفاً)'], ['Price must be between 0 and 999,999 USD', 'يجب أن يكون السعر بين 0 و999,999 دولار أمريكي'], ['Descriptions must be 3,000 characters or fewer', 'يجب ألا يتجاوز طول الوصف 3000 حرف'], ['Choose a valid product type', 'اختر نوعاً صالحاً للمنتج'], ['Choose an active product category', 'اختر تصنيفاً نشطاً'],
        ['Account deleted. Essential order records are retained in anonymized form.', 'تم حذف الحساب. تُحتفظ بسجلات الطلبات الأساسية بعد إخفاء الهوية.'],
        ['Recorded Balance (not paid)', 'رصيد مسجل (غير مدفوع)'], ['Recorded earnings:', 'الأرباح المسجلة:'], ['Creator payouts are disabled in this version. These ledger balances are not paid funds.', 'صرف أرباح المنشئين معطل في هذا الإصدار. أرصدة السجل ليست أموالاً مدفوعة.'], ['💰 View earnings and payout status', '💰 عرض الأرباح وحالة الصرف'], ['Creator earnings ledger', 'سجل أرباح المنشئ'], ['Recorded balance', 'الرصيد المسجل'], ['Payouts are disabled. Do not treat wallet balances as paid funds; contact support about manual settlement.', 'الصرف متوقف. لا تعتبر أرصدة المحفظة أموالاً مدفوعة؛ تواصل مع الدعم بشأن التسوية اليدوية.'], ['Creator payouts are disabled in this version; no transfer was made.', 'صرف أرباح المنشئين معطل في هذا الإصدار؛ لم يتم إجراء أي تحويل.'], ['No withdrawal requests are recorded.', 'لا توجد طلبات سحب مسجلة.'], 
        ['Your Earnings (80%) — ledger only, not paid', 'أرباحك (80٪) — مسجلة وليست مدفوعة'], ['Completed sales by currency', 'المبيعات المكتملة حسب العملة'], ['Completed spend by currency', 'الإنفاق المكتمل حسب العملة'], ['Processed amount by currency', 'المبلغ المعالج حسب العملة'], ['Order currency does not match the creator ledger currency; manual reconciliation is required.', 'عملة الطلب لا تطابق عملة سجل المنشئ؛ يلزم إجراء تسوية يدوية.'],
        ['The selected file exceeds the 500 MB limit.', 'الملف المحدد يتجاوز الحد الأقصى البالغ 500 ميغابايت.'],
        ['Unable to upload this product.', 'تعذر رفع هذا المنتج.'], ['Product submitted for review.', 'تم إرسال المنتج للمراجعة.'],
        ['An error occurred. Please try again.', 'حدث خطأ. يرجى المحاولة مرة أخرى.'], ['A network error occurred.', 'حدث خطأ في الاتصال.'],
        ['Unable to remove item', 'تعذرت إزالة المنتج'], ['Unable to update this order.', 'تعذر تحديث الطلب.'],
        ['Payment confirmed; the product was added to the customer library.', 'تم تأكيد الدفع وإضافة المنتج إلى مكتبة العميل.'],
        ['Only pending orders can be confirmed', 'يمكن تأكيد الطلبات المعلقة فقط'], ['Only pending orders can be rejected', 'يمكن رفض الطلبات المعلقة فقط'],
        ['You already own this product', 'أنت تملك هذا المنتج بالفعل'], ['Product type', 'نوع المنتج'],
        ['ebook', 'كتاب إلكتروني'], ['template', 'قالب'], ['design', 'تصميم'], ['software', 'برنامج'], ['course', 'دورة'], ['other', 'أخرى'],
        ['admin', 'مشرف'], ['creator', 'منشئ'], ['customer', 'عميل'], ['completed', 'مكتمل'], ['rejected', 'مرفوض'], ['published', 'منشور'], ['draft', 'مسودة'], ['active', 'نشط'], ['inactive', 'غير نشط'], ['open', 'مفتوحة'], ['closed', 'مغلقة'],
        ['Access Denied - ProAssets', 'تم رفض الوصول - ProAssets'], ['Page Not Found - ProAssets', 'الصفحة غير موجودة - ProAssets'], ['Server Error - ProAssets', 'خطأ في الخادم - ProAssets'],
        ['For privacy questions, use the', 'للاستفسارات المتعلقة بالخصوصية، استخدم'],
        ['For questions about these terms, use the', 'للاستفسارات عن هذه الشروط، استخدم'],
        ['contact page', 'صفحة التواصل'],

        // Privacy, terms and errors
        ['Last updated: January 2024', 'آخر تحديث: يناير 2024'], ['Summary:', 'الملخص:'], ['1. Introduction', '1. المقدمة'], ['2. Information Collection', '2. جمع المعلومات'], ['Personal Information', 'المعلومات الشخصية'], ['Automatic Information', 'المعلومات التلقائية'], ['3. How We Use Your Information', '3. كيفية استخدام معلوماتك'], ['4. Data Security', '4. أمن البيانات'], ['5. Data Retention', '5. الاحتفاظ بالبيانات'], ['6. Your Rights', '6. حقوقك'], ['7. Third-Party Services', '7. خدمات الجهات الخارجية'], ['8. Cookies', '8. ملفات تعريف الارتباط'], ['9. Changes to This Policy', '9. تعديلات هذه السياسة'], ['10. Contact Us', '10. تواصل معنا'],
        ['We take your privacy seriously. We collect only necessary information to provide our services and never share your data without your consent.', 'نحترم خصوصيتك. نجمع المعلومات اللازمة لتقديم خدماتنا فقط، ولا نشارك بياناتك دون موافقتك.'],
        ['ProAssets ("we", "our", or "us") operates the ProAssets platform. This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our service.', 'تدير ProAssets منصة ProAssets. توضح هذه الصفحة سياساتنا بشأن جمع البيانات الشخصية واستخدامها والإفصاح عنها عند استخدام الخدمة.'],
        ['Name and email address', 'الاسم والبريد الإلكتروني'], ['Account username and password (hashed)', 'اسم المستخدم وكلمة المرور (مشفرة التجزئة)'], ['Payment information (processed securely)', 'معلومات الدفع (تُعالج بأمان)'], ['Profile information (optional)', 'معلومات الملف الشخصي (اختيارية)'], ['Usage data and analytics', 'بيانات الاستخدام والتحليلات'], ['IP address and browser type', 'عنوان IP ونوع المتصفح'], ['Pages visited and time spent', 'الصفحات التي تمت زيارتها والوقت المستغرق'], ['Device information', 'معلومات الجهاز'], ['Referrer data', 'بيانات مصدر الزيارة'],
        ['Providing and maintaining our service', 'تقديم خدمتنا وصيانتها'], ['Processing transactions and sending related information', 'معالجة المعاملات وإرسال المعلومات ذات الصلة'], ['Sending promotional emails (with your consent)', 'إرسال رسائل ترويجية (بموافقتك)'], ['Improving and personalizing the service', 'تحسين الخدمة وتخصيصها'], ['Detecting and preventing fraud', 'اكتشاف الاحتيال ومنعه'], ['Complying with legal obligations', 'الامتثال للالتزامات القانونية'], ['SSL/TLS encryption for data transmission', 'تشفير SSL/TLS لنقل البيانات'], ['Password hashing with Werkzeug', 'تجزئة كلمات المرور باستخدام Werkzeug'], ['Regular security audits', 'عمليات تدقيق أمني منتظمة'], ['Secure database connections', 'اتصالات آمنة بقاعدة البيانات'], ['Limited access to sensitive data', 'تقييد الوصول إلى البيانات الحساسة'],
        ['Access your personal data', 'الوصول إلى بياناتك الشخصية'], ['Correct inaccurate data', 'تصحيح البيانات غير الدقيقة'], ['Request deletion of your data', 'طلب حذف بياناتك'], ['Opt-out of marketing communications', 'إلغاء الاشتراك في الرسائل التسويقية'], ['Data portability', 'نقل البيانات'], ['Email:', 'البريد الإلكتروني:'], ['Website:', 'الموقع الإلكتروني:'],
        ['Use of ProAssets is subject to applicable laws and the licenses attached to each digital product.', 'يخضع استخدام ProAssets للقوانين المعمول بها وللتراخيص المرفقة بكل منتج رقمي.'], ['Digital products', 'المنتجات الرقمية'], ["Customers may use purchased products only according to the seller's license. Redistribution or unauthorized sharing is prohibited.", 'يجوز للعملاء استخدام المنتجات المشتراة وفق ترخيص البائع فقط. يُحظر إعادة توزيعها أو مشاركتها دون إذن.'], ['Accounts', 'الحسابات'], ['Keep your credentials secure and provide accurate information.', 'حافظ على سرية بيانات الدخول وقدّم معلومات دقيقة.'],
        ['Access Denied', 'تم رفض الوصول'], ['You don\'t have permission to access this page. Please login or contact support if you believe this is an error.', 'ليس لديك إذن للوصول إلى هذه الصفحة. سجّل الدخول أو تواصل مع الدعم إذا كنت تعتقد بوجود خطأ.'], ['Go Home', 'العودة إلى الرئيسية'],
        ['Page Not Found', 'الصفحة غير موجودة'], ["Sorry, the page you're looking for doesn't exist or has been moved.", 'عذراً، الصفحة التي تبحث عنها غير موجودة أو تم نقلها.'],
        ['Server Error', 'خطأ في الخادم'], ["Something went wrong on our end. Our team has been notified and is working to fix it.", 'حدث خطأ من جانبنا. تم إبلاغ فريقنا ويعمل على إصلاحه.'], ['Report Issue', 'الإبلاغ عن مشكلة'], ['Login', 'تسجيل الدخول'],
    ];

    const lookup = new Map();
    pairs.forEach(([en, ar]) => {
        lookup.set(en, {en, ar});
        lookup.set(ar, {en, ar});
    });
    const originalText = new WeakMap();
    const lastAppliedText = new WeakMap();
    const originalAttributes = new WeakMap();
    let language = 'ar';

    function translate(value, targetLanguage) {
        const trimmed = value.trim();
        if (targetLanguage === 'ar') {
            let match = trimmed.match(/^Welcome,\s*(.+?)\s*!\s*🎉$/u);
            if (match) return value.replace(trimmed, `مرحباً، ${match[1].trim()}! 🎉`);
            match = trimmed.match(/^Welcome back,\s*(.+?)\s*!\s*👋$/u);
            if (match) return value.replace(trimmed, `مرحباً بعودتك، ${match[1].trim()}! 👋`);
            match = trimmed.match(/^(\d+)\s+pending$/u);
            if (match) return value.replace(trimmed, `${match[1]} طلب معلّق`);
            match = trimmed.match(/^(\d+)\s+Items?$/u);
            if (match) return value.replace(trimmed, `${match[1]} منتجات`);
            match = trimmed.match(/^Pending\s+\((\d+)\)$/u);
            if (match) return value.replace(trimmed, `معلّق (${match[1]})`);
            match = trimmed.match(/^Open\s+\((\d+)\)$/u);
            if (match) return value.replace(trimmed, `مفتوح (${match[1]})`);
            match = trimmed.match(/^Search:\s*[“"](.+?)[”"]$/u);
            if (match) return value.replace(trimmed, `بحث: «${match[1]}»`);
        }
        const pair = lookup.get(trimmed);
        if (!pair) return value;
        const translated = targetLanguage === 'ar' ? pair.ar : pair.en;
        const leading = value.match(/^\s*/)?.[0] || '';
        const trailing = value.match(/\s*$/)?.[0] || '';
        return `${leading}${translated}${trailing}`;
    }

    function translateText(root) {
        if (!root) return;
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                const parent = node.parentElement;
                if (!parent || parent.closest('script,style,noscript,textarea,code,pre,#siteLanguageToggle,[data-lang-en][data-lang-ar]')) return NodeFilter.FILTER_REJECT;
                return node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            }
        });
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        nodes.forEach(node => {
            const current = node.nodeValue;
            const source = originalText.has(node) ? originalText.get(node) : current;
            originalText.set(node, source);
            const result = translate(source, language);
            node.nodeValue = result;
            lastAppliedText.set(node, result);
        });
    }

    function translateAttributes(root) {
        if (!root || root.nodeType !== Node.ELEMENT_NODE) return;
        const elements = [root, ...root.querySelectorAll('*')];
        elements.forEach(element => {
            if (element.id === 'siteLanguageToggle') return;
            ['placeholder', 'title', 'aria-label'].forEach(attribute => {
                if (!element.hasAttribute(attribute)) return;
                let stored = originalAttributes.get(element);
                if (!stored) { stored = {}; originalAttributes.set(element, stored); }
                const current = element.getAttribute(attribute);
                if (stored[attribute] === undefined || stored[`${attribute}_last`] !== current) {
                    stored[attribute] = current;
                }
                const result = translate(stored[attribute], language);
                element.setAttribute(attribute, result);
                stored[`${attribute}_last`] = result;
            });
        });
    }

    function translateBilingualFields() {
        document.querySelectorAll('[data-lang-en][data-lang-ar]').forEach(element => {
            const target = language === 'ar' ? element.dataset.langAr : element.dataset.langEn;
            if (target !== undefined) element.textContent = target;
            if (element.tagName === 'OPTION') element.setAttribute('dir', language === 'ar' ? 'rtl' : 'ltr');
        });
    }

    function applyLanguage(nextLanguage) {
        language = nextLanguage === 'en' ? 'en' : 'ar';
        document.documentElement.lang = language;
        document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
        if (document.body) {
            document.body.dir = document.documentElement.dir;
            translateBilingualFields();
            translateText(document.body);
            translateAttributes(document.body);
        }
        if (!document.documentElement.dataset.originalTitle) {
            document.documentElement.dataset.originalTitle = document.title;
        }
        document.title = translate(document.documentElement.dataset.originalTitle, language).trim();
        const toggle = document.getElementById('siteLanguageToggle');
        if (toggle) {
            toggle.textContent = language === 'ar' ? 'English' : 'العربية';
            toggle.setAttribute('aria-label', language === 'ar' ? 'Switch to English' : 'التبديل إلى العربية');
            toggle.setAttribute('title', toggle.getAttribute('aria-label'));
        }
        try { localStorage.setItem('proassets-language', language); } catch (_) { /* storage may be disabled */ }
    }

    function addRtlStyles() {
        if (document.getElementById('site-i18n-rtl')) return;
        const style = document.createElement('style');
        style.id = 'site-i18n-rtl';
        style.textContent = `
            html[dir="rtl"] body { direction: rtl; }
            html[dir="rtl"] th, html[dir="rtl"] td { text-align: right; }
            html[dir="rtl"] input, html[dir="rtl"] textarea, html[dir="rtl"] select { text-align: start; }
            #siteLanguageToggle { position: fixed; z-index: 10000; inset-inline-end: 16px; bottom: 16px; border: 1px solid rgba(255,255,255,.75); border-radius: 999px; padding: 10px 15px; background: #0F172A; color: #fff; box-shadow: 0 5px 18px rgba(15,23,42,.25); font: 700 14px/1.2 system-ui,sans-serif; cursor: pointer; }
            #siteLanguageToggle:hover { background: #7C3AED; }
            #siteLanguageToggle:focus-visible { outline: 3px solid #A78BFA; outline-offset: 3px; }
        `;
        document.head.appendChild(style);
    }

    function initialize() {
        if (document.documentElement.classList.contains('pa-page')) return;
        addRtlStyles();
        if (!document.getElementById('siteLanguageToggle')) {
            const button = document.createElement('button');
            button.id = 'siteLanguageToggle';
            button.type = 'button';
            button.textContent = 'English';
            button.setAttribute('aria-label', 'Switch to English');
            document.body.appendChild(button);
            button.addEventListener('click', () => applyLanguage(language === 'ar' ? 'en' : 'ar'));
        }

        let saved = 'ar';
        try { saved = localStorage.getItem('proassets-language') || saved; } catch (_) { /* storage may be disabled */ }
        applyLanguage(saved);

        const observer = new MutationObserver(records => {
            records.forEach(record => {
                if (record.type === 'characterData') {
                    const node = record.target;
                    if (lastAppliedText.has(node) && lastAppliedText.get(node) === node.nodeValue) return;
                    originalText.set(node, node.nodeValue);
                    const result = translate(node.nodeValue, language);
                    node.nodeValue = result;
                    lastAppliedText.set(node, result);
                } else {
                    record.addedNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            if (node.parentElement?.closest('[data-lang-en][data-lang-ar],script,style,textarea,code,pre,#siteLanguageToggle')) return;
                            originalText.set(node, node.nodeValue);
                            const result = translate(node.nodeValue, language);
                            node.nodeValue = result;
                            lastAppliedText.set(node, result);
                        } else if (node.nodeType === Node.ELEMENT_NODE) {
                            translateBilingualFields();
                            translateText(node);
                            translateAttributes(node);
                        }
                    });
                }
            });
        });
        observer.observe(document.body, {subtree: true, childList: true, characterData: true});
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, {once: true});
    else initialize();
})();
