from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import (
    User, Vendor, Car, ImportRequest, Inquiry, VerificationCode,
    SparePart, SparePartCategory, Supplier, PurchaseOrder, PurchaseOrderItem,
    CarBrand, CarModel, VehicleCondition
)
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
            from urllib.parse import urlparse
            site_url = getattr(settings, 'SITE_URL', 'https://gurumishamotors.com')
            parsed_url = urlparse(site_url)

            context = {
                'user': user,
                'token': token,
                'domain': parsed_url.netloc,
                'protocol': parsed_url.scheme,
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
            except User.MultipleObjectsReturned:
                raise ValidationError(
                    "Multiple accounts found with this email address. Please contact support for assistance."
                )
        return username


class SellCarForm(forms.ModelForm):
    """Enhanced form for selling a car with improved styling and validation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create independent hardcoded choice fields
        # Brand selector (independent)
        self.fields['brand'] = forms.ChoiceField(
            choices=[
                ('', 'Select a brand'),
                ('toyota', 'Toyota'),
                ('honda', 'Honda'),
                ('nissan', 'Nissan'),
                ('mazda', 'Mazda'),
                ('subaru', 'Subaru'),
                ('mitsubishi', 'Mitsubishi'),
                ('bmw', 'BMW'),
                ('mercedes', 'Mercedes-Benz'),
                ('audi', 'Audi'),
                ('volkswagen', 'Volkswagen'),
                ('hyundai', 'Hyundai'),
                ('kia', 'KIA'),
                ('ford', 'Ford'),
                ('chevrolet', 'Chevrolet'),
                ('peugeot', 'Peugeot'),
                ('renault', 'Renault'),
                ('land_rover', 'Land Rover'),
                ('jeep', 'Jeep'),
                ('volvo', 'Volvo'),
                ('lexus', 'Lexus'),
                ('infiniti', 'Infiniti'),
                ('acura', 'Acura'),
                ('other', 'Other'),
            ],
            required=True,
            widget=forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            })
        )

        # Model selector (independent)
        self.fields['model'] = forms.ChoiceField(
            choices=[
                ('', 'Select a model'),
                # Popular models across all brands (alphabetical)
                ('3_series', '3 Series'),
                ('5_series', '5 Series'),
                ('7_series', '7 Series'),
                ('accord', 'Accord'),
                ('altima', 'Altima'),
                ('camry', 'Camry'),
                ('civic', 'Civic'),
                ('corolla', 'Corolla'),
                ('cr_v', 'CR-V'),
                ('crown', 'Crown'),
                ('e_class', 'E-Class'),
                ('fit', 'Fit'),
                ('forester', 'Forester'),
                ('gla', 'GLA'),
                ('glc', 'GLC'),
                ('gle', 'GLE'),
                ('harrier', 'Harrier'),
                ('highlander', 'Highlander'),
                ('hilux', 'Hilux'),
                ('impreza', 'Impreza'),
                ('land_cruiser', 'Land Cruiser'),
                ('mark_x', 'Mark X'),
                ('navara', 'Navara'),
                ('noah', 'Noah'),
                ('note', 'Note'),
                ('outback', 'Outback'),
                ('pathfinder', 'Pathfinder'),
                ('pilot', 'Pilot'),
                ('prius', 'Prius'),
                ('rav4', 'RAV4'),
                ('rogue', 'Rogue'),
                ('s_class', 'S-Class'),
                ('sentra', 'Sentra'),
                ('stepwgn', 'StepWGN'),
                ('stream', 'Stream'),
                ('tiida', 'Tiida'),
                ('vezel', 'Vezel'),
                ('vitz', 'Vitz'),
                ('voxy', 'Voxy'),
                ('x1', 'X1'),
                ('x3', 'X3'),
                ('x5', 'X5'),
                ('x6', 'X6'),
                ('x_trail', 'X-Trail'),
                ('other', 'Other (specify in description)'),
            ],
            required=True,
            widget=forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            })
        )

        # Condition selector (independent)
        self.fields['condition'] = forms.ChoiceField(
            choices=[
                ('', 'Select condition'),
                ('new', 'New'),
                ('used', 'Used'),
                ('certified', 'Certified Pre-Owned'),
                ('excellent', 'Excellent'),
                ('good', 'Good'),
                ('fair', 'Fair'),
                ('needs_work', 'Needs Work'),
            ],
            required=True,
            widget=forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            })
        )

        # Remove HTMX attributes since we're using independent selectors
        # No dynamic loading needed for independent brand/model selection

        # Add country choices with Kenya at top and East African countries prominently featured
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
            # Other African Countries (Alphabetical)
            ('Angola', 'Angola'),
            ('Benin', 'Benin'),
            ('Botswana', 'Botswana'),
            ('Burkina Faso', 'Burkina Faso'),
            ('Cameroon', 'Cameroon'),
            ('Cape Verde', 'Cape Verde'),
            ('Central African Republic', 'Central African Republic'),
            ('Chad', 'Chad'),
            ('Comoros', 'Comoros'),
            ('Democratic Republic of Congo', 'Democratic Republic of Congo'),
            ('Equatorial Guinea', 'Equatorial Guinea'),
            ('Gabon', 'Gabon'),
            ('Gambia', 'Gambia'),
            ('Guinea', 'Guinea'),
            ('Guinea-Bissau', 'Guinea-Bissau'),
            ('Ivory Coast', 'Ivory Coast'),
            ('Lesotho', 'Lesotho'),
            ('Liberia', 'Liberia'),
            ('Madagascar', 'Madagascar'),
            ('Malawi', 'Malawi'),
            ('Mali', 'Mali'),
            ('Mauritius', 'Mauritius'),
            ('Mozambique', 'Mozambique'),
            ('Namibia', 'Namibia'),
            ('Niger', 'Niger'),
            ('Republic of Congo', 'Republic of Congo'),
            ('Sao Tome and Principe', 'Sao Tome and Principe'),
            ('Senegal', 'Senegal'),
            ('Seychelles', 'Seychelles'),
            ('Sierra Leone', 'Sierra Leone'),
            ('Sudan', 'Sudan'),
            ('Swaziland', 'Swaziland'),
            ('Togo', 'Togo'),
            ('Zambia', 'Zambia'),
            ('Zimbabwe', 'Zimbabwe'),
            # Major Global Markets
            ('United States', 'United States'),
            ('United Kingdom', 'United Kingdom'),
            ('Germany', 'Germany'),
            ('Japan', 'Japan'),
            ('China', 'China'),
            ('India', 'India'),
            ('Canada', 'Canada'),
            ('Australia', 'Australia'),
            ('France', 'France'),
            ('Italy', 'Italy'),
            ('Spain', 'Spain'),
            ('Brazil', 'Brazil'),
            ('Mexico', 'Mexico'),
            ('South Korea', 'South Korea'),
            ('Netherlands', 'Netherlands'),
            ('Belgium', 'Belgium'),
            ('Switzerland', 'Switzerland'),
            ('Austria', 'Austria'),
            ('Sweden', 'Sweden'),
            ('Norway', 'Norway'),
            ('Denmark', 'Denmark'),
            ('Finland', 'Finland'),
            # Other Countries (Alphabetical)
            ('Afghanistan', 'Afghanistan'),
            ('Albania', 'Albania'),
            ('Argentina', 'Argentina'),
            ('Armenia', 'Armenia'),
            ('Azerbaijan', 'Azerbaijan'),
            ('Bahamas', 'Bahamas'),
            ('Bahrain', 'Bahrain'),
            ('Bangladesh', 'Bangladesh'),
            ('Barbados', 'Barbados'),
            ('Belarus', 'Belarus'),
            ('Belize', 'Belize'),
            ('Bhutan', 'Bhutan'),
            ('Bolivia', 'Bolivia'),
            ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),
            ('Brunei', 'Brunei'),
            ('Bulgaria', 'Bulgaria'),
            ('Cambodia', 'Cambodia'),
            ('Chile', 'Chile'),
            ('Colombia', 'Colombia'),
            ('Costa Rica', 'Costa Rica'),
            ('Croatia', 'Croatia'),
            ('Cuba', 'Cuba'),
            ('Cyprus', 'Cyprus'),
            ('Czech Republic', 'Czech Republic'),
            ('Dominica', 'Dominica'),
            ('Dominican Republic', 'Dominican Republic'),
            ('Ecuador', 'Ecuador'),
            ('El Salvador', 'El Salvador'),
            ('Estonia', 'Estonia'),
            ('Fiji', 'Fiji'),
            ('Georgia', 'Georgia'),
            ('Greece', 'Greece'),
            ('Grenada', 'Grenada'),
            ('Guatemala', 'Guatemala'),
            ('Guyana', 'Guyana'),
            ('Haiti', 'Haiti'),
            ('Honduras', 'Honduras'),
            ('Hungary', 'Hungary'),
            ('Iceland', 'Iceland'),
            ('Indonesia', 'Indonesia'),
            ('Iran', 'Iran'),
            ('Iraq', 'Iraq'),
            ('Ireland', 'Ireland'),
            ('Israel', 'Israel'),
            ('Jamaica', 'Jamaica'),
            ('Jordan', 'Jordan'),
            ('Kazakhstan', 'Kazakhstan'),
            ('Kuwait', 'Kuwait'),
            ('Kyrgyzstan', 'Kyrgyzstan'),
            ('Laos', 'Laos'),
            ('Latvia', 'Latvia'),
            ('Lebanon', 'Lebanon'),
            ('Lithuania', 'Lithuania'),
            ('Luxembourg', 'Luxembourg'),
            ('Malaysia', 'Malaysia'),
            ('Maldives', 'Maldives'),
            ('Malta', 'Malta'),
            ('Moldova', 'Moldova'),
            ('Mongolia', 'Mongolia'),
            ('Montenegro', 'Montenegro'),
            ('Myanmar', 'Myanmar'),
            ('Nepal', 'Nepal'),
            ('New Zealand', 'New Zealand'),
            ('Nicaragua', 'Nicaragua'),
            ('North Macedonia', 'North Macedonia'),
            ('Oman', 'Oman'),
            ('Pakistan', 'Pakistan'),
            ('Panama', 'Panama'),
            ('Paraguay', 'Paraguay'),
            ('Peru', 'Peru'),
            ('Philippines', 'Philippines'),
            ('Poland', 'Poland'),
            ('Portugal', 'Portugal'),
            ('Qatar', 'Qatar'),
            ('Romania', 'Romania'),
            ('Russia', 'Russia'),
            ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
            ('Saint Lucia', 'Saint Lucia'),
            ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
            ('Saudi Arabia', 'Saudi Arabia'),
            ('Serbia', 'Serbia'),
            ('Singapore', 'Singapore'),
            ('Slovakia', 'Slovakia'),
            ('Slovenia', 'Slovenia'),
            ('Sri Lanka', 'Sri Lanka'),
            ('Suriname', 'Suriname'),
            ('Syria', 'Syria'),
            ('Tajikistan', 'Tajikistan'),
            ('Thailand', 'Thailand'),
            ('Trinidad and Tobago', 'Trinidad and Tobago'),
            ('Turkey', 'Turkey'),
            ('Turkmenistan', 'Turkmenistan'),
            ('Ukraine', 'Ukraine'),
            ('United Arab Emirates', 'United Arab Emirates'),
            ('Uruguay', 'Uruguay'),
            ('Uzbekistan', 'Uzbekistan'),
            ('Venezuela', 'Venezuela'),
            ('Vietnam', 'Vietnam'),
            ('Yemen', 'Yemen'),
        ]

    class Meta:
        model = Car
        fields = [
            'year', 'engine_size', 'fuel_type', 'transmission', 'mileage',
            'color', 'price', 'title', 'description', 'features',
            'listing_type', 'negotiable', 'area', 'city', 'country'
        ]
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'min': '1990',
                'max': '2025',
                'placeholder': 'e.g., 2020'
            }),
            'engine_size': forms.TextInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'e.g., 2.0L, 1800cc, 2500cc'
            }),
            'fuel_type': forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            }),
            'transmission': forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'Mileage in kilometers (e.g., 50000)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'e.g., Pearl White, Metallic Black, Silver'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'Price in KES (e.g., 2500000)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'e.g., 2020 Toyota Camry - Excellent Condition'
            }),
            'description': forms.Textarea(attrs={
                'class': 'enhanced-textarea w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base resize-none',
                'rows': 6,
                'placeholder': 'Describe your car in detail... Include any unique features, maintenance history, or special characteristics that make your vehicle stand out.'
            }),
            'features': forms.Textarea(attrs={
                'class': 'enhanced-textarea w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base resize-none',
                'rows': 4,
                'placeholder': 'List key features separated by commas (e.g., Air Conditioning, Power Steering, ABS, Leather Seats, Sunroof, Navigation System)'
            }),

            'listing_type': forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            }),
            'negotiable': forms.CheckboxInput(attrs={
                'class': 'enhanced-checkbox w-5 h-5 text-harrier-red bg-white/80 border-2 border-gray-200 rounded-lg focus:ring-harrier-red focus:ring-2 transition-all duration-300'
            }),
            'area': forms.TextInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'e.g., Westlands, Karen, Kilimani'
            }),
            'city': forms.TextInput(attrs={
                'class': 'enhanced-input w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base',
                'placeholder': 'e.g., Nairobi, Mombasa, Kisumu'
            }),
            'country': forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            })
        }

    def clean_year(self):
        """Validate year field"""
        year = self.cleaned_data.get('year')
        from datetime import datetime
        current_year = datetime.now().year

        if year and (year < 1990 or year > current_year + 1):
            raise forms.ValidationError(f'Year must be between 1990 and {current_year + 1}')
        return year

    def clean_price(self):
        """Validate price field"""
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Price cannot be negative')
        if price and price > 100000000:  # 100 million KES
            raise forms.ValidationError('Price seems too high. Please check your input.')
        return price

    def clean_mileage(self):
        """Validate mileage field"""
        mileage = self.cleaned_data.get('mileage')
        if mileage and mileage < 0:
            raise forms.ValidationError('Mileage cannot be negative')
        if mileage and mileage > 1000000:  # 1 million km
            raise forms.ValidationError('Mileage seems too high. Please check your input.')
        return mileage

    def save_images(self, car, image_files, captions=None, is_primary_list=None):
        """
        Save multiple images for the car

        Args:
            car: Car instance
            image_files: List of uploaded image files
            captions: List of captions for images
            is_primary_list: List of boolean values indicating primary images
        """
        from .models import CarImage
        try:
            from .utils.image_optimization import validate_car_image
        except ImportError:
            # Fallback validation function if utils not available
            def validate_car_image(image_file):
                return True, None

        if not image_files:
            return []

        created_images = []
        captions = captions or []
        is_primary_list = is_primary_list or []

        # Ensure only one primary image
        primary_count = sum(1 for is_primary in is_primary_list if is_primary)
        if primary_count != 1:
            # Set first image as primary if no primary or multiple primaries
            is_primary_list = [i == 0 for i in range(len(image_files))]

        for i, image_file in enumerate(image_files):
            try:
                # Validate image
                is_valid, error_msg = validate_car_image(image_file)
                if not is_valid:
                    continue  # Skip invalid images

                # Create CarImage instance
                car_image = CarImage.objects.create(
                    car=car,
                    image=image_file,
                    caption=captions[i] if i < len(captions) else '',
                    order=i + 1,
                    is_primary=is_primary_list[i] if i < len(is_primary_list) else False
                )

                created_images.append(car_image)

            except Exception as e:
                # Log error but continue with other images
                print(f"Error saving image {i}: {str(e)}")
                continue

        return created_images

    def save(self, commit=True):
        """Custom save method to handle independent hardcoded choices"""
        instance = super().save(commit=False)

        # Since we're using independent hardcoded choices, always save as strings
        brand_value = self.cleaned_data.get('brand')
        if brand_value:
            instance.brand_name = brand_value
            instance.brand = None

        model_value = self.cleaned_data.get('model')
        if model_value:
            instance.model_name = model_value
            instance.model = None

        condition_value = self.cleaned_data.get('condition')
        if condition_value:
            instance.condition_name = condition_value
            instance.condition = None

        if commit:
            instance.save()
        return instance


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
            except User.MultipleObjectsReturned:
                # Handle case where multiple users have the same email (should not happen after migration)
                raise ValidationError(
                    "Multiple accounts found with this email address. Please contact support for assistance."
                )

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
            except User.MultipleObjectsReturned:
                raise ValidationError(
                    "Multiple accounts found with this email address. Please contact support for assistance."
                )
        return email

    def send_verification_email(self):
        """Send verification email to the user"""
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.MultipleObjectsReturned:
            # If multiple users exist, we can't proceed safely
            raise ValidationError(
                "Multiple accounts found with this email address. Please contact support for assistance."
            )

        try:
            # Generate new verification token
            token = user.generate_email_verification_token()

            # Prepare email context
            from urllib.parse import urlparse
            site_url = getattr(settings, 'SITE_URL', 'https://gurumishamotors.com')
            parsed_url = urlparse(site_url)

            context = {
                'user': user,
                'token': token,
                'domain': parsed_url.netloc,
                'protocol': parsed_url.scheme,
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
        except User.MultipleObjectsReturned:
            # If multiple users exist, we can't proceed safely
            raise ValidationError(
                "Multiple accounts found with this email address. Please contact support for assistance."
            )

        try:
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


# ============================================================================
# SPARE PARTS MANAGEMENT FORMS
# ============================================================================

class SparePartForm(forms.ModelForm):
    """Enhanced form for creating and editing spare parts with two-tier category support"""

    # Add sub-category field for two-tier hierarchy (hardcoded options)
    sub_category = forms.ModelChoiceField(
        queryset=SparePartCategory.objects.filter(parent__isnull=False, is_active=True).order_by('parent__name', 'name'),
        required=False,
        empty_label="Select Sub-Category (Optional)",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
            'id': 'id_sub_category'
        })
    )

    class Meta:
        model = SparePart
        fields = [
            'name', 'part_number', 'sku', 'barcode', 'category_new', 'supplier',
            'description', 'specifications', 'condition', 'unit', 'price', 'cost_price',
            'discount_price', 'stock_quantity', 'minimum_stock', 'maximum_stock',
            'reorder_point', 'reorder_quantity', 'warehouse_location', 'storage_conditions',
            'weight', 'dimensions', 'year_from', 'year_to', 'compatible_brands',
            'compatible_models', 'main_image', 'is_available', 'is_featured'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Enter spare part name'
            }),
            'part_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Manufacturer part number'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Stock Keeping Unit'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Barcode (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 4,
                'placeholder': 'Detailed description of the spare part'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 3,
                'placeholder': 'Technical specifications'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Selling price in KSh',
                'step': '0.01'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Cost price in KSh',
                'step': '0.01'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Discounted price (optional)',
                'step': '0.01'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Current stock quantity'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Minimum stock level'
            }),
            'maximum_stock': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Maximum stock level'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Reorder trigger point'
            }),
            'reorder_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Quantity to reorder'
            }),
            'warehouse_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Warehouse/shelf location'
            }),
            'storage_conditions': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Special storage requirements'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Weight in kg',
                'step': '0.01'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Dimensions (L x W x H in cm)'
            }),
            'year_from': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Compatible from year'
            }),
            'year_to': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Compatible to year'
            }),
            'compatible_brands': forms.CheckboxSelectMultiple(attrs={
                'class': 'grid grid-cols-2 gap-2'
            }),
            'compatible_models': forms.CheckboxSelectMultiple(attrs={
                'class': 'grid grid-cols-2 gap-2'
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        # Set vendor if provided
        if self.vendor:
            self.instance.vendor = self.vendor

        # Customize category choices - only show parent categories (no parent)
        self.fields['category_new'].queryset = SparePartCategory.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('name')
        self.fields['category_new'].empty_label = "Select Primary Category"

        # Set widget class for category field
        self.fields['category_new'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent'
        })

        # Customize supplier choices
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['supplier'].empty_label = "Select Supplier (Optional)"

        # Handle existing spare part with category (simplified for hardcoded sub-categories)
        if self.instance.pk and self.instance.category_new:
            if self.instance.category_new.parent:
                # This is a sub-category, set the parent as main category and this as sub-category
                self.fields['category_new'].initial = self.instance.category_new.parent
                self.fields['sub_category'].initial = self.instance.category_new

    def clean_sku(self):
        """Ensure SKU is unique"""
        sku = self.cleaned_data.get('sku')
        if sku:
            existing = SparePart.objects.filter(sku=sku)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A spare part with this SKU already exists.")
        return sku

    def clean_barcode(self):
        """Ensure barcode is unique if provided"""
        barcode = self.cleaned_data.get('barcode')
        if barcode:
            existing = SparePart.objects.filter(barcode=barcode)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A spare part with this barcode already exists.")
        return barcode

    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()

        # Validate price relationships
        price = cleaned_data.get('price')
        cost_price = cleaned_data.get('cost_price')
        discount_price = cleaned_data.get('discount_price')

        if cost_price and price and cost_price > price:
            raise ValidationError("Cost price cannot be higher than selling price.")

        if discount_price and price and discount_price >= price:
            raise ValidationError("Discount price must be lower than regular price.")

        # Validate stock levels
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        reorder_point = cleaned_data.get('reorder_point')

        if minimum_stock and maximum_stock and minimum_stock >= maximum_stock:
            raise ValidationError("Minimum stock must be less than maximum stock.")

        if reorder_point and minimum_stock and reorder_point < minimum_stock:
            raise ValidationError("Reorder point should be at or above minimum stock level.")

        # Validate year range
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')

        if year_from and year_to and year_from > year_to:
            raise ValidationError("'From year' cannot be later than 'To year'.")

        return cleaned_data

    def clean_main_image(self):
        """Validate image upload"""
        image = self.cleaned_data.get('main_image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file size cannot exceed 5MB.")

            # Check file type
            if not image.content_type.startswith('image/'):
                raise ValidationError("Please upload a valid image file.")

            # Check image dimensions (optional)
            try:
                from PIL import Image
                img = Image.open(image)
                if img.width < 200 or img.height < 200:
                    raise ValidationError("Image must be at least 200x200 pixels.")
            except ImportError:
                # PIL not available, skip dimension check
                pass
            except Exception:
                raise ValidationError("Invalid image file.")

        return image

    def save_images(self, car, image_files, captions=None, is_primary_list=None):
        """
        Save multiple images for the car

        Args:
            car: Car instance
            image_files: List of uploaded image files
            captions: List of captions for images
            is_primary_list: List of boolean values indicating primary images
        """
        from .models import CarImage
        from .utils.image_optimization import validate_car_image

        if not image_files:
            return []

        created_images = []
        captions = captions or []
        is_primary_list = is_primary_list or []

        # Ensure only one primary image
        primary_count = sum(1 for is_primary in is_primary_list if is_primary)
        if primary_count != 1:
            # Set first image as primary if no primary or multiple primaries
            is_primary_list = [i == 0 for i in range(len(image_files))]

        for i, image_file in enumerate(image_files):
            try:
                # Validate image
                is_valid, error_msg = validate_car_image(image_file)
                if not is_valid:
                    continue  # Skip invalid images

                # Create CarImage instance
                car_image = CarImage.objects.create(
                    car=car,
                    image=image_file,
                    caption=captions[i] if i < len(captions) else '',
                    order=i + 1,
                    is_primary=is_primary_list[i] if i < len(is_primary_list) else False
                )

                created_images.append(car_image)

            except Exception as e:
                # Log error but continue with other images
                print(f"Error saving image {i}: {str(e)}")
                continue

        return created_images

    def save(self, commit=True):
        """Override save to ensure vendor is set and handle two-tier category system"""
        instance = super().save(commit=False)

        # Ensure vendor is set
        if self.vendor and not instance.vendor:
            instance.vendor = self.vendor

        # Handle two-tier category system
        sub_category = self.cleaned_data.get('sub_category')
        if sub_category:
            # If sub-category is selected, use it as the main category
            instance.category_new = sub_category
            instance.category = sub_category.name
        elif instance.category_new:
            # If only primary category is selected, use it
            instance.category = instance.category_new.name
        elif not instance.category:
            # Set a default category if none provided
            instance.category = 'General'

        # Set default values for vendor parts
        if not instance.is_available:
            instance.is_available = True

        if commit:
            instance.save()
            # Save many-to-many fields
            self.save_m2m()

        return instance


class VendorSparePartForm(SparePartForm):
    """Specialized form for vendor spare parts management"""

    class Meta(SparePartForm.Meta):
        # Exclude admin-only fields for vendors
        fields = [
            'name', 'part_number', 'sku', 'barcode', 'category_new', 'supplier',
            'description', 'specifications', 'condition', 'unit', 'price', 'cost_price',
            'discount_price', 'stock_quantity', 'minimum_stock', 'maximum_stock',
            'reorder_point', 'warehouse_location', 'weight', 'dimensions',
            'year_from', 'year_to', 'main_image', 'is_available'
        ]

    def __init__(self, *args, **kwargs):
        # Extract vendor before calling super().__init__
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        # Make certain fields required for vendors
        self.fields['name'].required = True
        self.fields['sku'].required = True
        self.fields['category_new'].required = True
        self.fields['condition'].required = True
        self.fields['price'].required = True
        self.fields['stock_quantity'].required = True

        # Add helpful text for vendors
        self.fields['sku'].help_text = "Unique identifier for this part in your inventory"
        self.fields['minimum_stock'].help_text = "You'll be notified when stock falls below this level"
        self.fields['cost_price'].help_text = "Your purchase cost (used for profit calculations)"

        # Limit supplier choices to active suppliers only
        if self.vendor:
            # Vendors can only select from suppliers they have relationships with
            # or create new supplier relationships through admin
            self.fields['supplier'].queryset = Supplier.objects.filter(
                is_active=True
            ).order_by('name')

    def clean_sku(self):
        """Ensure SKU is unique within vendor's parts"""
        sku = self.cleaned_data.get('sku')
        if sku and self.vendor:
            existing = SparePart.objects.filter(
                sku=sku,
                vendor=self.vendor
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("You already have a spare part with this SKU.")
        elif sku:
            # Fallback to global uniqueness if no vendor
            existing = SparePart.objects.filter(sku=sku)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A spare part with this SKU already exists.")
        return sku

    def clean_price(self):
        """Validate price is reasonable"""
        price = self.cleaned_data.get('price')
        if price:
            if price <= 0:
                raise ValidationError("Price must be greater than zero.")
            if price > 10000000:  # 10 million KSh
                raise ValidationError("Price seems unreasonably high. Please verify.")
        return price

    def clean_stock_quantity(self):
        """Validate stock quantity"""
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is not None:
            if stock_quantity < 0:
                raise ValidationError("Stock quantity cannot be negative.")
            if stock_quantity > 1000000:  # 1 million units
                raise ValidationError("Stock quantity seems unreasonably high. Please verify.")
        return stock_quantity


class SupplierForm(forms.ModelForm):
    """Form for creating and editing suppliers"""

    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address', 'website',
            'tax_number', 'payment_terms', 'rating', 'is_active'
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Supplier company name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Primary contact person'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'supplier@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': '+254700000000'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 3,
                'placeholder': 'Physical address'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'https://supplier-website.com'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Tax/VAT number'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'e.g., Net 30 days'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Rating out of 5',
                'min': '1',
                'max': '5',
                'step': '0.1'
            }),
        }

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            existing = Supplier.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A supplier with this email already exists.")
        return email

    def clean_rating(self):
        """Validate rating range"""
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError("Rating must be between 1 and 5.")
        return rating


class PurchaseOrderForm(forms.ModelForm):
    """Form for creating purchase orders"""

    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'expected_delivery', 'shipping_cost', 'tax_amount',
            'notes', 'terms_conditions'
        ]

        widgets = {
            'expected_delivery': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'type': 'date'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Shipping cost in KSh',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Tax amount in KSh',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 3,
                'placeholder': 'Additional notes for this purchase order'
            }),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 4,
                'placeholder': 'Terms and conditions for this purchase order'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        # Set vendor if provided
        if self.vendor:
            self.instance.vendor = self.vendor

        # Filter suppliers to active ones
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['supplier'].empty_label = "Select Supplier"


class PurchaseOrderItemForm(forms.ModelForm):
    """Form for adding items to purchase orders"""

    class Meta:
        model = PurchaseOrderItem
        fields = ['spare_part', 'quantity_ordered', 'unit_cost', 'notes']

        widgets = {
            'quantity_ordered': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Quantity to order'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Cost per unit in KSh',
                'step': '0.01'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Additional notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

        # Filter spare parts to vendor's parts if vendor is provided
        if self.vendor:
            self.fields['spare_part'].queryset = SparePart.objects.filter(vendor=self.vendor)
        else:
            self.fields['spare_part'].queryset = SparePart.objects.all()

        self.fields['spare_part'].empty_label = "Select Spare Part"

    def clean_quantity_ordered(self):
        """Validate quantity"""
        quantity = self.cleaned_data.get('quantity_ordered')
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean_unit_cost(self):
        """Validate unit cost"""
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost and unit_cost <= 0:
            raise ValidationError("Unit cost must be greater than zero.")
        return unit_cost


class SparePartCategoryForm(forms.ModelForm):
    """Form for creating and editing spare part categories"""

    class Meta:
        model = SparePartCategory
        fields = ['name', 'description', 'parent', 'is_active']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-harrier-red focus:border-transparent',
                'rows': 3,
                'placeholder': 'Category description'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Exclude self from parent choices to prevent circular references
        if self.instance.pk:
            self.fields['parent'].queryset = SparePartCategory.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent'].queryset = SparePartCategory.objects.filter(is_active=True)

        self.fields['parent'].empty_label = "No Parent (Top Level Category)"

    def clean_name(self):
        """Validate category name uniqueness"""
        name = self.cleaned_data.get('name')
        if name:
            existing = SparePartCategory.objects.filter(name=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A category with this name already exists.")
        return name
