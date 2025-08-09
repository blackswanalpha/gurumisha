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

    # Override email field to make it unique
    email = models.EmailField(unique=True, help_text="Email address must be unique")

    # Override username field to remove default validators
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer.',
        validators=[],  # Remove all default validators
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )

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



class CarMake(models.Model):
    """Enhanced car makes with additional metadata"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Make description and history")
    country_of_origin = models.CharField(max_length=100, blank=True, help_text="Country where make originated")
    logo = models.ImageField(upload_to='makes/', blank=True)
    logo_url = models.URLField(blank=True, help_text="Alternative logo URL if not uploaded")
    website = models.URLField(blank=True, help_text="Official make website")
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False, help_text="Mark as premium/luxury make")
    display_order = models.PositiveIntegerField(default=0, help_text="Order for display in lists")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order', 'name']


class VehicleCondition(models.Model):
    """Vehicle condition types with flexible management"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, help_text="Detailed description of this condition")
    display_order = models.PositiveIntegerField(default=0, help_text="Order for display in forms")
    is_active = models.BooleanField(default=True)
    color_code = models.CharField(max_length=7, blank=True, help_text="Hex color code for UI display")
    icon_class = models.CharField(max_length=50, blank=True, help_text="CSS icon class for display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Vehicle Condition"
        verbose_name_plural = "Vehicle Conditions"


class CarModel(models.Model):
    """Enhanced car models with additional specifications"""
    BODY_TYPE_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('pickup', 'Pickup Truck'),
        ('van', 'Van'),
        ('crossover', 'Crossover'),
        ('sports', 'Sports Car'),
        ('luxury', 'Luxury'),
        ('compact', 'Compact'),
        ('other', 'Other'),
    ]

    make = models.ForeignKey(CarMake, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES, blank=True)
    engine_options = models.TextField(blank=True, help_text="Available engine options (comma-separated)")
    model_year_start = models.PositiveIntegerField(null=True, blank=True, help_text="First year this model was produced")
    model_year_end = models.PositiveIntegerField(null=True, blank=True, help_text="Last year this model was produced (blank if still in production)")
    description = models.TextField(blank=True, help_text="Model description and key features")
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular model for featured display")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.make.name} {self.name}"

    class Meta:
        ordering = ['make__name', 'name']
        unique_together = ['make', 'name']

    def get_production_years(self):
        """Get production year range as string"""
        if self.model_year_start:
            if self.model_year_end:
                return f"{self.model_year_start}-{self.model_year_end}"
            else:
                return f"{self.model_year_start}-Present"
        return "Unknown"


# Aliases for consistency
VehicleMake = CarMake
VehicleModel = CarModel
# Legacy aliases for backward compatibility
CarBrand = CarMake
VehicleBrand = CarMake


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

    # CONDITION_CHOICES moved to VehicleCondition model

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
    make = models.ForeignKey(CarMake, on_delete=models.CASCADE, null=True, blank=True)
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE, null=True, blank=True)
    year = models.PositiveIntegerField()
    condition = models.ForeignKey(VehicleCondition, on_delete=models.CASCADE, null=True, blank=True)

    # Fallback string fields for when using hardcoded choices
    make_name = models.CharField(max_length=100, blank=True, help_text="Make name when not using database makes")
    model_name = models.CharField(max_length=100, blank=True, help_text="Model name when not using database models")
    condition_name = models.CharField(max_length=50, blank=True, help_text="Condition when not using database conditions")

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

    # Location Information
    area = models.CharField(max_length=200, blank=True, help_text="Specific area/neighborhood where the car is located")
    city = models.CharField(max_length=100, blank=True, help_text="City where the car is located")
    country = models.CharField(max_length=100, blank=True, help_text="Country where the car is located")

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
        make_name = self.make.name if self.make else self.make_name
        model_name = self.model.name if self.model else self.model_name
        return f"{self.year} {make_name} {model_name}"

    def get_make_name(self):
        """Get make name from either database model or string field"""
        return self.make.name if self.make else self.make_name

    def get_model_name(self):
        """Get model name from either database model or string field"""
        return self.model.name if self.model else self.model_name

    def get_condition_name(self):
        """Get condition name from either database model or string field"""
        return self.condition.name if self.condition else self.condition_name

    def get_absolute_url(self):
        return reverse('car_detail', kwargs={'pk': self.pk})

    def get_features_list(self):
        """Return features as a list"""
        if self.features:
            return [feature.strip() for feature in self.features.split(',')]
        return []

    def get_gallery_images(self):
        """Get all gallery images ordered by priority"""
        return self.images.all().order_by('order', '-is_primary', '-created_at')

    def get_primary_gallery_image(self):
        """Get the primary gallery image or first available image"""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    def get_display_image(self):
        """Get the best image to display (main_image or primary gallery image)"""
        if self.main_image:
            return self.main_image
        primary_gallery = self.get_primary_gallery_image()
        return primary_gallery.image if primary_gallery else None

    def get_all_images(self):
        """Get all images including main_image and gallery images"""
        images = []
        if self.main_image:
            images.append({
                'url': self.main_image.url,
                'caption': 'Main Image',
                'is_main': True,
                'is_primary': True
            })

        for img in self.get_gallery_images():
            images.append({
                'url': img.image.url,
                'caption': img.caption or f'Gallery Image {img.order + 1}',
                'is_main': False,
                'is_primary': img.is_primary,
                'id': img.id
            })

        return images

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
        from decimal import Decimal

        if self.discount_type == 'percentage':
            # Convert to Decimal to avoid float/Decimal multiplication issues
            discount_value_decimal = Decimal(str(self.discount_value))
            discount_amount = (self.original_price * discount_value_decimal) / Decimal('100')
            self.discounted_price = self.original_price - discount_amount
        else:  # fixed
            self.discounted_price = self.original_price - self.discount_value

        # Ensure discounted price is not negative
        self.discounted_price = max(Decimal('0'), self.discounted_price)

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
    """Enhanced additional images for cars with gallery support"""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='cars/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False, help_text="Set as primary gallery image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.car} - {'Primary' if self.is_primary else 'Gallery'}"

    def save(self, *args, **kwargs):
        # Optimize image before saving
        if self.image and hasattr(self.image, 'file'):
            try:
                from .utils.image_optimization import optimize_car_image, validate_car_image

                # Validate image
                is_valid, error_msg = validate_car_image(self.image.file)
                if not is_valid:
                    raise ValueError(error_msg)

                # Optimize image
                optimized_image = optimize_car_image(self.image.file)
                self.image.save(
                    self.image.name,
                    optimized_image,
                    save=False
                )
            except ImportError:
                # Fallback if optimization utils are not available
                pass
            except Exception as e:
                # Log error but don't fail the save
                print(f"Image optimization error: {str(e)}")

        # Ensure only one primary image per car
        if self.is_primary:
            CarImage.objects.filter(car=self.car, is_primary=True).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        """Get thumbnail URL for the image"""
        # For now, return the original image URL
        # In production, you might want to use a thumbnail service
        return self.image.url if self.image else None

    @classmethod
    def get_primary_image(cls, car):
        """Get the primary image for a car"""
        try:
            return cls.objects.filter(car=car, is_primary=True).first()
        except cls.DoesNotExist:
            return None

    class Meta:
        ordering = ['order', '-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['car', 'is_primary']),
            models.Index(fields=['car', 'order']),
        ]


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
    make = models.CharField(max_length=100)
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
        return f"Import Request: {self.year} {self.make} {self.model} - {self.customer.username}"

    @property
    def vehicle_details(self):
        """Return formatted vehicle details string"""
        return f"{self.year} {self.make} {self.model}"

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
    make = models.CharField(max_length=100)
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
    chassis_number = models.CharField(max_length=100, blank=True, null=True)
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

    # GPS Tracking Information
    current_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, help_text="Current latitude coordinate")
    current_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, help_text="Current longitude coordinate")
    current_location_name = models.CharField(max_length=200, blank=True, help_text="Human-readable current location")
    last_location_update = models.DateTimeField(null=True, blank=True, help_text="When location was last updated")
    tracking_enabled = models.BooleanField(default=True, help_text="Enable GPS tracking for this order")

    # Additional Information
    special_requirements = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import Order {self.order_number} - {self.year} {self.make} {self.model}"

    @property
    def vehicle_details(self):
        """Return formatted vehicle details string"""
        return f"{self.year} {self.make} {self.model}"

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
        return (self.total_cost or 0) - (self.paid_amount or 0)

    def get_payment_status_color(self):
        """Return color class for payment status"""
        payment_colors = {
            'pending': 'red',
            'partial': 'yellow',
            'paid': 'green',
            'refunded': 'gray',
        }
        return payment_colors.get(self.payment_status, 'gray')

    # GPS Tracking Methods
    @property
    def current_coordinates(self):
        """Get current coordinates as a tuple"""
        if self.current_latitude and self.current_longitude:
            return (float(self.current_latitude), float(self.current_longitude))
        return None

    @property
    def current_coordinates_string(self):
        """Get current coordinates as a formatted string"""
        if self.current_latitude and self.current_longitude:
            return f"{self.current_latitude}, {self.current_longitude}"
        return "Location not available"

    @property
    def google_maps_url(self):
        """Generate Google Maps URL for current location"""
        if self.current_latitude and self.current_longitude:
            return f"https://maps.google.com/?q={self.current_latitude},{self.current_longitude}"
        return None

    def update_current_location(self, latitude, longitude, location_name='', user=None):
        """Update the current GPS location"""
        try:
            # Use update() to avoid model validation and unique constraint issues
            from django.db import transaction
            with transaction.atomic():
                ImportOrder.objects.filter(id=self.id).update(
                    current_latitude=latitude,
                    current_longitude=longitude,
                    current_location_name=location_name,
                    last_location_update=timezone.now()
                )
                # Refresh the instance to get updated values
                self.refresh_from_db(fields=[
                    'current_latitude', 'current_longitude',
                    'current_location_name', 'last_location_update'
                ])
        except Exception as e:
            print(f"Error updating location for order {self.order_number}: {e}")
            return

        # Create tracking history entry
        if user:
            from .models import LocationTrackingHistory
            LocationTrackingHistory.objects.create(
                import_order=self,
                latitude=latitude,
                longitude=longitude,
                tracking_source='manual',
                status_at_time=self.status,
                recorded_at=timezone.now(),
                created_by=user,
                notes=f"Location updated to: {location_name}" if location_name else "Location updated"
            )

    def get_current_location(self):
        """Get the current location object if it exists"""
        return self.locations.filter(is_current_location=True).first()

    def has_tracking_enabled(self):
        """Check if tracking is enabled for this order"""
        return self.tracking_enabled and self.status not in ['delivered', 'cancelled']

    def get_import_stages_timeline(self):
        """Get timeline data for import stages with status and progress"""
        stages = [
            {
                'id': 'import_request',
                'name': 'Import Request',
                'description': 'Initial import request submitted and being processed',
                'icon': 'file-alt',
                'status': 'import_request',
            },
            {
                'id': 'auction_won',
                'name': 'Auction Won',
                'description': 'Vehicle successfully purchased at auction',
                'icon': 'gavel',
                'status': 'auction_won',
            },
            {
                'id': 'shipped',
                'name': 'Shipped',
                'description': 'Vehicle loaded and shipped from origin port',
                'icon': 'ship',
                'status': 'shipped',
            },
            {
                'id': 'in_transit',
                'name': 'In Transit',
                'description': 'Vehicle is currently being transported',
                'icon': 'route',
                'status': 'in_transit',
            },
            {
                'id': 'arrived_docked',
                'name': 'Arrived & Docked',
                'description': 'Vehicle has arrived at destination port',
                'icon': 'anchor',
                'status': 'arrived_docked',
            },
            {
                'id': 'under_clearance',
                'name': 'Under Clearance',
                'description': 'Vehicle is going through customs clearance',
                'icon': 'clipboard-check',
                'status': 'under_clearance',
            },
            {
                'id': 'registered',
                'name': 'Registered',
                'description': 'Vehicle has been registered with local authorities',
                'icon': 'certificate',
                'status': 'registered',
            },
            {
                'id': 'ready_for_dispatch',
                'name': 'Ready for Dispatch',
                'description': 'Vehicle is ready for final delivery',
                'icon': 'truck',
                'status': 'ready_for_dispatch',
            },
            {
                'id': 'delivered',
                'name': 'Delivered',
                'description': 'Vehicle has been delivered to customer',
                'icon': 'check-circle',
                'status': 'delivered',
            },
        ]

        # Get status order for comparison
        status_order = [choice[0] for choice in self.STATUS_CHOICES if choice[0] != 'cancelled']
        current_status_index = status_order.index(self.status) if self.status in status_order else -1

        # Mark stages as completed, current, or pending
        for i, stage in enumerate(stages):
            stage_index = status_order.index(stage['status']) if stage['status'] in status_order else -1

            if stage_index < current_status_index:
                stage['is_completed'] = True
                stage['is_current'] = False
            elif stage_index == current_status_index:
                stage['is_completed'] = False
                stage['is_current'] = True
            else:
                stage['is_completed'] = False
                stage['is_current'] = False

            # Add location information if available
            stage['location'] = None
            stage['estimated_date'] = None
            stage['documents'] = []

            # Try to find related location for this stage
            if hasattr(self, 'locations'):
                location_types = {
                    'import_request': 'origin',
                    'auction_won': 'auction_house',
                    'shipped': 'departure_port',
                    'in_transit': 'current_position',
                    'arrived_docked': 'arrival_port',
                    'under_clearance': 'customs_facility',
                    'registered': 'registration_office',
                    'ready_for_dispatch': 'dispatch_center',
                    'delivered': 'delivery_address',
                }

                location_type = location_types.get(stage['status'])
                if location_type:
                    stage['location'] = self.locations.filter(location_type=location_type).first()

        return stages

    def save(self, *args, **kwargs):
        """Custom save method"""
        # Generate order number if empty
        if not self.order_number:
            import uuid
            self.order_number = f"IMP{timezone.now().year}{str(uuid.uuid4())[:8].upper()}"

        # Handle empty chassis_number to avoid issues
        if self.chassis_number == '':
            self.chassis_number = None

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['chassis_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['current_latitude', 'current_longitude']),
            models.Index(fields=['tracking_enabled', 'status']),
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
    name = models.CharField(max_length=100)
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
        unique_together = [['name', 'parent']]  # Allow same name with different parents


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

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='spare_parts', null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='spare_parts')

    # Part Information
    name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    category = models.CharField(max_length=100)  # Keep original field
    category_new = models.ForeignKey(SparePartCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='parts')

    # Compatibility
    compatible_makes = models.ManyToManyField(CarMake, blank=True)
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
        vendor_name = self.vendor.company_name if self.vendor else "Admin"
        return f"{self.name} - {vendor_name}"

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
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)  # Track which vendor supplied the part

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
        if not self.vendor_id and self.spare_part.vendor:
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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
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
        if self.order:
            return f"Payment {self.payment_id} - Order {self.order.order_number}"
        elif self.import_order:
            return f"Payment {self.payment_id} - Import Order {self.import_order.order_number}"
        else:
            return f"Payment {self.payment_id}"

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
    """Enhanced customer inquiries with admin response capabilities"""
    INQUIRY_TYPE_CHOICES = [
        ('car', 'Car Inquiry'),
        ('spare_part', 'Spare Part Inquiry'),
        ('import', 'Import Inquiry'),
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending_customer', 'Pending Customer Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    # Basic Information
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

    # Admin Management
    assigned_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inquiries',
        limit_choices_to={'role': 'admin'}
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Admin Response
    admin_response = models.TextField(blank=True, help_text="Admin's response to the inquiry")
    internal_notes = models.TextField(blank=True, help_text="Internal notes for admin use only")
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the inquiry was resolved")

    # Response Tracking
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    response_time_hours = models.PositiveIntegerField(null=True, blank=True, help_text="Hours to first response")
    resolution_time_hours = models.PositiveIntegerField(null=True, blank=True, help_text="Hours to resolution")

    # Customer Satisfaction
    customer_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        help_text="Customer satisfaction rating (1-5)"
    )
    customer_feedback = models.TextField(blank=True, help_text="Customer feedback on resolution")

    # Flags and Metadata
    is_escalated = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateTimeField(null=True, blank=True)

    # Email tracking
    customer_notified = models.BooleanField(default=False)
    last_notification_sent = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.customer.username} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Override save to track response and resolution times"""
        from django.utils import timezone

        # Track first response time
        if self.admin_response and not self.first_response_at:
            self.first_response_at = timezone.now()
            if self.created_at:
                time_diff = self.first_response_at - self.created_at
                self.response_time_hours = int(time_diff.total_seconds() / 3600)

        # Track resolution time
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
            if self.created_at:
                time_diff = self.resolved_at - self.created_at
                self.resolution_time_hours = int(time_diff.total_seconds() / 3600)

        # Track closure time
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if inquiry is overdue based on priority"""
        from django.utils import timezone
        if self.status in ['resolved', 'closed']:
            return False

        hours_since_created = (timezone.now() - self.created_at).total_seconds() / 3600

        # Define SLA hours based on priority
        sla_hours = {
            'critical': 2,
            'urgent': 4,
            'high': 8,
            'normal': 24,
            'low': 48,
        }

        return hours_since_created > sla_hours.get(self.priority, 24)

    @property
    def time_since_created(self):
        """Get human-readable time since creation"""
        from django.utils import timezone
        time_diff = timezone.now() - self.created_at

        if time_diff.days > 0:
            return f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

    def get_priority_color(self):
        """Get color class for priority display"""
        colors = {
            'low': 'text-gray-600 bg-gray-100',
            'normal': 'text-blue-600 bg-blue-100',
            'high': 'text-orange-600 bg-orange-100',
            'urgent': 'text-red-600 bg-red-100',
            'critical': 'text-red-800 bg-red-200',
        }
        return colors.get(self.priority, 'text-gray-600 bg-gray-100')

    def get_status_color(self):
        """Get color class for status display"""
        colors = {
            'new': 'text-blue-600 bg-blue-100',
            'open': 'text-yellow-600 bg-yellow-100',
            'in_progress': 'text-purple-600 bg-purple-100',
            'pending_customer': 'text-orange-600 bg-orange-100',
            'resolved': 'text-green-600 bg-green-100',
            'closed': 'text-gray-600 bg-gray-100',
            'escalated': 'text-red-600 bg-red-100',
        }
        return colors.get(self.status, 'text-gray-600 bg-gray-100')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_admin', 'status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_urgent', 'status']),
        ]


class InquiryResponse(models.Model):
    """Responses to customer inquiries - tracks conversation history"""
    RESPONSE_TYPE_CHOICES = [
        ('admin_reply', 'Admin Reply'),
        ('customer_reply', 'Customer Reply'),
        ('system_note', 'System Note'),
        ('status_change', 'Status Change'),
        ('assignment', 'Assignment Change'),
        ('escalation', 'Escalation'),
    ]

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='responses')
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPE_CHOICES)

    # Response details
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiry_responses')

    # Metadata
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to customer")
    is_email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    # Attachments
    attachment = models.FileField(upload_to='inquiry_attachments/', blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_response_type_display()} - {self.inquiry.subject}"

    class Meta:
        ordering = ['created_at']


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


# Enhanced Content Management Models

class ContentCategory(models.Model):
    """Categories for organizing content"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for category")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = "Content Categories"


class ContentTag(models.Model):
    """Tags for content organization"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6B7280', help_text="Hex color code for tag")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class BlogPost(models.Model):
    """Enhanced blog posts for content marketing"""
    CONTENT_TYPE_CHOICES = [
        ('article', 'Article'),
        ('guide', 'Guide'),
        ('infographic', 'Infographic'),
        ('opinion', 'Opinion'),
        ('news', 'News'),
        ('review', 'Review'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Brief summary of the content")

    # Content Classification
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='article')
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(ContentTag, blank=True, related_name='posts')

    # Content Attributes
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, blank=True)
    estimated_read_time = models.PositiveIntegerField(default=5, help_text="Estimated reading time in minutes")

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    # Media
    featured_image = models.ImageField(upload_to='content/featured/', blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True, help_text="Alt text for featured image")
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")

    # Guide-specific fields
    pdf_file = models.FileField(upload_to='content/guides/pdfs/%Y/%m/', blank=True,
                               help_text="PDF file for guides (max 10MB)")
    pdf_file_size = models.PositiveIntegerField(null=True, blank=True, help_text="PDF file size in bytes")
    pdf_download_count = models.PositiveIntegerField(default=0, help_text="Number of PDF downloads")

    # Infographic-specific fields
    chart_data = models.JSONField(blank=True, null=True, help_text="Chart configuration and data for infographics")
    chart_type = models.CharField(max_length=20, blank=True,
                                 choices=[
                                     ('bar', 'Bar Chart'),
                                     ('line', 'Line Chart'),
                                     ('pie', 'Pie Chart'),
                                     ('doughnut', 'Doughnut Chart'),
                                     ('radar', 'Radar Chart'),
                                     ('scatter', 'Scatter Plot'),
                                     ('bubble', 'Bubble Chart'),
                                     ('polar', 'Polar Area Chart'),
                                 ], help_text="Primary chart type for infographics")

    # News-specific fields
    news_source = models.CharField(max_length=200, blank=True, help_text="Source of the news article")
    news_location = models.CharField(max_length=200, blank=True, help_text="Location where news occurred")
    breaking_news = models.BooleanField(default=False, help_text="Mark as breaking news")
    news_priority = models.CharField(max_length=20, blank=True,
                                   choices=[
                                       ('low', 'Low Priority'),
                                       ('medium', 'Medium Priority'),
                                       ('high', 'High Priority'),
                                       ('urgent', 'Urgent'),
                                   ], help_text="News priority level")

    # Enhanced engagement fields
    comment_count = models.PositiveIntegerField(default=0, help_text="Number of approved comments")
    bookmark_count = models.PositiveIntegerField(default=0, help_text="Number of bookmarks")

    # Status and Publishing
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text="Show in featured content sections")
    published_at = models.DateTimeField(null=True, blank=True)

    # Engagement Metrics
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:resource_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        # Update PDF file size if PDF file exists
        if self.pdf_file:
            self.pdf_file_size = self.pdf_file.size

        super().save(*args, **kwargs)

    @property
    def content_type_display(self):
        """Get display name for content type"""
        return dict(self.CONTENT_TYPE_CHOICES).get(self.content_type, self.content_type)

    @property
    def pdf_file_size_formatted(self):
        """Return formatted PDF file size"""
        if not self.pdf_file_size:
            return "Unknown"

        size = self.pdf_file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def has_pdf(self):
        """Check if this guide has a PDF file"""
        return bool(self.pdf_file and self.content_type == 'guide')

    def increment_pdf_download(self):
        """Increment PDF download counter"""
        if self.has_pdf:
            self.pdf_download_count += 1
            self.save(update_fields=['pdf_download_count'])

    @property
    def has_chart_data(self):
        """Check if this infographic has chart data"""
        return bool(self.chart_data and self.content_type == 'infographic')

    def get_chart_config(self):
        """Get Chart.js configuration for this infographic"""
        if not self.has_chart_data:
            return None

        # Default configuration
        config = {
            'type': self.chart_type or 'bar',
            'data': self.chart_data.get('data', {}),
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': self.title,
                        'font': {
                            'size': 16,
                            'weight': 'bold'
                        }
                    },
                    'legend': {
                        'display': True,
                        'position': 'bottom'
                    }
                }
            }
        }

        # Merge with custom options if provided
        if 'options' in self.chart_data:
            config['options'].update(self.chart_data['options'])

        return config

    def set_chart_data(self, chart_type, data, options=None):
        """Set chart data for infographic"""
        self.chart_type = chart_type
        self.chart_data = {
            'data': data,
            'options': options or {}
        }
        self.save(update_fields=['chart_type', 'chart_data'])

    @property
    def is_news(self):
        """Check if this is a news post"""
        return self.content_type == 'news'

    @property
    def is_breaking_news(self):
        """Check if this is breaking news"""
        return self.is_news and self.breaking_news

    @property
    def has_poll(self):
        """Check if this opinion post has a poll"""
        return hasattr(self, 'poll') and self.content_type == 'opinion'

    def update_engagement_counts(self):
        """Update engagement metrics from related objects"""
        if hasattr(self, 'comments'):
            self.comment_count = self.comments.filter(is_approved=True).count()
        if hasattr(self, 'bookmarks'):
            self.bookmark_count = self.bookmarks.count()
        self.save(update_fields=['comment_count', 'bookmark_count'])

    def get_content_type_icon(self):
        """Get Font Awesome icon for content type"""
        icons = {
            'article': 'fas fa-newspaper',
            'guide': 'fas fa-book',
            'infographic': 'fas fa-chart-bar',
            'opinion': 'fas fa-comment-alt',
            'news': 'fas fa-rss',
            'review': 'fas fa-star',
        }
        return icons.get(self.content_type, 'fas fa-file-alt')

    def get_reading_progress_estimate(self, words_per_minute=200):
        """Calculate reading progress based on content length"""
        import re
        # Count words in content
        word_count = len(re.findall(r'\w+', self.content))
        return max(1, round(word_count / words_per_minute))

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Content Post"
        verbose_name_plural = "Content Posts"


class ContentSeries(models.Model):
    """Series for organizing related content"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    featured_image = models.ImageField(upload_to='content/series/', blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['sort_order', 'title']
        verbose_name_plural = "Content Series"


class ContentSeriesItem(models.Model):
    """Items in a content series"""
    series = models.ForeignKey(ContentSeries, on_delete=models.CASCADE, related_name='items')
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='series_items')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.series.title} - {self.post.title}"

    class Meta:
        ordering = ['order']
        unique_together = ['series', 'post']


class ContentView(models.Model):
    """Track content views for analytics"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='content_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View of {self.post.title} at {self.viewed_at}"

    class Meta:
        ordering = ['-viewed_at']


class ContentLike(models.Model):
    """Track content likes"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='content_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"

    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']


class ContentComment(models.Model):
    """Comments on content posts"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    class Meta:
        ordering = ['-created_at']


class ContentBookmark(models.Model):
    """User bookmarks for content"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.title}"

    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']


# Static Pages Management Models

class StaticPage(models.Model):
    """Static pages for website content management"""
    PAGE_TYPE_CHOICES = [
        ('about', 'About Us'),
        ('contact', 'Contact Us'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms of Service'),
        ('faq', 'FAQ'),
        ('help', 'Help Center'),
        ('custom', 'Custom Page'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    page_type = models.CharField(max_length=20, choices=PAGE_TYPE_CHOICES, default='custom')
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Brief description of the page")

    # SEO Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (60 chars max)")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (160 chars max)")
    meta_keywords = models.CharField(max_length=200, blank=True)

    # Media
    featured_image = models.ImageField(upload_to='static_pages/', blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    # Status and Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Show in featured sections")
    show_in_menu = models.BooleanField(default=False, help_text="Show in navigation menu")
    menu_order = models.PositiveIntegerField(default=0, help_text="Order in navigation menu")

    # Author and Timestamps
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='static_pages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    views_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:static_page', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['menu_order', 'title']
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"


# Enhanced Content Analytics Models

class ContentAnalytics(models.Model):
    """Daily analytics for content performance"""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()

    # Engagement Metrics
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    bookmarks = models.PositiveIntegerField(default=0)

    # Time Metrics
    avg_time_on_page = models.DurationField(null=True, blank=True)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Traffic Sources
    direct_traffic = models.PositiveIntegerField(default=0)
    search_traffic = models.PositiveIntegerField(default=0)
    social_traffic = models.PositiveIntegerField(default=0)
    referral_traffic = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.post.title} on {self.date}"

    class Meta:
        unique_together = ['post', 'date']
        ordering = ['-date']
        verbose_name = "Content Analytics"
        verbose_name_plural = "Content Analytics"


class ContentPerformanceReport(models.Model):
    """Monthly/Weekly performance reports for content"""
    REPORT_TYPE_CHOICES = [
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()

    # Summary Metrics
    total_views = models.PositiveIntegerField(default=0)
    total_unique_views = models.PositiveIntegerField(default=0)
    total_engagement = models.PositiveIntegerField(default=0)
    top_performing_posts = models.JSONField(default=list, blank=True)

    # Report Data
    report_data = models.JSONField(default=dict, blank=True)

    # Status
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Performance Report"
        verbose_name_plural = "Performance Reports"


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


class RecentlyViewedCar(models.Model):
    """Track recently viewed cars for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='recently_viewed_cars')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='recent_views')
    session_key = models.CharField(max_length=40, blank=True, help_text="For anonymous users")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
            models.Index(fields=['session_key', '-viewed_at']),
            models.Index(fields=['car', '-viewed_at']),
        ]
        unique_together = [
            ['user', 'car'],
            ['session_key', 'car'],
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} viewed {self.car.title}"
        return f"Anonymous user viewed {self.car.title}"


class Wishlist(models.Model):
    """User wishlist for saving favorite cars"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'car']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['car', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.car.title}"

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


# Messaging System Models

class Message(models.Model):
    """Admin-created messages and announcements for users"""

    MESSAGE_TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('newsletter', 'Newsletter'),
        ('alert', 'Alert'),
        ('promotion', 'Promotion'),
        ('maintenance', 'Maintenance Notice'),
        ('feature', 'Feature Update'),
        ('policy', 'Policy Update'),
        ('welcome', 'Welcome Message'),
    ]

    TARGET_AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('customers', 'Customers Only'),
        ('vendors', 'Vendors Only'),
        ('admins', 'Admins Only'),
        ('new_users', 'New Users (< 30 days)'),
        ('active_users', 'Active Users'),
        ('inactive_users', 'Inactive Users'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    title = models.CharField(max_length=200, help_text="Message title/headline")
    content = models.TextField(help_text="Message content (HTML supported)")
    excerpt = models.TextField(blank=True, help_text="Brief summary for previews")

    # Classification
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='announcement')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='all')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    # Display Settings
    show_as_popup = models.BooleanField(default=True, help_text="Show as popup modal")
    show_as_banner = models.BooleanField(default=False, help_text="Show as banner notification")
    show_in_dashboard = models.BooleanField(default=True, help_text="Show in user dashboard")

    # Styling Options
    background_color = models.CharField(max_length=7, default='#ffffff', help_text="Hex color code")
    text_color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
    icon_class = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")

    # Media
    featured_image = models.ImageField(upload_to='messages/images/', blank=True)
    featured_image_alt = models.CharField(max_length=200, blank=True)

    # Action Button
    action_button_text = models.CharField(max_length=50, blank=True, help_text="Call-to-action button text")
    action_button_url = models.URLField(blank=True, help_text="URL for action button")
    action_button_color = models.CharField(max_length=7, default='#dc2626', help_text="Button color (hex)")

    # Scheduling and Lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    publication_date = models.DateTimeField(null=True, blank=True, help_text="When to start showing")
    expiration_date = models.DateTimeField(null=True, blank=True, help_text="When to stop showing")

    # Targeting Rules
    min_user_age_days = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum user account age in days")
    max_user_age_days = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum user account age in days")
    require_email_verified = models.BooleanField(default=False)

    # Display Rules
    max_displays_per_user = models.PositiveIntegerField(default=1, help_text="Maximum times to show to each user")
    display_frequency_hours = models.PositiveIntegerField(default=24, help_text="Minimum hours between displays")
    auto_dismiss_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Auto-dismiss after X seconds")

    # Analytics
    total_views = models.PositiveIntegerField(default=0)
    total_clicks = models.PositiveIntegerField(default=0)
    total_dismissals = models.PositiveIntegerField(default=0)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_message_type_display()})"

    @property
    def is_active(self):
        """Check if message is currently active"""
        now = timezone.now()

        if self.status != 'active':
            return False

        if self.publication_date and now < self.publication_date:
            return False

        if self.expiration_date and now > self.expiration_date:
            return False

        return True

    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.total_views == 0:
            return 0
        return (self.total_clicks / self.total_views) * 100

    def get_absolute_url(self):
        return reverse('core:admin_message_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Auto-update status based on dates
        now = timezone.now()

        if self.status == 'scheduled' and self.publication_date and now >= self.publication_date:
            self.status = 'active'
        elif self.status == 'active' and self.expiration_date and now >= self.expiration_date:
            self.status = 'expired'

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'target_audience']),
            models.Index(fields=['publication_date', 'expiration_date']),
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['-priority', '-created_at']),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"


class MessageRead(models.Model):
    """Track which users have read/seen which messages"""

    ACTION_CHOICES = [
        ('viewed', 'Viewed'),
        ('clicked', 'Clicked'),
        ('dismissed', 'Dismissed'),
        ('ignored', 'Ignored'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reads')

    # Interaction Details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='viewed')
    display_count = models.PositiveIntegerField(default=1, help_text="Number of times shown to user")

    # Context Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer_url = models.URLField(blank=True)

    # Timing
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    action_taken_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} {self.action} '{self.message.title}'"

    def mark_action(self, action_type):
        """Mark a specific action taken by user"""
        self.action = action_type
        self.action_taken_at = timezone.now()
        self.save()

        # Update message analytics
        if action_type == 'clicked':
            self.message.total_clicks += 1
        elif action_type == 'dismissed':
            self.message.total_dismissals += 1

        self.message.save()

    class Meta:
        unique_together = ['message', 'user']
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['message', 'action']),
            models.Index(fields=['user', '-last_seen_at']),
            models.Index(fields=['action', '-action_taken_at']),
        ]
        verbose_name = "Message Read Record"
        verbose_name_plural = "Message Read Records"


class MessageSchedule(models.Model):
    """Advanced scheduling options for messages"""

    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='schedule')

    # Frequency Settings
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')

    # Time Settings
    send_time = models.TimeField(help_text="Time of day to send")
    timezone = models.CharField(max_length=50, default='UTC', help_text="Timezone for scheduling")

    # Weekly Settings
    weekdays = models.JSONField(default=list, blank=True, help_text="List of weekday numbers (0=Monday)")

    # Monthly Settings
    day_of_month = models.PositiveIntegerField(null=True, blank=True, help_text="Day of month (1-31)")

    # Recurrence Limits
    max_occurrences = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of times to send")
    end_date = models.DateField(null=True, blank=True, help_text="Stop recurring after this date")

    # Status
    is_active = models.BooleanField(default=True)
    occurrences_sent = models.PositiveIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Schedule for '{self.message.title}' - {self.get_frequency_display()}"

    def calculate_next_send_time(self):
        """Calculate the next time this message should be sent"""
        from datetime import datetime, timedelta
        import pytz

        if not self.is_active:
            return None

        # Check if we've reached max occurrences
        if self.max_occurrences and self.occurrences_sent >= self.max_occurrences:
            return None

        # Check if we've passed the end date
        if self.end_date and timezone.now().date() > self.end_date:
            return None

        tz = pytz.timezone(self.timezone)
        now = timezone.now().astimezone(tz)

        if self.frequency == 'once':
            if self.occurrences_sent > 0:
                return None
            return self.message.publication_date

        elif self.frequency == 'daily':
            next_date = now.date() + timedelta(days=1)

        elif self.frequency == 'weekly':
            # Find next occurrence based on weekdays
            days_ahead = 7  # Default to next week
            current_weekday = now.weekday()

            for weekday in sorted(self.weekdays):
                days_until = (weekday - current_weekday) % 7
                if days_until == 0:  # Today
                    if now.time() < self.send_time:
                        days_until = 0
                    else:
                        continue
                if days_until < days_ahead:
                    days_ahead = days_until
                    break

            next_date = now.date() + timedelta(days=days_ahead)

        elif self.frequency == 'monthly':
            if self.day_of_month:
                next_month = now.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                try:
                    next_date = next_month.replace(day=self.day_of_month).date()
                except ValueError:
                    # Handle months with fewer days
                    next_date = next_month.replace(day=28).date()
            else:
                next_date = now.date() + timedelta(days=30)

        else:
            return None

        # Combine date and time
        next_datetime = tz.localize(datetime.combine(next_date, self.send_time))
        return next_datetime.astimezone(pytz.UTC)

    def mark_sent(self):
        """Mark this schedule as having sent a message"""
        self.occurrences_sent += 1
        self.last_sent_at = timezone.now()
        self.next_send_at = self.calculate_next_send_time()
        self.save()

    class Meta:
        ordering = ['next_send_at']
        indexes = [
            models.Index(fields=['is_active', 'next_send_at']),
            models.Index(fields=['frequency', 'is_active']),
        ]
        verbose_name = "Message Schedule"
        verbose_name_plural = "Message Schedules"


class MessageTarget(models.Model):
    """Advanced targeting rules for messages"""

    CONDITION_CHOICES = [
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('contains', 'Contains'),
        ('not_contains', 'Does Not Contain'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('in_list', 'In List'),
        ('not_in_list', 'Not In List'),
    ]

    FIELD_CHOICES = [
        ('user.role', 'User Role'),
        ('user.date_joined', 'Registration Date'),
        ('user.last_login', 'Last Login Date'),
        ('user.is_email_verified', 'Email Verified'),
        ('user.city', 'City'),
        ('user.country', 'Country'),
        ('user.language', 'Language'),
        ('vendor.is_verified', 'Vendor Verified'),
        ('vendor.company_name', 'Company Name'),
        ('car_count', 'Number of Cars Listed'),
        ('order_count', 'Number of Orders'),
        ('login_count', 'Login Count'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='targeting_rules')

    # Targeting Rule
    field_name = models.CharField(max_length=50, choices=FIELD_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    value = models.TextField(help_text="Value to compare against")

    # Logic
    is_required = models.BooleanField(default=True, help_text="Must match for user to see message")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message.title}: {self.field_name} {self.condition} {self.value}"

    def evaluate_for_user(self, user):
        """Evaluate if this targeting rule matches for a given user"""
        try:
            # Get the actual value from the user
            if self.field_name.startswith('user.'):
                field_path = self.field_name[5:]  # Remove 'user.' prefix
                actual_value = getattr(user, field_path, None)
            elif self.field_name.startswith('vendor.') and hasattr(user, 'vendor'):
                field_path = self.field_name[7:]  # Remove 'vendor.' prefix
                actual_value = getattr(user.vendor, field_path, None)
            elif self.field_name == 'car_count':
                actual_value = user.cars.count() if hasattr(user, 'cars') else 0
            elif self.field_name == 'order_count':
                actual_value = user.orders.count() if hasattr(user, 'orders') else 0
            elif self.field_name == 'login_count':
                actual_value = user.activity_logs.filter(action='login').count()
            else:
                return False

            # Convert values for comparison
            target_value = self.value

            # Handle different data types
            if isinstance(actual_value, bool):
                target_value = target_value.lower() in ['true', '1', 'yes']
            elif isinstance(actual_value, int):
                try:
                    target_value = int(target_value)
                except ValueError:
                    return False
            elif hasattr(actual_value, 'date'):  # DateTime field
                from datetime import datetime
                try:
                    target_value = datetime.strptime(target_value, '%Y-%m-%d').date()
                    actual_value = actual_value.date() if hasattr(actual_value, 'date') else actual_value
                except ValueError:
                    return False

            # Perform comparison based on condition
            if self.condition == 'equals':
                return actual_value == target_value
            elif self.condition == 'not_equals':
                return actual_value != target_value
            elif self.condition == 'contains':
                return target_value in str(actual_value)
            elif self.condition == 'not_contains':
                return target_value not in str(actual_value)
            elif self.condition == 'greater_than':
                return actual_value > target_value
            elif self.condition == 'less_than':
                return actual_value < target_value
            elif self.condition == 'in_list':
                target_list = [item.strip() for item in target_value.split(',')]
                return str(actual_value) in target_list
            elif self.condition == 'not_in_list':
                target_list = [item.strip() for item in target_value.split(',')]
                return str(actual_value) not in target_list

        except Exception as e:
            # Log error and return False for safety
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating targeting rule {self.id}: {e}")
            return False

        return False

    class Meta:
        ordering = ['message', 'field_name']
        indexes = [
            models.Index(fields=['message', 'is_required']),
        ]
        verbose_name = "Message Target Rule"
        verbose_name_plural = "Message Target Rules"


class MessageAnalytics(models.Model):
    """Daily analytics for message performance"""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='daily_analytics')
    date = models.DateField()

    # Display Metrics
    total_displays = models.PositiveIntegerField(default=0)
    unique_users_shown = models.PositiveIntegerField(default=0)

    # Interaction Metrics
    total_clicks = models.PositiveIntegerField(default=0)
    unique_users_clicked = models.PositiveIntegerField(default=0)
    total_dismissals = models.PositiveIntegerField(default=0)
    unique_users_dismissed = models.PositiveIntegerField(default=0)

    # Audience Breakdown
    customers_shown = models.PositiveIntegerField(default=0)
    vendors_shown = models.PositiveIntegerField(default=0)
    admins_shown = models.PositiveIntegerField(default=0)

    # Device/Platform Breakdown
    desktop_displays = models.PositiveIntegerField(default=0)
    mobile_displays = models.PositiveIntegerField(default=0)
    tablet_displays = models.PositiveIntegerField(default=0)

    # Engagement Quality
    avg_time_to_action = models.DurationField(null=True, blank=True)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for '{self.message.title}' on {self.date}"

    @property
    def click_through_rate(self):
        """Calculate click-through rate for this day"""
        if self.total_displays == 0:
            return 0
        return (self.total_clicks / self.total_displays) * 100

    @property
    def dismissal_rate(self):
        """Calculate dismissal rate for this day"""
        if self.total_displays == 0:
            return 0
        return (self.total_dismissals / self.total_displays) * 100

    class Meta:
        unique_together = ['message', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['message', '-date']),
            models.Index(fields=['-date']),
        ]
        verbose_name = "Message Analytics"
        verbose_name_plural = "Message Analytics"


class MessageTemplate(models.Model):
    """Reusable message templates for common message types"""

    TEMPLATE_CATEGORY_CHOICES = [
        ('announcement', 'Announcements'),
        ('promotion', 'Promotions'),
        ('maintenance', 'Maintenance'),
        ('welcome', 'Welcome Messages'),
        ('feature', 'Feature Updates'),
        ('policy', 'Policy Updates'),
        ('seasonal', 'Seasonal Messages'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORY_CHOICES)
    description = models.TextField(blank=True)

    # Template Content
    title_template = models.CharField(max_length=200, help_text="Use {{variable}} for dynamic content")
    content_template = models.TextField(help_text="Use {{variable}} for dynamic content")

    # Default Settings
    default_message_type = models.CharField(max_length=20, choices=Message.MESSAGE_TYPE_CHOICES)
    default_target_audience = models.CharField(max_length=20, choices=Message.TARGET_AUDIENCE_CHOICES)
    default_priority = models.IntegerField(choices=Message.PRIORITY_CHOICES, default=2)

    # Styling Defaults
    default_background_color = models.CharField(max_length=7, default='#ffffff')
    default_text_color = models.CharField(max_length=7, default='#000000')
    default_icon_class = models.CharField(max_length=50, blank=True)

    # Template Variables
    available_variables = models.JSONField(default=list, help_text="List of available template variables")

    # Usage Statistics
    usage_count = models.PositiveIntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def render_template(self, context=None):
        """Render template with provided context variables"""
        if context is None:
            context = {}

        title = self.title_template
        content = self.content_template

        # Simple template variable replacement
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            title = title.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))

        return {
            'title': title,
            'content': content
        }

    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-usage_count']),
        ]
        verbose_name = "Message Template"
        verbose_name_plural = "Message Templates"


# ===== GPS TRACKING AND LOCATION MODELS =====

class ImportOrderLocation(models.Model):
    """GPS coordinate tracking for import orders with comprehensive location data"""

    LOCATION_TYPE_CHOICES = [
        ('origin', 'Origin Location'),
        ('auction_house', 'Auction House'),
        ('departure_port', 'Departure Port'),
        ('transit_port', 'Transit Port'),
        ('arrival_port', 'Arrival Port'),
        ('customs_facility', 'Customs Facility'),
        ('registration_office', 'Registration Office'),
        ('dispatch_center', 'Dispatch Center'),
        ('delivery_address', 'Delivery Address'),
        ('current_position', 'Current Position'),
    ]

    ACCURACY_LEVEL_CHOICES = [
        ('high', 'High (GPS)'),
        ('medium', 'Medium (Network)'),
        ('low', 'Low (Estimated)'),
        ('manual', 'Manual Entry'),
    ]

    # Relationships
    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE, related_name='locations')

    # Location Information
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES)
    name = models.CharField(max_length=200, help_text="Human-readable location name")
    description = models.TextField(blank=True, help_text="Additional location details")

    # GPS Coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=7, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=10, decimal_places=7, help_text="Longitude coordinate")
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Altitude in meters")
    accuracy = models.CharField(max_length=10, choices=ACCURACY_LEVEL_CHOICES, default='manual')

    # Address Information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Timing Information
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    actual_arrival_time = models.DateTimeField(null=True, blank=True)
    estimated_departure_time = models.DateTimeField(null=True, blank=True)
    actual_departure_time = models.DateTimeField(null=True, blank=True)

    # Status and Visibility
    is_current_location = models.BooleanField(default=False, help_text="Is this the current location?")
    is_waypoint = models.BooleanField(default=False, help_text="Is this a route waypoint?")
    is_customer_visible = models.BooleanField(default=True, help_text="Show to customer?")

    # Additional Data
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    facility_hours = models.CharField(max_length=200, blank=True)
    special_instructions = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_locations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.import_order.order_number} - {self.get_location_type_display()}: {self.name}"

    @property
    def coordinates_string(self):
        """Return formatted coordinates string"""
        return f"{self.latitude}, {self.longitude}"

    @property
    def google_maps_url(self):
        """Generate Google Maps URL for this location"""
        return f"https://maps.google.com/?q={self.latitude},{self.longitude}"

    def save(self, *args, **kwargs):
        # Ensure only one current location per import order
        if self.is_current_location:
            ImportOrderLocation.objects.filter(
                import_order=self.import_order,
                is_current_location=True
            ).exclude(pk=self.pk).update(is_current_location=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['import_order', 'location_type']),
            models.Index(fields=['import_order', 'is_current_location']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        verbose_name = "Import Order Location"
        verbose_name_plural = "Import Order Locations"


class LocationTrackingHistory(models.Model):
    """Historical tracking data for import order movements"""

    TRACKING_SOURCE_CHOICES = [
        ('gps', 'GPS Device'),
        ('manual', 'Manual Entry'),
        ('api', 'External API'),
        ('estimated', 'Estimated Position'),
        ('vessel_tracking', 'Vessel Tracking'),
        ('customs_update', 'Customs Update'),
    ]

    # Relationships
    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE, related_name='tracking_history')
    location = models.ForeignKey(ImportOrderLocation, on_delete=models.CASCADE, related_name='tracking_entries', null=True, blank=True)

    # Position Data
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Tracking Information
    tracking_source = models.CharField(max_length=20, choices=TRACKING_SOURCE_CHOICES)
    speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Speed in km/h")
    heading = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Direction in degrees")
    accuracy_radius = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Accuracy radius in meters")

    # Status Information
    status_at_time = models.CharField(max_length=30, choices=ImportOrder.STATUS_CHOICES)
    notes = models.TextField(blank=True)

    # Metadata
    recorded_at = models.DateTimeField(help_text="When this position was recorded")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracking_entries', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.import_order.order_number} - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def coordinates_string(self):
        """Return formatted coordinates string"""
        return f"{self.latitude}, {self.longitude}"

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['import_order', '-recorded_at']),
            models.Index(fields=['status_at_time', '-recorded_at']),
            models.Index(fields=['tracking_source', '-recorded_at']),
        ]
        verbose_name = "Location Tracking History"
        verbose_name_plural = "Location Tracking Histories"


class ImportOrderRoute(models.Model):
    """Planned route information for import orders"""

    ROUTE_TYPE_CHOICES = [
        ('sea_freight', 'Sea Freight'),
        ('air_freight', 'Air Freight'),
        ('land_transport', 'Land Transport'),
        ('multimodal', 'Multimodal Transport'),
    ]

    ROUTE_STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
    ]

    # Relationships
    import_order = models.OneToOneField(ImportOrder, on_delete=models.CASCADE, related_name='route')

    # Route Information
    route_name = models.CharField(max_length=200, help_text="Descriptive name for the route")
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPE_CHOICES)
    route_status = models.CharField(max_length=20, choices=ROUTE_STATUS_CHOICES, default='planned')

    # Origin and Destination
    origin_location = models.ForeignKey(ImportOrderLocation, on_delete=models.CASCADE, related_name='routes_as_origin')
    destination_location = models.ForeignKey(ImportOrderLocation, on_delete=models.CASCADE, related_name='routes_as_destination')

    # Route Details
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_duration_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Timing
    planned_start_time = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    planned_end_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)

    # Transport Details
    vessel_name = models.CharField(max_length=200, blank=True)
    vessel_imo = models.CharField(max_length=20, blank=True, help_text="International Maritime Organization number")
    transport_company = models.CharField(max_length=200, blank=True)
    transport_reference = models.CharField(max_length=100, blank=True)

    # Route Configuration
    auto_update_enabled = models.BooleanField(default=True, help_text="Enable automatic position updates")
    tracking_interval_minutes = models.PositiveIntegerField(default=60, help_text="How often to update position")

    # Additional Information
    route_notes = models.TextField(blank=True)
    special_handling_requirements = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_routes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.import_order.order_number} - {self.route_name}"

    @property
    def progress_percentage(self):
        """Calculate route progress based on current location and waypoints"""
        if self.route_status == 'completed':
            return 100
        elif self.route_status in ['planned', 'cancelled']:
            return 0

        # Calculate based on completed waypoints
        total_waypoints = self.waypoints.count()
        if total_waypoints == 0:
            return 0

        completed_waypoints = self.waypoints.filter(is_completed=True).count()
        return int((completed_waypoints / total_waypoints) * 100)

    @property
    def current_waypoint(self):
        """Get the current active waypoint"""
        return self.waypoints.filter(is_current=True).first()

    @property
    def next_waypoint(self):
        """Get the next waypoint in sequence"""
        current = self.current_waypoint
        if current:
            return self.waypoints.filter(sequence_order__gt=current.sequence_order).first()
        return self.waypoints.filter(is_completed=False).first()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['import_order']),
            models.Index(fields=['route_status']),
        ]
        verbose_name = "Import Order Route"
        verbose_name_plural = "Import Order Routes"


class RouteWaypoint(models.Model):
    """Individual waypoints along an import order route"""

    WAYPOINT_TYPE_CHOICES = [
        ('departure', 'Departure Point'),
        ('transit', 'Transit Point'),
        ('checkpoint', 'Checkpoint'),
        ('customs', 'Customs Point'),
        ('arrival', 'Arrival Point'),
        ('delivery', 'Delivery Point'),
    ]

    # Relationships
    route = models.ForeignKey(ImportOrderRoute, on_delete=models.CASCADE, related_name='waypoints')
    location = models.ForeignKey(ImportOrderLocation, on_delete=models.CASCADE, related_name='waypoints')

    # Waypoint Information
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPE_CHOICES)
    sequence_order = models.PositiveIntegerField(help_text="Order in the route sequence")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Status
    is_current = models.BooleanField(default=False, help_text="Is this the current waypoint?")
    is_completed = models.BooleanField(default=False, help_text="Has this waypoint been reached?")
    is_mandatory = models.BooleanField(default=True, help_text="Is this waypoint mandatory?")

    # Timing
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    estimated_departure = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)

    # Distance and Duration
    distance_from_previous_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration_from_previous_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Additional Information
    waypoint_notes = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.route.import_order.order_number} - Waypoint {self.sequence_order}: {self.name}"

    def mark_completed(self, completion_notes=''):
        """Mark this waypoint as completed"""
        self.is_completed = True
        self.is_current = False
        self.actual_arrival = timezone.now()
        self.completed_at = timezone.now()
        self.completion_notes = completion_notes
        self.save()

        # Set next waypoint as current
        next_waypoint = self.route.waypoints.filter(
            sequence_order__gt=self.sequence_order,
            is_completed=False
        ).first()
        if next_waypoint:
            next_waypoint.is_current = True
            next_waypoint.save()

    def save(self, *args, **kwargs):
        # Ensure only one current waypoint per route
        if self.is_current:
            RouteWaypoint.objects.filter(
                route=self.route,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['route', 'sequence_order']
        unique_together = ['route', 'sequence_order']
        indexes = [
            models.Index(fields=['route', 'sequence_order']),
            models.Index(fields=['route', 'is_current']),
            models.Index(fields=['route', 'is_completed']),
        ]
        verbose_name = "Route Waypoint"
        verbose_name_plural = "Route Waypoints"


# Opinion Polling and Review Models

class OpinionPoll(models.Model):
    """Polls associated with opinion posts"""

    POLL_TYPE_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('rating', 'Rating Scale'),
        ('yes_no', 'Yes/No'),
    ]

    opinion_post = models.OneToOneField(BlogPost, on_delete=models.CASCADE, related_name='poll',
                                       limit_choices_to={'content_type': 'opinion'})
    question = models.CharField(max_length=300, help_text="The poll question")
    poll_type = models.CharField(max_length=20, choices=POLL_TYPE_CHOICES, default='single_choice')

    # Poll Settings
    is_active = models.BooleanField(default=True)
    allow_anonymous_voting = models.BooleanField(default=False)
    show_results_before_voting = models.BooleanField(default=False)
    multiple_votes_per_user = models.BooleanField(default=False)

    # Timing
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no end date")

    # Analytics
    total_votes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Poll: {self.question[:50]}..."

    @property
    def is_open(self):
        """Check if poll is currently open for voting"""
        if not self.is_active:
            return False

        now = timezone.now()
        if self.end_date and now > self.end_date:
            return False

        return True

    def get_results(self):
        """Get poll results with percentages"""
        if self.total_votes == 0:
            return []

        results = []
        for option in self.options.all():
            percentage = (option.vote_count / self.total_votes) * 100
            results.append({
                'option': option,
                'percentage': round(percentage, 1),
                'votes': option.vote_count
            })

        return sorted(results, key=lambda x: x['votes'], reverse=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Opinion Poll"
        verbose_name_plural = "Opinion Polls"


class PollOption(models.Model):
    """Options for opinion polls"""

    poll = models.ForeignKey(OpinionPoll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    vote_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.poll.question[:30]}... - {self.text}"

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['poll', 'order']
        verbose_name = "Poll Option"
        verbose_name_plural = "Poll Options"


class PollVote(models.Model):
    """Individual votes on opinion polls"""

    poll = models.ForeignKey(OpinionPoll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='poll_votes')

    # Anonymous voting support
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Metadata
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        voter = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{voter} voted for {self.option.text}"

    class Meta:
        ordering = ['-created_at']
        # Prevent duplicate votes (either by user or session)
        constraints = [
            models.UniqueConstraint(
                fields=['poll', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_poll_vote'
            ),
            models.UniqueConstraint(
                fields=['poll', 'session_key'],
                condition=models.Q(session_key__isnull=False),
                name='unique_session_poll_vote'
            ),
        ]
        verbose_name = "Poll Vote"
        verbose_name_plural = "Poll Votes"


class OpinionReview(models.Model):
    """Reviews and ratings for opinion posts"""

    RATING_CHOICES = [
        (1, '1 - Strongly Disagree'),
        (2, '2 - Disagree'),
        (3, '3 - Neutral'),
        (4, '4 - Agree'),
        (5, '5 - Strongly Agree'),
    ]

    opinion_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='opinion_reviews',
                                    limit_choices_to={'content_type': 'opinion'})
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opinion_reviews')

    # Review Content
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(blank=True, help_text="Optional review text")

    # Moderation
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    # Engagement
    helpful_votes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reviewer.username} - {self.rating}/5 on {self.opinion_post.title[:30]}..."

    @property
    def rating_percentage(self):
        """Convert rating to percentage for display"""
        return (self.rating / 5) * 100

    class Meta:
        ordering = ['-created_at']
        unique_together = ['opinion_post', 'reviewer']
        indexes = [
            models.Index(fields=['opinion_post', 'is_approved']),
            models.Index(fields=['reviewer', '-created_at']),
            models.Index(fields=['rating', 'is_approved']),
        ]
        verbose_name = "Opinion Review"
        verbose_name_plural = "Opinion Reviews"


class ReviewHelpfulVote(models.Model):
    """Track helpful votes on opinion reviews"""

    review = models.ForeignKey(OpinionReview, on_delete=models.CASCADE, related_name='helpful_vote_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_helpful_votes')
    is_helpful = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        vote_type = "helpful" if self.is_helpful else "not helpful"
        return f"{self.user.username} found review {vote_type}"

    class Meta:
        unique_together = ['review', 'user']
        ordering = ['-created_at']
        verbose_name = "Review Helpful Vote"
        verbose_name_plural = "Review Helpful Votes"
