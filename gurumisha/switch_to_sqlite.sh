#!/bin/bash
# Quick Fix: Switch to SQLite for PostgreSQL Version Compatibility Issues
# Usage: bash switch_to_sqlite.sh

echo "🔄 Switching Gurumisha to SQLite (PostgreSQL Compatibility Fix)..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "manage.py not found. Please run this script from the Django project root."
    exit 1
fi

print_status "Creating backup of current .env file..."
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    print_success "Backup created: .env.backup.$(date +%Y%m%d_%H%M%S)"
else
    print_warning ".env file not found, creating new one..."
fi

print_status "Configuring environment for SQLite..."

# Create or update .env file for SQLite
cat > .env << EOF
# SQLite Configuration (PostgreSQL Compatibility Fix)
USE_SQLITE=True
DEBUG=True

# Django Settings
SECRET_KEY=your-secret-key-here-$(openssl rand -hex 16)
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=kamandembugua18@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Static/Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Database (SQLite - Fallback)
# PostgreSQL settings (commented out due to version compatibility)
# DB_NAME=gurumisha_db
# DB_USER=gurumisha_user
# DB_PASSWORD=gurumisha_password
# DB_HOST=localhost
# DB_PORT=5432
EOF

print_success ".env file configured for SQLite"

print_status "Running database migrations with SQLite..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
elif [ -d "env" ]; then
    print_status "Activating virtual environment..."
    source env/bin/activate
fi

# Run migrations
python manage.py makemigrations
if [ $? -eq 0 ]; then
    print_success "Migrations created successfully"
else
    print_error "Failed to create migrations"
    exit 1
fi

python manage.py migrate
if [ $? -eq 0 ]; then
    print_success "Database migrations completed"
else
    print_error "Failed to run migrations"
    exit 1
fi

# Create superuser if it doesn't exist
print_status "Creating default admin user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@gurumisha.com', 'admin123')
    print("Admin user created: admin/admin123")
else:
    print("Admin user already exists")
EOF

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

print_success "SQLite configuration complete!"
echo ""
echo "🎉 Gurumisha is now configured to use SQLite"
echo ""
echo "📋 Next Steps:"
echo "1. Start the development server: python manage.py runserver"
echo "2. Access admin panel: http://localhost:8000/admin/"
echo "3. Login with: admin / admin123"
echo ""
echo "⚠️  Important Notes:"
echo "• This is a temporary fix for PostgreSQL version compatibility"
echo "• For production, request PostgreSQL 12+ upgrade from your hosting provider"
echo "• SQLite is suitable for development but not recommended for production"
echo ""
echo "📞 Contact your hosting provider to upgrade PostgreSQL to version 12 or later"
echo "   Current requirement: PostgreSQL 12+ (Django 4.2+ compatibility)"
