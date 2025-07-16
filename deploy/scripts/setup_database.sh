#!/bin/bash

# Gurumisha Motors - Database Setup Script
# Configures PostgreSQL or MySQL database for production

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
LOG_FILE="$PROJECT_DIR/logs/database_setup.log"

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

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to setup PostgreSQL database
setup_postgresql() {
    print_status "Setting up PostgreSQL database..."
    
    # Check if PostgreSQL is available
    if ! command_exists psql; then
        print_error "PostgreSQL not found. Please install PostgreSQL or use cPanel database interface."
        return 1
    fi
    
    # Database configuration
    DB_NAME="gurumisha_db"
    DB_USER="gurumisha_user"
    DB_PASSWORD=$(generate_password)
    
    print_status "Creating PostgreSQL database and user..."
    
    # Create database and user (requires superuser privileges)
    sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE ${DB_NAME};

-- Create user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Additional privileges for Django
ALTER USER ${DB_USER} CREATEDB;

-- Exit
\q
EOF

    # Update .env file
    DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
    
    print_success "PostgreSQL database created successfully"
    print_status "Database URL: $DATABASE_URL"
    
    # Update .env file
    if [ -f "$PROJECT_DIR/.env" ]; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$PROJECT_DIR/.env"
        print_success ".env file updated with database URL"
    else
        print_warning ".env file not found. Please update DATABASE_URL manually."
    fi
    
    log_message "PostgreSQL database setup completed"
}

# Function to setup MySQL database
setup_mysql() {
    print_status "Setting up MySQL database..."
    
    # Check if MySQL is available
    if ! command_exists mysql; then
        print_error "MySQL not found. Please install MySQL or use cPanel database interface."
        return 1
    fi
    
    # Database configuration
    DB_NAME="gurumisha_db"
    DB_USER="gurumisha_user"
    DB_PASSWORD=$(generate_password)
    
    print_status "Creating MySQL database and user..."
    
    # Prompt for MySQL root password
    read -s -p "Enter MySQL root password: " MYSQL_ROOT_PASSWORD
    echo
    
    # Create database and user
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- Create database
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';

-- Grant privileges
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Exit
EXIT;
EOF

    # Update .env file
    DATABASE_URL="mysql://${DB_USER}:${DB_PASSWORD}@localhost:3306/${DB_NAME}"
    
    print_success "MySQL database created successfully"
    print_status "Database URL: $DATABASE_URL"
    
    # Update .env file
    if [ -f "$PROJECT_DIR/.env" ]; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$PROJECT_DIR/.env"
        print_success ".env file updated with database URL"
    else
        print_warning ".env file not found. Please update DATABASE_URL manually."
    fi
    
    log_message "MySQL database setup completed"
}

# Function to setup SQLite database (fallback)
setup_sqlite() {
    print_status "Setting up SQLite database..."
    
    DB_PATH="$PROJECT_DIR/db.sqlite3"
    DATABASE_URL="sqlite:///$DB_PATH"
    
    # Create database file if it doesn't exist
    if [ ! -f "$DB_PATH" ]; then
        touch "$DB_PATH"
        chmod 644 "$DB_PATH"
        print_success "SQLite database file created"
    else
        print_warning "SQLite database file already exists"
    fi
    
    # Update .env file
    if [ -f "$PROJECT_DIR/.env" ]; then
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" "$PROJECT_DIR/.env"
        print_success ".env file updated with database URL"
    else
        print_warning ".env file not found. Please update DATABASE_URL manually."
    fi
    
    print_success "SQLite database setup completed"
    log_message "SQLite database setup completed"
}

# Function to run Django migrations
run_migrations() {
    print_status "Running Django migrations..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Set Django settings
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Make migrations
    python manage.py makemigrations
    
    # Run migrations
    python manage.py migrate
    
    print_success "Django migrations completed"
    log_message "Django migrations completed"
}

# Function to create superuser
create_superuser() {
    print_status "Creating Django superuser..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set Django settings
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
        print_warning "Superuser already exists"
        return 0
    fi
    
    # Create superuser interactively
    print_status "Please provide superuser details:"
    python manage.py createsuperuser
    
    print_success "Superuser created successfully"
    log_message "Superuser created"
}

# Function to load initial data
load_initial_data() {
    print_status "Loading initial data..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set Django settings
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Load fixtures if they exist
    if [ -d "fixtures" ]; then
        for fixture in fixtures/*.json; do
            if [ -f "$fixture" ]; then
                python manage.py loaddata "$fixture"
                print_success "Loaded fixture: $fixture"
            fi
        done
    else
        print_warning "No fixtures directory found"
    fi
    
    log_message "Initial data loading completed"
}

# Function to optimize database
optimize_database() {
    print_status "Optimizing database..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set Django settings
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
    fi
    
    # Optimize based on database type
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        print_status "Running PostgreSQL optimization..."
        python manage.py dbshell --command="VACUUM ANALYZE;" || print_warning "VACUUM failed"
        
    elif [[ "$DATABASE_URL" == mysql* ]]; then
        print_status "Running MySQL optimization..."
        python manage.py dbshell --command="OPTIMIZE TABLE;" || print_warning "OPTIMIZE failed"
        
    else
        print_status "Running SQLite optimization..."
        if [ -f "db.sqlite3" ]; then
            sqlite3 "db.sqlite3" "VACUUM;" || print_warning "VACUUM failed"
        fi
    fi
    
    print_success "Database optimization completed"
    log_message "Database optimization completed"
}

# Function to setup database backup
setup_backup() {
    print_status "Setting up database backup..."
    
    # Create backup directory
    BACKUP_DIR="$PROJECT_DIR/backups/database"
    mkdir -p "$BACKUP_DIR"
    
    # Create backup script
    cat > "$PROJECT_DIR/backup_database.sh" << 'EOF'
#!/bin/bash
# Database backup script

cd "$(dirname "$0")"
source .env

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/database"

if [[ "$DATABASE_URL" == postgresql* ]]; then
    # PostgreSQL backup
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
    DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
    DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
    
    PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
elif [[ "$DATABASE_URL" == mysql* ]]; then
    # MySQL backup
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
    DB_USER=$(echo $DATABASE_URL | sed 's/.*:\/\/\([^:]*\):.*/\1/')
    DB_HOST=$(echo $DATABASE_URL | sed 's/.*@\([^:]*\):.*/\1/')
    DB_PORT=$(echo $DATABASE_URL | sed 's/.*:\([0-9]*\)\/.*/\1/')
    
    mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
else
    # SQLite backup
    if [ -f "db.sqlite3" ]; then
        cp "db.sqlite3" "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
        gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
    fi
fi

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Database backup completed: $TIMESTAMP"
EOF

    chmod +x "$PROJECT_DIR/backup_database.sh"
    
    print_success "Database backup script created"
    log_message "Database backup setup completed"
}

# Function to display database information
show_database_info() {
    print_success "Database setup completed!"
    echo
    print_status "Database Information:"
    print_status "===================="
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        print_status "Database URL: $DATABASE_URL"
    fi
    
    print_status "Backup script: $PROJECT_DIR/backup_database.sh"
    print_status "Log file: $LOG_FILE"
    echo
    print_status "Next Steps:"
    print_status "1. Test database connection"
    print_status "2. Run application health check"
    print_status "3. Setup automated backups"
    print_status "4. Configure monitoring"
}

# Main function
main() {
    print_status "Starting $PROJECT_NAME database setup..."
    log_message "Database setup started"
    
    # Create logs directory
    mkdir -p "$PROJECT_DIR/logs"
    
    # Prompt for database type
    echo
    print_status "Select database type:"
    print_status "1. PostgreSQL (recommended for production)"
    print_status "2. MySQL"
    print_status "3. SQLite (development/small sites)"
    echo
    read -p "Enter your choice (1-3): " DB_CHOICE
    
    case $DB_CHOICE in
        1)
            setup_postgresql
            ;;
        2)
            setup_mysql
            ;;
        3)
            setup_sqlite
            ;;
        *)
            print_error "Invalid choice. Defaulting to SQLite."
            setup_sqlite
            ;;
    esac
    
    # Run common setup tasks
    run_migrations
    create_superuser
    load_initial_data
    optimize_database
    setup_backup
    show_database_info
    
    log_message "Database setup completed successfully"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
