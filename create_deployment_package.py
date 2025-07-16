#!/usr/bin/env python3
"""
Gurumisha Motors - Deployment Package Creator
Creates a deployment-ready ZIP archive for cPanel/HostPinnacle hosting
"""

import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """Create a deployment-ready package for Gurumisha Motors"""
    
    print("Creating Gurumisha Motors Deployment Package...")
    
    # Set up paths
    source_dir = Path("gurumisha")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"gurumisha_deployment_{timestamp}.zip"
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "gurumisha_deployment"
        temp_path.mkdir()
        
        print(f"Using temporary directory: {temp_path}")
        
        # Copy essential files and directories
        essential_items = [
            "gurumisha_project",
            "core",
            "templates",
            "static",
            "media",
            "server.py",
            "manage.py",
            "requirements.txt",
            "db.sqlite3",
            "serverdoc.txt",
            "DEPLOYMENT_ANALYSIS.md",
            "DEPLOYMENT_PACKAGE_GUIDE.md",
            "ENHANCED_SERVER_DOCUMENTATION.md",
            "ENHANCED_SERVER_SUMMARY.md",
            "SERVER_DOCUMENTATION.md",
            "SERVER_IMPLEMENTATION_SUMMARY.md",
            "SERVER_USAGE_GUIDE.md",
            "PLATFORM_ANALYSIS.md"
        ]
        
        print("Copying essential files...")
        for item in essential_items:
            source_path = source_dir / item
            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(source_path, temp_path / item, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo', '*.pyd'))
                else:
                    shutil.copy2(source_path, temp_path / item)
                print(f"  ✓ {item}")
            else:
                print(f"  ⚠ {item} not found, skipping")
        
        # Create necessary directories
        print("Creating necessary directories...")
        directories = ["logs", "backups", "deployment/config", "deployment/scripts"]
        for directory in directories:
            (temp_path / directory).mkdir(parents=True, exist_ok=True)
            # Create .gitkeep files
            (temp_path / directory / ".gitkeep").touch()
            print(f"  ✓ {directory}")
        
        # Copy deployment configuration files
        print("Copying deployment configuration...")
        deploy_config_source = Path("deploy/config")
        deploy_scripts_source = Path("deploy/scripts")
        
        if deploy_config_source.exists():
            shutil.copytree(deploy_config_source, temp_path / "deployment/config", dirs_exist_ok=True)
            print("  ✓ Configuration files copied")
        
        if deploy_scripts_source.exists():
            shutil.copytree(deploy_scripts_source, temp_path / "deployment/scripts", dirs_exist_ok=True)
            print("  ✓ Script files copied")
        
        # Create .htaccess file for cPanel
        print("Creating .htaccess file...")
        htaccess_content = """# Gurumisha Motors - Apache Configuration

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
"""
        
        with open(temp_path / ".htaccess", "w") as f:
            f.write(htaccess_content)
        print("  ✓ .htaccess file created")
        
        # Create .env.example file
        print("Creating .env.example file...")
        env_example_content = """# Gurumisha Motors - Environment Configuration
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
"""
        
        with open(temp_path / ".env.example", "w") as f:
            f.write(env_example_content)
        print("  ✓ .env.example file created")
        
        # Create deployment README
        print("Creating DEPLOYMENT_README.md...")
        readme_content = """# Gurumisha Motors - Deployment Package

This package contains a deployment-ready version of the Gurumisha Motors e-commerce platform.

## Quick Start

1. Upload this entire package to your cPanel/HostPinnacle server
2. SSH into your server and navigate to the uploaded directory
3. Run the automated deployment script:
   ```
   python server.py --auto-init
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
- `DEPLOYMENT_PACKAGE_GUIDE.md` (Comprehensive deployment guide)
- `DEPLOYMENT_ANALYSIS.md` (Deployment documentation analysis)
- `serverdoc.txt` (Server verification document)

## Support

For support, contact the development team.
"""
        
        with open(temp_path / "DEPLOYMENT_README.md", "w") as f:
            f.write(readme_content)
        print("  ✓ DEPLOYMENT_README.md created")
        
        # Clean up unnecessary files
        print("Cleaning up unnecessary files...")
        cleanup_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/.DS_Store",
            "**/venv",
            "**/*.log",
            "**/*.bak"
        ]
        
        for pattern in cleanup_patterns:
            for file_path in temp_path.rglob(pattern.replace("**/", "")):
                if file_path.exists():
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
        print("  ✓ Cleanup completed")
        
        # Create ZIP archive
        print(f"Creating ZIP archive: {package_name}")
        with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_path.parent)
                    zipf.write(file_path, arcname)
        
        # Get package size
        package_size = os.path.getsize(package_name)
        package_size_mb = package_size / (1024 * 1024)
        
        print(f"\n✅ Deployment package created successfully!")
        print(f"📦 Package: {package_name}")
        print(f"📏 Size: {package_size_mb:.2f} MB")
        print(f"📁 Location: {os.path.abspath(package_name)}")
        
        print(f"\n📋 Package Contents:")
        print(f"   ✓ Django project files")
        print(f"   ✓ Enhanced server.py with auto-deployment")
        print(f"   ✓ Database file (db.sqlite3)")
        print(f"   ✓ Static and media files")
        print(f"   ✓ Requirements.txt with all dependencies")
        print(f"   ✓ Documentation files")
        print(f"   ✓ cPanel configuration (.htaccess)")
        print(f"   ✓ Environment template (.env.example)")
        print(f"   ✓ Deployment scripts and configuration")
        
        print(f"\n🚀 Ready for deployment to cPanel/HostPinnacle!")
        print(f"📖 See DEPLOYMENT_README.md for deployment instructions")

if __name__ == "__main__":
    create_deployment_package()
