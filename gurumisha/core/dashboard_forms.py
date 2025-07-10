"""
Dashboard-specific forms for Gurumisha Motors
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Vendor, Car, ImportRequest, Inquiry

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your phone number'
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your username'
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


class VendorProfileForm(forms.ModelForm):
    """Form for updating vendor profile information"""

    class Meta:
        model = Vendor
        fields = ['company_name', 'business_license', 'description', 'website']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your company name'
            }),
            'business_license': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Enter your business license number'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'Describe your business',
                'rows': 4
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-harrier-red focus:border-harrier-red',
                'placeholder': 'https://your-website.com'
            }),
        }


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
