#!/usr/bin/env python
"""
Simple test script to verify all pages are working
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

def test_pages():
    """Test all main pages"""
    client = Client()
    
    pages_to_test = [
        ('Homepage', '/'),
        ('Car List', '/cars/'),
        ('Spare Parts', '/spare-parts/'),
        ('Blog', '/blog/'),
        ('About Us', '/about/'),
        ('Contact Us', '/contact/'),
    ]
    
    print("🧪 Testing Gurumisha Motors Pages...")
    print("=" * 50)
    
    all_passed = True
    
    for page_name, url in pages_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {page_name}: OK (200)")
            else:
                print(f"❌ {page_name}: FAILED ({response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {page_name}: ERROR - {str(e)}")
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All pages are working correctly!")
    else:
        print("⚠️  Some pages have issues. Check the logs above.")
    
    return all_passed

if __name__ == "__main__":
    test_pages()
