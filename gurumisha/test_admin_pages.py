#!/usr/bin/env python3
"""
Test script to verify all admin pages are accessible
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_admin_pages():
    """Test that all admin pages are accessible"""
    
    # Create a test client
    client = Client()
    
    # Create an admin user
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
    
    # Login as admin
    client.force_login(admin_user)
    
    # List of admin pages to test
    admin_pages = [
        ('dashboard', 'Admin Dashboard'),
        ('admin_users', 'User Management'),
        ('admin_vendors', 'Vendor Management'),
        ('admin_listings', 'Car Listings'),
        ('admin_analytics', 'Analytics'),
        ('admin_import_requests', 'Import Requests'),
        ('admin_spare_shop', 'Spare Shop'),
        ('admin_queries', 'Queries'),
        ('admin_content_management', 'Content Management'),
        ('admin_system_settings', 'System Settings'),
        ('admin_tracking_management', 'Tracking Management'),
        ('notifications', 'Notifications'),
    ]
    
    print("Testing Admin Pages Accessibility:")
    print("=" * 50)
    
    success_count = 0
    total_count = len(admin_pages)
    
    for url_name, page_name in admin_pages:
        try:
            url = reverse(f'core:{url_name}')
            response = client.get(url)
            
            if response.status_code == 200:
                print(f"✅ {page_name}: ACCESSIBLE ({url})")
                success_count += 1
            else:
                print(f"❌ {page_name}: ERROR {response.status_code} ({url})")
                
        except Exception as e:
            print(f"❌ {page_name}: EXCEPTION - {str(e)}")
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_count} pages accessible")
    
    if success_count == total_count:
        print("🎉 All admin pages are accessible!")
        return True
    else:
        print("⚠️  Some admin pages have issues.")
        return False

def test_sidebar_navigation():
    """Test that sidebar navigation links are working"""
    
    print("\nTesting Sidebar Navigation:")
    print("=" * 50)
    
    # Test that the base admin dashboard template loads
    client = Client()
    admin_user = User.objects.filter(role='admin').first()
    client.force_login(admin_user)
    
    response = client.get(reverse('core:dashboard'))
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for key navigation elements
        nav_elements = [
            'Dashboard',
            'Import Request',
            'User Management',
            'Vendor Management',
            'Car Listings',
            'Spare',  # Will match "Spare Shop"
            'Queries',
            'Notifications',
            'Content Management',
            'System Settings',
            'Analytics'
        ]
        
        found_elements = []
        for element in nav_elements:
            if element in content:
                found_elements.append(element)
                print(f"✅ {element}: Found in navigation")
            else:
                print(f"❌ {element}: Missing from navigation")
        
        print("=" * 50)
        print(f"Navigation Elements: {len(found_elements)}/{len(nav_elements)} found")
        
        return len(found_elements) == len(nav_elements)
    else:
        print(f"❌ Dashboard page failed to load: {response.status_code}")
        return False

if __name__ == '__main__':
    print("Gurumisha Admin Dashboard Test Suite")
    print("=" * 50)
    
    # Test page accessibility
    pages_ok = test_admin_pages()
    
    # Test navigation
    nav_ok = test_sidebar_navigation()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"Pages Accessible: {'✅ PASS' if pages_ok else '❌ FAIL'}")
    print(f"Navigation Working: {'✅ PASS' if nav_ok else '❌ FAIL'}")
    
    if pages_ok and nav_ok:
        print("\n🎉 All tests passed! Admin dashboard is fully functional.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        sys.exit(1)
