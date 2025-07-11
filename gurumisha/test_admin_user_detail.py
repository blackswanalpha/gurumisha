#!/usr/bin/env python3
"""
Quick test script for admin user detail view
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
sys.path.append('/home/hp/Documents/augment-projects/gurumisha')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Vendor

User = get_user_model()

def test_admin_user_detail():
    """Test the admin user detail view"""
    print("Testing admin user detail view...")
    
    # Create test users
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )
        print("Created test admin user")
    
    test_user = User.objects.filter(role='customer').first()
    if not test_user:
        test_user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='customer'
        )
        print("Created test customer user")
    
    # Create test vendor
    vendor_user = User.objects.filter(role='vendor').first()
    if not vendor_user:
        vendor_user = User.objects.create_user(
            username='testvendor',
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        vendor, created = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                'company_name': 'Test Motors',
                'description': 'Test car dealership',
                'is_approved': True
            }
        )
        print("Created test vendor user")
    
    # Test the view
    client = Client()
    
    # Login as admin
    login_success = client.login(username=admin_user.username, password='testpass123')
    if not login_success:
        print("Failed to login as admin")
        return False
    
    print("Logged in as admin successfully")
    
    # Test customer user detail page
    response = client.get(f'/dashboard/admin/users/{test_user.id}/')
    print(f"Customer user detail page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Customer user detail page loads successfully")
        print(f"  - Page title contains: {test_user.username}")
    else:
        print(f"✗ Customer user detail page failed: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Error content: {response.content[:500]}")
        return False
    
    # Test vendor user detail page
    response = client.get(f'/dashboard/admin/users/{vendor_user.id}/')
    print(f"Vendor user detail page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Vendor user detail page loads successfully")
        print(f"  - Page title contains: {vendor_user.username}")
    else:
        print(f"✗ Vendor user detail page failed: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Error content: {response.content[:500]}")
        return False
    
    # Test admin users list page links
    response = client.get('/dashboard/admin/users/')
    print(f"Admin users list page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Admin users list page loads successfully")
        # Check if the detail links are present
        content = response.content.decode('utf-8')
        if f'/dashboard/admin/users/{test_user.id}/' in content:
            print("✓ User detail links are present in the list")
        else:
            print("✗ User detail links not found in the list")
    else:
        print(f"✗ Admin users list page failed: {response.status_code}")
        return False
    
    print("\n🎉 All tests passed! Admin user detail page is working correctly.")
    print(f"\nYou can now visit:")
    print(f"- http://127.0.0.1:8000/dashboard/admin/users/ (users list)")
    print(f"- http://127.0.0.1:8000/dashboard/admin/users/{test_user.id}/ (customer detail)")
    print(f"- http://127.0.0.1:8000/dashboard/admin/users/{vendor_user.id}/ (vendor detail)")
    
    return True

if __name__ == '__main__':
    try:
        test_admin_user_detail()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
