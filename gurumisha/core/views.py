from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q, Min, Max, Avg
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
import logging
from .models import (
    Car, CarBrand, CarModel, VehicleCondition, SparePart, ImportRequest, ImportOrder, ImportOrderStatusHistory, ImportOrderDocument,
    Inquiry, Testimonial, BlogPost, Vendor, User,
    Cart, CartItem, Order, OrderItem, Payment, Invoice, StockMovement,
    OpinionPoll, PollOption, PollVote, OpinionReview, ReviewHelpfulVote
)
from .forms import (
    CustomUserRegistrationForm, CustomLoginForm, SellCarForm,
    ImportRequestForm, ContactForm, CustomPasswordResetForm, CustomSetPasswordForm,
    CustomAuthenticationForm, ResendVerificationEmailForm,
    VerificationCodeForm, RequestVerificationCodeForm
)

# Import HTMX views
from .htmx_spare_parts_views import (
    spare_parts_live_search, spare_parts_quick_view, add_to_cart_htmx,
    update_cart_quantity_htmx, spare_parts_category_filter, spare_parts_stats_htmx
)

# Initialize logger
logger = logging.getLogger(__name__)


# Authentication Views
def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('core:homepage')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = form.cleaned_data.get('remember_me', False)

            # Check email verification
            if not user.is_email_verified:
                messages.warning(
                    request,
                    'Please verify your email address before logging in. Check your inbox for the verification link.'
                )
                return redirect('core:email_verification_required')

            login(request, user)

            # Enhanced session expiry based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(2592000)  # 30 days (30 * 24 * 60 * 60)

            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')

            # Redirect based on user role
            if user.role == 'admin':
                return redirect('core:dashboard')
            else:
                return redirect('core:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomAuthenticationForm()

    return render(request, 'core/auth/login.html', {'form': form})


def user_register(request):
    """Enhanced user registration view with email verification"""
    if request.user.is_authenticated:
        return redirect('core:homepage')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Account created successfully for {user.get_full_name() or user.username}! '
                'Please check your email to verify your account before logging in.'
            )
            return redirect('core:email_verification_sent')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomUserRegistrationForm()

    return render(request, 'core/auth/register.html', {'form': form})


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:homepage')


def forgot_password(request):
    """Forgot password view with custom form and harrier design"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            # Send password reset email
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='core/auth/password_reset_email.html',
                subject_template_name='core/auth/password_reset_subject.txt',
            )
            messages.success(
                request,
                'Password reset instructions have been sent to your email address.'
            )
            return redirect('core:password_reset_done')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomPasswordResetForm()

    return render(request, 'core/auth/forgot_password.html', {'form': form})


def password_reset_done(request):
    """Password reset done view"""
    return render(request, 'core/auth/password_reset_done.html')


def password_reset_confirm(request, uidb64=None, token=None):
    """Password reset confirm view with custom form"""
    from django.contrib.auth.views import PasswordResetConfirmView
    from django.urls import reverse_lazy

    class CustomPasswordResetConfirmView(PasswordResetConfirmView):
        form_class = CustomSetPasswordForm
        template_name = 'core/auth/password_reset_confirm.html'
        success_url = reverse_lazy('core:password_reset_complete')

        def form_valid(self, form):
            messages.success(
                self.request,
                'Your password has been reset successfully. You can now log in with your new password.'
            )
            return super().form_valid(form)

        def form_invalid(self, form):
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, error)
            return super().form_invalid(form)

    view = CustomPasswordResetConfirmView.as_view()
    return view(request, uidb64=uidb64, token=token)


def password_reset_complete(request):
    """Password reset complete view"""
    return render(request, 'core/auth/password_reset_complete.html')


def verify_email(request, token):
    """Email verification view"""
    try:
        user = User.objects.get(email_verification_token=token)

        if user.is_email_verification_token_valid():
            user.verify_email()
            messages.success(
                request,
                'Your email has been verified successfully! You can now access all features.'
            )
            return render(request, 'core/auth/email_verification_success.html', {'user': user})
        else:
            messages.error(
                request,
                'This verification link has expired. Please request a new verification email.'
            )
            return render(request, 'core/auth/email_verification_expired.html')

    except User.DoesNotExist:
        messages.error(
            request,
            'Invalid verification link. Please check the link or request a new verification email.'
        )
        return render(request, 'core/auth/email_verification_invalid.html')


def resend_verification_email(request):
    """Resend email verification view"""
    if request.method == 'POST':
        form = ResendVerificationEmailForm(request.POST)
        if form.is_valid():
            if form.send_verification_email():
                messages.success(
                    request,
                    'Verification email has been sent! Please check your inbox.'
                )
                return redirect('core:email_verification_sent')
            else:
                messages.error(
                    request,
                    'Failed to send verification email. Please try again later.'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ResendVerificationEmailForm()

    return render(request, 'core/auth/resend_verification.html', {'form': form})


def email_verification_sent(request):
    """Email verification sent confirmation view"""
    return render(request, 'core/auth/email_verification_sent.html')


def email_verification_required(request):
    """Email verification required view"""
    return render(request, 'core/auth/email_verification_required.html')


@login_required
def user_dashboard(request):
    """Enhanced user dashboard view with role-based context"""
    user = request.user
    context = {
        'user': user,
    }

    if user.role == 'admin':
        # Admin dashboard context with import tracking stats
        from django.db.models import Count
        from datetime import timedelta

        # Import tracking stats
        total_import_orders = ImportOrder.objects.count()
        pending_imports = ImportOrder.objects.filter(
            status__in=['quotation_pending', 'confirmed']
        ).count()
        in_transit_count = ImportOrder.objects.filter(status='in_transit').count()
        arrived_count = ImportOrder.objects.filter(status='arrived_docked').count()
        active_orders = ImportOrder.objects.exclude(
            status__in=['delivered', 'cancelled']
        ).count()
        new_inquiries = Inquiry.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        context.update({
            'total_users': User.objects.count(),
            'active_vendors': Vendor.objects.filter(is_approved=True).count(),
            'pending_approvals': Car.objects.filter(is_approved=False).count() +
                               Vendor.objects.filter(is_approved=False).count(),
            'total_listings': Car.objects.count(),
            'recent_users': User.objects.order_by('-date_joined')[:5],
            'pending_cars': Car.objects.filter(is_approved=False).order_by('-created_at')[:5],
            # Import tracking stats for sidebar
            'total_import_orders': total_import_orders,
            'pending_imports': pending_imports,
            'in_transit_count': in_transit_count,
            'arrived_count': arrived_count,
            'active_orders': active_orders,
            'new_inquiries': new_inquiries,
        })

    elif user.role == 'vendor':
        try:
            vendor = user.vendor
            vendor_cars = Car.objects.filter(vendor=vendor)
            total_views = sum(car.views_count for car in vendor_cars)

            # Get analytics data for vendor
            from .utils.analytics_utils import get_analytics_dashboard_data
            analytics_data = get_analytics_dashboard_data(user)
            monthly_growth = analytics_data.get('view_growth_rate', 0) if analytics_data else 0

            context.update({
                'vendor': vendor,
                'vendor_cars': vendor_cars.order_by('-created_at')[:5],
                'pending_inquiries': Inquiry.objects.filter(
                    car__vendor=vendor, status='open'
                ).order_by('-created_at')[:5],
                'total_views': total_views,
                'monthly_growth': monthly_growth,
                'analytics_data': analytics_data,
            })
        except Vendor.DoesNotExist:
            # Vendor profile doesn't exist, redirect to create one
            messages.warning(request, 'Please complete your vendor profile.')
            return redirect('core:vendor_profile_create')

    elif user.role == 'customer':
        # Get user's car listings count if they have a vendor profile
        user_pending_cars_count = 0
        try:
            vendor = user.vendor
            user_pending_cars_count = Car.objects.filter(vendor=vendor, is_approved=False).count()
        except Vendor.DoesNotExist:
            pass

        context.update({
            'customer_inquiries': Inquiry.objects.filter(customer=user).order_by('-created_at')[:5],
            'import_requests': ImportRequest.objects.filter(customer=user).order_by('-created_at')[:5],
            'import_orders': ImportOrder.objects.filter(customer=user).order_by('-created_at')[:5],
            'user_pending_cars_count': user_pending_cars_count,
        })

    return render(request, 'core/dashboard.html', context)


def homepage(request):
    """Homepage with all sections"""
    from django.db.models import Case, When, IntegerField

    # Get featured cars (max 9)
    featured_cars = Car.objects.filter(
        is_approved=True,
        is_featured=True
    ).order_by('-calculated_rating', '-views_count')[:9]

    # Get active hot deals
    hot_deals = Car.objects.filter(
        is_approved=True,
        is_hot_deal=True
    ).order_by('-created_at')[:4]

    # Year range for search form
    current_year = timezone.now().year
    year_range = list(range(1990, current_year + 2))
    year_range.reverse()  # Show newest years first

    context = {
        'featured_cars': featured_cars,
        'car_brands': CarBrand.objects.filter(is_active=True)[:8],
        'testimonials': Testimonial.objects.filter(is_approved=True, is_featured=True)[:3],
        'blog_posts': BlogPost.objects.filter(is_published=True)[:3],
        'hot_deals': hot_deals,
        'vehicle_types': ['SUV', 'Sedan', 'Hatchback', 'Pickup', 'Coupe', 'Convertible'],
        'spare_part_categories': ['Engine Parts', 'Brake System', 'Electrical', 'Body Parts'],
        'year_range': year_range,
    }
    return render(request, 'core/homepage.html', context)


class CarListView(ListView):
    """Enhanced car listing page with advanced filters and HTMX support"""
    model = Car
    template_name = 'core/car_list.html'
    context_object_name = 'cars'
    paginate_by = 12

    def get_queryset(self):
        queryset = Car.objects.filter(is_approved=True).select_related('brand', 'model')

        # Search filters - enhanced to include more fields
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(model__name__icontains=search) |
                Q(description__icontains=search) |
                Q(features__icontains=search)
            )

        # Brand filter
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand__id=brand)

        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Year range filter - enhanced
        min_year = self.request.GET.get('min_year')
        max_year = self.request.GET.get('max_year')
        if min_year:
            queryset = queryset.filter(year__gte=min_year)
        if max_year:
            queryset = queryset.filter(year__lte=max_year)

        # Mileage filter - new
        max_mileage = self.request.GET.get('max_mileage')
        if max_mileage:
            queryset = queryset.filter(mileage__lte=max_mileage)

        # Fuel type filter
        fuel_type = self.request.GET.get('fuel_type')
        if fuel_type:
            queryset = queryset.filter(fuel_type=fuel_type)

        # Transmission filter
        transmission = self.request.GET.get('transmission')
        if transmission:
            queryset = queryset.filter(transmission=transmission)

        # Condition filter - updated for VehicleCondition foreign key
        condition = self.request.GET.get('condition')
        if condition:
            try:
                # Filter by condition ID since it's now a foreign key
                queryset = queryset.filter(condition__id=condition)
            except (ValueError, TypeError):
                # If condition is not a valid ID, skip filtering
                pass

        # Vendor filter - for dealer profile pages
        vendor = self.request.GET.get('vendor')
        if vendor:
            queryset = queryset.filter(vendor__id=vendor)

        # Listing type filter - new pill section feature
        listing_type = self.request.GET.get('listing_type')
        if listing_type:
            queryset = queryset.filter(listing_type=listing_type)

        # Featured filter
        featured_only = self.request.GET.get('featured_only')
        if featured_only:
            queryset = queryset.filter(is_featured=True)

        # Star rating filter
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.filter(calculated_rating__gte=min_rating)
            except ValueError:
                pass

        # Hot deals filter
        hot_deals_only = self.request.GET.get('hot_deals')
        if hot_deals_only:
            queryset = queryset.filter(is_hot_deal=True)

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        else:
            # Default: show available and featured cars
            queryset = queryset.filter(status__in=['available', 'featured'])

        # Sorting - enhanced options with star ratings and featured priority
        sort_by = self.request.GET.get('sort', 'featured')

        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'year_new':
            queryset = queryset.order_by('-year')
        elif sort_by == 'year_old':
            queryset = queryset.order_by('year')
        elif sort_by == 'mileage_low':
            queryset = queryset.order_by('mileage')
        elif sort_by == 'mileage_high':
            queryset = queryset.order_by('-mileage')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'rating_high':
            queryset = queryset.order_by('-calculated_rating', '-views_count')
        elif sort_by == 'rating_low':
            queryset = queryset.order_by('calculated_rating', '-views_count')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:  # featured (default) - prioritize featured cars
            from django.db.models import Case, When, IntegerField
            queryset = queryset.annotate(
                featured_priority=Case(
                    When(is_featured=True, then=1),
                    default=999,
                    output_field=IntegerField()
                )
            ).order_by('featured_priority', '-calculated_rating', '-views_count')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Enhanced context data
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        context['fuel_types'] = Car.FUEL_TYPE_CHOICES
        context['transmission_types'] = Car.TRANSMISSION_CHOICES
        # Get condition types from VehicleCondition model
        from .models import VehicleCondition
        context['condition_types'] = [(condition.id, condition.name) for condition in VehicleCondition.objects.filter(is_active=True).order_by('display_order', 'name')]

        # Promotion system context - simplified for binary featured system
        context['featured_options'] = [
            ('featured', 'Featured Cars'),
            ('certified', 'Certified Cars'),
            ('hot_deals', 'Hot Deals'),
        ]
        context['rating_options'] = [
            (4.5, '4.5+ stars'),
            (4.0, '4+ stars'),
            (3.5, '3.5+ stars'),
            (3.0, '3+ stars'),
            (2.5, '2.5+ stars'),
            (2.0, '2+ stars'),
        ]
        context['sort_options'] = [
            ('featured', 'Featured First'),
            ('rating_high', 'Highest Rated'),
            ('rating_low', 'Lowest Rated'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('year_new', 'Year: Newest First'),
            ('year_old', 'Year: Oldest First'),
            ('popular', 'Most Popular'),
            ('newest', 'Recently Added'),
        ]
        context['current_filters'] = self.request.GET

        # Year range for filters
        current_year = timezone.now().year
        context['year_range'] = range(1990, current_year + 2)

        # Pill section counts - get counts for each listing type
        base_queryset = Car.objects.filter(is_approved=True, status__in=['available', 'featured'])
        context['total_cars'] = base_queryset.count()
        context['imported_count'] = base_queryset.filter(listing_type='imported').count()
        context['sell_behalf_count'] = base_queryset.filter(listing_type='sell_behalf').count()
        context['auction_count'] = base_queryset.filter(listing_type='auction').count()
        context['local_count'] = base_queryset.filter(listing_type='local').count()

        # Add car brands for the brand showcase section
        context['car_brands'] = CarBrand.objects.filter(is_active=True).prefetch_related('car_set')[:6]

        # Add recently viewed cars
        context['recently_viewed_cars'] = self.get_recently_viewed_cars()

        return context

    def get_recently_viewed_cars(self):
        """Get recently viewed cars for the current user/session"""
        from .models import RecentlyViewedCar

        if self.request.user.is_authenticated:
            # For authenticated users
            recently_viewed = RecentlyViewedCar.objects.filter(
                user=self.request.user
            ).select_related('car', 'car__brand', 'car__model').order_by('-viewed_at')[:5]
        else:
            # For anonymous users, use session
            session_key = self.request.session.session_key
            if session_key:
                recently_viewed = RecentlyViewedCar.objects.filter(
                    session_key=session_key
                ).select_related('car', 'car__brand', 'car__model').order_by('-viewed_at')[:5]
            else:
                recently_viewed = RecentlyViewedCar.objects.none()

        return [rv.car for rv in recently_viewed if rv.car.is_approved]

    def render_to_response(self, context, **response_kwargs):
        # Handle HTMX requests by returning only the results section
        if self.request.headers.get('HX-Request'):
            # Create a partial template for HTMX responses
            return render(self.request, 'core/partials/car_list_results.html', context)
        return super().render_to_response(context, **response_kwargs)


class CarDetailView(DetailView):
    """Car detail page"""
    model = Car
    template_name = 'core/car_detail.html'
    context_object_name = 'car'

    def get_queryset(self):
        return Car.objects.filter(is_approved=True)

    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])

        # Track recently viewed car
        self.track_recently_viewed(obj)

        return obj

    def track_recently_viewed(self, car):
        """Track this car as recently viewed"""
        from .models import RecentlyViewedCar

        # Get session key for anonymous users
        if not self.request.session.session_key:
            self.request.session.create()
        session_key = self.request.session.session_key

        # Get client IP
        ip_address = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0]
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')

        if self.request.user.is_authenticated:
            # For authenticated users
            recently_viewed, created = RecentlyViewedCar.objects.update_or_create(
                user=self.request.user,
                car=car,
                defaults={
                    'ip_address': ip_address,
                    'session_key': session_key,
                }
            )
            if not created:
                # Update the viewed_at timestamp
                recently_viewed.save()
        else:
            # For anonymous users
            recently_viewed, created = RecentlyViewedCar.objects.update_or_create(
                session_key=session_key,
                car=car,
                defaults={
                    'ip_address': ip_address,
                }
            )
            if not created:
                # Update the viewed_at timestamp
                recently_viewed.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car = self.object

        # Related cars
        context['related_cars'] = Car.objects.filter(
            brand=car.brand,
            is_approved=True,
            status='available'
        ).exclude(id=car.id)[:4]

        # Rating system context
        if self.request.user.is_authenticated:
            try:
                from .models import CarRating
                user_rating = CarRating.objects.get(car=car, customer=self.request.user)
                context['user_rating'] = user_rating
            except CarRating.DoesNotExist:
                context['user_rating'] = None

        # Hot deal information
        if car.is_hot_deal:
            try:
                from .models import HotDeal
                hot_deal = HotDeal.objects.get(car=car)
                if hot_deal.is_currently_active():
                    context['hot_deal'] = hot_deal
            except HotDeal.DoesNotExist:
                pass

        return context


@login_required
def submit_car_rating(request):
    """Submit a car rating via HTMX"""
    if request.method == 'POST':
        from .models import CarRating

        car_id = request.POST.get('car_id')
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')

        try:
            car = get_object_or_404(Car, id=car_id, is_approved=True)
            rating_value = float(rating)

            # Validate rating value
            if not (0.5 <= rating_value <= 5.0):
                return JsonResponse({
                    'success': False,
                    'message': 'Rating must be between 0.5 and 5.0'
                })

            # Round to nearest 0.5
            rating_value = round(rating_value * 2) / 2

            # Create or update rating
            car_rating, created = CarRating.objects.update_or_create(
                car=car,
                customer=request.user,
                defaults={
                    'rating': rating_value,
                    'review': review,
                    'is_approved': False  # Requires admin approval
                }
            )

            # Update car's calculated rating
            car.update_calculated_rating()

            return JsonResponse({
                'success': True,
                'message': 'Thank you for your rating! It will be reviewed before being published.',
                'rating': rating_value,
                'created': created
            })

        except Car.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Car not found'
            })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid rating value'
            })
        except Exception:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while submitting your rating'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def htmx_featured_cars_filter(request):
    """HTMX endpoint for filtering featured cars"""
    tier = request.GET.get('tier', '')
    min_rating = request.GET.get('min_rating', '')

    # Base queryset for featured cars
    cars = Car.objects.filter(
        is_approved=True,
        is_featured=True
    ).select_related('brand', 'model', 'vendor')

    # Apply filters
    if min_rating:
        try:
            min_rating_value = float(min_rating)
            cars = cars.filter(calculated_rating__gte=min_rating_value)
        except ValueError:
            pass

    # Order by rating and views
    cars = cars.order_by('-calculated_rating', '-views_count')[:12]

    context = {'cars': cars}
    return render(request, 'components/featured_cars_grid.html', context)


def htmx_hot_deals_refresh(request):
    """HTMX endpoint for refreshing hot deals"""
    from .models import HotDeal

    # Get active hot deals
    hot_deals = HotDeal.objects.filter(
        is_active=True,
        car__is_approved=True
    ).select_related('car', 'car__brand', 'car__model').order_by('-created_at')[:8]

    context = {'hot_deals': hot_deals}
    return render(request, 'components/hot_deals_grid.html', context)


def htmx_car_rating_form(request, car_id):
    """HTMX endpoint for car rating form"""
    car = get_object_or_404(Car, id=car_id, is_approved=True)

    if request.method == 'POST' and request.user.is_authenticated:
        from .models import CarRating

        rating = request.POST.get('rating')
        review = request.POST.get('review', '')

        try:
            rating_value = float(rating)
            rating_value = round(rating_value * 2) / 2  # Round to nearest 0.5

            # Create or update rating
            car_rating, created = CarRating.objects.update_or_create(
                car=car,
                customer=request.user,
                defaults={
                    'rating': rating_value,
                    'review': review,
                    'is_approved': False
                }
            )

            # Update car's calculated rating
            car.update_calculated_rating()

            context = {
                'car': car,
                'success': True,
                'message': 'Thank you for your rating! It will be reviewed before being published.',
                'user_rating': car_rating
            }

        except ValueError:
            context = {
                'car': car,
                'error': True,
                'message': 'Invalid rating value'
            }
    else:
        # Get user's existing rating if any
        user_rating = None
        if request.user.is_authenticated:
            try:
                from .models import CarRating
                user_rating = CarRating.objects.get(car=car, customer=request.user)
            except CarRating.DoesNotExist:
                pass

        context = {
            'car': car,
            'user_rating': user_rating
        }

    return render(request, 'components/car_rating_form.html', context)


def htmx_promotion_analytics_widget(request):
    """HTMX endpoint for promotion analytics widget"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    from .analytics_utils import PromotionAnalyticsManager

    analytics = PromotionAnalyticsManager()
    days = int(request.GET.get('days', 7))

    # Get recent metrics
    daily_metrics = analytics.get_daily_metrics(days)
    featured_performance = analytics.get_featured_cars_performance(days)

    context = {
        'daily_metrics': daily_metrics,
        'featured_performance': featured_performance,
        'days': days
    }

    return render(request, 'components/promotion_analytics_widget.html', context)


def htmx_countdown_timer_update(request, deal_id):
    """HTMX endpoint for updating countdown timer"""
    from .models import HotDeal

    try:
        hot_deal = HotDeal.objects.get(id=deal_id, is_active=True)

        if not hot_deal.is_currently_active():
            # Deal expired
            context = {
                'deal': hot_deal,
                'expired': True
            }
        else:
            context = {
                'deal': hot_deal,
                'time_remaining': hot_deal.time_remaining_formatted()
            }

        return render(request, 'components/countdown_timer.html', context)

    except HotDeal.DoesNotExist:
        return render(request, 'components/countdown_timer.html', {'expired': True})


def htmx_car_list_filter(request):
    """HTMX endpoint for dynamic car list filtering"""
    # Get filter parameters
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    year_from = request.GET.get('year_from')
    year_to = request.GET.get('year_to')
    fuel_type = request.GET.get('fuel_type')
    transmission = request.GET.get('transmission')
    condition = request.GET.get('condition')
    featured_only = request.GET.get('featured_only')
    min_rating = request.GET.get('min_rating')
    hot_deals_only = request.GET.get('hot_deals')
    sort_by = request.GET.get('sort', 'featured')

    # Base queryset
    cars = Car.objects.filter(
        is_approved=True,
        status__in=['available', 'featured']
    ).select_related('brand', 'model', 'vendor')

    # Apply filters
    if brand:
        cars = cars.filter(brand_id=brand)

    if min_price:
        try:
            cars = cars.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            cars = cars.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if year_from:
        try:
            cars = cars.filter(year__gte=int(year_from))
        except ValueError:
            pass

    if year_to:
        try:
            cars = cars.filter(year__lte=int(year_to))
        except ValueError:
            pass

    if fuel_type:
        cars = cars.filter(fuel_type=fuel_type)

    if transmission:
        cars = cars.filter(transmission=transmission)

    if condition:
        cars = cars.filter(condition=condition)

    if featured_only:
        cars = cars.filter(is_featured=True)

    if min_rating:
        try:
            min_rating_value = float(min_rating)
            cars = cars.filter(calculated_rating__gte=min_rating_value)
        except ValueError:
            pass

    if hot_deals_only:
        cars = cars.filter(is_hot_deal=True)

    # Apply sorting
    if sort_by == 'price_low':
        cars = cars.order_by('price')
    elif sort_by == 'price_high':
        cars = cars.order_by('-price')
    elif sort_by == 'year_new':
        cars = cars.order_by('-year')
    elif sort_by == 'year_old':
        cars = cars.order_by('year')
    elif sort_by == 'rating_high':
        cars = cars.order_by('-calculated_rating', '-views_count')
    elif sort_by == 'rating_low':
        cars = cars.order_by('calculated_rating', '-views_count')
    elif sort_by == 'popular':
        cars = cars.order_by('-views_count')
    elif sort_by == 'newest':
        cars = cars.order_by('-created_at')
    else:  # featured (default)
        from django.db.models import Case, When, IntegerField
        cars = cars.annotate(
            featured_priority=Case(
                When(is_featured=True, then=1),
                default=999,
                output_field=IntegerField()
            )
        ).order_by('featured_priority', '-calculated_rating', '-views_count')

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'cars': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj
    }

    return render(request, 'components/car_list_grid.html', context)


def featured_cars_by_tier(request, tier=None):
    """Display featured cars - simplified for binary featured system"""
    # Redirect to general featured cars since we no longer use tiers
    return redirect('core:car_list', featured_only=True)


def featured_cars_list(request):
    """Display all featured cars"""
    # Base queryset for featured cars
    cars = Car.objects.filter(
        is_approved=True,
        is_featured=True
    ).select_related('brand', 'model', 'vendor')

    # Order by rating and views
    cars = cars.order_by('-calculated_rating', '-views_count')

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get featured car statistics
    featured_stats = {
        'total_count': cars.count(),
        'avg_rating': cars.aggregate(avg_rating=Avg('calculated_rating'))['avg_rating'] or 0,
        'avg_price': cars.aggregate(avg_price=Avg('price'))['avg_price'] or 0,
        'certified_count': cars.filter(is_certified=True).count(),
        'hot_deals_count': cars.filter(is_hot_deal=True).count(),
    }

    context = {
        'cars': page_obj,
        'featured_stats': featured_stats,
        'page_title': 'Featured Cars',
        'meta_description': 'Browse all featured cars with premium placement'
    }

    return render(request, 'core/featured_cars.html', context)


def top_rated_vehicles(request):
    """Display top-rated vehicles"""
    min_rating = float(request.GET.get('min_rating', 4.0))
    category = request.GET.get('category', '')

    # Base queryset for top-rated cars
    cars = Car.objects.filter(
        is_approved=True,
        calculated_rating__gte=min_rating
    ).select_related('brand', 'model', 'vendor')

    # Filter by category if provided
    if category:
        cars = cars.filter(body_type=category)

    # Order by rating and views
    cars = cars.order_by('-calculated_rating', '-views_count')

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get rating statistics
    rating_stats = {
        'total_rated_cars': Car.objects.filter(calculated_rating__gt=0).count(),
        'avg_rating': Car.objects.filter(calculated_rating__gt=0).aggregate(
            avg_rating=Avg('calculated_rating')
        )['avg_rating'] or 0,
        'five_star_count': Car.objects.filter(calculated_rating=5.0).count(),
        'four_plus_count': Car.objects.filter(calculated_rating__gte=4.0).count(),
    }

    # Get available categories
    categories = Car.objects.filter(
        is_approved=True,
        calculated_rating__gte=min_rating
    ).values_list('body_type', flat=True).distinct()

    context = {
        'cars': page_obj,
        'min_rating': min_rating,
        'current_category': category,
        'categories': categories,
        'rating_stats': rating_stats,
        'page_title': f'Top Rated {category} Vehicles' if category else 'Top Rated Vehicles',
        'meta_description': f'Discover the highest rated {category.lower()} vehicles' if category else 'Browse our top-rated vehicles with excellent customer reviews'
    }

    return render(request, 'core/top_rated_vehicles.html', context)


def smart_recommendations(request):
    """Display smart car recommendations based on user behavior"""
    recommendations = []

    if request.user.is_authenticated:
        # Get user's viewing history and preferences
        from .models import CarRating

        # Get cars user has rated highly
        user_ratings = CarRating.objects.filter(
            customer=request.user,
            rating__gte=4.0
        ).select_related('car')

        # Get brands and models user likes
        liked_brands = set()
        liked_models = set()
        price_range = []

        for rating in user_ratings:
            liked_brands.add(rating.car.brand_id)
            liked_models.add(rating.car.model_id)
            price_range.append(rating.car.price)

        if price_range:
            avg_price = sum(price_range) / len(price_range)
            min_price = avg_price * 0.7
            max_price = avg_price * 1.3
        else:
            min_price = max_price = None

        # Build recommendation queryset
        recommendation_query = Car.objects.filter(
            is_approved=True,
            status__in=['available', 'featured']
        ).exclude(
            id__in=user_ratings.values_list('car_id', flat=True)
        ).select_related('brand', 'model', 'vendor')

        # Apply preferences
        if liked_brands:
            brand_recommendations = recommendation_query.filter(
                brand_id__in=liked_brands
            )
            recommendations.extend(list(brand_recommendations[:5]))

        if liked_models:
            model_recommendations = recommendation_query.filter(
                model_id__in=liked_models
            ).exclude(id__in=[car.id for car in recommendations])
            recommendations.extend(list(model_recommendations[:3]))

        if min_price and max_price:
            price_recommendations = recommendation_query.filter(
                price__gte=min_price,
                price__lte=max_price
            ).exclude(id__in=[car.id for car in recommendations])
            recommendations.extend(list(price_recommendations[:4]))

    # Fill with popular cars if not enough recommendations
    if len(recommendations) < 12:
        popular_cars = Car.objects.filter(
            is_approved=True,
            status__in=['available', 'featured']
        ).exclude(
            id__in=[car.id for car in recommendations]
        ).order_by('-views_count', '-calculated_rating')[:12 - len(recommendations)]

        recommendations.extend(list(popular_cars))

    # Get trending cars (high recent activity)
    from datetime import timedelta
    recent_date = timezone.now() - timedelta(days=7)
    trending_cars = Car.objects.filter(
        is_approved=True,
        created_at__gte=recent_date
    ).order_by('-views_count')[:6]

    context = {
        'recommendations': recommendations[:12],
        'trending_cars': trending_cars,
        'user_authenticated': request.user.is_authenticated,
        'page_title': 'Smart Recommendations',
        'meta_description': 'Discover cars tailored to your preferences with our smart recommendation system'
    }

    return render(request, 'core/smart_recommendations.html', context)


def hot_deals_list(request):
    """Display all active hot deals"""
    from .models import HotDeal

    # Get active hot deals
    hot_deals = HotDeal.objects.filter(
        is_active=True,
        car__is_approved=True
    ).select_related('car', 'car__brand', 'car__model').order_by('-created_at')

    # Filter by search
    search = request.GET.get('search')
    if search:
        hot_deals = hot_deals.filter(
            Q(title__icontains=search) |
            Q(car__title__icontains=search) |
            Q(car__brand__name__icontains=search)
        )

    # Filter by discount type
    discount_type = request.GET.get('discount_type')
    if discount_type:
        hot_deals = hot_deals.filter(discount_type=discount_type)

    context = {
        'hot_deals': hot_deals,
        'search': search,
        'discount_type': discount_type,
    }

    return render(request, 'core/hot_deals.html', context)


def hot_deal_detail(request, deal_id):
    """Display hot deal detail"""
    from .models import HotDeal

    hot_deal = get_object_or_404(
        HotDeal,
        id=deal_id,
        is_active=True,
        car__is_approved=True
    )

    # Check if deal is still active
    if not hot_deal.is_currently_active():
        messages.warning(request, 'This hot deal has expired.')
        return redirect('core:hot_deals_list')

    # Increment views count
    hot_deal.views_count += 1
    hot_deal.save(update_fields=['views_count'])

    # Related hot deals
    related_deals = HotDeal.objects.filter(
        is_active=True,
        car__is_approved=True,
        car__brand=hot_deal.car.brand
    ).exclude(id=hot_deal.id)[:3]

    context = {
        'hot_deal': hot_deal,
        'car': hot_deal.car,
        'related_deals': related_deals,
    }

    return render(request, 'core/hot_deal_detail.html', context)


@login_required
def create_hot_deal(request):
    """Create a new hot deal (vendor only)"""
    if request.user.role != 'vendor':
        messages.error(request, 'Only vendors can create hot deals.')
        return redirect('core:homepage')

    try:
        vendor = request.user.vendor
    except:
        messages.error(request, 'Vendor profile not found.')
        return redirect('core:homepage')

    if request.method == 'POST':
        from .models import HotDeal

        car_id = request.POST.get('car_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            car = get_object_or_404(Car, id=car_id, vendor=vendor, is_approved=True)

            # Check if car already has an active hot deal
            if HotDeal.objects.filter(car=car, is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This car already has an active hot deal.'
                })

            # Create hot deal
            hot_deal = HotDeal.objects.create(
                car=car,
                title=title,
                description=description,
                discount_type=discount_type,
                discount_value=float(discount_value),
                original_price=car.price,
                start_date=start_date,
                end_date=end_date,
                is_active=False,  # Will be activated by management command
                auto_activate=True
            )

            return JsonResponse({
                'success': True,
                'message': 'Hot deal created successfully!',
                'deal_id': hot_deal.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating hot deal: {str(e)}'
            })

    # Get vendor's cars for the form
    vendor_cars = Car.objects.filter(
        vendor=vendor,
        is_approved=True,
        status__in=['available', 'featured']
    ).exclude(
        id__in=HotDeal.objects.filter(is_active=True).values_list('car_id', flat=True)
    )

    context = {
        'vendor_cars': vendor_cars,
    }

    return render(request, 'core/create_hot_deal.html', context)


class SparePartListView(ListView):
    """Spare parts listing"""
    model = SparePart
    template_name = 'core/spare_parts.html'
    context_object_name = 'spare_parts'
    paginate_by = 12

    def get_queryset(self):
        queryset = SparePart.objects.filter(is_available=True)

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__icontains=search) |
                Q(part_number__icontains=search)
            )

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_new__id=category)

        # Brand compatibility filter
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(compatible_brands__id=brand)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use the new SparePartCategory model instead of the old category field
        from .models import SparePartCategory
        context['categories'] = SparePartCategory.objects.filter(is_active=True).order_by('name')
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')

        # Add price range for filters
        price_range = SparePart.objects.filter(is_available=True).aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price')
        )
        context['price_range'] = price_range

        # Add condition choices
        context['condition_choices'] = SparePart.CONDITION_CHOICES

        # Get featured categories with counts
        from django.db.models import Count
        from .models import SparePartCategory
        context['featured_categories'] = SparePartCategory.objects.filter(
            is_active=True,
            parts__is_available=True
        ).annotate(
            parts_count=Count('parts', distinct=True)
        ).order_by('-parts_count')[:6]

        # Get statistics for hero section
        context['total_parts_count'] = SparePart.objects.filter(is_available=True).count()
        context['vendors_count'] = Vendor.objects.filter(is_approved=True).count()

        # Get system settings for hero section
        from .models import SystemSetting
        try:
            context['support_hours'] = SystemSetting.objects.get(key='support_hours', is_active=True).value
        except SystemSetting.DoesNotExist:
            context['support_hours'] = '24/7'

        try:
            context['genuine_percentage'] = SystemSetting.objects.get(key='genuine_percentage', is_active=True).value
        except SystemSetting.DoesNotExist:
            context['genuine_percentage'] = '100%'

        return context


class SparePartDetailView(DetailView):
    """Spare part detail page"""
    model = SparePart
    template_name = 'core/spare_part_detail.html'
    context_object_name = 'spare_part'

    def get_queryset(self):
        return SparePart.objects.filter(is_available=True).select_related(
            'vendor', 'supplier', 'category_new'
        ).prefetch_related('compatible_brands', 'compatible_models', 'images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spare_part = self.get_object()

        # Related parts (same category, different part)
        context['related_parts'] = SparePart.objects.filter(
            category=spare_part.category,
            is_available=True
        ).exclude(id=spare_part.id).select_related('vendor')[:6]

        # Check if user has this item in cart
        if self.request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=self.request.user)
                context['in_cart'] = cart.items.filter(spare_part=spare_part).exists()
                cart_item = cart.items.filter(spare_part=spare_part).first()
                context['cart_quantity'] = cart_item.quantity if cart_item else 0
            except Cart.DoesNotExist:
                context['in_cart'] = False
                context['cart_quantity'] = 0
        else:
            context['in_cart'] = False
            context['cart_quantity'] = 0

        return context


def spare_parts_search(request):
    """HTMX endpoint for dynamic spare parts search"""
    if request.method == 'GET':
        queryset = SparePart.objects.filter(is_available=True)

        # Search filter
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(category__icontains=search) |
                Q(part_number__icontains=search) |
                Q(description__icontains=search)
            )

        # Category filter
        category = request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Brand compatibility filter
        brand = request.GET.get('brand')
        if brand:
            queryset = queryset.filter(compatible_brands__id=brand)

        # Price range filter
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Condition filter
        condition = request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)

        # Sort options
        sort_by = request.GET.get('sort', '-created_at')
        valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name', '-name']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(queryset, 12)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'spare_parts': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
        }

        return render(request, 'core/partials/spare_parts_grid.html', context)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def spare_parts_autocomplete(request):
    """HTMX endpoint for search autocomplete"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        if len(query) >= 2:
            # Get matching part names and categories
            parts = SparePart.objects.filter(
                Q(name__icontains=query) |
                Q(category__icontains=query) |
                Q(part_number__icontains=query),
                is_available=True
            ).values('name', 'category', 'part_number').distinct()[:10]

            suggestions = []
            for part in parts:
                suggestions.append({
                    'name': part['name'],
                    'category': part['category'],
                    'part_number': part['part_number']
                })

            return render(request, 'core/partials/search_suggestions.html', {
                'suggestions': suggestions,
                'query': query
            })

    return JsonResponse({'suggestions': []})


@login_required
def add_to_cart(request):
    """Add spare part to cart (HTMX endpoint)"""
    if request.method == 'POST':
        part_id = request.POST.get('part_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            spare_part = SparePart.objects.get(id=part_id, is_available=True)

            # Check stock availability
            if spare_part.available_quantity < quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {spare_part.available_quantity} items available in stock'
                })

            # Get or create cart
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Get or create cart item
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                spare_part=spare_part,
                defaults={
                    'quantity': quantity,
                    'price': spare_part.discount_price or spare_part.price
                }
            )

            if not item_created:
                # Update quantity if item already exists
                new_quantity = cart_item.quantity + quantity
                if spare_part.available_quantity < new_quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Cannot add {quantity} more. Only {spare_part.available_quantity - cart_item.quantity} more available'
                    })
                cart_item.quantity = new_quantity
                cart_item.save()

            return JsonResponse({
                'success': True,
                'message': f'{spare_part.name} added to cart',
                'cart_total_items': cart.total_items,
                'cart_total_amount': float(cart.total_amount)
            })

        except SparePart.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Spare part not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while adding to cart'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def cart_view(request):
    """Display shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('spare_part', 'spare_part__vendor').all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'shipping_cost': 500,  # Fixed shipping cost for now
    }
    return render(request, 'core/cart.html', context)


@login_required
def update_cart_item(request):
    """Update cart item quantity (HTMX endpoint)"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            if quantity <= 0:
                cart_item.delete()
                message = 'Item removed from cart'
            else:
                # Check stock availability
                if cart_item.spare_part.available_quantity < quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Only {cart_item.spare_part.available_quantity} items available'
                    })

                cart_item.quantity = quantity
                cart_item.save()
                message = 'Cart updated'

            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total_items': cart.total_items,
                'cart_total_amount': float(cart.total_amount),
                'item_total': float(cart_item.total_price) if quantity > 0 else 0
            })

        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cart item not found'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def remove_from_cart(request):
    """Remove item from cart (HTMX endpoint)"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart = cart_item.cart
            cart_item.delete()

            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_total_items': cart.total_items,
                'cart_total_amount': float(cart.total_amount)
            })

        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cart item not found'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def checkout_view(request):
    """Display checkout page"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('spare_part', 'spare_part__vendor').all()

    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('core:cart')

    shipping_cost = 500  # Fixed shipping cost
    total_amount = cart.total_amount + shipping_cost

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount,
    }
    return render(request, 'core/checkout.html', context)


@login_required
def process_checkout(request):
    """Process checkout and create order"""
    if request.method == 'POST':
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('spare_part', 'spare_part__vendor').all()

        if not cart_items:
            return JsonResponse({
                'success': False,
                'message': 'Your cart is empty'
            })

        # Get form data
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email')
        customer_phone = request.POST.get('customer_phone')
        shipping_address = request.POST.get('shipping_address')
        shipping_city = request.POST.get('shipping_city')
        shipping_postal_code = request.POST.get('shipping_postal_code', '')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes', '')

        # Validate required fields
        if not all([customer_name, customer_email, customer_phone, shipping_address, shipping_city]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields'
            })

        try:
            # Check stock availability for all items
            for item in cart_items:
                if item.spare_part.available_quantity < item.quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Insufficient stock for {item.spare_part.name}. Only {item.spare_part.available_quantity} available.'
                    })

            # Create order
            import uuid
            order_number = f"ORD-{timezone.now().year}-{str(uuid.uuid4())[:8].upper()}"

            shipping_cost = 500
            subtotal = cart.total_amount
            total_amount = subtotal + shipping_cost

            order = Order.objects.create(
                order_number=order_number,
                customer=request.user,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_postal_code=shipping_postal_code,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                notes=notes
            )

            # Create order items and reserve stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    spare_part=item.spare_part,
                    vendor=item.spare_part.vendor,  # Can be None if spare part has no vendor
                    part_name=item.spare_part.name,
                    part_sku=item.spare_part.sku,
                    part_description=item.spare_part.description,
                    quantity=item.quantity,
                    unit_price=item.price,
                    total_price=item.total_price
                )

                # Reserve stock
                item.spare_part.reserved_quantity += item.quantity
                item.spare_part.save()

                # Create stock movement record
                StockMovement.objects.create(
                    spare_part=item.spare_part,
                    movement_type='out',
                    reason='sale',
                    quantity=-item.quantity,
                    quantity_before=item.spare_part.stock_quantity + item.quantity,
                    quantity_after=item.spare_part.stock_quantity,
                    reference_number=order.order_number,
                    created_by=request.user
                )

            # Process payment based on method
            if payment_method == 'mpesa':
                # Initiate M-Pesa payment
                payment_result = initiate_mpesa_payment(order, customer_phone, request)
                if payment_result['success']:
                    # Clear cart
                    cart.clear()

                    return JsonResponse({
                        'success': True,
                        'message': 'Order created successfully. Please complete M-Pesa payment.',
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'redirect_url': f'/orders/{order.id}/'
                    })
                else:
                    # Delete order if payment initiation failed
                    order.delete()
                    return JsonResponse({
                        'success': False,
                        'message': f'Payment initiation failed: {payment_result["message"]}'
                    })
            else:
                # For other payment methods, mark as pending
                Payment.objects.create(
                    payment_id=f"PAY-{str(uuid.uuid4())[:8].upper()}",
                    order=order,
                    payment_method=payment_method,
                    amount=total_amount,
                    status='pending'
                )

                # Clear cart
                cart.clear()

                return JsonResponse({
                    'success': True,
                    'message': 'Order created successfully.',
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'redirect_url': f'/orders/{order.id}/'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def initiate_mpesa_payment(order, phone_number, request=None):
    """Initiate M-Pesa payment for an order using enhanced integration"""
    try:
        from .mpesa_integration import MPesaAPI
        import uuid

        # Create payment record first
        payment = Payment.objects.create(
            payment_id=f"MPESA-{str(uuid.uuid4())[:8].upper()}",
            order=order,
            payment_method='mpesa',
            amount=order.total_amount,
            mpesa_phone_number=phone_number,
            status='pending'
        )

        # Initialize M-Pesa API
        mpesa_api = MPesaAPI(request)

        # Initiate STK push
        result = mpesa_api.initiate_stk_push(
            phone_number=phone_number,
            amount=order.total_amount,
            account_reference=f"ORDER-{order.order_number}",
            transaction_desc=f"Payment for Order {order.order_number}"
        )

        if result['success']:
            # Update payment record with checkout request ID
            payment.mpesa_checkout_request_id = result.get('checkout_request_id', '')
            payment.status = 'processing'
            payment.save()

            return {
                'success': True,
                'message': result['message'],
                'payment_id': payment.payment_id,
                'checkout_request_id': payment.mpesa_checkout_request_id
            }
        else:
            # Update payment status to failed
            payment.status = 'failed'
            payment.failure_reason = result['message']
            payment.save()

            return {
                'success': False,
                'message': result['message']
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to initiate M-Pesa payment: {str(e)}'
        }


@login_required
def order_detail_view(request, order_id):
    """Display order details"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        order_items = order.items.select_related('spare_part', 'vendor').all()
        payments = order.payments.all()

        context = {
            'order': order,
            'order_items': order_items,
            'payments': payments,
        }
        return render(request, 'core/order_detail.html', context)

    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('core:orders')


@login_required
def orders_list_view(request):
    """Display user's orders"""
    orders = Order.objects.filter(customer=request.user).prefetch_related('items', 'payments').order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'core/orders.html', context)


@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, customer=request.user)

            if not order.can_be_cancelled:
                return JsonResponse({
                    'success': False,
                    'message': 'This order cannot be cancelled'
                })

            # Release reserved stock
            for item in order.items.all():
                item.spare_part.reserved_quantity -= item.quantity
                item.spare_part.save()

                # Create stock movement record
                StockMovement.objects.create(
                    spare_part=item.spare_part,
                    movement_type='in',
                    reason='return',
                    quantity=item.quantity,
                    quantity_before=item.spare_part.stock_quantity - item.quantity,
                    quantity_after=item.spare_part.stock_quantity,
                    reference_number=f"CANCEL-{order.order_number}",
                    created_by=request.user
                )

            # Update order status
            order.status = 'cancelled'
            order.save()

            # Update payment status if exists
            for payment in order.payments.all():
                if payment.status in ['pending', 'processing']:
                    payment.status = 'cancelled'
                    payment.save()

            return JsonResponse({
                'success': True,
                'message': 'Order cancelled successfully'
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def mpesa_callback(request):
    """Handle M-Pesa payment callback"""
    if request.method == 'POST':
        try:
            import json
            callback_data = json.loads(request.body)

            # Extract callback data
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            result_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

            if checkout_request_id:
                try:
                    payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)

                    if result_code == 0:  # Success
                        # Extract transaction details
                        callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])

                        for item in callback_metadata:
                            if item.get('Name') == 'MpesaReceiptNumber':
                                payment.mpesa_receipt_number = item.get('Value')
                            elif item.get('Name') == 'TransactionDate':
                                payment.mpesa_transaction_id = item.get('Value')

                        # Update payment status
                        payment.status = 'completed'
                        payment.completed_at = timezone.now()
                        payment.gateway_response = callback_data
                        payment.save()

                        # Update order status
                        if payment.order:
                            # Spare parts order
                            order = payment.order
                            order.payment_status = 'completed'
                            order.status = 'paid'
                            order.save()
                            # Generate invoice
                            generate_invoice(order)
                        elif payment.import_order:
                            # Import order
                            import_order = payment.import_order
                            import_order.payment_status = 'paid'
                            import_order.save()

                        # Send confirmation email (placeholder)
                        # send_order_confirmation_email(order)

                    else:  # Failed
                        payment.status = 'failed'
                        payment.failure_reason = result_desc
                        payment.gateway_response = callback_data
                        payment.save()

                        # Update order status
                        order = payment.order
                        order.payment_status = 'failed'
                        order.save()

                        # Release reserved stock
                        for item in order.items.all():
                            item.spare_part.reserved_quantity -= item.quantity
                            item.spare_part.save()

                except Payment.DoesNotExist:
                    pass  # Payment not found, ignore

            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': f'Error: {str(e)}'})

    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'})


@csrf_exempt
def mpesa_timeout(request):
    """Handle M-Pesa payment timeout callback"""
    if request.method == 'POST':
        try:
            import json
            from django.utils import timezone

            timeout_data = json.loads(request.body)

            # Log timeout data for debugging
            logger.info(f"M-Pesa timeout callback received: {timeout_data}")

            # Extract timeout information
            checkout_request_id = timeout_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            result_desc = timeout_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc', 'Payment timeout')

            if checkout_request_id:
                try:
                    payment = Payment.objects.get(mpesa_checkout_request_id=checkout_request_id)

                    # Update payment status to failed due to timeout
                    payment.status = 'failed'
                    payment.failure_reason = f"Payment timeout: {result_desc}"
                    payment.gateway_response = timeout_data
                    payment.save()

                    # Update order status
                    if payment.order:
                        # Spare parts order
                        order = payment.order
                        order.payment_status = 'failed'
                        order.save()

                        # Release reserved stock
                        for item in order.items.all():
                            item.spare_part.reserved_quantity -= item.quantity
                            item.spare_part.save()
                    elif payment.import_order:
                        # Import order
                        import_order = payment.import_order
                        import_order.payment_status = 'failed'
                        import_order.save()

                    logger.warning(f"Payment timeout processed: {payment.payment_id}")

                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for timeout CheckoutRequestID: {checkout_request_id}")

            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Timeout processed'})

        except Exception as e:
            logger.error(f"Error processing M-Pesa timeout: {str(e)}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': f'Error: {str(e)}'})

    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'})


def initiate_import_mpesa_payment(import_order, phone_number, request=None):
    """Initiate M-Pesa payment for an import order"""
    try:
        from .mpesa_integration import MPesaAPI
        import uuid

        # Create payment record first
        payment = Payment.objects.create(
            payment_id=f"IMPORT-MPESA-{str(uuid.uuid4())[:8].upper()}",
            import_order=import_order,
            payment_method='mpesa',
            amount=import_order.total_cost,
            mpesa_phone_number=phone_number,
            status='pending'
        )

        # Initialize M-Pesa API
        mpesa_api = MPesaAPI(request)

        # Initiate STK push
        result = mpesa_api.initiate_stk_push(
            phone_number=phone_number,
            amount=import_order.total_cost,
            account_reference=f"IMPORT-{import_order.order_number}",
            transaction_desc=f"Import Fee - {import_order.brand} {import_order.model}"
        )

        if result['success']:
            # Update payment record with checkout request ID
            payment.mpesa_checkout_request_id = result.get('checkout_request_id', '')
            payment.status = 'processing'
            payment.save()

            return {
                'success': True,
                'message': result['message'],
                'payment_id': payment.payment_id,
                'checkout_request_id': payment.mpesa_checkout_request_id
            }
        else:
            # Update payment status to failed
            payment.status = 'failed'
            payment.failure_reason = result['message']
            payment.save()

            return {
                'success': False,
                'message': result['message']
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to initiate M-Pesa payment: {str(e)}'
        }


def generate_invoice(order):
    """Generate invoice for completed order"""
    try:
        if hasattr(order, 'invoice'):
            return order.invoice  # Invoice already exists

        import uuid
        invoice_number = f"INV-{timezone.now().year}-{str(uuid.uuid4())[:8].upper()}"

        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            order=order,
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            notes="Thank you for your business!",
            terms_conditions="Payment due within 30 days of invoice date."
        )

        return invoice

    except Exception as e:
        # Log error but don't fail the payment process
        print(f"Error generating invoice: {str(e)}")
        return None


@login_required
def create_inquiry(request):
    """Create inquiry (HTMX endpoint)"""
    if request.method == 'POST':
        try:
            # Handle inquiry creation
            inquiry_type = request.POST.get('inquiry_type')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            inquiry = Inquiry.objects.create(
                customer=request.user,
                inquiry_type=inquiry_type,
                subject=subject,
                message=message,
                customer_phone=request.POST.get('phone', ''),
                customer_email=request.POST.get('email', request.user.email)
            )

            # Add related objects if specified
            car_id = request.POST.get('car_id')
            if car_id:
                inquiry.car_id = car_id
                inquiry.save()

            spare_part_id = request.POST.get('spare_part_id')
            if spare_part_id:
                inquiry.spare_part_id = spare_part_id
                inquiry.save()

            if request.headers.get('HX-Request'):
                return render(request, 'core/partials/inquiry_success.html', {
                    'message': 'Inquiry submitted successfully! We will get back to you soon.'
                })
            else:
                return JsonResponse({'success': True, 'message': 'Inquiry submitted successfully!'})

        except Exception as e:
            if request.headers.get('HX-Request'):
                return render(request, 'core/partials/inquiry_error.html', {
                    'message': 'There was an error submitting your inquiry. Please try again.'
                })
            else:
                return JsonResponse({'success': False, 'message': 'Error submitting inquiry'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


class BlogListView(ListView):
    """Enhanced resources listing page with filtering and search"""
    model = BlogPost
    template_name = 'core/blog.html'
    context_object_name = 'posts'
    paginate_by = 20  # Updated to match project preferences

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_published=True).select_related('author', 'category').prefetch_related('tags')

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()

        # Content type filtering
        content_type = self.request.GET.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        # Category filtering
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Tag filtering
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        return queryset.order_by('-is_featured', '-published_at', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get featured posts separately
        featured_posts = BlogPost.objects.filter(
            is_published=True,
            is_featured=True
        ).select_related('author', 'category').prefetch_related('tags')[:2]

        context['featured_posts'] = featured_posts

        # Add filter context
        context['search_query'] = self.request.GET.get('search', '')
        context['current_content_type'] = self.request.GET.get('content_type', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_tag'] = self.request.GET.get('tag', '')

        # Add content type choices for filters
        context['content_types'] = BlogPost.CONTENT_TYPE_CHOICES

        # Add categories and tags for filters
        from .models import ContentCategory, ContentTag
        context['categories'] = ContentCategory.objects.filter(is_active=True).order_by('sort_order', 'name')
        context['popular_tags'] = ContentTag.objects.filter(is_active=True).order_by('name')[:10]

        return context


class BlogDetailView(DetailView):
    """Enhanced blog post detail page"""
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).select_related('author', 'category').prefetch_related('tags')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get related posts
        related_posts = BlogPost.objects.filter(
            is_published=True,
            category=self.object.category
        ).exclude(id=self.object.id).select_related('author', 'category')[:3]

        context['related_posts'] = related_posts

        # Get posts by same author
        author_posts = BlogPost.objects.filter(
            is_published=True,
            author=self.object.author
        ).exclude(id=self.object.id).select_related('author', 'category')[:3]

        context['author_posts'] = author_posts

        return context


# HTMX Views for Resources

def resources_live_search(request):
    """HTMX endpoint for live search in resources"""
    search_query = request.GET.get('search', '')
    content_type = request.GET.get('content_type', '')
    category = request.GET.get('category', '')
    tag = request.GET.get('tag', '')

    queryset = BlogPost.objects.filter(is_published=True).select_related('author', 'category').prefetch_related('tags')

    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()

    if content_type:
        queryset = queryset.filter(content_type=content_type)

    if category:
        queryset = queryset.filter(category__slug=category)

    if tag:
        queryset = queryset.filter(tags__slug=tag)

    # Get featured posts first (before slicing)
    featured_posts = queryset.filter(is_featured=True).order_by('-published_at')[:2]

    # Get all posts
    posts = queryset.order_by('-is_featured', '-published_at')[:20]

    context = {
        'posts': posts,
        'featured_posts': featured_posts,
        'search_query': search_query,
        'current_content_type': content_type,
        'current_category': category,
        'current_tag': tag,
    }

    return render(request, 'core/htmx/resources_content_new.html', context)


def resources_filter_by_category(request, category_slug):
    """HTMX endpoint for filtering resources by category"""
    from .models import ContentCategory

    try:
        category = ContentCategory.objects.get(slug=category_slug, is_active=True)
        posts = BlogPost.objects.filter(
            is_published=True,
            category=category
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')[:20]

        context = {
            'posts': posts,
            'featured_posts': posts.filter(is_featured=True)[:2],
            'current_category': category_slug,
            'category_name': category.name,
        }

        return render(request, 'core/htmx/resources_content_new.html', context)

    except ContentCategory.DoesNotExist:
        return render(request, 'core/htmx/resources_content_new.html', {'posts': []})


def resources_filter_by_tag(request, tag_slug):
    """HTMX endpoint for filtering resources by tag"""
    from .models import ContentTag

    try:
        tag = ContentTag.objects.get(slug=tag_slug, is_active=True)
        posts = BlogPost.objects.filter(
            is_published=True,
            tags=tag
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')[:20]

        context = {
            'posts': posts,
            'featured_posts': posts.filter(is_featured=True)[:2],
            'current_tag': tag_slug,
            'tag_name': tag.name,
        }

        return render(request, 'core/htmx/resources_content_new.html', context)

    except ContentTag.DoesNotExist:
        return render(request, 'core/htmx/resources_content_new.html', {'posts': []})


def content_like_toggle(request, post_id):
    """HTMX endpoint for toggling content likes"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'})

    try:
        post = get_object_or_404(BlogPost, id=post_id, is_published=True)
        from .models import ContentLike

        like, created = ContentLike.objects.get_or_create(
            post=post,
            user=request.user
        )

        if not created:
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            liked = False
        else:
            post.likes_count += 1
            liked = True

        post.save(update_fields=['likes_count'])

        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': post.likes_count
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error processing request'})


def content_bookmark_toggle(request, post_id):
    """HTMX endpoint for toggling content bookmarks"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'})

    try:
        post = get_object_or_404(BlogPost, id=post_id, is_published=True)
        from .models import ContentBookmark

        bookmark, created = ContentBookmark.objects.get_or_create(
            post=post,
            user=request.user
        )

        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True

        return JsonResponse({
            'success': True,
            'bookmarked': bookmarked,
            'message': 'Bookmarked!' if bookmarked else 'Bookmark removed!'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error processing request'})


def about_us(request):
    """About us page"""
    context = {
        'testimonials': Testimonial.objects.filter(is_approved=True)[:6],
        'team_members': [],  # Add team members if needed
    }
    return render(request, 'core/about_us.html', context)


def dealer_list(request):
    """Public dealer listing page"""
    vendors = Vendor.objects.filter(
        is_approved=True,
        user__is_active=True
    ).select_related('user').prefetch_related('cars').order_by('-created_at')

    # Add statistics for each vendor
    for vendor in vendors:
        vendor.total_listings = vendor.cars.filter(is_approved=True, status='available').count()
        vendor.total_views = sum(car.views_count for car in vendor.cars.all())

    context = {
        'vendors': vendors,
        'total_dealers': vendors.count(),
    }
    return render(request, 'core/dealer_list.html', context)


def dealer_profile(request, vendor_id):
    """Public dealer profile page"""
    vendor = get_object_or_404(
        Vendor.objects.select_related('user').prefetch_related('cars'),
        id=vendor_id,
        is_approved=True,
        user__is_active=True
    )

    # Get vendor's cars
    vendor_cars = Car.objects.filter(
        vendor=vendor,
        is_approved=True,
        status='available'
    ).order_by('-created_at')

    # Calculate statistics
    total_listings = vendor_cars.count()
    total_views = sum(car.views_count for car in vendor_cars)
    featured_cars = vendor_cars.filter(is_featured=True)
    hot_deals = vendor_cars.filter(is_hot_deal=True)

    # Get recent cars (last 6)
    recent_cars = vendor_cars[:6]

    # Track profile view
    try:
        from .utils.analytics_utils import track_profile_view
        track_profile_view(vendor.user, request.user if request.user.is_authenticated else None)
    except:
        pass

    # Increment profile views
    vendor.profile_views = (vendor.profile_views or 0) + 1
    vendor.save(update_fields=['profile_views'])

    context = {
        'vendor': vendor,
        'vendor_cars': recent_cars,
        'total_listings': total_listings,
        'total_views': total_views,
        'featured_cars': featured_cars,
        'hot_deals': hot_deals,
        'all_cars': vendor_cars,  # For pagination if needed
    }
    return render(request, 'core/dealer_profile.html', context)


def car_compare(request):
    """Car comparison page"""
    # Get car IDs from session or query parameters
    compare_ids = request.session.get('compare_list', [])

    # Also check for query parameters (for direct links)
    if 'cars' in request.GET:
        try:
            query_ids = [int(id) for id in request.GET.get('cars', '').split(',') if id.strip()]
            compare_ids.extend(query_ids)
            compare_ids = list(set(compare_ids))  # Remove duplicates
        except ValueError:
            pass

    # Limit to 3 cars maximum
    compare_ids = compare_ids[:3]

    # Get car objects
    cars = Car.objects.filter(
        id__in=compare_ids,
        is_approved=True
    ).select_related('brand', 'model', 'vendor').prefetch_related('images')

    # Ensure cars are in the same order as compare_ids
    cars_dict = {car.id: car for car in cars}
    ordered_cars = [cars_dict[car_id] for car_id in compare_ids if car_id in cars_dict]

    context = {
        'cars': ordered_cars,
        'compare_count': len(ordered_cars),
        'max_compare': 3,
    }
    return render(request, 'core/car_compare.html', context)


@require_http_methods(["POST"])
def add_to_compare(request, car_id):
    """Add car to comparison list via HTMX"""
    try:
        car = get_object_or_404(Car, id=car_id, is_approved=True)
        compare_list = request.session.get('compare_list', [])

        if len(compare_list) >= 3:
            return JsonResponse({
                'success': False,
                'message': 'You can only compare up to 3 cars at a time.',
                'count': len(compare_list)
            })

        if car_id in compare_list:
            return JsonResponse({
                'success': False,
                'message': 'Car is already in comparison list.',
                'count': len(compare_list)
            })

        compare_list.append(car_id)
        request.session['compare_list'] = compare_list

        return JsonResponse({
            'success': True,
            'message': f'{car.title} added to comparison!',
            'count': len(compare_list),
            'car_title': car.title
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding car to comparison.',
            'count': len(request.session.get('compare_list', []))
        })


@require_http_methods(["POST"])
def remove_from_compare(request, car_id):
    """Remove car from comparison list via HTMX"""
    try:
        compare_list = request.session.get('compare_list', [])

        if car_id in compare_list:
            compare_list.remove(car_id)
            request.session['compare_list'] = compare_list

            car = get_object_or_404(Car, id=car_id)

            return JsonResponse({
                'success': True,
                'message': f'{car.title} removed from comparison.',
                'count': len(compare_list)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Car not found in comparison list.',
                'count': len(compare_list)
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error removing car from comparison.',
            'count': len(request.session.get('compare_list', []))
        })


@require_http_methods(["POST"])
def clear_compare(request):
    """Clear all cars from comparison list"""
    request.session['compare_list'] = []

    return JsonResponse({
        'success': True,
        'message': 'Comparison list cleared.',
        'count': 0
    })


def car_calculator(request):
    """Car financing calculator page"""
    # Get car details if car_id is provided
    car = None
    car_id = request.GET.get('car_id')
    if car_id:
        try:
            car = Car.objects.get(id=car_id, is_approved=True)
        except Car.DoesNotExist:
            pass

    context = {
        'car': car,
        'default_price': car.price if car else 0,
        'default_down_payment': 0.2,  # 20% default
        'default_loan_term': 60,  # 5 years default
        'default_interest_rate': 12.5,  # 12.5% default for Kenya
    }
    return render(request, 'core/car_calculator.html', context)


@require_http_methods(["POST"])
def calculate_loan(request):
    """Calculate loan payments via HTMX"""
    try:
        # Get form data
        car_price = float(request.POST.get('car_price', 0))
        down_payment_percent = float(request.POST.get('down_payment_percent', 20))
        loan_term_months = int(request.POST.get('loan_term_months', 60))
        interest_rate = float(request.POST.get('interest_rate', 12.5))
        insurance_monthly = float(request.POST.get('insurance_monthly', 0))
        other_fees_monthly = float(request.POST.get('other_fees_monthly', 0))

        # Validate inputs
        if car_price <= 0:
            return JsonResponse({'error': 'Car price must be greater than 0'})

        if down_payment_percent < 0 or down_payment_percent > 100:
            return JsonResponse({'error': 'Down payment must be between 0% and 100%'})

        if loan_term_months <= 0:
            return JsonResponse({'error': 'Loan term must be greater than 0'})

        if interest_rate < 0:
            return JsonResponse({'error': 'Interest rate cannot be negative'})

        # Calculate loan details
        down_payment_amount = car_price * (down_payment_percent / 100)
        loan_amount = car_price - down_payment_amount

        # Calculate monthly payment using loan formula
        if interest_rate > 0:
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** loan_term_months) / ((1 + monthly_rate) ** loan_term_months - 1)
        else:
            monthly_payment = loan_amount / loan_term_months

        # Calculate totals
        total_loan_payments = monthly_payment * loan_term_months
        total_interest = total_loan_payments - loan_amount
        total_insurance = insurance_monthly * loan_term_months
        total_other_fees = other_fees_monthly * loan_term_months
        total_cost = car_price + total_interest + total_insurance + total_other_fees
        total_monthly_payment = monthly_payment + insurance_monthly + other_fees_monthly

        # Prepare response data
        calculations = {
            'car_price': car_price,
            'down_payment_percent': down_payment_percent,
            'down_payment_amount': down_payment_amount,
            'loan_amount': loan_amount,
            'loan_term_months': loan_term_months,
            'loan_term_years': loan_term_months / 12,
            'interest_rate': interest_rate,
            'monthly_payment': monthly_payment,
            'insurance_monthly': insurance_monthly,
            'other_fees_monthly': other_fees_monthly,
            'total_monthly_payment': total_monthly_payment,
            'total_loan_payments': total_loan_payments,
            'total_interest': total_interest,
            'total_insurance': total_insurance,
            'total_other_fees': total_other_fees,
            'total_cost': total_cost,
            'savings_vs_total': car_price - total_cost,
        }

        return JsonResponse({
            'success': True,
            'calculations': calculations
        })

    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid input values. Please check your entries.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred during calculation.'
        })


def contact_us(request):
    """Contact us page with toast notifications"""
    from .toast_utils import toast_success_response, toast_error_response
    from django.contrib import messages

    if request.method == 'POST':
        try:
            # Handle contact form submission
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            phone = request.POST.get('phone', '')

            # Create a general inquiry
            if request.user.is_authenticated:
                customer = request.user
            else:
                # For anonymous users, show error toast
                error_msg = 'Please login to submit inquiries.'
                if request.headers.get('HX-Request'):
                    return toast_error_response(error_msg)
                else:
                    messages.error(request, error_msg)
                    return render(request, 'core/contact_us.html', {'form': ContactForm()})

            Inquiry.objects.create(
                customer=customer,
                inquiry_type='general',
                subject=subject,
                message=f"From: {first_name} {last_name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}",
                customer_email=email,
                customer_phone=phone
            )

            success_msg = 'Thank you for your message! We will get back to you within 24 hours.'
            if request.headers.get('HX-Request'):
                return toast_success_response(success_msg)
            else:
                messages.success(request, success_msg)
                return render(request, 'core/contact_us.html', {'form': ContactForm()})

        except Exception as e:
            error_msg = 'There was an error sending your message. Please try again.'
            if request.headers.get('HX-Request'):
                return toast_error_response(error_msg)
            else:
                messages.error(request, error_msg)
                return render(request, 'core/contact_us.html', {'form': ContactForm()})

    context = {'form': ContactForm()}
    return render(request, 'core/contact_us.html', context)


def toast_test(request):
    """Test page for toast notifications"""
    from .toast_utils import toast_success_response, toast_error_response, toast_warning_response, toast_info_response
    from django.contrib import messages

    if request.method == 'POST':
        toast_type = request.POST.get('toast_type', 'info')
        message = request.POST.get('message', 'Test message')

        if request.headers.get('HX-Request'):
            # HTMX request - return JSON response
            if toast_type == 'success':
                return toast_success_response(message)
            elif toast_type == 'error':
                return toast_error_response(message)
            elif toast_type == 'warning':
                return toast_warning_response(message)
            else:
                return toast_info_response(message)
        else:
            # Regular request - use Django messages
            if toast_type == 'success':
                messages.success(request, message)
            elif toast_type == 'error':
                messages.error(request, message)
            elif toast_type == 'warning':
                messages.warning(request, message)
            else:
                messages.info(request, message)

    return render(request, 'core/toast_test.html')


def system_test(request):
    """System test page for activity, audit, and notification systems"""
    return render(request, 'core/system_test.html')


# HTMX Views for Sell Car Form
def htmx_models_by_brand(request):
    """HTMX endpoint to load models by brand"""
    brand_id = request.GET.get('brand')
    models = []

    if brand_id:
        try:
            brand = CarBrand.objects.get(id=brand_id, is_active=True)
            models = CarModel.objects.filter(brand=brand, is_active=True).order_by('name')
        except CarBrand.DoesNotExist:
            pass

    return render(request, 'core/htmx/models_by_brand.html', {
        'models': models
    })


# Car Sales Views
@login_required
def sell_car(request):
    """Sell car form view"""
    # Check if this is a modal request for admin
    is_admin_modal = request.GET.get('modal') == 'true' and request.GET.get('admin') == 'true'

    # Redirect admin users to admin car listings page (except for modal requests)
    if request.user.role == 'admin' and not is_admin_modal:
        messages.info(request, 'As an admin, please use the admin car listings page to manage cars and sell on behalf functionality.')
        return redirect('core:admin_listings')

    if request.method == 'POST':
        form = SellCarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)

            # Handle vendor assignment based on user role
            if request.user.role == 'admin':
                # For admin users, check if a specific vendor is selected or create a default one
                vendor_id = request.POST.get('vendor_id')
                if vendor_id:
                    try:
                        vendor = Vendor.objects.get(id=vendor_id)
                    except Vendor.DoesNotExist:
                        vendor = None

                if not vendor_id or not vendor:
                    # Create or get a default admin vendor profile
                    vendor, created = Vendor.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'company_name': 'Gurumisha Motors Admin',
                            'is_approved': True
                        }
                    )

                car.is_approved = True  # Admin cars are auto-approved
            elif request.user.role == 'vendor':
                try:
                    vendor = request.user.vendor
                except Vendor.DoesNotExist:
                    # Create vendor profile if it doesn't exist
                    vendor = Vendor.objects.create(
                        user=request.user,
                        company_name=f"{request.user.first_name} {request.user.last_name}",
                        is_approved=False
                    )
                car.is_approved = False  # Vendor cars require admin approval
            else:
                # For customers, create a basic vendor profile
                vendor = Vendor.objects.create(
                    user=request.user,
                    company_name=f"{request.user.first_name} {request.user.last_name}",
                    is_approved=False
                )
                # Update user role to vendor
                request.user.role = 'vendor'
                request.user.save()
                car.is_approved = False  # Customer cars require admin approval

            car.vendor = vendor
            car.status = 'available'
            car.save()

            # Handle success message and redirect based on user role
            if request.user.role == 'admin':
                messages.success(request, 'Car listing has been created and approved successfully.')
                # For HTMX modal requests, return JSON response
                if request.headers.get('HX-Request'):
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Car listing created successfully!',
                        'redirect': '/dashboard/admin/listings/'
                    })
                return redirect('core:admin_listings')
            else:
                messages.success(request, 'Your car listing has been submitted for review. We will notify you once it\'s approved.')
                # For HTMX modal requests, return JSON response
                if request.headers.get('HX-Request'):
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Car listing submitted for review!',
                        'redirect': '/dashboard/'
                    })
                return redirect('core:dashboard')
        else:
            # Handle form validation errors
            if request.headers.get('HX-Request'):
                # Return JSON error response for HTMX
                error_details = {}
                for field, errors in form.errors.items():
                    error_details[field] = [str(error) for error in errors]

                return JsonResponse({
                    'status': 'error',
                    'message': 'Please correct the validation errors below.',
                    'errors': error_details
                }, status=400)
    else:
        form = SellCarForm()

    context = {
        'form': form,
        'car_brands': CarBrand.objects.filter(is_active=True).order_by('display_order', 'name'),
        'vehicle_conditions': VehicleCondition.objects.filter(is_active=True).order_by('display_order', 'name'),
    }

    # Check if this is a modal request
    if request.GET.get('modal') == 'true':
        # Check if this is an admin modal request
        if request.GET.get('admin') == 'true':
            context['is_admin_modal'] = True
        return render(request, 'core/modals/car_creation_modal.html', context)

    return render(request, 'core/sell_car.html', context)


# Import Request Views
@login_required
def import_request(request):
    """Car import request form view"""
    if request.method == 'POST':
        form = ImportRequestForm(request.POST)
        if form.is_valid():
            import_req = form.save(commit=False)
            import_req.customer = request.user
            import_req.status = 'pending'
            import_req.save()

            messages.success(request, 'Your import request has been submitted. We will contact you soon with available options.')
            return redirect('core:dashboard')
    else:
        form = ImportRequestForm()

    return render(request, 'core/import_request.html', {'form': form})


def import_listings(request):
    """Import listings page showing available import services"""
    context = {
        'popular_imports': [
            {'country': 'Japan', 'description': 'High-quality, well-maintained vehicles', 'image': 'japan-cars.jpg'},
            {'country': 'Germany', 'description': 'Premium luxury and performance cars', 'image': 'german-cars.jpg'},
            {'country': 'UK', 'description': 'Right-hand drive vehicles', 'image': 'uk-cars.jpg'},
            {'country': 'USA', 'description': 'American muscle and luxury cars', 'image': 'usa-cars.jpg'},
        ],
        'import_process': [
            {'step': 1, 'title': 'Submit Request', 'description': 'Tell us what car you want to import'},
            {'step': 2, 'title': 'Get Quote', 'description': 'We find the best options and provide pricing'},
            {'step': 3, 'title': 'Confirm Order', 'description': 'Approve the car and make payment'},
            {'step': 4, 'title': 'Shipping', 'description': 'We handle all shipping and customs'},
            {'step': 5, 'title': 'Delivery', 'description': 'Your car is delivered to your location'},
        ],
        'recent_imports': ImportRequest.objects.filter(status='completed').order_by('-updated_at')[:6],
    }
    return render(request, 'core/import_listings.html', context)


@login_required
def user_profile(request):
    """User profile edit view"""
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.address = request.POST.get('address', '')
        user.role = request.POST.get('role', user.role)

        try:
            user.save()
            messages.success(request, 'Your profile has been updated successfully!')
        except Exception as e:
            messages.error(request, 'There was an error updating your profile. Please try again.')

        return redirect('core:profile')

    return render(request, 'core/profile.html')


# Error Views
def custom_404_view(request, exception):
    """Custom 404 error page with automotive theme"""
    return render(request, 'core/404.html', status=404)


def test_404_view(request):
    """Test view for 404 page (works in DEBUG mode)"""
    return render(request, 'core/404.html', status=404)


# Import Order Tracking Views
@login_required
def import_order_tracking_dashboard(request):
    """Dashboard view for import order tracking"""
    user_orders = ImportOrder.objects.filter(customer=request.user).order_by('-created_at')

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        user_orders = user_orders.filter(status=status_filter)

    # Search by order number or chassis number
    search_query = request.GET.get('search')
    if search_query:
        user_orders = user_orders.filter(
            Q(order_number__icontains=search_query) |
            Q(chassis_number__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query)
        )

    context = {
        'orders': user_orders,
        'status_choices': ImportOrder.STATUS_CHOICES,
        'current_filter': status_filter,
        'search_query': search_query,
        'total_orders': ImportOrder.objects.filter(customer=request.user).count(),
        'active_orders': ImportOrder.objects.filter(
            customer=request.user
        ).exclude(status__in=['delivered', 'cancelled']).count(),
        'delivered_orders': ImportOrder.objects.filter(
            customer=request.user, status='delivered'
        ).count(),
    }

    return render(request, 'core/import_tracking/dashboard.html', context)


@login_required
def import_order_detail(request, order_number):
    """Detailed view for a specific import order"""
    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    # Get status history
    status_history = order.status_history.all().order_by('-created_at')

    # Get documents
    documents = order.documents.filter(is_customer_visible=True).order_by('-created_at')

    # Calculate stage information
    stages = [
        {
            'number': 1,
            'title': 'Quotation & Confirmation',
            'description': 'Order confirmed and quotation provided',
            'statuses': ['quotation_pending', 'confirmed'],
            'is_current': order.current_stage_number == 1,
            'is_completed': order.current_stage_number > 1,
        },
        {
            'number': 2,
            'title': 'Auction Process',
            'description': 'Bidding and winning at auction',
            'statuses': ['auction_won'],
            'is_current': order.current_stage_number == 2,
            'is_completed': order.current_stage_number > 2,
        },
        {
            'number': 3,
            'title': 'Inspection & Shipping',
            'description': 'Vehicle inspection and shipping preparation',
            'statuses': ['shipped'],
            'is_current': order.current_stage_number == 3,
            'is_completed': order.current_stage_number > 3,
        },
        {
            'number': 4,
            'title': 'In Transit',
            'description': 'Vehicle is being shipped',
            'statuses': ['in_transit'],
            'is_current': order.current_stage_number == 4,
            'is_completed': order.current_stage_number > 4,
        },
        {
            'number': 5,
            'title': 'Arrival',
            'description': 'Vehicle has arrived at port',
            'statuses': ['arrived_docked'],
            'is_current': order.current_stage_number == 5,
            'is_completed': order.current_stage_number > 5,
        },
        {
            'number': 6,
            'title': 'Clearance & Registration',
            'description': 'Customs clearance and vehicle registration',
            'statuses': ['under_clearance', 'registered'],
            'is_current': order.current_stage_number == 6,
            'is_completed': order.current_stage_number > 6,
        },
        {
            'number': 7,
            'title': 'Delivery',
            'description': 'Ready for dispatch and delivery',
            'statuses': ['ready_for_dispatch', 'delivered'],
            'is_current': order.current_stage_number == 7,
            'is_completed': order.status == 'delivered',
        },
    ]

    context = {
        'order': order,
        'status_history': status_history,
        'documents': documents,
        'stages': stages,
        'progress_percentage': order.progress_percentage,
    }

    return render(request, 'core/import_tracking/order_detail.html', context)


@login_required
def chassis_number_search(request):
    """Search for import order by chassis number"""
    chassis_number = request.GET.get('chassis_number', '').strip()

    if not chassis_number:
        messages.error(request, 'Please enter a chassis number to search.')
        return redirect('core:import_order_tracking')

    try:
        order = ImportOrder.objects.get(chassis_number=chassis_number, customer=request.user)
        return redirect('core:import_order_detail', order_number=order.order_number)
    except ImportOrder.DoesNotExist:
        messages.error(request, f'No import order found with chassis number: {chassis_number}')
        return redirect('core:import_order_tracking')


# HTMX Views for Import Order Tracking
from .decorators import htmx_login_required

@htmx_login_required
def import_order_status_update_htmx(request, order_number):
    """HTMX endpoint for real-time status updates"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    context = {
        'order': order,
        'progress_percentage': order.progress_percentage,
    }

    return render(request, 'core/import_tracking/partials/status_update.html', context)


@htmx_login_required
def import_order_timeline_htmx(request, order_number):
    """HTMX endpoint for loading order timeline"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)
    status_history = order.status_history.all().order_by('-created_at')

    context = {
        'order': order,
        'status_history': status_history,
    }

    return render(request, 'core/import_tracking/partials/timeline.html', context)


# GPS Tracking HTMX Views
@login_required
def import_order_location_update_htmx(request, order_number):
    """HTMX endpoint for real-time location updates"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    # Get current location data
    current_location = order.get_current_location()
    tracking_history = order.tracking_history.all().order_by('-recorded_at')[:10]

    # Prepare location data for JSON response
    location_data = {
        'order_number': order.order_number,
        'current_latitude': float(order.current_latitude) if order.current_latitude else None,
        'current_longitude': float(order.current_longitude) if order.current_longitude else None,
        'current_location_name': order.current_location_name or 'Location updating...',
        'last_update': order.last_location_update.isoformat() if order.last_location_update else None,
        'status': order.status,
        'status_display': order.get_status_display(),
        'progress_percentage': order.progress_percentage,
        'coordinates_string': order.current_coordinates_string,
        'google_maps_url': order.google_maps_url,
        'tracking_enabled': order.has_tracking_enabled(),
    }

    # Add recent tracking history
    location_data['recent_history'] = []
    for entry in tracking_history:
        location_data['recent_history'].append({
            'latitude': float(entry.latitude),
            'longitude': float(entry.longitude),
            'recorded_at': entry.recorded_at.isoformat(),
            'tracking_source': entry.tracking_source,
            'notes': entry.notes,
        })

    return JsonResponse(location_data)


@login_required
def import_order_route_data_htmx(request, order_number):
    """HTMX endpoint for loading route and waypoint data"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    route_data = {
        'order_number': order.order_number,
        'waypoints': [],
        'route_exists': False,
    }

    # Check if route exists
    if hasattr(order, 'route') and order.route:
        route = order.route
        route_data['route_exists'] = True
        route_data['route_name'] = route.route_name
        route_data['route_type'] = route.route_type
        route_data['route_status'] = route.route_status
        route_data['progress_percentage'] = route.progress_percentage

        # Add waypoints
        for waypoint in route.waypoints.all().order_by('sequence_order'):
            waypoint_data = {
                'sequence_order': waypoint.sequence_order,
                'name': waypoint.name,
                'waypoint_type': waypoint.waypoint_type,
                'latitude': float(waypoint.location.latitude),
                'longitude': float(waypoint.location.longitude),
                'is_current': waypoint.is_current,
                'is_completed': waypoint.is_completed,
                'estimated_arrival': waypoint.estimated_arrival.isoformat() if waypoint.estimated_arrival else None,
                'actual_arrival': waypoint.actual_arrival.isoformat() if waypoint.actual_arrival else None,
            }
            route_data['waypoints'].append(waypoint_data)

    # Add all locations for this order
    route_data['locations'] = []
    for location in order.locations.filter(is_customer_visible=True).order_by('created_at'):
        location_data = {
            'name': location.name,
            'location_type': location.location_type,
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'address': location.address,
            'is_current_location': location.is_current_location,
            'estimated_arrival_time': location.estimated_arrival_time.isoformat() if location.estimated_arrival_time else None,
            'actual_arrival_time': location.actual_arrival_time.isoformat() if location.actual_arrival_time else None,
        }
        route_data['locations'].append(location_data)

    return JsonResponse(route_data)


@htmx_login_required
def import_order_live_tracking_htmx(request, order_number):
    """Enhanced HTMX endpoint for live tracking with real-time updates"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    # Get comprehensive tracking data
    tracking_data = {
        'order_number': order.order_number,
        'vehicle_details': order.vehicle_details,
        'status': order.status,
        'status_display': order.get_status_display(),
        'progress_percentage': order.progress_percentage,
        'tracking_enabled': order.has_tracking_enabled(),
        'last_update_timestamp': timezone.now().isoformat(),
    }

    # Current location data
    if order.current_latitude and order.current_longitude:
        tracking_data['current_location'] = {
            'latitude': float(order.current_latitude),
            'longitude': float(order.current_longitude),
            'name': order.current_location_name or 'Current Location',
            'coordinates_string': order.current_coordinates_string,
            'google_maps_url': order.google_maps_url,
            'last_update': order.last_location_update.isoformat() if order.last_location_update else None,
            'time_since_update': order.last_location_update.strftime('%Y-%m-%d %H:%M:%S') if order.last_location_update else None,
        }
    else:
        tracking_data['current_location'] = None

    # Route and waypoint data
    if hasattr(order, 'route') and order.route:
        route = order.route
        tracking_data['route'] = {
            'name': route.route_name,
            'type': route.route_type,
            'status': route.route_status,
            'progress_percentage': route.progress_percentage,
            'current_waypoint': None,
            'next_waypoint': None,
        }

        # Current waypoint
        current_waypoint = route.current_waypoint
        if current_waypoint:
            tracking_data['route']['current_waypoint'] = {
                'name': current_waypoint.name,
                'type': current_waypoint.waypoint_type,
                'estimated_arrival': current_waypoint.estimated_arrival.isoformat() if current_waypoint.estimated_arrival else None,
            }

        # Next waypoint
        next_waypoint = route.next_waypoint
        if next_waypoint:
            tracking_data['route']['next_waypoint'] = {
                'name': next_waypoint.name,
                'type': next_waypoint.waypoint_type,
                'estimated_arrival': next_waypoint.estimated_arrival.isoformat() if next_waypoint.estimated_arrival else None,
            }

    # Recent tracking history (last 5 entries)
    recent_history = order.tracking_history.all().order_by('-recorded_at')[:5]
    tracking_data['recent_history'] = []
    for entry in recent_history:
        tracking_data['recent_history'].append({
            'latitude': float(entry.latitude),
            'longitude': float(entry.longitude),
            'recorded_at': entry.recorded_at.isoformat(),
            'tracking_source': entry.tracking_source,
            'notes': entry.notes,
            'status_at_time': entry.status_at_time,
        })

    # Estimated arrival information
    if order.estimated_arrival_date:
        tracking_data['estimated_arrival'] = {
            'date': order.estimated_arrival_date.isoformat(),
            'days_remaining': (order.estimated_arrival_date - timezone.now().date()).days,
        }

    return JsonResponse(tracking_data)


@htmx_login_required
def import_order_tracking_dashboard_htmx(request):
    """HTMX endpoint for updating the tracking dashboard with live data"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # Get user's orders with tracking enabled
    orders = ImportOrder.objects.filter(
        customer=request.user,
        tracking_enabled=True
    ).exclude(status__in=['delivered', 'cancelled']).order_by('-created_at')

    dashboard_data = {
        'total_tracked_orders': orders.count(),
        'orders_with_location': orders.filter(
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).count(),
        'orders': []
    }

    for order in orders:
        order_data = {
            'order_number': order.order_number,
            'vehicle_details': order.vehicle_details,
            'status': order.status,
            'status_display': order.get_status_display(),
            'progress_percentage': order.progress_percentage,
            'current_location': None,
            'last_update': None,
        }

        if order.current_latitude and order.current_longitude:
            order_data['current_location'] = {
                'name': order.current_location_name or 'Location Available',
                'coordinates': order.current_coordinates_string,
                'google_maps_url': order.google_maps_url,
            }
            order_data['last_update'] = order.last_location_update.isoformat() if order.last_location_update else None

        dashboard_data['orders'].append(order_data)

    return JsonResponse(dashboard_data)


@login_required
def import_order_location_history_htmx(request, order_number):
    """HTMX endpoint for loading location history with pagination"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    # Pagination parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))

    # Get tracking history with pagination
    history_entries = order.tracking_history.all().order_by('-recorded_at')
    total_entries = history_entries.count()

    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    page_entries = history_entries[start_index:end_index]

    history_data = {
        'order_number': order.order_number,
        'total_entries': total_entries,
        'current_page': page,
        'per_page': per_page,
        'total_pages': (total_entries + per_page - 1) // per_page,
        'has_next': end_index < total_entries,
        'has_previous': page > 1,
        'entries': []
    }

    for entry in page_entries:
        history_data['entries'].append({
            'id': entry.id,
            'latitude': float(entry.latitude),
            'longitude': float(entry.longitude),
            'coordinates_string': entry.coordinates_string,
            'recorded_at': entry.recorded_at.isoformat(),
            'tracking_source': entry.tracking_source,
            'tracking_source_display': entry.get_tracking_source_display(),
            'status_at_time': entry.status_at_time,
            'status_display': entry.get_status_at_time_display(),
            'notes': entry.notes,
            'speed': float(entry.speed) if entry.speed else None,
            'heading': float(entry.heading) if entry.heading else None,
        })

    return JsonResponse(history_data)


@login_required
def import_order_sse_tracking(request, order_number):
    """Server-Sent Events endpoint for real-time tracking updates"""
    from django.http import StreamingHttpResponse
    import json
    import time

    order = get_object_or_404(ImportOrder, order_number=order_number, customer=request.user)

    def event_stream():
        """Generate SSE events for real-time tracking"""
        last_update = None

        while True:
            try:
                # Check if order still exists and tracking is enabled
                current_order = ImportOrder.objects.get(id=order.id)
                if not current_order.has_tracking_enabled():
                    break

                # Check for location updates
                current_update = current_order.last_location_update
                if current_update != last_update:
                    # Location has been updated
                    tracking_data = {
                        'type': 'location_update',
                        'order_number': current_order.order_number,
                        'current_location': None,
                        'status': current_order.status,
                        'status_display': current_order.get_status_display(),
                        'progress_percentage': current_order.progress_percentage,
                        'timestamp': timezone.now().isoformat(),
                    }

                    if current_order.current_latitude and current_order.current_longitude:
                        tracking_data['current_location'] = {
                            'latitude': float(current_order.current_latitude),
                            'longitude': float(current_order.current_longitude),
                            'name': current_order.current_location_name or 'Current Location',
                            'coordinates_string': current_order.current_coordinates_string,
                            'last_update': current_order.last_location_update.isoformat() if current_order.last_location_update else None,
                        }

                    yield f"data: {json.dumps(tracking_data)}\n\n"
                    last_update = current_update

                # Send heartbeat every 30 seconds
                heartbeat_data = {
                    'type': 'heartbeat',
                    'timestamp': timezone.now().isoformat(),
                    'order_number': current_order.order_number,
                    'tracking_active': current_order.has_tracking_enabled(),
                }
                yield f"data: {json.dumps(heartbeat_data)}\n\n"

                # Wait before next check
                time.sleep(30)

            except ImportOrder.DoesNotExist:
                # Order was deleted
                break
            except Exception as e:
                # Log error and continue
                error_data = {
                    'type': 'error',
                    'message': 'Tracking temporarily unavailable',
                    'timestamp': timezone.now().isoformat(),
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                time.sleep(60)  # Wait longer on error

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'

    return response


@login_required
def import_order_tracking_notifications_htmx(request):
    """HTMX endpoint for tracking notifications and alerts"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # Get user's orders with recent updates
    recent_cutoff = timezone.now() - timezone.timedelta(hours=1)
    recent_updates = LocationTrackingHistory.objects.filter(
        import_order__customer=request.user,
        recorded_at__gte=recent_cutoff
    ).select_related('import_order').order_by('-recorded_at')[:10]

    notifications = []
    for update in recent_updates:
        notification = {
            'id': update.id,
            'order_number': update.import_order.order_number,
            'vehicle_details': update.import_order.vehicle_details,
            'message': update.notes or 'Location updated',
            'timestamp': update.recorded_at.isoformat(),
            'time_ago': (timezone.now() - update.recorded_at).total_seconds() / 60,  # minutes
            'coordinates': update.coordinates_string,
            'tracking_source': update.get_tracking_source_display(),
            'status': update.import_order.status,
        }
        notifications.append(notification)

    return JsonResponse({
        'notifications': notifications,
        'count': len(notifications),
        'last_check': timezone.now().isoformat(),
    })


# HTMX Views for Admin Sidebar Real-time Updates
from .decorators import htmx_staff_required, htmx_admin_required

@htmx_admin_required
def admin_tracking_stats_htmx(request):
    """HTMX endpoint for real-time tracking statistics in admin sidebar"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    from datetime import timedelta

    # Calculate real-time statistics
    stats = {
        'total_orders': ImportOrder.objects.count(),
        'pending_orders': ImportOrder.objects.filter(
            status__in=['quotation_pending', 'confirmed']
        ).count(),
        'in_transit': ImportOrder.objects.filter(status='in_transit').count(),
        'arrived': ImportOrder.objects.filter(status='arrived_docked').count(),
        'under_clearance': ImportOrder.objects.filter(status='under_clearance').count(),
        'ready_for_dispatch': ImportOrder.objects.filter(status='ready_for_dispatch').count(),
    }

    return JsonResponse(stats)


@htmx_admin_required
def admin_inquiry_stats_htmx(request):
    """HTMX endpoint for real-time inquiry statistics"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    from datetime import timedelta

    stats = {
        'new_inquiries': Inquiry.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'total_inquiries': Inquiry.objects.count(),
        'pending_inquiries': Inquiry.objects.filter(
            # Add status field if available
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
    }

    return JsonResponse(stats)


@htmx_admin_required
def admin_quick_actions_htmx(request):
    """HTMX endpoint for admin sidebar quick actions and stats"""
    if not request.headers.get('HX-Request'):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    from datetime import timedelta

    # Comprehensive admin statistics
    stats = {
        # Import tracking stats
        'total_import_orders': ImportOrder.objects.count(),
        'pending_imports': ImportOrder.objects.filter(
            status__in=['quotation_pending', 'confirmed']
        ).count(),
        'in_transit_count': ImportOrder.objects.filter(status='in_transit').count(),
        'arrived_count': ImportOrder.objects.filter(status='arrived_docked').count(),
        'delivered_count': ImportOrder.objects.filter(status='delivered').count(),

        # User management stats
        'total_users': User.objects.count(),
        'new_users_week': User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'active_vendors': Vendor.objects.filter(is_approved=True).count(),

        # Inventory stats
        'total_cars': Car.objects.count(),
        'pending_approvals': Car.objects.filter(is_approved=False).count(),

        # Communication stats
        'new_inquiries': Inquiry.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),

        # System health indicators
        'system_status': 'operational',
        'last_updated': timezone.now().isoformat(),
    }

    return JsonResponse(stats)


def verify_email_with_code(request):
    """Email verification using 6-digit code"""
    if request.user.is_authenticated and request.user.is_email_verified:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = VerificationCodeForm(request.POST, user=request.user, code_type='email_verification')
        if form.is_valid():
            if form.verify_and_mark_used():
                # Mark user email as verified
                request.user.is_email_verified = True
                request.user.save()

                messages.success(
                    request,
                    'Your email has been verified successfully! You can now access all features.'
                )
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Failed to verify email. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = VerificationCodeForm(user=request.user, code_type='email_verification')

    return render(request, 'core/auth/verify_email_code.html', {'form': form})


def request_verification_code(request):
    """Request a new verification code"""
    if request.method == 'POST':
        form = RequestVerificationCodeForm(request.POST, code_type='email_verification')
        if form.is_valid():
            if form.send_verification_code():
                messages.success(
                    request,
                    'A new verification code has been sent to your email address.'
                )
                return redirect('core:verify_email_code')
            else:
                messages.error(
                    request,
                    'Failed to send verification code. Please try again later.'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RequestVerificationCodeForm(code_type='email_verification')

    return render(request, 'core/auth/request_verification_code.html', {'form': form})


def password_reset_with_code(request):
    """Password reset using 6-digit code"""
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST, code_type='password_reset')
        if form.is_valid():
            if form.verify_and_mark_used():
                # Store verification in session for password reset
                request.session['password_reset_verified'] = True
                request.session['password_reset_user_id'] = form.user.id

                messages.success(
                    request,
                    'Code verified! You can now set your new password.'
                )
                return redirect('core:set_new_password')
            else:
                messages.error(request, 'Failed to verify code. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = VerificationCodeForm(code_type='password_reset')

    return render(request, 'core/auth/password_reset_code.html', {'form': form})


def request_password_reset_code(request):
    """Request a password reset code"""
    if request.method == 'POST':
        form = RequestVerificationCodeForm(request.POST, code_type='password_reset')
        if form.is_valid():
            if form.send_verification_code():
                messages.success(
                    request,
                    'A password reset code has been sent to your email address.'
                )
                return redirect('core:password_reset_code')
            else:
                messages.error(
                    request,
                    'Failed to send password reset code. Please try again later.'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RequestVerificationCodeForm(code_type='password_reset')

    return render(request, 'core/auth/request_password_reset_code.html', {'form': form})


# Opinion Polling Views

@require_http_methods(["POST"])
def poll_vote(request, poll_id):
    """HTMX endpoint for submitting poll votes"""
    try:
        poll = get_object_or_404(OpinionPoll, id=poll_id)

        if not poll.is_open:
            return JsonResponse({
                'success': False,
                'message': 'This poll is no longer accepting votes.'
            })

        option_id = request.POST.get('option_id')
        if not option_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select an option.'
            })

        option = get_object_or_404(PollOption, id=option_id, poll=poll)

        # Check for existing vote
        existing_vote = None
        if request.user.is_authenticated:
            existing_vote = PollVote.objects.filter(poll=poll, user=request.user).first()
        elif not poll.allow_anonymous_voting:
            return JsonResponse({
                'success': False,
                'message': 'You must be logged in to vote on this poll.'
            })
        else:
            # Check by session for anonymous users
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            existing_vote = PollVote.objects.filter(poll=poll, session_key=session_key).first()

        # Handle existing vote
        if existing_vote and not poll.multiple_votes_per_user:
            if existing_vote.option == option:
                return JsonResponse({
                    'success': False,
                    'message': 'You have already voted for this option.'
                })
            else:
                # Update existing vote
                existing_vote.option.vote_count -= 1
                existing_vote.option.save()
                existing_vote.option = option
                existing_vote.save()
                option.vote_count += 1
                option.save()
        else:
            # Create new vote
            vote_data = {
                'poll': poll,
                'option': option,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }

            if request.user.is_authenticated:
                vote_data['user'] = request.user
            else:
                vote_data['session_key'] = session_key

            PollVote.objects.create(**vote_data)
            option.vote_count += 1
            option.save()

            # Update poll total
            poll.total_votes += 1
            poll.save()

        # Return updated results
        results = poll.get_results()
        context = {
            'poll': poll,
            'results': results,
            'user_voted': True,
        }

        return render(request, 'core/htmx/poll_results.html', context)

    except Exception as e:
        logging.error(f"Error in poll_vote: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your vote.'
        })


@require_http_methods(["POST"])
def opinion_review_submit(request, post_id):
    """HTMX endpoint for submitting opinion reviews"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'You must be logged in to submit a review.'
        })

    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='opinion', is_published=True)

        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text', '').strip()

        if not rating:
            return JsonResponse({
                'success': False,
                'message': 'Please provide a rating.'
            })

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid rating value.'
            })

        # Create or update review
        review, created = OpinionReview.objects.update_or_create(
            opinion_post=post,
            reviewer=request.user,
            defaults={
                'rating': rating,
                'review_text': review_text,
                'is_approved': False  # Requires moderation
            }
        )

        action = 'submitted' if created else 'updated'

        # Calculate average rating for the post
        avg_rating = OpinionReview.objects.filter(
            opinion_post=post,
            is_approved=True
        ).aggregate(avg=models.Avg('rating'))['avg'] or 0

        context = {
            'post': post,
            'review': review,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': post.opinion_reviews.filter(is_approved=True).count(),
            'success_message': f'Your review has been {action} and is pending approval.'
        }

        return render(request, 'core/htmx/opinion_review_form.html', context)

    except Exception as e:
        logging.error(f"Error in opinion_review_submit: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while submitting your review.'
        })


@require_http_methods(["POST"])
def review_helpful_vote(request, review_id):
    """HTMX endpoint for voting on review helpfulness"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'You must be logged in to vote.'
        })

    try:
        review = get_object_or_404(OpinionReview, id=review_id, is_approved=True)
        is_helpful = request.POST.get('is_helpful') == 'true'

        # Create or update helpful vote
        helpful_vote, created = ReviewHelpfulVote.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={'is_helpful': is_helpful}
        )

        if not created:
            # If vote changed, update counts
            if helpful_vote.is_helpful != is_helpful:
                if is_helpful:
                    review.helpful_votes += 1
                else:
                    review.helpful_votes = max(0, review.helpful_votes - 1)
                review.save()
        else:
            # New vote
            if is_helpful:
                review.helpful_votes += 1
                review.save()

        return JsonResponse({
            'success': True,
            'helpful_votes': review.helpful_votes,
            'user_voted_helpful': is_helpful
        })

    except Exception as e:
        logging.error(f"Error in review_helpful_vote: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your vote.'
        })


# PDF Management Views

def guide_pdf_download(request, post_id):
    """Download PDF file for guide posts"""
    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='guide', is_published=True)

        if not post.has_pdf:
            messages.error(request, 'PDF file not available for this guide.')
            return redirect('core:resource_detail', slug=post.slug)

        # Increment download counter
        post.increment_pdf_download()

        # Serve the file
        response = HttpResponse(post.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{post.title}.pdf"'
        response['Content-Length'] = post.pdf_file_size or post.pdf_file.size

        return response

    except Exception as e:
        logging.error(f"Error in guide_pdf_download: {str(e)}")
        messages.error(request, 'Error downloading PDF file.')
        return redirect('core:resources')


def guide_pdf_viewer(request, post_id):
    """View PDF file inline for guide posts"""
    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='guide', is_published=True)

        if not post.has_pdf:
            messages.error(request, 'PDF file not available for this guide.')
            return redirect('core:resource_detail', slug=post.slug)

        # Serve the file for inline viewing
        response = HttpResponse(post.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{post.title}.pdf"'
        response['Content-Length'] = post.pdf_file_size or post.pdf_file.size

        return response

    except Exception as e:
        logging.error(f"Error in guide_pdf_viewer: {str(e)}")
        messages.error(request, 'Error viewing PDF file.')
        return redirect('core:resource_detail', slug=post.slug)


@require_http_methods(["GET"])
def guide_pdf_info(request, post_id):
    """HTMX endpoint for PDF file information"""
    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='guide', is_published=True)

        context = {
            'post': post,
            'has_pdf': post.has_pdf,
            'pdf_size': post.pdf_file_size_formatted if post.has_pdf else None,
            'download_count': post.pdf_download_count,
        }

        return render(request, 'core/htmx/guide_pdf_info.html', context)

    except Exception as e:
        logging.error(f"Error in guide_pdf_info: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error loading PDF information.'
        })


# Infographic Chart Management Views

@require_http_methods(["GET"])
def infographic_chart_data(request, post_id):
    """HTMX endpoint for getting chart data for infographics"""
    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='infographic', is_published=True)

        if not post.has_chart_data:
            return JsonResponse({
                'success': False,
                'message': 'No chart data available for this infographic.'
            })

        chart_config = post.get_chart_config()

        return JsonResponse({
            'success': True,
            'chart_config': chart_config,
            'chart_type': post.chart_type
        })

    except Exception as e:
        logging.error(f"Error in infographic_chart_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error loading chart data.'
        })


@require_http_methods(["POST"])
def infographic_chart_update(request, post_id):
    """HTMX endpoint for updating chart data (admin only)"""
    if not (request.user.is_staff or getattr(request.user, 'role', None) == 'admin'):
        return JsonResponse({
            'success': False,
            'message': 'Access denied.'
        })

    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='infographic')

        chart_type = request.POST.get('chart_type')
        chart_data_json = request.POST.get('chart_data')

        if not chart_type or not chart_data_json:
            return JsonResponse({
                'success': False,
                'message': 'Chart type and data are required.'
            })

        try:
            import json
            chart_data = json.loads(chart_data_json)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid chart data format.'
            })

        # Update chart data
        post.set_chart_data(chart_type, chart_data)

        return JsonResponse({
            'success': True,
            'message': 'Chart data updated successfully.',
            'chart_config': post.get_chart_config()
        })

    except Exception as e:
        logging.error(f"Error in infographic_chart_update: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error updating chart data.'
        })


@require_http_methods(["GET"])
def infographic_chart_preview(request, post_id):
    """HTMX endpoint for chart preview"""
    try:
        post = get_object_or_404(BlogPost, id=post_id, content_type='infographic', is_published=True)

        context = {
            'post': post,
            'has_chart': post.has_chart_data,
            'chart_config': post.get_chart_config() if post.has_chart_data else None,
        }

        return render(request, 'core/htmx/infographic_chart_preview.html', context)

    except Exception as e:
        logging.error(f"Error in infographic_chart_preview: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error loading chart preview.'
        })


# Message System Debug View

@login_required
def message_debug_view(request):
    """Debug view to test message system functionality"""
    from .models import Message, MessageRead
    from .services.message_service import MessageTargetingService

    # Get active popup messages
    popup_messages = Message.objects.filter(
        status='active',
        show_as_popup=True
    ).order_by('-priority', '-created_at')

    # Check which messages should show to current user
    messages_for_user = []
    for message in popup_messages:
        read_status = MessageRead.objects.filter(message=message, user=request.user).first()
        should_show = MessageTargetingService.should_show_message_to_user(message, request.user)

        messages_for_user.append({
            'message': message,
            'read_status': read_status,
            'should_show': should_show
        })

    context = {
        'popup_messages': popup_messages,
        'messages_for_user': messages_for_user,
        'user': request.user,
    }

    return render(request, 'core/message_debug.html', context)
