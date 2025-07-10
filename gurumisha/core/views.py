from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q, Min, Max
from django.db import models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .models import (
    Car, CarBrand, CarModel, SparePart, ImportRequest, ImportOrder, ImportOrderStatusHistory, ImportOrderDocument,
    Inquiry, Testimonial, BlogPost, Vendor, User,
    Cart, CartItem, Order, OrderItem, Payment, Invoice, StockMovement
)
from .forms import (
    CustomUserRegistrationForm, CustomLoginForm, SellCarForm,
    ImportRequestForm, ContactForm, CustomPasswordResetForm, CustomSetPasswordForm,
    CustomAuthenticationForm, ResendVerificationEmailForm,
    VerificationCodeForm, RequestVerificationCodeForm
)


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

            context.update({
                'vendor': vendor,
                'vendor_cars': vendor_cars.order_by('-created_at')[:5],
                'pending_inquiries': Inquiry.objects.filter(
                    car__vendor=vendor, status='open'
                ).order_by('-created_at')[:5],
                'total_views': total_views,
                'monthly_growth': 15,  # This would be calculated based on actual data
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
    context = {
        'featured_cars': Car.objects.filter(status='featured', is_approved=True)[:6],
        'car_brands': CarBrand.objects.filter(is_active=True)[:8],
        'testimonials': Testimonial.objects.filter(is_approved=True, is_featured=True)[:3],
        'blog_posts': BlogPost.objects.filter(is_published=True)[:3],
        'hot_deals': Car.objects.filter(is_approved=True).order_by('-created_at')[:4],
        'vehicle_types': ['SUV', 'Sedan', 'Hatchback', 'Pickup', 'Coupe', 'Convertible'],
        'spare_part_categories': ['Engine Parts', 'Brake System', 'Electrical', 'Body Parts'],
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

        # Condition filter - new
        condition = self.request.GET.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)

        # Listing type filter - new pill section feature
        listing_type = self.request.GET.get('listing_type')
        if listing_type:
            queryset = queryset.filter(listing_type=listing_type)

        # Status filter - include featured cars
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        else:
            # Default: show available and featured cars
            queryset = queryset.filter(status__in=['available', 'featured'])

        # Sorting - enhanced options
        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sorts = [
            'price', '-price', 'year', '-year', 'mileage', '-mileage',
            '-created_at', 'created_at', 'title', '-title', 'views_count', '-views_count'
        ]
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Enhanced context data
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')
        context['fuel_types'] = Car.FUEL_TYPE_CHOICES
        context['transmission_types'] = Car.TRANSMISSION_CHOICES
        context['condition_types'] = Car.CONDITION_CHOICES
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

        return context

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
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Related cars
        context['related_cars'] = Car.objects.filter(
            brand=self.object.brand,
            is_approved=True,
            status='available'
        ).exclude(id=self.object.id)[:4]
        return context


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
            queryset = queryset.filter(category=category)

        # Brand compatibility filter
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(compatible_brands__id=brand)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SparePart.objects.values_list('category', flat=True).distinct().order_by('category')
        context['brands'] = CarBrand.objects.filter(is_active=True).order_by('name')

        # Add price range for filters
        price_range = SparePart.objects.filter(is_available=True).aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price')
        )
        context['price_range'] = price_range

        # Add condition choices
        context['condition_choices'] = SparePart.CONDITION_CHOICES

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
                    vendor=item.spare_part.vendor,
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
                payment_result = initiate_mpesa_payment(order, customer_phone)
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


def initiate_mpesa_payment(order, phone_number):
    """Initiate M-Pesa STK Push payment"""
    # This is a placeholder for M-Pesa integration
    # In a real implementation, you would integrate with Safaricom's Daraja API

    try:
        import uuid

        # Create payment record
        payment = Payment.objects.create(
            payment_id=f"MPESA-{str(uuid.uuid4())[:8].upper()}",
            order=order,
            payment_method='mpesa',
            amount=order.total_amount,
            mpesa_phone_number=phone_number,
            mpesa_checkout_request_id=f"ws_CO_{str(uuid.uuid4())[:20]}",
            status='processing'
        )

        # Simulate M-Pesa STK push
        # In real implementation, you would call Safaricom's API here

        return {
            'success': True,
            'message': 'M-Pesa payment initiated successfully',
            'payment_id': payment.payment_id,
            'checkout_request_id': payment.mpesa_checkout_request_id
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
                        order = payment.order
                        order.payment_status = 'completed'
                        order.status = 'paid'
                        order.save()

                        # Generate invoice
                        generate_invoice(order)

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
    """Blog listing page"""
    model = BlogPost
    template_name = 'core/blog.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).order_by('-published_at')


class BlogDetailView(DetailView):
    """Blog post detail page"""
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)


def about_us(request):
    """About us page"""
    context = {
        'testimonials': Testimonial.objects.filter(is_approved=True)[:6],
        'team_members': [],  # Add team members if needed
    }
    return render(request, 'core/about_us.html', context)


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


# Car Sales Views
@login_required
def sell_car(request):
    """Sell car form view"""
    if request.method == 'POST':
        form = SellCarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)

            # Get or create vendor profile for the user
            if request.user.role == 'vendor':
                try:
                    vendor = request.user.vendor
                except Vendor.DoesNotExist:
                    # Create vendor profile if it doesn't exist
                    vendor = Vendor.objects.create(
                        user=request.user,
                        company_name=f"{request.user.first_name} {request.user.last_name}",
                        is_approved=False
                    )
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

            car.vendor = vendor
            car.status = 'available'
            car.is_approved = False  # Requires admin approval
            car.save()

            messages.success(request, 'Your car listing has been submitted for review. We will notify you once it\'s approved.')
            return redirect('core:dashboard')
    else:
        form = SellCarForm()

    context = {
        'form': form,
        'car_brands': CarBrand.objects.filter(is_active=True),
    }
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
@login_required
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


@login_required
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


# HTMX Views for Admin Sidebar Real-time Updates
@login_required
@user_passes_test(lambda u: u.is_staff)
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


@login_required
@user_passes_test(lambda u: u.is_staff)
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


@login_required
@user_passes_test(lambda u: u.is_staff)
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
