#!/bin/bash

# Gurumisha Django E-Commerce Platform Setup Script
# This script automates the initial setup process

set -e  # Exit on any error

echo "🚀 Setting up Gurumisha Django E-Commerce Platform..."
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ and try again."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. You have Python $python_version."
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

node_version=$(node -v | cut -d'v' -f2)
echo "✅ Node.js $node_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Python dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm install
    echo "✅ Node.js dependencies installed"
else
    echo "❌ package.json not found"
    exit 1
fi

# Navigate to Django project directory
cd gurumisha

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
DEBUG=True
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=kamandembugua18@gmail.com
EMAIL_HOST_PASSWORD=your-email-password-here
EMAIL_USE_TLS=True
ALLOWED_HOSTS=localhost,127.0.0.1
EOL
    echo "✅ .env file created"
    echo "⚠️  Please update EMAIL_HOST_PASSWORD in .env file"
else
    echo "✅ .env file already exists"
fi

# Run database migrations
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate
echo "✅ Database migrations completed"

# Create superuser (optional)
echo "👤 Creating superuser account..."
echo "You can skip this step and create it later with: python manage.py createsuperuser"
read -p "Do you want to create a superuser now? (y/N): " create_superuser

if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    echo "✅ Superuser created"
else
    echo "⏭️  Skipping superuser creation"
fi

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
cd ..
npm run build
echo "✅ Tailwind CSS built"

# Collect static files
echo "📁 Collecting static files..."
cd gurumisha
python manage.py collectstatic --noinput
echo "✅ Static files collected"

# Final setup complete
echo ""
echo "🎉 Setup completed successfully!"
echo "=================================================="
echo ""
echo "📋 Next steps:"
echo "1. Update EMAIL_HOST_PASSWORD in gurumisha/.env file"
echo "2. Start the development server:"
echo "   cd gurumisha"
echo "   source ../venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "3. In another terminal, start Tailwind CSS watcher:"
echo "   npm run dev"
echo ""
echo "4. Visit http://127.0.0.1:8000 to see your application"
echo "5. Admin panel: http://127.0.0.1:8000/admin/"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "🚀 Happy coding!"
