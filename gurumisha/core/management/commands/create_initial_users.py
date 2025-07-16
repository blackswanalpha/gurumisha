from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Vendor

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial users: admin, vendor, and customer'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating initial users...'))
        
        # Create Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gurumisha.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_email_verified': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created admin user: {admin_user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Admin user already exists: {admin_user.username}'))

        # Create Customer User
        customer_user, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@gurumisha.com',
                'first_name': 'John',
                'last_name': 'Customer',
                'role': 'customer',
                'is_active': True,
                'is_email_verified': True,
                'phone': '+254712345678',
                'city': 'Nairobi'
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created customer user: {customer_user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Customer user already exists: {customer_user.username}'))

        # Create Vendor User
        vendor_user, created = User.objects.get_or_create(
            username='vendor',
            defaults={
                'email': 'vendor@gurumisha.com',
                'first_name': 'Jane',
                'last_name': 'Vendor',
                'role': 'vendor',
                'is_active': True,
                'is_email_verified': True,
                'phone': '+254787654321',
                'city': 'Mombasa'
            }
        )
        if created:
            vendor_user.set_password('vendor123')
            vendor_user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created vendor user: {vendor_user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Vendor user already exists: {vendor_user.username}'))

        # Create Vendor Profile for the vendor user
        vendor_profile, created = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                'company_name': 'Gurumisha Motors Ltd',
                'business_license': 'BRN123456',
                'business_type': 'dealership',
                'year_established': 2019,
                'physical_address': '123 Moi Avenue, Mombasa',
                'business_phone': '+254787654321',
                'business_email': 'vendor@gurumisha.com',
                'website': 'https://gurumishamotors.com',
                'description': 'Leading car dealership in Mombasa specializing in quality vehicles',
                'is_approved': True,
                'verification_status': 'verified'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created vendor profile: {vendor_profile.company_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Vendor profile already exists: {vendor_profile.company_name}'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Total users created: {User.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nUsers:'))
        for user in User.objects.all():
            self.stdout.write(self.style.SUCCESS(f'  - {user.username} ({user.role}) - {user.email}'))
        self.stdout.write(self.style.SUCCESS(f'\nTotal vendors: {Vendor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\nLogin Credentials:'))
        self.stdout.write(self.style.SUCCESS('  Admin:    username=admin,    password=admin123'))
        self.stdout.write(self.style.SUCCESS('  Vendor:   username=vendor,   password=vendor123'))
        self.stdout.write(self.style.SUCCESS('  Customer: username=customer, password=customer123'))
        self.stdout.write(self.style.SUCCESS('='*50))
