"""
Dashboard-specific forms for Gurumisha Motors
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Vendor, Car, ImportRequest, Inquiry, CarMake, CarModel, VehicleCondition
from .utils.image_utils import default_image_handler

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'profile-picture-input'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'username',
            'profile_picture', 'bio', 'date_of_birth', 'gender', 'city', 'country',
            'secondary_phone', 'whatsapp_number', 'address', 'preferred_language',
            'email_notifications', 'sms_notifications', 'marketing_emails',
            'newsletter_subscription', 'profile_visibility', 'show_email', 'show_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your phone number'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your username'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Tell us about yourself...',
                'rows': 4,
                'maxlength': 500
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-input'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your city'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your country'
            }),
            'secondary_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter secondary phone number'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter WhatsApp number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full address',
                'rows': 3
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-input'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'newsletter_subscription': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'profile_visibility': forms.Select(attrs={
                'class': 'form-input'
            }),
            'show_email': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'show_phone': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            is_valid, error_message = default_image_handler.validate(profile_picture)
            if not is_valid:
                raise ValidationError(error_message)
        return profile_picture

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        if len(bio) > 500:
            raise ValidationError("Bio must be 500 characters or less.")
        return bio

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Basic phone validation
            import re
            phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError("Please enter a valid phone number.")
        return phone


class AdminUserEditForm(forms.ModelForm):
    """Admin-specific user edit form with role management"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set country choices with Kenya at top and East African countries prominently featured
        self.fields['country'].choices = [
            ('', 'Select a country'),
            # Primary Market - Kenya
            ('Kenya', 'Kenya'),
            # East African Community
            ('Uganda', 'Uganda'),
            ('Tanzania', 'Tanzania'),
            ('Rwanda', 'Rwanda'),
            ('Burundi', 'Burundi'),
            ('South Sudan', 'South Sudan'),
            # Other East African Countries
            ('Ethiopia', 'Ethiopia'),
            ('Somalia', 'Somalia'),
            ('Djibouti', 'Djibouti'),
            ('Eritrea', 'Eritrea'),
            # Major African Markets
            ('South Africa', 'South Africa'),
            ('Nigeria', 'Nigeria'),
            ('Egypt', 'Egypt'),
            ('Morocco', 'Morocco'),
            ('Ghana', 'Ghana'),
            ('Algeria', 'Algeria'),
            ('Tunisia', 'Tunisia'),
            ('Libya', 'Libya'),
            # Other Countries (Alphabetical)
            ('Afghanistan', 'Afghanistan'),
            ('Albania', 'Albania'),
            ('Argentina', 'Argentina'),
            ('Australia', 'Australia'),
            ('Austria', 'Austria'),
            ('Bangladesh', 'Bangladesh'),
            ('Belgium', 'Belgium'),
            ('Brazil', 'Brazil'),
            ('Canada', 'Canada'),
            ('China', 'China'),
            ('Denmark', 'Denmark'),
            ('Finland', 'Finland'),
            ('France', 'France'),
            ('Germany', 'Germany'),
            ('India', 'India'),
            ('Indonesia', 'Indonesia'),
            ('Italy', 'Italy'),
            ('Japan', 'Japan'),
            ('Malaysia', 'Malaysia'),
            ('Netherlands', 'Netherlands'),
            ('Norway', 'Norway'),
            ('Pakistan', 'Pakistan'),
            ('Philippines', 'Philippines'),
            ('Poland', 'Poland'),
            ('Portugal', 'Portugal'),
            ('Russia', 'Russia'),
            ('Saudi Arabia', 'Saudi Arabia'),
            ('Singapore', 'Singapore'),
            ('Spain', 'Spain'),
            ('Sweden', 'Sweden'),
            ('Switzerland', 'Switzerland'),
            ('Thailand', 'Thailand'),
            ('Turkey', 'Turkey'),
            ('United Arab Emirates', 'United Arab Emirates'),
            ('United Kingdom', 'United Kingdom'),
            ('United States', 'United States'),
            ('Other', 'Other'),
        ]

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'username', 'role',
            'city', 'country', 'is_active', 'is_staff'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter last name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter phone number'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter city'
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is already taken by another user
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.pk).first()
            if existing_user:
                raise ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username is already taken by another user
            existing_user = User.objects.filter(username=username).exclude(pk=self.instance.pk).first()
            if existing_user:
                raise ValidationError("This username is already taken.")
        return username


class VendorProfileForm(forms.ModelForm):
    """Form for updating vendor profile information"""

    company_logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'company-logo-input'
        })
    )

    cover_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'cover-image-input'
        })
    )

    class Meta:
        model = Vendor
        fields = [
            'company_name', 'business_license', 'business_type', 'description',
            'website', 'business_phone', 'business_email', 'physical_address',
            'company_logo', 'cover_image', 'facebook_url', 'twitter_url',
            'instagram_url', 'linkedin_url', 'youtube_url', 'year_established',
            'number_of_employees', 'specializations', 'service_areas',
            'email_notifications', 'sms_notifications', 'inquiry_notifications',
            'order_notifications', 'promotion_notifications', 'business_hours_note',
            'operates_monday', 'operates_tuesday', 'operates_wednesday',
            'operates_thursday', 'operates_friday', 'operates_saturday', 'operates_sunday',
            'mpesa_number', 'mpesa_business_shortcode', 'bank_name', 'account_number',
            'account_name', 'swift_code', 'accepts_installments', 'minimum_deposit_percentage',
            'public_profile', 'show_contact', 'auto_approve_inquiries',
            'allow_direct_messages', 'show_business_hours', 'auto_response_enabled',
            'auto_response_message', 'auto_response_delay_minutes'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your company name'
            }),
            'business_license': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your business license number'
            }),
            'business_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe your business',
                'rows': 4
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://your-website.com'
            }),
            'business_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter business phone number'
            }),
            'business_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter business email'
            }),
            'physical_address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your business address',
                'rows': 3
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://twitter.com/yourhandle'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://instagram.com/yourhandle'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://linkedin.com/company/yourcompany'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://youtube.com/channel/yourchannel'
            }),
            'year_established': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Year established',
                'min': 1900,
                'max': 2024
            }),
            'number_of_employees': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of employees',
                'min': 1
            }),
            'specializations': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter specializations (comma-separated)',
                'rows': 2
            }),
            'service_areas': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Areas where you provide services',
                'rows': 2
            }),
            'business_hours_note': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Additional notes about business hours',
                'rows': 2
            }),
            'mpesa_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'M-Pesa number'
            }),
            'mpesa_business_shortcode': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'M-Pesa business shortcode'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Bank name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Account number'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Account name'
            }),
            'swift_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'SWIFT code'
            }),
            'minimum_deposit_percentage': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 10,
                'max': 100,
                'placeholder': 'Minimum deposit percentage'
            }),
            'auto_response_message': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Auto-response message for inquiries',
                'rows': 3,
                'maxlength': 500
            }),
            'auto_response_delay_minutes': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 60,
                'placeholder': 'Delay in minutes'
            }),
            # Boolean fields
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'inquiry_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'order_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'promotion_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_monday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_tuesday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_wednesday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_thursday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_friday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_saturday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'operates_sunday': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'accepts_installments': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'public_profile': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'show_contact': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'auto_approve_inquiries': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'allow_direct_messages': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'show_business_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'auto_response_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_company_logo(self):
        company_logo = self.cleaned_data.get('company_logo')
        if company_logo:
            is_valid, error_message = default_image_handler.validate(company_logo)
            if not is_valid:
                raise ValidationError(error_message)
        return company_logo

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            is_valid, error_message = default_image_handler.validate(cover_image)
            if not is_valid:
                raise ValidationError(error_message)
        return cover_image

    def clean_business_phone(self):
        phone = self.cleaned_data.get('business_phone', '')
        if phone:
            import re
            phone_pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError("Please enter a valid business phone number.")
        return phone

    def clean_business_email(self):
        email = self.cleaned_data.get('business_email', '')
        if email:
            from django.core.validators import validate_email
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Please enter a valid business email address.")
        return email

    def clean_website(self):
        website = self.cleaned_data.get('website', '')
        if website:
            import re
            url_pattern = r'^https?://.+'
            if not re.match(url_pattern, website):
                raise ValidationError("Website URL must start with http:// or https://")
        return website


class UserPreferencesForm(forms.ModelForm):
    """Form for updating user preferences and settings"""

    class Meta:
        model = User
        fields = [
            'email_notifications', 'sms_notifications', 'marketing_emails',
            'newsletter_subscription', 'profile_visibility', 'show_email',
            'show_phone', 'preferred_language', 'timezone'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'newsletter_subscription': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'profile_visibility': forms.Select(attrs={
                'class': 'form-input',
                'data-toggle': 'preference'
            }),
            'show_email': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'show_phone': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'preference'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-input',
                'data-toggle': 'preference'
            }),
            'timezone': forms.Select(attrs={
                'class': 'form-input',
                'data-toggle': 'preference'
            }),
        }


class VendorPreferencesForm(forms.ModelForm):
    """Form for updating vendor-specific preferences"""

    class Meta:
        model = Vendor
        fields = [
            'email_notifications', 'sms_notifications', 'inquiry_notifications',
            'order_notifications', 'promotion_notifications', 'public_profile',
            'show_contact', 'auto_approve_inquiries', 'allow_direct_messages',
            'show_business_hours', 'auto_response_enabled', 'auto_response_message',
            'auto_response_delay_minutes'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'inquiry_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'order_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'promotion_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'public_profile': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'show_contact': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'auto_approve_inquiries': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'allow_direct_messages': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'show_business_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'auto_response_enabled': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'data-toggle': 'auto-response'
            }),
            'auto_response_message': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Enter your auto-response message...',
                'maxlength': 500
            }),
            'auto_response_delay_minutes': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 60,
                'placeholder': 'Minutes'
            }),
        }

    def clean_auto_response_message(self):
        message = self.cleaned_data.get('auto_response_message', '')
        auto_response_enabled = self.cleaned_data.get('auto_response_enabled', False)

        if auto_response_enabled and not message.strip():
            raise ValidationError("Auto-response message is required when auto-response is enabled.")

        if len(message) > 500:
            raise ValidationError("Auto-response message must be 500 characters or less.")

        return message


class BusinessHoursForm(forms.Form):
    """Form for managing business hours"""

    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        for day_code, day_name in self.DAYS_OF_WEEK:
            # Operating day checkbox
            self.fields[f'operates_{day_code}'] = forms.BooleanField(
                required=False,
                label=f'Open on {day_name}',
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-checkbox',
                    'data-day': day_code
                })
            )

            # Opening time
            self.fields[f'{day_code}_open'] = forms.TimeField(
                required=False,
                label=f'{day_name} Opening Time',
                widget=forms.TimeInput(attrs={
                    'class': 'form-input',
                    'type': 'time'
                })
            )

            # Closing time
            self.fields[f'{day_code}_close'] = forms.TimeField(
                required=False,
                label=f'{day_name} Closing Time',
                widget=forms.TimeInput(attrs={
                    'class': 'form-input',
                    'type': 'time'
                })
            )

            # Set initial values if vendor exists
            if vendor:
                operates_field = f'operates_{day_code}'
                if hasattr(vendor, operates_field):
                    self.fields[f'operates_{day_code}'].initial = getattr(vendor, operates_field)

    def clean(self):
        cleaned_data = super().clean()

        for day_code, day_name in self.DAYS_OF_WEEK:
            operates = cleaned_data.get(f'operates_{day_code}')
            open_time = cleaned_data.get(f'{day_code}_open')
            close_time = cleaned_data.get(f'{day_code}_close')

            if operates:
                if not open_time:
                    raise ValidationError(f"Opening time is required for {day_name}")
                if not close_time:
                    raise ValidationError(f"Closing time is required for {day_name}")
                if open_time and close_time and open_time >= close_time:
                    raise ValidationError(f"Opening time must be before closing time for {day_name}")

        return cleaned_data


class PasswordChangeForm(forms.Form):
    """Form for changing user password"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Enter current password'
        }),
        label='Current Password'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Enter new password'
        }),
        label='New Password',
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError("New passwords do not match.")
        
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()


class InquiryResponseForm(forms.ModelForm):
    """Form for vendors to respond to inquiries"""

    response = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Type your response here...',
            'rows': 4
        }),
        required=True,
        label='Your Response'
    )

    class Meta:
        model = Inquiry
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
            })
        }


class AdminInquiryReplyForm(forms.Form):
    """Enhanced form for admin replies to customer inquiries"""

    response_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Type your response to the customer...',
            'rows': 6,
            'required': True
        }),
        label='Response to Customer',
        help_text='This response will be sent to the customer via email'
    )

    internal_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Add internal notes (not visible to customer)...',
            'rows': 3
        }),
        required=False,
        label='Internal Notes',
        help_text='These notes are only visible to admin users'
    )

    status = forms.ChoiceField(
        choices=Inquiry.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        label='Update Status'
    )

    priority = forms.ChoiceField(
        choices=Inquiry.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        label='Priority Level'
    )

    assign_to_admin = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Assign to Admin',
        help_text='Assign this inquiry to a specific admin user'
    )

    send_email = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        required=False,
        initial=True,
        label='Send email notification to customer'
    )

    requires_followup = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        required=False,
        label='Requires follow-up'
    )

    followup_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-input',
            'type': 'datetime-local'
        }),
        required=False,
        label='Follow-up Date'
    )

    attachment = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'
        }),
        required=False,
        label='Attach File',
        help_text='Attach supporting documents (PDF, DOC, images)'
    )

    def __init__(self, *args, **kwargs):
        inquiry = kwargs.pop('inquiry', None)
        super().__init__(*args, **kwargs)

        # Set admin users queryset
        from .models import User
        self.fields['assign_to_admin'].queryset = User.objects.filter(
            role='admin', is_active=True
        ).order_by('first_name', 'last_name')

        # Set initial values if inquiry is provided
        if inquiry:
            self.fields['status'].initial = inquiry.status
            self.fields['priority'].initial = inquiry.priority
            self.fields['assign_to_admin'].initial = inquiry.assigned_admin
            self.fields['requires_followup'].initial = inquiry.requires_followup
            self.fields['followup_date'].initial = inquiry.followup_date


class AdminInquiryStatusForm(forms.ModelForm):
    """Quick form for updating inquiry status and priority"""

    class Meta:
        model = Inquiry
        fields = ['status', 'priority', 'assigned_admin', 'requires_followup']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-input text-sm'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-input text-sm'
            }),
            'assigned_admin': forms.Select(attrs={
                'class': 'form-input text-sm'
            }),
            'requires_followup': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter admin users
        from .models import User
        self.fields['assigned_admin'].queryset = User.objects.filter(
            role='admin', is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['assigned_admin'].empty_label = "Unassigned"


class AdminInquiryBulkActionForm(forms.Form):
    """Form for bulk actions on multiple inquiries"""

    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('assign', 'Assign to Admin'),
        ('status_change', 'Change Status'),
        ('priority_change', 'Change Priority'),
        ('mark_urgent', 'Mark as Urgent'),
        ('remove_urgent', 'Remove Urgent Flag'),
        ('export', 'Export Selected'),
        ('delete', 'Delete Selected'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input',
            'onchange': 'toggleBulkActionFields(this.value)'
        }),
        label='Bulk Action'
    )

    assign_to_admin = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Assign to Admin'
    )

    new_status = forms.ChoiceField(
        choices=Inquiry.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='New Status'
    )

    new_priority = forms.ChoiceField(
        choices=Inquiry.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='New Priority'
    )

    selected_inquiries = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set admin users queryset
        from .models import User
        self.fields['assign_to_admin'].queryset = User.objects.filter(
            role='admin', is_active=True
        ).order_by('first_name', 'last_name')


class AdminInquiryFilterForm(forms.Form):
    """Advanced filter form for admin inquiry management"""

    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search by subject, customer, or content...'
        }),
        required=False,
        label='Search'
    )

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Inquiry.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Status'
    )

    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Inquiry.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Priority'
    )

    inquiry_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Inquiry.INQUIRY_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Type'
    )

    assigned_admin = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-input'
        }),
        required=False,
        label='Assigned Admin'
    )

    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        }),
        required=False,
        label='From Date'
    )

    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        }),
        required=False,
        label='To Date'
    )

    is_urgent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        required=False,
        label='Urgent Only'
    )

    is_overdue = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        required=False,
        label='Overdue Only'
    )

    unassigned_only = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        required=False,
        label='Unassigned Only'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set admin users queryset
        from .models import User
        self.fields['assigned_admin'].queryset = User.objects.filter(
            role='admin', is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['assigned_admin'].empty_label = "All Admins"


class CarApprovalForm(forms.ModelForm):
    """Form for admin to approve/reject car listings"""

    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Add notes about the approval/rejection...',
            'rows': 3
        }),
        required=False,
        label='Admin Notes'
    )

    class Meta:
        model = Car
        fields = ['is_approved']


class VendorApprovalForm(forms.ModelForm):
    """Form for admin to approve/reject vendor applications"""

    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Add notes about the approval/rejection...',
            'rows': 3
        }),
        required=False,
        label='Admin Notes'
    )

    class Meta:
        model = Vendor
        fields = ['is_approved']


class UserSearchForm(forms.Form):
    """Form for searching users in admin panel"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Search by name, email, or username...'
        })
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )


class CarSearchForm(forms.Form):
    """Form for searching cars in admin panel"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Search by title, make, or model...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('approved', 'Approved'), ('pending', 'Pending Approval')],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )


class VendorSearchForm(forms.Form):
    """Form for searching vendors in admin panel"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Search by company name...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('approved', 'Approved'), ('pending', 'Pending Approval')],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )


class BulkActionForm(forms.Form):
    """Form for bulk actions in admin panels"""
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('approve', 'Approve Selected'),
            ('reject', 'Reject Selected'),
            ('delete', 'Delete Selected')
        ],
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )
    selected_items = forms.CharField(
        widget=forms.HiddenInput()
    )

    def clean_selected_items(self):
        selected_items = self.cleaned_data['selected_items']
        if not selected_items:
            raise ValidationError("Please select at least one item.")
        try:
            item_ids = [int(id) for id in selected_items.split(',') if id.strip()]
            return item_ids
        except ValueError:
            raise ValidationError("Invalid selection.")


class NotificationForm(forms.Form):
    """Form for sending notifications to users"""
    recipient_type = forms.ChoiceField(
        choices=[
            ('all', 'All Users'),
            ('customers', 'All Customers'),
            ('vendors', 'All Vendors'),
            ('specific', 'Specific User')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )
    specific_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Enter notification subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
            'placeholder': 'Enter notification message',
            'rows': 5
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        specific_user = cleaned_data.get('specific_user')

        if recipient_type == 'specific' and not specific_user:
            raise ValidationError("Please select a specific user when choosing 'Specific User' option.")
        
        return cleaned_data


class AdminCarEditForm(forms.ModelForm):
    """Enhanced form for admin to edit all car details"""

    # Additional fields for fallback names
    make_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter make name if not in dropdown'
        }),
        help_text='Use only if make is not available in dropdown'
    )

    model_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter model name if not in dropdown'
        }),
        help_text='Use only if model is not available in dropdown'
    )

    condition_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter condition if not in dropdown'
        }),
        help_text='Use only if condition is not available in dropdown'
    )

    # Admin notes field
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Add notes about approval, rejection, or special instructions...'
        }),
        help_text='Internal notes for admin reference and vendor communication'
    )

    # Hot deal fields
    hot_deal_discount = forms.IntegerField(
        required=False,
        min_value=5,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter discount percentage (5-50%)'
        }),
        help_text='Discount percentage for hot deals'
    )

    hot_deal_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter number of days (1-30)'
        }),
        help_text='Number of days for hot deal duration'
    )

    # Featured until field
    featured_until = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-input',
            'type': 'datetime-local'
        }),
        help_text='When featuring expires'
    )

    class Meta:
        model = Car
        fields = [
            # Basic Information
            'title', 'description', 'features',

            # Vehicle Identification
            'make', 'model', 'make_name', 'model_name', 'year', 'color',

            # Vehicle Condition & Specifications
            'condition', 'condition_name', 'mileage', 'engine_size',
            'fuel_type', 'transmission',

            # Pricing
            'price', 'negotiable',

            # Listing Information
            'listing_type', 'status',

            # Location
            'area', 'city', 'country',

            # Admin Controls
            'is_approved', 'star_rating',

            # Promotional Features
            'is_featured', 'featured_until', 'auto_featured',
            'is_hot_deal', 'is_certified',

            # Images
            'main_image'
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Toyota Camry 2020 - Excellent Condition'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Detailed description of the car\'s condition, history, and features...'
            }),
            'features': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Air conditioning, Leather seats, Sunroof, Navigation system...'
            }),
            'make': forms.Select(attrs={'class': 'form-input'}),
            'model': forms.Select(attrs={'class': 'form-input'}),
            'year': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1900,
                'max': 2030
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., White, Black, Silver'
            }),
            'condition': forms.Select(attrs={'class': 'form-input'}),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'step': 1000
            }),
            'engine_size': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 2.0L, 1800cc'
            }),
            'fuel_type': forms.Select(attrs={'class': 'form-input'}),
            'transmission': forms.Select(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-input price-format',
                'min': 0,
                'step': 1000
            }),
            'listing_type': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'area': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Westlands, Karen, CBD'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Nairobi, Mombasa, Kisumu'
            }),
            'country': forms.Select(attrs={'class': 'form-input'}),
            'star_rating': forms.Select(attrs={'class': 'form-input'}),
            'main_image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'negotiable': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-harrier-red focus:ring-harrier-red'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-green-600 focus:ring-green-500'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-purple-600 focus:ring-purple-500'
            }),
            'auto_featured': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-blue-600 focus:ring-blue-500'
            }),
            'is_hot_deal': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-red-600 focus:ring-red-500'
            }),
            'is_certified': forms.CheckboxInput(attrs={
                'class': 'form-checkbox text-green-600 focus:ring-green-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate make choices
        self.fields['make'].queryset = CarMake.objects.filter(is_active=True).order_by('name')
        self.fields['make'].empty_label = "Select Make"

        # Populate model choices (will be filtered by brand via JavaScript)
        self.fields['model'].queryset = CarModel.objects.filter(is_active=True).order_by('name')
        self.fields['model'].empty_label = "Select Model"

        # Populate condition choices
        self.fields['condition'].queryset = VehicleCondition.objects.filter(is_active=True).order_by('display_order')
        self.fields['condition'].empty_label = "Select Condition"

        # Set star rating choices
        self.fields['star_rating'].choices = [
            ('', 'No Rating'),
            (1, '⭐ 1 Star'),
            (2, '⭐⭐ 2 Stars'),
            (3, '⭐⭐⭐ 3 Stars'),
            (4, '⭐⭐⭐⭐ 4 Stars'),
            (5, '⭐⭐⭐⭐⭐ 5 Stars'),
        ]

        # Set country choices (prioritizing East African countries)
        country_choices = [
            ('', 'Select Country'),
            ('Kenya', 'Kenya'),
            ('Uganda', 'Uganda'),
            ('Tanzania', 'Tanzania'),
            ('Rwanda', 'Rwanda'),
            ('Burundi', 'Burundi'),
            ('South Sudan', 'South Sudan'),
            ('Ethiopia', 'Ethiopia'),
            ('Somalia', 'Somalia'),
            ('Djibouti', 'Djibouti'),
            ('Eritrea', 'Eritrea'),
            # Add more countries as needed
        ]
        self.fields['country'].choices = country_choices

        # Make certain fields required
        self.fields['title'].required = True
        self.fields['price'].required = True
        self.fields['year'].required = True
        self.fields['color'].required = True
        self.fields['fuel_type'].required = True
        self.fields['transmission'].required = True
        self.fields['mileage'].required = True
        self.fields['listing_type'].required = True
        self.fields['status'].required = True
        self.fields['description'].required = True

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            if price <= 0:
                raise forms.ValidationError("Price must be greater than 0")
            if price > 1000000000:  # 1 billion limit
                raise forms.ValidationError("Price cannot exceed 1 billion")
        return price

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year is not None:
            current_year = timezone.now().year
            if year < 1900 or year > current_year + 1:
                raise forms.ValidationError(f"Year must be between 1900 and {current_year + 1}")
        return year

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage is not None and mileage < 0:
            raise forms.ValidationError("Mileage cannot be negative")
        return mileage

    def clean(self):
        cleaned_data = super().clean()

        # Validate that either make or make_name is provided
        make = cleaned_data.get('make')
        make_name = cleaned_data.get('make_name')
        if not make and not make_name:
            raise forms.ValidationError("Please select a make or enter a make name")

        # Validate hot deal fields if hot deal is enabled
        is_hot_deal = cleaned_data.get('is_hot_deal')
        if is_hot_deal:
            hot_deal_discount = cleaned_data.get('hot_deal_discount')
            hot_deal_days = cleaned_data.get('hot_deal_days')

            if not hot_deal_discount:
                self.add_error('hot_deal_discount', 'Discount percentage is required for hot deals')
            if not hot_deal_days:
                self.add_error('hot_deal_days', 'Duration in days is required for hot deals')

        return cleaned_data
