#!/usr/bin/env python3
"""
Test script to verify modal fixes for the valuation system
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from core.models import CarMake, CarModel

def test_make_model_data():
    """Test that we have sufficient make/model data for the dropdowns"""
    print("Testing Make/Model Data...")
    
    # Check total counts
    total_makes = CarMake.objects.filter(is_active=True).count()
    total_models = CarModel.objects.filter(is_active=True).count()
    
    print(f"Total active makes: {total_makes}")
    print(f"Total active models: {total_models}")
    
    # Check popular makes have models
    popular_makes = ['Toyota', 'Honda', 'Nissan', 'BMW', 'Mercedes-Benz', 'Audi']
    
    for make_name in popular_makes:
        try:
            make = CarMake.objects.get(name=make_name, is_active=True)
            model_count = CarModel.objects.filter(make=make, is_active=True).count()
            print(f"{make_name}: {model_count} models")
            
            if model_count > 0:
                # Show first few models
                models = CarModel.objects.filter(make=make, is_active=True)[:5]
                model_names = [m.name for m in models]
                print(f"  Sample models: {', '.join(model_names)}")
            
        except CarMake.DoesNotExist:
            print(f"{make_name}: NOT FOUND")
    
    print("\n" + "="*50)
    return total_makes > 0 and total_models > 0

def test_htmx_endpoint():
    """Test the HTMX models endpoint"""
    print("Testing HTMX Models Endpoint...")
    
    from django.test import RequestFactory
    from core.views import htmx_models_by_make
    
    factory = RequestFactory()
    
    # Test with Toyota
    try:
        toyota = CarMake.objects.get(name='Toyota')
        request = factory.get(f'/htmx/models-by-make/?make={toyota.id}&context=valuation')
        response = htmx_models_by_make(request)
        
        print(f"Response status: {response.status_code}")
        print(f"Response content length: {len(response.content)}")
        
        # Check if response contains options
        content = response.content.decode('utf-8')
        if '<option' in content:
            option_count = content.count('<option')
            print(f"Found {option_count} option elements")
            print("✅ HTMX endpoint working correctly")
        else:
            print("❌ No option elements found in response")
            print(f"Response content: {content[:200]}...")
            
    except CarMake.DoesNotExist:
        print("❌ Toyota make not found")
    except Exception as e:
        print(f"❌ Error testing HTMX endpoint: {e}")
    
    print("\n" + "="*50)

def test_valuation_system():
    """Test the valuation calculation system"""
    print("Testing Valuation System...")
    
    from core.views import calculate_base_value, apply_age_depreciation, apply_mileage_adjustment, apply_condition_adjustment
    
    try:
        # Test with Toyota Camry
        toyota = CarMake.objects.get(name='Toyota')
        camry = CarModel.objects.filter(make=toyota, name__icontains='Camry').first()
        
        if camry:
            print(f"Testing with: {camry}")
            
            # Test calculations
            base_value = calculate_base_value(toyota, camry, 2020)
            depreciated = apply_age_depreciation(base_value, 4)
            mileage_adjusted = apply_mileage_adjustment(depreciated, 50000)
            final_value = apply_condition_adjustment(mileage_adjusted, 'good')
            
            print(f"Base value: {base_value:,} KSH")
            print(f"After depreciation: {depreciated:,} KSH")
            print(f"After mileage adjustment: {mileage_adjusted:,} KSH")
            print(f"Final value: {final_value:,} KSH")
            
            if final_value > 0:
                print("✅ Valuation system working correctly")
            else:
                print("❌ Valuation system returned zero value")
        else:
            print("❌ Toyota Camry not found")
            
    except Exception as e:
        print(f"❌ Error testing valuation system: {e}")
    
    print("\n" + "="*50)

if __name__ == '__main__':
    print("🚗 Testing Gurumisha Modal Fixes")
    print("="*50)
    
    # Run tests
    test_make_model_data()
    test_htmx_endpoint()
    test_valuation_system()
    
    print("✅ All tests completed!")
