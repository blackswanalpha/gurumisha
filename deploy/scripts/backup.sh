#!/bin/bash

# Gurumisha Motors - Backup Script
# Automated backup solution for database, media files, and configurations

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
BACKUP_DIR="/home/$(whoami)/backups/gurumisha"
LOG_FILE="$BACKUP_DIR/backup.log"
RETENTION_DAYS=30  # Keep backups for 30 days

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

# Function to create backup directory
setup_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        print_success "Backup directory created: $BACKUP_DIR"
    fi
    
    # Create subdirectories
    mkdir -p "$BACKUP_DIR/database"
    mkdir -p "$BACKUP_DIR/media"
    mkdir -p "$BACKUP_DIR/static"
    mkdir -p "$BACKUP_DIR/config"
    
    log_message "Backup directories setup"
}

# Function to backup database
backup_database() {
    print_status "Backing up database..."
    
    cd "$PROJECT_DIR"
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
    fi
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # Check if using PostgreSQL
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        # Extract database details
        DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
        DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
        DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
        
        # PostgreSQL backup
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sql"
        
        # Compress the backup
        gzip "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sql"
        
        print_success "PostgreSQL database backup created"
        
    elif [[ "$DATABASE_URL" == mysql* ]]; then
        # Extract MySQL database details
        DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
        DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
        DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
        
        # MySQL backup
        mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sql"
        
        # Compress the backup
        gzip "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sql"
        
        print_success "MySQL database backup created"
        
    else
        # SQLite backup
        if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
            cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sqlite3"
            gzip "$BACKUP_DIR/database/db_backup_$TIMESTAMP.sqlite3"
            print_success "SQLite database backup created"
        else
            print_warning "SQLite database file not found"
        fi
    fi
    
    log_message "Database backup completed: $TIMESTAMP"
}

# Function to backup media files
backup_media() {
    print_status "Backing up media files..."
    
    if [ -d "$PROJECT_DIR/media" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        
        # Create tar archive of media files
        tar -czf "$BACKUP_DIR/media/media_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" media/
        
        print_success "Media files backup created"
        log_message "Media backup completed: $TIMESTAMP"
    else
        print_warning "Media directory not found"
    fi
}

# Function to backup static files
backup_static() {
    print_status "Backing up static files..."
    
    if [ -d "$PROJECT_DIR/staticfiles" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        
        # Create tar archive of static files
        tar -czf "$BACKUP_DIR/static/static_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" staticfiles/
        
        print_success "Static files backup created"
        log_message "Static backup completed: $TIMESTAMP"
    else
        print_warning "Static files directory not found"
    fi
}

# Function to backup configuration files
backup_config() {
    print_status "Backing up configuration files..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CONFIG_BACKUP_DIR="$BACKUP_DIR/config/config_backup_$TIMESTAMP"
    
    mkdir -p "$CONFIG_BACKUP_DIR"
    
    # Backup important configuration files
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$CONFIG_BACKUP_DIR/"
    fi
    
    if [ -f "$PROJECT_DIR/.htaccess" ]; then
        cp "$PROJECT_DIR/.htaccess" "$CONFIG_BACKUP_DIR/"
    fi
    
    if [ -f "$PROJECT_DIR/wsgi.py" ]; then
        cp "$PROJECT_DIR/wsgi.py" "$CONFIG_BACKUP_DIR/"
    fi
    
    if [ -d "$PROJECT_DIR/gurumisha_project" ]; then
        cp -r "$PROJECT_DIR/gurumisha_project" "$CONFIG_BACKUP_DIR/"
    fi
    
    # Create tar archive
    tar -czf "$BACKUP_DIR/config/config_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR/config" "config_backup_$TIMESTAMP"
    
    # Remove temporary directory
    rm -rf "$CONFIG_BACKUP_DIR"
    
    print_success "Configuration files backup created"
    log_message "Configuration backup completed: $TIMESTAMP"
}

# Function to backup logs
backup_logs() {
    print_status "Backing up log files..."
    
    if [ -d "$PROJECT_DIR/logs" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        
        # Create tar archive of log files
        tar -czf "$BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" logs/
        
        print_success "Log files backup created"
        log_message "Logs backup completed: $TIMESTAMP"
    else
        print_warning "Logs directory not found"
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    print_status "Cleaning up old backups..."
    
    # Remove backups older than retention period
    find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sqlite3" -mtime +$RETENTION_DAYS -delete
    
    print_success "Old backups cleaned up (older than $RETENTION_DAYS days)"
    log_message "Cleanup completed"
}

# Function to create backup manifest
create_manifest() {
    print_status "Creating backup manifest..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    MANIFEST_FILE="$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
    
    cat > "$MANIFEST_FILE" << EOF
Gurumisha Motors - Backup Manifest
Generated: $(date)
Backup Directory: $BACKUP_DIR
Retention Period: $RETENTION_DAYS days

=== BACKUP CONTENTS ===

Database Backups:
$(ls -la "$BACKUP_DIR/database/" 2>/dev/null || echo "No database backups found")

Media Backups:
$(ls -la "$BACKUP_DIR/media/" 2>/dev/null || echo "No media backups found")

Static Files Backups:
$(ls -la "$BACKUP_DIR/static/" 2>/dev/null || echo "No static backups found")

Configuration Backups:
$(ls -la "$BACKUP_DIR/config/" 2>/dev/null || echo "No config backups found")

=== DISK USAGE ===
$(du -sh "$BACKUP_DIR"/* 2>/dev/null || echo "No backup data found")

=== SYSTEM INFO ===
Hostname: $(hostname)
User: $(whoami)
Disk Space: $(df -h "$BACKUP_DIR" | tail -1)
EOF

    print_success "Backup manifest created: $MANIFEST_FILE"
    log_message "Backup manifest created"
}

# Function to send backup notification (if email is configured)
send_notification() {
    print_status "Sending backup notification..."
    
    # Check if mail command is available
    if command -v mail >/dev/null 2>&1; then
        SUBJECT="Gurumisha Motors - Backup Completed $(date)"
        BODY="Backup completed successfully at $(date)\n\nBackup location: $BACKUP_DIR\n\nCheck the backup manifest for details."
        
        echo -e "$BODY" | mail -s "$SUBJECT" "admin@yourdomain.com" 2>/dev/null || print_warning "Failed to send email notification"
        
        print_success "Backup notification sent"
    else
        print_warning "Mail command not available, skipping notification"
    fi
    
    log_message "Notification process completed"
}

# Function to display backup summary
show_summary() {
    print_success "Backup completed successfully!"
    echo
    print_status "Backup Summary:"
    print_status "==============="
    print_status "Backup Directory: $BACKUP_DIR"
    print_status "Retention Period: $RETENTION_DAYS days"
    print_status "Total Backup Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo
    print_status "Backup Contents:"
    print_status "- Database: $(ls "$BACKUP_DIR/database/" 2>/dev/null | wc -l) files"
    print_status "- Media: $(ls "$BACKUP_DIR/media/" 2>/dev/null | wc -l) files"
    print_status "- Static: $(ls "$BACKUP_DIR/static/" 2>/dev/null | wc -l) files"
    print_status "- Config: $(ls "$BACKUP_DIR/config/" 2>/dev/null | wc -l) files"
    echo
    print_status "Log file: $LOG_FILE"
}

# Main backup process
main() {
    print_status "Starting $PROJECT_NAME backup process..."
    log_message "Backup process started"
    
    # Run backup steps
    setup_backup_dir
    backup_database
    backup_media
    backup_static
    backup_config
    backup_logs
    cleanup_old_backups
    create_manifest
    send_notification
    show_summary
    
    log_message "Backup process completed successfully"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
