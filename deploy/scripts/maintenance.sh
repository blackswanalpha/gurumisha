#!/bin/bash

# Gurumisha Motors - Maintenance Script
# System maintenance, updates, and health checks

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
LOG_FILE="$PROJECT_DIR/logs/maintenance.log"

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

# Function to check disk space
check_disk_space() {
    print_status "Checking disk space..."
    
    # Get disk usage for project directory
    DISK_USAGE=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt 90 ]; then
        print_error "Disk space critical: ${DISK_USAGE}% used"
        log_message "CRITICAL: Disk space at ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -gt 80 ]; then
        print_warning "Disk space warning: ${DISK_USAGE}% used"
        log_message "WARNING: Disk space at ${DISK_USAGE}%"
    else
        print_success "Disk space OK: ${DISK_USAGE}% used"
        log_message "Disk space check passed: ${DISK_USAGE}%"
    fi
}

# Function to check memory usage
check_memory() {
    print_status "Checking memory usage..."
    
    # Get memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [ "$MEMORY_USAGE" -gt 90 ]; then
        print_error "Memory usage critical: ${MEMORY_USAGE}%"
        log_message "CRITICAL: Memory usage at ${MEMORY_USAGE}%"
    elif [ "$MEMORY_USAGE" -gt 80 ]; then
        print_warning "Memory usage warning: ${MEMORY_USAGE}%"
        log_message "WARNING: Memory usage at ${MEMORY_USAGE}%"
    else
        print_success "Memory usage OK: ${MEMORY_USAGE}%"
        log_message "Memory check passed: ${MEMORY_USAGE}%"
    fi
}

# Function to check database health
check_database() {
    print_status "Checking database health..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Test database connection
    if python manage.py dbshell --command="SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connection OK"
        log_message "Database connection test passed"
    else
        print_error "Database connection failed"
        log_message "ERROR: Database connection failed"
        return 1
    fi
    
    # Check for pending migrations
    PENDING_MIGRATIONS=$(python manage.py showmigrations --plan | grep -c "\[ \]" || true)
    if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
        print_warning "$PENDING_MIGRATIONS pending migrations found"
        log_message "WARNING: $PENDING_MIGRATIONS pending migrations"
    else
        print_success "All migrations applied"
        log_message "Migration check passed"
    fi
}

# Function to check application health
check_application() {
    print_status "Checking application health..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Run Django system checks
    if python manage.py check --deploy >/dev/null 2>&1; then
        print_success "Django system checks passed"
        log_message "Django system checks passed"
    else
        print_error "Django system checks failed"
        log_message "ERROR: Django system checks failed"
        return 1
    fi
    
    # Check if health check script exists and run it
    if [ -f "$PROJECT_DIR/health_check.py" ]; then
        if python health_check.py >/dev/null 2>&1; then
            print_success "Application health check passed"
            log_message "Application health check passed"
        else
            print_error "Application health check failed"
            log_message "ERROR: Application health check failed"
            return 1
        fi
    fi
}

# Function to clean temporary files
clean_temp_files() {
    print_status "Cleaning temporary files..."
    
    # Clean Django cache
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    python manage.py clearsessions
    print_success "Django sessions cleaned"
    
    # Clean Python cache files
    find "$PROJECT_DIR" -name "*.pyc" -delete
    find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    print_success "Python cache files cleaned"
    
    # Clean log files older than 30 days
    if [ -d "$PROJECT_DIR/logs" ]; then
        find "$PROJECT_DIR/logs" -name "*.log" -mtime +30 -delete
        print_success "Old log files cleaned"
    fi
    
    log_message "Temporary files cleanup completed"
}

# Function to optimize database
optimize_database() {
    print_status "Optimizing database..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
    fi
    
    # Check database type and optimize accordingly
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        # PostgreSQL optimization
        print_status "Running PostgreSQL VACUUM..."
        python manage.py dbshell --command="VACUUM ANALYZE;" >/dev/null 2>&1 || print_warning "VACUUM failed"
        print_success "PostgreSQL optimization completed"
        
    elif [[ "$DATABASE_URL" == mysql* ]]; then
        # MySQL optimization
        print_status "Running MySQL OPTIMIZE..."
        python manage.py dbshell --command="OPTIMIZE TABLE;" >/dev/null 2>&1 || print_warning "OPTIMIZE failed"
        print_success "MySQL optimization completed"
        
    else
        # SQLite optimization
        if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
            print_status "Running SQLite VACUUM..."
            sqlite3 "$PROJECT_DIR/db.sqlite3" "VACUUM;" >/dev/null 2>&1 || print_warning "VACUUM failed"
            print_success "SQLite optimization completed"
        fi
    fi
    
    log_message "Database optimization completed"
}

# Function to update dependencies
update_dependencies() {
    print_status "Checking for dependency updates..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Check for outdated packages
    OUTDATED=$(pip list --outdated --format=freeze | wc -l)
    
    if [ "$OUTDATED" -gt 0 ]; then
        print_warning "$OUTDATED packages have updates available"
        print_status "Run 'pip list --outdated' to see details"
        log_message "WARNING: $OUTDATED packages have updates available"
    else
        print_success "All packages are up to date"
        log_message "All packages are up to date"
    fi
}

# Function to check SSL certificate
check_ssl() {
    print_status "Checking SSL certificate..."
    
    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    fi
    
    # Extract domain from ALLOWED_HOSTS
    DOMAIN=$(echo "$ALLOWED_HOSTS" | cut -d',' -f1)
    
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
        # Check SSL certificate expiration
        SSL_EXPIRY=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
        
        if [ -n "$SSL_EXPIRY" ]; then
            SSL_EXPIRY_EPOCH=$(date -d "$SSL_EXPIRY" +%s)
            CURRENT_EPOCH=$(date +%s)
            DAYS_UNTIL_EXPIRY=$(( (SSL_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
            
            if [ "$DAYS_UNTIL_EXPIRY" -lt 7 ]; then
                print_error "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
                log_message "CRITICAL: SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
            elif [ "$DAYS_UNTIL_EXPIRY" -lt 30 ]; then
                print_warning "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
                log_message "WARNING: SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
            else
                print_success "SSL certificate valid for $DAYS_UNTIL_EXPIRY days"
                log_message "SSL certificate check passed: $DAYS_UNTIL_EXPIRY days remaining"
            fi
        else
            print_warning "Could not check SSL certificate"
            log_message "WARNING: SSL certificate check failed"
        fi
    else
        print_warning "No domain configured for SSL check"
        log_message "SSL check skipped: no domain configured"
    fi
}

# Function to generate maintenance report
generate_report() {
    print_status "Generating maintenance report..."
    
    REPORT_FILE="$PROJECT_DIR/logs/maintenance_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
Gurumisha Motors - Maintenance Report
Generated: $(date)

=== SYSTEM STATUS ===
Hostname: $(hostname)
Uptime: $(uptime)
Load Average: $(uptime | awk -F'load average:' '{print $2}')

=== DISK USAGE ===
$(df -h "$PROJECT_DIR")

=== MEMORY USAGE ===
$(free -h)

=== PROCESS STATUS ===
$(ps aux | grep -E "(python|gunicorn|nginx)" | grep -v grep)

=== RECENT LOG ENTRIES ===
$(tail -20 "$LOG_FILE" 2>/dev/null || echo "No recent log entries")

=== BACKUP STATUS ===
$(ls -la /home/$(whoami)/backups/gurumisha/ 2>/dev/null | tail -5 || echo "No backups found")

=== DJANGO STATUS ===
$(cd "$PROJECT_DIR" && source venv/bin/activate && export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production" && python manage.py check --deploy 2>&1 || echo "Django check failed")

=== RECOMMENDATIONS ===
- Review log files for any errors or warnings
- Ensure regular backups are running
- Monitor disk space and clean up if necessary
- Keep dependencies updated
- Check SSL certificate expiration
EOF

    print_success "Maintenance report generated: $REPORT_FILE"
    log_message "Maintenance report generated"
}

# Function to display maintenance summary
show_summary() {
    print_success "Maintenance completed!"
    echo
    print_status "Maintenance Summary:"
    print_status "==================="
    print_status "Project: $PROJECT_NAME"
    print_status "Maintenance Date: $(date)"
    print_status "Log File: $LOG_FILE"
    echo
    print_status "Checks Performed:"
    print_status "- Disk space usage"
    print_status "- Memory usage"
    print_status "- Database health"
    print_status "- Application health"
    print_status "- SSL certificate status"
    print_status "- Dependency updates"
    echo
    print_status "Maintenance Tasks:"
    print_status "- Temporary files cleaned"
    print_status "- Database optimized"
    print_status "- Maintenance report generated"
    echo
    print_warning "Review the maintenance report and log files for any issues."
}

# Main maintenance process
main() {
    print_status "Starting $PROJECT_NAME maintenance..."
    log_message "Maintenance process started"
    
    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/logs"
    
    # Run maintenance tasks
    check_disk_space
    check_memory
    check_database
    check_application
    check_ssl
    clean_temp_files
    optimize_database
    update_dependencies
    generate_report
    show_summary
    
    log_message "Maintenance process completed"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
