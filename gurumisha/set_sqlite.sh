#!/bin/bash
# SQLite Environment Configuration Script
# Usage: source set_sqlite.sh

echo "🗃️ Setting up SQLite environment for Gurumisha..."

# SQLite Database Configuration
export USE_SQLITE=True

# Unset PostgreSQL variables
unset DB_NAME
unset DB_USER
unset DB_PASSWORD
unset DB_HOST
unset DB_PORT

# Django Settings
export DEBUG=True

# Email Configuration
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=kamandembugua18@gmail.com

# Other settings
export ALLOWED_HOSTS=localhost,127.0.0.1

echo "✅ SQLite environment variables set!"
echo "📊 Database: SQLite (db.sqlite3)"
echo ""
echo "🚀 You can now run:"
echo "   python manage.py runserver"
echo "   python manage.py shell"
echo "   python manage.py migrate"
echo ""
echo "🔄 To switch back to PostgreSQL, run: source set_postgresql.sh"
