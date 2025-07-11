from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """Extended User model with role-based access"""
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
        ('fr', 'French'),
    ]

    # Basic Information
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Profile Information
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Brief description about yourself")
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')

    # Contact Information
    secondary_phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    # Preferences
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')

    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=True)

    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('contacts_only', 'Contacts Only'),
        ],
        default='public'
    )
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=True)

    # Account Status
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def generate_email_verification_token(self):
        """Generate a unique email verification token"""
        import uuid
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def is_email_verification_token_valid(self):
        """Check if email verification token is still valid (24 hours)"""
        if not self.email_verification_sent_at:
            return False

        from datetime import timedelta
        expiry_time = self.email_verification_sent_at + timedelta(hours=24)
        return timezone.now() < expiry_time

    def verify_email(self):
        """Mark email as verified and clear verification token"""
        self.is_email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save()

    @property
    def can_access_protected_areas(self):
        """Check if user can access protected areas (email verified)"""
        return self.is_email_verified


class VerificationCode(models.Model):
    """Model for storing email verification codes as an alternative to UUID tokens"""
    CODE_TYPES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('two_factor', 'Two Factor Authentication'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=10)
    code_type = models.CharField(max_length=20, choices=CODE_TYPES, default='email_verification')
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'code_type', 'is_used']),
            models.Index(fields=['email', 'code_type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.code_type} code for {self.email}"

    @classmethod
    def generate_code(cls, length=6, code_type='numeric'):
        """Generate a verification code"""
        if code_type == 'numeric':
            return ''.join(random.choices(string.digits, k=length))
        elif code_type == 'alphanumeric':
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        else:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @classmethod
    def create_verification_code(cls, user, code_type='email_verification', expiry_minutes=15):
        """Create a new verification code for a user"""
        # Invalidate any existing codes of the same type
        cls.objects.filter(
            user=user,
            code_type=code_type,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(is_used=True, used_at=timezone.now())

        # Generate new code
        code = cls.generate_code(length=6, code_type='numeric')
        expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)

        return cls.objects.create(
            user=user,
            code=code,
            code_type=code_type,
            email=user.email,
            expires_at=expires_at
        )

    def is_valid(self):
        """Check if the code is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark the code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class VendorSubscription(models.Model):
    """Vendor subscription tiers for automatic featuring"""
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    vendor = models.OneToOneField('Vendor', on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)

    # Tier benefits
    max_featured_cars = models.PositiveIntegerField(default=0)
    max_hot_deals = models.PositiveIntegerField(default=0)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor.company_name} - {self.get_tier_display()}"

    def is_expired(self):
        """Check if subscription is expired"""
        if self.end_date:
            return timezone.now() > self.end_date
        return False

    class Meta:
        ordering = ['-created_at']


class FeaturedCarTier(models.Model):
    """Featured car tier configuration"""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    priority_order = models.PositiveIntegerField(unique=True, help_text="Lower numbers = higher priority")
    badge_color = models.CharField(max_length=20, default='bg-gray-500')
    badge_icon = models.CharField(max_length=50, default='fas fa-star')

    # Tier benefits
    homepage_slots = models.PositiveIntegerField(default=0, help_text="Number of slots on homepage")
    listing_boost_percentage = models.PositiveIntegerField(default=0, help_text="Boost in search results")

    # Pricing (for future subscription system)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['priority_order']


class Vendor(models.Model):
    """Vendor profile for car dealers and spare parts sellers"""
    BUSINESS_TYPE_CHOICES = [
        ('dealership', 'Car Dealership'),
        ('spare_parts', 'Spare Parts Seller'),
        ('both', 'Both Cars and Spare Parts'),
        ('service_center', 'Service Center'),
        ('individual', 'Individual Seller'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    business_license = models.CharField(max_length=100, blank=True)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='dealership')
    description = models.TextField(blank=True)

    # Contact Information
    website = models.URLField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    business_email = models.EmailField(blank=True)
    physical_address = models.TextField(blank=True)

    # Visual Identity
    company_logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='vendor_covers/', blank=True, null=True)

    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Business Details
    year_established = models.PositiveIntegerField(blank=True, null=True)
    number_of_employees = models.PositiveIntegerField(blank=True, null=True)
    specializations = models.TextField(blank=True, help_text="Comma-separated list of specializations")
    service_areas = models.TextField(blank=True, help_text="Areas where services are provided")

    # Verification and Status
    is_approved = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    approval_date = models.DateTimeField(null=True, blank=True)
    verification_documents = models.TextField(blank=True, help_text="JSON formatted verification documents")

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    inquiry_notifications = models.BooleanField(default=True)
    order_notifications = models.BooleanField(default=True)
    promotion_notifications = models.BooleanField(default=True)

    # Business hours and timezone
    business_hours = models.TextField(blank=True, help_text="JSON formatted business hours")
    business_hours_note = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')

    # Operating Days
    operates_monday = models.BooleanField(default=True)
    operates_tuesday = models.BooleanField(default=True)
    operates_wednesday = models.BooleanField(default=True)
    operates_thursday = models.BooleanField(default=True)
    operates_friday = models.BooleanField(default=True)
    operates_saturday = models.BooleanField(default=True)
    operates_sunday = models.BooleanField(default=False)

    # Payment settings
    mpesa_number = models.CharField(max_length=15, blank=True)
    mpesa_business_shortcode = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    payment_methods = models.TextField(blank=True, help_text="JSON formatted payment methods")
    accepts_installments = models.BooleanField(default=False)
    minimum_deposit_percentage = models.PositiveIntegerField(default=20, help_text="Minimum deposit percentage for installments")

    # Account preferences
    public_profile = models.BooleanField(default=True)
    show_contact = models.BooleanField(default=True)
    auto_approve_inquiries = models.BooleanField(default=False)
    allow_direct_messages = models.BooleanField(default=True)
    show_business_hours = models.BooleanField(default=True)

    # Auto-response settings
    auto_response_enabled = models.BooleanField(default=False)
    auto_response_message = models.TextField(blank=True, max_length=500)
    auto_response_delay_minutes = models.PositiveIntegerField(default=5)

    # Enhanced vendor metrics
    total_sales = models.PositiveIntegerField(default=0)
    total_listings = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    response_time_hours = models.PositiveIntegerField(default=24, help_text="Average response time in hours")
    profile_views = models.PositiveIntegerField(default=0)
    total_inquiries = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

    def get_subscription_tier(self):
        """Get current subscription tier"""
        try:
            subscription = self.subscription
            if subscription.is_active and not subscription.is_expired():
                return subscription.tier
        except VendorSubscription.DoesNotExist:
            pass
        return 'basic'

    def can_feature_cars(self):
        """Check if vendor can feature cars based on subscription"""
        tier = self.get_subscription_tier()
        return tier in ['bronze', 'silver', 'gold', 'platinum']

    def get_max_featured_cars(self):
        """Get maximum number of cars vendor can feature"""
        try:
            subscription = self.subscription
            if subscription.is_active and not subscription.is_expired():
                return subscription.max_featured_cars
        except VendorSubscription.DoesNotExist:
            pass
        return 0

    def update_average_rating(self):
        """Update vendor's average rating based on car ratings"""
        car_ratings = self.cars.exclude(calculated_rating=0).values_list('calculated_rating', flat=True)
        if car_ratings:
            self.average_rating = sum(car_ratings) / len(car_ratings)
            self.save(update_fields=['average_rating'])


class CarBrand(models.Model):
    """Car brands like Toyota, Honda, etc."""
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class CarModel(models.Model):
    """Car models like Camry, Civic, etc."""
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    class Meta:
        ordering = ['brand__name', 'name']
        unique_together = ['brand', 'name']


class Car(models.Model):
    """Car listings"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
        ('featured', 'Featured'),
    ]

    LISTING_TYPE_CHOICES = [
        ('local', 'Local Listing'),
        ('imported', 'Imported Car'),
        ('sell_behalf', 'Sell on Behalf'),
        ('auction', 'Auctioned'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('certified', 'Certified Pre-Owned'),
    ]

    FUEL_TYPE_CHOICES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
    ]

    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
    ]

    # Basic Information
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='cars')
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)

    # Technical Specifications
    engine_size = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    mileage = models.PositiveIntegerField(help_text="Mileage in kilometers")
    color = models.CharField(max_length=50)

    # Pricing and Status
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='local')
    negotiable = models.BooleanField(default=False)

    # Description and Features
    title = models.CharField(max_length=200)
    description = models.TextField()
    features = models.TextField(blank=True, help_text="Comma-separated list of features")

    # Images
    main_image = models.ImageField(upload_to='cars/main/', blank=True)

    # Metadata
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    inquiry_count = models.PositiveIntegerField(default=0)

    # Enhanced Promotion System
    is_hot_deal = models.BooleanField(default=False, help_text="Mark as hot deal for special promotion")
    star_rating = models.PositiveIntegerField(default=0, help_text="Legacy star rating from 0-5")
    calculated_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0,
                                          help_text="Calculated rating with half-star precision (0.0-5.0)")

    # Featured car system (simplified binary system)
    is_featured = models.BooleanField(default=False, help_text="Mark car as featured")
    featured_until = models.DateTimeField(null=True, blank=True, help_text="When featuring expires")
    auto_featured = models.BooleanField(default=False, help_text="Automatically featured based on vendor subscription")

    # Certified car feature
    is_certified = models.BooleanField(default=False, help_text="Mark car as certified with additional benefits")

    # Performance metrics for rating calculation
    last_rating_update = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.year} {self.brand.name} {self.model.name}"

    def get_absolute_url(self):
        return reverse('car_detail', kwargs={'pk': self.pk})

    def get_features_list(self):
        """Return features as a list"""
        if self.features:
            return [feature.strip() for feature in self.features.split(',')]
        return []

    def is_currently_featured(self):
        """Check if car is currently featured"""
        return (self.is_featured and
                (self.featured_until is None or self.featured_until > timezone.now()))

    def get_star_display(self):
        """Get star rating display with half-star support"""
        full_stars = int(self.calculated_rating)
        half_star = (self.calculated_rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        display = '★' * full_stars
        if half_star:
            display += '☆'  # Half star representation
        display += '☆' * empty_stars
        return display

    def get_star_display_html(self):
        """Get HTML star rating display with half-star support"""
        full_stars = int(self.calculated_rating)
        half_star = (self.calculated_rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        html = '<div class="flex items-center">'
        # Full stars
        for _ in range(full_stars):
            html += '<i class="fas fa-star text-yellow-400"></i>'
        # Half star
        if half_star:
            html += '<i class="fas fa-star-half-alt text-yellow-400"></i>'
        # Empty stars
        for _ in range(empty_stars):
            html += '<i class="far fa-star text-gray-300"></i>'
        html += f'<span class="ml-1 text-sm text-gray-600">({self.calculated_rating})</span></div>'
        return html

    def get_promotion_badges(self):
        """Get list of promotion badges for this car"""
        badges = []

        # Featured badge (simplified)
        if self.is_currently_featured():
            badges.append({
                'type': 'featured',
                'text': 'Featured',
                'class': 'bg-purple-600',
                'icon': 'fas fa-star'
            })

        # Certified badge
        if self.is_certified:
            badges.append({
                'type': 'certified',
                'text': 'Certified',
                'class': 'bg-green-600',
                'icon': 'fas fa-certificate'
            })

        # Hot deal badge
        if self.is_hot_deal:
            badges.append({
                'type': 'hot_deal',
                'text': 'Hot Deal',
                'class': 'bg-red-500',
                'icon': 'fas fa-fire'
            })

        # High rating badge
        if self.calculated_rating >= 4.5:
            badges.append({
                'type': 'top_rated',
                'text': 'Top Rated',
                'class': 'bg-green-500',
                'icon': 'fas fa-star'
            })

        return badges

    def calculate_automatic_rating(self):
        """Calculate automatic rating based on car metrics"""
        # Base rating factors
        base_rating = 3.0

        # Views factor (0-1 points)
        if self.views_count > 0:
            views_factor = min(self.views_count / 1000, 1.0)  # Max 1 point for 1000+ views
            base_rating += views_factor

        # Inquiry factor (0-1 points)
        if self.inquiry_count > 0:
            inquiry_factor = min(self.inquiry_count / 50, 1.0)  # Max 1 point for 50+ inquiries
            base_rating += inquiry_factor

        # Vendor rating factor (0-1 points)
        if hasattr(self.vendor, 'average_rating') and self.vendor.average_rating > 0:
            vendor_factor = (self.vendor.average_rating - 3.0) / 2.0  # Convert 3-5 scale to 0-1
            base_rating += max(0, vendor_factor)

        # Car age factor (-0.5 to 0 points)
        car_age = timezone.now().year - self.year
        if car_age <= 2:
            age_factor = 0
        elif car_age <= 5:
            age_factor = -0.1 * (car_age - 2)
        else:
            age_factor = -0.5
        base_rating += age_factor

        # Ensure rating is within bounds and round to nearest 0.5
        rating = max(0.0, min(5.0, base_rating))
        return round(rating * 2) / 2  # Round to nearest 0.5

    def update_calculated_rating(self):
        """Update the calculated rating"""
        self.calculated_rating = self.calculate_automatic_rating()
        self.last_rating_update = timezone.now()
        self.save(update_fields=['calculated_rating', 'last_rating_update'])

    def get_featured_priority(self):
        """Get priority order for featured cars (lower = higher priority)"""
        if self.is_currently_featured():
            return 1  # Featured cars get priority
        return 999  # Non-featured cars get lowest priority

    @classmethod
    def get_featured_cars_count(cls):
        """Get current count of featured cars"""
        return cls.objects.filter(
            is_approved=True,
            is_featured=True
        ).count()

    @classmethod
    def can_feature_more_cars(cls):
        """Check if more cars can be featured (max 9)"""
        return cls.get_featured_cars_count() < 9

    @classmethod
    def get_featured_cars_remaining(cls):
        """Get number of remaining featured car slots"""
        return max(0, 9 - cls.get_featured_cars_count())

    def can_be_featured(self):
        """Check if this specific car can be featured"""
        if not self.is_approved:
            return False, "Car must be approved before featuring"

        if self.is_currently_featured():
            return False, "Car is already featured"

        if not self.__class__.can_feature_more_cars():
            return False, "Maximum featured cars limit (9) reached"

        return True, "Car can be featured"

    def feature_car(self):
        """Feature this car"""
        can_feature, message = self.can_be_featured()
        if not can_feature:
            return False, message

        self.is_featured = True
        self.auto_featured = False
        self.save(update_fields=['is_featured', 'auto_featured'])
        return True, "Car has been featured successfully"

    def unfeature_car(self):
        """Remove featured status from this car"""
        if not self.is_currently_featured():
            return False, "Car is not currently featured"

        self.is_featured = False
        self.featured_until = None
        self.auto_featured = False
        self.save(update_fields=['is_featured', 'featured_until', 'auto_featured'])
        return True, "Featured status removed"

    class Meta:
        ordering = ['-created_at']


class HotDeal(models.Model):
    """Time-limited hot deals for cars"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='hot_deal_details')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Discount configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2,
                                       help_text="Percentage (0-100) or fixed amount")
    original_price = models.DecimalField(max_digits=12, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Time configuration
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Status
    is_active = models.BooleanField(default=True)
    auto_activate = models.BooleanField(default=True, help_text="Automatically activate/deactivate based on dates")

    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    clicks_count = models.PositiveIntegerField(default=0)
    inquiries_count = models.PositiveIntegerField(default=0)

    # Notifications
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hot Deal: {self.title}"

    def is_currently_active(self):
        """Check if deal is currently active"""
        now = timezone.now()
        return (self.is_active and
                self.start_date <= now <= self.end_date)

    def time_remaining(self):
        """Get time remaining for the deal"""
        if not self.is_currently_active():
            return None
        return self.end_date - timezone.now()

    def time_remaining_formatted(self):
        """Get formatted time remaining"""
        remaining = self.time_remaining()
        if not remaining:
            return "Expired"

        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def calculate_discounted_price(self):
        """Calculate and update discounted price"""
        if self.discount_type == 'percentage':
            discount_amount = (self.original_price * self.discount_value) / 100
            self.discounted_price = self.original_price - discount_amount
        else:  # fixed
            self.discounted_price = self.original_price - self.discount_value

        # Ensure discounted price is not negative
        self.discounted_price = max(0, self.discounted_price)

    def save(self, *args, **kwargs):
        """Override save to calculate discounted price"""
        self.calculate_discounted_price()
        super().save(*args, **kwargs)

        # Update car's hot deal status
        if self.is_currently_active():
            self.car.is_hot_deal = True
            self.car.price = self.discounted_price
        else:
            self.car.is_hot_deal = False
            self.car.price = self.original_price
        self.car.save(update_fields=['is_hot_deal', 'price'])

    class Meta:
        ordering = ['-created_at']


class CarRating(models.Model):
    """Individual car ratings from customers"""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='ratings')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='car_ratings')

    # Rating details
    rating = models.DecimalField(max_digits=3, decimal_places=1,
                               help_text="Rating from 0.5 to 5.0 in 0.5 increments")
    review = models.TextField(blank=True)

    # Rating categories
    condition_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    value_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    service_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

    # Status
    is_verified = models.BooleanField(default=False, help_text="Verified purchase")
    is_approved = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.username} rated {self.car.title} - {self.rating} stars"

    def save(self, *args, **kwargs):
        """Override save to update car's calculated rating"""
        super().save(*args, **kwargs)
        # Update car's calculated rating
        self.car.update_calculated_rating()

    class Meta:
        ordering = ['-created_at']
        unique_together = ['car', 'customer']  # One rating per customer per car


class PromotionAnalytics(models.Model):
    """Analytics for promotion performance"""
    METRIC_TYPE_CHOICES = [
        ('featured_views', 'Featured Car Views'),
        ('featured_clicks', 'Featured Car Clicks'),
        ('hot_deal_views', 'Hot Deal Views'),
        ('hot_deal_clicks', 'Hot Deal Clicks'),
        ('tier_performance', 'Tier Performance'),
        ('rating_distribution', 'Rating Distribution'),
    ]

    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)

    # Metric data
    metric_value = models.PositiveIntegerField(default=0)
    metric_data = models.JSONField(default=dict, help_text="Additional metric data")

    # Time period
    date = models.DateField(auto_now_add=True)
    hour = models.PositiveIntegerField(default=0, help_text="Hour of the day (0-23)")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.metric_value}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'date']),
            models.Index(fields=['car', 'metric_type']),
            models.Index(fields=['vendor', 'metric_type']),
        ]


class CarImage(models.Model):
    """Additional images for cars"""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='cars/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Image for {self.car}"

    class Meta:
        ordering = ['order']


class ImportRequest(models.Model):
    """Car import requests from customers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('on_quotation', 'On Quotation'),
        ('processing', 'Processing'),
        ('fee_paid', 'Fee Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_requests')

    # Car Details
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    preferred_color = models.CharField(max_length=50, blank=True)

    # Import Details
    origin_country = models.CharField(max_length=100)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)

    # Additional Information
    special_requirements = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import Request: {self.year} {self.brand} {self.model} - {self.customer.username}"

    @property
    def vehicle_details(self):
        """Return formatted vehicle details string"""
        return f"{self.year} {self.brand} {self.model}"

    class Meta:
        ordering = ['-created_at']


class ImportOrder(models.Model):
    """Enhanced import order tracking with comprehensive workflow management"""

    # 7-Stage Import Process Status Choices
    STATUS_CHOICES = [
        ('import_request', 'Import Request'),
        ('auction_won', 'Auction Won'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('arrived_docked', 'Arrived - Docked'),
        ('under_clearance', 'Under Clearance'),
        ('registered', 'Registered'),
        ('ready_for_dispatch', 'Ready for Dispatch'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
    ]

    # Basic Order Information
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_orders')
    import_request = models.OneToOneField(ImportRequest, on_delete=models.CASCADE, related_name='import_order', null=True, blank=True)

    # Car Details
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    color = models.CharField(max_length=50, blank=True)
    engine_size = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(max_length=20, blank=True)
    transmission = models.CharField(max_length=20, blank=True)
    mileage = models.PositiveIntegerField(null=True, blank=True, help_text="Mileage in kilometers")

    # Import Details
    origin_country = models.CharField(max_length=100)
    origin_city = models.CharField(max_length=100, blank=True)

    # Status and Tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='import_request')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Financial Information
    quotation_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Auction Information
    auction_house = models.CharField(max_length=200, blank=True)
    auction_date = models.DateField(null=True, blank=True)
    winning_bid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Vehicle Identification
    chassis_number = models.CharField(max_length=100, blank=True, unique=True, null=True)
    engine_number = models.CharField(max_length=100, blank=True)

    # Shipping Information
    bill_of_lading = models.CharField(max_length=100, blank=True)
    vessel_name = models.CharField(max_length=200, blank=True)
    departure_port = models.CharField(max_length=100, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    arrival_port = models.CharField(max_length=100, default='Mombasa')
    estimated_arrival_date = models.DateField(null=True, blank=True)
    actual_arrival_date = models.DateField(null=True, blank=True)

    # Clearance and Registration
    customs_reference = models.CharField(max_length=100, blank=True)
    duty_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duty_paid_date = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=20, blank=True)
    registration_date = models.DateField(null=True, blank=True)

    # Delivery Information
    delivery_address = models.TextField(blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivery_contact_person = models.CharField(max_length=200, blank=True)
    delivery_contact_phone = models.CharField(max_length=20, blank=True)

    # Additional Information
    special_requirements = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import Order {self.order_number} - {self.year} {self.brand} {self.model}"

    @property
    def vehicle_details(self):
        """Return formatted vehicle details string"""
        return f"{self.year} {self.brand} {self.model}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import uuid
            self.order_number = f"IMP{timezone.now().year}{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        """Calculate progress percentage based on current status"""
        status_progress = {
            'quotation_pending': 5,
            'confirmed': 15,
            'auction_won': 25,
            'shipped': 40,
            'in_transit': 55,
            'arrived_docked': 70,
            'under_clearance': 80,
            'registered': 90,
            'ready_for_dispatch': 95,
            'delivered': 100,
            'cancelled': 0,
        }
        return status_progress.get(self.status, 0)

    @property
    def current_stage_number(self):
        """Get current stage number (1-7)"""
        stage_mapping = {
            'quotation_pending': 1,
            'confirmed': 1,
            'auction_won': 2,
            'shipped': 3,
            'in_transit': 4,
            'arrived_docked': 5,
            'under_clearance': 6,
            'registered': 6,
            'ready_for_dispatch': 7,
            'delivered': 7,
            'cancelled': 0,
        }
        return stage_mapping.get(self.status, 1)

    @property
    def estimated_days_remaining(self):
        """Calculate estimated days remaining based on current status"""
        if self.status == 'delivered':
            return 0

        # Base estimates for each stage
        days_mapping = {
            'quotation_pending': 30,
            'confirmed': 25,
            'auction_won': 20,
            'shipped': 15,
            'in_transit': 10,
            'arrived_docked': 7,
            'under_clearance': 5,
            'registered': 3,
            'ready_for_dispatch': 1,
        }
        return days_mapping.get(self.status, 30)

    def get_progress_percentage(self):
        """Calculate progress percentage based on current status"""
        status_progress = {
            'quotation_pending': 5,
            'confirmed': 15,
            'auction_won': 25,
            'shipped': 35,
            'in_transit': 50,
            'arrived_docked': 65,
            'under_clearance': 75,
            'registered': 85,
            'ready_for_dispatch': 95,
            'delivered': 100,
        }
        return status_progress.get(self.status, 0)

    def get_status_color(self):
        """Return color class for status"""
        status_colors = {
            'confirmed': 'blue',
            'auction_won': 'green',
            'shipped': 'indigo',
            'in_transit': 'yellow',
            'arrived_docked': 'purple',
            'under_clearance': 'orange',
            'registered': 'teal',
            'ready_for_dispatch': 'pink',
            'delivered': 'green',
            'cancelled': 'red',
        }
        return status_colors.get(self.status, 'gray')

    def get_status_icon(self):
        """Return FontAwesome icon for status"""
        status_icons = {
            'confirmed': 'check-circle',
            'auction_won': 'gavel',
            'shipped': 'ship',
            'in_transit': 'route',
            'arrived_docked': 'anchor',
            'under_clearance': 'file-signature',
            'registered': 'certificate',
            'ready_for_dispatch': 'truck',
            'delivered': 'flag-checkered',
            'cancelled': 'times-circle',
        }
        return status_icons.get(self.status, 'circle')

    def get_balance_due(self):
        """Calculate balance due"""
        return self.total_cost - (self.amount_paid or 0)

    def get_payment_status_color(self):
        """Return color class for payment status"""
        payment_colors = {
            'pending': 'red',
            'partial': 'yellow',
            'paid': 'green',
            'refunded': 'gray',
        }
        return payment_colors.get(self.payment_status, 'gray')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['chassis_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
        ]


class ImportOrderStatusHistory(models.Model):
    """Track status changes for import orders with complete audit trail"""

    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30, choices=ImportOrder.STATUS_CHOICES, blank=True)
    new_status = models.CharField(max_length=30, choices=ImportOrder.STATUS_CHOICES)

    # Change Information
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_changes_made')
    change_reason = models.TextField(blank=True, help_text="Reason for status change")
    admin_notes = models.TextField(blank=True, help_text="Internal notes for this status change")
    customer_notification_sent = models.BooleanField(default=False)

    # Additional Data for specific statuses
    estimated_date = models.DateField(null=True, blank=True, help_text="Estimated date for next milestone")
    actual_date = models.DateField(null=True, blank=True, help_text="Actual date when status was achieved")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.import_order.order_number}: {self.previous_status} → {self.new_status}"

    def get_status_icon(self):
        """Return FontAwesome icon for the status"""
        status_icons = {
            'import_request': 'file-import',
            'auction_won': 'gavel',
            'shipped': 'ship',
            'in_transit': 'route',
            'arrived_docked': 'anchor',
            'under_clearance': 'file-signature',
            'registered': 'certificate',
            'ready_for_dispatch': 'truck',
            'delivered': 'flag-checkered',
        }
        return status_icons.get(self.new_status, 'circle')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Import Order Status History"
        verbose_name_plural = "Import Order Status Histories"


class ImportOrderDocument(models.Model):
    """Store and manage documents related to import orders"""

    DOCUMENT_TYPE_CHOICES = [
        ('quotation', 'Quotation'),
        ('invoice', 'Invoice'),
        ('payment_receipt', 'Payment Receipt'),
        ('auction_certificate', 'Auction Certificate'),
        ('inspection_report', 'Inspection Report'),
        ('bill_of_lading', 'Bill of Lading'),
        ('shipping_manifest', 'Shipping Manifest'),
        ('customs_declaration', 'Customs Declaration'),
        ('duty_payment_receipt', 'Duty Payment Receipt'),
        ('registration_certificate', 'Registration Certificate'),
        ('delivery_receipt', 'Delivery Receipt'),
        ('other', 'Other Document'),
    ]

    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # File Information
    document_file = models.FileField(upload_to='import_orders/documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Access Control
    is_customer_visible = models.BooleanField(default=True, help_text="Whether customer can view this document")
    is_confidential = models.BooleanField(default=False, help_text="Mark as confidential (admin only)")

    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.import_order.order_number} - {self.title}"

    def save(self, *args, **kwargs):
        if self.document_file:
            self.file_size = self.document_file.size
        super().save(*args, **kwargs)

    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if not self.file_size:
            return "Unknown"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['import_order', 'document_type']),
            models.Index(fields=['document_type']),
        ]


class SparePartCategory(models.Model):
    """Spare parts categories for better organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Spare Part Categories"


class Supplier(models.Model):
    """Suppliers for spare parts inventory"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)

    # Business Details
    tax_number = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g., Net 30 days")

    # Status
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Supplier rating out of 5")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SparePart(models.Model):
    """Enhanced spare parts inventory with comprehensive stock management"""
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]

    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('set', 'Set'),
        ('pair', 'Pair'),
        ('kit', 'Kit'),
        ('liter', 'Liter'),
        ('meter', 'Meter'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='spare_parts')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='spare_parts')

    # Part Information
    name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    category = models.CharField(max_length=100)  # Keep original field
    category_new = models.ForeignKey(SparePartCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='parts')

    # Compatibility
    compatible_brands = models.ManyToManyField(CarBrand, blank=True)
    compatible_models = models.ManyToManyField(CarModel, blank=True)
    year_from = models.PositiveIntegerField(null=True, blank=True)
    year_to = models.PositiveIntegerField(null=True, blank=True)

    # Details
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    description = models.TextField()
    specifications = models.TextField(blank=True, help_text="Technical specifications")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H in cm")

    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Purchase cost")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Enhanced Inventory Management
    stock_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0, help_text="Quantity reserved for pending orders")
    minimum_stock = models.PositiveIntegerField(default=5, help_text="Minimum stock level for reorder alerts")
    maximum_stock = models.PositiveIntegerField(default=100, help_text="Maximum stock level")
    reorder_point = models.PositiveIntegerField(default=10, help_text="Automatic reorder trigger point")
    reorder_quantity = models.PositiveIntegerField(default=20, help_text="Quantity to reorder")

    # Location and Storage
    warehouse_location = models.CharField(max_length=100, blank=True, help_text="Warehouse/shelf location")
    storage_conditions = models.CharField(max_length=200, blank=True, help_text="Special storage requirements")

    # Status
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_discontinued = models.BooleanField(default=False)

    # Images
    main_image = models.ImageField(upload_to='spare_parts/', blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.vendor.company_name}"

    def is_in_stock(self):
        return self.available_quantity > 0 and self.is_available

    @property
    def available_quantity(self):
        """Available quantity excluding reserved stock"""
        return max(0, self.stock_quantity - self.reserved_quantity)

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.stock_quantity <= self.minimum_stock

    @property
    def needs_reorder(self):
        """Check if stock needs reordering"""
        return self.stock_quantity <= self.reorder_point

    @property
    def stock_value(self):
        """Calculate total stock value"""
        if self.cost_price:
            return self.stock_quantity * self.cost_price
        return self.stock_quantity * self.price

    def get_category_display(self):
        """Get category for display (backward compatibility)"""
        if self.category_new:
            return str(self.category_new)
        return self.category

    class Meta:
        ordering = ['-created_at']


class SparePartImage(models.Model):
    """Additional images for spare parts"""
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='spare_parts/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Image for {self.spare_part.name}"

    class Meta:
        ordering = ['order']


class PurchaseOrder(models.Model):
    """Purchase orders for restocking spare parts"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Order Information
    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')

    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateField(null=True, blank=True)

    # Financial
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Additional Information
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"

    def calculate_totals(self):
        """Calculate order totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.total_amount for item in items)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost
        self.save()

    class Meta:
        ordering = ['-created_at']


class PurchaseOrderItem(models.Model):
    """Line items for purchase orders"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)

    # Quantities
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)

    # Pricing
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Additional Information
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity_ordered * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.spare_part.name} - Qty: {self.quantity_ordered}"

    @property
    def quantity_pending(self):
        return self.quantity_ordered - self.quantity_received

    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered


class StockMovement(models.Model):
    """Track all stock movements for inventory management"""
    MOVEMENT_TYPE_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('transfer', 'Stock Transfer'),
        ('return', 'Return'),
        ('damaged', 'Damaged/Lost'),
    ]

    REASON_CHOICES = [
        ('purchase', 'Purchase Order'),
        ('sale', 'Sale'),
        ('return', 'Customer Return'),
        ('adjustment', 'Stock Adjustment'),
        ('damaged', 'Damaged Goods'),
        ('expired', 'Expired'),
        ('transfer', 'Warehouse Transfer'),
        ('initial', 'Initial Stock'),
    ]

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)

    # Quantities
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()

    # Reference
    reference_number = models.CharField(max_length=100, blank=True, help_text="PO number, invoice number, etc.")
    purchase_order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True)

    # Additional Information
    notes = models.TextField(blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.spare_part.name} - {self.movement_type} - {self.quantity}"

    class Meta:
        ordering = ['-created_at']


class InventoryAlert(models.Model):
    """Alerts for inventory management"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('reorder', 'Reorder Required'),
        ('overstock', 'Overstock'),
        ('expired', 'Expired Items'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Alert Details
    message = models.TextField()
    current_stock = models.PositiveIntegerField()
    threshold_value = models.PositiveIntegerField(null=True, blank=True)

    # Actions
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.alert_type} - {self.spare_part.name}"

    class Meta:
        ordering = ['-created_at']


class Cart(models.Model):
    """Shopping cart for spare parts"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of adding to cart
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity}x {self.spare_part.name}"

    @property
    def total_price(self):
        return self.quantity * self.price

    class Meta:
        unique_together = ['cart', 'spare_part']


class Order(models.Model):
    """Customer orders for spare parts"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    # Order Information
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    # Shipping Information
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default='Kenya')

    # Financial Information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Additional Information
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"

    def calculate_totals(self):
        """Calculate order totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        self.save()

    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'paid']

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Line items for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)  # Track which vendor supplied the part

    # Product details at time of order
    part_name = models.CharField(max_length=200)
    part_sku = models.CharField(max_length=100)
    part_description = models.TextField(blank=True)

    # Quantities and Pricing
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        # Auto-populate part details
        if not self.part_name:
            self.part_name = self.spare_part.name
        if not self.part_sku:
            self.part_sku = self.spare_part.sku
        if not self.part_description:
            self.part_description = self.spare_part.description
        if not self.vendor_id:
            self.vendor = self.spare_part.vendor

        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.part_name} - Order {self.order.order_number}"


class Payment(models.Model):
    """Payment records for orders"""
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    # Payment Information
    payment_id = models.CharField(max_length=100, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Amount Information
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')

    # M-Pesa Specific Fields
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_transaction_id = models.CharField(max_length=100, blank=True)
    mpesa_phone_number = models.CharField(max_length=20, blank=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)

    # Gateway Response
    gateway_response = models.JSONField(blank=True, null=True)
    failure_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.order.order_number}"

    class Meta:
        ordering = ['-created_at']


class Invoice(models.Model):
    """Invoices for orders"""
    invoice_number = models.CharField(max_length=50, unique=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')

    # Invoice Details
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    # Company Information (can be customized per invoice)
    company_name = models.CharField(max_length=200, default='Gurumisha Motors')
    company_address = models.TextField(default='Nairobi, Kenya')
    company_phone = models.CharField(max_length=20, default='+254700000000')
    company_email = models.EmailField(default='info@gurumisha.com')

    # Additional Information
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)

    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.order.order_number}"

    class Meta:
        ordering = ['-created_at']


class Inquiry(models.Model):
    """Customer inquiries for cars and spare parts"""
    INQUIRY_TYPE_CHOICES = [
        ('car', 'Car Inquiry'),
        ('spare_part', 'Spare Part Inquiry'),
        ('import', 'Import Inquiry'),
        ('general', 'General Inquiry'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPE_CHOICES)

    # Related Objects (optional)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, null=True, blank=True, related_name='inquiries')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, null=True, blank=True, related_name='inquiries')

    # Inquiry Details
    subject = models.CharField(max_length=200)
    message = models.TextField()
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.customer.username}"

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    """Messages between customers and vendors"""
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')

    content = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"

    class Meta:
        ordering = ['created_at']


class Testimonial(models.Model):
    """Customer testimonials"""
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials')

    # Content
    content = models.TextField()
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars

    # Related Purchase (optional)
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)

    # Display Settings
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.customer.username} - {self.rating} stars"

    class Meta:
        ordering = ['-created_at']


class BlogPost(models.Model):
    """Blog posts for content marketing"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    # Images
    featured_image = models.ImageField(upload_to='blog/', blank=True)

    # Status
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    class Meta:
        ordering = ['-published_at', '-created_at']


class Notification(models.Model):
    """System notifications for users"""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('system', 'System'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, help_text="Optional URL for action button")
    action_text = models.CharField(max_length=50, blank=True, help_text="Text for action button")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]


class SystemSetting(models.Model):
    """System-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

    class Meta:
        ordering = ['key']


class ActivityLog(models.Model):
    """Track user activities across the system"""
    ACTION_CHOICES = [
        # Authentication
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('register', 'User Registration'),
        ('password_change', 'Password Change'),

        # Profile & Settings
        ('profile_update', 'Profile Update'),
        ('settings_change', 'Settings Change'),
        ('avatar_upload', 'Avatar Upload'),

        # Car Management
        ('car_create', 'Car Created'),
        ('car_update', 'Car Updated'),
        ('car_delete', 'Car Deleted'),
        ('car_view', 'Car Viewed'),
        ('car_approve', 'Car Approved'),
        ('car_reject', 'Car Rejected'),

        # Import Management
        ('import_request_create', 'Import Request Created'),
        ('import_request_update', 'Import Request Updated'),
        ('import_status_change', 'Import Status Changed'),
        ('import_document_upload', 'Import Document Uploaded'),

        # Spare Parts
        ('spare_part_create', 'Spare Part Created'),
        ('spare_part_update', 'Spare Part Updated'),
        ('spare_part_delete', 'Spare Part Deleted'),
        ('spare_part_view', 'Spare Part Viewed'),

        # Orders & Payments
        ('order_create', 'Order Created'),
        ('order_update', 'Order Updated'),
        ('order_cancel', 'Order Cancelled'),
        ('payment_made', 'Payment Made'),
        ('payment_failed', 'Payment Failed'),

        # Communication
        ('inquiry_create', 'Inquiry Created'),
        ('inquiry_respond', 'Inquiry Responded'),
        ('message_send', 'Message Sent'),

        # Admin Actions
        ('user_approve', 'User Approved'),
        ('user_suspend', 'User Suspended'),
        ('vendor_approve', 'Vendor Approved'),
        ('system_setting_change', 'System Setting Changed'),

        # Search & Browse
        ('search_performed', 'Search Performed'),
        ('filter_applied', 'Filter Applied'),
        ('page_view', 'Page Viewed'),

        # File Operations
        ('file_upload', 'File Uploaded'),
        ('file_download', 'File Downloaded'),
        ('file_delete', 'File Deleted'),
    ]

    # Core Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(help_text="Human-readable description of the action")

    # Context Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    # Object Information (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Additional Data
    extra_data = models.JSONField(default=dict, blank=True, help_text="Additional context data")

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]


class AuditLog(models.Model):
    """Comprehensive audit trail for security and compliance"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Change'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('system_config', 'System Configuration'),
        ('security_event', 'Security Event'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Core Audit Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    table_name = models.CharField(max_length=100, blank=True)
    record_id = models.CharField(max_length=100, blank=True)

    # Change Details
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    # Context
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')

    # Technical Details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)

    # Additional Context
    extra_data = models.JSONField(default=dict, blank=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.get_action_type_display()} - {self.description[:50]}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]

    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject_template = models.CharField(max_length=200, blank=True)
    body_template = models.TextField()

    # Template Variables
    available_variables = models.JSONField(default=list, help_text="List of available template variables")

    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="1=Low, 2=Medium, 3=High, 4=Critical")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    class Meta:
        ordering = ['name']


class NotificationPreference(models.Model):
    """User preferences for different types of notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')

    # Email Notifications
    email_enabled = models.BooleanField(default=True)
    email_order_updates = models.BooleanField(default=True)
    email_import_updates = models.BooleanField(default=True)
    email_inquiry_responses = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    email_security_alerts = models.BooleanField(default=True)

    # SMS Notifications
    sms_enabled = models.BooleanField(default=False)
    sms_order_updates = models.BooleanField(default=False)
    sms_import_updates = models.BooleanField(default=False)
    sms_security_alerts = models.BooleanField(default=True)

    # Push Notifications
    push_enabled = models.BooleanField(default=True)
    push_order_updates = models.BooleanField(default=True)
    push_import_updates = models.BooleanField(default=True)
    push_inquiry_responses = models.BooleanField(default=True)
    push_marketing = models.BooleanField(default=False)

    # In-App Notifications
    in_app_enabled = models.BooleanField(default=True)
    in_app_order_updates = models.BooleanField(default=True)
    in_app_import_updates = models.BooleanField(default=True)
    in_app_inquiry_responses = models.BooleanField(default=True)
    in_app_system_updates = models.BooleanField(default=True)

    # Frequency Settings
    digest_frequency = models.CharField(max_length=20, choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], default='immediate')

    # Quiet Hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"


class NotificationQueue(models.Model):
    """Queue for managing notification delivery"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]

    # Core Information
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_queue')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, null=True, blank=True)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()

    # Delivery Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=1, help_text="1=Low, 2=Medium, 3=High, 4=Critical")

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Retry Logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Error Handling
    error_message = models.TextField(blank=True)

    # Context Data
    context_data = models.JSONField(default=dict, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.channel} notification to {self.recipient.username} - {self.status}"

    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['scheduled_at']),
        ]


class NotificationDeliveryLog(models.Model):
    """Log of all notification delivery attempts"""
    notification_queue = models.ForeignKey(NotificationQueue, on_delete=models.CASCADE, related_name='delivery_logs')

    # Delivery Details
    attempt_number = models.PositiveIntegerField()
    delivery_status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('rejected', 'Rejected'),
    ])

    # Response Information
    response_code = models.CharField(max_length=10, blank=True)
    response_message = models.TextField(blank=True)

    # Provider Information
    provider = models.CharField(max_length=50, blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)

    # Timing
    attempted_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attempt {self.attempt_number} - {self.delivery_status}"

    class Meta:
        ordering = ['-attempted_at']


class ProfileView(models.Model):
    """Track profile views for analytics"""
    profile_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views_received')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile_views_made')
    viewer_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile_user', 'viewed_at']),
            models.Index(fields=['viewer', 'viewed_at']),
            models.Index(fields=['viewer_ip', 'viewed_at']),
        ]

    def __str__(self):
        viewer_name = self.viewer.username if self.viewer else f"Anonymous ({self.viewer_ip})"
        return f"{viewer_name} viewed {self.profile_user.username}'s profile"


class VendorAnalytics(models.Model):
    """Vendor performance analytics"""
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='analytics')

    # Profile metrics
    total_profile_views = models.PositiveIntegerField(default=0)
    unique_profile_views = models.PositiveIntegerField(default=0)
    profile_views_this_month = models.PositiveIntegerField(default=0)
    profile_views_last_month = models.PositiveIntegerField(default=0)

    # Engagement metrics
    total_inquiries = models.PositiveIntegerField(default=0)
    inquiries_this_month = models.PositiveIntegerField(default=0)
    inquiry_response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_response_time_hours = models.PositiveIntegerField(default=24)

    # Sales metrics
    total_sales = models.PositiveIntegerField(default=0)
    sales_this_month = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    revenue_this_month = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    # Listing metrics
    active_listings = models.PositiveIntegerField(default=0)
    featured_listings = models.PositiveIntegerField(default=0)
    sold_listings = models.PositiveIntegerField(default=0)
    average_listing_views = models.PositiveIntegerField(default=0)

    # Rating metrics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_ratings = models.PositiveIntegerField(default=0)
    five_star_ratings = models.PositiveIntegerField(default=0)
    four_star_ratings = models.PositiveIntegerField(default=0)
    three_star_ratings = models.PositiveIntegerField(default=0)
    two_star_ratings = models.PositiveIntegerField(default=0)
    one_star_ratings = models.PositiveIntegerField(default=0)

    # Performance scores (0-100)
    profile_completion_score = models.PositiveIntegerField(default=0)
    customer_satisfaction_score = models.PositiveIntegerField(default=0)
    response_time_score = models.PositiveIntegerField(default=0)
    overall_performance_score = models.PositiveIntegerField(default=0)

    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        vendor = self.vendor
        user = vendor.user

        fields_to_check = [
            # User fields
            (user.first_name, 10),
            (user.last_name, 10),
            (user.email, 5),
            (user.phone, 5),
            (user.profile_picture, 10),
            (user.bio, 10),

            # Vendor fields
            (vendor.company_name, 10),
            (vendor.description, 15),
            (vendor.business_phone, 5),
            (vendor.physical_address, 5),
            (vendor.company_logo, 10),
            (vendor.website, 5),
        ]

        total_score = 0
        for field_value, weight in fields_to_check:
            if field_value:
                total_score += weight

        self.profile_completion_score = min(total_score, 100)
        return self.profile_completion_score

    def calculate_performance_scores(self):
        """Calculate various performance scores"""
        # Response time score (inverse relationship)
        if self.average_response_time_hours <= 1:
            self.response_time_score = 100
        elif self.average_response_time_hours <= 6:
            self.response_time_score = 90
        elif self.average_response_time_hours <= 24:
            self.response_time_score = 75
        elif self.average_response_time_hours <= 48:
            self.response_time_score = 50
        else:
            self.response_time_score = 25

        # Customer satisfaction score based on ratings
        if self.total_ratings > 0:
            weighted_score = (
                (self.five_star_ratings * 5) +
                (self.four_star_ratings * 4) +
                (self.three_star_ratings * 3) +
                (self.two_star_ratings * 2) +
                (self.one_star_ratings * 1)
            )
            average_rating = weighted_score / self.total_ratings
            self.customer_satisfaction_score = int((average_rating / 5) * 100)
        else:
            self.customer_satisfaction_score = 0

        # Overall performance score (weighted average)
        self.overall_performance_score = int(
            (self.profile_completion_score * 0.3) +
            (self.customer_satisfaction_score * 0.4) +
            (self.response_time_score * 0.3)
        )

    def update_analytics(self):
        """Update all analytics data"""
        self.calculate_profile_completion()
        self.calculate_performance_scores()
        self.save()

    def __str__(self):
        return f"Analytics for {self.vendor.company_name}"


class UserActivityLog(models.Model):
    """Track user activities for analytics"""
    ACTION_CHOICES = [
        ('profile_view', 'Profile View'),
        ('profile_update', 'Profile Update'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('inquiry_sent', 'Inquiry Sent'),
        ('inquiry_received', 'Inquiry Received'),
        ('listing_created', 'Listing Created'),
        ('listing_updated', 'Listing Updated'),
        ('listing_viewed', 'Listing Viewed'),
        ('order_placed', 'Order Placed'),
        ('payment_made', 'Payment Made'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"
