#!/bin/bash

# Create Deployment Package for Gurumisha Motors
# This script creates a deployment-ready ZIP archive of the Gurumisha project
# with all necessary files for cPanel/HostPinnacle deployment

# Set variables
SOURCE_DIR="gurumisha"
PACKAGE_NAME="gurumisha_deployment_$(date +%Y%m%d).zip"
TEMP_DIR="gurumisha_temp"

# Create temporary directory
echo "Creating temporary directory..."
mkdir -p "$TEMP_DIR"

# Copy all files to temporary directory
echo "Copying files to temporary directory..."
cp -r "$SOURCE_DIR"/* "$TEMP_DIR"/

# Create logs directory (will be needed in production)
mkdir -p "$TEMP_DIR/logs"
touch "$TEMP_DIR/logs/.gitkeep"

# Create backups directory
mkdir -p "$TEMP_DIR/backups"
touch "$TEMP_DIR/backups/.gitkeep"

# Create deployment directory structure
mkdir -p "$TEMP_DIR/deployment/config"
mkdir -p "$TEMP_DIR/deployment/scripts"

# Copy deployment files
echo "Copying deployment configuration files..."
cp -r deploy/config/* "$TEMP_DIR/deployment/config/"
cp -r deploy/scripts/* "$TEMP_DIR/deployment/scripts/"

# Make scripts executable
chmod +x "$TEMP_DIR/deployment/scripts/"*.sh

# Create .htaccess file for cPanel
echo "Creating .htaccess file for cPanel..."
cat > "$TEMP_DIR/.htaccess" << 'EOF'
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

# Create .env.example file
echo "Creating .env.example file..."
cat > "$TEMP_DIR/.env.example" << 'EOF'
# Gurumisha Motors - Environment Configuration
# Rename this file to .env and update with your values

# Core Settings
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Database Configuration
# For SQLite (development):
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL (production):
# DATABASE_URL=postgresql://gurumisha_user:your_password@localhost:5432/gurumisha_db
# For MySQL (production):
# DATABASE_URL=mysql://gurumisha_user:your_password@localhost:3306/gurumisha_db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=kamandembugua18@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=Gurumisha <kamandembugua18@gmail.com>
SERVER_EMAIL=kamandembugua18@gmail.com

# M-Pesa Configuration
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your-production-key
MPESA_CONSUMER_SECRET=your-production-secret
MPESA_BUSINESS_SHORT_CODE=your-shortcode
MPESA_PASSKEY=your-production-passkey

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Redis Cache (optional)
# REDIS_URL=redis://127.0.0.1:6379/1

# AWS S3 Storage (optional)
# USE_S3=True
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=us-east-1

# Error Reporting (optional)
# SENTRY_DSN=your-sentry-dsn
EOF

# Create deployment README
echo "Creating deployment README..."
cat > "$TEMP_DIR/DEPLOYMENT_README.md" << 'EOF'
# Gurumisha Motors - Deployment Package

This package contains a deployment-ready version of the Gurumisha Motors e-commerce platform.

## Quick Start

1. Upload this entire package to your cPanel/HostPinnacle server
2. SSH into your server and navigate to the uploaded directory
3. Run the automated deployment script:
   ```
   ./deployment/scripts/deploy.sh
   ```

## Manual Deployment Steps

If you prefer to deploy manually, follow these steps:

1. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env with your production values
   ```

4. Run the server.py script with auto-initialization:
   ```
   python server.py --auto-init
   ```

## Configuration

See the `.env.example` file for all required configuration variables.

## Superuser Account

The deployment automatically creates a superuser with these credentials:
- Username: admin
- Email: admin@gurumisha.com
- Password: admin123

**IMPORTANT:** Change these credentials immediately after deployment!

## Documentation

For detailed deployment instructions, see:
- `deploy/docs/CPANEL_VPS_DEPLOYMENT_GUIDE.md`
- `serverdoc.txt` (Server verification document)

## Support

For support, contact the development team.
EOF

# Remove unnecessary files
echo "Removing unnecessary files..."
find "$TEMP_DIR" -name "__pycache__" -type d -exec rm -rf {} +
find "$TEMP_DIR" -name "*.pyc" -type f -delete
find "$TEMP_DIR" -name "*.pyo" -type f -delete
find "$TEMP_DIR" -name "*.pyd" -type f -delete
find "$TEMP_DIR" -name ".DS_Store" -type f -delete
find "$TEMP_DIR" -name ".git*" -type f -delete
find "$TEMP_DIR" -name ".idea" -type d -exec rm -rf {} +
find "$TEMP_DIR" -name ".vscode" -type d -exec rm -rf {} +
find "$TEMP_DIR" -name "venv" -type d -exec rm -rf {} +
find "$TEMP_DIR" -name "*.log" -type f -delete
find "$TEMP_DIR" -name "*.bak" -type f -delete

# Create ZIP archive
echo "Creating deployment package..."
zip -r "$PACKAGE_NAME" "$TEMP_DIR"

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Deployment package created: $PACKAGE_NAME"
echo "Package is ready for upload to cPanel/HostPinnacle hosting."
