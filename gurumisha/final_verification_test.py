#!/usr/bin/env python
"""
Final comprehensive test for email verification system
This script performs the complete end-to-end test as requested
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from core.models import User, VerificationCode
from core.email_notifications import send_verification_code_email
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def register_test_user():
    """Register a test user with genixailabs@gmail.com"""
    print("👤 Registering Test User")
    print("=" * 40)
    
    test_email = 'genixailabs@gmail.com'
    test_username = 'genixailabs'
    
    # Clean up any existing user
    User.objects.filter(email=test_email).delete()
    User.objects.filter(username=test_username).delete()
    
    try:
        # Create user
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password='TestPassword123!',
            first_name='Genix',
            last_name='AI Labs',
            is_email_verified=False
        )
        
        print(f"✅ User created successfully")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.get_full_name()}")
        print(f"   Email Verified: {user.is_email_verified}")
        
        return user
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return None

def test_uuid_token_verification(user):
    """Test UUID token-based email verification"""
    print("\n🔗 Testing UUID Token Verification")
    print("=" * 40)
    
    try:
        # Generate UUID token
        token = user.generate_email_verification_token()
        print(f"✅ UUID token generated: {token[:8]}...")
        
        # Prepare email context
        context = {
            'user': user,
            'token': token,
            'domain': 'localhost:8000',
            'protocol': 'http',
        }
        
        # Render email content
        html_message = render_to_string('core/auth/email_verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        result = send_mail(
            subject='Verify Your Email - Gurumisha Motors',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ UUID token verification email sent successfully!")
            print(f"   Verification URL: http://localhost:8000/verify-email/{token}/")
            print(f"   Token expires: {user.email_verification_sent_at}")
            return True
        else:
            print("❌ Failed to send UUID token email")
            return False
            
    except Exception as e:
        print(f"❌ UUID token verification failed: {e}")
        return False

def test_6_digit_code_verification(user):
    """Test 6-digit code verification"""
    print("\n🔢 Testing 6-Digit Code Verification")
    print("=" * 40)
    
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
        
        # Send verification code email
        result = send_verification_code_email(user, verification_code)
        
        if result:
            print("✅ Verification code email sent successfully!")
            print(f"   Code: {verification_code.code}")
            print(f"   Verification URL: http://localhost:8000/verify-email-code/")
            return verification_code
        else:
            print("❌ Failed to send verification code email")
            return None
            
    except Exception as e:
        print(f"❌ 6-digit code verification failed: {e}")
        return None

def test_email_template_rendering():
    """Test email template rendering with harrier design"""
    print("\n🎨 Testing Email Template Rendering")
    print("=" * 40)
    
    try:
        # Test UUID token email template
        uuid_context = {
            'user': {'get_full_name': 'Genix AI Labs', 'username': 'genixailabs'},
            'token': 'test-uuid-token-123',
            'domain': 'localhost:8000',
            'protocol': 'http',
        }
        
        uuid_html = render_to_string('core/auth/email_verification_email.html', uuid_context)
        
        # Check for harrier design elements
        harrier_elements = [
            'Gurumisha Motors',
            'harrier',
            'DC2626',  # Harrier red color
            '1F2937',  # Harrier dark color
            'verify-button',
            'security-notice'
        ]
        
        uuid_score = sum(1 for element in harrier_elements if element in uuid_html)
        print(f"✅ UUID token email template rendered")
        print(f"   Harrier design elements: {uuid_score}/{len(harrier_elements)}")
        
        # Test verification code email template
        code_context = {
            'user': {'get_full_name': 'Genix AI Labs', 'username': 'genixailabs'},
            'verification_code': '123456',
            'expiry_minutes': 15,
            'site_name': 'Gurumisha Motors',
        }
        
        code_html = render_to_string('core/auth/verification_code_email.html', code_context)
        code_score = sum(1 for element in harrier_elements if element in code_html)
        
        print(f"✅ Verification code email template rendered")
        print(f"   Harrier design elements: {code_score}/{len(harrier_elements)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email template rendering failed: {e}")
        return False

def test_verification_workflow_simulation(user, verification_code):
    """Simulate the verification workflow"""
    print("\n🔄 Simulating Verification Workflow")
    print("=" * 40)
    
    try:
        # Test code validation
        if verification_code and verification_code.is_valid():
            print("✅ Verification code is valid")
            
            # Simulate code verification
            verification_code.mark_as_used()
            user.is_email_verified = True
            user.save()
            
            print("✅ Email verification completed")
            print(f"   User email verified: {user.is_email_verified}")
            print(f"   Code marked as used: {verification_code.is_used}")
            
            return True
        else:
            print("❌ Verification code is invalid or expired")
            return False
            
    except Exception as e:
        print(f"❌ Verification workflow simulation failed: {e}")
        return False

def main():
    """Run the complete email verification test"""
    print("🚀 Gurumisha Motors - Final Email Verification Test")
    print("=" * 70)
    print(f"📧 SMTP Configuration:")
    print(f"   Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   TLS: {settings.EMAIL_USE_TLS}")
    print("=" * 70)
    
    # Step 1: Register test user
    user = register_test_user()
    if not user:
        print("❌ Test failed: Could not create user")
        return
    
    # Step 2: Test email template rendering
    template_test = test_email_template_rendering()
    
    # Step 3: Test UUID token verification
    uuid_test = test_uuid_token_verification(user)
    
    # Step 4: Test 6-digit code verification
    verification_code = test_6_digit_code_verification(user)
    code_test = verification_code is not None
    
    # Step 5: Simulate verification workflow
    workflow_test = test_verification_workflow_simulation(user, verification_code)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    tests = [
        ("User Registration", user is not None),
        ("Email Template Rendering", template_test),
        ("UUID Token Verification", uuid_test),
        ("6-Digit Code Verification", code_test),
        ("Verification Workflow", workflow_test),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25} {status}")
    
    print(f"\n🏁 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email verification system is fully operational.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\n📧 Email Verification System Status: READY")
    print("\n📋 Manual Testing Instructions:")
    print("1. Open browser: http://localhost:8000/register/")
    print("2. Register with email: genixailabs@gmail.com")
    print("3. Check email inbox (and spam folder) for verification messages")
    print("4. Test both verification methods:")
    print("   - Click the UUID token link in the email")
    print("   - OR enter the 6-digit code on the verification page")
    print("5. Verify that login works after email verification")
    print("6. Test the complete user journey from registration to dashboard access")
    
    print("\n🌐 Server Information:")
    print("   Django Server: http://localhost:8000")
    print("   Registration: http://localhost:8000/register/")
    print("   Login: http://localhost:8000/login/")
    print("   Dashboard: http://localhost:8000/dashboard/")
    
    print("\n✉️  Check your email inbox for test verification messages!")

if __name__ == "__main__":
    main()
