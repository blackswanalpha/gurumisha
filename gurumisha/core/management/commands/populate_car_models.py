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
            {'name': 'Jeep', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Peugeot', 'country_of_origin': 'France', 'is_premium': False},
            {'name': 'Renault', 'country_of_origin': 'France', 'is_premium': False},
            {'name': 'Porsche', 'country_of_origin': 'Germany', 'is_premium': True},
            {'name': 'Cadillac', 'country_of_origin': 'USA', 'is_premium': True},
            {'name': 'Lincoln', 'country_of_origin': 'USA', 'is_premium': True},
            {'name': 'Genesis', 'country_of_origin': 'South Korea', 'is_premium': True},
            # Additional 40 brands for comprehensive coverage
            {'name': 'Alfa Romeo', 'country_of_origin': 'Italy', 'is_premium': True},
            {'name': 'Aston Martin', 'country_of_origin': 'UK', 'is_premium': True},
            {'name': 'Bentley', 'country_of_origin': 'UK', 'is_premium': True},
            {'name': 'Bugatti', 'country_of_origin': 'France', 'is_premium': True},
            {'name': 'Buick', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Chery', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'Chrysler', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Citroen', 'country_of_origin': 'France', 'is_premium': False},
            {'name': 'Dacia', 'country_of_origin': 'Romania', 'is_premium': False},
            {'name': 'Daewoo', 'country_of_origin': 'South Korea', 'is_premium': False},
            {'name': 'Daihatsu', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Dodge', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Ferrari', 'country_of_origin': 'Italy', 'is_premium': True},
            {'name': 'Fiat', 'country_of_origin': 'Italy', 'is_premium': False},
            {'name': 'Geely', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'GMC', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Great Wall', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'Haval', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'Hummer', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Isuzu', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Iveco', 'country_of_origin': 'Italy', 'is_premium': False},
            {'name': 'Lamborghini', 'country_of_origin': 'Italy', 'is_premium': True},
            {'name': 'Lancia', 'country_of_origin': 'Italy', 'is_premium': False},
            {'name': 'Mahindra', 'country_of_origin': 'India', 'is_premium': False},
            {'name': 'Maserati', 'country_of_origin': 'Italy', 'is_premium': True},
            {'name': 'McLaren', 'country_of_origin': 'UK', 'is_premium': True},
            {'name': 'Mini', 'country_of_origin': 'UK', 'is_premium': False},
            {'name': 'Opel', 'country_of_origin': 'Germany', 'is_premium': False},
            {'name': 'Proton', 'country_of_origin': 'Malaysia', 'is_premium': False},
            {'name': 'Ram', 'country_of_origin': 'USA', 'is_premium': False},
            {'name': 'Rolls Royce', 'country_of_origin': 'UK', 'is_premium': True},
            {'name': 'Saab', 'country_of_origin': 'Sweden', 'is_premium': False},
            {'name': 'Seat', 'country_of_origin': 'Spain', 'is_premium': False},
            {'name': 'Skoda', 'country_of_origin': 'Czech Republic', 'is_premium': False},
            {'name': 'Smart', 'country_of_origin': 'Germany', 'is_premium': False},
            {'name': 'SsangYong', 'country_of_origin': 'South Korea', 'is_premium': False},
            {'name': 'Suzuki', 'country_of_origin': 'Japan', 'is_premium': False},
            {'name': 'Tata', 'country_of_origin': 'India', 'is_premium': False},
            {'name': 'Tesla', 'country_of_origin': 'USA', 'is_premium': True},
            {'name': 'BYD', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'Dongfeng', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'FAW', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'Foton', 'country_of_origin': 'China', 'is_premium': False},
            {'name': 'JAC', 'country_of_origin': 'China', 'is_premium': False},
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

        # Add 200 additional car models for comprehensive coverage
        additional_models = {
            # Fill empty brands with popular models
            'Acura': [
                {'name': 'TLX', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2015},
                {'name': 'MDX', 'body_type': 'suv', 'is_popular': True, 'year_start': 2001},
                {'name': 'RDX', 'body_type': 'suv', 'is_popular': True, 'year_start': 2007},
                {'name': 'ILX', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2013},
                {'name': 'NSX', 'body_type': 'sports', 'is_popular': False, 'year_start': 2016},
                {'name': 'TSX', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2004, 'year_end': 2014},
                {'name': 'RSX', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2002, 'year_end': 2006},
                {'name': 'Integra', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2022},
            ],
            'Infiniti': [
                {'name': 'Q50', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2014},
                {'name': 'Q60', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2017},
                {'name': 'QX50', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'QX60', 'body_type': 'suv', 'is_popular': True, 'year_start': 2013},
                {'name': 'QX80', 'body_type': 'suv', 'is_popular': False, 'year_start': 2014},
                {'name': 'G35', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2003, 'year_end': 2008},
                {'name': 'G37', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2008, 'year_end': 2013},
                {'name': 'FX35', 'body_type': 'suv', 'is_popular': False, 'year_start': 2003, 'year_end': 2012},
            ],
            'Jaguar': [
                {'name': 'XE', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2015},
                {'name': 'XF', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2008},
                {'name': 'XJ', 'body_type': 'luxury', 'is_popular': False, 'year_start': 1968},
                {'name': 'F-PACE', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'E-PACE', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'I-PACE', 'body_type': 'suv', 'is_popular': False, 'year_start': 2018},
                {'name': 'F-TYPE', 'body_type': 'sports', 'is_popular': True, 'year_start': 2014},
                {'name': 'XK', 'body_type': 'coupe', 'is_popular': False, 'year_start': 1996, 'year_end': 2014},
            ],
            'Lexus': [
                {'name': 'ES', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1989},
                {'name': 'IS', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1999},
                {'name': 'LS', 'body_type': 'luxury', 'is_popular': True, 'year_start': 1989},
                {'name': 'RX', 'body_type': 'suv', 'is_popular': True, 'year_start': 1998},
                {'name': 'GX', 'body_type': 'suv', 'is_popular': True, 'year_start': 2003},
                {'name': 'LX', 'body_type': 'suv', 'is_popular': False, 'year_start': 1996},
                {'name': 'NX', 'body_type': 'suv', 'is_popular': True, 'year_start': 2015},
                {'name': 'UX', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2019},
                {'name': 'LC', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2018},
                {'name': 'RC', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2015},
            ],
            'Subaru': [
                {'name': 'Outback', 'body_type': 'wagon', 'is_popular': True, 'year_start': 1995},
                {'name': 'Forester', 'body_type': 'suv', 'is_popular': True, 'year_start': 1997},
                {'name': 'Impreza', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1992},
                {'name': 'Legacy', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1989},
                {'name': 'Crosstrek', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2013},
                {'name': 'Ascent', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'WRX', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2002},
                {'name': 'BRZ', 'body_type': 'sports', 'is_popular': False, 'year_start': 2013},
            ],
            'Mitsubishi': [
                {'name': 'Outlander', 'body_type': 'suv', 'is_popular': True, 'year_start': 2003},
                {'name': 'Eclipse Cross', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2018},
                {'name': 'Mirage', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2014},
                {'name': 'Lancer', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1973, 'year_end': 2017},
                {'name': 'Pajero', 'body_type': 'suv', 'is_popular': True, 'year_start': 1982},
                {'name': 'ASX', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2010},
                {'name': 'L200', 'body_type': 'pickup', 'is_popular': True, 'year_start': 1978},
                {'name': 'Galant', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1969, 'year_end': 2012},
            ],
            'Volkswagen': [
                {'name': 'Golf', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1974},
                {'name': 'Jetta', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1979},
                {'name': 'Passat', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1973},
                {'name': 'Tiguan', 'body_type': 'suv', 'is_popular': True, 'year_start': 2007},
                {'name': 'Atlas', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'Polo', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1975},
                {'name': 'Touareg', 'body_type': 'suv', 'is_popular': False, 'year_start': 2003},
                {'name': 'Arteon', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2017},
                {'name': 'Beetle', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1938, 'year_end': 2019},
            ],
            'Chevrolet': [
                {'name': 'Malibu', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1964},
                {'name': 'Equinox', 'body_type': 'suv', 'is_popular': True, 'year_start': 2005},
                {'name': 'Tahoe', 'body_type': 'suv', 'is_popular': True, 'year_start': 1995},
                {'name': 'Silverado', 'body_type': 'pickup', 'is_popular': True, 'year_start': 1999},
                {'name': 'Camaro', 'body_type': 'sports', 'is_popular': True, 'year_start': 1967},
                {'name': 'Corvette', 'body_type': 'sports', 'is_popular': True, 'year_start': 1953},
                {'name': 'Traverse', 'body_type': 'suv', 'is_popular': True, 'year_start': 2009},
                {'name': 'Suburban', 'body_type': 'suv', 'is_popular': False, 'year_start': 1935},
                {'name': 'Cruze', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2009, 'year_end': 2019},
                {'name': 'Impala', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1958, 'year_end': 2020},
            ],
            'Peugeot': [
                {'name': '208', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2012},
                {'name': '308', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2007},
                {'name': '508', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2011},
                {'name': '3008', 'body_type': 'suv', 'is_popular': True, 'year_start': 2009},
                {'name': '5008', 'body_type': 'suv', 'is_popular': True, 'year_start': 2009},
                {'name': '2008', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2013},
                {'name': '206', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1998, 'year_end': 2012},
                {'name': '407', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2004, 'year_end': 2011},
            ],
            'Renault': [
                {'name': 'Clio', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1990},
                {'name': 'Megane', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1995},
                {'name': 'Kadjar', 'body_type': 'suv', 'is_popular': True, 'year_start': 2015},
                {'name': 'Captur', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2013},
                {'name': 'Koleos', 'body_type': 'suv', 'is_popular': True, 'year_start': 2008},
                {'name': 'Scenic', 'body_type': 'van', 'is_popular': False, 'year_start': 1996},
                {'name': 'Fluence', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2010, 'year_end': 2016},
                {'name': 'Duster', 'body_type': 'suv', 'is_popular': True, 'year_start': 2010},
            ],
            'Land Rover': [
                {'name': 'Range Rover', 'body_type': 'luxury', 'is_popular': True, 'year_start': 1970},
                {'name': 'Range Rover Sport', 'body_type': 'suv', 'is_popular': True, 'year_start': 2005},
                {'name': 'Range Rover Evoque', 'body_type': 'suv', 'is_popular': True, 'year_start': 2011},
                {'name': 'Discovery', 'body_type': 'suv', 'is_popular': True, 'year_start': 1989},
                {'name': 'Discovery Sport', 'body_type': 'suv', 'is_popular': True, 'year_start': 2015},
                {'name': 'Defender', 'body_type': 'suv', 'is_popular': True, 'year_start': 1983},
                {'name': 'Freelander', 'body_type': 'suv', 'is_popular': False, 'year_start': 1997, 'year_end': 2014},
                {'name': 'Velar', 'body_type': 'suv', 'is_popular': False, 'year_start': 2017},
            ],
            'Jeep': [
                {'name': 'Wrangler', 'body_type': 'suv', 'is_popular': True, 'year_start': 1987},
                {'name': 'Grand Cherokee', 'body_type': 'suv', 'is_popular': True, 'year_start': 1993},
                {'name': 'Cherokee', 'body_type': 'suv', 'is_popular': True, 'year_start': 1974},
                {'name': 'Compass', 'body_type': 'suv', 'is_popular': True, 'year_start': 2007},
                {'name': 'Renegade', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2015},
                {'name': 'Gladiator', 'body_type': 'pickup', 'is_popular': True, 'year_start': 2020},
                {'name': 'Patriot', 'body_type': 'suv', 'is_popular': False, 'year_start': 2007, 'year_end': 2017},
                {'name': 'Liberty', 'body_type': 'suv', 'is_popular': False, 'year_start': 2002, 'year_end': 2012},
            ],
            'Volvo': [
                {'name': 'XC90', 'body_type': 'suv', 'is_popular': True, 'year_start': 2003},
                {'name': 'XC60', 'body_type': 'suv', 'is_popular': True, 'year_start': 2008},
                {'name': 'XC40', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2018},
                {'name': 'S60', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2000},
                {'name': 'S90', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2016},
                {'name': 'V60', 'body_type': 'wagon', 'is_popular': False, 'year_start': 2010},
                {'name': 'V90', 'body_type': 'wagon', 'is_popular': False, 'year_start': 2016},
                {'name': 'S40', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1995, 'year_end': 2012},
            ],
        }

        # Add more models to existing brands for comprehensive coverage
        expanded_models = {
            'Toyota': [
                {'name': 'Land Cruiser', 'body_type': 'suv', 'is_popular': True, 'year_start': 1951},
                {'name': '4Runner', 'body_type': 'suv', 'is_popular': True, 'year_start': 1984},
                {'name': 'Sequoia', 'body_type': 'suv', 'is_popular': False, 'year_start': 2001},
                {'name': 'Yaris', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1999},
                {'name': 'C-HR', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2017},
                {'name': 'Supra', 'body_type': 'sports', 'is_popular': True, 'year_start': 2019},
                {'name': 'Celica', 'body_type': 'sports', 'is_popular': False, 'year_start': 1970, 'year_end': 2006},
                {'name': 'Matrix', 'body_type': 'wagon', 'is_popular': False, 'year_start': 2003, 'year_end': 2014},
            ],
            'Honda': [
                {'name': 'Element', 'body_type': 'suv', 'is_popular': False, 'year_start': 2003, 'year_end': 2011},
                {'name': 'S2000', 'body_type': 'convertible', 'is_popular': True, 'year_start': 1999, 'year_end': 2009},
                {'name': 'Prelude', 'body_type': 'coupe', 'is_popular': False, 'year_start': 1978, 'year_end': 2001},
                {'name': 'Del Sol', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1993, 'year_end': 1997},
            ],
            'BMW': [
                {'name': '2 Series', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2014},
                {'name': '8 Series', 'body_type': 'luxury', 'is_popular': False, 'year_start': 2019},
                {'name': 'X2', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2018},
                {'name': 'X4', 'body_type': 'suv', 'is_popular': False, 'year_start': 2014},
                {'name': 'Z4', 'body_type': 'convertible', 'is_popular': False, 'year_start': 2003},
                {'name': 'i3', 'body_type': 'electric', 'is_popular': False, 'year_start': 2013, 'year_end': 2022},
                {'name': 'i8', 'body_type': 'sports', 'is_popular': False, 'year_start': 2014, 'year_end': 2020},
            ],
            'Mercedes-Benz': [
                {'name': 'GLA', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2014},
                {'name': 'GLB', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'GLE Coupe', 'body_type': 'suv', 'is_popular': False, 'year_start': 2015},
                {'name': 'GLS Coupe', 'body_type': 'suv', 'is_popular': False, 'year_start': 2017},
                {'name': 'SL', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1954},
                {'name': 'SLK', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1996, 'year_end': 2016},
                {'name': 'AMG GT', 'body_type': 'sports', 'is_popular': False, 'year_start': 2015},
            ],
            'Audi': [
                {'name': 'Q8', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'Q2', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2016},
                {'name': 'A5', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2007},
                {'name': 'A7', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2010},
                {'name': 'R8', 'body_type': 'sports', 'is_popular': False, 'year_start': 2007},
                {'name': 'e-tron', 'body_type': 'electric', 'is_popular': True, 'year_start': 2019},
            ],
            'Ford': [
                {'name': 'Ranger', 'body_type': 'pickup', 'is_popular': True, 'year_start': 1983},
                {'name': 'Bronco', 'body_type': 'suv', 'is_popular': True, 'year_start': 2021},
                {'name': 'EcoSport', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2003},
                {'name': 'Fiesta', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1976},
                {'name': 'Taurus', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1986, 'year_end': 2019},
                {'name': 'Crown Victoria', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1992, 'year_end': 2011},
            ],
        }

        # Add more popular models and missing brands
        final_additions = {
            'Nissan': [
                {'name': 'Maxima', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1981},
                {'name': '370Z', 'body_type': 'sports', 'is_popular': True, 'year_start': 2009},
                {'name': 'GT-R', 'body_type': 'sports', 'is_popular': False, 'year_start': 2007},
                {'name': 'Juke', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2010},
                {'name': 'X-Trail', 'body_type': 'suv', 'is_popular': True, 'year_start': 2001},
            ],
            'Hyundai': [
                {'name': 'Genesis', 'body_type': 'luxury', 'is_popular': True, 'year_start': 2009},
                {'name': 'Azera', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2006},
                {'name': 'Santa Cruz', 'body_type': 'pickup', 'is_popular': True, 'year_start': 2022},
                {'name': 'Venue', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2020},
            ],
            'Kia': [
                {'name': 'Carnival', 'body_type': 'van', 'is_popular': True, 'year_start': 2022},
                {'name': 'Seltos', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2020},
                {'name': 'Niro', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2017},
                {'name': 'Cadenza', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2014},
            ],
            'Mazda': [
                {'name': 'CX-50', 'body_type': 'suv', 'is_popular': True, 'year_start': 2023},
                {'name': 'CX-90', 'body_type': 'suv', 'is_popular': True, 'year_start': 2024},
                {'name': 'RX-8', 'body_type': 'sports', 'is_popular': False, 'year_start': 2003, 'year_end': 2012},
                {'name': 'Tribute', 'body_type': 'suv', 'is_popular': False, 'year_start': 2001, 'year_end': 2011},
            ],
        }

        # Add some additional luxury and specialty brands if they exist
        luxury_additions = {
            'Porsche': [
                {'name': '911', 'body_type': 'sports', 'is_popular': True, 'year_start': 1963},
                {'name': 'Cayenne', 'body_type': 'suv', 'is_popular': True, 'year_start': 2003},
                {'name': 'Macan', 'body_type': 'suv', 'is_popular': True, 'year_start': 2014},
                {'name': 'Panamera', 'body_type': 'luxury', 'is_popular': False, 'year_start': 2010},
                {'name': 'Boxster', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1997},
                {'name': 'Cayman', 'body_type': 'sports', 'is_popular': False, 'year_start': 2006},
            ],
            'Cadillac': [
                {'name': 'Escalade', 'body_type': 'suv', 'is_popular': True, 'year_start': 1999},
                {'name': 'XT5', 'body_type': 'suv', 'is_popular': True, 'year_start': 2017},
                {'name': 'CT5', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2020},
                {'name': 'XT4', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2019},
                {'name': 'CTS', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2003, 'year_end': 2019},
                {'name': 'SRX', 'body_type': 'suv', 'is_popular': False, 'year_start': 2004, 'year_end': 2016},
            ],
            'Lincoln': [
                {'name': 'Navigator', 'body_type': 'suv', 'is_popular': True, 'year_start': 1998},
                {'name': 'Aviator', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'Corsair', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2020},
                {'name': 'Nautilus', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'Continental', 'body_type': 'luxury', 'is_popular': False, 'year_start': 2017, 'year_end': 2020},
            ],
            'Genesis': [
                {'name': 'G90', 'body_type': 'luxury', 'is_popular': True, 'year_start': 2017},
                {'name': 'G80', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2017},
                {'name': 'G70', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2019},
                {'name': 'GV70', 'body_type': 'suv', 'is_popular': True, 'year_start': 2022},
                {'name': 'GV80', 'body_type': 'suv', 'is_popular': True, 'year_start': 2021},
            ],
        }

        models_data.update(additional_models)
        models_data.update(expanded_models)
        models_data.update(final_additions)

        # Add 500 more models for comprehensive coverage
        massive_expansion = {
            # New brands with comprehensive models
            'Alfa Romeo': [
                {'name': 'Giulia', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2016},
                {'name': 'Giulietta', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2010},
                {'name': 'Stelvio', 'body_type': 'suv', 'is_popular': True, 'year_start': 2017},
                {'name': 'Tonale', 'body_type': 'suv', 'is_popular': True, 'year_start': 2022},
                {'name': '4C', 'body_type': 'sports', 'is_popular': False, 'year_start': 2013},
                {'name': 'MiTo', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2008, 'year_end': 2018},
                {'name': '159', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2005, 'year_end': 2011},
                {'name': 'Brera', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2005, 'year_end': 2010},
                {'name': 'Spider', 'body_type': 'convertible', 'is_popular': False, 'year_start': 2006, 'year_end': 2010},
                {'name': 'GT', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2003, 'year_end': 2010},
            ],
            'Tesla': [
                {'name': 'Model S', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2012},
                {'name': 'Model 3', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2017},
                {'name': 'Model X', 'body_type': 'suv', 'is_popular': True, 'year_start': 2015},
                {'name': 'Model Y', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'Cybertruck', 'body_type': 'pickup', 'is_popular': True, 'year_start': 2024},
                {'name': 'Roadster', 'body_type': 'sports', 'is_popular': False, 'year_start': 2008, 'year_end': 2012},
                {'name': 'Semi', 'body_type': 'truck', 'is_popular': False, 'year_start': 2024},
            ],
            'Ferrari': [
                {'name': '488 GTB', 'body_type': 'sports', 'is_popular': True, 'year_start': 2015},
                {'name': 'F8 Tributo', 'body_type': 'sports', 'is_popular': True, 'year_start': 2019},
                {'name': 'SF90 Stradale', 'body_type': 'sports', 'is_popular': True, 'year_start': 2019},
                {'name': 'Roma', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2020},
                {'name': 'Portofino', 'body_type': 'convertible', 'is_popular': True, 'year_start': 2017},
                {'name': '812 Superfast', 'body_type': 'sports', 'is_popular': False, 'year_start': 2017},
                {'name': 'LaFerrari', 'body_type': 'sports', 'is_popular': False, 'year_start': 2013, 'year_end': 2016},
                {'name': '458 Italia', 'body_type': 'sports', 'is_popular': False, 'year_start': 2009, 'year_end': 2015},
                {'name': 'California', 'body_type': 'convertible', 'is_popular': False, 'year_start': 2008, 'year_end': 2017},
                {'name': 'F12 Berlinetta', 'body_type': 'sports', 'is_popular': False, 'year_start': 2012, 'year_end': 2017},
            ],
            'Lamborghini': [
                {'name': 'Huracan', 'body_type': 'sports', 'is_popular': True, 'year_start': 2014},
                {'name': 'Aventador', 'body_type': 'sports', 'is_popular': True, 'year_start': 2011},
                {'name': 'Urus', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'Gallardo', 'body_type': 'sports', 'is_popular': False, 'year_start': 2003, 'year_end': 2013},
                {'name': 'Murcielago', 'body_type': 'sports', 'is_popular': False, 'year_start': 2001, 'year_end': 2010},
                {'name': 'Countach', 'body_type': 'sports', 'is_popular': False, 'year_start': 1974, 'year_end': 1990},
                {'name': 'Diablo', 'body_type': 'sports', 'is_popular': False, 'year_start': 1990, 'year_end': 2001},
            ],
            'Maserati': [
                {'name': 'Ghibli', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2013},
                {'name': 'Levante', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'Quattroporte', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2004},
                {'name': 'GranTurismo', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2007},
                {'name': 'GranCabrio', 'body_type': 'convertible', 'is_popular': False, 'year_start': 2010},
                {'name': 'MC20', 'body_type': 'sports', 'is_popular': False, 'year_start': 2020},
            ],
            'McLaren': [
                {'name': '720S', 'body_type': 'sports', 'is_popular': True, 'year_start': 2017},
                {'name': '570S', 'body_type': 'sports', 'is_popular': True, 'year_start': 2015},
                {'name': 'Artura', 'body_type': 'sports', 'is_popular': True, 'year_start': 2022},
                {'name': 'GT', 'body_type': 'sports', 'is_popular': True, 'year_start': 2019},
                {'name': '650S', 'body_type': 'sports', 'is_popular': False, 'year_start': 2014, 'year_end': 2017},
                {'name': 'P1', 'body_type': 'sports', 'is_popular': False, 'year_start': 2013, 'year_end': 2015},
                {'name': 'Senna', 'body_type': 'sports', 'is_popular': False, 'year_start': 2018, 'year_end': 2020},
            ],
            'Aston Martin': [
                {'name': 'DB11', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2016},
                {'name': 'Vantage', 'body_type': 'sports', 'is_popular': True, 'year_start': 2018},
                {'name': 'DBX', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'DBS', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2019},
                {'name': 'Rapide', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2010, 'year_end': 2020},
                {'name': 'Vanquish', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2012, 'year_end': 2018},
                {'name': 'DB9', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2004, 'year_end': 2016},
                {'name': 'Virage', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2011, 'year_end': 2012},
            ],
            'Bentley': [
                {'name': 'Continental GT', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2003},
                {'name': 'Bentayga', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'Flying Spur', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2005},
                {'name': 'Mulsanne', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2010, 'year_end': 2020},
                {'name': 'Arnage', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1998, 'year_end': 2009},
                {'name': 'Azure', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1995, 'year_end': 2009},
                {'name': 'Brooklands', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2008, 'year_end': 2011},
            ],
            'Rolls Royce': [
                {'name': 'Ghost', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2009},
                {'name': 'Phantom', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2003},
                {'name': 'Cullinan', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'Wraith', 'body_type': 'coupe', 'is_popular': True, 'year_start': 2013},
                {'name': 'Dawn', 'body_type': 'convertible', 'is_popular': True, 'year_start': 2015},
                {'name': 'Corniche', 'body_type': 'convertible', 'is_popular': False, 'year_start': 1971, 'year_end': 2002},
                {'name': 'Silver Seraph', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1998, 'year_end': 2002},
            ],
            'Mini': [
                {'name': 'Cooper', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2001},
                {'name': 'Countryman', 'body_type': 'suv', 'is_popular': True, 'year_start': 2010},
                {'name': 'Clubman', 'body_type': 'wagon', 'is_popular': True, 'year_start': 2007},
                {'name': 'Paceman', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2013, 'year_end': 2016},
                {'name': 'Roadster', 'body_type': 'convertible', 'is_popular': False, 'year_start': 2012, 'year_end': 2015},
                {'name': 'Coupe', 'body_type': 'coupe', 'is_popular': False, 'year_start': 2011, 'year_end': 2015},
                {'name': 'John Cooper Works', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2008},
            ],
            'Fiat': [
                {'name': '500', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2007},
                {'name': '500X', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2014},
                {'name': '500L', 'body_type': 'van', 'is_popular': True, 'year_start': 2012},
                {'name': 'Panda', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1980},
                {'name': 'Punto', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1993},
                {'name': 'Tipo', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2015},
                {'name': 'Bravo', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1995, 'year_end': 2014},
                {'name': 'Doblo', 'body_type': 'van', 'is_popular': False, 'year_start': 2001},
                {'name': 'Ducato', 'body_type': 'van', 'is_popular': False, 'year_start': 1981},
                {'name': 'Grande Punto', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2005, 'year_end': 2012},
            ],
        }

        # Only add luxury brands if they exist in the database
        for brand_name in luxury_additions.keys():
            if CarBrand.objects.filter(name=brand_name).exists():
                models_data.update({brand_name: luxury_additions[brand_name]})

        # Add the massive expansion
        models_data.update(massive_expansion)

        # Add models for remaining new brands
        remaining_brands = {
            'Suzuki': [
                {'name': 'Swift', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2004},
                {'name': 'Vitara', 'body_type': 'suv', 'is_popular': True, 'year_start': 1988},
                {'name': 'Jimny', 'body_type': 'suv', 'is_popular': True, 'year_start': 1998},
                {'name': 'Baleno', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2015},
                {'name': 'S-Cross', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2013},
                {'name': 'Alto', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1979},
                {'name': 'Celerio', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2014},
                {'name': 'Ciaz', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2014},
                {'name': 'Ertiga', 'body_type': 'van', 'is_popular': True, 'year_start': 2012},
                {'name': 'Grand Vitara', 'body_type': 'suv', 'is_popular': False, 'year_start': 1998, 'year_end': 2015},
                {'name': 'Ignis', 'body_type': 'crossover', 'is_popular': False, 'year_start': 2016},
                {'name': 'Kizashi', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2009, 'year_end': 2013},
                {'name': 'SX4', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2006, 'year_end': 2014},
                {'name': 'Wagon R', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1993},
                {'name': 'XL6', 'body_type': 'van', 'is_popular': False, 'year_start': 2019},
            ],
            'Skoda': [
                {'name': 'Octavia', 'body_type': 'sedan', 'is_popular': True, 'year_start': 1996},
                {'name': 'Superb', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2001},
                {'name': 'Fabia', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1999},
                {'name': 'Kodiaq', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'Karoq', 'body_type': 'suv', 'is_popular': True, 'year_start': 2017},
                {'name': 'Kamiq', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2019},
                {'name': 'Scala', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2019},
                {'name': 'Rapid', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2012},
                {'name': 'Citigo', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2011, 'year_end': 2019},
                {'name': 'Yeti', 'body_type': 'suv', 'is_popular': False, 'year_start': 2009, 'year_end': 2017},
                {'name': 'Roomster', 'body_type': 'van', 'is_popular': False, 'year_start': 2006, 'year_end': 2015},
            ],
            'Seat': [
                {'name': 'Leon', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1999},
                {'name': 'Ibiza', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1984},
                {'name': 'Ateca', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'Arona', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2017},
                {'name': 'Tarraco', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'Toledo', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1991},
                {'name': 'Alhambra', 'body_type': 'van', 'is_popular': False, 'year_start': 1996},
                {'name': 'Altea', 'body_type': 'van', 'is_popular': False, 'year_start': 2004, 'year_end': 2015},
                {'name': 'Cordoba', 'body_type': 'sedan', 'is_popular': False, 'year_start': 1993, 'year_end': 2009},
                {'name': 'Exeo', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2008, 'year_end': 2013},
                {'name': 'Mii', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2011, 'year_end': 2019},
            ],
            'Daihatsu': [
                {'name': 'Terios', 'body_type': 'suv', 'is_popular': True, 'year_start': 1997},
                {'name': 'Sirion', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1998},
                {'name': 'Charade', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 1977},
                {'name': 'Cuore', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1980},
                {'name': 'Materia', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2006, 'year_end': 2011},
                {'name': 'Move', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1995},
                {'name': 'Rocky', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'Tanto', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2003},
                {'name': 'YRV', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2000, 'year_end': 2005},
            ],
            'Isuzu': [
                {'name': 'D-Max', 'body_type': 'pickup', 'is_popular': True, 'year_start': 2002},
                {'name': 'MU-X', 'body_type': 'suv', 'is_popular': True, 'year_start': 2013},
                {'name': 'Trooper', 'body_type': 'suv', 'is_popular': False, 'year_start': 1981, 'year_end': 2002},
                {'name': 'Rodeo', 'body_type': 'pickup', 'is_popular': False, 'year_start': 1988, 'year_end': 2012},
                {'name': 'Ascender', 'body_type': 'suv', 'is_popular': False, 'year_start': 2003, 'year_end': 2008},
                {'name': 'Axiom', 'body_type': 'suv', 'is_popular': False, 'year_start': 2002, 'year_end': 2004},
                {'name': 'VehiCROSS', 'body_type': 'suv', 'is_popular': False, 'year_start': 1997, 'year_end': 2001},
            ],
            'Tata': [
                {'name': 'Nexon', 'body_type': 'suv', 'is_popular': True, 'year_start': 2017},
                {'name': 'Harrier', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'Safari', 'body_type': 'suv', 'is_popular': True, 'year_start': 1998},
                {'name': 'Tiago', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2016},
                {'name': 'Tigor', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2017},
                {'name': 'Altroz', 'body_type': 'hatchback', 'is_popular': True, 'year_start': 2020},
                {'name': 'Punch', 'body_type': 'crossover', 'is_popular': True, 'year_start': 2021},
                {'name': 'Nano', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2008, 'year_end': 2018},
                {'name': 'Indica', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 1998, 'year_end': 2018},
                {'name': 'Indigo', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2002, 'year_end': 2019},
                {'name': 'Sumo', 'body_type': 'suv', 'is_popular': False, 'year_start': 1994},
                {'name': 'Xenon', 'body_type': 'pickup', 'is_popular': False, 'year_start': 2007, 'year_end': 2019},
            ],
            'Mahindra': [
                {'name': 'XUV500', 'body_type': 'suv', 'is_popular': True, 'year_start': 2011},
                {'name': 'XUV300', 'body_type': 'suv', 'is_popular': True, 'year_start': 2019},
                {'name': 'Scorpio', 'body_type': 'suv', 'is_popular': True, 'year_start': 2002},
                {'name': 'Thar', 'body_type': 'suv', 'is_popular': True, 'year_start': 2010},
                {'name': 'Bolero', 'body_type': 'suv', 'is_popular': True, 'year_start': 2001},
                {'name': 'KUV100', 'body_type': 'crossover', 'is_popular': False, 'year_start': 2016},
                {'name': 'TUV300', 'body_type': 'suv', 'is_popular': False, 'year_start': 2015},
                {'name': 'Marazzo', 'body_type': 'van', 'is_popular': False, 'year_start': 2018},
                {'name': 'Xylo', 'body_type': 'van', 'is_popular': False, 'year_start': 2009, 'year_end': 2019},
            ],
            'BYD': [
                {'name': 'Tang', 'body_type': 'suv', 'is_popular': True, 'year_start': 2015},
                {'name': 'Song', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'Qin', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2012},
                {'name': 'Han', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2020},
                {'name': 'Yuan', 'body_type': 'suv', 'is_popular': True, 'year_start': 2016},
                {'name': 'e6', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2009},
                {'name': 'F3', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2005},
                {'name': 'S6', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2011},
                {'name': 'S7', 'body_type': 'suv', 'is_popular': False, 'year_start': 2017},
            ],
            'Geely': [
                {'name': 'Coolray', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'Azkarra', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'Emgrand', 'body_type': 'sedan', 'is_popular': True, 'year_start': 2009},
                {'name': 'Okavango', 'body_type': 'suv', 'is_popular': True, 'year_start': 2021},
                {'name': 'Tugella', 'body_type': 'suv', 'is_popular': False, 'year_start': 2020},
                {'name': 'Atlas', 'body_type': 'pickup', 'is_popular': False, 'year_start': 2018},
                {'name': 'GC9', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2015},
                {'name': 'Vision', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2006},
            ],
            'Great Wall': [
                {'name': 'Wingle', 'body_type': 'pickup', 'is_popular': True, 'year_start': 2006},
                {'name': 'Hover', 'body_type': 'suv', 'is_popular': True, 'year_start': 2005},
                {'name': 'Voleex', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2008},
                {'name': 'Florid', 'body_type': 'sedan', 'is_popular': False, 'year_start': 2008},
                {'name': 'Peri', 'body_type': 'hatchback', 'is_popular': False, 'year_start': 2007},
                {'name': 'Sailor', 'body_type': 'pickup', 'is_popular': False, 'year_start': 2002},
            ],
            'Haval': [
                {'name': 'H6', 'body_type': 'suv', 'is_popular': True, 'year_start': 2011},
                {'name': 'H9', 'body_type': 'suv', 'is_popular': True, 'year_start': 2014},
                {'name': 'F7', 'body_type': 'suv', 'is_popular': True, 'year_start': 2018},
                {'name': 'H2', 'body_type': 'suv', 'is_popular': False, 'year_start': 2014},
                {'name': 'H4', 'body_type': 'suv', 'is_popular': False, 'year_start': 2018},
                {'name': 'Jolion', 'body_type': 'suv', 'is_popular': True, 'year_start': 2020},
                {'name': 'Big Dog', 'body_type': 'suv', 'is_popular': False, 'year_start': 2020},
            ],
        }

        models_data.update(remaining_brands)

        # Count total models to be added
        total_new_models = 0
        for brand_name, models in models_data.items():
            if CarBrand.objects.filter(name=brand_name).exists():
                total_new_models += len(models)

        self.stdout.write(f'Planning to add {total_new_models} car models...')

        created_count = 0
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
                            'model_year_start': model_data.get('year_start'),
                            'model_year_end': model_data.get('year_end'),
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(f'✓ Created model: {brand.name} {model.name}')
                    else:
                        self.stdout.write(f'• Model already exists: {brand.name} {model.name}')
            except CarBrand.DoesNotExist:
                self.stdout.write(f'⚠ Brand {brand_name} not found, skipping models')

        self.stdout.write(f'\n📊 Summary: Created {created_count} new car models')
        final_count = CarModel.objects.count()
        self.stdout.write(f'📊 Total car models in database: {final_count}')
