#!/bin/bash
set -euo pipefail

# ProAssets local setup — never seeds a known/default administrator.

echo "🚀 ProAssets Installation"
echo "========================="

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
    echo "❌ ProAssets requires Python 3.9 or newer."
    exit 1
fi

echo "📦 Python $(python3 --version | cut -d' ' -f2) found"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚙️  Created .env from .env.example; review settings before running."
fi

mkdir -p private_storage static/css static/js
python migrations.py

echo ""
echo "✅ Setup completed. Start locally with:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "🔐 No default admin/test accounts are created. To create the first admin locally:"
echo "   Add BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_EMAIL, and a strong BOOTSTRAP_ADMIN_PASSWORD to .env"
echo "   python bootstrap_admin.py"
echo "   Then remove the BOOTSTRAP_ADMIN_* values from .env"
