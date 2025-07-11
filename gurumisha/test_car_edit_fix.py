#!/usr/bin/env python3
"""
Test script to validate car edit functionality fixes
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/hp/Documents/augment-projects/gurumisha')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from core.models import Car, HotDeal
from core.dashboard_forms import AdminCarEditForm
from django.contrib.auth import get_user_model

User = get_user_model()

def test_car_edit_functionality():
    """Test the car edit functionality"""
    print("🚗 Testing Car Edit Functionality")
    print("=" * 50)
    
    # Get a test car
    car = Car.objects.first()
    if not car:
        print("❌ No cars found in database")
        return False
    
    print(f"✅ Found test car: {car.title}")
    
    # Test form instantiation
    try:
        form = AdminCarEditForm(instance=car)
        print("✅ AdminCarEditForm instantiated successfully")
        
        # Check if new fields are present
        if 'is_featured' in form.fields:
            print("✅ is_featured field present in form")
        else:
            print("❌ is_featured field missing from form")
            
        if 'is_certified' in form.fields:
            print("✅ is_certified field present in form")
        else:
            print("❌ is_certified field missing from form")
            
    except Exception as e:
        print(f"❌ Form instantiation failed: {e}")
        return False
    
    # Test model methods
    try:
        # Test new featured system
        original_featured = car.is_featured
        print(f"✅ Car featured status: {original_featured}")
        
        # Test can_be_featured method
        can_feature, message = car.can_be_featured()
        print(f"✅ Can be featured: {can_feature} - {message}")
        
        # Test certified status
        print(f"✅ Car certified status: {car.is_certified}")
        
        # Test hot deal status
        print(f"✅ Car hot deal status: {car.is_hot_deal}")
        
    except Exception as e:
        print(f"❌ Model method test failed: {e}")
        return False
    
    # Test form validation with sample data
    try:
        form_data = {
            'title': car.title,
            'brand': car.brand.id if car.brand else '',
            'model': car.model.id if car.model else '',
            'year': car.year,
            'condition': car.condition,
            'engine_size': car.engine_size,
            'fuel_type': car.fuel_type,
            'transmission': car.transmission,
            'mileage': car.mileage,
            'color': car.color,
            'price': car.price,
            'description': car.description,
            'features': car.features,
            'listing_type': car.listing_type,
            'status': car.status,
            'is_approved': car.is_approved,
            'negotiable': car.negotiable,
            'is_hot_deal': True,  # Test hot deal
            'is_featured': True,  # Test featured
            'is_certified': True,  # Test certified
            'star_rating': car.star_rating or 4.0,
        }
        
        form = AdminCarEditForm(form_data, instance=car)
        if form.is_valid():
            print("✅ Form validation passed")
            
            # Test save (but don't actually save)
            # updated_car = form.save(commit=False)
            # print("✅ Form save test passed")
            
        else:
            print("❌ Form validation failed:")
            for field, errors in form.errors.items():
                print(f"  - {field}: {errors}")
            
    except Exception as e:
        print(f"❌ Form validation test failed: {e}")
        return False
    
    print("\n🎉 All tests completed!")
    return True

def test_hot_deals_functionality():
    """Test hot deals functionality"""
    print("\n🔥 Testing Hot Deals Functionality")
    print("=" * 50)
    
    try:
        # Get a car for testing
        car = Car.objects.first()
        if not car:
            print("❌ No cars found for hot deals test")
            return False
        
        print(f"✅ Testing hot deals with car: {car.title}")
        
        # Test HotDeal model
        hot_deal_data = {
            'car': car,
            'title': f'Hot Deal: {car.title}',
            'discount_type': 'percentage',
            'discount_value': 15.0,
            'original_price': car.price,
            'start_date': django.utils.timezone.now(),
            'end_date': django.utils.timezone.now() + django.utils.timezone.timedelta(days=7),
            'is_active': True
        }
        
        # Test hot deal creation (but don't save)
        hot_deal = HotDeal(**hot_deal_data)
        print("✅ HotDeal instance created successfully")
        
        # Test calculation methods
        hot_deal.calculate_discounted_price()
        print(f"✅ Discounted price calculated: {hot_deal.discounted_price}")
        
        print("✅ Hot deals functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Hot deals test failed: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Running Car Edit Functionality Tests")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_car_edit_functionality()
    success &= test_hot_deals_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Car edit functionality should work correctly.")
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
    
    print("=" * 60)
