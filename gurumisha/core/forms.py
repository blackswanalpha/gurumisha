from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import User, Vendor, Car, ImportRequest, Inquiry, VerificationCode
from .email_notifications import send_verification_code_email


class CustomUserRegistrationForm(UserCreationForm):
    """Custom user registration form with additional fields"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your phone number (optional)'
        })
    )
    # Public registration role choices (excluding admin)
    PUBLIC_ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ]

    role = forms.ChoiceField(
        choices=PUBLIC_ROLE_CHOICES,
        initial='customer',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
        }),
        help_text='Choose "Customer" to buy cars and request imports, or "Vendor" to sell cars and parts.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']
        user.is_email_verified = False  # Require email verification
        if commit:
            user.save()
            # Send email verification
            self.send_verification_email(user)
        return user

    def send_verification_email(self, user):
        """Send email verification email to the user"""
        try:
            # Generate verification token
            token = user.generate_email_verification_token()

            # Prepare email context
            context = {
                'user': user,
                'token': token,
                'domain': 'localhost:8000',  # Update this for production
                'protocol': 'http',  # Update to https for production
            }

            # Render email content
            html_message = render_to_string('core/auth/email_verification_email.html', context)
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject='Verify Your Email - Gurumisha Motors',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't prevent user creation
            print(f"Failed to send verification email: {e}")


class CustomLoginForm(AuthenticationForm):
    """Custom login form with styling"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow login with email
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username


class SellCarForm(forms.ModelForm):
    """Form for selling a car"""
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'condition', 'engine_size', 'fuel_type',
            'transmission', 'mileage', 'color', 'price', 'title', 'description',
            'features', 'main_image'
        ]
        widgets = {
            'brand': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
            }),
            'model': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'min': '1990',
                'max': '2025'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
            }),
            'engine_size': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., 2.0L, 1800cc'
            }),
            'fuel_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
            }),
            'transmission': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'Mileage in kilometers'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., White, Black, Silver'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'Price in KES'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., 2020 Toyota Camry - Excellent Condition'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'rows': 5,
                'placeholder': 'Describe your car in detail...'
            }),
            'features': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'rows': 3,
                'placeholder': 'List features separated by commas (e.g., Air Conditioning, Power Steering, ABS)'
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'accept': 'image/*'
            })
        }


class ImportRequestForm(forms.ModelForm):
    """Form for car import requests"""
    class Meta:
        model = ImportRequest
        fields = [
            'brand', 'model', 'year', 'preferred_color', 'origin_country',
            'budget_min', 'budget_max', 'special_requirements'
        ]
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., Toyota, Honda, BMW'
            }),
            'model': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., Camry, Civic, X5'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'min': '2000',
                'max': '2025'
            }),
            'preferred_color': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., White, Black, Silver (optional)'
            }),
            'origin_country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'e.g., Japan, Germany, UK'
            }),
            'budget_min': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'Minimum budget in KES'
            }),
            'budget_max': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'placeholder': 'Maximum budget in KES'
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
                'rows': 4,
                'placeholder': 'Any specific requirements or preferences...'
            })
        }


class ContactForm(forms.Form):
    """Contact form"""
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Your first name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Your last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Your email address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Your phone number (optional)'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'placeholder': 'Subject of your message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent transition-all duration-200',
            'rows': 6,
            'placeholder': 'Your message...'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with harrier design styling"""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text='Enter the email address associated with your account.'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if user with this email exists
            if not User.objects.filter(email=email).exists():
                raise ValidationError(
                    "No account found with this email address. Please check your email or create a new account."
                )
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with enhanced validation and harrier design styling"""
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password'
        }),
        help_text='Your password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters.'
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Confirm your new password',
            'autocomplete': 'new-password'
        })
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            # Enhanced password validation
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")

            if not any(c.islower() for c in password):
                raise ValidationError("Password must contain at least one lowercase letter.")

            if not any(c.isupper() for c in password):
                raise ValidationError("Password must contain at least one uppercase letter.")

            if not any(c.isdigit() for c in password):
                raise ValidationError("Password must contain at least one number.")

            if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
                raise ValidationError("Password must contain at least one special character.")

        return password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")

        return password2


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with email-only login and enhanced styling"""
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text='Enter the email address associated with your account.'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me for 30 days",
        widget=forms.CheckboxInput(attrs={
            'class': 'auth-checkbox'
        }),
        help_text='Keep me signed in on this device for 30 days.'
    )

    def clean(self):
        email = self.cleaned_data.get('username')  # Django uses 'username' field internally
        password = self.cleaned_data.get('password')

        if email and password:
            # Authenticate using email only
            try:
                user = User.objects.get(email=email)
                self.user_cache = authenticate(
                    self.request,
                    username=user.username,
                    password=password
                )

                if self.user_cache is None:
                    raise ValidationError("Invalid email or password.")
                else:
                    self.confirm_login_allowed(self.user_cache)

            except User.DoesNotExist:
                raise ValidationError("No account found with this email address.")

        return self.cleaned_data

    def clean_username(self):
        """Validate email format and existence"""
        email = self.cleaned_data.get('username')
        if email:
            if not User.objects.filter(email=email).exists():
                raise ValidationError("No account found with this email address.")
        return email


class ResendVerificationEmailForm(forms.Form):
    """Form for resending email verification"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text='Enter the email address you used to register.'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                if user.is_email_verified:
                    raise ValidationError("This email address is already verified.")
            except User.DoesNotExist:
                raise ValidationError("No account found with this email address.")
        return email

    def send_verification_email(self):
        """Send verification email to the user"""
        email = self.cleaned_data['email']
        user = User.objects.get(email=email)

        try:
            # Generate new verification token
            token = user.generate_email_verification_token()

            # Prepare email context
            context = {
                'user': user,
                'token': token,
                'domain': 'localhost:8000',  # Update this for production
                'protocol': 'http',  # Update to https for production
            }

            # Render email content
            html_message = render_to_string('core/auth/email_verification_email.html', context)
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject='Verify Your Email - Gurumisha Motors',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False


class VerificationCodeForm(forms.Form):
    """Form for entering verification code"""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'auth-form-input text-center text-2xl font-mono tracking-widest',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'style': 'letter-spacing: 0.5rem;'
        }),
        help_text='Enter the 6-digit code sent to your email'
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.code_type = kwargs.pop('code_type', 'email_verification')
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            raise ValidationError("Please enter the verification code.")

        if not code.isdigit():
            raise ValidationError("Verification code must contain only numbers.")

        if len(code) != 6:
            raise ValidationError("Verification code must be exactly 6 digits.")

        # Verify the code exists and is valid
        try:
            verification_code = VerificationCode.objects.get(
                user=self.user,
                code=code,
                code_type=self.code_type,
                is_used=False
            )

            if not verification_code.is_valid():
                raise ValidationError("This verification code has expired. Please request a new one.")

        except VerificationCode.DoesNotExist:
            raise ValidationError("Invalid verification code. Please check and try again.")

        return code

    def verify_and_mark_used(self):
        """Verify the code and mark it as used"""
        code = self.cleaned_data.get('code')
        try:
            verification_code = VerificationCode.objects.get(
                user=self.user,
                code=code,
                code_type=self.code_type,
                is_used=False
            )
            verification_code.mark_as_used()
            return True
        except VerificationCode.DoesNotExist:
            return False


class RequestVerificationCodeForm(forms.Form):
    """Form for requesting a new verification code"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text='Enter the email address associated with your account.'
    )

    def __init__(self, *args, **kwargs):
        self.code_type = kwargs.pop('code_type', 'email_verification')
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No account found with this email address.")
        return email

    def send_verification_code(self):
        """Generate and send a new verification code"""
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)

            # Create verification code
            verification_code = VerificationCode.create_verification_code(
                user=user,
                code_type=self.code_type,
                expiry_minutes=15
            )

            # Send email
            return send_verification_code_email(user, verification_code)

        except Exception as e:
            print(f"Failed to send verification code: {e}")
            return False
