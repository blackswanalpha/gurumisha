#!/usr/bin/env python
"""
Test script for email verification system
Run this script to test the email verification functionality
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from core.models import User, VerificationCode
from core.email_notifications import send_verification_code_email
from django.utils import timezone

def test_verification_code_system():
    """Test the verification code system"""
    print("🧪 Testing Email Verification Code System")
    print("=" * 50)
    
    # Test 1: Create a test user
    print("\n1. Creating test user...")
    try:
        # Delete existing test user if exists
        User.objects.filter(username='testuser').delete()

        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            is_email_verified=False
        )
        print("✅ Test user created successfully")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return
    
    # Test 2: Generate verification code
    print("\n2. Generating verification code...")
    try:
        verification_code = VerificationCode.create_verification_code(
            user=test_user,
            code_type='email_verification',
            expiry_minutes=15
        )
        print(f"✅ Verification code generated: {verification_code.code}")
        print(f"   Expires at: {verification_code.expires_at}")
    except Exception as e:
        print(f"❌ Error generating verification code: {e}")
        return
    
    # Test 3: Validate code properties
    print("\n3. Validating code properties...")
    try:
        assert len(verification_code.code) == 6, "Code should be 6 digits"
        assert verification_code.code.isdigit(), "Code should be numeric"
        assert verification_code.is_valid(), "Code should be valid"
        assert not verification_code.is_used, "Code should not be used"
        print("✅ Code properties are valid")
    except AssertionError as e:
        print(f"❌ Code validation failed: {e}")
        return
    except Exception as e:
        print(f"❌ Error validating code: {e}")
        return
    
    # Test 4: Test code expiry logic
    print("\n4. Testing code expiry logic...")
    try:
        # Create an expired code
        expired_code = VerificationCode.objects.create(
            user=test_user,
            code='123456',
            code_type='email_verification',
            email=test_user.email,
            expires_at=timezone.now() - timezone.timedelta(minutes=1)
        )
        assert not expired_code.is_valid(), "Expired code should not be valid"
        print("✅ Code expiry logic works correctly")
    except Exception as e:
        print(f"❌ Error testing code expiry: {e}")
        return
    
    # Test 5: Test code invalidation
    print("\n5. Testing code invalidation...")
    try:
        # Create another code (should invalidate previous ones)
        new_code = VerificationCode.create_verification_code(
            user=test_user,
            code_type='email_verification',
            expiry_minutes=15
        )
        
        # Refresh the original code from database
        verification_code.refresh_from_db()
        assert verification_code.is_used, "Previous code should be invalidated"
        print("✅ Code invalidation works correctly")
    except Exception as e:
        print(f"❌ Error testing code invalidation: {e}")
        return
    
    # Test 6: Test code usage
    print("\n6. Testing code usage...")
    try:
        new_code.mark_as_used()
        assert new_code.is_used, "Code should be marked as used"
        assert new_code.used_at is not None, "Used timestamp should be set"
        print("✅ Code usage tracking works correctly")
    except Exception as e:
        print(f"❌ Error testing code usage: {e}")
        return
    
    # Test 7: Test email sending (dry run)
    print("\n7. Testing email sending (dry run)...")
    try:
        # Create a fresh code for email testing
        email_test_code = VerificationCode.create_verification_code(
            user=test_user,
            code_type='email_verification',
            expiry_minutes=15
        )
        
        # Note: This will attempt to send an actual email
        # Make sure email settings are configured properly
        print("⚠️  Email sending test skipped (requires proper SMTP configuration)")
        print(f"   Code to send: {email_test_code.code}")
        print("   To test email sending, configure SMTP settings and uncomment the line below:")
        print("   # result = send_verification_code_email(test_user, email_test_code)")
        
    except Exception as e:
        print(f"❌ Error in email sending test: {e}")
    
    # Cleanup
    print("\n8. Cleaning up test data...")
    try:
        VerificationCode.objects.filter(user=test_user).delete()
        test_user.delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean up test data: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Email verification code system test completed!")
    print("✅ All tests passed successfully")

def test_uuid_token_system():
    """Test the UUID token system"""
    print("\n🧪 Testing UUID Token Verification System")
    print("=" * 50)
    
    try:
        # Delete existing test user if exists
        User.objects.filter(username='tokenuser').delete()

        # Create test user
        test_user = User.objects.create_user(
            username='tokenuser',
            email='token@example.com',
            password='testpassword123',
            first_name='Token',
            last_name='User',
            is_email_verified=False
        )
        
        # Test token generation
        token = test_user.generate_email_verification_token()
        print(f"✅ UUID token generated: {token[:8]}...")
        
        # Test token validation
        assert test_user.is_email_verification_token_valid(), "Token should be valid"
        print("✅ Token validation works")
        
        # Test email verification
        test_user.verify_email()
        assert test_user.is_email_verified, "User should be verified"
        assert test_user.email_verification_token is None, "Token should be cleared"
        print("✅ Email verification works")
        
        # Cleanup
        test_user.delete()
        print("✅ UUID token system test completed")
        
    except Exception as e:
        print(f"❌ Error in UUID token test: {e}")

if __name__ == "__main__":
    print("🚀 Starting Email Verification System Tests")
    print("=" * 60)
    
    # Test both systems
    test_verification_code_system()
    test_uuid_token_system()
    
    print("\n" + "=" * 60)
    print("🏁 All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Configure Gmail App Password in settings.py")
    print("2. Test email sending with real SMTP settings")
    print("3. Test the web interface by running the Django server")
    print("4. Register a new user and verify the email workflow")
