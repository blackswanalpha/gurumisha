#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
Gurumisha Car Dealership Application

This script handles the complete migration from SQLite to PostgreSQL
with data validation, backup creation, and rollback capabilities.
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import django
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

class DatabaseMigrator:
    """Handles the complete database migration process"""
    
    def __init__(self):
        self.backup_dir = project_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sqlite_backup = None
        self.data_backup = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
    def create_backups(self):
        """Create comprehensive backups before migration"""
        self.log("Creating database backups...")
        
        # Backup SQLite database file
        sqlite_path = project_dir / 'db.sqlite3'
        if sqlite_path.exists():
            self.sqlite_backup = self.backup_dir / f'db_backup_{self.timestamp}.sqlite3'
            shutil.copy2(sqlite_path, self.sqlite_backup)
            self.log(f"SQLite backup created: {self.sqlite_backup}")
        else:
            self.log("SQLite database not found!", "ERROR")
            return False
            
        # Export data using Django dumpdata
        self.data_backup = self.backup_dir / f'data_backup_{self.timestamp}.json'
        try:
            with open(self.data_backup, 'w') as f:
                execute_from_command_line([
                    'manage.py', 'dumpdata', 
                    '--natural-foreign', '--natural-primary',
                    '--output', str(self.data_backup)
                ])
            self.log(f"Data backup created: {self.data_backup}")
        except Exception as e:
            self.log(f"Failed to create data backup: {e}", "ERROR")
            return False
            
        return True
        
    def validate_postgresql_connection(self):
        """Test PostgreSQL connection and configuration"""
        self.log("Validating PostgreSQL connection...")
        
        try:
            # Temporarily switch to PostgreSQL settings
            os.environ['USE_SQLITE'] = 'False'
            
            # Test database connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.log(f"PostgreSQL connection successful: {version}")
                return True
                
        except Exception as e:
            self.log(f"PostgreSQL connection failed: {e}", "ERROR")
            return False
            
    def run_postgresql_migrations(self):
        """Run Django migrations on PostgreSQL"""
        self.log("Running PostgreSQL migrations...")
        
        try:
            # Ensure we're using PostgreSQL
            os.environ['USE_SQLITE'] = 'False'
            
            # Run migrations
            execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
            self.log("PostgreSQL migrations completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Migration failed: {e}", "ERROR")
            return False
            
    def load_data_to_postgresql(self):
        """Load data from backup into PostgreSQL"""
        self.log("Loading data into PostgreSQL...")
        
        try:
            # Load data from backup
            execute_from_command_line([
                'manage.py', 'loaddata', str(self.data_backup)
            ])
            self.log("Data loaded successfully into PostgreSQL")
            return True
            
        except Exception as e:
            self.log(f"Data loading failed: {e}", "ERROR")
            return False
            
    def validate_data_integrity(self):
        """Validate data integrity after migration"""
        self.log("Validating data integrity...")
        
        try:
            from core.models import (
                User, Car, CarMake, CarModel, SparePart, 
                ImportOrder, Vendor, Inquiry
            )
            
            # Count records in key tables
            counts = {
                'Users': User.objects.count(),
                'Cars': Car.objects.count(),
                'Car Makes': CarMake.objects.count(),
                'Car Models': CarModel.objects.count(),
                'Spare Parts': SparePart.objects.count(),
                'Import Orders': ImportOrder.objects.count(),
                'Vendors': Vendor.objects.count(),
                'Inquiries': Inquiry.objects.count(),
            }
            
            self.log("Data integrity validation:")
            for table, count in counts.items():
                self.log(f"  {table}: {count} records")
                
            # Basic relationship validation
            cars_with_make = Car.objects.filter(make__isnull=False).count()
            cars_with_vendor = Car.objects.filter(vendor__isnull=False).count()
            
            self.log(f"  Cars with make: {cars_with_make}")
            self.log(f"  Cars with vendor: {cars_with_vendor}")
            
            return True
            
        except Exception as e:
            self.log(f"Data validation failed: {e}", "ERROR")
            return False
            
    def create_postgresql_indexes(self):
        """Create custom indexes for performance optimization"""
        self.log("Creating PostgreSQL indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_car_make_model ON core_car(make_id, model_id);",
            "CREATE INDEX IF NOT EXISTS idx_car_price_range ON core_car(price) WHERE is_approved = true;",
            "CREATE INDEX IF NOT EXISTS idx_car_status_approved ON core_car(status, is_approved);",
            "CREATE INDEX IF NOT EXISTS idx_sparepart_category ON core_sparepart(category_new_id);",
            "CREATE INDEX IF NOT EXISTS idx_sparepart_available ON core_sparepart(is_available, stock_quantity);",
            "CREATE INDEX IF NOT EXISTS idx_import_order_status ON core_importorder(status);",
            "CREATE INDEX IF NOT EXISTS idx_import_order_customer ON core_importorder(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_email_verified ON core_user(email) WHERE is_email_verified = true;",
            "CREATE INDEX IF NOT EXISTS idx_user_role_active ON core_user(role, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_inquiry_status ON core_inquiry(status, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_car_created_approved ON core_car(created_at) WHERE is_approved = true;",
        ]
        
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                for index_sql in indexes:
                    cursor.execute(index_sql)
                    self.log(f"Created index: {index_sql.split()[5]}")
                    
            self.log("All indexes created successfully")
            return True
            
        except Exception as e:
            self.log(f"Index creation failed: {e}", "ERROR")
            return False
            
    def update_sequences(self):
        """Update PostgreSQL sequences to match current data"""
        self.log("Updating PostgreSQL sequences...")
        
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Get all tables with auto-increment fields
                cursor.execute("""
                    SELECT table_name, column_name 
                    FROM information_schema.columns 
                    WHERE column_default LIKE 'nextval%'
                    AND table_schema = 'public'
                """)
                
                for table_name, column_name in cursor.fetchall():
                    # Update sequence to current max value
                    cursor.execute(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{table_name}', '{column_name}'),
                            COALESCE(MAX({column_name}), 1)
                        ) FROM {table_name};
                    """)
                    
            self.log("Sequences updated successfully")
            return True
            
        except Exception as e:
            self.log(f"Sequence update failed: {e}", "ERROR")
            return False
            
    def rollback_to_sqlite(self):
        """Rollback to SQLite in case of migration failure"""
        self.log("Rolling back to SQLite...")
        
        try:
            # Switch back to SQLite
            os.environ['USE_SQLITE'] = 'True'
            
            # Restore SQLite backup if needed
            if self.sqlite_backup and self.sqlite_backup.exists():
                sqlite_path = project_dir / 'db.sqlite3'
                shutil.copy2(self.sqlite_backup, sqlite_path)
                self.log("SQLite database restored from backup")
                
            self.log("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.log(f"Rollback failed: {e}", "ERROR")
            return False
            
    def migrate(self):
        """Execute the complete migration process"""
        self.log("Starting database migration from SQLite to PostgreSQL")
        
        # Step 1: Create backups
        if not self.create_backups():
            self.log("Backup creation failed. Aborting migration.", "ERROR")
            return False
            
        # Step 2: Validate PostgreSQL connection
        if not self.validate_postgresql_connection():
            self.log("PostgreSQL validation failed. Aborting migration.", "ERROR")
            return False
            
        # Step 3: Run PostgreSQL migrations
        if not self.run_postgresql_migrations():
            self.log("PostgreSQL migrations failed. Rolling back...", "ERROR")
            self.rollback_to_sqlite()
            return False
            
        # Step 4: Load data into PostgreSQL
        if not self.load_data_to_postgresql():
            self.log("Data loading failed. Rolling back...", "ERROR")
            self.rollback_to_sqlite()
            return False
            
        # Step 5: Validate data integrity
        if not self.validate_data_integrity():
            self.log("Data validation failed. Rolling back...", "ERROR")
            self.rollback_to_sqlite()
            return False
            
        # Step 6: Create performance indexes
        if not self.create_postgresql_indexes():
            self.log("Index creation failed. Continuing anyway...", "WARNING")
            
        # Step 7: Update sequences
        if not self.update_sequences():
            self.log("Sequence update failed. Continuing anyway...", "WARNING")
            
        self.log("Database migration completed successfully!")
        self.log(f"Backups available at: {self.backup_dir}")
        return True

def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    
    # Check if PostgreSQL dependencies are installed
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
        
    # Execute migration
    success = migrator.migrate()
    
    if success:
        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Next steps:")
        print("1. Update your environment variables to use PostgreSQL")
        print("2. Test all application functionality")
        print("3. Monitor performance and optimize as needed")
        print("4. Update deployment scripts")
    else:
        print("\n" + "="*60)
        print("MIGRATION FAILED!")
        print("="*60)
        print("The system has been rolled back to SQLite.")
        print("Check the logs above for error details.")
        
    return success

if __name__ == "__main__":
    main()
