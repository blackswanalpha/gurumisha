# M-Pesa Integration Setup Guide

This guide will help you set up M-Pesa integration for the Gurumisha Motors project.

## 🚀 Quick Setup

### 1. Environment Configuration

Copy the example environment file and configure your M-Pesa credentials:

```bash
cp .env.example .env
```

### 2. Get M-Pesa Credentials

#### For Sandbox Testing:
1. Visit [Safaricom Developer Portal](https://developer.safaricom.co.ke/)
2. Create an account and log in
3. Create a new app for testing
4. Get your sandbox credentials:
   - Consumer Key
   - Consumer Secret
   - Passkey
   - Business Short Code (usually 174379 for sandbox)

#### For Production:
1. Contact Safaricom to get production credentials
2. Complete the integration testing process
3. Get your production credentials

### 3. Configure Environment Variables

Update your `.env` file with your actual M-Pesa credentials:

```env
# M-Pesa Sandbox Configuration
MPESA_SANDBOX_CONSUMER_KEY=your_actual_consumer_key
MPESA_SANDBOX_CONSUMER_SECRET=your_actual_consumer_secret
MPESA_SANDBOX_BUSINESS_SHORT_CODE=174379
MPESA_SANDBOX_PASSKEY=your_actual_passkey

# M-Pesa Environment
MPESA_ENVIRONMENT=sandbox

# Callback URLs (for development)
MPESA_CALLBACK_URL=https://your-ngrok-url.ngrok.io/payments/mpesa/callback/
MPESA_TIMEOUT_URL=https://your-ngrok-url.ngrok.io/payments/mpesa/timeout/
```

### 4. Set Up Callback URLs for Development

Since M-Pesa needs to send callbacks to your application, you need a public URL for development:

#### Option 1: Using ngrok (Recommended)
```bash
# Install ngrok
npm install -g ngrok

# Start your Django server
python manage.py runserver

# In another terminal, expose your local server
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Update your .env file with this URL
```

#### Option 2: Using localtunnel
```bash
# Install localtunnel
npm install -g localtunnel

# Start your Django server
python manage.py runserver

# In another terminal
lt --port 8000

# Copy the URL and update your .env file
```

### 5. Install Dependencies

Make sure you have the required dependencies:

```bash
pip install python-decouple requests
```

## 🧪 Testing M-Pesa Integration

### 1. Test Configuration

Run this command to check if M-Pesa is properly configured:

```python
# In Django shell
python manage.py shell

from core.mpesa_integration import MPesaAPI
mpesa = MPesaAPI()
print("M-Pesa configured:", mpesa.config.is_configured)
print("Environment:", mpesa.config.environment)
print("Business Short Code:", mpesa.config.business_short_code)
```

### 2. Test STK Push

```python
# In Django shell
from core.mpesa_integration import MPesaAPI

mpesa = MPesaAPI()
result = mpesa.initiate_stk_push(
    phone_number="254708374149",  # Use your test phone number
    amount=1,
    account_reference="TEST123",
    transaction_desc="Test Payment"
)
print(result)
```

### 3. Test with Spare Parts Purchase

1. Add items to cart
2. Go to checkout
3. Select M-Pesa payment method
4. Enter your phone number (254XXXXXXXXX format)
5. Complete payment on your phone
6. Check order status

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MPESA_ENVIRONMENT` | sandbox or production | `sandbox` |
| `MPESA_SANDBOX_CONSUMER_KEY` | Sandbox consumer key | `abc123...` |
| `MPESA_SANDBOX_CONSUMER_SECRET` | Sandbox consumer secret | `def456...` |
| `MPESA_SANDBOX_PASSKEY` | Sandbox passkey | `ghi789...` |
| `MPESA_CALLBACK_URL` | Callback URL for payment notifications | `https://yourdomain.com/payments/mpesa/callback/` |

### API Endpoints

The following M-Pesa endpoints are configured:

- **OAuth**: `/oauth/v1/generate?grant_type=client_credentials`
- **STK Push**: `/mpesa/stkpush/v1/processrequest`
- **STK Query**: `/mpesa/stkpushquery/v1/query`
- **B2C**: `/mpesa/b2c/v1/paymentrequest`

### Transaction Types

- `CustomerPayBillOnline` - For paybill transactions
- `CustomerBuyGoodsOnline` - For till number transactions

## 🚨 Troubleshooting

### Common Issues

1. **"M-Pesa is not properly configured"**
   - Check your environment variables
   - Ensure all required credentials are set
   - Verify the environment (sandbox/production)

2. **"Failed to get M-Pesa access token"**
   - Check your consumer key and secret
   - Verify internet connection
   - Check if credentials are for the correct environment

3. **"Invalid phone number format"**
   - Use format: 254XXXXXXXXX (Kenyan numbers only)
   - Remove spaces and special characters

4. **Callback not received**
   - Ensure callback URL is publicly accessible
   - Check if ngrok/localtunnel is running
   - Verify callback URL in environment variables

### Debug Mode

Enable debug logging by setting:

```env
LOG_LEVEL=DEBUG
MPESA_ENABLE_LOGGING=True
```

### Test Phone Numbers

For sandbox testing, use these test phone numbers:
- `254708374149`
- `254792823173`

## 🔒 Security Best Practices

1. **Never commit credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Use HTTPS for callback URLs in production**
4. **Validate all incoming callback data**
5. **Implement proper error handling**
6. **Log all transactions for audit purposes**

## 📚 Additional Resources

- [Safaricom Developer Portal](https://developer.safaricom.co.ke/)
- [M-Pesa API Documentation](https://developer.safaricom.co.ke/docs)
- [M-Pesa Sandbox Testing](https://developer.safaricom.co.ke/test_credentials)

## 🆘 Support

If you encounter issues:

1. Check the Django logs for error messages
2. Verify your M-Pesa credentials
3. Test with the provided test phone numbers
4. Ensure your callback URL is accessible
5. Contact Safaricom support for API-related issues
