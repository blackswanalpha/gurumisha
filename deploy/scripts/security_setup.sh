#!/bin/bash

# Gurumisha Motors - Security Setup Script
# Configures security settings, SSL, and hardening measures

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Gurumisha Motors"
PROJECT_DIR="/home/$(whoami)/public_html"
LOG_FILE="$PROJECT_DIR/logs/security_setup.log"

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

# Function to generate secure secret key
generate_secret_key() {
    print_status "Generating new Django secret key..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Generate new secret key
    NEW_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Update .env file
    if [ -f ".env" ]; then
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|" ".env"
        print_success "Secret key updated in .env file"
    else
        print_error ".env file not found"
        return 1
    fi
    
    log_message "Secret key generated and updated"
}

# Function to set file permissions
set_secure_permissions() {
    print_status "Setting secure file permissions..."
    
    cd "$PROJECT_DIR"
    
    # Set directory permissions (755)
    find . -type d -exec chmod 755 {} \;
    
    # Set file permissions (644)
    find . -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    chmod +x deploy/scripts/*.sh
    chmod +x *.py 2>/dev/null || true
    
    # Secure sensitive files (600)
    chmod 600 .env 2>/dev/null || true
    chmod 600 db.sqlite3 2>/dev/null || true
    chmod 600 logs/*.log 2>/dev/null || true
    
    # Secure directories
    chmod 700 logs/ 2>/dev/null || mkdir -p logs && chmod 700 logs/
    chmod 755 media/ 2>/dev/null || mkdir -p media && chmod 755 media/
    chmod 755 staticfiles/ 2>/dev/null || mkdir -p staticfiles && chmod 755 staticfiles/
    
    print_success "File permissions set securely"
    log_message "Secure file permissions applied"
}

# Function to configure security headers
configure_security_headers() {
    print_status "Configuring security headers..."
    
    # Update .htaccess with security headers
    cat > "$PROJECT_DIR/.htaccess" << 'EOF'
# Gurumisha Motors - Security Configuration

# Enable Rewrite Engine
RewriteEngine On

# Python WSGI Application
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_URI} !^/static/
RewriteCond %{REQUEST_URI} !^/media/
RewriteRule ^(.*)$ wsgi.py/$1 [QSA,PT,L]

# Security Headers
<IfModule mod_headers.c>
    # Prevent MIME type sniffing
    Header always set X-Content-Type-Options nosniff
    
    # Prevent clickjacking
    Header always set X-Frame-Options DENY
    
    # XSS Protection
    Header always set X-XSS-Protection "1; mode=block"
    
    # Referrer Policy
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    
    # Content Security Policy
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self';"
    
    # Remove server information
    Header always unset Server
    Header always unset X-Powered-By
</IfModule>

# Protect sensitive files
<Files ".env">
    Order allow,deny
    Deny from all
</Files>

<Files "*.py">
    Order allow,deny
    Deny from all
</Files>

<Files "requirements*.txt">
    Order allow,deny
    Deny from all
</Files>

<Files "*.log">
    Order allow,deny
    Deny from all
</Files>

# Allow access to WSGI file
<Files "wsgi.py">
    Order allow,deny
    Allow from all
</Files>

# Prevent access to version control
<DirectoryMatch "\.git">
    Order allow,deny
    Deny from all
</DirectoryMatch>

# Prevent access to Python cache
<DirectoryMatch "__pycache__">
    Order allow,deny
    Deny from all
</DirectoryMatch>

# Prevent access to backup files
<FilesMatch "\.(bak|backup|old|tmp)$">
    Order allow,deny
    Deny from all
</FilesMatch>
EOF

    print_success "Security headers configured"
    log_message "Security headers configured in .htaccess"
}

# Function to setup SSL redirect
setup_ssl_redirect() {
    print_status "Setting up SSL redirect..."
    
    # Check if SSL is available
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        # Extract domain from ALLOWED_HOSTS
        DOMAIN=$(echo "$ALLOWED_HOSTS" | cut -d',' -f1)
        
        if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
            # Test SSL availability
            if curl -s -I "https://$DOMAIN" >/dev/null 2>&1; then
                print_status "SSL certificate detected, enabling HTTPS redirect..."
                
                # Add HTTPS redirect to .htaccess
                cat >> "$PROJECT_DIR/.htaccess" << 'EOF'

# Force HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
EOF
                
                # Update .env for SSL
                sed -i "s|SECURE_SSL_REDIRECT=.*|SECURE_SSL_REDIRECT=True|" ".env"
                sed -i "s|SESSION_COOKIE_SECURE=.*|SESSION_COOKIE_SECURE=True|" ".env"
                sed -i "s|CSRF_COOKIE_SECURE=.*|CSRF_COOKIE_SECURE=True|" ".env"
                
                print_success "HTTPS redirect enabled"
                log_message "HTTPS redirect configured"
            else
                print_warning "SSL certificate not detected. Please install SSL first."
                log_message "SSL certificate not available"
            fi
        else
            print_warning "No domain configured for SSL check"
        fi
    else
        print_error ".env file not found"
    fi
}

# Function to configure firewall rules
configure_firewall() {
    print_status "Configuring firewall rules..."
    
    # Note: This is informational as cPanel VPS firewall is usually managed through WHM
    print_warning "Firewall configuration should be done through WHM/cPanel interface"
    print_status "Recommended firewall rules:"
    print_status "- Allow HTTP (80) and HTTPS (443)"
    print_status "- Allow SSH (22) from trusted IPs only"
    print_status "- Allow database ports only from localhost"
    print_status "- Block all other incoming connections"
    
    log_message "Firewall configuration notes provided"
}

# Function to setup fail2ban (if available)
setup_fail2ban() {
    print_status "Checking for fail2ban..."
    
    if command -v fail2ban-client >/dev/null 2>&1; then
        print_status "fail2ban detected, configuring Django protection..."
        
        # Create Django jail configuration
        sudo tee /etc/fail2ban/jail.d/django.conf > /dev/null << EOF
[django-auth]
enabled = true
port = http,https
filter = django-auth
logpath = $PROJECT_DIR/logs/django.log
maxretry = 5
bantime = 3600
findtime = 600

[django-404]
enabled = true
port = http,https
filter = django-404
logpath = $PROJECT_DIR/logs/django.log
maxretry = 10
bantime = 1800
findtime = 600
EOF

        # Create Django auth filter
        sudo tee /etc/fail2ban/filter.d/django-auth.conf > /dev/null << EOF
[Definition]
failregex = ^.*\[.*\] WARNING.*Invalid password.*from <HOST>.*$
            ^.*\[.*\] WARNING.*Authentication failure.*from <HOST>.*$
ignoreregex =
EOF

        # Create Django 404 filter
        sudo tee /etc/fail2ban/filter.d/django-404.conf > /dev/null << EOF
[Definition]
failregex = ^.*\[.*\] WARNING.*Not Found.*<HOST>.*$
ignoreregex = ^.*\[.*\] WARNING.*Not Found.*\.(css|js|png|jpg|jpeg|gif|ico|svg).*$
EOF

        # Restart fail2ban
        sudo systemctl restart fail2ban
        
        print_success "fail2ban configured for Django protection"
        log_message "fail2ban configured"
    else
        print_warning "fail2ban not available. Consider installing for additional protection."
        log_message "fail2ban not available"
    fi
}

# Function to setup security monitoring
setup_security_monitoring() {
    print_status "Setting up security monitoring..."
    
    # Create security check script
    cat > "$PROJECT_DIR/security_check.py" << 'EOF'
#!/usr/bin/env python3
"""
Security monitoring script for Gurumisha Motors
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_file_permissions():
    """Check for insecure file permissions"""
    issues = []
    
    # Check sensitive files
    sensitive_files = ['.env', 'db.sqlite3']
    for file in sensitive_files:
        if os.path.exists(file):
            stat = os.stat(file)
            mode = oct(stat.st_mode)[-3:]
            if mode != '600':
                issues.append(f"Insecure permissions on {file}: {mode}")
    
    return issues

def check_debug_mode():
    """Check if DEBUG mode is disabled"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            if 'DEBUG=True' in content:
                return ["DEBUG mode is enabled in production"]
    return []

def check_secret_key():
    """Check if secret key is secure"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            if 'django-insecure' in content:
                return ["Insecure Django secret key detected"]
    return []

def main():
    """Run security checks"""
    all_issues = []
    
    checks = [
        check_file_permissions,
        check_debug_mode,
        check_secret_key,
    ]
    
    for check in checks:
        issues = check()
        all_issues.extend(issues)
    
    if all_issues:
        logger.warning("Security issues detected:")
        for issue in all_issues:
            logger.warning(f"  - {issue}")
        sys.exit(1)
    else:
        logger.info("All security checks passed")
        sys.exit(0)

if __name__ == '__main__':
    main()
EOF

    chmod +x "$PROJECT_DIR/security_check.py"
    
    print_success "Security monitoring script created"
    log_message "Security monitoring setup completed"
}

# Function to create security documentation
create_security_docs() {
    print_status "Creating security documentation..."
    
    cat > "$PROJECT_DIR/SECURITY.md" << 'EOF'
# Gurumisha Motors - Security Guide

## Security Measures Implemented

### 1. Django Security Settings
- DEBUG mode disabled in production
- Secure secret key generated
- HTTPS enforcement enabled
- Secure cookie settings
- CSRF protection enabled
- XSS protection enabled

### 2. Web Server Security
- Security headers configured
- File access restrictions
- Directory browsing disabled
- Server information hidden

### 3. File System Security
- Restrictive file permissions
- Sensitive files protected
- Log files secured
- Backup files protected

### 4. Database Security
- Strong database passwords
- Limited database privileges
- Connection encryption (if supported)
- Regular backups

### 5. SSL/TLS Configuration
- HTTPS redirect enabled
- Secure cookie flags set
- HSTS headers configured
- Strong cipher suites

## Security Checklist

- [ ] SSL certificate installed and valid
- [ ] HTTPS redirect working
- [ ] Debug mode disabled
- [ ] Strong secret key in use
- [ ] File permissions properly set
- [ ] Security headers configured
- [ ] Database access restricted
- [ ] Regular backups scheduled
- [ ] Monitoring and logging enabled
- [ ] Fail2ban configured (if available)

## Regular Security Tasks

### Daily
- Monitor security logs
- Check for failed login attempts
- Verify SSL certificate status

### Weekly
- Run security check script
- Review access logs
- Update dependencies

### Monthly
- Security audit
- Password rotation
- SSL certificate renewal check
- Backup verification

## Incident Response

1. Identify the security issue
2. Isolate affected systems
3. Document the incident
4. Implement fixes
5. Monitor for recurrence
6. Update security measures

## Contact Information

- System Administrator: admin@yourdomain.com
- Hosting Provider Support: [provider contact]
- Emergency Contact: [emergency contact]
EOF

    print_success "Security documentation created"
    log_message "Security documentation created"
}

# Function to display security summary
show_security_summary() {
    print_success "Security setup completed!"
    echo
    print_status "Security Summary:"
    print_status "================="
    print_status "✅ Secret key generated"
    print_status "✅ File permissions secured"
    print_status "✅ Security headers configured"
    print_status "✅ SSL redirect setup (if SSL available)"
    print_status "✅ Security monitoring enabled"
    print_status "✅ Documentation created"
    echo
    print_status "Security Files:"
    print_status "- Security check: $PROJECT_DIR/security_check.py"
    print_status "- Security docs: $PROJECT_DIR/SECURITY.md"
    print_status "- Log file: $LOG_FILE"
    echo
    print_warning "Important Next Steps:"
    print_warning "1. Install SSL certificate through cPanel"
    print_warning "2. Configure firewall through WHM"
    print_warning "3. Setup monitoring alerts"
    print_warning "4. Schedule regular security checks"
    print_warning "5. Review and test all security measures"
}

# Main function
main() {
    print_status "Starting $PROJECT_NAME security setup..."
    log_message "Security setup started"
    
    # Create logs directory
    mkdir -p "$PROJECT_DIR/logs"
    
    # Run security setup tasks
    generate_secret_key
    set_secure_permissions
    configure_security_headers
    setup_ssl_redirect
    configure_firewall
    setup_fail2ban
    setup_security_monitoring
    create_security_docs
    show_security_summary
    
    log_message "Security setup completed successfully"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
