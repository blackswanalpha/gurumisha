#!/usr/bin/env python3
"""
Script to add comprehensive car models to the Gurumisha database
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha.settings')
django.setup()

from core.models import CarMake, CarModel

def add_models_for_brand(brand_name, models_data):
    """Add models for a specific brand"""
    try:
        brand = CarMake.objects.get(name=brand_name)
        created_count = 0
        
        for model_data in models_data:
            model, created = CarModel.objects.get_or_create(
                make=brand,
                name=model_data['name'],
                defaults={
                    'body_type': model_data['body_type'],
                    'is_popular': model_data.get('is_popular', False),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                print(f'✓ Created: {brand_name} {model.name}')
            else:
                print(f'• Already exists: {brand_name} {model.name}')
        
        total_models = CarModel.objects.filter(make=brand).count()
        print(f'\nCreated {created_count} new {brand_name} models')
        print(f'Total {brand_name} models: {total_models}\n')
        
    except CarMake.DoesNotExist:
        print(f'Brand {brand_name} not found')

# Suzuki models
suzuki_models = [
    {'name': 'AERIO', 'body_type': 'sedan'},
    {'name': 'ALTO', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'ALTO_C', 'body_type': 'hatchback'},
    {'name': 'ALTO_C2', 'body_type': 'hatchback'},
    {'name': 'ALTO_ECO', 'body_type': 'hatchback'},
    {'name': 'ALTO_HUSTLE', 'body_type': 'hatchback'},
    {'name': 'ALTO_LAPIN', 'body_type': 'hatchback'},
    {'name': 'ALTO_LAPIN_CHOCOLAT', 'body_type': 'hatchback'},
    {'name': 'ALTO_LAPIN_LC', 'body_type': 'hatchback'},
    {'name': 'ALTO_TURBO_RS', 'body_type': 'hatchback'},
    {'name': 'ALTO_WALKTHROUGH_VAN', 'body_type': 'van'},
    {'name': 'ALTO_WORKS', 'body_type': 'hatchback'},
    {'name': 'BALENO', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'CAPPUCCINO', 'body_type': 'convertible'},
    {'name': 'CARA', 'body_type': 'hatchback'},
    {'name': 'CARRY_TRUCK', 'body_type': 'pickup'},
    {'name': 'CARRY_VAN', 'body_type': 'van'},
    {'name': 'CERVO', 'body_type': 'hatchback'},
    {'name': 'CERVO_CLASSIC', 'body_type': 'hatchback'},
    {'name': 'CERVO_MODE', 'body_type': 'hatchback'},
    {'name': 'CULTUS', 'body_type': 'hatchback'},
    {'name': 'CULTUS_CRESCENT_WAGON', 'body_type': 'wagon'},
    {'name': 'CULTUS_WAGON', 'body_type': 'wagon'},
    {'name': 'ESCUDO', 'body_type': 'suv'},
    {'name': 'EVERY', 'body_type': 'van'},
    {'name': 'EVERY_LANDY', 'body_type': 'van'},
    {'name': 'EVERY_PLUS', 'body_type': 'van'},
    {'name': 'EVERY_WAGON', 'body_type': 'wagon'},
    {'name': 'FRONTE', 'body_type': 'hatchback'},
    {'name': 'FRONX', 'body_type': 'crossover'},
    {'name': 'HUSTLER', 'body_type': 'crossover'},
    {'name': 'IGNIS', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'JIMNY', 'body_type': 'suv', 'is_popular': True},
    {'name': 'JIMNY_1000', 'body_type': 'suv'},
    {'name': 'JIMNY_1300', 'body_type': 'suv'},
    {'name': 'JIMNY_L', 'body_type': 'suv'},
    {'name': 'JIMNY_NOMADE', 'body_type': 'suv'},
    {'name': 'JIMNY_SIERRA', 'body_type': 'suv'},
    {'name': 'JIMNY_WIDE', 'body_type': 'suv'},
    {'name': 'KEI', 'body_type': 'hatchback'},
    {'name': 'KEI_SPORT', 'body_type': 'hatchback'},
    {'name': 'KEI_WORKS', 'body_type': 'hatchback'},
    {'name': 'KIZASHI', 'body_type': 'sedan', 'is_popular': True},
    {'name': 'LANDY', 'body_type': 'van'},
    {'name': 'MIGHTY_BOY', 'body_type': 'pickup'},
    {'name': 'MR_WAGON', 'body_type': 'wagon'},
    {'name': 'MR_WAGON_WIT', 'body_type': 'wagon'},
    {'name': 'PALETTE', 'body_type': 'van'},
    {'name': 'PALETTE_SW', 'body_type': 'van'},
    {'name': 'SOLIO', 'body_type': 'van'},
    {'name': 'SOLIO_BANDIT', 'body_type': 'van'},
    {'name': 'SPACIA', 'body_type': 'van'},
    {'name': 'SPACIA_BASE', 'body_type': 'van'},
    {'name': 'SPACIA_CUSTOM', 'body_type': 'van'},
    {'name': 'SPACIA_CUSTOM_Z', 'body_type': 'van'},
    {'name': 'SPACIA_GEAR', 'body_type': 'van'},
    {'name': 'SPLASH', 'body_type': 'hatchback'},
    {'name': 'SUPER_CARRY', 'body_type': 'pickup'},
    {'name': 'SUZUKI_OTHER', 'body_type': 'other'},
    {'name': 'SWIFT', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'SWIFT_SPORT', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'SX4', 'body_type': 'crossover', 'is_popular': True},
    {'name': 'SX4_SEDAN', 'body_type': 'sedan'},
    {'name': 'SX4_S_CROSS', 'body_type': 'crossover'},
    {'name': 'TWIN', 'body_type': 'hatchback'},
    {'name': 'WAGON_R', 'body_type': 'wagon', 'is_popular': True},
    {'name': 'WAGON_R_CUSTOM_Z', 'body_type': 'wagon'},
    {'name': 'WAGON_R_RR', 'body_type': 'wagon'},
    {'name': 'WAGON_R_SMILE', 'body_type': 'wagon'},
    {'name': 'WAGON_R_STINGRAY', 'body_type': 'wagon'},
    {'name': 'WAGON_R_WIDE', 'body_type': 'wagon'},
    {'name': 'X-90', 'body_type': 'suv'},
    {'name': 'XBEE', 'body_type': 'crossover'},
]

# Lexus models
lexus_models = [
    {'name': 'CT', 'body_type': 'hatchback', 'is_popular': True},
    {'name': 'ES', 'body_type': 'sedan', 'is_popular': True},
    {'name': 'GS', 'body_type': 'sedan', 'is_popular': True},
    {'name': 'GS_F', 'body_type': 'sedan'},
    {'name': 'GX', 'body_type': 'suv', 'is_popular': True},
    {'name': 'HS', 'body_type': 'sedan'},
    {'name': 'IS', 'body_type': 'sedan', 'is_popular': True},
    {'name': 'IS_F', 'body_type': 'sedan'},
    {'name': 'LBX', 'body_type': 'crossover'},
    {'name': 'LC', 'body_type': 'coupe', 'is_popular': True},
    {'name': 'LEXUS_OTHER', 'body_type': 'other'},
    {'name': 'LFA', 'body_type': 'sports'},
    {'name': 'LM', 'body_type': 'van'},
    {'name': 'LS', 'body_type': 'luxury', 'is_popular': True},
    {'name': 'LX', 'body_type': 'suv', 'is_popular': True},
    {'name': 'NX', 'body_type': 'crossover', 'is_popular': True},
    {'name': 'RC', 'body_type': 'coupe', 'is_popular': True},
    {'name': 'RC_F', 'body_type': 'coupe'},
    {'name': 'RX', 'body_type': 'suv', 'is_popular': True},
    {'name': 'RZ', 'body_type': 'suv'},
    {'name': 'SC', 'body_type': 'convertible'},
    {'name': 'UX', 'body_type': 'crossover', 'is_popular': True},
]

if __name__ == '__main__':
    print("Adding comprehensive car models...")
    
    # Add Suzuki models
    print("Adding Suzuki models...")
    add_models_for_brand('Suzuki', suzuki_models)
    
    # Add Lexus models
    print("Adding Lexus models...")
    add_models_for_brand('Lexus', lexus_models)
    
    print("Comprehensive models addition completed!")
