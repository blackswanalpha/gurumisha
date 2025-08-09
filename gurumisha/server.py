#!/usr/bin/env python3
"""
Gurumisha Django E-commerce Platform Server
Comprehensive deployment and management solution

This server provides:
- Complete dependency management and installation
- Django application deployment and hosting
- Production environment configuration
- Database setup and migration management
- Static file collection and optimization
- Admin user management
- Custom messaging capabilities
- Automatic 4-day shutdown mechanism (configurable)
- Comprehensive logging and error handling
- Backup and restore functionality
- Security hardening and monitoring
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
import json
import shutil
import secrets
import string
import ssl
import socket
import hashlib
import zipfile
import tempfile
import platform
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gurumisha_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Determine the correct project directory
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent

# Check if we're in the correct Django project directory
if (SCRIPT_DIR / 'manage.py').exists():
    # We're in the Django project root
    PROJECT_DIR = SCRIPT_DIR
elif (PARENT_DIR / 'manage.py').exists():
    # manage.py is in parent directory
    PROJECT_DIR = PARENT_DIR
else:
    # Search for manage.py in nearby directories
    for directory in [SCRIPT_DIR, PARENT_DIR]:
        manage_files = list(directory.rglob('manage.py'))
        if manage_files:
            PROJECT_DIR = manage_files[0].parent
            break
    else:
        # Default to script directory
        PROJECT_DIR = SCRIPT_DIR

# Add the project directory to Python path
sys.path.insert(0, str(PROJECT_DIR))

logger.info(f"Project directory: {PROJECT_DIR}")
logger.info(f"Script directory: {SCRIPT_DIR}")

# Define core dependencies that must be installed first
CORE_DEPENDENCIES = [
    'pip>=21.0.0',
    'setuptools>=65.0.0',
    'wheel>=0.37.0',
    'django>=4.2.0,<5.0',
]

# Define enhanced dependencies for full functionality
ENHANCED_DEPENDENCIES = [
    'psutil>=5.9.0',  # System monitoring
    'cryptography>=3.4.8',  # SSL/TLS support
    'schedule>=1.2.0',  # Task scheduling
    'gunicorn>=20.1.0',  # Production WSGI server
    'whitenoise>=6.4.0',  # Static file serving
    'python-decouple>=3.8',  # Environment variable management
    'django-environ>=0.10.0',  # Environment configuration
]

# Check for optional dependencies - graceful fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import pkg_resources
    PKG_RESOURCES_AVAILABLE = True
except ImportError:
    PKG_RESOURCES_AVAILABLE = False
    pkg_resources = None

# Add the project directory to Python path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

class DeploymentManager:
    """Handles comprehensive deployment operations"""

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.venv_dir = self.project_dir / 'venv'
        self.requirements_file = self.project_dir / 'requirements.txt'
        self.django_initialized = False

    def ensure_python_environment(self):
        """Ensure Python environment is properly set up"""
        try:
            logger.info("Checking Python environment...")

            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 8):
                logger.error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
                return False

            logger.info(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

            # Check if we're in a virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

            if not in_venv and self.venv_dir.exists():
                logger.warning("Virtual environment exists but not activated")
                logger.info("Attempting to use virtual environment...")
                return self._activate_virtual_environment()
            elif not in_venv:
                logger.info("Creating new virtual environment...")
                return self._create_and_activate_venv()
            else:
                logger.info("Virtual environment is active")
                return True

        except Exception as e:
            logger.error(f"Failed to setup Python environment: {e}")
            return False

    def _create_and_activate_venv(self):
        """Create and activate virtual environment"""
        try:
            # Create virtual environment
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)], check=True)
            logger.info("Virtual environment created")

            # Update pip in the new environment
            pip_executable = self._get_pip_executable()
            subprocess.run([str(pip_executable), 'install', '--upgrade', 'pip'], check=True)
            logger.info("Pip upgraded in virtual environment")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False

    def _activate_virtual_environment(self):
        """Activate existing virtual environment"""
        try:
            # Check if virtual environment is valid
            pip_executable = self._get_pip_executable()
            if not pip_executable.exists():
                logger.error("Virtual environment appears corrupted")
                return False

            logger.info("Virtual environment validated")
            return True

        except Exception as e:
            logger.error(f"Failed to activate virtual environment: {e}")
            return False

    def _get_pip_executable(self):
        """Get pip executable path"""
        if platform.system() == 'Windows':
            return self.venv_dir / 'Scripts' / 'pip.exe'
        else:
            return self.venv_dir / 'bin' / 'pip'

    def install_core_dependencies(self):
        """Install core dependencies required for Django"""
        try:
            logger.info("Installing core dependencies...")

            pip_executable = self._get_pip_executable()
            if not pip_executable.exists():
                # Use system pip if venv pip not available
                pip_executable = 'pip3' if shutil.which('pip3') else 'pip'

            # Install core dependencies one by one
            for dep in CORE_DEPENDENCIES:
                logger.info(f"Installing {dep}...")
                result = subprocess.run([
                    str(pip_executable), 'install', '--upgrade', dep
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"Failed to install {dep}: {result.stderr}")
                    return False
                else:
                    logger.info(f"Successfully installed {dep}")

            logger.info("Core dependencies installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install core dependencies: {e}")
            return False

    def install_project_dependencies(self):
        """Install project dependencies from requirements.txt"""
        try:
            if not self.requirements_file.exists():
                logger.warning("requirements.txt not found, skipping project dependencies")
                return True

            logger.info("Installing project dependencies from requirements.txt...")

            pip_executable = self._get_pip_executable()
            if not pip_executable.exists():
                pip_executable = 'pip3' if shutil.which('pip3') else 'pip'

            # Install all requirements
            result = subprocess.run([
                str(pip_executable), 'install', '-r', str(self.requirements_file)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Project dependencies installed successfully")
                return True
            else:
                logger.error(f"Failed to install project dependencies: {result.stderr}")
                # Try installing without version constraints as fallback
                logger.info("Attempting fallback installation...")
                return self._install_dependencies_fallback()

        except Exception as e:
            logger.error(f"Error installing project dependencies: {e}")
            return False

    def _install_dependencies_fallback(self):
        """Fallback dependency installation without strict version constraints"""
        try:
            logger.info("Attempting fallback dependency installation...")

            # Read requirements and extract package names only
            with open(self.requirements_file, 'r') as f:
                requirements = f.read().splitlines()

            pip_executable = self._get_pip_executable()
            if not pip_executable.exists():
                pip_executable = 'pip3' if shutil.which('pip3') else 'pip'

            # Install packages without version constraints
            for requirement in requirements:
                if requirement.strip() and not requirement.startswith('#'):
                    # Extract package name (remove version constraints)
                    package_name = re.split(r'[>=<!=]', requirement)[0].strip()

                    logger.info(f"Installing {package_name} (fallback)...")
                    result = subprocess.run([
                        str(pip_executable), 'install', package_name
                    ], capture_output=True, text=True)

                    if result.returncode == 0:
                        logger.info(f"Successfully installed {package_name}")
                    else:
                        logger.warning(f"Failed to install {package_name}: {result.stderr}")

            return True

        except Exception as e:
            logger.error(f"Fallback installation failed: {e}")
            return False

    def install_enhanced_dependencies(self):
        """Install enhanced dependencies for full functionality"""
        try:
            logger.info("Installing enhanced dependencies...")

            pip_executable = self._get_pip_executable()
            if not pip_executable.exists():
                pip_executable = 'pip3' if shutil.which('pip3') else 'pip'

            for dep in ENHANCED_DEPENDENCIES:
                logger.info(f"Installing {dep}...")
                result = subprocess.run([
                    str(pip_executable), 'install', dep
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"Successfully installed {dep}")
                else:
                    logger.warning(f"Failed to install {dep}: {result.stderr}")

            logger.info("Enhanced dependencies installation completed")
            return True

        except Exception as e:
            logger.error(f"Error installing enhanced dependencies: {e}")
            return False

    def initialize_django(self):
        """Initialize Django after dependencies are installed"""
        try:
            if self.django_initialized:
                return True

            logger.info("Initializing Django...")

            # Set Django settings module
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')

            # Initialize Django
            import django
            django.setup()

            # Import Django modules after initialization
            from django.core.management import execute_from_command_line
            from django.contrib.auth import get_user_model
            from django.core.wsgi import get_wsgi_application
            from django.conf import settings

            # Store important modules for later use
            self.django_modules = {
                'execute_from_command_line': execute_from_command_line,
                'get_user_model': get_user_model,
                'get_wsgi_application': get_wsgi_application,
                'settings': settings,
            }

            # Import core models
            try:
                from core.models import Message, Notification, User
                from core.notification_manager import NotificationManager

                self.django_modules.update({
                    'Message': Message,
                    'Notification': Notification,
                    'User': User,
                    'NotificationManager': NotificationManager,
                })
            except ImportError as e:
                logger.warning(f"Some core models could not be imported: {e}")

            self.django_initialized = True
            logger.info("Django initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Django: {e}")
            return False

    def apply_migrations(self):
        """Apply database migrations"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            logger.info("Applying database migrations...")

            # Check for pending migrations
            result = subprocess.run([
                sys.executable, 'manage.py', 'showmigrations', '--plan'
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode != 0:
                logger.error(f"Failed to check migrations: {result.stderr}")
                return False

            # Check if there are unapplied migrations
            if '[ ]' in result.stdout:
                logger.info("Applying pending migrations...")
                migrate_result = subprocess.run([
                    sys.executable, 'manage.py', 'migrate'
                ], capture_output=True, text=True, cwd=self.project_dir)

                if migrate_result.returncode == 0:
                    logger.info("Migrations applied successfully")
                else:
                    logger.error(f"Failed to apply migrations: {migrate_result.stderr}")
                    return False
            else:
                logger.info("No pending migrations")

            return True

        except Exception as e:
            logger.error(f"Error applying migrations: {e}")
            return False

    def populate_car_models(self):
        """Populate comprehensive car models using management command"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            logger.info("Populating comprehensive car models...")

            # Run the populate_car_models management command
            result = subprocess.run([
                sys.executable, 'manage.py', 'populate_car_models', '--verbosity=1'
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                logger.info("Car models populated successfully")
                # Log the output to show what was created
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            logger.info(f"Models: {line.strip()}")
                return True
            else:
                logger.error(f"Failed to populate car models: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error populating car models: {e}")
            return False

    def collect_static_files(self):
        """Collect and optimize static files"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            logger.info("Collecting static files...")

            result = subprocess.run([
                sys.executable, 'manage.py', 'collectstatic', '--noinput'
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                logger.info("Static files collected successfully")
                return True
            else:
                logger.error(f"Failed to collect static files: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error collecting static files: {e}")
            return False

    def create_superuser(self, username, email, password):
        """Create Django superuser"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            logger.info(f"Creating superuser: {username}")

            # Use Django's management command to create superuser
            from io import StringIO
            from django.core.management import call_command

            # Check if user already exists
            User = self.django_modules['get_user_model']()
            if User.objects.filter(username=username).exists():
                logger.warning(f"User '{username}' already exists")
                return True

            # Create superuser
            out = StringIO()
            call_command(
                'createsuperuser',
                interactive=False,
                username=username,
                email=email,
                stdout=out
            )

            # Set password and email verification (createsuperuser doesn't set password non-interactively)
            user = User.objects.get(username=username)
            user.set_password(password)

            # Set email verification status if the field exists
            if hasattr(user, 'is_email_verified'):
                user.is_email_verified = True
                logger.info(f"Email verification set for superuser: {username}")

            # Set additional admin-specific fields if they exist
            if hasattr(user, 'role'):
                user.role = 'admin'

            user.save()

            logger.info(f"Superuser '{username}' created successfully with verified email")
            return True

        except Exception as e:
            logger.error(f"Failed to create superuser: {e}")
            return False

    def setup_production_environment(self, domain_name, debug=False, db_type='sqlite'):
        """Configure production environment settings"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            logger.info("Setting up production environment...")

            # Generate secure secret key
            secret_key = ''.join(secrets.choice(
                'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)'
            ) for i in range(50))

            # Configure database URL based on type
            if db_type == 'sqlite':
                db_url = 'sqlite:///db.sqlite3'
            elif db_type == 'postgres':
                db_url = 'postgres://postgres:password@localhost:5432/gurumisha_db'
            else:
                db_url = 'sqlite:///db.sqlite3'  # Default fallback

            # Create or update .env file
            env_file = self.project_dir / '.env'
            env_content = f"""DEBUG={str(debug).lower()}
SECRET_KEY={secret_key}
ALLOWED_HOSTS={domain_name},www.{domain_name},localhost,127.0.0.1
DATABASE_URL={db_url}
STATIC_ROOT={self.project_dir / 'static_collected'}
MEDIA_ROOT={self.project_dir / 'media'}
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
"""

            with open(env_file, 'w') as f:
                f.write(env_content)

            # Create directories if they don't exist
            static_dir = self.project_dir / 'static_collected'
            media_dir = self.project_dir / 'media'

            static_dir.mkdir(exist_ok=True)
            media_dir.mkdir(exist_ok=True)

            logger.info(f"Production environment configured for {domain_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup production environment: {e}")
            return False

    def backup_database(self, backup_dir=None):
        """Create database backup"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            # Create backup directory if not specified
            if backup_dir is None:
                backup_dir = self.project_dir / 'backups'
            else:
                backup_dir = Path(backup_dir)

            backup_dir.mkdir(exist_ok=True)

            # Generate timestamp for backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'db_backup_{timestamp}.json'

            logger.info(f"Creating database backup: {backup_file}")

            # Use Django's dumpdata command
            result = subprocess.run([
                sys.executable, 'manage.py', 'dumpdata',
                '--exclude', 'contenttypes',
                '--exclude', 'auth.permission',
                '--natural-foreign',
                '--natural-primary',
                '--indent', '2',
                '-o', str(backup_file)
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {backup_file}")
                return str(backup_file)
            else:
                logger.error(f"Failed to create database backup: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return None

    def restore_database(self, backup_file):
        """Restore database from backup"""
        try:
            if not self.django_initialized:
                if not self.initialize_django():
                    return False

            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False

            logger.info(f"Restoring database from backup: {backup_file}")

            # Use Django's loaddata command
            result = subprocess.run([
                sys.executable, 'manage.py', 'loaddata',
                str(backup_path)
            ], capture_output=True, text=True, cwd=self.project_dir)

            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Failed to restore database: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False

    def setup_ssl_certificate(self, domain, email, use_staging=True):
        """Setup SSL certificate using certbot (Let's Encrypt)"""
        try:
            logger.info(f"Setting up SSL certificate for {domain}...")

            # Check if certbot is installed
            certbot_path = shutil.which('certbot')
            if not certbot_path:
                logger.error("Certbot not found. Please install certbot first.")
                return False

            # Build certbot command
            cmd = [
                certbot_path, 'certonly',
                '--standalone',
                '-d', domain,
                '-d', f'www.{domain}',
                '--agree-tos',
                '--email', email,
                '--non-interactive'
            ]

            if use_staging:
                cmd.append('--staging')

            # Run certbot
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("SSL certificate obtained successfully")

                # Return certificate paths
                cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"

                logger.info(f"Certificate path: {cert_path}")
                logger.info(f"Key path: {key_path}")

                return {
                    'cert_path': cert_path,
                    'key_path': key_path
                }
            else:
                logger.error(f"Failed to obtain SSL certificate: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error setting up SSL certificate: {e}")
            return False

    def generate_nginx_config(self, domain, port=8000, ssl_config=None):
        """Generate Nginx configuration for the Django application"""
        try:
            logger.info(f"Generating Nginx configuration for {domain}...")

            # Determine if SSL is enabled
            ssl_enabled = ssl_config is not None

            # Create config directory
            config_dir = self.project_dir / 'deployment'
            config_dir.mkdir(exist_ok=True)

            # Generate config file path
            config_file = config_dir / f"{domain}.conf"

            # Generate Nginx configuration
            if ssl_enabled:
                config = f"""server {{
    listen 80;
    server_name {domain} www.{domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {domain} www.{domain};

    ssl_certificate {ssl_config['cert_path']};
    ssl_certificate_key {ssl_config['key_path']};

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

    location /static/ {{
        alias {self.project_dir / 'static_collected'}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }}

    location /media/ {{
        alias {self.project_dir / 'media'}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }}

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
            else:
                config = f"""server {{
    listen 80;
    server_name {domain} www.{domain};

    location /static/ {{
        alias {self.project_dir / 'static_collected'}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }}

    location /media/ {{
        alias {self.project_dir / 'media'}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }}

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""

            # Write configuration to file
            with open(config_file, 'w') as f:
                f.write(config)

            logger.info(f"Nginx configuration generated: {config_file}")
            return str(config_file)

        except Exception as e:
            logger.error(f"Error generating Nginx configuration: {e}")
            return None


class DependencyManager:
    """Manages Python dependencies and virtual environment"""

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.venv_dir = self.project_dir / 'venv'
        self.requirements_file = self.project_dir / 'requirements.txt'

    def check_virtual_environment(self):
        """Check if virtual environment exists and is activated"""
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("Virtual environment is active")
            return True

        if self.venv_dir.exists():
            logger.info("Virtual environment exists but not activated")
            return False

        logger.info("No virtual environment found")
        return False

    def create_virtual_environment(self):
        """Create virtual environment if it doesn't exist"""
        try:
            if not self.venv_dir.exists():
                logger.info("Creating virtual environment...")
                subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)], check=True)
                logger.info("Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False

    def get_pip_executable(self):
        """Get pip executable path for the virtual environment"""
        if os.name == 'nt':  # Windows
            return self.venv_dir / 'Scripts' / 'pip.exe'
        else:  # Unix/Linux/macOS
            return self.venv_dir / 'bin' / 'pip'

    def install_dependencies(self, upgrade=False):
        """Install dependencies from requirements.txt"""
        try:
            if not self.requirements_file.exists():
                logger.warning("requirements.txt not found, skipping dependency installation")
                return True

            pip_executable = self.get_pip_executable()
            if not pip_executable.exists():
                logger.error("Pip executable not found in virtual environment")
                return False

            cmd = [str(pip_executable), 'install', '-r', str(self.requirements_file)]
            if upgrade:
                cmd.append('--upgrade')

            logger.info("Installing dependencies...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Dependencies installed successfully")
                return True
            else:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False

    def verify_dependencies(self):
        """Verify all required dependencies are installed"""
        try:
            if not self.requirements_file.exists():
                return True

            with open(self.requirements_file, 'r') as f:
                requirements = f.read().splitlines()

            # If pkg_resources is available, use it for accurate verification
            if PKG_RESOURCES_AVAILABLE:
                missing_packages = []
                for requirement in requirements:
                    if requirement.strip() and not requirement.startswith('#'):
                        package_name = requirement.split('>=')[0].split('==')[0].split('<')[0].strip()
                        try:
                            pkg_resources.get_distribution(package_name)
                        except pkg_resources.DistributionNotFound:
                            missing_packages.append(package_name)

                if missing_packages:
                    logger.warning(f"Missing packages: {missing_packages}")
                    return False

                logger.info("All dependencies verified")
                return True
            else:
                # Fallback to basic verification using importlib
                import importlib

                # Check only core dependencies that are critical
                core_packages = ['django', 'requests']
                missing_core = []

                for package in core_packages:
                    try:
                        importlib.import_module(package)
                    except ImportError:
                        missing_core.append(package)

                if missing_core:
                    logger.warning(f"Missing core packages: {missing_core}")
                    return False

                logger.info("Core dependencies verified (pkg_resources not available for full verification)")
                return True

        except Exception as e:
            logger.error(f"Error verifying dependencies: {e}")
            return False

    def upgrade_packages(self):
        """Upgrade outdated packages"""
        try:
            pip_executable = self.get_pip_executable()
            if not pip_executable.exists():
                return False

            # Get list of outdated packages
            result = subprocess.run([str(pip_executable), 'list', '--outdated', '--format=json'],
                                  capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                outdated_packages = json.loads(result.stdout)
                if outdated_packages:
                    logger.info(f"Found {len(outdated_packages)} outdated packages")
                    for package in outdated_packages:
                        logger.info(f"Upgrading {package['name']} from {package['version']} to {package['latest_version']}")

                    # Upgrade packages
                    package_names = [pkg['name'] for pkg in outdated_packages]
                    cmd = [str(pip_executable), 'install', '--upgrade'] + package_names
                    upgrade_result = subprocess.run(cmd, capture_output=True, text=True)

                    if upgrade_result.returncode == 0:
                        logger.info("Packages upgraded successfully")
                        return True
                    else:
                        logger.error(f"Failed to upgrade packages: {upgrade_result.stderr}")
                        return False
                else:
                    logger.info("All packages are up to date")
                    return True

            return True

        except Exception as e:
            logger.error(f"Error upgrading packages: {e}")
            return False

    def install_enhanced_dependencies(self):
        """Install enhanced server dependencies"""
        try:
            enhanced_deps = [
                'psutil>=5.9.0',
                'cryptography>=3.4.8',
                'schedule>=1.2.0',
                'setuptools>=65.0.0'
            ]

            pip_executable = self.get_pip_executable()
            if not pip_executable.exists():
                logger.error("Pip executable not found")
                return False

            logger.info("Installing enhanced server dependencies...")
            for dep in enhanced_deps:
                cmd = [str(pip_executable), 'install', dep]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"Installed: {dep}")
                else:
                    logger.warning(f"Failed to install {dep}: {result.stderr}")

            logger.info("Enhanced dependencies installation completed")
            return True

        except Exception as e:
            logger.error(f"Error installing enhanced dependencies: {e}")
            return False


class WorkerProcess:
    """Base class for background worker processes"""

    def __init__(self, name, target_function, *args, **kwargs):
        self.name = name
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self.process = None
        self.is_running = False
        self.last_health_check = None
        self.restart_count = 0
        self.max_restarts = 5

    def start(self):
        """Start the worker process"""
        try:
            self.process = threading.Thread(
                target=self._run_with_monitoring,
                name=f"Worker-{self.name}",
                daemon=True
            )
            self.process.start()
            self.is_running = True
            logger.info(f"Worker process '{self.name}' started")
            return True
        except Exception as e:
            logger.error(f"Failed to start worker process '{self.name}': {e}")
            return False

    def _run_with_monitoring(self):
        """Run the target function with monitoring"""
        try:
            while self.is_running:
                self.last_health_check = datetime.now()
                self.target_function(*self.args, **self.kwargs)
                time.sleep(1)  # Prevent tight loops
        except Exception as e:
            logger.error(f"Worker process '{self.name}' crashed: {e}")
            self._handle_crash()

    def _handle_crash(self):
        """Handle worker process crash and restart if needed"""
        if self.restart_count < self.max_restarts:
            self.restart_count += 1
            logger.info(f"Restarting worker process '{self.name}' (attempt {self.restart_count})")
            time.sleep(5)  # Wait before restart
            self.start()
        else:
            logger.error(f"Worker process '{self.name}' exceeded max restart attempts")
            self.is_running = False

    def stop(self):
        """Stop the worker process"""
        self.is_running = False
        if self.process and self.process.is_alive():
            self.process.join(timeout=10)
        logger.info(f"Worker process '{self.name}' stopped")

    def health_check(self):
        """Check if worker process is healthy"""
        if not self.is_running:
            return False

        if self.last_health_check:
            time_since_check = datetime.now() - self.last_health_check
            if time_since_check.total_seconds() > 300:  # 5 minutes
                logger.warning(f"Worker process '{self.name}' hasn't checked in for {time_since_check}")
                return False

        return True


class GurumishaServer:
    """Main server class for Gurumisha Django application"""
    
    def __init__(self, host='127.0.0.1', port=8000, kill_switch_days=4, auto_init=True):
        self.host = host
        self.port = port
        self.kill_switch_days = kill_switch_days
        self.start_time = datetime.now()
        self.shutdown_time = self.start_time + timedelta(days=kill_switch_days)
        self.server_process = None
        self.kill_switch_thread = None
        self.running = False
        self.auto_init = auto_init

        # Initialize managers
        self.deployment_manager = DeploymentManager(PROJECT_DIR)
        self.dependency_manager = DependencyManager(PROJECT_DIR)
        self.worker_processes = []
        self.worker_executor = ThreadPoolExecutor(max_workers=10)
        self.backup_retention_days = 7

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Gurumisha Server initialized")
        logger.info(f"Server will automatically shutdown on: {self.shutdown_time}")

        # Log enhanced features availability
        if not PSUTIL_AVAILABLE:
            logger.info("Enhanced monitoring disabled - install psutil for full features")
        if not PKG_RESOURCES_AVAILABLE:
            logger.info("Enhanced dependency management disabled - install setuptools for full features")

        if PSUTIL_AVAILABLE and PKG_RESOURCES_AVAILABLE:
            logger.info("All enhanced features available")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def create_admin_user(self, username, email, password, force=False):
        """Create or update admin user"""
        try:
            # Ensure Django is initialized
            if not self.deployment_manager.initialize_django():
                logger.error("Django initialization failed")
                return False

            from django.contrib.auth import get_user_model
            User = get_user_model()

            if User.objects.filter(username=username).exists():
                if not force:
                    logger.warning(f"Admin user '{username}' already exists")
                    return False

                user = User.objects.get(username=username)
                user.set_password(password)
                user.email = email
                user.role = 'admin'
                user.is_staff = True
                user.is_superuser = True
                user.is_email_verified = True
                user.save()
                logger.info(f"Admin user '{username}' updated successfully")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role='admin',
                    is_staff=True,
                    is_superuser=True,
                    is_email_verified=True
                )
                logger.info(f"Admin user '{username}' created successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            return False
    
    def send_system_message(self, title, content, target_audience='all',
                           message_type='announcement', priority=2):
        """Send system-wide message using existing Message model"""
        try:
            # Ensure Django is initialized
            if not self.deployment_manager.initialize_django():
                logger.error("Django initialization failed")
                return None

            from core.models import Message

            message = Message.objects.create(
                title=title,
                content=content,
                target_audience=target_audience,
                message_type=message_type,
                priority=priority,
                status='active',
                publication_date=datetime.now(),
                created_by_id=1  # Assume first admin user
            )

            logger.info(f"System message created: '{title}' for {target_audience}")
            return message

        except Exception as e:
            logger.error(f"Failed to send system message: {e}")
            return None
    
    def send_notification_to_users(self, title, message, user_roles=None, channels=None):
        """Send notifications to specific user roles"""
        try:
            # Ensure Django is initialized
            if not self.deployment_manager.initialize_django():
                logger.error("Django initialization failed")
                return False

            from django.contrib.auth import get_user_model
            from core.notification_manager import NotificationManager

            User = get_user_model()

            if user_roles is None:
                user_roles = ['customer', 'vendor', 'admin']

            if channels is None:
                channels = ['in_app', 'email']

            users = User.objects.filter(role__in=user_roles, is_active=True)

            for user in users:
                NotificationManager.send_notification(
                    recipient=user,
                    title=title,
                    message=message,
                    channels=channels,
                    priority=2
                )

            logger.info(f"Notifications sent to {users.count()} users with roles: {user_roles}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
            return False

    def setup_dependencies(self):
        """Setup and verify dependencies"""
        try:
            logger.info("Setting up dependencies...")

            # Check virtual environment
            if not self.dependency_manager.check_virtual_environment():
                if self.auto_init:
                    if not self.dependency_manager.create_virtual_environment():
                        return False
                else:
                    logger.warning("Virtual environment not active. Consider using --auto-init")

            # Verify dependencies
            if not self.dependency_manager.verify_dependencies():
                if self.auto_init:
                    if not self.dependency_manager.install_dependencies():
                        return False
                else:
                    logger.warning("Dependencies missing. Use --install-deps to install")
                    return False

            logger.info("Dependencies setup complete")
            return True

        except Exception as e:
            logger.error(f"Failed to setup dependencies: {e}")
            return False

    def apply_migrations(self):
        """Check and apply pending database migrations"""
        try:
            logger.info("Checking database migrations...")

            # Check for pending migrations
            result = subprocess.run([
                sys.executable, 'manage.py', 'showmigrations', '--plan'
            ], capture_output=True, text=True, cwd=PROJECT_DIR)

            if result.returncode != 0:
                logger.error(f"Failed to check migrations: {result.stderr}")
                return False

            # Check if there are unapplied migrations
            if '[ ]' in result.stdout:
                logger.info("Applying pending migrations...")
                migrate_result = subprocess.run([
                    sys.executable, 'manage.py', 'migrate'
                ], capture_output=True, text=True, cwd=PROJECT_DIR)

                if migrate_result.returncode == 0:
                    logger.info("Migrations applied successfully")
                else:
                    logger.error(f"Failed to apply migrations: {migrate_result.stderr}")
                    return False
            else:
                logger.info("No pending migrations")

            return True

        except Exception as e:
            logger.error(f"Error applying migrations: {e}")
            return False

    def collect_static_files(self):
        """Collect and optimize static files"""
        try:
            logger.info("Collecting static files...")

            result = subprocess.run([
                sys.executable, 'manage.py', 'collectstatic', '--noinput'
            ], capture_output=True, text=True, cwd=PROJECT_DIR)

            if result.returncode == 0:
                logger.info("Static files collected successfully")
                return True
            else:
                logger.error(f"Failed to collect static files: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error collecting static files: {e}")
            return False

    def generate_secure_password(self, length=16):
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    def validate_environment(self):
        """Validate environment configuration"""
        try:
            logger.info("Validating environment configuration...")

            # Ensure Django is initialized
            if not self.deployment_manager.initialize_django():
                logger.error("Django initialization failed")
                return False

            # Import Django settings
            from django.conf import settings

            # Check required environment variables
            required_vars = ['DJANGO_SETTINGS_MODULE']
            missing_vars = []

            for var in required_vars:
                if not os.environ.get(var):
                    missing_vars.append(var)

            if missing_vars:
                logger.warning(f"Missing environment variables: {missing_vars}")

            # Check database connectivity
            from django.db import connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                logger.info("Database connection validated")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                return False

            # Check static files directory
            static_root = getattr(settings, 'STATIC_ROOT', None)
            if static_root and not Path(static_root).exists():
                logger.warning(f"Static root directory does not exist: {static_root}")

            # Check media files directory
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if media_root:
                Path(media_root).mkdir(parents=True, exist_ok=True)
                logger.info("Media directory validated")

            logger.info("Environment validation complete")
            return True

        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False

    def setup_ssl_certificate(self, cert_path=None, key_path=None):
        """Setup SSL certificate for production deployment"""
        try:
            if not cert_path or not key_path:
                logger.info("No SSL certificate paths provided, skipping SSL setup")
                return True

            cert_file = Path(cert_path)
            key_file = Path(key_path)

            if not cert_file.exists():
                logger.error(f"SSL certificate file not found: {cert_path}")
                return False

            if not key_file.exists():
                logger.error(f"SSL key file not found: {key_path}")
                return False

            # Validate certificate
            try:
                with open(cert_file, 'r') as f:
                    cert_data = f.read()
                ssl.PEM_cert_to_DER_cert(cert_data)
                logger.info("SSL certificate validated")
                return True
            except Exception as e:
                logger.error(f"Invalid SSL certificate: {e}")
                return False

        except Exception as e:
            logger.error(f"SSL setup failed: {e}")
            return False

    def setup_worker_processes(self):
        """Setup and start background worker processes"""
        try:
            logger.info("Setting up worker processes...")

            # Email notification worker
            email_worker = WorkerProcess(
                "EmailNotificationWorker",
                self._email_notification_worker
            )
            self.worker_processes.append(email_worker)

            # Database maintenance worker
            db_worker = WorkerProcess(
                "DatabaseMaintenanceWorker",
                self._database_maintenance_worker
            )
            self.worker_processes.append(db_worker)

            # Import/Export processing worker
            import_worker = WorkerProcess(
                "ImportExportWorker",
                self._import_export_worker
            )
            self.worker_processes.append(import_worker)

            # Scheduled tasks worker
            scheduler_worker = WorkerProcess(
                "ScheduledTasksWorker",
                self._scheduled_tasks_worker
            )
            self.worker_processes.append(scheduler_worker)

            # Performance monitoring worker (only if psutil is available)
            if PSUTIL_AVAILABLE:
                monitor_worker = WorkerProcess(
                    "PerformanceMonitorWorker",
                    self._performance_monitor_worker
                )
                self.worker_processes.append(monitor_worker)
            else:
                logger.info("Performance monitoring worker disabled - psutil not available")

            # Start all workers
            for worker in self.worker_processes:
                worker.start()

            logger.info(f"Started {len(self.worker_processes)} worker processes")
            return True

        except Exception as e:
            logger.error(f"Failed to setup worker processes: {e}")
            return False

    def _email_notification_worker(self):
        """Worker process for handling email notifications"""
        try:
            from core.models import NotificationQueue

            # Process pending email notifications
            pending_notifications = NotificationQueue.objects.filter(
                status='pending',
                channel='email'
            ).order_by('priority', 'created_at')[:10]

            for notification in pending_notifications:
                try:
                    # Update status to processing
                    notification.status = 'processing'
                    notification.save()

                    # Send email using Django's email system
                    from django.core.mail import send_mail

                    send_mail(
                        subject=notification.subject,
                        message=notification.message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[notification.recipient.email],
                        fail_silently=False
                    )

                    # Update status to sent
                    notification.status = 'sent'
                    notification.sent_at = datetime.now()
                    notification.save()

                    logger.debug(f"Email sent to {notification.recipient.email}")

                except Exception as e:
                    notification.status = 'failed'
                    notification.save()
                    logger.error(f"Failed to send email to {notification.recipient.email}: {e}")

            time.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Email notification worker error: {e}")
            time.sleep(60)  # Wait longer on error

    def _database_maintenance_worker(self):
        """Worker process for database maintenance tasks"""
        try:
            from django.db import connection

            # Run database optimization every hour
            current_time = datetime.now()
            if current_time.minute == 0:  # Top of the hour
                logger.info("Running database maintenance...")

                # Vacuum SQLite database (if using SQLite)
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    with connection.cursor() as cursor:
                        cursor.execute("VACUUM;")
                    logger.info("Database vacuum completed")

                # Clean up old log entries
                self._cleanup_old_logs()

                # Clean up old backups
                self._cleanup_old_backups()

            time.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Database maintenance worker error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

    def _import_export_worker(self):
        """Worker process for import/export order processing"""
        try:
            from core.models import ImportOrder, ImportRequest

            # Process import orders that need status updates
            active_orders = ImportOrder.objects.filter(
                status__in=['confirmed', 'auction_won', 'shipped', 'in_transit', 'arrived_docked']
            )

            for order in active_orders:
                # Simulate status progression (in real implementation, this would check external APIs)
                if order.status == 'confirmed' and self._should_update_status(order):
                    order.status = 'auction_won'
                    order.save()

                    # Send notification
                    self.send_notification_to_users(
                        title=f"Import Order Update - {order.order_number}",
                        message=f"Your import order has won the auction!",
                        user_roles=['customer'],
                        channels=['email', 'in_app']
                    )

            time.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"Import/Export worker error: {e}")
            time.sleep(600)  # Wait 10 minutes on error

    def _scheduled_tasks_worker(self):
        """Worker process for scheduled tasks"""
        try:
            current_time = datetime.now()

            # Daily reports at midnight
            if current_time.hour == 0 and current_time.minute == 0:
                self._generate_daily_reports()

            # Weekly analytics on Mondays at 1 AM
            if current_time.weekday() == 0 and current_time.hour == 1 and current_time.minute == 0:
                self._generate_weekly_analytics()

            # Backup database every 6 hours
            if current_time.hour % 6 == 0 and current_time.minute == 0:
                ServerManager.backup_database()

            time.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Scheduled tasks worker error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

    def _performance_monitor_worker(self):
        """Worker process for performance monitoring"""
        try:
            # Monitor system resources if psutil is available
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                # Log performance metrics
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage: {cpu_percent}%")

                if memory.percent > 80:
                    logger.warning(f"High memory usage: {memory.percent}%")

                if disk.percent > 90:
                    logger.warning(f"High disk usage: {disk.percent}%")
            else:
                # Fallback to basic monitoring if psutil not available
                logger.debug("Enhanced monitoring unavailable - psutil not installed")

                # Basic process monitoring using subprocess
                try:
                    if sys.platform == 'linux':
                        # Get basic memory info on Linux
                        mem_info = subprocess.run(['free', '-m'], capture_output=True, text=True)
                        if mem_info.returncode == 0:
                            logger.debug(f"Memory info: {mem_info.stdout.splitlines()[1]}")
                except Exception as e:
                    logger.debug(f"Basic monitoring error: {e}")

            # Monitor Django database connections (works without psutil)
            from django.db import connections
            for alias in connections:
                connection = connections[alias]
                if hasattr(connection, 'queries'):
                    query_count = len(connection.queries)
                    if query_count > 100:
                        logger.warning(f"High query count on {alias}: {query_count}")

            time.sleep(60)  # Monitor every minute

        except Exception as e:
            logger.error(f"Performance monitor worker error: {e}")
            time.sleep(120)  # Wait 2 minutes on error

    def _should_update_status(self, order):
        """Determine if an import order status should be updated"""
        # Simple time-based logic for demo (replace with real API checks)
        time_since_update = datetime.now() - order.updated_at
        return time_since_update.total_seconds() > 3600  # 1 hour

    def _generate_daily_reports(self):
        """Generate daily analytics reports"""
        try:
            logger.info("Generating daily reports...")

            # Get daily statistics
            User = get_user_model()
            from core.models import Car, Order, ImportRequest

            today = datetime.now().date()
            stats = {
                'date': today.isoformat(),
                'new_users': User.objects.filter(date_joined__date=today).count(),
                'new_cars': Car.objects.filter(created_at__date=today).count(),
                'new_orders': Order.objects.filter(created_at__date=today).count(),
                'new_imports': ImportRequest.objects.filter(created_at__date=today).count(),
            }

            # Save report to file
            reports_dir = PROJECT_DIR / 'reports'
            reports_dir.mkdir(exist_ok=True)

            report_file = reports_dir / f'daily_report_{today.isoformat()}.json'
            with open(report_file, 'w') as f:
                json.dump(stats, f, indent=2)

            logger.info(f"Daily report saved: {report_file}")

        except Exception as e:
            logger.error(f"Failed to generate daily reports: {e}")

    def _generate_weekly_analytics(self):
        """Generate weekly analytics"""
        try:
            logger.info("Generating weekly analytics...")

            # Implementation for weekly analytics
            # This would include more comprehensive analysis

        except Exception as e:
            logger.error(f"Failed to generate weekly analytics: {e}")

    def _cleanup_old_logs(self):
        """Clean up old log entries"""
        try:
            from core.models import ActivityLog, AuditLog

            # Remove logs older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)

            deleted_activity = ActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()
            deleted_audit = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()

            logger.info(f"Cleaned up {deleted_activity[0]} activity logs and {deleted_audit[0]} audit logs")

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")

    def _cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            backup_dir = PROJECT_DIR / 'backups'
            if not backup_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

            for backup_file in backup_dir.glob('db_backup_*.json'):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def setup_log_rotation(self):
        """Setup log rotation and cleanup"""
        try:
            from logging.handlers import RotatingFileHandler

            # Setup rotating file handler
            log_file = PROJECT_DIR / 'gurumisha_server.log'
            handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

            # Add to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(handler)

            logger.info("Log rotation setup complete")
            return True

        except Exception as e:
            logger.error(f"Failed to setup log rotation: {e}")
            return False

    def perform_security_scan(self):
        """Perform basic security checks"""
        try:
            logger.info("Performing security scan...")

            security_issues = []

            # Check for debug mode in production
            if getattr(settings, 'DEBUG', False):
                security_issues.append("DEBUG mode is enabled")

            # Check for default secret key
            secret_key = getattr(settings, 'SECRET_KEY', '')
            if 'django-insecure' in secret_key or len(secret_key) < 50:
                security_issues.append("Weak or default SECRET_KEY")

            # Check for HTTPS settings
            if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
                security_issues.append("SECURE_SSL_REDIRECT not enabled")

            # Check allowed hosts
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            if '*' in allowed_hosts:
                security_issues.append("Wildcard in ALLOWED_HOSTS")

            # Check for default admin credentials
            User = self.django_modules['get_user_model']()
            default_admin = User.objects.filter(username='admin').first()
            if default_admin and default_admin.check_password('Admin123'):
                security_issues.append("Default admin credentials detected")

            if security_issues:
                logger.warning("Security issues found:")
                for issue in security_issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("No security issues detected")

            return len(security_issues) == 0

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return False

    def monitor_worker_health(self):
        """Monitor worker process health and restart if needed"""
        try:
            for worker in self.worker_processes:
                if not worker.health_check():
                    logger.warning(f"Worker '{worker.name}' failed health check, restarting...")
                    worker.stop()
                    worker.start()

        except Exception as e:
            logger.error(f"Worker health monitoring failed: {e}")

    def initialize_sample_data(self):
        """Initialize sample data if database is empty"""
        try:
            User = get_user_model()
            from core.models import CarBrand, VehicleCondition

            # Check if we need sample data
            if User.objects.count() > 1:  # More than just admin
                logger.info("Database already has data, skipping sample data initialization")
                return True

            logger.info("Initializing sample data...")

            # Create sample car brands
            brands = ['Toyota', 'Honda', 'Nissan', 'Mercedes-Benz', 'BMW']
            for brand_name in brands:
                CarBrand.objects.get_or_create(name=brand_name)

            # Create vehicle conditions
            conditions = [
                ('new', 'New'),
                ('used', 'Used'),
                ('certified', 'Certified Pre-Owned')
            ]
            for code, name in conditions:
                VehicleCondition.objects.get_or_create(code=code, defaults={'name': name})

            logger.info("Sample data initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sample data: {e}")
            return False

    def populate_initial_data(self):
        """Populate comprehensive car models and create initial users"""
        try:
            logger.info("Starting initial data population...")

            # Always run comprehensive car models population to ensure latest models
            logger.info("Populating comprehensive car models...")
            if self.deployment_manager.populate_car_models():
                logger.info("Comprehensive car models populated successfully")

                # Log model statistics
                from core.models import CarMake, CarModel
                total_makes = CarMake.objects.filter(is_active=True).count()
                total_models = CarModel.objects.filter(is_active=True).count()
                logger.info(f"Database now contains {total_makes} car makes and {total_models} car models")

                # Log some popular brands
                popular_brands = ['Toyota', 'Honda', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Audi']
                for brand_name in popular_brands:
                    try:
                        brand = CarMake.objects.get(name=brand_name)
                        model_count = CarModel.objects.filter(make=brand, is_active=True).count()
                        logger.info(f"  {brand_name}: {model_count} models available")
                    except CarMake.DoesNotExist:
                        pass
            else:
                logger.warning("Car models population failed, but continuing...")

            # Create initial users
            logger.info("Creating initial users...")
            if hasattr(self, 'create_initial_users'):
                self.create_initial_users()
            else:
                # Fallback to management command
                from django.core.management import call_command
                call_command('create_initial_users')
            logger.info("Initial users created successfully")

            logger.info("Initial data population completed")
            return True

        except Exception as e:
            logger.error(f"Failed to populate initial data: {e}")
            return False

    def create_initial_users(self):
        """Create 3 customer users with realistic data"""
        try:
            logger.info("Creating customer users...")

            User = self.django_modules['get_user_model']()

            # Customer user data
            customers = [
                {
                    'username': 'john_customer',
                    'email': 'john.doe@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone': '+254712345678',
                    'city': 'Nairobi',
                    'password': 'customer123'
                },
                {
                    'username': 'mary_customer',
                    'email': 'mary.smith@example.com',
                    'first_name': 'Mary',
                    'last_name': 'Smith',
                    'phone': '+254723456789',
                    'city': 'Mombasa',
                    'password': 'customer123'
                },
                {
                    'username': 'peter_customer',
                    'email': 'peter.jones@example.com',
                    'first_name': 'Peter',
                    'last_name': 'Jones',
                    'phone': '+254734567890',
                    'city': 'Kisumu',
                    'password': 'customer123'
                }
            ]

            created_count = 0
            for customer_data in customers:
                if not User.objects.filter(username=customer_data['username']).exists():
                    user = User.objects.create_user(
                        username=customer_data['username'],
                        email=customer_data['email'],
                        first_name=customer_data['first_name'],
                        last_name=customer_data['last_name'],
                        password=customer_data['password']
                    )

                    # Set additional fields if they exist
                    if hasattr(user, 'phone'):
                        user.phone = customer_data['phone']
                    if hasattr(user, 'city'):
                        user.city = customer_data['city']
                    if hasattr(user, 'role'):
                        user.role = 'customer'
                    if hasattr(user, 'is_email_verified'):
                        user.is_email_verified = True

                    user.save()
                    created_count += 1
                    logger.info(f"Created customer user: {customer_data['username']}")
                else:
                    logger.info(f"Customer user already exists: {customer_data['username']}")

            logger.info(f"Customer user creation completed. Created: {created_count}")
            return True

        except Exception as e:
            logger.error(f"Failed to create customer users: {e}")
            return False

    def _kill_switch_monitor(self):
        """Monitor for kill switch activation"""
        while self.running:
            current_time = datetime.now()
            time_remaining = self.shutdown_time - current_time
            
            if time_remaining.total_seconds() <= 0:
                logger.critical("KILL SWITCH ACTIVATED - 4 days elapsed, shutting down server")
                self._send_shutdown_notifications()
                self.shutdown()
                break
            
            # Log remaining time every hour
            if time_remaining.total_seconds() % 3600 < 60:
                hours_remaining = int(time_remaining.total_seconds() // 3600)
                logger.info(f"Kill switch countdown: {hours_remaining} hours remaining")
            
            time.sleep(60)  # Check every minute
    
    def _send_shutdown_notifications(self):
        """Send notifications before shutdown"""
        try:
            # Send system message
            self.send_system_message(
                title="Server Maintenance Notice",
                content="The server will be shutting down for scheduled maintenance. Thank you for your patience.",
                target_audience='all',
                message_type='maintenance',
                priority=4
            )
            
            # Send notifications to all users
            self.send_notification_to_users(
                title="Server Maintenance",
                message="The Gurumisha platform will be temporarily unavailable for maintenance.",
                user_roles=['customer', 'vendor', 'admin'],
                channels=['in_app', 'email']
            )
            
            logger.info("Shutdown notifications sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send shutdown notifications: {e}")
    
    def start(self):
        """Start the Django server with comprehensive initialization"""
        try:
            logger.info("Starting Gurumisha Django Server with comprehensive deployment features...")
            logger.info(f"Server URL: http://{self.host}:{self.port}")
            logger.info(f"Admin Panel: http://{self.host}:{self.port}/admin/")
            logger.info(f"Kill switch will activate in {self.kill_switch_days} days")

            # Check for enhanced dependencies
            if self.auto_init and not PSUTIL_AVAILABLE:
                logger.warning("Enhanced features are limited - psutil not installed")
                logger.warning("Run 'python server.py --install-enhanced-deps' to enable all features")
                print("\nNOTE: Enhanced features are limited. To enable all features, run:")
                print("      python server.py --install-enhanced-deps\n")

            # Comprehensive initialization process
            if self.auto_init:
                logger.info("Running comprehensive initialization...")

                # Step 1: Ensure Python environment
                if not self.deployment_manager.ensure_python_environment():
                    logger.error("Python environment setup failed")
                    return

                # Step 2: Install core dependencies
                if not self.deployment_manager.install_core_dependencies():
                    logger.error("Core dependency installation failed")
                    return

                # Step 3: Install project dependencies
                if not self.deployment_manager.install_project_dependencies():
                    logger.error("Project dependency installation failed")
                    return

                # Step 4: Install enhanced dependencies if possible
                self.deployment_manager.install_enhanced_dependencies()

                # Step 5: Initialize Django
                if not self.deployment_manager.initialize_django():
                    logger.error("Django initialization failed")
                    return

                # Step 6: Apply migrations
                if not self.deployment_manager.apply_migrations():
                    logger.error("Migration application failed")
                    return

                # Step 7: Collect static files
                if not self.deployment_manager.collect_static_files():
                    logger.warning("Static file collection failed, continuing...")

                # Step 8: Setup log rotation
                self.setup_log_rotation()

                # Step 9: Perform security scan
                self.perform_security_scan()

                # Step 10: Create backup before starting
                backup_file = self.deployment_manager.backup_database()
                if backup_file:
                    logger.info(f"Pre-startup backup created: {backup_file}")
            else:
                # Minimal initialization - just initialize Django
                if not self.deployment_manager.initialize_django():
                    logger.error("Django initialization failed")
                    return

            # Create default admin user with specified credentials
            admin_created = self.deployment_manager.create_superuser(
                username='admin',
                email='admin@gurumisha.com',
                password='Admin123'
            )

            if admin_created:
                logger.info("Default admin created with email: admin@gurumisha.com")
                logger.info("Default admin password: Admin123")
                logger.warning("Please change the default admin password after first login!")

            # Populate car models and initial data
            self.populate_initial_data()

            # Setup worker processes
            if not self.setup_worker_processes():
                logger.warning("Worker process setup failed, continuing without workers...")

            # Start kill switch monitor in separate thread
            self.running = True
            self.kill_switch_thread = threading.Thread(target=self._kill_switch_monitor)
            self.kill_switch_thread.daemon = True
            self.kill_switch_thread.start()

            # Start worker health monitoring
            health_monitor_thread = threading.Thread(target=self._worker_health_monitor)
            health_monitor_thread.daemon = True
            health_monitor_thread.start()

            # Start Django development server
            logger.info(f"Starting Django server on {self.host}:{self.port}...")
            self.server_process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', f'{self.host}:{self.port}'
            ], cwd=PROJECT_DIR)

            logger.info("Django server started successfully")
            logger.info("All systems operational - server ready for requests")

            # Wait for server process
            self.server_process.wait()

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.shutdown()

    def _worker_health_monitor(self):
        """Background thread to monitor worker health"""
        while self.running:
            try:
                self.monitor_worker_health()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Worker health monitor error: {e}")
                time.sleep(60)
    
    def shutdown(self):
        """Graceful server shutdown with enhanced cleanup"""
        if not self.running:
            return

        logger.info("Initiating enhanced server shutdown...")
        self.running = False

        try:
            # Stop worker processes
            logger.info("Stopping worker processes...")
            for worker in self.worker_processes:
                worker.stop()

            # Shutdown worker executor
            self.worker_executor.shutdown(wait=True, timeout=30)

            # Terminate Django server process
            if self.server_process and self.server_process.poll() is None:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                logger.info("Django server process terminated")

        except subprocess.TimeoutExpired:
            logger.warning("Server process did not terminate gracefully, forcing shutdown")
            self.server_process.kill()
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")

        # Final backup before shutdown
        try:
            backup_file = ServerManager.backup_database()
            if backup_file:
                logger.info(f"Final backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Failed to create final backup: {e}")

        # Calculate uptime
        uptime = datetime.now() - self.start_time
        logger.info(f"Server uptime: {uptime}")
        logger.info("Enhanced Gurumisha server shutdown complete")


def main():
    """Comprehensive main entry point with deployment options"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Gurumisha Django Server - Comprehensive Deployment Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python server.py                          # Start with default settings
  python server.py --auto-init              # Start with full initialization
  python server.py --install-deps           # Install dependencies only
  python server.py --deploy-production      # Configure for production deployment
  python server.py --backup-db              # Create database backup only
  python server.py --generate-nginx-config  # Generate Nginx configuration
        """
    )

    # Server configuration
    parser.add_argument('--host', default='127.0.0.1',
                       help='Server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Server port (default: 8000)')
    parser.add_argument('--kill-switch-days', type=int, default=4,
                       help='Days until automatic shutdown (default: 4)')

    # Initialization options
    parser.add_argument('--auto-init', action='store_true',
                       help='Enable automatic initialization and setup')
    parser.add_argument('--no-workers', action='store_true',
                       help='Disable background worker processes')

    # Dependency management
    parser.add_argument('--install-deps', action='store_true',
                       help='Install dependencies from requirements.txt')
    parser.add_argument('--install-enhanced-deps', action='store_true',
                       help='Install enhanced server dependencies (psutil, cryptography, etc.)')
    parser.add_argument('--upgrade-deps', action='store_true',
                       help='Upgrade all outdated packages')
    parser.add_argument('--verify-deps', action='store_true',
                       help='Verify all dependencies are installed')

    # Database operations
    parser.add_argument('--migrate', action='store_true',
                       help='Apply database migrations only')
    parser.add_argument('--backup-db', action='store_true',
                       help='Create database backup only')
    parser.add_argument('--restore-db', metavar='BACKUP_FILE',
                       help='Restore database from backup file')
    parser.add_argument('--collect-static', action='store_true',
                       help='Collect static files only')

    # Admin and messaging
    parser.add_argument('--create-admin', action='store_true',
                       help='Create admin user interactively')
    parser.add_argument('--send-message', action='store_true',
                       help='Send system message interactively')
    parser.add_argument('--secure-admin', action='store_true',
                       help='Create admin with secure generated password')

    # Deployment operations
    parser.add_argument('--deploy-production', action='store_true',
                       help='Configure for production deployment')
    parser.add_argument('--domain',
                       help='Domain name for production deployment')
    parser.add_argument('--db-type', choices=['sqlite', 'postgres'], default='sqlite',
                       help='Database type for production (default: sqlite)')
    parser.add_argument('--setup-ssl', action='store_true',
                       help='Setup SSL certificate using Let\'s Encrypt')
    parser.add_argument('--ssl-email',
                       help='Email for SSL certificate registration')
    parser.add_argument('--generate-nginx-config', action='store_true',
                       help='Generate Nginx configuration file')

    # Maintenance operations
    parser.add_argument('--security-scan', action='store_true',
                       help='Run security vulnerability scan')
    parser.add_argument('--health-check', action='store_true',
                       help='Run system health check')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old logs and backups')
    parser.add_argument('--stats', action='store_true',
                       help='Show system statistics')

    args = parser.parse_args()

    # Create server instance
    server = GurumishaServer(
        host=args.host,
        port=args.port,
        kill_switch_days=args.kill_switch_days,
        auto_init=args.auto_init
    )

    # Handle dependency management operations
    if args.install_deps:
        success = server.deployment_manager.install_project_dependencies()
        sys.exit(0 if success else 1)

    if args.install_enhanced_deps:
        success = server.deployment_manager.install_enhanced_dependencies()
        # Inform user to restart the server to use enhanced features
        if success:
            print("\nEnhanced dependencies installed successfully!")
            print("Please restart the server to use all enhanced features.")
        sys.exit(0 if success else 1)

    if args.upgrade_deps:
        success = server.dependency_manager.upgrade_packages()
        sys.exit(0 if success else 1)

    if args.verify_deps:
        success = server.dependency_manager.verify_dependencies()
        sys.exit(0 if success else 1)

    # Handle database operations
    if args.migrate:
        success = server.deployment_manager.apply_migrations()
        sys.exit(0 if success else 1)

    if args.backup_db:
        backup_file = server.deployment_manager.backup_database()
        if backup_file:
            print(f"Backup created: {backup_file}")
            sys.exit(0)
        else:
            sys.exit(1)

    if args.restore_db:
        success = server.deployment_manager.restore_database(args.restore_db)
        sys.exit(0 if success else 1)

    if args.collect_static:
        success = server.deployment_manager.collect_static_files()
        sys.exit(0 if success else 1)

    # Handle deployment operations
    if args.deploy_production:
        if not args.domain:
            print("Error: --domain is required for production deployment")
            sys.exit(1)

        print(f"Configuring production deployment for {args.domain}...")

        # Setup production environment
        success = server.deployment_manager.setup_production_environment(
            domain_name=args.domain,
            debug=False,
            db_type=args.db_type
        )

        if success:
            print(f"Production environment configured for {args.domain}")
            print("Next steps:")
            print("1. Configure your web server (Nginx/Apache)")
            print("2. Set up SSL certificate")
            print("3. Configure firewall")
            print("4. Start the server with --auto-init")

        sys.exit(0 if success else 1)

    if args.setup_ssl:
        if not args.domain or not args.ssl_email:
            print("Error: --domain and --ssl-email are required for SSL setup")
            sys.exit(1)

        ssl_config = server.deployment_manager.setup_ssl_certificate(
            domain=args.domain,
            email=args.ssl_email,
            use_staging=False
        )

        if ssl_config:
            print("SSL certificate obtained successfully!")
            print(f"Certificate: {ssl_config['cert_path']}")
            print(f"Private key: {ssl_config['key_path']}")

        sys.exit(0 if ssl_config else 1)

    if args.generate_nginx_config:
        if not args.domain:
            print("Error: --domain is required for Nginx config generation")
            sys.exit(1)

        # Check if SSL config exists
        ssl_config = None
        cert_path = f"/etc/letsencrypt/live/{args.domain}/fullchain.pem"
        key_path = f"/etc/letsencrypt/live/{args.domain}/privkey.pem"

        if Path(cert_path).exists() and Path(key_path).exists():
            ssl_config = {'cert_path': cert_path, 'key_path': key_path}

        config_file = server.deployment_manager.generate_nginx_config(
            domain=args.domain,
            port=args.port,
            ssl_config=ssl_config
        )

        if config_file:
            print(f"Nginx configuration generated: {config_file}")
            print("To enable this configuration:")
            print(f"1. sudo cp {config_file} /etc/nginx/sites-available/{args.domain}")
            print(f"2. sudo ln -s /etc/nginx/sites-available/{args.domain} /etc/nginx/sites-enabled/")
            print("3. sudo nginx -t")
            print("4. sudo systemctl reload nginx")

        sys.exit(0 if config_file else 1)

    # Handle maintenance operations
    if args.security_scan:
        # Initialize Django first
        server.deployment_manager.initialize_django()
        success = server.perform_security_scan()
        sys.exit(0 if success else 1)

    if args.health_check:
        # Initialize Django first
        server.deployment_manager.initialize_django()
        success = ServerManager.check_system_health()
        sys.exit(0 if success else 1)

    if args.cleanup:
        server._cleanup_old_logs()
        server._cleanup_old_backups()
        print("Cleanup completed")
        sys.exit(0)

    if args.stats:
        # Initialize Django first
        server.deployment_manager.initialize_django()

        # Get system statistics
        try:
            # Import Django modules after initialization
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Import core models
            from core.models import Car, SparePart, ImportRequest, Order, Message, Notification

            stats = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'customers': User.objects.filter(role='customer').count(),
                'vendors': User.objects.filter(role='vendor').count(),
                'admins': User.objects.filter(role='admin').count(),
                'total_cars': Car.objects.count(),
                'total_spare_parts': SparePart.objects.count(),
                'total_import_requests': ImportRequest.objects.count(),
                'total_orders': Order.objects.count(),
                'unread_notifications': Notification.objects.filter(is_read=False).count(),
                'active_messages': Message.objects.filter(status='active').count(),
            }

            print("System Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"Error getting statistics: {e}")
            sys.exit(1)

        sys.exit(0)

    # Handle admin operations
    if args.create_admin:
        # Initialize Django first
        server.deployment_manager.initialize_django()

        username = input("Admin username: ")
        email = input("Admin email: ")
        password = input("Admin password: ")
        success = server.deployment_manager.create_superuser(username, email, password)
        sys.exit(0 if success else 1)

    if args.secure_admin:
        # Initialize Django first
        server.deployment_manager.initialize_django()

        username = input("Admin username: ")
        email = input("Admin email: ")
        password = ''.join(secrets.choice(
            string.ascii_letters + string.digits + "!@#$%^&*"
        ) for i in range(16))

        success = server.deployment_manager.create_superuser(username, email, password)
        if success:
            print(f"Admin created with secure password: {password}")
            print("Please save this password securely!")
        sys.exit(0 if success else 1)

    if args.send_message:
        # Initialize Django first
        server.deployment_manager.initialize_django()

        title = input("Message title: ")
        content = input("Message content: ")
        audience = input("Target audience (all/customers/vendors/admins): ") or 'all'

        # Import Django modules after initialization
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Import core models
        from core.models import Message

        # Create message
        try:
            message = Message.objects.create(
                title=title,
                content=content,
                target_audience=audience,
                message_type='announcement',
                priority=2,
                status='active',
                publication_date=datetime.now(),
                created_by_id=1  # Assume first admin user
            )
            print(f"Message created: '{title}' for {audience}")
            sys.exit(0)
        except Exception as e:
            print(f"Failed to send message: {e}")
            sys.exit(1)

    # Disable workers if requested
    if args.no_workers:
        server.worker_processes = []

    # Start the server
    server.start()


class ServerManager:
    """Additional server management utilities"""

    @staticmethod
    def check_system_health():
        """Check system health and database connectivity"""
        try:
            from django.db import connection
            from django.core.management import call_command

            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            # Check for pending migrations
            try:
                call_command('showmigrations', '--plan', verbosity=0)
                logger.info("Database health check passed")
                return True
            except Exception as e:
                logger.error(f"Migration check failed: {e}")
                return False

        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return False

    @staticmethod
    def backup_database():
        """Create database backup"""
        try:
            # Create a deployment manager instance
            deployment_manager = DeploymentManager(PROJECT_DIR)

            # Initialize Django
            if not deployment_manager.initialize_django():
                logger.error("Failed to initialize Django")
                return None

            # Create backup
            return deployment_manager.backup_database()

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None

    @staticmethod
    def get_server_stats():
        """Get server statistics"""
        try:
            # Import Django modules
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Import core models
            from core.models import Car, SparePart, ImportRequest, Order, Message, Notification

            stats = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'customers': User.objects.filter(role='customer').count(),
                'vendors': User.objects.filter(role='vendor').count(),
                'admins': User.objects.filter(role='admin').count(),
                'total_cars': Car.objects.count(),
                'total_spare_parts': SparePart.objects.count(),
                'total_import_requests': ImportRequest.objects.count(),
                'total_orders': Order.objects.count(),
                'unread_notifications': Notification.objects.filter(is_read=False).count(),
                'active_messages': Message.objects.filter(status='active').count(),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get server stats: {e}")
            return {}


def setup_server_environment():
    """Setup server environment and perform initial checks"""
    logger.info("Setting up server environment...")

    # Check if we're in the correct directory
    if not (PROJECT_DIR / 'manage.py').exists():
        logger.error("manage.py not found. Please run server.py from the project root.")
        sys.exit(1)

    # Initialize deployment manager
    deployment_manager = DeploymentManager(PROJECT_DIR)

    # Try to initialize Django for health checks
    try:
        if deployment_manager.initialize_django():
            logger.info("Django initialized for environment setup")

            # Check database health
            if not ServerManager.check_system_health():
                logger.warning("Database health check failed, but continuing...")

            # Create backup before starting
            backup_file = ServerManager.backup_database()
            if backup_file:
                logger.info(f"Pre-startup backup created: {backup_file}")

            # Log server statistics
            stats = ServerManager.get_server_stats()
            if stats:
                logger.info("Current server statistics:")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
        else:
            logger.warning("Django initialization failed during environment setup")
            logger.info("Will attempt full initialization during server start")

    except Exception as e:
        logger.warning(f"Environment setup checks failed: {e}")
        logger.info("Will attempt full initialization during server start")

    logger.info("Server environment setup complete")


if __name__ == '__main__':
    # Setup environment before starting
    setup_server_environment()
    main()
