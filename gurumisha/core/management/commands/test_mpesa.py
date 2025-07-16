"""
Django management command to test M-Pesa integration
Usage: python manage.py test_mpesa [--full]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from core.mpesa_integration import MPesaAPI, MPesaConfig
import json


class Command(BaseCommand):
    help = 'Test M-Pesa integration configuration and functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full integration test including STK Push',
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='254708374149',
            help='Phone number for STK Push test (default: 254708374149)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 M-Pesa Integration Test Suite')
        )
        self.stdout.write('=' * 50)

        # Test configuration
        self.test_configuration()
        
        # Test access token
        if self.test_access_token():
            # Test password generation
            self.test_password_generation()
            
            # Test STK Push if requested
            if options['full']:
                self.test_stk_push(options['phone'])
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('✅ M-Pesa test completed!')
        )

    def test_configuration(self):
        """Test M-Pesa configuration"""
        self.stdout.write('\n🔧 Testing M-Pesa Configuration...')
        self.stdout.write('-' * 50)
        
        config = MPesaConfig()
        
        self.stdout.write(f"Environment: {config.environment}")
        self.stdout.write(f"Business Short Code: {config.business_short_code}")
        
        # Check credentials without exposing them
        consumer_key_status = '✓ Set' if config.consumer_key else '✗ Missing'
        consumer_secret_status = '✓ Set' if config.consumer_secret else '✗ Missing'
        passkey_status = '✓ Set' if config.passkey else '✗ Missing'
        
        self.stdout.write(f"Consumer Key: {consumer_key_status}")
        self.stdout.write(f"Consumer Secret: {consumer_secret_status}")
        self.stdout.write(f"Passkey: {passkey_status}")
        self.stdout.write(f"Callback URL: {config.callback_url}")
        self.stdout.write(f"Timeout URL: {config.timeout_url}")
        self.stdout.write(f"Base URL: {config.base_url}")
        
        if config.is_configured:
            self.stdout.write(
                self.style.SUCCESS('✓ Configuration is complete')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Configuration is incomplete')
            )
            self.stdout.write(
                self.style.WARNING('Please check your .env file and ensure all M-Pesa credentials are set')
            )
        
        return config.is_configured

    def test_access_token(self):
        """Test M-Pesa access token generation"""
        self.stdout.write('\n🔑 Testing Access Token Generation...')
        self.stdout.write('-' * 50)
        
        try:
            mpesa = MPesaAPI()
            token = mpesa.get_access_token()
            
            if token:
                self.stdout.write(
                    self.style.SUCCESS('✓ Access token generated successfully')
                )
                self.stdout.write(f"Token (first 20 chars): {token[:20]}...")
                return True
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to generate access token')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error generating access token: {str(e)}')
            )
            return False

    def test_password_generation(self):
        """Test M-Pesa password generation"""
        self.stdout.write('\n🔐 Testing Password Generation...')
        self.stdout.write('-' * 50)
        
        try:
            mpesa = MPesaAPI()
            password, timestamp = mpesa.generate_password()
            
            self.stdout.write(
                self.style.SUCCESS('✓ Password generated successfully')
            )
            self.stdout.write(f"Timestamp: {timestamp}")
            self.stdout.write(f"Password (first 20 chars): {password[:20]}...")
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error generating password: {str(e)}')
            )
            return False

    def test_stk_push(self, phone_number):
        """Test STK Push functionality"""
        self.stdout.write('\n📱 Testing STK Push...')
        self.stdout.write('-' * 50)
        
        # Confirm before sending actual STK Push
        self.stdout.write(
            self.style.WARNING(f'⚠️  This will send an actual STK Push to {phone_number}')
        )
        confirm = input('Continue? (y/N): ')
        
        if confirm.lower() != 'y':
            self.stdout.write('STK Push test cancelled')
            return False
        
        test_amount = 1  # Minimum amount
        
        try:
            mpesa = MPesaAPI()
            result = mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount=test_amount,
                account_reference="TEST123",
                transaction_desc="Test Payment"
            )
            
            self.stdout.write('STK Push Result:')
            self.stdout.write(json.dumps(result, indent=2))
            
            if result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS('✓ STK Push initiated successfully')
                )
                self.stdout.write(
                    self.style.WARNING('📱 Please check your phone and complete the payment')
                )
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ STK Push failed: {result.get("message")}')
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error initiating STK Push: {str(e)}')
            )
            return False

    def style_text(self, text, style_func):
        """Helper to style text"""
        return style_func(text)
