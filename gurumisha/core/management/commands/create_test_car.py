"""
Management command to create a test car with enhanced image gallery
"""
import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from core.models import Car, CarBrand, CarModel, CarImage, VehicleCondition, Vendor, User


class Command(BaseCommand):
    help = 'Create a test car with enhanced image gallery using product images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing test car before creating new one',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test car with enhanced image gallery...'))

        # Delete existing test car if requested
        if options['delete_existing']:
            Car.objects.filter(title__icontains='Test Gallery Car').delete()
            self.stdout.write(self.style.WARNING('Deleted existing test cars'))

        # Get or create required objects
        brand, created = CarBrand.objects.get_or_create(
            name='Toyota',
            defaults={'description': 'Japanese automotive manufacturer'}
        )
        if created:
            self.stdout.write(f'Created brand: {brand.name}')

        model, created = CarModel.objects.get_or_create(
            brand=brand,
            name='Camry',
            defaults={'description': 'Mid-size sedan'}
        )
        if created:
            self.stdout.write(f'Created model: {model.name}')

        condition, created = VehicleCondition.objects.get_or_create(
            name='Excellent',
            defaults={'description': 'Vehicle in excellent condition'}
        )
        if created:
            self.stdout.write(f'Created condition: {condition.name}')

        # Get or create a vendor user
        vendor_user, created = User.objects.get_or_create(
            username='test_vendor',
            defaults={
                'email': 'vendor@test.com',
                'first_name': 'Test',
                'last_name': 'Vendor',
                'role': 'vendor'
            }
        )
        if created:
            vendor_user.set_password('testpass123')
            vendor_user.save()
            self.stdout.write(f'Created vendor user: {vendor_user.username}')

        vendor, created = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                'company_name': 'Test Motors Ltd',
                'business_phone': '+254700000000',
                'physical_address': 'Nairobi, Kenya',
                'is_approved': True,
                'verification_status': 'verified',
                'business_type': 'dealership',
                'description': 'Premium automotive dealership specializing in quality vehicles'
            }
        )
        if created:
            self.stdout.write(f'Created vendor: {vendor.company_name}')

        # Create the test car
        car = Car.objects.create(
            title='Test Gallery Car - 2023 Toyota Camry Hybrid',
            brand=brand,
            model=model,
            condition=condition,
            year=2023,
            price=3500000,  # 3.5M KES
            mileage=15000,
            fuel_type='hybrid',
            transmission='automatic',
            color='Pearl White',
            engine_size='2.5L',
            description='''
This is a comprehensive test car created to demonstrate the enhanced image gallery functionality 
of the Gurumisha platform. This 2023 Toyota Camry Hybrid represents the perfect blend of 
efficiency, comfort, and reliability.

Key Features:
- Hybrid powertrain for exceptional fuel economy
- Advanced safety features including Toyota Safety Sense 2.0
- Premium interior with leather-appointed seating
- Dual-zone automatic climate control
- 9-inch touchscreen infotainment system
- Apple CarPlay and Android Auto compatibility
- LED headlights and taillights
- Alloy wheels with low-profile tires

This vehicle has been meticulously maintained with full service history. Perfect for both 
city driving and long-distance travel. The hybrid system provides excellent fuel economy 
while maintaining smooth performance.

Contact us today to schedule a test drive and experience this exceptional vehicle firsthand.
            '''.strip(),
            features='Hybrid Engine, Leather Seats, Navigation System, Backup Camera, Bluetooth, USB Ports, Keyless Entry, Push Button Start, Cruise Control, Lane Departure Warning, Automatic Emergency Braking, Blind Spot Monitoring',
            listing_type='standard',
            negotiable=True,
            area='Westlands',
            city='Nairobi',
            country='Kenya',
            vendor=vendor,
            status='available',
            is_approved=True,
            is_featured=True
        )

        self.stdout.write(f'Created test car: {car.title}')

        # Copy and set up images
        static_images_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'products-images')
        media_cars_path = os.path.join(settings.MEDIA_ROOT, 'cars')
        media_gallery_path = os.path.join(settings.MEDIA_ROOT, 'cars', 'gallery')

        # Ensure media directories exist
        os.makedirs(media_cars_path, exist_ok=True)
        os.makedirs(media_gallery_path, exist_ok=True)

        # Set main image (p1.jpg)
        main_image_src = os.path.join(static_images_path, 'p1.jpg')
        main_image_dest = os.path.join(media_cars_path, 'test_car_main.jpg')
        
        if os.path.exists(main_image_src):
            shutil.copy2(main_image_src, main_image_dest)
            with open(main_image_dest, 'rb') as f:
                car.main_image.save('test_car_main.jpg', File(f), save=True)
            self.stdout.write('Set main image (p1.jpg)')
        else:
            self.stdout.write(self.style.ERROR(f'Main image not found: {main_image_src}'))

        # Create gallery images (p2.jpg, p3.jpg, p4.jpg)
        gallery_images = [
            {'file': 'p2.jpg', 'caption': 'Interior View - Premium leather seats and modern dashboard', 'is_primary': True},
            {'file': 'p3.jpg', 'caption': 'Side Profile - Elegant design with aerodynamic styling', 'is_primary': False},
            {'file': 'p4.jpg', 'caption': 'Rear View - LED taillights and sporty rear design', 'is_primary': False},
        ]

        for i, img_data in enumerate(gallery_images):
            src_path = os.path.join(static_images_path, img_data['file'])
            dest_filename = f'test_car_gallery_{i+1}.jpg'
            dest_path = os.path.join(media_gallery_path, dest_filename)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                
                with open(dest_path, 'rb') as f:
                    car_image = CarImage.objects.create(
                        car=car,
                        caption=img_data['caption'],
                        order=i + 1,
                        is_primary=img_data['is_primary']
                    )
                    car_image.image.save(dest_filename, File(f), save=True)
                
                self.stdout.write(f'Created gallery image {i+1}: {img_data["file"]} - {img_data["caption"][:50]}...')
            else:
                self.stdout.write(self.style.ERROR(f'Gallery image not found: {src_path}'))

        # Display summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('TEST CAR CREATED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Car ID: {car.id}')
        self.stdout.write(f'Title: {car.title}')
        self.stdout.write(f'Price: KES {car.price:,}')
        self.stdout.write(f'Main Image: {"✓" if car.main_image else "✗"}')
        self.stdout.write(f'Gallery Images: {car.images.count()}')
        self.stdout.write(f'Primary Gallery Image: {"✓" if car.images.filter(is_primary=True).exists() else "✗"}')
        self.stdout.write(f'Car Detail URL: /cars/{car.id}/')
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Display gallery images info
        if car.images.exists():
            self.stdout.write('\nGallery Images:')
            for img in car.images.all().order_by('order'):
                primary_marker = " [PRIMARY]" if img.is_primary else ""
                self.stdout.write(f'  {img.order}. {img.caption[:50]}...{primary_marker}')
        
        self.stdout.write(f'\nYou can now visit the car detail page to see the enhanced image gallery in action!')
        self.stdout.write(f'URL: http://localhost:8000/cars/{car.id}/')
