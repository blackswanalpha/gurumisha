# Email Verification System - Gurumisha Motors

## Overview

The Gurumisha Motors Django application implements a comprehensive email verification system with two approaches:

1. **UUID Token-based Verification** (Primary - Already Implemented)
2. **6-Digit Code Verification** (Alternative - Newly Added)

## System Components

### 1. User Model Extensions

The `User` model includes email verification fields:

```python
class User(AbstractUser):
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
```

### 2. VerificationCode Model (New)

Alternative verification system using 6-digit codes:

```python
class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    code_type = models.CharField(max_length=20, choices=CODE_TYPES)
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
```

## Email Configuration

### Settings Configuration

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'kamandembugua18@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password-here'  # TODO: Replace with actual Gmail App Password
DEFAULT_FROM_EMAIL = 'Gurumisha Motors <kamandembugua18@gmail.com>'

# Email Verification Settings
EMAIL_VERIFICATION_TIMEOUT_HOURS = 24
EMAIL_VERIFICATION_REQUIRED = True
```

### Required Setup Steps

1. **Gmail App Password Setup:**
   - Enable 2-factor authentication on Gmail account
   - Generate an App Password for Django
   - Replace `'your-app-password-here'` with the actual App Password

2. **Production Settings:**
   - Update domain and protocol in email templates
   - Use HTTPS in production
   - Consider using environment variables for sensitive settings

## Verification Workflows

### UUID Token Workflow (Current)

1. **Registration:**
   - User registers with email
   - UUID token generated and stored
   - Email sent with verification link
   - User clicks link to verify

2. **Email Template:** `email_verification_email.html`
3. **Views:** `verify_email()`, `resend_verification_email()`
4. **URLs:** `/verify-email/<token>/`, `/resend-verification/`

### 6-Digit Code Workflow (New)

1. **Registration/Request:**
   - User requests verification code
   - 6-digit numeric code generated
   - Code expires in 15 minutes
   - Email sent with code

2. **Verification:**
   - User enters code on verification page
   - Code validated and marked as used
   - Email marked as verified

3. **Email Templates:**
   - `verification_code_email.html`
   - `password_reset_code_email.html`

4. **Views:**
   - `verify_email_with_code()`
   - `request_verification_code()`
   - `password_reset_with_code()`
   - `request_password_reset_code()`

5. **URLs:**
   - `/verify-email-code/`
   - `/request-verification-code/`
   - `/password-reset-code/`
   - `/request-password-reset-code/`

## Security Features

### Token Security
- UUID tokens expire after 24 hours
- Tokens are cleared after successful verification
- One-time use tokens

### Code Security
- 6-digit numeric codes
- 15-minute expiration
- Previous codes invalidated when new ones are generated
- Codes marked as used after verification

### Middleware Protection
- `EmailVerificationMiddleware` enforces verification
- Exempt URLs for public access
- Redirects unverified users to verification pages

## Email Templates

### Professional Design Features
- Harrier design system colors (red/black/dark blue/white)
- Responsive mobile-first design
- Clear call-to-action buttons
- Security notices and instructions
- Branded headers and footers

### Template Files
1. `email_verification_email.html` - UUID token verification
2. `verification_code_email.html` - 6-digit code verification
3. `password_reset_code_email.html` - Password reset codes
4. Various status pages (success, expired, invalid, etc.)

## Forms and Validation

### VerificationCodeForm
- 6-digit numeric input validation
- Real-time code verification
- User-friendly error messages
- Auto-formatting and focus

### RequestVerificationCodeForm
- Email validation
- User existence checking
- Code generation and sending

## Usage Examples

### Sending Verification Code

```python
from core.models import VerificationCode
from core.email_notifications import send_verification_code_email

# Create verification code
verification_code = VerificationCode.create_verification_code(
    user=user,
    code_type='email_verification',
    expiry_minutes=15
)

# Send email
send_verification_code_email(user, verification_code)
```

### Verifying Code

```python
# In view
form = VerificationCodeForm(request.POST, user=request.user)
if form.is_valid():
    if form.verify_and_mark_used():
        user.is_email_verified = True
        user.save()
```

## Database Migrations

Run migrations to create the VerificationCode model:

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Testing Recommendations

1. **Email Delivery Testing:**
   - Test with real Gmail account
   - Verify spam folder handling
   - Test email formatting across clients

2. **Code Validation Testing:**
   - Test expired codes
   - Test invalid codes
   - Test already used codes
   - Test multiple code requests

3. **Security Testing:**
   - Test token/code expiration
   - Test middleware protection
   - Test unauthorized access attempts

## Monitoring and Logging

- Email sending failures are logged
- Verification attempts are tracked
- Consider adding analytics for verification success rates

## Future Enhancements

1. **SMS Verification:** Extend system for SMS codes
2. **Two-Factor Authentication:** Use verification codes for 2FA
3. **Rate Limiting:** Prevent code request abuse
4. **Analytics Dashboard:** Track verification metrics
5. **Email Templates:** A/B testing for better conversion

## Troubleshooting

### Common Issues

1. **Emails not sending:**
   - Check Gmail App Password
   - Verify SMTP settings
   - Check firewall/network restrictions

2. **Codes not working:**
   - Check expiration times
   - Verify code generation logic
   - Check database constraints

3. **Template rendering issues:**
   - Verify template paths
   - Check context variables
   - Test email client compatibility

### Debug Commands

```bash
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

# Check verification codes
>>> from core.models import VerificationCode
>>> VerificationCode.objects.filter(is_used=False)
```

## Conclusion

The email verification system provides robust, secure, and user-friendly email verification with both traditional token-based and modern code-based approaches. The system is production-ready with proper security measures, professional email templates, and comprehensive error handling.
