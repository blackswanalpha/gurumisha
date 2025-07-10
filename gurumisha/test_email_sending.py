#!/usr/bin/env python
"""
Test script for email sending functionality
Run this script to test the SMTP configuration and email delivery
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

def test_basic_email_sending():
    """Test basic email sending functionality"""
    print("📧 Testing Basic Email Sending")
    print("=" * 40)
    
    try:
        result = send_mail(
            subject='Test Email - Gurumisha Motors',
            message='This is a test email to verify SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['genixailabs@gmail.com'],
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ Basic email sent successfully!")
            return True
        else:
            print("❌ Failed to send basic email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending basic email: {e}")
        return False

def test_html_email_sending():
    """Test HTML email sending"""
    print("\n📧 Testing HTML Email Sending")
    print("=" * 40)
    
    try:
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; padding: 30px;">
                <h1 style="color: #DC2626; text-align: center;">🚗 Gurumisha Motors</h1>
                <h2 style="color: #1F2937;">Email Configuration Test</h2>
                <p>This is a test HTML email to verify that the email configuration is working correctly.</p>
                <div style="background-color: #EFF6FF; border: 1px solid #3B82F6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1E40AF; margin-top: 0;">✅ Test Results:</h3>
                    <ul>
                        <li>SMTP Configuration: Working</li>
                        <li>HTML Email Rendering: Working</li>
                        <li>Email Delivery: Successful</li>
                    </ul>
                </div>
                <p style="text-align: center; margin-top: 30px;">
                    <strong>The Gurumisha Motors Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_content = strip_tags(html_content)
        
        result = send_mail(
            subject='HTML Email Test - Gurumisha Motors',
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['genixailabs@gmail.com'],
            html_message=html_content,
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ HTML email sent successfully!")
            return True
        else:
            print("❌ Failed to send HTML email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending HTML email: {e}")
        return False

def test_verification_code_email():
    """Test verification code email sending"""
    print("\n📧 Testing Verification Code Email")
    print("=" * 40)
    
    try:
        # Create or get test user
        test_user, created = User.objects.get_or_create(
            email='genixailabs@gmail.com',
            defaults={
                'username': 'testuser_genix',
                'first_name': 'Test',
                'last_name': 'User',
                'is_email_verified': False
            }
        )
        
        if created:
            test_user.set_password('testpassword123')
            test_user.save()
            print("✅ Test user created")
        else:
            print("✅ Using existing test user")
        
        # Generate verification code
        verification_code = VerificationCode.create_verification_code(
            user=test_user,
            code_type='email_verification',
            expiry_minutes=15
        )
        
        print(f"✅ Verification code generated: {verification_code.code}")
        
        # Send verification code email
        result = send_verification_code_email(test_user, verification_code)
        
        if result:
            print("✅ Verification code email sent successfully!")
            print(f"   Code: {verification_code.code}")
            print(f"   Expires: {verification_code.expires_at}")
            return True
        else:
            print("❌ Failed to send verification code email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending verification code email: {e}")
        return False

def test_uuid_token_email():
    """Test UUID token verification email"""
    print("\n📧 Testing UUID Token Verification Email")
    print("=" * 40)
    
    try:
        # Get or create test user
        test_user, created = User.objects.get_or_create(
            email='genixailabs@gmail.com',
            defaults={
                'username': 'testuser_genix_uuid',
                'first_name': 'Test',
                'last_name': 'User UUID',
                'is_email_verified': False
            }
        )
        
        # Generate UUID token
        token = test_user.generate_email_verification_token()
        print(f"✅ UUID token generated: {token[:8]}...")
        
        # Prepare email context
        context = {
            'user': test_user,
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
            recipient_list=[test_user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result == 1:
            print("✅ UUID token verification email sent successfully!")
            print(f"   Token: {token[:8]}...")
            print(f"   Verification URL: http://localhost:8000/verify-email/{token}/")
            return True
        else:
            print("❌ Failed to send UUID token email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending UUID token email: {e}")
        return False

def main():
    """Run all email tests"""
    print("🚀 Starting Email Verification System Tests")
    print("=" * 60)
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"📧 Test Recipient: genixailabs@gmail.com")
    print("=" * 60)
    
    tests = [
        test_basic_email_sending,
        test_html_email_sending,
        test_verification_code_email,
        test_uuid_token_email
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Email Tests Completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All email tests passed! Email verification system is ready.")
        print("\n📋 Next Steps:")
        print("1. Start Django server: python3 manage.py runserver")
        print("2. Navigate to: http://localhost:8000/register/")
        print("3. Register with email: genixailabs@gmail.com")
        print("4. Check email for verification messages")
    else:
        print("⚠️  Some email tests failed. Please check SMTP configuration.")
    
    print("\n📧 Check your email inbox (and spam folder) for test messages!")

if __name__ == "__main__":
    main()
