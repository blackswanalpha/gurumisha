#!/usr/bin/env python
"""
Test script for car listing functionality fixes
Tests edit car details, feature/unfeature, and deletion process
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Car, CarBrand, CarModel, Vendor
import json

User = get_user_model()

def test_car_listing_functionality():
    """Test all car listing functionality"""
    print("🚗 Testing Car Listing Functionality Fixes")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Create test admin user
    admin_user = User.objects.create_user(
        username='testadmin',
        email='admin@test.com',
        password='testpass123',
        role='admin'
    )
    
    # Create test vendor
    vendor_user = User.objects.create_user(
        username='testvendor',
        email='vendor@test.com',
        password='testpass123',
        role='vendor'
    )
    
    vendor = Vendor.objects.create(
        user=vendor_user,
        company_name='Test Motors',
        is_approved=True
    )
    
    # Create test brand and model
    brand = CarBrand.objects.create(name='Toyota', is_active=True)
    model = CarModel.objects.create(name='Camry', brand=brand, is_active=True)
    
    # Create test car
    car = Car.objects.create(
        vendor=vendor,
        brand=brand,
        model=model,
        year=2020,
        condition='used',
        engine_size='2.5L',
        fuel_type='petrol',
        transmission='automatic',
        mileage=50000,
        color='White',
        price=2500000,
        title='2020 Toyota Camry',
        description='Well maintained car',
        is_approved=True
    )
    
    print(f"✅ Created test car: {car.title}")
    
    # Login as admin
    client.login(username='testadmin', password='testpass123')
    print("✅ Logged in as admin")
    
    # Test 1: Edit car details
    print("\n📝 Testing Edit Car Details...")
    edit_url = reverse('core:admin_car_edit', kwargs={'car_id': car.id})
    edit_data = {
        'title': '2020 Toyota Camry - Updated',
        'brand': brand.id,
        'model': model.id,
        'year': 2020,
        'condition': 'used',
        'engine_size': '2.5L',
        'fuel_type': 'petrol',
        'transmission': 'automatic',
        'mileage': 45000,
        'color': 'Silver',
        'price': 2400000,
        'description': 'Updated description',
        'features': 'AC, Power Steering',
        'listing_type': 'local',
        'status': 'available',
        'is_approved': True,
        'negotiable': True,
        'is_hot_deal': False,
        'star_rating': 4
    }
    
    response = client.post(edit_url, edit_data, HTTP_HX_REQUEST='true')
    
    if response.status_code == 200:
        try:
            response_data = json.loads(response.content)
            if response_data.get('status') == 'success':
                print("✅ Edit car details: SUCCESS")
                
                # Verify changes
                car.refresh_from_db()
                assert car.title == '2020 Toyota Camry - Updated'
                assert car.color == 'Silver'
                assert car.mileage == 45000
                print("✅ Car details updated correctly")
            else:
                print(f"❌ Edit failed: {response_data.get('message', 'Unknown error')}")
        except json.JSONDecodeError:
            print("❌ Edit response not JSON - form validation errors")
    else:
        print(f"❌ Edit request failed with status {response.status_code}")
    
    # Test 2: Feature car
    print("\n⭐ Testing Feature Car...")
    feature_url = reverse('core:admin_feature_car', kwargs={'car_id': car.id})
    feature_data = 'action=feature&tier=bronze'
    
    response = client.post(
        feature_url, 
        feature_data, 
        content_type='application/x-www-form-urlencoded'
    )
    
    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data.get('status') == 'success':
            print("✅ Feature car: SUCCESS")
            
            # Verify car is featured
            car.refresh_from_db()
            assert car.is_featured()
            assert car.featured_tier == 'bronze'
            print("✅ Car featured correctly")
        else:
            print(f"❌ Feature failed: {response_data.get('message', 'Unknown error')}")
    else:
        print(f"❌ Feature request failed with status {response.status_code}")
    
    # Test 3: Unfeature car
    print("\n🌟 Testing Unfeature Car...")
    unfeature_data = 'action=unfeature'
    
    response = client.post(
        feature_url, 
        unfeature_data, 
        content_type='application/x-www-form-urlencoded'
    )
    
    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data.get('status') == 'success':
            print("✅ Unfeature car: SUCCESS")
            
            # Verify car is not featured
            car.refresh_from_db()
            assert not car.is_featured()
            assert car.featured_tier == 'none'
            print("✅ Car unfeatured correctly")
        else:
            print(f"❌ Unfeature failed: {response_data.get('message', 'Unknown error')}")
    else:
        print(f"❌ Unfeature request failed with status {response.status_code}")
    
    # Test 4: Delete car
    print("\n🗑️ Testing Delete Car...")
    delete_url = reverse('core:admin_car_delete', kwargs={'car_id': car.id})
    
    response = client.post(delete_url, content_type='application/json')
    
    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data.get('status') == 'success':
            print("✅ Delete car: SUCCESS")
            
            # Verify car is deleted
            assert not Car.objects.filter(id=car.id).exists()
            print("✅ Car deleted correctly")
        else:
            print(f"❌ Delete failed: {response_data.get('message', 'Unknown error')}")
    else:
        print(f"❌ Delete request failed with status {response.status_code}")
    
    print("\n🎉 All tests completed!")
    print("=" * 50)

if __name__ == '__main__':
    test_car_listing_functionality()
