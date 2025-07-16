"""
Management command to populate spare parts test data
Usage: python manage.py populate_spare_parts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

from core.models import (
    SparePart, SparePartCategory, Supplier, Vendor, CarBrand, CarModel,
    StockMovement
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate spare parts test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of spare parts to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing spare parts data before populating'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_data = options['clear']

        if clear_data:
            self.stdout.write('Clearing existing spare parts data...')
            SparePart.objects.all().delete()
            SparePartCategory.objects.all().delete()
            Supplier.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared successfully'))

        self.stdout.write(f'Creating {count} spare parts...')

        # Create categories
        categories = self.create_categories()
        
        # Create suppliers
        suppliers = self.create_suppliers()
        
        # Get or create vendors
        vendors = self.get_or_create_vendors()
        
        # Get car brands and models
        car_brands = list(CarBrand.objects.all())
        
        # Create spare parts
        self.create_spare_parts(count, categories, suppliers, vendors, car_brands)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} spare parts')
        )

    def create_categories(self):
        """Create spare part categories"""
        category_data = [
            {
                'name': 'Engine Parts',
                'description': 'Engine components and accessories',
                'icon': 'fa-cogs'
            },
            {
                'name': 'Brake System',
                'description': 'Brake pads, discs, and brake components',
                'icon': 'fa-stop-circle'
            },
            {
                'name': 'Suspension',
                'description': 'Suspension components and shock absorbers',
                'icon': 'fa-car'
            },
            {
                'name': 'Electrical',
                'description': 'Electrical components and wiring',
                'icon': 'fa-bolt'
            },
            {
                'name': 'Body Parts',
                'description': 'Body panels and exterior components',
                'icon': 'fa-car-side'
            },
            {
                'name': 'Filters',
                'description': 'Air, oil, and fuel filters',
                'icon': 'fa-filter'
            },
            {
                'name': 'Transmission',
                'description': 'Transmission and drivetrain components',
                'icon': 'fa-cog'
            },
            {
                'name': 'Cooling System',
                'description': 'Radiators, hoses, and cooling components',
                'icon': 'fa-thermometer-half'
            },
            {
                'name': 'Exhaust System',
                'description': 'Exhaust pipes, mufflers, and catalytic converters',
                'icon': 'fa-wind'
            },
            {
                'name': 'Interior',
                'description': 'Interior components and accessories',
                'icon': 'fa-chair'
            }
        ]

        categories = []
        for data in category_data:
            category, created = SparePartCategory.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'icon': data['icon'],
                    'is_active': True
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')

        return categories

    def create_suppliers(self):
        """Create suppliers"""
        supplier_data = [
            {
                'name': 'AutoParts Kenya Ltd',
                'contact_person': 'John Kamau',
                'email': 'info@autopartskenya.com',
                'phone': '+254700123456',
                'address': 'Industrial Area, Nairobi',
                'rating': 4.5
            },
            {
                'name': 'Genuine Parts Suppliers',
                'contact_person': 'Mary Wanjiku',
                'email': 'sales@genuineparts.co.ke',
                'phone': '+254701234567',
                'address': 'Mombasa Road, Nairobi',
                'rating': 4.8
            },
            {
                'name': 'Motor Spares International',
                'contact_person': 'David Ochieng',
                'email': 'orders@motorspares.com',
                'phone': '+254702345678',
                'address': 'Thika Road, Nairobi',
                'rating': 4.2
            },
            {
                'name': 'Quality Auto Components',
                'contact_person': 'Grace Muthoni',
                'email': 'info@qualityauto.co.ke',
                'phone': '+254703456789',
                'address': 'Westlands, Nairobi',
                'rating': 4.6
            },
            {
                'name': 'East Africa Motors Supply',
                'contact_person': 'Peter Kiprotich',
                'email': 'supply@eamotors.com',
                'phone': '+254704567890',
                'address': 'Eldoret, Kenya',
                'rating': 4.3
            }
        ]

        suppliers = []
        for data in supplier_data:
            supplier, created = Supplier.objects.get_or_create(
                name=data['name'],
                defaults={
                    'contact_person': data['contact_person'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'rating': data['rating'],
                    'is_active': True
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')

        return suppliers

    def get_or_create_vendors(self):
        """Get existing vendors or create test vendors"""
        vendors = list(Vendor.objects.filter(is_approved=True))
        
        if not vendors:
            # Create test vendor users
            vendor_data = [
                {
                    'email': 'vendor1@gurumisha.com',
                    'first_name': 'James',
                    'last_name': 'Mwangi',
                    'company_name': 'Mwangi Auto Parts',
                    'business_registration': 'BRN001234',
                    'location': 'Nairobi'
                },
                {
                    'email': 'vendor2@gurumisha.com',
                    'first_name': 'Sarah',
                    'last_name': 'Njeri',
                    'company_name': 'Njeri Motor Spares',
                    'business_registration': 'BRN005678',
                    'location': 'Mombasa'
                }
            ]
            
            for data in vendor_data:
                user, created = User.objects.get_or_create(
                    email=data['email'],
                    defaults={
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'role': 'vendor',
                        'is_active': True,
                        'email_verified': True
                    }
                )
                
                if created:
                    user.set_password('testpass123')
                    user.save()
                
                vendor, vendor_created = Vendor.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': data['company_name'],
                        'business_registration': data['business_registration'],
                        'location': data['location'],
                        'is_active': True
                    }
                )
                
                vendors.append(vendor)
                if vendor_created:
                    self.stdout.write(f'Created vendor: {vendor.company_name}')

        return vendors

    def create_spare_parts(self, count, categories, suppliers, vendors, car_brands):
        """Create spare parts"""
        part_names = [
            'Engine Oil Filter', 'Air Filter', 'Fuel Filter', 'Brake Pads Front',
            'Brake Pads Rear', 'Brake Disc Front', 'Brake Disc Rear', 'Shock Absorber',
            'Strut Mount', 'Ball Joint', 'Tie Rod End', 'CV Joint', 'Spark Plug',
            'Ignition Coil', 'Alternator', 'Starter Motor', 'Battery', 'Radiator',
            'Water Pump', 'Thermostat', 'Timing Belt', 'Serpentine Belt', 'Clutch Kit',
            'Clutch Disc', 'Pressure Plate', 'Release Bearing', 'Exhaust Pipe',
            'Muffler', 'Catalytic Converter', 'Oxygen Sensor', 'Mass Air Flow Sensor',
            'Throttle Body', 'Fuel Injector', 'Fuel Pump', 'Power Steering Pump',
            'Steering Rack', 'Control Arm', 'Sway Bar Link', 'Wheel Bearing',
            'Hub Assembly', 'Caliper', 'Master Cylinder', 'Brake Booster',
            'Headlight', 'Tail Light', 'Turn Signal', 'Fog Light', 'Mirror',
            'Door Handle', 'Window Regulator', 'Wiper Blade', 'Cabin Filter'
        ]

        conditions = ['new', 'used', 'refurbished']
        
        for i in range(count):
            part_name = random.choice(part_names)
            category = random.choice(categories)
            supplier = random.choice(suppliers) if random.choice([True, False]) else None
            vendor = random.choice(vendors)
            
            # Generate realistic pricing
            base_price = random.uniform(500, 15000)
            cost_price = base_price * random.uniform(0.6, 0.8)
            discount_price = base_price * random.uniform(0.85, 0.95) if random.choice([True, False]) else None
            
            # Generate stock levels
            stock_quantity = random.randint(0, 100)
            minimum_stock = random.randint(5, 20)
            
            spare_part = SparePart.objects.create(
                vendor=vendor,
                name=f"{part_name} - {vendor.company_name[:10]}",
                sku=f"SP{i+1:04d}",
                part_number=f"PN{random.randint(10000, 99999)}",
                category_new=category,
                supplier=supplier,
                description=f"High quality {part_name.lower()} for various vehicle models. "
                           f"Compatible with multiple brands and models.",
                condition=random.choice(conditions),
                price=Decimal(str(round(base_price, 2))),
                cost_price=Decimal(str(round(cost_price, 2))),
                discount_price=Decimal(str(round(discount_price, 2))) if discount_price else None,
                stock_quantity=stock_quantity,
                minimum_stock=minimum_stock,
                maximum_stock=minimum_stock * 5,
                reorder_point=minimum_stock + 5,
                reorder_quantity=minimum_stock * 2,
                warehouse_location=f"A{random.randint(1, 10)}-{random.randint(1, 20)}",
                weight=Decimal(str(round(random.uniform(0.1, 10.0), 2))),
                dimensions=f"{random.randint(10, 50)}x{random.randint(10, 50)}x{random.randint(5, 30)}",
                year_from=random.randint(2000, 2015),
                year_to=random.randint(2016, 2024),
                is_available=True,
                is_featured=random.choice([True, False])
            )
            
            # Add compatible brands
            if car_brands:
                compatible_brands = random.sample(
                    car_brands, 
                    min(random.randint(1, 3), len(car_brands))
                )
                spare_part.compatible_brands.set(compatible_brands)
            
            # Create initial stock movement
            StockMovement.objects.create(
                spare_part=spare_part,
                movement_type='in',
                reason='initial',
                quantity=stock_quantity,
                quantity_before=0,
                quantity_after=stock_quantity,
                notes=f'Initial stock for {spare_part.name}',
                created_by=vendor.user
            )
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i + 1} spare parts...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} spare parts with stock movements')
        )
