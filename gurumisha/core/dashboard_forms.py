"""
Dashboard-specific forms for Gurumisha Motors
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Vendor, Car, ImportRequest, Inquiry, CarBrand, CarModel
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
            'placeholder': 'Search by title, brand, or model...'
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
    """Form for admin to edit car details"""

    class Meta:
        model = Car
        fields = [
            'title', 'brand', 'model', 'year', 'condition', 'engine_size',
            'fuel_type', 'transmission', 'mileage', 'color', 'price',
            'description', 'features', 'listing_type', 'status', 'is_approved',
            'negotiable', 'is_hot_deal', 'is_featured', 'is_certified', 'star_rating'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter car title'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-input'
            }),
            'model': forms.Select(attrs={
                'class': 'form-input'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1900,
                'max': 2025
            }),
            'condition': forms.Select(attrs={
                'class': 'form-input'
            }),
            'engine_size': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.1',
                'min': '0.1'
            }),
            'fuel_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'transmission': forms.Select(attrs={
                'class': 'form-input'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter car color'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Enter car description'
            }),
            'features': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Enter features separated by commas'
            }),
            'listing_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-input'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
            }),
            'negotiable': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
            }),
            'is_hot_deal': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
            }),
            'is_certified': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-harrier-red bg-gray-100 border-gray-300 rounded focus:ring-harrier-red focus:ring-2'
            }),
            'star_rating': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'max': '5'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for brand and model
        self.fields['brand'].queryset = CarBrand.objects.filter(is_active=True)
        if self.instance and self.instance.brand:
            self.fields['model'].queryset = CarModel.objects.filter(brand=self.instance.brand, is_active=True)
        else:
            self.fields['model'].queryset = CarModel.objects.none()
