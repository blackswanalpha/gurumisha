"""
Management command to create all authentication test accounts from auth.txt
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Vendor

User = get_user_model()


class Command(BaseCommand):
    help = 'Create all authentication test accounts with verified status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating authentication test accounts...'))
        
        # Admin Account
        self.create_admin_account()
        
        # Vendor Accounts
        self.create_vendor_accounts()
        
        # Customer Accounts
        self.create_customer_accounts()
        
        # Additional Test Accounts
        self.create_additional_test_accounts()
        
        self.stdout.write(self.style.SUCCESS('All authentication test accounts created successfully!'))
        self.display_credentials()

    def create_admin_account(self):
        """Create admin account"""
        admin_data = {
            'username': 'admin',
            'email': 'admin@gurumisha.com',
            'password': 'admin123',
            'role': 'admin'
        }
        
        user, created = User.objects.get_or_create(
            username=admin_data['username'],
            defaults={
                'email': admin_data['email'],
                'role': admin_data['role'],
                'is_verified': True,
                'is_email_verified': True,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'System',
                'last_name': 'Administrator'
            }
        )
        
        if created:
            user.set_password(admin_data['password'])
            user.save()
            self.stdout.write(f'✅ Created admin user: {admin_data["username"]}')
        else:
            # Update existing user to ensure verified status
            user.is_verified = True
            user.is_email_verified = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(f'✅ Updated admin user: {admin_data["username"]}')

    def create_vendor_accounts(self):
        """Create vendor accounts"""
        vendors_data = [
            {
                'username': 'tokyomotors',
                'email': 'vendor1@gurumisha.com',
                'password': 'vendor123',
                'company': 'Tokyo Motors Kenya',
                'first_name': 'Tokyo',
                'last_name': 'Motors'
            },
            {
                'username': 'nairobiparts',
                'email': 'vendor2@gurumisha.com',
                'password': 'vendor123',
                'company': 'Nairobi Auto Parts',
                'first_name': 'Nairobi',
                'last_name': 'Parts'
            },
            {
                'username': 'mombasacars',
                'email': 'vendor3@gurumisha.com',
                'password': 'vendor123',
                'company': 'Mombasa Car Dealers',
                'first_name': 'Mombasa',
                'last_name': 'Cars'
            }
        ]
        
        for vendor_data in vendors_data:
            user, created = User.objects.get_or_create(
                username=vendor_data['username'],
                defaults={
                    'email': vendor_data['email'],
                    'role': 'vendor',
                    'is_verified': True,
                    'is_email_verified': True,
                    'first_name': vendor_data['first_name'],
                    'last_name': vendor_data['last_name']
                }
            )
            
            if created:
                user.set_password(vendor_data['password'])
                user.save()
                self.stdout.write(f'✅ Created vendor user: {vendor_data["username"]}')
            else:
                # Update existing user to ensure verified status
                user.is_verified = True
                user.is_email_verified = True
                user.save()
                self.stdout.write(f'✅ Updated vendor user: {vendor_data["username"]}')
            
            # Create or update vendor profile
            vendor, vendor_created = Vendor.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': vendor_data['company'],
                    'is_approved': True,
                    'approval_date': timezone.now(),
                    'description': f'Professional automotive services by {vendor_data["company"]}',
                    'email_notifications': True,
                    'inquiry_notifications': True,
                    'order_notifications': True
                }
            )
            
            if vendor_created:
                self.stdout.write(f'✅ Created vendor profile: {vendor_data["company"]}')
            else:
                # Update existing vendor to ensure approved status
                vendor.is_approved = True
                vendor.approval_date = timezone.now()
                vendor.save()
                self.stdout.write(f'✅ Updated vendor profile: {vendor_data["company"]}')

    def create_customer_accounts(self):
        """Create customer accounts"""
        customers_data = [
            {
                'username': 'johndoe',
                'email': 'customer1@gurumisha.com',
                'password': 'customer123',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            {
                'username': 'janesmith',
                'email': 'customer2@gurumisha.com',
                'password': 'customer123',
                'first_name': 'Jane',
                'last_name': 'Smith'
            },
            {
                'username': 'michaeljohnson',
                'email': 'customer3@gurumisha.com',
                'password': 'customer123',
                'first_name': 'Michael',
                'last_name': 'Johnson'
            }
        ]

        for customer_data in customers_data:
            user, created = User.objects.get_or_create(
                username=customer_data['username'],
                defaults={
                    'email': customer_data['email'],
                    'role': 'customer',
                    'is_verified': True,
                    'is_email_verified': True,
                    'first_name': customer_data['first_name'],
                    'last_name': customer_data['last_name']
                }
            )

            if created:
                user.set_password(customer_data['password'])
                user.save()
                self.stdout.write(f'✅ Created customer user: {customer_data["username"]}')
            else:
                # Update existing user to ensure verified status
                user.is_verified = True
                user.is_email_verified = True
                user.save()
                self.stdout.write(f'✅ Updated customer user: {customer_data["username"]}')

    def create_additional_test_accounts(self):
        """Create additional test accounts"""
        additional_accounts = [
            {
                'username': 'genixailabs',
                'email': 'genixailabs@gmail.com',
                'password': 'TestPassword123!',
                'first_name': 'Genix',
                'last_name': 'AI Labs',
                'role': 'customer'
            },
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'testpass123',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'customer'
            },
            {
                'username': 'tokenuser',
                'email': 'token@example.com',
                'password': 'testpassword123',
                'first_name': 'Token',
                'last_name': 'User',
                'role': 'customer'
            }
        ]

        for account_data in additional_accounts:
            user, created = User.objects.get_or_create(
                username=account_data['username'],
                defaults={
                    'email': account_data['email'],
                    'role': account_data['role'],
                    'is_verified': True,
                    'is_email_verified': True,
                    'first_name': account_data['first_name'],
                    'last_name': account_data['last_name']
                }
            )

            if created:
                user.set_password(account_data['password'])
                user.save()
                self.stdout.write(f'✅ Created additional test user: {account_data["username"]}')
            else:
                # Update existing user to ensure verified status
                user.is_verified = True
                user.is_email_verified = True
                user.save()
                self.stdout.write(f'✅ Updated additional test user: {account_data["username"]}')

    def display_credentials(self):
        """Display all created credentials"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('AUTHENTICATION TEST ACCOUNTS CREATED'))
        self.stdout.write('='*60)

        self.stdout.write('\n🔑 ADMIN ACCOUNT:')
        self.stdout.write('   Username: admin')
        self.stdout.write('   Email: admin@gurumisha.com')
        self.stdout.write('   Password: admin123')
        self.stdout.write('   Role: Admin (Superuser)')

        self.stdout.write('\n🏢 VENDOR ACCOUNTS:')
        vendors = [
            ('tokyomotors', 'vendor1@gurumisha.com', 'Tokyo Motors Kenya'),
            ('nairobiparts', 'vendor2@gurumisha.com', 'Nairobi Auto Parts'),
            ('mombasacars', 'vendor3@gurumisha.com', 'Mombasa Car Dealers')
        ]
        for username, email, company in vendors:
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: vendor123')
            self.stdout.write(f'   Company: {company}')
            self.stdout.write('')

        self.stdout.write('👥 CUSTOMER ACCOUNTS:')
        customers = [
            ('johndoe', 'customer1@gurumisha.com', 'John Doe'),
            ('janesmith', 'customer2@gurumisha.com', 'Jane Smith'),
            ('michaeljohnson', 'customer3@gurumisha.com', 'Michael Johnson')
        ]
        for username, email, name in customers:
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: customer123')
            self.stdout.write(f'   Name: {name}')
            self.stdout.write('')

        self.stdout.write('🧪 ADDITIONAL TEST ACCOUNTS:')
        self.stdout.write('   Username: genixailabs | Email: genixailabs@gmail.com | Password: TestPassword123!')
        self.stdout.write('   Username: testuser | Email: testuser@example.com | Password: testpass123')
        self.stdout.write('   Username: tokenuser | Email: token@example.com | Password: testpassword123')

        self.stdout.write('\n✅ All accounts are VERIFIED and ready for testing!')
        self.stdout.write('✅ All vendor accounts are APPROVED!')
        self.stdout.write('✅ Admin account has superuser privileges!')
        self.stdout.write('='*60)
