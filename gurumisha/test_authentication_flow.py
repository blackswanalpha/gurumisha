#!/usr/bin/env python3
"""
Test script to verify the authentication flow is working correctly
"""

import requests
import sys

def test_authentication_flow():
    """Test the complete authentication flow"""
    base_url = "http://localhost:8001"
    
    print("🔐 Testing Gurumisha Motors Authentication Flow")
    print("=" * 50)
    
    # Test 1: Public pages should be accessible
    public_pages = [
        ('/', 'Homepage'),
        ('/login/', 'Login Page'),
        ('/register/', 'Registration Page'),
        ('/cars/', 'Car Listings'),
        ('/about/', 'About Page'),
        ('/contact/', 'Contact Page'),
        ('/import/', 'Import Services'),
        ('/resources/', 'Resources'),
    ]
    
    print("\n1. Testing Public Pages:")
    for url, name in public_pages:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"   {name}: {status}")
        except Exception as e:
            print(f"   {name}: ❌ ERROR - {str(e)}")
    
    # Test 2: Protected pages should redirect to login
    protected_pages = [
        ('/sell-car/', 'Sell Car Page'),
        ('/dashboard/', 'User Dashboard'),
        ('/import/request/', 'Import Request'),
        ('/profile/', 'User Profile'),
    ]
    
    print("\n2. Testing Protected Pages (should redirect to login):")
    for url, name in protected_pages:
        try:
            response = requests.get(f"{base_url}{url}", allow_redirects=False, timeout=5)
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if location.startswith('/login/?next='):
                    print(f"   {name}: ✅ PASS (redirects to login)")
                else:
                    print(f"   {name}: ❌ FAIL (wrong redirect: {location})")
            else:
                print(f"   {name}: ❌ FAIL (status: {response.status_code})")
        except Exception as e:
            print(f"   {name}: ❌ ERROR - {str(e)}")
    
    # Test 3: Login page with next parameter
    print("\n3. Testing Login Page with Next Parameter:")
    test_urls = [
        '/login/?next=/sell-car/',
        '/login/?next=/dashboard/',
        '/login/?next=/import/request/',
    ]
    
    for url in test_urls:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"   {url}: {status}")
        except Exception as e:
            print(f"   {url}: ❌ ERROR - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication Flow Test Complete!")
    print("\nNext Steps:")
    print("1. Visit http://localhost:8001/ to see the homepage")
    print("2. Try accessing http://localhost:8001/sell-car/ (should redirect to login)")
    print("3. Register a new account at http://localhost:8001/register/")
    print("4. Login and test the dashboard functionality")

if __name__ == "__main__":
    test_authentication_flow()
