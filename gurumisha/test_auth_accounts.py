#!/usr/bin/env python
"""
Test script to verify all authentication test accounts are working correctly
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import User, Vendor


def test_authentication():
    """Test authentication for all test accounts"""
    print("🔐 TESTING AUTHENTICATION FOR ALL TEST ACCOUNTS")
    print("=" * 60)
    
    # Test accounts data
    test_accounts = [
        # Admin
        {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'type': 'Admin'},
        
        # Vendors
        {'username': 'tokyomotors', 'password': 'vendor123', 'role': 'vendor', 'type': 'Vendor'},
        {'username': 'nairobiparts', 'password': 'vendor123', 'role': 'vendor', 'type': 'Vendor'},
        {'username': 'mombasacars', 'password': 'vendor123', 'role': 'vendor', 'type': 'Vendor'},
        
        # Customers
        {'username': 'johndoe', 'password': 'customer123', 'role': 'customer', 'type': 'Customer'},
        {'username': 'janesmith', 'password': 'customer123', 'role': 'customer', 'type': 'Customer'},
        {'username': 'michaeljohnson', 'password': 'customer123', 'role': 'customer', 'type': 'Customer'},
        
        # Additional test accounts
        {'username': 'genixailabs', 'password': 'TestPassword123!', 'role': 'customer', 'type': 'Test'},
        {'username': 'testuser', 'password': 'testpass123', 'role': 'customer', 'type': 'Test'},
        {'username': 'tokenuser', 'password': 'testpassword123', 'role': 'customer', 'type': 'Test'},
    ]
    
    successful_logins = 0
    failed_logins = 0
    
    for account in test_accounts:
        print(f"\n🧪 Testing {account['type']} Account: {account['username']}")
        print("-" * 40)
        
        # Test authentication
        user = authenticate(username=account['username'], password=account['password'])
        
        if user:
            print(f"✅ Authentication: SUCCESS")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Verified: {user.is_verified}")
            print(f"   Email Verified: {user.is_email_verified}")
            print(f"   Full Name: {user.get_full_name()}")
            
            # Additional checks for specific roles
            if user.role == 'admin':
                print(f"   Superuser: {user.is_superuser}")
                print(f"   Staff: {user.is_staff}")
            elif user.role == 'vendor':
                try:
                    vendor = user.vendor
                    print(f"   Company: {vendor.company_name}")
                    print(f"   Approved: {vendor.is_approved}")
                except:
                    print("   ⚠️  Vendor profile not found")
            
            successful_logins += 1
        else:
            print(f"❌ Authentication: FAILED")
            failed_logins += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AUTHENTICATION TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful logins: {successful_logins}")
    print(f"❌ Failed logins: {failed_logins}")
    print(f"📈 Success rate: {(successful_logins/(successful_logins+failed_logins)*100):.1f}%")
    
    if failed_logins == 0:
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ All test accounts are ready for use")
    else:
        print(f"\n⚠️  {failed_logins} authentication tests failed")
        print("❌ Some accounts may need to be recreated")


def test_database_status():
    """Test database status and user counts"""
    print("\n\n📊 DATABASE STATUS CHECK")
    print("=" * 60)
    
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True, is_email_verified=True).count()
    admin_users = User.objects.filter(role='admin').count()
    vendor_users = User.objects.filter(role='vendor').count()
    customer_users = User.objects.filter(role='customer').count()
    approved_vendors = Vendor.objects.filter(is_approved=True).count()
    
    print(f"👥 Total Users: {total_users}")
    print(f"✅ Verified Users: {verified_users}")
    print(f"🔑 Admin Users: {admin_users}")
    print(f"🏢 Vendor Users: {vendor_users}")
    print(f"👤 Customer Users: {customer_users}")
    print(f"✅ Approved Vendors: {approved_vendors}")
    
    print(f"\n📈 Verification Rate: {(verified_users/total_users*100):.1f}%")
    print(f"📈 Vendor Approval Rate: {(approved_vendors/vendor_users*100):.1f}%")


def main():
    """Main test function"""
    print("🚀 GURUMISHA AUTHENTICATION TEST SUITE")
    print("=" * 60)
    print("Testing all authentication accounts from auth.txt")
    print("=" * 60)
    
    try:
        test_authentication()
        test_database_status()
        
        print("\n\n🎯 NEXT STEPS")
        print("=" * 60)
        print("1. Start the development server: python manage.py runserver")
        print("2. Navigate to: http://localhost:8000/auth/login/")
        print("3. Test login with any of the verified credentials")
        print("4. Check role-based dashboard access")
        print("5. Verify all functionality works as expected")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        print("Please check your Django setup and database connection")


if __name__ == '__main__':
    main()
