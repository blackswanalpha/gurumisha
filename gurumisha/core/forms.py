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
        # Remove any validators from the username field
        self.fields['username'].validators = []
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

    def clean_username(self):
        """Custom username validation - allow any characters"""
        username = self.cleaned_data.get('username')
        if username:
            # Check for minimum and maximum length
            if len(username) < 3:
                raise ValidationError("Username must be at least 3 characters long.")
            if len(username) > 30:
                raise ValidationError("Username must be less than 30 characters.")

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise ValidationError("A user with that username already exists.")

        return username

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
        # Brand selector with comprehensive brand list (72 brands)
        self.fields['brand'] = forms.ChoiceField(
            choices=[
                ('', 'Select a brand'),
                ('acura', 'Acura'),
                ('alfa_romeo', 'Alfa Romeo'),
                ('aston_martin', 'Aston Martin'),
                ('audi', 'Audi'),
                ('bentley', 'Bentley'),
                ('bmw', 'BMW'),
                ('buick', 'Buick'),
                ('byd', 'BYD'),
                ('cadillac', 'Cadillac'),
                ('chery', 'Chery'),
                ('chevrolet', 'Chevrolet'),
                ('chrysler', 'Chrysler'),
                ('citroen', 'Citroen'),
                ('dacia', 'Dacia'),
                ('daewoo', 'Daewoo'),
                ('daihatsu', 'Daihatsu'),
                ('dodge', 'Dodge'),
                ('dongfeng', 'Dongfeng'),
                ('faw', 'FAW'),
                ('ferrari', 'Ferrari'),
                ('fiat', 'Fiat'),
                ('ford', 'Ford'),
                ('foton', 'Foton'),
                ('geely', 'Geely'),
                ('genesis', 'Genesis'),
                ('gmc', 'GMC'),
                ('great_wall', 'Great Wall'),
                ('haval', 'Haval'),
                ('honda', 'Honda'),
                ('hummer', 'Hummer'),
                ('hyundai', 'Hyundai'),
                ('infiniti', 'Infiniti'),
                ('isuzu', 'Isuzu'),
                ('iveco', 'Iveco'),
                ('jac', 'JAC'),
                ('jaguar', 'Jaguar'),
                ('jeep', 'Jeep'),
                ('kia', 'Kia'),
                ('lamborghini', 'Lamborghini'),
                ('lancia', 'Lancia'),
                ('land_rover', 'Land Rover'),
                ('lexus', 'Lexus'),
                ('lincoln', 'Lincoln'),
                ('mahindra', 'Mahindra'),
                ('maserati', 'Maserati'),
                ('mazda', 'Mazda'),
                ('mclaren', 'McLaren'),
                ('mercedes', 'Mercedes-Benz'),
                ('mini', 'Mini'),
                ('mitsubishi', 'Mitsubishi'),
                ('nissan', 'Nissan'),
                ('opel', 'Opel'),
                ('peugeot', 'Peugeot'),
                ('porsche', 'Porsche'),
                ('proton', 'Proton'),
                ('ram', 'Ram'),
                ('renault', 'Renault'),
                ('rolls_royce', 'Rolls Royce'),
                ('saab', 'Saab'),
                ('seat', 'Seat'),
                ('skoda', 'Skoda'),
                ('smart', 'Smart'),
                ('ssangyong', 'SsangYong'),
                ('subaru', 'Subaru'),
                ('suzuki', 'Suzuki'),
                ('tata', 'Tata'),
                ('tesla', 'Tesla'),
                ('toyota', 'Toyota'),
                ('volkswagen', 'Volkswagen'),
                ('volvo', 'Volvo'),
                ('other', 'Other'),
            ],
            required=True,
            widget=forms.Select(attrs={
                'class': 'enhanced-select w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-harrier-red focus:border-harrier-red transition-all duration-300 bg-white/80 backdrop-blur-sm font-raleway text-base'
            })
        )

        # Model selector with 200+ comprehensive car models
        self.fields['model'] = forms.ChoiceField(
            choices=[
                ('', 'Select a model'),
                # Toyota Models
                ('4runner', 'Toyota 4Runner'),
                ('avalon', 'Toyota Avalon'),
                ('camry', 'Toyota Camry'),
                ('c_hr', 'Toyota C-HR'),
                ('celica', 'Toyota Celica'),
                ('corolla', 'Toyota Corolla'),
                ('crown', 'Toyota Crown'),
                ('harrier', 'Toyota Harrier'),
                ('highlander', 'Toyota Highlander'),
                ('hilux', 'Toyota Hilux'),
                ('land_cruiser', 'Toyota Land Cruiser'),
                ('mark_x', 'Toyota Mark X'),
                ('matrix', 'Toyota Matrix'),
                ('noah', 'Toyota Noah'),
                ('prius', 'Toyota Prius'),
                ('rav4', 'Toyota RAV4'),
                ('sequoia', 'Toyota Sequoia'),
                ('sienna', 'Toyota Sienna'),
                ('supra', 'Toyota Supra'),
                ('tacoma', 'Toyota Tacoma'),
                ('tundra', 'Toyota Tundra'),
                ('venza', 'Toyota Venza'),
                ('vitz', 'Toyota Vitz'),
                ('voxy', 'Toyota Voxy'),
                ('yaris', 'Toyota Yaris'),
                # Honda Models
                ('accord', 'Honda Accord'),
                ('civic', 'Honda Civic'),
                ('cr_v', 'Honda CR-V'),
                ('del_sol', 'Honda Del Sol'),
                ('element', 'Honda Element'),
                ('fit', 'Honda Fit'),
                ('hr_v', 'Honda HR-V'),
                ('insight', 'Honda Insight'),
                ('odyssey', 'Honda Odyssey'),
                ('passport', 'Honda Passport'),
                ('pilot', 'Honda Pilot'),
                ('prelude', 'Honda Prelude'),
                ('ridgeline', 'Honda Ridgeline'),
                ('s2000', 'Honda S2000'),
                ('stepwgn', 'Honda StepWGN'),
                ('stream', 'Honda Stream'),
                ('vezel', 'Honda Vezel'),
                # BMW Models
                ('1_series', 'BMW 1 Series'),
                ('2_series', 'BMW 2 Series'),
                ('3_series', 'BMW 3 Series'),
                ('4_series', 'BMW 4 Series'),
                ('5_series', 'BMW 5 Series'),
                ('7_series', 'BMW 7 Series'),
                ('8_series', 'BMW 8 Series'),
                ('i3', 'BMW i3'),
                ('i8', 'BMW i8'),
                ('x1', 'BMW X1'),
                ('x2', 'BMW X2'),
                ('x3', 'BMW X3'),
                ('x4', 'BMW X4'),
                ('x5', 'BMW X5'),
                ('x6', 'BMW X6'),
                ('x7', 'BMW X7'),
                ('z4', 'BMW Z4'),
                # Mercedes-Benz Models
                ('a_class', 'Mercedes-Benz A-Class'),
                ('amg_gt', 'Mercedes-Benz AMG GT'),
                ('c_class', 'Mercedes-Benz C-Class'),
                ('cla', 'Mercedes-Benz CLA'),
                ('cls', 'Mercedes-Benz CLS'),
                ('e_class', 'Mercedes-Benz E-Class'),
                ('g_class', 'Mercedes-Benz G-Class'),
                ('gla', 'Mercedes-Benz GLA'),
                ('glb', 'Mercedes-Benz GLB'),
                ('glc', 'Mercedes-Benz GLC'),
                ('gle', 'Mercedes-Benz GLE'),
                ('gle_coupe', 'Mercedes-Benz GLE Coupe'),
                ('gls', 'Mercedes-Benz GLS'),
                ('gls_coupe', 'Mercedes-Benz GLS Coupe'),
                ('s_class', 'Mercedes-Benz S-Class'),
                ('sl', 'Mercedes-Benz SL'),
                ('slk', 'Mercedes-Benz SLK'),
                # Audi Models
                ('a3', 'Audi A3'),
                ('a4', 'Audi A4'),
                ('a5', 'Audi A5'),
                ('a6', 'Audi A6'),
                ('a7', 'Audi A7'),
                ('a8', 'Audi A8'),
                ('e_tron', 'Audi e-tron'),
                ('q2', 'Audi Q2'),
                ('q3', 'Audi Q3'),
                ('q5', 'Audi Q5'),
                ('q7', 'Audi Q7'),
                ('q8', 'Audi Q8'),
                ('r8', 'Audi R8'),
                ('tt', 'Audi TT'),
                # Nissan Models
                ('370z', 'Nissan 370Z'),
                ('altima', 'Nissan Altima'),
                ('armada', 'Nissan Armada'),
                ('frontier', 'Nissan Frontier'),
                ('gt_r', 'Nissan GT-R'),
                ('juke', 'Nissan Juke'),
                ('kicks', 'Nissan Kicks'),
                ('maxima', 'Nissan Maxima'),
                ('murano', 'Nissan Murano'),
                ('navara', 'Nissan Navara'),
                ('note', 'Nissan Note'),
                ('pathfinder', 'Nissan Pathfinder'),
                ('rogue', 'Nissan Rogue'),
                ('sentra', 'Nissan Sentra'),
                ('tiida', 'Nissan Tiida'),
                ('titan', 'Nissan Titan'),
                ('versa', 'Nissan Versa'),
                ('x_trail', 'Nissan X-Trail'),
                # Mazda Models
                ('cx_3', 'Mazda CX-3'),
                ('cx_30', 'Mazda CX-30'),
                ('cx_5', 'Mazda CX-5'),
                ('cx_50', 'Mazda CX-50'),
                ('cx_9', 'Mazda CX-9'),
                ('cx_90', 'Mazda CX-90'),
                ('mazda3', 'Mazda3'),
                ('mazda6', 'Mazda6'),
                ('mx_5_miata', 'Mazda MX-5 Miata'),
                ('rx_8', 'Mazda RX-8'),
                ('tribute', 'Mazda Tribute'),
                # Hyundai Models
                ('accent', 'Hyundai Accent'),
                ('azera', 'Hyundai Azera'),
                ('elantra', 'Hyundai Elantra'),
                ('genesis_sedan', 'Hyundai Genesis'),
                ('kona', 'Hyundai Kona'),
                ('palisade', 'Hyundai Palisade'),
                ('santa_cruz', 'Hyundai Santa Cruz'),
                ('santa_fe', 'Hyundai Santa Fe'),
                ('sonata', 'Hyundai Sonata'),
                ('tucson', 'Hyundai Tucson'),
                ('veloster', 'Hyundai Veloster'),
                ('venue', 'Hyundai Venue'),
                # Kia Models
                ('cadenza', 'Kia Cadenza'),
                ('carnival', 'Kia Carnival'),
                ('forte', 'Kia Forte'),
                ('niro', 'Kia Niro'),
                ('optima', 'Kia Optima'),
                ('rio', 'Kia Rio'),
                ('seltos', 'Kia Seltos'),
                ('sorento', 'Kia Sorento'),
                ('soul', 'Kia Soul'),
                ('sportage', 'Kia Sportage'),
                ('stinger', 'Kia Stinger'),
                ('telluride', 'Kia Telluride'),
                # Ford Models
                ('bronco', 'Ford Bronco'),
                ('crown_victoria', 'Ford Crown Victoria'),
                ('ecosport', 'Ford EcoSport'),
                ('edge', 'Ford Edge'),
                ('escape', 'Ford Escape'),
                ('expedition', 'Ford Expedition'),
                ('explorer', 'Ford Explorer'),
                ('f_150', 'Ford F-150'),
                ('fiesta', 'Ford Fiesta'),
                ('focus', 'Ford Focus'),
                ('fusion', 'Ford Fusion'),
                ('mustang', 'Ford Mustang'),
                ('ranger', 'Ford Ranger'),
                ('taurus', 'Ford Taurus'),
                # Chevrolet Models
                ('camaro', 'Chevrolet Camaro'),
                ('corvette', 'Chevrolet Corvette'),
                ('cruze', 'Chevrolet Cruze'),
                ('equinox', 'Chevrolet Equinox'),
                ('impala', 'Chevrolet Impala'),
                ('malibu', 'Chevrolet Malibu'),
                ('silverado', 'Chevrolet Silverado'),
                ('suburban', 'Chevrolet Suburban'),
                ('tahoe', 'Chevrolet Tahoe'),
                ('traverse', 'Chevrolet Traverse'),
                # Volkswagen Models
                ('arteon', 'Volkswagen Arteon'),
                ('atlas', 'Volkswagen Atlas'),
                ('beetle', 'Volkswagen Beetle'),
                ('golf', 'Volkswagen Golf'),
                ('jetta', 'Volkswagen Jetta'),
                ('passat', 'Volkswagen Passat'),
                ('polo', 'Volkswagen Polo'),
                ('tiguan', 'Volkswagen Tiguan'),
                ('touareg', 'Volkswagen Touareg'),
                # Subaru Models
                ('ascent', 'Subaru Ascent'),
                ('brz', 'Subaru BRZ'),
                ('crosstrek', 'Subaru Crosstrek'),
                ('forester', 'Subaru Forester'),
                ('impreza', 'Subaru Impreza'),
                ('legacy', 'Subaru Legacy'),
                ('outback', 'Subaru Outback'),
                ('wrx', 'Subaru WRX'),
                # Mitsubishi Models
                ('asx', 'Mitsubishi ASX'),
                ('eclipse_cross', 'Mitsubishi Eclipse Cross'),
                ('galant', 'Mitsubishi Galant'),
                ('l200', 'Mitsubishi L200'),
                ('lancer', 'Mitsubishi Lancer'),
                ('mirage', 'Mitsubishi Mirage'),
                ('outlander', 'Mitsubishi Outlander'),
                ('pajero', 'Mitsubishi Pajero'),
                # Lexus Models
                ('es', 'Lexus ES'),
                ('gx', 'Lexus GX'),
                ('is', 'Lexus IS'),
                ('lc', 'Lexus LC'),
                ('ls', 'Lexus LS'),
                ('lx', 'Lexus LX'),
                ('nx', 'Lexus NX'),
                ('rc', 'Lexus RC'),
                ('rx', 'Lexus RX'),
                ('ux', 'Lexus UX'),
                # Infiniti Models
                ('fx35', 'Infiniti FX35'),
                ('g35', 'Infiniti G35'),
                ('g37', 'Infiniti G37'),
                ('q50', 'Infiniti Q50'),
                ('q60', 'Infiniti Q60'),
                ('qx50', 'Infiniti QX50'),
                ('qx60', 'Infiniti QX60'),
                ('qx80', 'Infiniti QX80'),
                # Acura Models
                ('ilx', 'Acura ILX'),
                ('integra', 'Acura Integra'),
                ('mdx', 'Acura MDX'),
                ('nsx', 'Acura NSX'),
                ('rdx', 'Acura RDX'),
                ('rsx', 'Acura RSX'),
                ('tlx', 'Acura TLX'),
                ('tsx', 'Acura TSX'),
                # Jaguar Models
                ('e_pace', 'Jaguar E-PACE'),
                ('f_pace', 'Jaguar F-PACE'),
                ('f_type', 'Jaguar F-TYPE'),
                ('i_pace', 'Jaguar I-PACE'),
                ('xe', 'Jaguar XE'),
                ('xf', 'Jaguar XF'),
                ('xj', 'Jaguar XJ'),
                ('xk', 'Jaguar XK'),
                # Land Rover Models
                ('defender', 'Land Rover Defender'),
                ('discovery', 'Land Rover Discovery'),
                ('discovery_sport', 'Land Rover Discovery Sport'),
                ('freelander', 'Land Rover Freelander'),
                ('range_rover', 'Land Rover Range Rover'),
                ('range_rover_evoque', 'Land Rover Range Rover Evoque'),
                ('range_rover_sport', 'Land Rover Range Rover Sport'),
                ('velar', 'Land Rover Velar'),
                # Jeep Models
                ('cherokee', 'Jeep Cherokee'),
                ('compass', 'Jeep Compass'),
                ('gladiator', 'Jeep Gladiator'),
                ('grand_cherokee', 'Jeep Grand Cherokee'),
                ('liberty', 'Jeep Liberty'),
                ('patriot', 'Jeep Patriot'),
                ('renegade', 'Jeep Renegade'),
                ('wrangler', 'Jeep Wrangler'),
                # Volvo Models
                ('s40', 'Volvo S40'),
                ('s60', 'Volvo S60'),
                ('s90', 'Volvo S90'),
                ('v60', 'Volvo V60'),
                ('v90', 'Volvo V90'),
                ('xc40', 'Volvo XC40'),
                ('xc60', 'Volvo XC60'),
                ('xc90', 'Volvo XC90'),
                # Peugeot Models
                ('206', 'Peugeot 206'),
                ('208', 'Peugeot 208'),
                ('2008', 'Peugeot 2008'),
                ('308', 'Peugeot 308'),
                ('3008', 'Peugeot 3008'),
                ('407', 'Peugeot 407'),
                ('508', 'Peugeot 508'),
                ('5008', 'Peugeot 5008'),
                # Renault Models
                ('captur', 'Renault Captur'),
                ('clio', 'Renault Clio'),
                ('duster', 'Renault Duster'),
                ('fluence', 'Renault Fluence'),
                ('kadjar', 'Renault Kadjar'),
                ('koleos', 'Renault Koleos'),
                ('megane', 'Renault Megane'),
                ('scenic', 'Renault Scenic'),
                # Porsche Models
                ('911', 'Porsche 911'),
                ('boxster', 'Porsche Boxster'),
                ('cayenne', 'Porsche Cayenne'),
                ('cayman', 'Porsche Cayman'),
                ('macan', 'Porsche Macan'),
                ('panamera', 'Porsche Panamera'),
                # Cadillac Models
                ('ct5', 'Cadillac CT5'),
                ('cts', 'Cadillac CTS'),
                ('escalade', 'Cadillac Escalade'),
                ('srx', 'Cadillac SRX'),
                ('xt4', 'Cadillac XT4'),
                ('xt5', 'Cadillac XT5'),
                # Lincoln Models
                ('aviator', 'Lincoln Aviator'),
                ('continental', 'Lincoln Continental'),
                ('corsair', 'Lincoln Corsair'),
                ('nautilus', 'Lincoln Nautilus'),
                ('navigator', 'Lincoln Navigator'),
                # Genesis Models
                ('g70', 'Genesis G70'),
                ('g80', 'Genesis G80'),
                ('g90', 'Genesis G90'),
                ('gv70', 'Genesis GV70'),
                ('gv80', 'Genesis GV80'),
                # Additional Toyota Models
                ('alphard', 'Toyota Alphard'),
                ('aqua', 'Toyota Aqua'),
                ('auris', 'Toyota Auris'),
                ('avensis', 'Toyota Avensis'),
                ('belta', 'Toyota Belta'),
                ('blade', 'Toyota Blade'),
                ('caldina', 'Toyota Caldina'),
                ('carina', 'Toyota Carina'),
                ('century', 'Toyota Century'),
                ('chaser', 'Toyota Chaser'),
                ('coaster', 'Toyota Coaster'),
                ('cressida', 'Toyota Cressida'),
                ('cresta', 'Toyota Cresta'),
                ('duet', 'Toyota Duet'),
                ('echo', 'Toyota Echo'),
                ('estima', 'Toyota Estima'),
                ('fielder', 'Toyota Fielder'),
                ('fortuner', 'Toyota Fortuner'),
                ('funcargo', 'Toyota Funcargo'),
                ('gaia', 'Toyota Gaia'),
                ('granvia', 'Toyota Granvia'),
                ('hiace', 'Toyota Hiace'),
                ('ipsum', 'Toyota Ipsum'),
                ('ist', 'Toyota Ist'),
                ('kluger', 'Toyota Kluger'),
                ('landcruiser_prado', 'Toyota Land Cruiser Prado'),
                ('lite_ace', 'Toyota Lite Ace'),
                ('mark_ii', 'Toyota Mark II'),
                ('nadia', 'Toyota Nadia'),
                ('opa', 'Toyota Opa'),
                ('picnic', 'Toyota Picnic'),
                ('platz', 'Toyota Platz'),
                ('premio', 'Toyota Premio'),
                ('probox', 'Toyota Probox'),
                ('progres', 'Toyota Progres'),
                ('raum', 'Toyota Raum'),
                ('rush', 'Toyota Rush'),
                ('sai', 'Toyota Sai'),
                ('sienta', 'Toyota Sienta'),
                ('spacio', 'Toyota Spacio'),
                ('succeed', 'Toyota Succeed'),
                ('terrios', 'Toyota Terrios'),
                ('townace', 'Toyota Townace'),
                ('verossa', 'Toyota Verossa'),
                ('vellfire', 'Toyota Vellfire'),
                ('voltz', 'Toyota Voltz'),
                ('wish', 'Toyota Wish'),
                ('yaris_cross', 'Toyota Yaris Cross'),
                # Additional Honda Models
                ('airwave', 'Honda Airwave'),
                ('avancier', 'Honda Avancier'),
                ('city', 'Honda City'),
                ('concerto', 'Honda Concerto'),
                ('crossroad', 'Honda Crossroad'),
                ('domani', 'Honda Domani'),
                ('edix', 'Honda Edix'),
                ('elysion', 'Honda Elysion'),
                ('freed', 'Honda Freed'),
                ('grace', 'Honda Grace'),
                ('inspire', 'Honda Inspire'),
                ('integra', 'Honda Integra'),
                ('jade', 'Honda Jade'),
                ('lagreat', 'Honda Lagreat'),
                ('legend', 'Honda Legend'),
                ('life', 'Honda Life'),
                ('logo', 'Honda Logo'),
                ('mobilio', 'Honda Mobilio'),
                ('orthia', 'Honda Orthia'),
                ('partner', 'Honda Partner'),
                ('rafaga', 'Honda Rafaga'),
                ('shuttle', 'Honda Shuttle'),
                ('spike', 'Honda Spike'),
                ('torneo', 'Honda Torneo'),
                ('vamos', 'Honda Vamos'),
                ('vigor', 'Honda Vigor'),
                ('zest', 'Honda Zest'),
                # Additional BMW Models
                ('alpina_b3', 'BMW Alpina B3'),
                ('alpina_b5', 'BMW Alpina B5'),
                ('alpina_b7', 'BMW Alpina B7'),
                ('ix', 'BMW iX'),
                ('ix3', 'BMW iX3'),
                ('m2', 'BMW M2'),
                ('m3', 'BMW M3'),
                ('m4', 'BMW M4'),
                ('m5', 'BMW M5'),
                ('m6', 'BMW M6'),
                ('m8', 'BMW M8'),
                ('x3m', 'BMW X3 M'),
                ('x4m', 'BMW X4 M'),
                ('x5m', 'BMW X5 M'),
                ('x6m', 'BMW X6 M'),
                ('z3', 'BMW Z3'),
                ('z8', 'BMW Z8'),
                # Additional Mercedes-Benz Models
                ('a35_amg', 'Mercedes-Benz A35 AMG'),
                ('a45_amg', 'Mercedes-Benz A45 AMG'),
                ('amg_c63', 'Mercedes-Benz AMG C63'),
                ('amg_e63', 'Mercedes-Benz AMG E63'),
                ('amg_g63', 'Mercedes-Benz AMG G63'),
                ('amg_s63', 'Mercedes-Benz AMG S63'),
                ('b_class', 'Mercedes-Benz B-Class'),
                ('cla45_amg', 'Mercedes-Benz CLA45 AMG'),
                ('clk', 'Mercedes-Benz CLK'),
                ('cls53_amg', 'Mercedes-Benz CLS53 AMG'),
                ('eqc', 'Mercedes-Benz EQC'),
                ('eqs', 'Mercedes-Benz EQS'),
                ('glk', 'Mercedes-Benz GLK'),
                ('ml', 'Mercedes-Benz ML'),
                ('r_class', 'Mercedes-Benz R-Class'),
                ('slc', 'Mercedes-Benz SLC'),
                ('sls_amg', 'Mercedes-Benz SLS AMG'),
                ('sprinter', 'Mercedes-Benz Sprinter'),
                ('v_class', 'Mercedes-Benz V-Class'),
                # Additional Audi Models
                ('a1', 'Audi A1'),
                ('allroad', 'Audi Allroad'),
                ('e_tron_gt', 'Audi e-tron GT'),
                ('q4_e_tron', 'Audi Q4 e-tron'),
                ('rs3', 'Audi RS3'),
                ('rs4', 'Audi RS4'),
                ('rs5', 'Audi RS5'),
                ('rs6', 'Audi RS6'),
                ('rs7', 'Audi RS7'),
                ('rsq3', 'Audi RSQ3'),
                ('rsq8', 'Audi RSQ8'),
                ('s3', 'Audi S3'),
                ('s4', 'Audi S4'),
                ('s5', 'Audi S5'),
                ('s6', 'Audi S6'),
                ('s7', 'Audi S7'),
                ('s8', 'Audi S8'),
                ('sq5', 'Audi SQ5'),
                ('sq7', 'Audi SQ7'),
                ('sq8', 'Audi SQ8'),
                ('tt_rs', 'Audi TT RS'),
                ('tts', 'Audi TTS'),
                # Additional Nissan Models
                ('180sx', 'Nissan 180SX'),
                ('200sx', 'Nissan 200SX'),
                ('240sx', 'Nissan 240SX'),
                ('300zx', 'Nissan 300ZX'),
                ('350z', 'Nissan 350Z'),
                ('ad', 'Nissan AD'),
                ('almera', 'Nissan Almera'),
                ('avenir', 'Nissan Avenir'),
                ('bassara', 'Nissan Bassara'),
                ('bluebird', 'Nissan Bluebird'),
                ('caravan', 'Nissan Caravan'),
                ('cedric', 'Nissan Cedric'),
                ('cefiro', 'Nissan Cefiro'),
                ('cube', 'Nissan Cube'),
                ('dualis', 'Nissan Dualis'),
                ('elgrand', 'Nissan Elgrand'),
                ('expert', 'Nissan Expert'),
                ('fairlady', 'Nissan Fairlady'),
                ('fuga', 'Nissan Fuga'),
                ('gloria', 'Nissan Gloria'),
                ('lafesta', 'Nissan Lafesta'),
                ('largo', 'Nissan Largo'),
                ('laurel', 'Nissan Laurel'),
                ('leaf', 'Nissan Leaf'),
                ('liberty', 'Nissan Liberty'),
                ('march', 'Nissan March'),
                ('micra', 'Nissan Micra'),
                ('moco', 'Nissan Moco'),
                ('otti', 'Nissan Otti'),
                ('presage', 'Nissan Presage'),
                ('primera', 'Nissan Primera'),
                ('pulsar', 'Nissan Pulsar'),
                ('quest', 'Nissan Quest'),
                ('rasheen', 'Nissan Rasheen'),
                ('serena', 'Nissan Serena'),
                ('silvia', 'Nissan Silvia'),
                ('skyline', 'Nissan Skyline'),
                ('stagea', 'Nissan Stagea'),
                ('sunny', 'Nissan Sunny'),
                ('teana', 'Nissan Teana'),
                ('terrano', 'Nissan Terrano'),
                ('vanette', 'Nissan Vanette'),
                ('wingroad', 'Nissan Wingroad'),
                ('xterra', 'Nissan Xterra'),
                # Additional Mazda Models
                ('atenza', 'Mazda Atenza'),
                ('axela', 'Mazda Axela'),
                ('biante', 'Mazda Biante'),
                ('bongo', 'Mazda Bongo'),
                ('capella', 'Mazda Capella'),
                ('carol', 'Mazda Carol'),
                ('cx_7', 'Mazda CX-7'),
                ('demio', 'Mazda Demio'),
                ('familia', 'Mazda Familia'),
                ('flair', 'Mazda Flair'),
                ('lantis', 'Mazda Lantis'),
                ('millenia', 'Mazda Millenia'),
                ('mpv', 'Mazda MPV'),
                ('mx_6', 'Mazda MX-6'),
                ('premacy', 'Mazda Premacy'),
                ('protege', 'Mazda Protege'),
                ('roadster', 'Mazda Roadster'),
                ('rx_7', 'Mazda RX-7'),
                ('scrum', 'Mazda Scrum'),
                ('verisa', 'Mazda Verisa'),
                # Additional Hyundai Models
                ('atos', 'Hyundai Atos'),
                ('avante', 'Hyundai Avante'),
                ('centennial', 'Hyundai Centennial'),
                ('coupe', 'Hyundai Coupe'),
                ('creta', 'Hyundai Creta'),
                ('entourage', 'Hyundai Entourage'),
                ('equus', 'Hyundai Equus'),
                ('excel', 'Hyundai Excel'),
                ('galloper', 'Hyundai Galloper'),
                ('getz', 'Hyundai Getz'),
                ('grandeur', 'Hyundai Grandeur'),
                ('h1', 'Hyundai H1'),
                ('i10', 'Hyundai i10'),
                ('i20', 'Hyundai i20'),
                ('i30', 'Hyundai i30'),
                ('i40', 'Hyundai i40'),
                ('ioniq', 'Hyundai Ioniq'),
                ('ix35', 'Hyundai ix35'),
                ('lantra', 'Hyundai Lantra'),
                ('matrix', 'Hyundai Matrix'),
                ('nexo', 'Hyundai Nexo'),
                ('santa_fe_sport', 'Hyundai Santa Fe Sport'),
                ('starex', 'Hyundai Starex'),
                ('terracan', 'Hyundai Terracan'),
                ('tiburon', 'Hyundai Tiburon'),
                ('trajet', 'Hyundai Trajet'),
                ('veracruz', 'Hyundai Veracruz'),
                ('xg', 'Hyundai XG'),
                # Additional Kia Models
                ('besta', 'Kia Besta'),
                ('borrego', 'Kia Borrego'),
                ('carens', 'Kia Carens'),
                ('carnival_sedona', 'Kia Carnival/Sedona'),
                ('cerato', 'Kia Cerato'),
                ('clarus', 'Kia Clarus'),
                ('credos', 'Kia Credos'),
                ('enterprise', 'Kia Enterprise'),
                ('k3', 'Kia K3'),
                ('k5', 'Kia K5'),
                ('k7', 'Kia K7'),
                ('k9', 'Kia K9'),
                ('magentis', 'Kia Magentis'),
                ('mohave', 'Kia Mohave'),
                ('morning', 'Kia Morning'),
                ('opirus', 'Kia Opirus'),
                ('picanto', 'Kia Picanto'),
                ('pregio', 'Kia Pregio'),
                ('pride', 'Kia Pride'),
                ('quoris', 'Kia Quoris'),
                ('retona', 'Kia Retona'),
                ('rondo', 'Kia Rondo'),
                ('sedona', 'Kia Sedona'),
                ('sephia', 'Kia Sephia'),
                ('shuma', 'Kia Shuma'),
                ('spectra', 'Kia Spectra'),
                ('venga', 'Kia Venga'),
                # Additional Ford Models
                ('aerostar', 'Ford Aerostar'),
                ('aspire', 'Ford Aspire'),
                ('c_max', 'Ford C-Max'),
                ('contour', 'Ford Contour'),
                ('courier', 'Ford Courier'),
                ('excursion', 'Ford Excursion'),
                ('freestar', 'Ford Freestar'),
                ('freestyle', 'Ford Freestyle'),
                ('galaxy', 'Ford Galaxy'),
                ('ka', 'Ford Ka'),
                ('kuga', 'Ford Kuga'),
                ('maverick', 'Ford Maverick'),
                ('mondeo', 'Ford Mondeo'),
                ('puma', 'Ford Puma'),
                ('s_max', 'Ford S-Max'),
                ('scorpio', 'Ford Scorpio'),
                ('sierra', 'Ford Sierra'),
                ('streetka', 'Ford StreetKa'),
                ('tempo', 'Ford Tempo'),
                ('territory', 'Ford Territory'),
                ('thunderbird', 'Ford Thunderbird'),
                ('tourneo', 'Ford Tourneo'),
                ('transit', 'Ford Transit'),
                ('windstar', 'Ford Windstar'),
                # Additional Chevrolet Models
                ('astro', 'Chevrolet Astro'),
                ('avalanche', 'Chevrolet Avalanche'),
                ('aveo', 'Chevrolet Aveo'),
                ('blazer', 'Chevrolet Blazer'),
                ('captiva', 'Chevrolet Captiva'),
                ('cavalier', 'Chevrolet Cavalier'),
                ('cobalt', 'Chevrolet Cobalt'),
                ('colorado', 'Chevrolet Colorado'),
                ('express', 'Chevrolet Express'),
                ('hhr', 'Chevrolet HHR'),
                ('lumina', 'Chevrolet Lumina'),
                ('monte_carlo', 'Chevrolet Monte Carlo'),
                ('orlando', 'Chevrolet Orlando'),
                ('s10', 'Chevrolet S-10'),
                ('sonic', 'Chevrolet Sonic'),
                ('spark', 'Chevrolet Spark'),
                ('ssr', 'Chevrolet SSR'),
                ('trailblazer', 'Chevrolet Trailblazer'),
                ('uplander', 'Chevrolet Uplander'),
                ('venture', 'Chevrolet Venture'),
                ('volt', 'Chevrolet Volt'),
                # Additional Volkswagen Models
                ('amarok', 'Volkswagen Amarok'),
                ('bora', 'Volkswagen Bora'),
                ('caddy', 'Volkswagen Caddy'),
                ('cc', 'Volkswagen CC'),
                ('corrado', 'Volkswagen Corrado'),
                ('crafter', 'Volkswagen Crafter'),
                ('eos', 'Volkswagen Eos'),
                ('fox', 'Volkswagen Fox'),
                ('id3', 'Volkswagen ID.3'),
                ('id4', 'Volkswagen ID.4'),
                ('lupo', 'Volkswagen Lupo'),
                ('multivan', 'Volkswagen Multivan'),
                ('new_beetle', 'Volkswagen New Beetle'),
                ('phaeton', 'Volkswagen Phaeton'),
                ('routan', 'Volkswagen Routan'),
                ('scirocco', 'Volkswagen Scirocco'),
                ('sharan', 'Volkswagen Sharan'),
                ('t_cross', 'Volkswagen T-Cross'),
                ('t_roc', 'Volkswagen T-Roc'),
                ('taos', 'Volkswagen Taos'),
                ('transporter', 'Volkswagen Transporter'),
                ('up', 'Volkswagen Up!'),
                ('vento', 'Volkswagen Vento'),
                # Additional Subaru Models
                ('alcyone', 'Subaru Alcyone'),
                ('baja', 'Subaru Baja'),
                ('brat', 'Subaru BRAT'),
                ('domingo', 'Subaru Domingo'),
                ('exiga', 'Subaru Exiga'),
                ('justy', 'Subaru Justy'),
                ('leone', 'Subaru Leone'),
                ('levorg', 'Subaru Levorg'),
                ('libero', 'Subaru Libero'),
                ('loyale', 'Subaru Loyale'),
                ('pleo', 'Subaru Pleo'),
                ('r1', 'Subaru R1'),
                ('r2', 'Subaru R2'),
                ('sambar', 'Subaru Sambar'),
                ('stella', 'Subaru Stella'),
                ('svx', 'Subaru SVX'),
                ('tribeca', 'Subaru Tribeca'),
                ('vivio', 'Subaru Vivio'),
                ('xv', 'Subaru XV'),
                # Additional Mitsubishi Models
                ('3000gt', 'Mitsubishi 3000GT'),
                ('airtrek', 'Mitsubishi Airtrek'),
                ('carisma', 'Mitsubishi Carisma'),
                ('challenger', 'Mitsubishi Challenger'),
                ('chariot', 'Mitsubishi Chariot'),
                ('colt', 'Mitsubishi Colt'),
                ('delica', 'Mitsubishi Delica'),
                ('diamante', 'Mitsubishi Diamante'),
                ('eclipse', 'Mitsubishi Eclipse'),
                ('endeavor', 'Mitsubishi Endeavor'),
                ('evo', 'Mitsubishi Lancer Evolution'),
                ('expo', 'Mitsubishi Expo'),
                ('fto', 'Mitsubishi FTO'),
                ('grandis', 'Mitsubishi Grandis'),
                ('gto', 'Mitsubishi GTO'),
                ('i_miev', 'Mitsubishi i-MiEV'),
                ('legnum', 'Mitsubishi Legnum'),
                ('magna', 'Mitsubishi Magna'),
                ('montero', 'Mitsubishi Montero'),
                ('montero_sport', 'Mitsubishi Montero Sport'),
                ('raider', 'Mitsubishi Raider'),
                ('rvr', 'Mitsubishi RVR'),
                ('sigma', 'Mitsubishi Sigma'),
                ('space_star', 'Mitsubishi Space Star'),
                ('space_wagon', 'Mitsubishi Space Wagon'),
                ('starion', 'Mitsubishi Starion'),
                ('verada', 'Mitsubishi Verada'),
                # Additional Lexus Models (Premium Models)
                ('ct', 'Lexus CT'),
                ('gs', 'Lexus GS'),
                ('hs', 'Lexus HS'),
                ('lfa', 'Lexus LFA'),
                ('sc', 'Lexus SC'),
                # Additional Infiniti Models
                ('ex', 'Infiniti EX'),
                ('i30', 'Infiniti I30'),
                ('i35', 'Infiniti I35'),
                ('j30', 'Infiniti J30'),
                ('m30', 'Infiniti M30'),
                ('m35', 'Infiniti M35'),
                ('m37', 'Infiniti M37'),
                ('m45', 'Infiniti M45'),
                ('m56', 'Infiniti M56'),
                ('q30', 'Infiniti Q30'),
                ('q40', 'Infiniti Q40'),
                ('q45', 'Infiniti Q45'),
                ('q70', 'Infiniti Q70'),
                ('qx30', 'Infiniti QX30'),
                ('qx4', 'Infiniti QX4'),
                ('qx56', 'Infiniti QX56'),
                ('qx70', 'Infiniti QX70'),
                # Additional Acura Models
                ('cl', 'Acura CL'),
                ('csx', 'Acura CSX'),
                ('el', 'Acura EL'),
                ('legend_sedan', 'Acura Legend'),
                ('rl', 'Acura RL'),
                ('slx', 'Acura SLX'),
                ('tl', 'Acura TL'),
                ('vigor_sedan', 'Acura Vigor'),
                ('zdx', 'Acura ZDX'),
                # Additional Jaguar Models (Luxury)
                ('s_type', 'Jaguar S-Type'),
                ('x_type', 'Jaguar X-Type'),
                ('xf_sportbrake', 'Jaguar XF Sportbrake'),
                ('xfr', 'Jaguar XFR'),
                ('xj12', 'Jaguar XJ12'),
                ('xj6', 'Jaguar XJ6'),
                ('xj8', 'Jaguar XJ8'),
                ('xjr', 'Jaguar XJR'),
                ('xjs', 'Jaguar XJS'),
                ('xk8', 'Jaguar XK8'),
                ('xkr', 'Jaguar XKR'),
                # Additional Land Rover Models
                ('discovery_3', 'Land Rover Discovery 3'),
                ('discovery_4', 'Land Rover Discovery 4'),
                ('freelander_2', 'Land Rover Freelander 2'),
                ('lr2', 'Land Rover LR2'),
                ('lr3', 'Land Rover LR3'),
                ('lr4', 'Land Rover LR4'),
                ('range_rover_classic', 'Land Rover Range Rover Classic'),
                ('range_rover_hse', 'Land Rover Range Rover HSE'),
                ('range_rover_supercharged', 'Land Rover Range Rover Supercharged'),
                ('range_rover_vogue', 'Land Rover Range Rover Vogue'),
                # Additional Jeep Models
                ('cj5', 'Jeep CJ-5'),
                ('cj7', 'Jeep CJ-7'),
                ('commander', 'Jeep Commander'),
                ('grand_wagoneer', 'Jeep Grand Wagoneer'),
                ('tj', 'Jeep Wrangler TJ'),
                ('unlimited', 'Jeep Wrangler Unlimited'),
                ('wagoneer', 'Jeep Wagoneer'),
                ('yj', 'Jeep Wrangler YJ'),
                # Additional Volvo Models
                ('240', 'Volvo 240'),
                ('740', 'Volvo 740'),
                ('760', 'Volvo 760'),
                ('780', 'Volvo 780'),
                ('850', 'Volvo 850'),
                ('940', 'Volvo 940'),
                ('960', 'Volvo 960'),
                ('c30', 'Volvo C30'),
                ('c70', 'Volvo C70'),
                ('s70', 'Volvo S70'),
                ('s80', 'Volvo S80'),
                ('v40', 'Volvo V40'),
                ('v50', 'Volvo V50'),
                ('v70', 'Volvo V70'),
                ('xc70', 'Volvo XC70'),
                # Additional Peugeot Models
                ('1007', 'Peugeot 1007'),
                ('106', 'Peugeot 106'),
                ('107', 'Peugeot 107'),
                ('205', 'Peugeot 205'),
                ('207', 'Peugeot 207'),
                ('301', 'Peugeot 301'),
                ('306', 'Peugeot 306'),
                ('307', 'Peugeot 307'),
                ('309', 'Peugeot 309'),
                ('405', 'Peugeot 405'),
                ('406', 'Peugeot 406'),
                ('408', 'Peugeot 408'),
                ('504', 'Peugeot 504'),
                ('505', 'Peugeot 505'),
                ('605', 'Peugeot 605'),
                ('607', 'Peugeot 607'),
                ('807', 'Peugeot 807'),
                ('bipper', 'Peugeot Bipper'),
                ('boxer', 'Peugeot Boxer'),
                ('expert', 'Peugeot Expert'),
                ('ion', 'Peugeot iOn'),
                ('partner', 'Peugeot Partner'),
                ('rcz', 'Peugeot RCZ'),
                # Tesla Models
                ('model_3', 'Tesla Model 3'),
                ('model_s', 'Tesla Model S'),
                ('model_x', 'Tesla Model X'),
                ('model_y', 'Tesla Model Y'),
                ('cybertruck', 'Tesla Cybertruck'),
                ('roadster_tesla', 'Tesla Roadster'),
                ('semi', 'Tesla Semi'),
                # Ferrari Models
                ('488_gtb', 'Ferrari 488 GTB'),
                ('f8_tributo', 'Ferrari F8 Tributo'),
                ('sf90_stradale', 'Ferrari SF90 Stradale'),
                ('roma', 'Ferrari Roma'),
                ('portofino', 'Ferrari Portofino'),
                ('812_superfast', 'Ferrari 812 Superfast'),
                ('laferrari', 'Ferrari LaFerrari'),
                ('458_italia', 'Ferrari 458 Italia'),
                ('california', 'Ferrari California'),
                ('f12_berlinetta', 'Ferrari F12 Berlinetta'),
                # Lamborghini Models
                ('huracan', 'Lamborghini Huracan'),
                ('aventador', 'Lamborghini Aventador'),
                ('urus', 'Lamborghini Urus'),
                ('gallardo', 'Lamborghini Gallardo'),
                ('murcielago', 'Lamborghini Murcielago'),
                ('countach', 'Lamborghini Countach'),
                ('diablo', 'Lamborghini Diablo'),
                # Maserati Models
                ('ghibli', 'Maserati Ghibli'),
                ('levante', 'Maserati Levante'),
                ('quattroporte', 'Maserati Quattroporte'),
                ('granturismo', 'Maserati GranTurismo'),
                ('grancabrio', 'Maserati GranCabrio'),
                ('mc20', 'Maserati MC20'),
                # McLaren Models
                ('720s', 'McLaren 720S'),
                ('570s', 'McLaren 570S'),
                ('artura', 'McLaren Artura'),
                ('gt_mclaren', 'McLaren GT'),
                ('650s', 'McLaren 650S'),
                ('p1', 'McLaren P1'),
                ('senna', 'McLaren Senna'),
                # Aston Martin Models
                ('db11', 'Aston Martin DB11'),
                ('vantage', 'Aston Martin Vantage'),
                ('dbx', 'Aston Martin DBX'),
                ('dbs', 'Aston Martin DBS'),
                ('rapide', 'Aston Martin Rapide'),
                ('vanquish', 'Aston Martin Vanquish'),
                ('db9', 'Aston Martin DB9'),
                ('virage', 'Aston Martin Virage'),
                # Bentley Models
                ('continental_gt', 'Bentley Continental GT'),
                ('bentayga', 'Bentley Bentayga'),
                ('flying_spur', 'Bentley Flying Spur'),
                ('mulsanne', 'Bentley Mulsanne'),
                ('arnage', 'Bentley Arnage'),
                ('azure', 'Bentley Azure'),
                ('brooklands', 'Bentley Brooklands'),
                # Rolls Royce Models
                ('ghost', 'Rolls Royce Ghost'),
                ('phantom', 'Rolls Royce Phantom'),
                ('cullinan', 'Rolls Royce Cullinan'),
                ('wraith', 'Rolls Royce Wraith'),
                ('dawn', 'Rolls Royce Dawn'),
                ('corniche', 'Rolls Royce Corniche'),
                ('silver_seraph', 'Rolls Royce Silver Seraph'),
                # Alfa Romeo Models
                ('giulia', 'Alfa Romeo Giulia'),
                ('giulietta', 'Alfa Romeo Giulietta'),
                ('stelvio', 'Alfa Romeo Stelvio'),
                ('tonale', 'Alfa Romeo Tonale'),
                ('4c', 'Alfa Romeo 4C'),
                ('mito', 'Alfa Romeo MiTo'),
                ('159', 'Alfa Romeo 159'),
                ('brera', 'Alfa Romeo Brera'),
                ('spider_alfa', 'Alfa Romeo Spider'),
                ('gt_alfa', 'Alfa Romeo GT'),
                # Mini Models
                ('cooper', 'Mini Cooper'),
                ('countryman', 'Mini Countryman'),
                ('clubman', 'Mini Clubman'),
                ('paceman', 'Mini Paceman'),
                ('roadster_mini', 'Mini Roadster'),
                ('coupe_mini', 'Mini Coupe'),
                ('john_cooper_works', 'Mini John Cooper Works'),
                # Fiat Models
                ('500', 'Fiat 500'),
                ('500x', 'Fiat 500X'),
                ('500l', 'Fiat 500L'),
                ('panda', 'Fiat Panda'),
                ('punto', 'Fiat Punto'),
                ('tipo', 'Fiat Tipo'),
                ('bravo', 'Fiat Bravo'),
                ('doblo', 'Fiat Doblo'),
                ('ducato', 'Fiat Ducato'),
                ('grande_punto', 'Fiat Grande Punto'),
                # Suzuki Models
                ('swift', 'Suzuki Swift'),
                ('vitara', 'Suzuki Vitara'),
                ('jimny', 'Suzuki Jimny'),
                ('baleno', 'Suzuki Baleno'),
                ('s_cross', 'Suzuki S-Cross'),
                ('alto', 'Suzuki Alto'),
                ('celerio', 'Suzuki Celerio'),
                ('ciaz', 'Suzuki Ciaz'),
                ('ertiga', 'Suzuki Ertiga'),
                ('grand_vitara', 'Suzuki Grand Vitara'),
                ('ignis', 'Suzuki Ignis'),
                ('kizashi', 'Suzuki Kizashi'),
                ('sx4', 'Suzuki SX4'),
                ('wagon_r', 'Suzuki Wagon R'),
                ('xl6', 'Suzuki XL6'),
                # Skoda Models
                ('octavia', 'Skoda Octavia'),
                ('superb', 'Skoda Superb'),
                ('fabia', 'Skoda Fabia'),
                ('kodiaq', 'Skoda Kodiaq'),
                ('karoq', 'Skoda Karoq'),
                ('kamiq', 'Skoda Kamiq'),
                ('scala', 'Skoda Scala'),
                ('rapid', 'Skoda Rapid'),
                ('citigo', 'Skoda Citigo'),
                ('yeti', 'Skoda Yeti'),
                ('roomster', 'Skoda Roomster'),
                # Seat Models
                ('leon', 'Seat Leon'),
                ('ibiza', 'Seat Ibiza'),
                ('ateca', 'Seat Ateca'),
                ('arona', 'Seat Arona'),
                ('tarraco', 'Seat Tarraco'),
                ('toledo', 'Seat Toledo'),
                ('alhambra', 'Seat Alhambra'),
                ('altea', 'Seat Altea'),
                ('cordoba', 'Seat Cordoba'),
                ('exeo', 'Seat Exeo'),
                ('mii', 'Seat Mii'),
                # Other Popular Models
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


class CustomAuthenticationForm(forms.Form):
    """Enhanced authentication form with comprehensive validation and styling"""
    username = forms.CharField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'data-validation': 'email'
        }),
        help_text='Enter the email address associated with your account.',
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'data-validation': 'password'
        }),
        error_messages={
            'required': 'Password is required.'
        }
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Remember me for 30 days",
        widget=forms.CheckboxInput(attrs={
            'class': 'auth-checkbox'
        }),
        help_text='Keep me signed in on this device for 30 days.'
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        # Skip parent class validation to avoid username format validation
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

    def get_user(self):
        """Return the authenticated user"""
        return self.user_cache

    def confirm_login_allowed(self, user):
        """Check if the user is allowed to log in"""
        if not user.is_active:
            raise ValidationError("This account is inactive.")

    def clean_username(self):
        """Enhanced email validation with detailed error messages"""
        email = self.cleaned_data.get('username')
        if email:
            # Validate email format
            try:
                from django.core.validators import validate_email
                validate_email(email)
            except ValidationError:
                raise ValidationError("Please enter a valid email address.")

            # Check if email exists in database
            if not User.objects.filter(email=email).exists():
                raise ValidationError("No account found with this email address. Please check your email or register for a new account.")

            # Check if account is active
            user = User.objects.filter(email=email).first()
            if user and not user.is_active:
                raise ValidationError("This account has been deactivated. Please contact support for assistance.")

        return email

    def clean_password(self):
        """Enhanced password validation"""
        password = self.cleaned_data.get('password')
        if password:
            # Basic length check
            if len(password) < 1:
                raise ValidationError("Password is required.")
        return password


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
