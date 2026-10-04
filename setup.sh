#!/bin/bash

# ===== ProAssets Setup Script =====
# سكريبت تثبيت المشروع

echo "🚀 ProAssets Installation"
echo "========================="

# 1. التحقق من Python
echo "📦 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python $(python3 --version | cut -d' ' -f2) found"

# 2. إنشاء Virtual Environment
echo ""
echo "📁 Creating virtual environment..."
python3 -m venv venv

# 3. تفعيل Virtual Environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# 4. تحديث pip
echo "📤 Upgrading pip..."
pip install --upgrade pip

# 5. تثبيت المتطلبات
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# 6. إنشاء المجلدات المطلوبة
echo "📁 Creating required directories..."
mkdir -p uploads
mkdir -p static/css
mkdir -p static/js

# 7. تهيئة قاعدة البيانات
echo ""
echo "🗄️  Initializing database..."
python3 migrations.py

# 8. إنشاء ملف .env
echo ""
echo "⚙️  Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created. Please update with your settings."
else
    echo "⚠️  .env file already exists"
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🚀 To start the server, run:"
echo "   source venv/bin/activate"
echo "   python3 run.py"
echo ""
echo "📝 Default Test Accounts:"
echo "   Admin: admin@proassets.test / Admin@123456"
echo "   Creator: creator@proassets.test / Creator@123456"
echo "   Customer: customer@proassets.test / Customer@123456"
