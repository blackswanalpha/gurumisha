#!/bin/bash
# PostgreSQL Environment Configuration Script
# Usage: source set_postgresql.sh

echo "🐘 Setting up PostgreSQL environment for Gurumisha..."

# PostgreSQL Database Configuration
export DB_NAME=gurumisha_db
export DB_USER=gurumisha_user
export DB_PASSWORD=gurumisha_password
export DB_HOST=localhost
export DB_PORT=5432
export USE_SQLITE=False

# Django Settings
export DEBUG=True

# Email Configuration
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=kamandembugua18@gmail.com

# Other settings
export ALLOWED_HOSTS=localhost,127.0.0.1

echo "✅ PostgreSQL environment variables set!"
echo "📊 Database: $DB_NAME"
echo "👤 User: $DB_USER"
echo "🏠 Host: $DB_HOST:$DB_PORT"
echo ""
echo "🚀 You can now run:"
echo "   python manage.py runserver"
echo "   python manage.py shell"
echo "   python manage.py migrate"
echo ""
echo "🔄 To switch back to SQLite, run: source set_sqlite.sh"
