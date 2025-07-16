# Gurumisha Motors - Deployment Package Guide

This guide explains how to create a deployment-ready package for the Gurumisha Motors e-commerce platform and deploy it to a cPanel/HostPinnacle hosting environment.

## Creating the Deployment Package

### Files to Include

The deployment package should include the following files and directories:

```
gurumisha/
├── gurumisha_project/          # Django project configuration
├── core/                       # Main application
├── templates/                  # HTML templates
├── static/                     # Static files
├── media/                      # User uploaded files
├── server.py                   # Enhanced server script
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── db.sqlite3                  # Database file (if using SQLite)
├── serverdoc.txt               # Server verification document
├── deployment/                 # Deployment configuration
│   ├── config/                # Production configuration files
│   └── scripts/               # Deployment scripts
├── .env.example                # Environment variables template
├── .htaccess                   # Apache configuration for cPanel
└── DEPLOYMENT_README.md        # Deployment instructions
```

### Files to Exclude

The following files and directories should be excluded from the deployment package:

```
__pycache__/                    # Python bytecode cache
*.pyc                           # Compiled Python files
*.pyo                           # Optimized Python files
*.pyd                           # Python DLL files
venv/                           # Virtual environment
.git/                           # Git repository
.idea/                          # IDE configuration
.vscode/                        # VS Code configuration
*.log                           # Log files
*.bak                           # Backup files
```

### Creating the Package Manually

1. Create a clean directory for the deployment package:
   ```bash
   mkdir -p gurumisha_deployment
   ```

2. Copy all necessary files:
   ```bash
   cp -r gurumisha/gurumisha_project gurumisha_deployment/
   cp -r gurumisha/core gurumisha_deployment/
   cp -r gurumisha/templates gurumisha_deployment/
   cp -r gurumisha/static gurumisha_deployment/
   cp -r gurumisha/media gurumisha_deployment/
   cp gurumisha/server.py gurumisha_deployment/
   cp gurumisha/manage.py gurumisha_deployment/
   cp gurumisha/requirements.txt gurumisha_deployment/
   cp gurumisha/db.sqlite3 gurumisha_deployment/
   cp gurumisha/serverdoc.txt gurumisha_deployment/
   ```

3. Create necessary directories:
   ```bash
   mkdir -p gurumisha_deployment/logs
   mkdir -p gurumisha_deployment/backups
   mkdir -p gurumisha_deployment/deployment/config
   mkdir -p gurumisha_deployment/deployment/scripts
   ```

4. Copy deployment configuration files:
   ```bash
   cp -r deploy/config/* gurumisha_deployment/deployment/config/
   cp -r deploy/scripts/* gurumisha_deployment/deployment/scripts/
   ```

5. Create .htaccess file for cPanel:
   ```bash
   cat > gurumisha_deployment/.htaccess << 'EOF'
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

6. Create .env.example file:
   ```bash
   cat > gurumisha_deployment/.env.example << 'EOF'
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
   EOF
   ```

7. Create deployment README:
   ```bash
   cat > gurumisha_deployment/DEPLOYMENT_README.md << 'EOF'
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
   ```

8. Remove unnecessary files:
   ```bash
   find gurumisha_deployment -name "__pycache__" -type d -exec rm -rf {} +
   find gurumisha_deployment -name "*.pyc" -type f -delete
   find gurumisha_deployment -name "*.pyo" -type f -delete
   find gurumisha_deployment -name "*.pyd" -type f -delete
   find gurumisha_deployment -name ".DS_Store" -type f -delete
   find gurumisha_deployment -name ".git*" -type f -delete
   find gurumisha_deployment -name ".idea" -type d -exec rm -rf {} +
   find gurumisha_deployment -name ".vscode" -type d -exec rm -rf {} +
   find gurumisha_deployment -name "venv" -type d -exec rm -rf {} +
   find gurumisha_deployment -name "*.log" -type f -delete
   find gurumisha_deployment -name "*.bak" -type f -delete
   ```

9. Create ZIP archive:
   ```bash
   zip -r gurumisha_deployment.zip gurumisha_deployment
   ```

## Deploying to cPanel/HostPinnacle

### Prerequisites

- cPanel/HostPinnacle hosting account
- SSH access to the server
- Python 3.10+ installed on the server
- Domain name pointed to the server

### Deployment Steps

1. **Upload the Package**
   - Upload the ZIP file to your server using cPanel File Manager or FTP
   - Extract the ZIP file in your public_html directory

2. **Configure Python Application**
   - Login to cPanel
   - Navigate to "Setup Python App"
   - Create a new application:
     - Python version: 3.10+ (latest available)
     - Application root: `/public_html`
     - Application URL: `yourdomain.com`
     - Application startup file: `wsgi.py`
     - Application Entry point: `application`

3. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Edit `.env` with your production values
   - Generate a secure secret key:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

4. **Run the Server Script**
   - SSH into your server
   - Navigate to your public_html directory
   - Run the server script with auto-initialization:
     ```bash
     python server.py --auto-init
     ```

5. **Configure SSL Certificate**
   - Login to cPanel
   - Navigate to "SSL/TLS"
   - Install Let's Encrypt certificate for your domain
   - Enable "Force HTTPS Redirect"

6. **Verify Deployment**
   - Visit your domain in a web browser
   - Login to the admin panel with the default credentials
   - Change the default admin password immediately

## Troubleshooting

### Common Issues

1. **Python Version Not Supported**
   - Contact your hosting provider to enable Python 3.10+
   - Use Python Selector in cPanel if available

2. **Permission Denied Errors**
   - Fix file permissions:
     ```bash
     chmod -R 755 ~/public_html
     chown -R yourusername:yourusername ~/public_html
     ```

3. **Database Connection Failed**
   - Verify database credentials in .env file
   - Check if database server is running
   - Ensure database user has proper privileges

4. **Static Files Not Loading**
   - Recollect static files:
     ```bash
     python server.py --collect-static
     ```
   - Check .htaccess configuration

5. **500 Internal Server Error**
   - Check error logs:
     ```bash
     tail -f ~/public_html/logs/django_error.log
     ```

## Maintenance

### Backup Strategy

1. **Database Backups**
   - Run daily backups:
     ```bash
     python server.py --backup-db
     ```
   - Store backups off-site

2. **File Backups**
   - Backup media files regularly
   - Backup configuration files

### Updates and Upgrades

1. **Dependency Updates**
   - Update dependencies:
     ```bash
     python server.py --upgrade-deps
     ```

2. **Security Updates**
   - Run security scan:
     ```bash
     python server.py --security-scan
     ```

3. **Performance Optimization**
   - Monitor system performance:
     ```bash
     python server.py --stats
     ```
