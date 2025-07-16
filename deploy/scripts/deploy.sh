#!/bin/bash

# Gurumisha Motors - Deployment Script for cPanel VPS
# This script handles the deployment process to cPanel VPS hosting

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Gurumisha Motors"
DOMAIN="yourdomain.com"  # Update with your domain
PROJECT_DIR="/home/$(whoami)/public_html"
REPO_URL="https://github.com/yourusername/gurumisha.git"  # Update with your repo
BRANCH="main"
LOG_FILE="$PROJECT_DIR/deploy.log"

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

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check Git
    if command_exists git; then
        print_success "Git found"
    else
        print_error "Git not found"
        exit 1
    fi
    
    # Check Node.js (optional)
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION found"
    else
        print_warning "Node.js not found (optional for frontend build)"
    fi
    
    log_message "System requirements checked"
}

# Function to clone or update repository
setup_repository() {
    print_status "Setting up repository..."
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        print_status "Updating existing repository..."
        cd "$PROJECT_DIR"
        git fetch origin
        git reset --hard origin/$BRANCH
        print_success "Repository updated"
    else
        print_status "Cloning repository..."
        git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
        print_success "Repository cloned"
    fi
    
    cd "$PROJECT_DIR"
    git submodule update --init --recursive
    
    log_message "Repository setup completed"
}

# Function to setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f ".env" ]; then
        if [ -f "deploy/config/.env.production" ]; then
            cp "deploy/config/.env.production" ".env"
            print_warning "Environment file created from template"
            print_warning "Please edit .env file with your production values"
        else
            print_error "Environment template not found"
            exit 1
        fi
    else
        print_success "Environment file already exists"
    fi
    
    log_message "Environment configuration setup"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is available
    if command_exists psql; then
        print_status "PostgreSQL found, setting up database..."
        
        # Read database configuration from .env
        source .env
        
        # Extract database details from DATABASE_URL
        DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
        DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
        
        # Create database if it doesn't exist
        createdb "$DB_NAME" 2>/dev/null || print_warning "Database may already exist"
        
        print_success "Database setup completed"
    else
        print_warning "PostgreSQL not found, using SQLite"
    fi
    
    log_message "Database setup completed"
}

# Function to configure web server
configure_webserver() {
    print_status "Configuring web server..."
    
    # Create .htaccess for Apache (common in cPanel)
    cat > "$PROJECT_DIR/.htaccess" << 'EOF'
# Gurumisha Motors - Apache Configuration

# Enable WSGI
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ wsgi.py/$1 [QSA,PT,L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

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

# Cache static files
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 month"
    ExpiresByType image/jpeg "access plus 1 month"
    ExpiresByType image/gif "access plus 1 month"
    ExpiresByType image/png "access plus 1 month"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/pdf "access plus 1 month"
    ExpiresByType text/javascript "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType application/x-shockwave-flash "access plus 1 month"
    ExpiresByType image/x-icon "access plus 1 year"
    ExpiresDefault "access plus 2 days"
</IfModule>
EOF

    # Copy production WSGI file
    if [ -f "deploy/config/wsgi_production.py" ]; then
        cp "deploy/config/wsgi_production.py" "$PROJECT_DIR/wsgi.py"
        print_success "WSGI configuration copied"
    fi
    
    print_success "Web server configuration completed"
    log_message "Web server configured"
}

# Function to setup SSL certificate
setup_ssl() {
    print_status "SSL certificate setup..."
    
    print_warning "SSL certificate setup must be done through cPanel interface"
    print_status "Steps to setup SSL:"
    print_status "1. Login to cPanel"
    print_status "2. Go to SSL/TLS section"
    print_status "3. Choose 'Let's Encrypt' or upload your certificate"
    print_status "4. Enable 'Force HTTPS Redirect'"
    print_status "5. Update .env file to enable SSL settings"
    
    log_message "SSL setup instructions provided"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create health check endpoint
    cat > "$PROJECT_DIR/health_check.py" << 'EOF'
#!/usr/bin/env python3
"""
Health check script for Gurumisha Motors
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings_production')
django.setup()

from django.db import connection
from django.core.cache import cache

def check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except:
        return False

def check_cache():
    try:
        cache.set('health_check', 'ok', 30)
        return cache.get('health_check') == 'ok'
    except:
        return False

def main():
    checks = {
        'database': check_database(),
        'cache': check_cache(),
    }
    
    all_ok = all(checks.values())
    
    if all_ok:
        print("OK - All systems operational")
        sys.exit(0)
    else:
        print("ERROR - System issues detected:")
        for check, status in checks.items():
            if not status:
                print(f"  - {check}: FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
EOF

    chmod +x "$PROJECT_DIR/health_check.py"
    print_success "Health check script created"
    
    log_message "Monitoring setup completed"
}

# Function to run post-deployment tests
run_tests() {
    print_status "Running post-deployment tests..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Test Django configuration
    python manage.py check --deploy
    
    # Test database connection
    python health_check.py
    
    # Test static files
    if [ -d "staticfiles" ] && [ "$(ls -A staticfiles)" ]; then
        print_success "Static files test passed"
    else
        print_error "Static files test failed"
    fi
    
    print_success "Post-deployment tests completed"
    log_message "Post-deployment tests completed"
}

# Function to display deployment summary
show_summary() {
    print_success "Deployment completed successfully!"
    echo
    print_status "Deployment Summary:"
    print_status "=================="
    print_status "Project: $PROJECT_NAME"
    print_status "Domain: $DOMAIN"
    print_status "Directory: $PROJECT_DIR"
    print_status "Log file: $LOG_FILE"
    echo
    print_status "Next Steps:"
    print_status "1. Update .env file with your production values"
    print_status "2. Setup SSL certificate through cPanel"
    print_status "3. Configure domain DNS settings"
    print_status "4. Test the application thoroughly"
    print_status "5. Setup automated backups"
    echo
    print_status "Admin Panel: https://$DOMAIN/admin/"
    print_status "Health Check: https://$DOMAIN/health_check.py"
    echo
    print_warning "Remember to keep your .env file secure and never commit it to version control!"
}

# Main deployment process
main() {
    print_status "Starting $PROJECT_NAME deployment to cPanel VPS..."
    log_message "Deployment started"
    
    # Run deployment steps
    check_requirements
    setup_repository
    setup_environment
    setup_database
    
    # Run build process
    if [ -f "$PROJECT_DIR/deploy/scripts/build.sh" ]; then
        bash "$PROJECT_DIR/deploy/scripts/build.sh"
    else
        print_error "Build script not found"
        exit 1
    fi
    
    configure_webserver
    setup_ssl
    setup_monitoring
    run_tests
    show_summary
    
    log_message "Deployment completed successfully"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
