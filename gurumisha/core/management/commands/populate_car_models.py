"""
Management command to populate car models with hardcoded data
Usage: python manage.py populate_car_models
"""

from django.core.management.base import BaseCommand
from core.models import CarBrand, CarModel

class Command(BaseCommand):
    help = 'Populate car models with hardcoded data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing car models before populating'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing car models...')
            CarModel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing car models'))

        self.stdout.write('Populating car models...')
        
        # Ensure brands exist first
        self.create_brands()
        
        # Create comprehensive car models
        self.create_car_models()
        
        self.stdout.write(self.style.SUCCESS('✓ Car models populated successfully!'))

    def create_brands(self):
        """Create car brands if they don't exist"""
        brands_data = [
            {'name': 'Toyota', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Honda', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Nissan', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Mercedes-Benz', 'country_of_origin': 'Germany', 'is_premium': True},
            {'name': 'BMW', 'country_of_origin': 'Germany', 'is_premium': True},
            {'name': 'Audi', 'country_of_origin': 'Germany', 'is_premium': True},
            {'name': 'Volkswagen', 'country_of_origin': 'Germany', 'is_premium': False},
            {'name': 'Ford', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Chevrolet', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Hyundai', 'country_of_origin': 'South Korea', 'is_premium': False},
            {'name': 'Kia', 'country_of_origin': 'South Korea', 'is_premium': False},
            {'name': 'Mazda', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Subaru', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Mitsubishi', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Lexus', 'country_of_origin': 'Japan', 'is_premium': True},
            {'name': 'Infiniti', 'country_of_origin': 'Japan', 'is_premium': True},
            {'name': 'Acura', 'country_of_origin': 'Japan', 'is_premium': True},
            {'name': 'Volvo', 'country_of_origin': 'Sweden', 'is_premium': True},
            {'name': 'Jaguar', 'country_of_origin': 'UK', 'is_premium': True},
            {'name': 'Land Rover', 'country_of_origin': 'UK', 'is_premium': True},
        ]
        
        for brand_data in brands_data:
            brand, created = CarBrand.objects.get_or_create(
                name=brand_data['name'],
                defaults={
                    'country_of_origin': brand_data['country_of_origin'],
                    'is_premium': brand_data['is_premium'],
                    'is_active': True,
                    'display_order': 0
                }
            )
            if created:
                self.stdout.write(f'✓ Created brand: {brand.name}')

    def create_car_models(self):
        """Create comprehensive car models"""
        models_data = {
            'Toyota': [
                {'name': 'Camry', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Corolla', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'RAV4', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Highlander', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Prius', 'body_type': 'hatchback', 'is_popular': True},
                {'name': 'Sienna', 'body_type': 'van', 'is_popular': False},
                {'name': 'Tacoma', 'body_type': 'pickup', 'is_popular': True},
                {'name': 'Tundra', 'body_type': 'pickup', 'is_popular': False},
                {'name': 'Avalon', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Venza', 'body_type': 'crossover', 'is_popular': False},
            ],
            'Honda': [
                {'name': 'Civic', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Accord', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'CR-V', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Pilot', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Fit', 'body_type': 'hatchback', 'is_popular': False},
                {'name': 'HR-V', 'body_type': 'crossover', 'is_popular': True},
                {'name': 'Odyssey', 'body_type': 'van', 'is_popular': False},
                {'name': 'Ridgeline', 'body_type': 'pickup', 'is_popular': False},
                {'name': 'Insight', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Passport', 'body_type': 'suv', 'is_popular': False},
            ],
            'Nissan': [
                {'name': 'Altima', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Sentra', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Rogue', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Murano', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Pathfinder', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Frontier', 'body_type': 'pickup', 'is_popular': False},
                {'name': 'Titan', 'body_type': 'pickup', 'is_popular': False},
                {'name': 'Versa', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Kicks', 'body_type': 'crossover', 'is_popular': False},
                {'name': 'Armada', 'body_type': 'suv', 'is_popular': False},
            ],
            'Mercedes-Benz': [
                {'name': 'C-Class', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'E-Class', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'S-Class', 'body_type': 'luxury', 'is_popular': True},
                {'name': 'GLC', 'body_type': 'suv', 'is_popular': True},
                {'name': 'GLE', 'body_type': 'suv', 'is_popular': True},
                {'name': 'GLS', 'body_type': 'suv', 'is_popular': False},
                {'name': 'A-Class', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'CLA', 'body_type': 'coupe', 'is_popular': False},
                {'name': 'CLS', 'body_type': 'coupe', 'is_popular': False},
                {'name': 'G-Class', 'body_type': 'suv', 'is_popular': True},
            ],
            'BMW': [
                {'name': '3 Series', 'body_type': 'sedan', 'is_popular': True},
                {'name': '5 Series', 'body_type': 'sedan', 'is_popular': True},
                {'name': '7 Series', 'body_type': 'luxury', 'is_popular': False},
                {'name': 'X3', 'body_type': 'suv', 'is_popular': True},
                {'name': 'X5', 'body_type': 'suv', 'is_popular': True},
                {'name': 'X7', 'body_type': 'suv', 'is_popular': False},
                {'name': '1 Series', 'body_type': 'hatchback', 'is_popular': False},
                {'name': '4 Series', 'body_type': 'coupe', 'is_popular': False},
                {'name': 'X1', 'body_type': 'crossover', 'is_popular': True},
                {'name': 'X6', 'body_type': 'suv', 'is_popular': False},
            ],
        }
        
        # Continue with more brands...
        models_data.update({
            'Audi': [
                {'name': 'A3', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'A4', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'A6', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Q3', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Q5', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Q7', 'body_type': 'suv', 'is_popular': False},
                {'name': 'A8', 'body_type': 'luxury', 'is_popular': False},
                {'name': 'TT', 'body_type': 'sports', 'is_popular': False},
            ],
            'Ford': [
                {'name': 'F-150', 'body_type': 'pickup', 'is_popular': True},
                {'name': 'Escape', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Explorer', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Fusion', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Focus', 'body_type': 'hatchback', 'is_popular': False},
                {'name': 'Mustang', 'body_type': 'sports', 'is_popular': True},
                {'name': 'Edge', 'body_type': 'suv', 'is_popular': False},
                {'name': 'Expedition', 'body_type': 'suv', 'is_popular': False},
            ],
            'Hyundai': [
                {'name': 'Elantra', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Sonata', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Tucson', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Santa Fe', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Accent', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Kona', 'body_type': 'crossover', 'is_popular': True},
                {'name': 'Palisade', 'body_type': 'suv', 'is_popular': False},
                {'name': 'Veloster', 'body_type': 'hatchback', 'is_popular': False},
            ],
            'Kia': [
                {'name': 'Forte', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Optima', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Sportage', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Sorento', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Rio', 'body_type': 'sedan', 'is_popular': False},
                {'name': 'Soul', 'body_type': 'crossover', 'is_popular': True},
                {'name': 'Telluride', 'body_type': 'suv', 'is_popular': True},
                {'name': 'Stinger', 'body_type': 'sedan', 'is_popular': False},
            ],
            'Mazda': [
                {'name': 'Mazda3', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'Mazda6', 'body_type': 'sedan', 'is_popular': True},
                {'name': 'CX-5', 'body_type': 'suv', 'is_popular': True},
                {'name': 'CX-9', 'body_type': 'suv', 'is_popular': False},
                {'name': 'CX-3', 'body_type': 'crossover', 'is_popular': False},
                {'name': 'MX-5 Miata', 'body_type': 'convertible', 'is_popular': True},
                {'name': 'CX-30', 'body_type': 'crossover', 'is_popular': True},
            ],
        })
        
        for brand_name, models in models_data.items():
            try:
                brand = CarBrand.objects.get(name=brand_name)
                for model_data in models:
                    model, created = CarModel.objects.get_or_create(
                        brand=brand,
                        name=model_data['name'],
                        defaults={
                            'body_type': model_data['body_type'],
                            'is_popular': model_data['is_popular'],
                            'is_active': True,
                        }
                    )
                    if created:
                        self.stdout.write(f'✓ Created model: {brand.name} {model.name}')
            except CarBrand.DoesNotExist:
                self.stdout.write(f'⚠ Brand {brand_name} not found, skipping models')
