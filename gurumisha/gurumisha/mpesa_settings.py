"""
M-Pesa Configuration Settings for Gurumisha Motors
This file contains all M-Pesa related configuration settings
"""

import os
from django.conf import settings

# M-Pesa API Configuration
# These should be set in your environment variables or Django settings

# Sandbox Configuration (for testing)
MPESA_SANDBOX_CONSUMER_KEY = os.getenv('MPESA_SANDBOX_CONSUMER_KEY', '')
MPESA_SANDBOX_CONSUMER_SECRET = os.getenv('MPESA_SANDBOX_CONSUMER_SECRET', '')
MPESA_SANDBOX_BUSINESS_SHORT_CODE = os.getenv('MPESA_SANDBOX_BUSINESS_SHORT_CODE', '174379')
MPESA_SANDBOX_PASSKEY = os.getenv('MPESA_SANDBOX_PASSKEY', '')

# Production Configuration
MPESA_PRODUCTION_CONSUMER_KEY = os.getenv('MPESA_PRODUCTION_CONSUMER_KEY', '')
MPESA_PRODUCTION_CONSUMER_SECRET = os.getenv('MPESA_PRODUCTION_CONSUMER_SECRET', '')
MPESA_PRODUCTION_BUSINESS_SHORT_CODE = os.getenv('MPESA_PRODUCTION_BUSINESS_SHORT_CODE', '')
MPESA_PRODUCTION_PASSKEY = os.getenv('MPESA_PRODUCTION_PASSKEY', '')

# Environment setting (sandbox or production)
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')

# Callback URLs
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://yourdomain.com/payments/mpesa/callback/')
MPESA_TIMEOUT_URL = os.getenv('MPESA_TIMEOUT_URL', 'https://yourdomain.com/payments/mpesa/timeout/')

# Current configuration based on environment
if MPESA_ENVIRONMENT == 'production':
    MPESA_CONSUMER_KEY = MPESA_PRODUCTION_CONSUMER_KEY
    MPESA_CONSUMER_SECRET = MPESA_PRODUCTION_CONSUMER_SECRET
    MPESA_BUSINESS_SHORT_CODE = MPESA_PRODUCTION_BUSINESS_SHORT_CODE
    MPESA_PASSKEY = MPESA_PRODUCTION_PASSKEY
else:
    MPESA_CONSUMER_KEY = MPESA_SANDBOX_CONSUMER_KEY
    MPESA_CONSUMER_SECRET = MPESA_SANDBOX_CONSUMER_SECRET
    MPESA_BUSINESS_SHORT_CODE = MPESA_SANDBOX_BUSINESS_SHORT_CODE
    MPESA_PASSKEY = MPESA_SANDBOX_PASSKEY

# API URLs
MPESA_BASE_URL = {
    'sandbox': 'https://sandbox.safaricom.co.ke',
    'production': 'https://api.safaricom.co.ke'
}

# API Endpoints
MPESA_ENDPOINTS = {
    'oauth': '/oauth/v1/generate?grant_type=client_credentials',
    'stk_push': '/mpesa/stkpush/v1/processrequest',
    'stk_query': '/mpesa/stkpushquery/v1/query',
    'b2c': '/mpesa/b2c/v1/paymentrequest',
    'account_balance': '/mpesa/accountbalance/v1/query',
    'transaction_status': '/mpesa/transactionstatus/v1/query'
}

# Transaction Types
MPESA_TRANSACTION_TYPES = {
    'customer_paybill': 'CustomerPayBillOnline',
    'customer_buygoods': 'CustomerBuyGoodsOnline',
    'business_paybill': 'BusinessPayBill',
    'business_buygoods': 'BusinessBuyGoods',
    'salary_payment': 'SalaryPayment',
    'business_payment': 'BusinessPayment',
    'promotion_payment': 'PromotionPayment'
}

# Default transaction settings
MPESA_DEFAULT_TRANSACTION_TYPE = MPESA_TRANSACTION_TYPES['customer_paybill']
MPESA_DEFAULT_ACCOUNT_REFERENCE = 'GURUMISHA'
MPESA_DEFAULT_TRANSACTION_DESC = 'Payment for Gurumisha Motors'

# Timeout settings (in seconds)
MPESA_REQUEST_TIMEOUT = 30
MPESA_TOKEN_CACHE_TIMEOUT = 3600  # 1 hour

# Logging configuration
MPESA_ENABLE_LOGGING = True
MPESA_LOG_LEVEL = 'INFO'

# Validation settings
MPESA_PHONE_NUMBER_REGEX = r'^254[0-9]{9}$'
MPESA_MIN_AMOUNT = 1
MPESA_MAX_AMOUNT = 70000

# Error messages
MPESA_ERROR_MESSAGES = {
    'invalid_phone': 'Please enter a valid Kenyan phone number (254XXXXXXXXX)',
    'invalid_amount': f'Amount must be between KSh {MPESA_MIN_AMOUNT} and KSh {MPESA_MAX_AMOUNT}',
    'payment_failed': 'Payment failed. Please try again.',
    'payment_cancelled': 'Payment was cancelled by user.',
    'payment_timeout': 'Payment request timed out. Please try again.',
    'insufficient_funds': 'Insufficient funds in your M-Pesa account.',
    'invalid_pin': 'Invalid M-Pesa PIN entered.',
    'user_cancelled': 'Payment was cancelled by user.',
    'duplicate_request': 'Duplicate payment request detected.',
    'system_error': 'System error occurred. Please try again later.'
}

# Response codes mapping
MPESA_RESPONSE_CODES = {
    '0': 'Success',
    '1': 'Insufficient Funds',
    '2': 'Less Than Minimum Transaction Value',
    '3': 'More Than Maximum Transaction Value',
    '4': 'Would Exceed Daily Transfer Limit',
    '5': 'Would Exceed Minimum Balance',
    '6': 'Unresolved Primary Party',
    '7': 'Unresolved Receiver Party',
    '8': 'Would Exceed Maximum Balance',
    '11': 'Debit Account Invalid',
    '12': 'Credit Account Invalid',
    '13': 'Unresolved Debit Account',
    '14': 'Unresolved Credit Account',
    '15': 'Duplicate Detected',
    '17': 'Internal Failure',
    '20': 'Unresolved Initiator',
    '26': 'Traffic Blocking Condition In Place',
    '1001': 'Duplicate Detected',
    '1019': 'Initiator Authentication Error',
    '1032': 'Request Cancelled By User',
    '1037': 'DS Timeout User Cannot Be Reached',
    '2001': 'Invalid Initiator Information',
    '9999': 'Request Cancelled By User'
}

# Success response codes
MPESA_SUCCESS_CODES = ['0']

# User cancellation codes
MPESA_USER_CANCELLED_CODES = ['1032', '1037', '9999']

# Insufficient funds codes
MPESA_INSUFFICIENT_FUNDS_CODES = ['1']

# System error codes
MPESA_SYSTEM_ERROR_CODES = ['17', '26', '2001']

def get_mpesa_config():
    """
    Get current M-Pesa configuration
    """
    return {
        'consumer_key': MPESA_CONSUMER_KEY,
        'consumer_secret': MPESA_CONSUMER_SECRET,
        'business_short_code': MPESA_BUSINESS_SHORT_CODE,
        'passkey': MPESA_PASSKEY,
        'environment': MPESA_ENVIRONMENT,
        'callback_url': MPESA_CALLBACK_URL,
        'timeout_url': MPESA_TIMEOUT_URL,
        'base_url': MPESA_BASE_URL[MPESA_ENVIRONMENT],
        'endpoints': MPESA_ENDPOINTS,
        'transaction_type': MPESA_DEFAULT_TRANSACTION_TYPE,
        'account_reference': MPESA_DEFAULT_ACCOUNT_REFERENCE,
        'transaction_desc': MPESA_DEFAULT_TRANSACTION_DESC
    }

def is_mpesa_configured():
    """
    Check if M-Pesa is properly configured
    """
    required_settings = [
        MPESA_CONSUMER_KEY,
        MPESA_CONSUMER_SECRET,
        MPESA_BUSINESS_SHORT_CODE,
        MPESA_PASSKEY,
        MPESA_CALLBACK_URL
    ]
    
    return all(setting for setting in required_settings)

def validate_phone_number(phone_number):
    """
    Validate Kenyan phone number format
    """
    import re
    
    # Remove any spaces or special characters
    phone_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Convert to 254 format
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+254'):
        phone_number = phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    # Validate format
    if re.match(MPESA_PHONE_NUMBER_REGEX, phone_number):
        return phone_number
    else:
        return None

def validate_amount(amount):
    """
    Validate transaction amount
    """
    try:
        amount = float(amount)
        if MPESA_MIN_AMOUNT <= amount <= MPESA_MAX_AMOUNT:
            return amount
        else:
            return None
    except (ValueError, TypeError):
        return None

def get_error_message(response_code):
    """
    Get user-friendly error message for response code
    """
    return MPESA_RESPONSE_CODES.get(str(response_code), MPESA_ERROR_MESSAGES['system_error'])

def is_success_response(response_code):
    """
    Check if response code indicates success
    """
    return str(response_code) in MPESA_SUCCESS_CODES

def is_user_cancelled(response_code):
    """
    Check if response code indicates user cancellation
    """
    return str(response_code) in MPESA_USER_CANCELLED_CODES

def is_insufficient_funds(response_code):
    """
    Check if response code indicates insufficient funds
    """
    return str(response_code) in MPESA_INSUFFICIENT_FUNDS_CODES

def is_system_error(response_code):
    """
    Check if response code indicates system error
    """
    return str(response_code) in MPESA_SYSTEM_ERROR_CODES

# Example environment variables file (.env)
EXAMPLE_ENV_VARIABLES = """
# M-Pesa Sandbox Configuration
MPESA_SANDBOX_CONSUMER_KEY=your_sandbox_consumer_key
MPESA_SANDBOX_CONSUMER_SECRET=your_sandbox_consumer_secret
MPESA_SANDBOX_BUSINESS_SHORT_CODE=174379
MPESA_SANDBOX_PASSKEY=your_sandbox_passkey

# M-Pesa Production Configuration
MPESA_PRODUCTION_CONSUMER_KEY=your_production_consumer_key
MPESA_PRODUCTION_CONSUMER_SECRET=your_production_consumer_secret
MPESA_PRODUCTION_BUSINESS_SHORT_CODE=your_production_shortcode
MPESA_PRODUCTION_PASSKEY=your_production_passkey

# Environment (sandbox or production)
MPESA_ENVIRONMENT=sandbox

# Callback URLs
MPESA_CALLBACK_URL=https://yourdomain.com/payments/mpesa/callback/
MPESA_TIMEOUT_URL=https://yourdomain.com/payments/mpesa/timeout/
"""
