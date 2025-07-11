"""
Tests for the enhanced profile system
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Vendor, VendorAnalytics, ProfileView, UserActivityLog
from core.dashboard_forms import UserProfileForm, VendorProfileForm
from core.utils.analytics_utils import track_profile_view, log_user_activity
import tempfile
from PIL import Image
import io

User = get_user_model()


class ProfileSystemTestCase(TestCase):
    """Test case for the enhanced profile system"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.customer_user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        
        self.vendor_user = User.objects.create_user(
            username='testvendor',
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        
        # Create vendor profile
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Motors',
            description='Test car dealership',
            is_approved=True
        )
    
    def create_test_image(self):
        """Create a test image file"""
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        return SimpleUploadedFile(
            name='test_image.jpg',
            content=image_file.getvalue(),
            content_type='image/jpeg'
        )


class UserProfileFormTestCase(ProfileSystemTestCase):
    """Test user profile forms"""
    
    def test_user_profile_form_valid_data(self):
        """Test user profile form with valid data"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '+254712345678',
            'bio': 'Test bio',
            'city': 'Nairobi',
            'country': 'Kenya',
            'preferred_language': 'en',
            'email_notifications': True,
            'profile_visibility': 'public'
        }
        
        form = UserProfileForm(data=form_data, instance=self.customer_user)
        self.assertTrue(form.is_valid())
    
    def test_user_profile_form_with_image(self):
        """Test user profile form with profile picture"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'profile_visibility': 'public'
        }
        
        file_data = {
            'profile_picture': self.create_test_image()
        }
        
        form = UserProfileForm(data=form_data, files=file_data, instance=self.customer_user)
        self.assertTrue(form.is_valid())
    
    def test_user_profile_form_invalid_email(self):
        """Test user profile form with invalid email"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'profile_visibility': 'public'
        }
        
        form = UserProfileForm(data=form_data, instance=self.customer_user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class VendorProfileFormTestCase(ProfileSystemTestCase):
    """Test vendor profile forms"""
    
    def test_vendor_profile_form_valid_data(self):
        """Test vendor profile form with valid data"""
        form_data = {
            'company_name': 'Updated Motors',
            'business_type': 'dealership',
            'description': 'Updated description',
            'business_phone': '+254712345678',
            'business_email': 'business@test.com',
            'website': 'https://test.com',
            'physical_address': 'Test Address',
            'email_notifications': True,
            'public_profile': True
        }
        
        form = VendorProfileForm(data=form_data, instance=self.vendor)
        self.assertTrue(form.is_valid())
    
    def test_vendor_profile_form_with_images(self):
        """Test vendor profile form with logo and cover image"""
        form_data = {
            'company_name': 'Updated Motors',
            'business_type': 'dealership',
            'public_profile': True
        }
        
        file_data = {
            'company_logo': self.create_test_image(),
            'cover_image': self.create_test_image()
        }
        
        form = VendorProfileForm(data=form_data, files=file_data, instance=self.vendor)
        self.assertTrue(form.is_valid())


class ProfileViewsTestCase(ProfileSystemTestCase):
    """Test profile views"""
    
    def test_user_profile_view_get(self):
        """Test GET request to user profile view"""
        self.client.login(username='testcustomer', password='testpass123')
        response = self.client.get(reverse('core:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile Settings')
        self.assertContains(response, 'testcustomer')
    
    def test_vendor_profile_view_get(self):
        """Test GET request to vendor profile view"""
        self.client.login(username='testvendor', password='testpass123')
        response = self.client.get(reverse('core:vendor_profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Business Profile')
        self.assertContains(response, 'Test Motors')
    
    def test_profile_update_post(self):
        """Test POST request to update profile"""
        self.client.login(username='testcustomer', password='testpass123')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
            'profile_visibility': 'public'
        }
        
        response = self.client.post(reverse('core:profile'), data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check if user was updated
        updated_user = User.objects.get(id=self.customer_user.id)
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
    
    def test_settings_view(self):
        """Test settings view"""
        self.client.login(username='testcustomer', password='testpass123')
        response = self.client.get(reverse('core:user_settings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')
        self.assertContains(response, 'Notification Preferences')


class AnalyticsTestCase(ProfileSystemTestCase):
    """Test analytics functionality"""
    
    def test_track_profile_view(self):
        """Test profile view tracking"""
        # Track a profile view
        request = type('MockRequest', (), {
            'user': self.customer_user,
            'META': {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Browser',
                'HTTP_REFERER': 'http://test.com'
            },
            'session': type('MockSession', (), {'session_key': 'test_session'})()
        })()
        
        profile_view = track_profile_view(request, self.vendor_user)
        
        self.assertIsNotNone(profile_view)
        self.assertEqual(profile_view.profile_user, self.vendor_user)
        self.assertEqual(profile_view.viewer, self.customer_user)
        self.assertEqual(profile_view.viewer_ip, '127.0.0.1')
    
    def test_log_user_activity(self):
        """Test user activity logging"""
        log_user_activity(
            user=self.customer_user,
            action='profile_update',
            description='Updated profile',
            metadata={'field': 'first_name'}
        )
        
        activity = UserActivityLog.objects.filter(user=self.customer_user).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.action, 'profile_update')
        self.assertEqual(activity.description, 'Updated profile')
    
    def test_vendor_analytics_creation(self):
        """Test vendor analytics creation"""
        analytics, created = VendorAnalytics.objects.get_or_create(vendor=self.vendor)
        
        self.assertTrue(created)
        self.assertEqual(analytics.vendor, self.vendor)
        self.assertEqual(analytics.total_profile_views, 0)
        self.assertEqual(analytics.profile_completion_score, 0)
    
    def test_vendor_analytics_calculation(self):
        """Test vendor analytics calculation"""
        analytics, created = VendorAnalytics.objects.get_or_create(vendor=self.vendor)
        
        # Calculate profile completion
        completion_score = analytics.calculate_profile_completion()
        
        # Should have some score based on existing data
        self.assertGreater(completion_score, 0)
        self.assertEqual(analytics.profile_completion_score, completion_score)


class ImageUploadTestCase(ProfileSystemTestCase):
    """Test image upload functionality"""
    
    def test_profile_picture_upload(self):
        """Test profile picture upload"""
        self.client.login(username='testcustomer', password='testpass123')
        
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@test.com',
            'profile_visibility': 'public'
        }
        
        files = {
            'profile_picture': self.create_test_image()
        }
        
        response = self.client.post(reverse('core:profile'), data, files=files)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check if profile picture was saved
        updated_user = User.objects.get(id=self.customer_user.id)
        self.assertTrue(updated_user.profile_picture)
    
    def test_company_logo_upload(self):
        """Test company logo upload"""
        self.client.login(username='testvendor', password='testpass123')
        
        data = {
            'company_name': 'Test Motors',
            'business_type': 'dealership',
            'public_profile': True
        }
        
        files = {
            'company_logo': self.create_test_image()
        }
        
        response = self.client.post(reverse('core:vendor_profile'), data, files=files)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check if logo was saved
        updated_vendor = Vendor.objects.get(id=self.vendor.id)
        self.assertTrue(updated_vendor.company_logo)


class SecurityTestCase(ProfileSystemTestCase):
    """Test security features"""
    
    def test_profile_access_requires_login(self):
        """Test that profile pages require login"""
        response = self.client.get(reverse('core:profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        response = self.client.get(reverse('core:vendor_profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_vendor_profile_requires_vendor_role(self):
        """Test that vendor profile requires vendor role"""
        self.client.login(username='testcustomer', password='testpass123')
        response = self.client.get(reverse('core:vendor_profile'))
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
    
    def test_password_change_view(self):
        """Test password change functionality"""
        self.client.login(username='testcustomer', password='testpass123')
        
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        }
        
        response = self.client.post(reverse('core:change_password'), data)
        
        # Should redirect after successful change
        self.assertEqual(response.status_code, 302)
