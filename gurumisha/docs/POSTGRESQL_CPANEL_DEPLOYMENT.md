# PostgreSQL cPanel Deployment Guide for Gurumisha Motors

## Overview

This comprehensive guide provides step-by-step instructions for deploying the Gurumisha Motors Django application with PostgreSQL database on cPanel hosting environments. This guide covers both shared hosting and VPS scenarios.

## Prerequisites

### System Requirements
- **cPanel hosting account** with PostgreSQL support
- **Python 3.10+** support (verify with hosting provider)
- **PostgreSQL 12+** (Django 4.2+ requirement - **CRITICAL**)
- **SSH access** (for VPS or advanced shared hosting)
- **Domain name** configured and pointing to hosting server
- **SSL certificate** (recommended for production)

### Required Information
Before starting, gather the following information from your hosting provider:
- cPanel login credentials
- Database server hostname (usually `localhost` or specific server IP)
- **PostgreSQL version supported** (must be 12 or later)
- Python version available
- SSH access details (if available)

### ⚠️ PostgreSQL Version Compatibility
**IMPORTANT**: Django 4.2+ requires PostgreSQL 12 or later. If your hosting provider only supports PostgreSQL 10.x or 11.x, you have these options:
1. **Request PostgreSQL upgrade** from your hosting provider (recommended)
2. **Use SQLite fallback** temporarily (see Troubleshooting section)
3. **Downgrade Django** to version 3.2 LTS (supports PostgreSQL 9.6+)

## Phase 1: Database Setup

### Step 1: Create PostgreSQL Database via cPanel

1. **Login to cPanel**
   - Access your cPanel dashboard
   - Navigate to "Databases" section

2. **Create PostgreSQL Database**
   ```
   Database Name: gurumisha_db
   ```
   - Click "PostgreSQL Databases"
   - Enter database name: `gurumisha_db`
   - Click "Create Database"

3. **Create Database User**
   ```
   Username: gurumisha_user
   Password: [Generate strong password]
   ```
   - In "PostgreSQL Users" section
   - Create new user: `gurumisha_user`
   - Generate a strong password (save this securely)
   - Click "Create User"

4. **Grant User Privileges**
   - In "Add User to Database" section
   - Select user: `gurumisha_user`
   - Select database: `gurumisha_db`
   - Grant "ALL PRIVILEGES"
   - Click "Add"

### Step 2: Configure Database Connection

Create or update your `.env` file with database credentials:

```env
# Database Configuration
DB_NAME=gurumisha_db
DB_USER=gurumisha_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Full Database URL (alternative format)
DATABASE_URL=postgresql://gurumisha_user:your_secure_password_here@localhost:5432/gurumisha_db

# Django Settings
DEBUG=False
SECRET_KEY=your_django_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration
EMAIL_HOST=your_smtp_server
EMAIL_PORT=587
EMAIL_HOST_USER=admin@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=admin@yourdomain.com
```

## Phase 2: Application Deployment

### Step 3: Upload Application Files

**Option A: Using cPanel File Manager**
1. Create deployment package:
   ```bash
   # On your local machine
   cd gurumisha
   zip -r gurumisha_deployment.zip . -x "venv/*" "__pycache__/*" "*.pyc" "db.sqlite3" ".git/*"
   ```

2. Upload via cPanel File Manager:
   - Navigate to `public_html` directory
   - Upload `gurumisha_deployment.zip`
   - Extract the archive
   - Delete the zip file

**Option B: Using SSH (if available)**
```bash
# Connect via SSH
ssh username@your-server.com

# Navigate to public_html
cd public_html

# Clone repository (if Git is available)
git clone https://github.com/blackswanalpha/gurumisha.git .

# Or upload files using SCP/SFTP
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Django Settings

Update `gurumisha_project/settings.py` for production:

```python
# Production Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='gurumisha_db'),
        'USER': config('DB_USER', default='gurumisha_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 60,
            'sslmode': 'prefer',  # Use SSL if available
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Phase 3: Database Migration and Setup

### Step 6: Run Database Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Load initial data
python manage.py populate_car_models
python manage.py create_initial_users
```

### Step 7: Test Database Connection

```bash
# Test database connection
python manage.py dbshell

# In PostgreSQL shell, run:
\dt  # List tables
\q   # Quit
```

## Phase 4: Web Server Configuration

### Step 8: Configure WSGI Application

Create `passenger_wsgi.py` in your domain root:

```python
#!/usr/bin/env python3
import sys
import os

# Add your project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 9: Configure Static Files

Update your `.htaccess` file:

```apache
RewriteEngine On
RewriteBase /

# Serve static files directly
RewriteRule ^static/(.*)$ /static/$1 [L]
RewriteRule ^media/(.*)$ /media/$1 [L]

# Route everything else to Django
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ passenger_wsgi.py/$1 [QSA,L]
```

## Phase 5: Production Optimization

### Step 10: Database Performance Tuning

```sql
-- Connect to PostgreSQL and run these optimizations
-- (Run via cPanel phpPgAdmin or command line)

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_cars_brand_id ON core_car(brand_id);
CREATE INDEX CONCURRENTLY idx_cars_model_id ON core_car(model_id);
CREATE INDEX CONCURRENTLY idx_cars_status ON core_car(status);
CREATE INDEX CONCURRENTLY idx_cars_is_featured ON core_car(is_featured);
CREATE INDEX CONCURRENTLY idx_cars_price ON core_car(price);
CREATE INDEX CONCURRENTLY idx_cars_year ON core_car(year);

-- Analyze tables for query optimization
ANALYZE;
```

### Step 11: Setup Backup Strategy

Create backup script `backup_database.sh`:

```bash
#!/bin/bash
# PostgreSQL Database Backup Script

# Configuration
DB_NAME="gurumisha_db"
DB_USER="gurumisha_user"
DB_HOST="localhost"
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
PGPASSWORD="$DB_PASSWORD" pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/gurumisha_backup_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/gurumisha_backup_$DATE.sql"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "gurumisha_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: gurumisha_backup_$DATE.sql.gz"
```

## Phase 6: Monitoring and Maintenance

### Step 12: Setup Logging

Configure Django logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/username/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### Step 13: Health Check Script

Create `health_check.py`:

```python
#!/usr/bin/env python3
import os
import sys
import django
from django.db import connection
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

def check_database():
    """Check database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

def check_static_files():
    """Check if static files are accessible"""
    import os
    from django.conf import settings

    static_root = settings.STATIC_ROOT
    if os.path.exists(static_root) and os.listdir(static_root):
        return True
    return False

if __name__ == "__main__":
    print("Running Gurumisha Health Check...")

    db_ok = check_database()
    static_ok = check_static_files()

    print(f"Database: {'✓' if db_ok else '✗'}")
    print(f"Static Files: {'✓' if static_ok else '✗'}")

    if db_ok and static_ok:
        print("All systems operational!")
        sys.exit(0)
    else:
        print("Some systems need attention!")
        sys.exit(1)
```

## Troubleshooting

### Common Issues and Solutions

1. **PostgreSQL Version Compatibility Error** ⚠️ **CRITICAL**
   ```
   django.db.utils.NotSupportedError: PostgreSQL 12 or later is required (found 10.23).
   ```

   **Solution A: Request PostgreSQL Upgrade (Recommended)**
   - Contact your hosting provider to upgrade PostgreSQL to version 12+
   - This is the best long-term solution for production

   **Solution B: Use SQLite Fallback (Temporary)**
   ```bash
   # Set environment variable to use SQLite
   export USE_SQLITE=True

   # Or add to .env file
   echo "USE_SQLITE=True" >> .env

   # Run migrations with SQLite
   python manage.py migrate
   ```

   **Solution C: Downgrade Django (Not Recommended)**
   ```bash
   # Downgrade to Django 3.2 LTS (supports PostgreSQL 9.6+)
   pip install "Django>=3.2,<4.0"
   ```

2. **Database Connection Errors**
   ```
   Error: FATAL: password authentication failed
   ```
   - Verify database credentials in `.env` file
   - Check user privileges in cPanel PostgreSQL section
   - Ensure database user has correct permissions

3. **Static Files Not Loading**
   ```
   Error: Static files not found
   ```
   - Run `python manage.py collectstatic`
   - Check `.htaccess` configuration
   - Verify `STATIC_ROOT` and `STATIC_URL` settings

4. **Permission Errors**
   ```
   Error: Permission denied
   ```
   - Set correct file permissions:
     ```bash
     chmod 755 passenger_wsgi.py
     chmod -R 755 static/
     chmod -R 755 media/
     ```

5. **Memory Errors**
   ```
   Error: Memory limit exceeded
   ```
   - Optimize Django settings for shared hosting
   - Use database connection pooling
   - Implement caching strategies

### Performance Optimization Tips

1. **Database Optimization**
   - Use database indexes on frequently queried fields
   - Implement query optimization with `select_related()` and `prefetch_related()`
   - Use database connection pooling

2. **Caching Strategy**
   ```python
   # Add to settings.py
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
           'LOCATION': 'cache_table',
       }
   }
   ```

3. **Static File Optimization**
   - Use CDN for static files (if available)
   - Enable gzip compression
   - Optimize images and CSS/JS files

## Security Checklist

- [ ] Database user has minimal required privileges
- [ ] Strong passwords for all accounts
- [ ] SSL certificate installed and configured
- [ ] Django security settings enabled
- [ ] Regular security updates applied
- [ ] Backup strategy implemented
- [ ] Monitoring and logging configured
- [ ] Error pages customized (no debug information)

## Maintenance Schedule

### Daily
- Monitor application logs
- Check database connectivity
- Verify backup completion

### Weekly
- Review performance metrics
- Update dependencies (if needed)
- Clean up old log files

### Monthly
- Security audit
- Database optimization
- Backup restoration test

## Support and Resources

### Documentation Links
- [Django PostgreSQL Documentation](https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes)
- [cPanel Documentation](https://docs.cpanel.net/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Emergency Contacts
- Hosting Provider Support
- Database Administrator
- Application Developer

---

**Note**: This guide assumes a standard cPanel hosting environment. Some steps may vary depending on your specific hosting provider's configuration. Always consult your hosting provider's documentation for provider-specific instructions.
