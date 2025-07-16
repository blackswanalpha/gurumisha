# Gurumisha Motors - cPanel VPS Deployment Guide

## Overview

This comprehensive guide walks you through deploying the Gurumisha Motors Django application on a cPanel VPS hosting environment. The deployment includes database setup, SSL configuration, static file serving, and production optimizations.

## Prerequisites

### System Requirements
- **VPS with cPanel/WHM access**
- **Python 3.10+** (check with hosting provider)
- **Node.js 16+** (for frontend build process)
- **PostgreSQL or MySQL** database access
- **SSH access** to the server
- **Domain name** pointed to your VPS

### Before You Start
- [ ] Backup your current website (if any)
- [ ] Ensure you have cPanel login credentials
- [ ] Verify SSH access to your VPS
- [ ] Have your domain DNS configured
- [ ] Prepare your database credentials

## Phase 1: Server Preparation

### Step 1: Access Your VPS
```bash
# SSH into your VPS
ssh username@your-server-ip

# Or use cPanel Terminal if available
```

### Step 2: Verify Python Installation
```bash
# Check Python version
python3 --version

# If Python 3.10+ is not available, contact your hosting provider
# Some cPanel hosts require enabling Python through cPanel interface
```

### Step 3: Create Project Directory
```bash
# Navigate to your domain's public_html directory
cd ~/public_html

# Create backup of existing files (if any)
mkdir -p ~/backups/website_backup_$(date +%Y%m%d)
cp -r * ~/backups/website_backup_$(date +%Y%m%d)/ 2>/dev/null || true

# Clear public_html for new deployment
rm -rf * .[^.]* 2>/dev/null || true
```

## Phase 2: Code Deployment

### Step 4: Clone Repository
```bash
# Clone your Gurumisha repository
git clone https://github.com/yourusername/gurumisha.git .

# Or upload files via cPanel File Manager if Git is not available
# Download the deploy folder from this repository and upload it
```

### Step 5: Setup Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 6: Install Dependencies
```bash
# Install production requirements
pip install -r deploy/config/requirements_production.txt

# If you encounter permission errors, contact your hosting provider
```

## Phase 3: Database Configuration

### Step 7: Create Database (via cPanel)
1. **Login to cPanel**
2. **Navigate to "MySQL Databases" or "PostgreSQL Databases"**
3. **Create new database:**
   - Database name: `gurumisha_db`
   - Username: `gurumisha_user`
   - Password: `[strong_password]`
4. **Grant all privileges to the user**
5. **Note down the database connection details**

### Step 8: Configure Environment Variables
```bash
# Copy environment template
cp deploy/config/.env.production .env

# Edit environment file
nano .env
```

**Update the following values in .env:**
```env
# Replace with your actual values
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Database configuration
DATABASE_URL=postgresql://gurumisha_user:your_password@localhost:5432/gurumisha_db
# OR for MySQL:
# DATABASE_URL=mysql://gurumisha_user:your_password@localhost:3306/gurumisha_db

# Email configuration
EMAIL_HOST_PASSWORD=your-gmail-app-password

# M-Pesa production credentials
MPESA_CONSUMER_KEY=your-production-key
MPESA_CONSUMER_SECRET=your-production-secret
MPESA_BUSINESS_SHORT_CODE=your-shortcode
MPESA_PASSKEY=your-production-passkey
```

### Step 9: Generate Secret Key
```bash
# Generate a new Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy the output and update SECRET_KEY in .env file
```

## Phase 4: Application Setup

### Step 10: Run Build Script
```bash
# Make sure you're in the project directory
cd ~/public_html

# Run the automated build script
./deploy/scripts/build.sh

# This script will:
# - Setup virtual environment
# - Install dependencies
# - Build frontend assets
# - Collect static files
# - Run database migrations
# - Create superuser account
# - Set file permissions
```

### Step 11: Configure Production Settings
```bash
# Copy production settings
cp deploy/config/settings_production.py gurumisha_project/settings_production.py

# Copy production WSGI
cp deploy/config/wsgi_production.py wsgi.py
```

## Phase 5: Web Server Configuration

### Step 12: Configure Apache (cPanel)
```bash
# Create .htaccess file for Apache
cat > .htaccess << 'EOF'
# Gurumisha Motors - Apache Configuration

# Python WSGI Application
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ wsgi.py/$1 [QSA,PT,L]

# Security Headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# Static Files Caching
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
</IfModule>

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
EOF
```

### Step 13: Setup Python App (cPanel Interface)
1. **Login to cPanel**
2. **Navigate to "Setup Python App"**
3. **Create New Application:**
   - Python version: 3.10+ (latest available)
   - Application root: `/public_html`
   - Application URL: `yourdomain.com`
   - Application startup file: `wsgi.py`
   - Application Entry point: `application`
4. **Click "Create"**

### Step 14: Configure Static Files Serving
```bash
# Create symbolic link for static files (if needed)
ln -sf ~/public_html/staticfiles ~/public_html/static

# Set proper permissions
chmod -R 755 staticfiles/
chmod -R 755 media/
```

## Phase 6: SSL and Security

### Step 15: Install SSL Certificate
1. **Login to cPanel**
2. **Navigate to "SSL/TLS"**
3. **Choose "Let's Encrypt" (recommended) or upload your certificate**
4. **Enable "Force HTTPS Redirect"**
5. **Update .env file:**
   ```env
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

### Step 16: Security Hardening
```bash
# Set restrictive file permissions
find ~/public_html -type f -exec chmod 644 {} \;
find ~/public_html -type d -exec chmod 755 {} \;

# Protect sensitive files
chmod 600 .env
chmod 600 db.sqlite3 2>/dev/null || true

# Make scripts executable
chmod +x deploy/scripts/*.sh
```

## Phase 7: Testing and Validation

### Step 17: Test Application
```bash
# Run health check
python3 health_check.py

# Test Django configuration
source venv/bin/activate
export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
python manage.py check --deploy

# Test database connection
python manage.py dbshell --command="SELECT 1;"
```

### Step 18: Access Your Site
1. **Visit your domain:** `https://yourdomain.com`
2. **Test key functionality:**
   - Homepage loads correctly
   - User registration/login
   - Car listings display
   - Admin panel access: `https://yourdomain.com/admin/`
   - Static files load (CSS, JS, images)

## Phase 8: Monitoring and Maintenance

### Step 19: Setup Automated Backups
```bash
# Create backup directory
mkdir -p ~/backups/gurumisha

# Setup cron job for daily backups
crontab -e

# Add this line for daily backup at 2 AM:
0 2 * * * /home/yourusername/public_html/deploy/scripts/backup.sh
```

### Step 20: Setup Monitoring
```bash
# Create health check cron job (every 5 minutes)
*/5 * * * * /home/yourusername/public_html/health_check.py

# Setup weekly maintenance (Sundays at 3 AM)
0 3 * * 0 /home/yourusername/public_html/deploy/scripts/maintenance.sh
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Python Version Not Supported
**Solution:** Contact your hosting provider to enable Python 3.10+ or use Python Selector in cPanel.

#### Issue 2: Permission Denied Errors
**Solution:** 
```bash
# Fix file permissions
chmod -R 755 ~/public_html
chown -R yourusername:yourusername ~/public_html
```

#### Issue 3: Database Connection Failed
**Solution:**
- Verify database credentials in .env file
- Check if database server is running
- Ensure database user has proper privileges

#### Issue 4: Static Files Not Loading
**Solution:**
```bash
# Recollect static files
source venv/bin/activate
python manage.py collectstatic --clear --noinput

# Check .htaccess configuration
# Verify static files permissions
```

#### Issue 5: 500 Internal Server Error
**Solution:**
```bash
# Check error logs
tail -f ~/public_html/logs/django_error.log

# Check Apache error logs (location varies by host)
tail -f /var/log/apache2/error.log
```

#### Issue 6: SSL Certificate Issues
**Solution:**
- Verify domain DNS is pointing to your server
- Check SSL certificate installation in cPanel
- Ensure HTTPS redirect is properly configured

### Performance Optimization

#### Enable Caching
```bash
# Install Redis (if available)
pip install redis django-redis

# Update .env file
REDIS_URL=redis://127.0.0.1:6379/1
```

#### Database Optimization
```bash
# Run weekly database optimization
./deploy/scripts/maintenance.sh
```

## Post-Deployment Checklist

- [ ] Application loads without errors
- [ ] SSL certificate is installed and working
- [ ] Database is properly configured and accessible
- [ ] Static files are serving correctly
- [ ] Email functionality is working
- [ ] Admin panel is accessible
- [ ] User registration/login works
- [ ] M-Pesa integration is configured (for production)
- [ ] Automated backups are scheduled
- [ ] Monitoring is setup
- [ ] Error logging is configured
- [ ] Performance optimization is applied

## Maintenance Schedule

### Daily
- Monitor application health
- Check error logs
- Verify backup completion

### Weekly
- Run maintenance script
- Review performance metrics
- Update dependencies (if needed)

### Monthly
- Security audit
- Database optimization
- SSL certificate check
- Backup verification

## Support and Resources

### Documentation
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- cPanel Documentation: https://docs.cpanel.net/
- Let's Encrypt: https://letsencrypt.org/

### Emergency Contacts
- Hosting Provider Support
- Domain Registrar Support
- SSL Certificate Provider

### Backup and Recovery
- Database backups: `~/backups/gurumisha/database/`
- Media backups: `~/backups/gurumisha/media/`
- Configuration backups: `~/backups/gurumisha/config/`

Remember to keep your deployment secure, regularly updated, and properly monitored for optimal performance and security.
