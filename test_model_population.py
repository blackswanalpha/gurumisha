#!/usr/bin/env python3
"""
Test script to verify model population functionality in server.py
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

# Import the server module
from server import DeploymentManager

def test_model_population():
    """Test the model population functionality"""
    print("Testing model population functionality...")
    
    # Create deployment manager instance
    deployment_manager = DeploymentManager('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
    
    # Initialize Django
    if not deployment_manager.initialize_django():
        print("Failed to initialize Django")
        return False
    
    # Test model population
    print("Running model population...")
    result = deployment_manager.populate_car_models()
    
    if result:
        print("✅ Model population successful!")
        
        # Check results
        from core.models import CarMake, CarModel
        total_makes = CarMake.objects.filter(is_active=True).count()
        total_models = CarModel.objects.filter(is_active=True).count()
        
        print(f"📊 Database Statistics:")
        print(f"   Total car makes: {total_makes}")
        print(f"   Total car models: {total_models}")
        
        # Show some popular brands
        popular_brands = ['Toyota', 'Honda', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Audi']
        print(f"\n🚗 Popular Brand Model Counts:")
        for brand_name in popular_brands:
            try:
                brand = CarMake.objects.get(name=brand_name)
                model_count = CarModel.objects.filter(make=brand, is_active=True).count()
                print(f"   {brand_name}: {model_count} models")
            except CarMake.DoesNotExist:
                print(f"   {brand_name}: Not found")
        
        return True
    else:
        print("❌ Model population failed!")
        return False

if __name__ == '__main__':
    success = test_model_population()
    sys.exit(0 if success else 1)
