#!/usr/bin/env python3
"""
Gurumisha Motors - Health Check Script
Monitors application health and system status
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project to Python path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings_production')

try:
    import django
    django.setup()
    
    from django.db import connection
    from django.core.cache import cache
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from core.models import Car, SparePart, ImportRequest
    
    DJANGO_AVAILABLE = True
except ImportError as e:
    DJANGO_AVAILABLE = False
    DJANGO_ERROR = str(e)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_DIR / 'logs' / 'health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health check for Gurumisha Motors application"""
    
    def __init__(self):
        self.checks = {}
        self.start_time = time.time()
        
    def check_django_setup(self):
        """Check if Django is properly configured"""
        try:
            if not DJANGO_AVAILABLE:
                return False, f"Django import failed: {DJANGO_ERROR}"
            
            # Test settings access
            debug_mode = settings.DEBUG
            secret_key = bool(settings.SECRET_KEY)
            
            if not secret_key:
                return False, "SECRET_KEY not configured"
                
            return True, f"Django OK (Debug: {debug_mode})"
            
        except Exception as e:
            return False, f"Django configuration error: {str(e)}"
    
    def check_database(self):
        """Check database connectivity and basic operations"""
        try:
            if not DJANGO_AVAILABLE:
                return False, "Django not available"
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            if result[0] != 1:
                return False, "Database query returned unexpected result"
            
            # Test model access
            User = get_user_model()
            user_count = User.objects.count()
            car_count = Car.objects.count()
            
            return True, f"Database OK (Users: {user_count}, Cars: {car_count})"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def check_cache(self):
        """Check cache system functionality"""
        try:
            if not DJANGO_AVAILABLE:
                return False, "Django not available"
            
            # Test cache write/read
            test_key = 'health_check_test'
            test_value = f'test_{int(time.time())}'
            
            cache.set(test_key, test_value, 30)
            cached_value = cache.get(test_key)
            
            if cached_value != test_value:
                return False, "Cache read/write mismatch"
            
            # Clean up
            cache.delete(test_key)
            
            return True, "Cache OK"
            
        except Exception as e:
            return False, f"Cache error: {str(e)}"
    
    def check_static_files(self):
        """Check static files availability"""
        try:
            static_root = PROJECT_DIR / 'staticfiles'
            
            if not static_root.exists():
                return False, "Static files directory not found"
            
            # Check for key static files
            css_files = list(static_root.glob('**/*.css'))
            js_files = list(static_root.glob('**/*.js'))
            
            if not css_files:
                return False, "No CSS files found"
            
            if not js_files:
                return False, "No JavaScript files found"
            
            return True, f"Static files OK (CSS: {len(css_files)}, JS: {len(js_files)})"
            
        except Exception as e:
            return False, f"Static files error: {str(e)}"
    
    def check_media_files(self):
        """Check media files directory"""
        try:
            media_root = PROJECT_DIR / 'media'
            
            if not media_root.exists():
                media_root.mkdir(parents=True, exist_ok=True)
                return True, "Media directory created"
            
            # Check permissions
            if not os.access(media_root, os.W_OK):
                return False, "Media directory not writable"
            
            return True, "Media directory OK"
            
        except Exception as e:
            return False, f"Media files error: {str(e)}"
    
    def check_logs(self):
        """Check logging system"""
        try:
            logs_dir = PROJECT_DIR / 'logs'
            
            if not logs_dir.exists():
                logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Test log writing
            test_log = logs_dir / 'health_check.log'
            with open(test_log, 'a') as f:
                f.write(f"Health check test: {datetime.now()}\n")
            
            return True, "Logging OK"
            
        except Exception as e:
            return False, f"Logging error: {str(e)}"
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(PROJECT_DIR)
            
            # Convert to GB
            total_gb = total // (1024**3)
            used_gb = used // (1024**3)
            free_gb = free // (1024**3)
            
            usage_percent = (used / total) * 100
            
            if usage_percent > 95:
                return False, f"Disk space critical: {usage_percent:.1f}% used"
            elif usage_percent > 85:
                return False, f"Disk space warning: {usage_percent:.1f}% used"
            
            return True, f"Disk space OK: {free_gb}GB free ({usage_percent:.1f}% used)"
            
        except Exception as e:
            return False, f"Disk space check error: {str(e)}"
    
    def check_memory(self):
        """Check memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 95:
                return False, f"Memory critical: {usage_percent}% used"
            elif usage_percent > 85:
                return False, f"Memory warning: {usage_percent}% used"
            
            return True, f"Memory OK: {usage_percent}% used"
            
        except ImportError:
            return True, "Memory check skipped (psutil not available)"
        except Exception as e:
            return False, f"Memory check error: {str(e)}"
    
    def check_environment(self):
        """Check environment configuration"""
        try:
            env_file = PROJECT_DIR / '.env'
            
            if not env_file.exists():
                return False, "Environment file (.env) not found"
            
            # Check for required environment variables
            required_vars = [
                'SECRET_KEY',
                'DATABASE_URL',
                'EMAIL_HOST_USER',
                'EMAIL_HOST_PASSWORD'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return False, f"Missing environment variables: {', '.join(missing_vars)}"
            
            return True, "Environment configuration OK"
            
        except Exception as e:
            return False, f"Environment check error: {str(e)}"
    
    def run_all_checks(self):
        """Run all health checks"""
        check_methods = [
            ('django_setup', self.check_django_setup),
            ('database', self.check_database),
            ('cache', self.check_cache),
            ('static_files', self.check_static_files),
            ('media_files', self.check_media_files),
            ('logs', self.check_logs),
            ('disk_space', self.check_disk_space),
            ('memory', self.check_memory),
            ('environment', self.check_environment),
        ]
        
        results = {}
        all_passed = True
        
        for check_name, check_method in check_methods:
            try:
                passed, message = check_method()
                results[check_name] = {
                    'status': 'PASS' if passed else 'FAIL',
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                if not passed:
                    all_passed = False
                    logger.error(f"Health check failed - {check_name}: {message}")
                else:
                    logger.info(f"Health check passed - {check_name}: {message}")
                    
            except Exception as e:
                results[check_name] = {
                    'status': 'ERROR',
                    'message': f"Check failed with exception: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                }
                all_passed = False
                logger.error(f"Health check error - {check_name}: {str(e)}")
        
        # Add summary
        results['summary'] = {
            'overall_status': 'HEALTHY' if all_passed else 'UNHEALTHY',
            'total_checks': len(check_methods),
            'passed_checks': sum(1 for r in results.values() if r.get('status') == 'PASS'),
            'failed_checks': sum(1 for r in results.values() if r.get('status') in ['FAIL', 'ERROR']),
            'execution_time': round(time.time() - self.start_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        return results, all_passed

def main():
    """Main health check execution"""
    checker = HealthChecker()
    results, all_passed = checker.run_all_checks()
    
    # Output results
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # JSON output for programmatic use
        print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        print(f"\nGurumisha Motors - Health Check Report")
        print(f"{'='*50}")
        print(f"Timestamp: {results['summary']['timestamp']}")
        print(f"Overall Status: {results['summary']['overall_status']}")
        print(f"Execution Time: {results['summary']['execution_time']}s")
        print(f"\nChecks: {results['summary']['passed_checks']}/{results['summary']['total_checks']} passed")
        print(f"{'='*50}")
        
        for check_name, result in results.items():
            if check_name == 'summary':
                continue
                
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {check_name.replace('_', ' ').title()}: {result['message']}")
        
        print(f"{'='*50}")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
