#!/bin/bash

# Gurumisha Motors - Production Build Script
# This script handles the complete build process for production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Gurumisha Motors"
PROJECT_DIR="/home/$(whoami)/public_html"  # Adjust for your cPanel setup
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups"
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

# Function to create backup
create_backup() {
    print_status "Creating backup..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
    fi
    
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    
    # Backup database
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/${BACKUP_NAME}_db.sqlite3"
        print_success "Database backup created"
    fi
    
    # Backup media files
    if [ -d "$PROJECT_DIR/media" ]; then
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz" -C "$PROJECT_DIR" media/
        print_success "Media files backup created"
    fi
    
    # Backup static files
    if [ -d "$PROJECT_DIR/staticfiles" ]; then
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_static.tar.gz" -C "$PROJECT_DIR" staticfiles/
        print_success "Static files backup created"
    fi
    
    log_message "Backup created: $BACKUP_NAME"
}

# Function to setup virtual environment
setup_virtualenv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "Pip upgraded"
    
    log_message "Virtual environment setup completed"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Ensure virtual environment is activated
    source "$VENV_DIR/bin/activate"
    
    # Install production requirements
    if [ -f "$PROJECT_DIR/deploy/config/requirements_production.txt" ]; then
        pip install -r "$PROJECT_DIR/deploy/config/requirements_production.txt"
        print_success "Production dependencies installed"
    else
        print_error "Production requirements file not found"
        exit 1
    fi
    
    # Freeze requirements for documentation
    pip freeze > "$PROJECT_DIR/requirements_frozen.txt"
    print_success "Requirements frozen"
    
    log_message "Python dependencies installed"
}

# Function to install Node.js dependencies
install_node_dependencies() {
    print_status "Installing Node.js dependencies..."
    
    if command_exists npm; then
        cd "$PROJECT_DIR"
        npm install
        print_success "Node.js dependencies installed"
    else
        print_warning "npm not found, skipping Node.js dependencies"
    fi
    
    log_message "Node.js dependencies processed"
}

# Function to build frontend assets
build_frontend() {
    print_status "Building frontend assets..."
    
    cd "$PROJECT_DIR"
    
    # Build Tailwind CSS
    if command_exists npm && [ -f "package.json" ]; then
        npm run build
        print_success "Tailwind CSS built"
    else
        print_warning "npm or package.json not found, skipping frontend build"
    fi
    
    log_message "Frontend assets built"
}

# Function to collect static files
collect_static() {
    print_status "Collecting static files..."
    
    # Ensure virtual environment is activated
    source "$VENV_DIR/bin/activate"
    
    cd "$PROJECT_DIR"
    
    # Set Django settings for production
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Create staticfiles directory
    mkdir -p staticfiles
    
    # Collect static files
    python manage.py collectstatic --noinput --clear
    print_success "Static files collected"
    
    log_message "Static files collection completed"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Ensure virtual environment is activated
    source "$VENV_DIR/bin/activate"
    
    cd "$PROJECT_DIR"
    
    # Set Django settings for production
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Check for pending migrations
    python manage.py showmigrations --plan
    
    # Run migrations
    python manage.py migrate --noinput
    print_success "Database migrations completed"
    
    log_message "Database migrations completed"
}

# Function to create superuser
create_superuser() {
    print_status "Creating superuser account..."
    
    # Ensure virtual environment is activated
    source "$VENV_DIR/bin/activate"
    
    cd "$PROJECT_DIR"
    
    # Set Django settings for production
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
        print_warning "Superuser already exists"
    else
        print_status "Please create a superuser account:"
        python manage.py createsuperuser
        print_success "Superuser created"
    fi
    
    log_message "Superuser setup completed"
}

# Function to set file permissions
set_permissions() {
    print_status "Setting file permissions..."
    
    # Set directory permissions
    find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find "$PROJECT_DIR" -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    chmod +x "$PROJECT_DIR/deploy/scripts/"*.sh
    
    # Set special permissions for media and logs
    chmod -R 755 "$PROJECT_DIR/media" 2>/dev/null || true
    chmod -R 755 "$PROJECT_DIR/logs" 2>/dev/null || true
    
    print_success "File permissions set"
    
    log_message "File permissions configured"
}

# Function to validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Ensure virtual environment is activated
    source "$VENV_DIR/bin/activate"
    
    cd "$PROJECT_DIR"
    
    # Set Django settings for production
    export DJANGO_SETTINGS_MODULE="gurumisha_project.settings_production"
    
    # Check Django configuration
    python manage.py check --deploy
    
    # Test database connection
    python manage.py dbshell --command="SELECT 1;" >/dev/null 2>&1 && print_success "Database connection OK" || print_error "Database connection failed"
    
    # Check static files
    if [ -d "$PROJECT_DIR/staticfiles" ] && [ "$(ls -A $PROJECT_DIR/staticfiles)" ]; then
        print_success "Static files OK"
    else
        print_error "Static files missing"
    fi
    
    log_message "Deployment validation completed"
}

# Main build process
main() {
    print_status "Starting $PROJECT_NAME build process..."
    log_message "Build process started"
    
    # Create necessary directories
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/media"
    mkdir -p "$PROJECT_DIR/staticfiles"
    
    # Run build steps
    create_backup
    setup_virtualenv
    install_dependencies
    install_node_dependencies
    build_frontend
    collect_static
    run_migrations
    create_superuser
    set_permissions
    validate_deployment
    
    print_success "$PROJECT_NAME build completed successfully!"
    print_status "Check the deployment guide for next steps."
    
    log_message "Build process completed successfully"
}

# Check if running as script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
