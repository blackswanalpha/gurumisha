"""
Enhanced M-Pesa Integration for Gurumisha Motors Spare Parts System
Provides comprehensive M-Pesa payment processing with Safaricom API integration
"""

import base64
import json
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def get_callback_url(request=None):
    """
    Generate proper callback URL based on environment
    """
    from django.contrib.sites.models import Site

    # Try to get from settings first
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')

    if callback_url and callback_url != 'https://yourdomain.com/payments/mpesa/callback/':
        return callback_url

    # Generate callback URL dynamically
    try:
        if request:
            # Use request to build absolute URL
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            callback_path = reverse('core:mpesa_callback')
            return f"{scheme}://{host}{callback_path}"
        else:
            # Fallback to site domain
            try:
                site = Site.objects.get_current()
                scheme = 'https' if not settings.DEBUG else 'http'
                callback_path = reverse('core:mpesa_callback')
                return f"{scheme}://{site.domain}{callback_path}"
            except:
                # Final fallback
                return 'https://yourdomain.com/payments/mpesa/callback/'
    except:
        return callback_url or 'https://yourdomain.com/payments/mpesa/callback/'


def get_timeout_url(request=None):
    """
    Generate proper timeout URL based on environment
    """
    from django.contrib.sites.models import Site

    # Try to get from settings first
    timeout_url = getattr(settings, 'MPESA_TIMEOUT_URL', '')

    if timeout_url and timeout_url != 'https://yourdomain.com/payments/mpesa/timeout/':
        return timeout_url

    # Generate timeout URL dynamically
    try:
        if request:
            # Use request to build absolute URL
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            timeout_path = reverse('core:mpesa_timeout')
            return f"{scheme}://{host}{timeout_path}"
        else:
            # Fallback to site domain
            try:
                site = Site.objects.get_current()
                scheme = 'https' if not settings.DEBUG else 'http'
                timeout_path = reverse('core:mpesa_timeout')
                return f"{scheme}://{site.domain}{timeout_path}"
            except:
                # Final fallback
                return 'https://yourdomain.com/payments/mpesa/timeout/'
    except:
        return timeout_url or 'https://yourdomain.com/payments/mpesa/timeout/'


class MPesaConfig:
    """M-Pesa configuration settings"""
    
    # Sandbox URLs (change to production for live environment)
    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
    
    # API Endpoints
    OAUTH_URL = "/oauth/v1/generate?grant_type=client_credentials"
    STK_PUSH_URL = "/mpesa/stkpush/v1/processrequest"
    STK_QUERY_URL = "/mpesa/stkpushquery/v1/query"
    
    def __init__(self, request=None):
        # Get settings from Django settings
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_short_code = getattr(settings, 'MPESA_BUSINESS_SHORT_CODE', '174379')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = get_callback_url(request)
        self.timeout_url = get_timeout_url(request)
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')

        # Set base URL based on environment
        self.base_url = self.PRODUCTION_BASE_URL if self.environment == 'production' else self.SANDBOX_BASE_URL
    
    @property
    def is_configured(self):
        """Check if M-Pesa is properly configured"""
        return all([
            self.consumer_key,
            self.consumer_secret,
            self.business_short_code,
            self.passkey,
            self.callback_url
        ])


class MPesaAPI:
    """M-Pesa API integration class"""

    def __init__(self, request=None):
        self.config = MPesaConfig(request)
        
    def get_access_token(self):
        """Get OAuth access token from Safaricom API"""
        cache_key = 'mpesa_access_token'
        token = cache.get(cache_key)
        
        if token:
            return token
            
        try:
            # Create authorization header
            credentials = f"{self.config.consumer_key}:{self.config.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.config.base_url}{self.config.OAUTH_URL}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = int(token_data.get('expires_in', 3600))
                
                # Cache token for slightly less than expiry time
                cache.set(cache_key, access_token, expires_in - 60)
                
                logger.info("M-Pesa access token obtained successfully")
                return access_token
            else:
                logger.error(f"Failed to get M-Pesa access token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting M-Pesa access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.config.business_short_code}{self.config.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push payment"""
        if not self.config.is_configured:
            return {
                'success': False,
                'message': 'M-Pesa is not properly configured'
            }
        
        access_token = self.get_access_token()
        if not access_token:
            return {
                'success': False,
                'message': 'Failed to get M-Pesa access token'
            }
        
        try:
            password, timestamp = self.generate_password()
            
            # Format phone number (ensure it starts with 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            payload = {
                "BusinessShortCode": self.config.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.config.business_short_code,
                "PhoneNumber": phone_number,
                "CallBackURL": self.config.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.config.base_url}{self.config.STK_PUSH_URL}",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('ResponseCode') == '0':
                    logger.info(f"STK push initiated successfully for {phone_number}")
                    return {
                        'success': True,
                        'message': 'STK push sent successfully',
                        'checkout_request_id': response_data.get('CheckoutRequestID'),
                        'merchant_request_id': response_data.get('MerchantRequestID'),
                        'response_code': response_data.get('ResponseCode'),
                        'response_description': response_data.get('ResponseDescription')
                    }
                else:
                    logger.error(f"STK push failed: {response_data}")
                    return {
                        'success': False,
                        'message': response_data.get('ResponseDescription', 'STK push failed')
                    }
            else:
                logger.error(f"STK push request failed: {response.text}")
                return {
                    'success': False,
                    'message': 'Failed to initiate payment'
                }
                
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return {
                'success': False,
                'message': f'Payment initiation error: {str(e)}'
            }
    
    def query_stk_status(self, checkout_request_id):
        """Query STK push transaction status"""
        access_token = self.get_access_token()
        if not access_token:
            return {
                'success': False,
                'message': 'Failed to get access token'
            }
        
        try:
            password, timestamp = self.generate_password()
            
            payload = {
                "BusinessShortCode": self.config.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.config.base_url}{self.config.STK_QUERY_URL}",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to query transaction status'
                }
                
        except Exception as e:
            logger.error(f"Error querying STK status: {str(e)}")
            return {
                'success': False,
                'message': f'Query error: {str(e)}'
            }


def process_mpesa_callback(callback_data):
    """Process M-Pesa callback data"""
    try:
        from .models import Payment, Order
        
        # Extract callback information
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        if not checkout_request_id:
            logger.error("No CheckoutRequestID in callback data")
            return False
        
        # Find the payment record
        try:
            payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for CheckoutRequestID: {checkout_request_id}")
            return False
        
        # Update payment based on result code
        if result_code == 0:  # Success
            # Extract transaction details
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            transaction_data = {}
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'MpesaReceiptNumber':
                    transaction_data['receipt_number'] = value
                elif name == 'TransactionDate':
                    transaction_data['transaction_date'] = value
                elif name == 'PhoneNumber':
                    transaction_data['phone_number'] = value
                elif name == 'Amount':
                    transaction_data['amount'] = value
            
            # Update payment record
            payment.status = 'completed'
            payment.mpesa_receipt_number = transaction_data.get('receipt_number', '')
            payment.mpesa_transaction_id = transaction_data.get('receipt_number', '')
            payment.completed_at = timezone.now()
            payment.gateway_response = callback_data
            payment.save()
            
            # Update order status
            order = payment.order
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()
            
            logger.info(f"Payment completed successfully: {payment.payment_id}")
            return True
            
        else:  # Failed
            payment.status = 'failed'
            payment.failure_reason = result_desc
            payment.gateway_response = callback_data
            payment.save()
            
            logger.error(f"Payment failed: {payment.payment_id} - {result_desc}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {str(e)}")
        return False


# Convenience functions
def initiate_mpesa_payment(order, phone_number, request=None):
    """Convenience function to initiate M-Pesa payment for an order"""
    mpesa = MPesaAPI(request)

    account_reference = f"ORDER-{order.order_number}"
    transaction_desc = f"Payment for Order {order.order_number}"

    return mpesa.initiate_stk_push(
        phone_number=phone_number,
        amount=order.total_amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc
    )


def check_mpesa_status(checkout_request_id, request=None):
    """Convenience function to check M-Pesa transaction status"""
    mpesa = MPesaAPI(request)
    return mpesa.query_stk_status(checkout_request_id)
