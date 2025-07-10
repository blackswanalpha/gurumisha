#!/usr/bin/env python
"""
End-to-end test for email verification system
This script tests the complete user registration and email verification workflow
"""

import os
import sys
import django
import time

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from core.models import User, VerificationCode
from django.contrib.auth import authenticate

def test_user_registration_and_verification():
    """Test complete user registration and email verification workflow"""
    print("🚀 Starting End-to-End Email Verification Test")
    print("=" * 60)
    
    # Test email
    test_email = 'genixailabs@gmail.com'
    test_username = 'genixailabs_test'
    
    # Clean up any existing test user
    User.objects.filter(email=test_email).delete()
    User.objects.filter(username=test_username).delete()
    
    # Create Django test client
    client = Client()
    
    print(f"📧 Test Email: {test_email}")
    print(f"👤 Test Username: {test_username}")
    print("=" * 60)
    
    # Step 1: Test registration page access
    print("\n1️⃣ Testing Registration Page Access")
    print("-" * 40)
    
    try:
        response = client.get('/register/')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✅ Registration page accessible")
    except Exception as e:
        print(f"❌ Registration page access failed: {e}")
        return False
    
    # Step 2: Test user registration
    print("\n2️⃣ Testing User Registration")
    print("-" * 40)
    
    registration_data = {
        'username': test_username,
        'email': test_email,
        'first_name': 'Genix',
        'last_name': 'AI Labs',
        'phone': '+254700000000',
        'role': 'customer',
        'password1': 'TestPassword123!',
        'password2': 'TestPassword123!',
    }
    
    try:
        response = client.post('/register/', registration_data)
        
        # Check if registration was successful (should redirect)
        if response.status_code == 302:
            print("✅ User registration successful (redirected)")
        else:
            print(f"⚠️  Registration response code: {response.status_code}")
            if hasattr(response, 'context') and response.context and 'form' in response.context:
                form_errors = response.context['form'].errors
                if form_errors:
                    print(f"   Form errors: {form_errors}")
        
        # Check if user was created
        user = User.objects.filter(email=test_email).first()
        if user:
            print(f"✅ User created in database: {user.username}")
            print(f"   Email verified: {user.is_email_verified}")
            print(f"   Has verification token: {bool(user.email_verification_token)}")
        else:
            print("❌ User not found in database")
            return False
            
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return False
    
    # Step 3: Test verification code generation
    print("\n3️⃣ Testing Verification Code Generation")
    print("-" * 40)
    
    try:
        # Generate verification code
        verification_code = VerificationCode.create_verification_code(
            user=user,
            code_type='email_verification',
            expiry_minutes=15
        )
        
        print(f"✅ Verification code generated: {verification_code.code}")
        print(f"   Code type: {verification_code.code_type}")
        print(f"   Expires at: {verification_code.expires_at}")
        print(f"   Is valid: {verification_code.is_valid()}")
        
    except Exception as e:
        print(f"❌ Verification code generation failed: {e}")
        return False
    
    # Step 4: Test UUID token verification
    print("\n4️⃣ Testing UUID Token Verification")
    print("-" * 40)
    
    try:
        if user.email_verification_token:
            token = user.email_verification_token
            verification_url = f'/verify-email/{token}/'
            
            print(f"   Token: {token[:8]}...")
            print(f"   Verification URL: {verification_url}")
            
            # Test token verification
            response = client.get(verification_url)
            
            if response.status_code == 200:
                print("✅ UUID token verification page accessible")
                
                # Refresh user from database
                user.refresh_from_db()
                if user.is_email_verified:
                    print("✅ Email verified via UUID token")
                else:
                    print("⚠️  Email not yet verified (may need manual verification)")
            else:
                print(f"❌ Token verification failed: {response.status_code}")
        else:
            print("⚠️  No UUID token found")
            
    except Exception as e:
        print(f"❌ UUID token verification failed: {e}")
    
    # Step 5: Test 6-digit code verification (create new user for this test)
    print("\n5️⃣ Testing 6-Digit Code Verification")
    print("-" * 40)
    
    try:
        # Create a new user for code verification test
        code_test_user = User.objects.create_user(
            username='genix_code_test',
            email='genixailabs+code@gmail.com',
            password='TestPassword123!',
            first_name='Code',
            last_name='Test',
            is_email_verified=False
        )
        
        # Generate verification code
        code_obj = VerificationCode.create_verification_code(
            user=code_test_user,
            code_type='email_verification',
            expiry_minutes=15
        )
        
        print(f"✅ Code test user created: {code_test_user.username}")
        print(f"✅ Verification code: {code_obj.code}")
        
        # Test code verification page
        response = client.get('/verify-email-code/')
        if response.status_code == 200:
            print("✅ Code verification page accessible")
        else:
            print(f"❌ Code verification page failed: {response.status_code}")
        
        # Test code submission (simulate form submission)
        code_data = {
            'code': code_obj.code
        }
        
        # Note: This would require proper session handling for the user
        print(f"   Code to verify: {code_obj.code}")
        print("   (Manual verification required via web interface)")
        
    except Exception as e:
        print(f"❌ 6-digit code verification test failed: {e}")
    
    # Step 6: Test login with verified user
    print("\n6️⃣ Testing Login with Verified User")
    print("-" * 40)
    
    try:
        # Manually verify the user for login test
        user.is_email_verified = True
        user.save()
        
        login_data = {
            'username': test_email,  # Using email as username
            'password': 'TestPassword123!',
        }
        
        response = client.post('/login/', login_data)
        
        if response.status_code == 302:
            print("✅ Login successful (redirected)")
        else:
            print(f"⚠️  Login response code: {response.status_code}")
        
        # Test authentication
        auth_user = authenticate(username=test_email, password='TestPassword123!')
        if auth_user:
            print("✅ User authentication successful")
        else:
            print("❌ User authentication failed")
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
    
    # Step 7: Cleanup
    print("\n7️⃣ Cleanup Test Data")
    print("-" * 40)
    
    try:
        # Clean up test users and verification codes
        VerificationCode.objects.filter(user__email__contains='genixailabs').delete()
        User.objects.filter(email__contains='genixailabs').delete()
        User.objects.filter(username__contains='genix').delete()
        
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 End-to-End Email Verification Test Completed!")
    print("\n📋 Manual Testing Steps:")
    print("1. Open browser: http://localhost:8000/register/")
    print("2. Register with email: genixailabs@gmail.com")
    print("3. Check email for verification messages")
    print("4. Test both UUID token link and 6-digit code")
    print("5. Verify login works after email verification")
    print("\n📧 Check your email inbox for verification messages!")
    
    return True

def test_email_templates():
    """Test email template rendering"""
    print("\n📧 Testing Email Template Rendering")
    print("=" * 40)
    
    try:
        from django.template.loader import render_to_string
        
        # Test UUID token email template
        context = {
            'user': {'get_full_name': 'Test User', 'username': 'testuser'},
            'token': 'test-token-123',
            'domain': 'localhost:8000',
            'protocol': 'http',
        }
        
        html_content = render_to_string('core/auth/email_verification_email.html', context)
        if html_content and len(html_content) > 100:
            print("✅ UUID token email template renders correctly")
        else:
            print("❌ UUID token email template rendering failed")
        
        # Test verification code email template
        code_context = {
            'user': {'get_full_name': 'Test User', 'username': 'testuser'},
            'verification_code': '123456',
            'expiry_minutes': 15,
            'site_name': 'Gurumisha Motors',
        }
        
        code_html = render_to_string('core/auth/verification_code_email.html', code_context)
        if code_html and len(code_html) > 100:
            print("✅ Verification code email template renders correctly")
        else:
            print("❌ Verification code email template rendering failed")
            
    except Exception as e:
        print(f"❌ Email template testing failed: {e}")

if __name__ == "__main__":
    print("🧪 Gurumisha Motors - Email Verification System Test Suite")
    print("=" * 70)
    
    # Run tests
    test_email_templates()
    test_user_registration_and_verification()
    
    print("\n" + "=" * 70)
    print("🏁 All tests completed!")
    print("\n🌐 Django Server Status:")
    print("   Server should be running at: http://localhost:8000")
    print("   Registration page: http://localhost:8000/register/")
    print("   Login page: http://localhost:8000/login/")
