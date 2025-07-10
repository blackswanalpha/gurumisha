"""
Dashboard-specific views for Gurumisha Motors
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json
from io import StringIO

from .models import (
    Car, CarBrand, CarModel, SparePart, ImportRequest, ImportOrder, ImportOrderStatusHistory,
    Inquiry, Testimonial, BlogPost, Vendor, User,
    Supplier, PurchaseOrder, StockMovement, InventoryAlert,
    Order, OrderItem, Payment, SparePartCategory, Notification, SystemSetting,
    ActivityLog, AuditLog, NotificationPreference, NotificationQueue
)
from .dashboard_forms import (
    UserProfileForm, VendorProfileForm, PasswordChangeForm,
    InquiryResponseForm, CarApprovalForm, VendorApprovalForm,
    UserSearchForm, CarSearchForm, VendorSearchForm
)


def apply_import_request_filters(request, queryset):
    """Apply comprehensive filters to import request queryset"""

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Search filter (across multiple fields)
    search_query = request.GET.get('search')
    if search_query:
        queryset = queryset.filter(
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(customer__email__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Brand filter
    brand_filter = request.GET.get('brand')
    if brand_filter:
        queryset = queryset.filter(brand=brand_filter)

    # Country filter
    country_filter = request.GET.get('country')
    if country_filter:
        queryset = queryset.filter(origin_country=country_filter)

    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass

    return queryset


@login_required
def user_profile_view(request):
    """User profile management view with form handling"""
    user = request.user
    vendor = None

    if user.role == 'vendor':
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            messages.warning(request, 'Please complete your vendor profile.')
            return redirect('core:vendor_profile_create')

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        vendor_form = VendorProfileForm(request.POST, instance=vendor) if vendor else None

        if user_form.is_valid() and (vendor_form is None or vendor_form.is_valid()):
            user_form.save()
            if vendor_form:
                vendor_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileForm(instance=user)
        vendor_form = VendorProfileForm(instance=vendor) if vendor else None

    context = {
        'user': user,
        'vendor': vendor,
        'user_form': user_form,
        'vendor_form': vendor_form,
    }

    return render(request, 'core/dashboard/profile.html', context)


@login_required
def user_orders_view(request):
    """User orders dashboard"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get user orders
    orders = Order.objects.filter(customer=request.user).prefetch_related('items', 'payments').order_by('-created_at')

    # Calculate stats
    total_orders = orders.count()
    total_spent = sum(order.total_amount for order in orders if order.payment_status == 'completed')
    pending_orders = orders.filter(status='pending').count()
    completed_orders = orders.filter(status='delivered').count()

    context = {
        'orders': orders[:10],  # Recent 10 orders
        'total_orders': total_orders,
        'total_spent': total_spent,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    }

    return render(request, 'core/dashboard/orders.html', context)


@login_required
def user_addresses_view(request):
    """User addresses management view"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # This would be implemented when address system is added
    context = {
        'addresses': [],  # Placeholder for addresses
    }

    return render(request, 'core/dashboard/addresses.html', context)


@login_required
def user_import_requests_view(request):
    """User import requests management view"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get user's import requests
    import_requests = ImportRequest.objects.filter(customer=request.user).order_by('-created_at')

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        import_requests = import_requests.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        import_requests = import_requests.filter(
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(origin_country__icontains=search_query)
        )

    # Calculate stats
    total_requests = ImportRequest.objects.filter(customer=request.user).count()
    pending_requests = ImportRequest.objects.filter(customer=request.user, status='pending').count()
    completed_requests = ImportRequest.objects.filter(customer=request.user, status='completed').count()
    in_progress_requests = ImportRequest.objects.filter(
        customer=request.user,
        status__in=['on_quotation', 'processing', 'fee_paid']
    ).count()

    context = {
        'import_requests': import_requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'in_progress_requests': in_progress_requests,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': ImportRequest.STATUS_CHOICES,
    }

    return render(request, 'core/dashboard/user_import_requests.html', context)


@login_required
def user_inquiries_view(request):
    """User inquiries management view"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get user's inquiries
    inquiries = Inquiry.objects.filter(customer=request.user).order_by('-created_at')

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        inquiries = inquiries.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        inquiries = inquiries.filter(
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    # Calculate stats
    total_inquiries = Inquiry.objects.filter(customer=request.user).count()
    open_inquiries = Inquiry.objects.filter(customer=request.user, status='open').count()
    resolved_inquiries = Inquiry.objects.filter(customer=request.user, status='resolved').count()
    in_progress_inquiries = Inquiry.objects.filter(customer=request.user, status='in_progress').count()

    context = {
        'inquiries': inquiries,
        'total_inquiries': total_inquiries,
        'open_inquiries': open_inquiries,
        'resolved_inquiries': resolved_inquiries,
        'in_progress_inquiries': in_progress_inquiries,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'core/dashboard/user_inquiries.html', context)


@login_required
def user_wishlist_view(request):
    """User wishlist management view"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # This would be implemented when wishlist system is added
    context = {
        'wishlist_items': [],  # Placeholder for wishlist items
        'wishlist_count': 0,
    }

    return render(request, 'core/dashboard/user_wishlist.html', context)


@login_required
def user_settings_view(request):
    """User settings management view"""
    if request.user.role != 'customer':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    if request.method == 'POST':
        # Handle settings updates
        pass

    context = {
        'user': request.user,
    }

    return render(request, 'core/dashboard/user_settings.html', context)


@login_required
def user_listings_view(request):
    """User car listings management view - for customers and vendors who submitted cars"""
    # Allow both customers and vendors to access this view
    # Vendors who were originally customers can see their submitted cars here
    if request.user.role not in ['customer', 'vendor']:
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get user's car listings through their vendor profile
    user_cars = Car.objects.none()
    try:
        # Check if user has a vendor profile (created when they submit a car)
        vendor = request.user.vendor
        user_cars = Car.objects.filter(vendor=vendor).order_by('-created_at')

        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter == 'approved':
            user_cars = user_cars.filter(is_approved=True)
        elif status_filter == 'pending':
            user_cars = user_cars.filter(is_approved=False)

        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            user_cars = user_cars.filter(
                Q(title__icontains=search_query) |
                Q(brand__name__icontains=search_query) |
                Q(model__name__icontains=search_query)
            )

    except Vendor.DoesNotExist:
        # User hasn't submitted any cars yet
        user_cars = Car.objects.none()

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(user_cars, 10)
    page_number = request.GET.get('page')
    cars_page = paginator.get_page(page_number)

    context = {
        'cars': cars_page,
        'total_cars': user_cars.count(),
        'approved_cars': user_cars.filter(is_approved=True).count(),
        'pending_cars': user_cars.filter(is_approved=False).count(),
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'core/dashboard/user_listings.html', context)


@login_required
def vendor_settings_view(request):
    """Vendor settings management view"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')

    if request.method == 'POST':
        # Handle settings updates
        setting_type = request.POST.get('setting_type')

        if setting_type == 'notifications':
            # Handle notification preferences
            vendor.email_notifications = request.POST.get('email_notifications') == 'on'
            vendor.sms_notifications = request.POST.get('sms_notifications') == 'on'
            vendor.inquiry_notifications = request.POST.get('inquiry_notifications') == 'on'
            vendor.order_notifications = request.POST.get('order_notifications') == 'on'
            vendor.save()
            messages.success(request, 'Notification preferences updated successfully.')

        elif setting_type == 'business_hours':
            # Handle business hours
            vendor.business_hours = request.POST.get('business_hours', '')
            vendor.timezone = request.POST.get('timezone', 'Africa/Nairobi')
            vendor.save()
            messages.success(request, 'Business hours updated successfully.')

        elif setting_type == 'payment':
            # Handle payment settings
            vendor.payment_methods = request.POST.get('payment_methods', '')
            vendor.bank_details = request.POST.get('bank_details', '')
            vendor.mpesa_number = request.POST.get('mpesa_number', '')
            vendor.save()
            messages.success(request, 'Payment settings updated successfully.')

        elif setting_type == 'account':
            # Handle account settings
            vendor.auto_approve_inquiries = request.POST.get('auto_approve_inquiries') == 'on'
            vendor.public_profile = request.POST.get('public_profile') == 'on'
            vendor.save()
            messages.success(request, 'Account settings updated successfully.')

        return redirect('core:vendor_settings')

    # Ensure vendor has all required fields with defaults
    if not hasattr(vendor, 'email_notifications'):
        vendor.email_notifications = True
        vendor.sms_notifications = False
        vendor.inquiry_notifications = True
        vendor.order_notifications = True
        vendor.public_profile = True
        vendor.show_contact = True
        vendor.auto_approve_inquiries = False
        vendor.timezone = 'Africa/Nairobi'
        vendor.save()

    context = {
        'vendor': vendor,
        'user': request.user,
    }

    return render(request, 'core/dashboard/vendor_settings.html', context)


@login_required
def vendor_listings_view(request):
    """Vendor car listings management view with filtering and HTMX support"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor

        # Simple context to avoid recursion - gradually add complexity
        context = {
            'vendor': vendor,
            'cars': [],  # Empty for now to avoid recursion
            'total_cars': 0,
            'approved_cars': 0,
            'pending_cars': 0,
            'total_views': 0,
            'status_filter': request.GET.get('status_filter', ''),
            'sort_by': request.GET.get('sort_by', '-created_at'),
            'search': request.GET.get('search', ''),
        }

        # Return partial template for HTMX requests
        if request.headers.get('HX-Request'):
            return render(request, 'core/dashboard/partials/vendor_car_list.html', context)

        return render(request, 'core/dashboard/vendor_listings.html', context)

    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')
    except Exception as e:
        # Log the error and provide a safe fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in vendor_listings_view: {str(e)}")

        messages.error(request, 'An error occurred while loading your listings. Please try again.')
        return redirect('core:dashboard')


@login_required
def vendor_inquiries_view(request):
    """Vendor inquiries management view with HTMX support"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor
        inquiries = Inquiry.objects.filter(car__vendor=vendor).order_by('-created_at')

        # Apply filters
        status_filter = request.GET.get('status_filter')
        car_filter = request.GET.get('car_filter')
        search = request.GET.get('search')

        if status_filter:
            inquiries = inquiries.filter(status=status_filter)

        if car_filter:
            inquiries = inquiries.filter(car_id=car_filter)

        if search:
            inquiries = inquiries.filter(
                Q(subject__icontains=search) |
                Q(message__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__email__icontains=search)
            )

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(inquiries, 10)
        page_number = request.GET.get('page')
        inquiries_page = paginator.get_page(page_number)

        context = {
            'vendor': vendor,
            'inquiries': inquiries_page,
            'vendor_cars': Car.objects.filter(vendor=vendor),
            'open_inquiries': Inquiry.objects.filter(car__vendor=vendor, status='open').count(),
            'in_progress_inquiries': Inquiry.objects.filter(car__vendor=vendor, status='in_progress').count(),
            'resolved_inquiries': Inquiry.objects.filter(car__vendor=vendor, status='resolved').count(),
        }

        # Return partial template for HTMX requests
        if request.headers.get('HX-Request'):
            return render(request, 'core/dashboard/partials/inquiry_list.html', context)

        return render(request, 'core/dashboard/vendor_inquiries.html', context)

    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')


@login_required
def vendor_analytics_view(request):
    """Vendor analytics and reporting view"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    
    try:
        vendor = request.user.vendor
        cars = Car.objects.filter(vendor=vendor)
        
        # Calculate analytics
        total_views = sum(car.views_count for car in cars)
        total_inquiries = Inquiry.objects.filter(car__vendor=vendor).count()
        
        # Monthly data (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_cars = cars.filter(created_at__range=[month_start, month_end])
            month_inquiries = Inquiry.objects.filter(
                car__vendor=vendor,
                created_at__range=[month_start, month_end]
            )
            
            monthly_data.append({
                'month': month_start.strftime('%B'),
                'cars_added': month_cars.count(),
                'inquiries': month_inquiries.count(),
                'views': sum(car.views_count for car in month_cars),
            })
        
        context = {
            'vendor': vendor,
            'total_cars': cars.count(),
            'total_views': total_views,
            'total_inquiries': total_inquiries,
            'monthly_data': monthly_data,
            'top_cars': cars.order_by('-views_count')[:5],
        }
        
        return render(request, 'core/dashboard/vendor_analytics.html', context)
        
    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')


@login_required
def admin_users_view(request):
    """Admin user management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by role if specified
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'total_users': User.objects.count(),
        'customers': User.objects.filter(role='customer').count(),
        'vendors': User.objects.filter(role='vendor').count(),
        'admins': User.objects.filter(role='admin').count(),
        'current_filter': role_filter,
        'search_query': search,
    }
    
    return render(request, 'core/dashboard/admin_users.html', context)


@login_required
def admin_vendors_view(request):
    """Admin vendor management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    
    vendors = Vendor.objects.all().order_by('-created_at')
    
    # Filter by approval status
    status_filter = request.GET.get('status')
    if status_filter == 'approved':
        vendors = vendors.filter(is_approved=True)
    elif status_filter == 'pending':
        vendors = vendors.filter(is_approved=False)
    
    context = {
        'vendors': vendors,
        'total_vendors': Vendor.objects.count(),
        'approved_vendors': Vendor.objects.filter(is_approved=True).count(),
        'pending_vendors': Vendor.objects.filter(is_approved=False).count(),
        'current_filter': status_filter,
    }
    
    return render(request, 'core/dashboard/admin_vendors.html', context)


@login_required
def admin_listings_view(request):
    """Admin car listings management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    
    cars = Car.objects.all().order_by('-created_at')
    
    # Filter by approval status
    status_filter = request.GET.get('status')
    if status_filter == 'approved':
        cars = cars.filter(is_approved=True)
    elif status_filter == 'pending':
        cars = cars.filter(is_approved=False)
    
    context = {
        'cars': cars,
        'total_cars': Car.objects.count(),
        'approved_cars': Car.objects.filter(is_approved=True).count(),
        'pending_cars': Car.objects.filter(is_approved=False).count(),
        'current_filter': status_filter,
    }
    
    return render(request, 'core/dashboard/admin_listings.html', context)


@login_required
def admin_analytics_view(request):
    """Admin analytics and reporting view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')
    
    # Calculate system-wide analytics
    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_vendors = Vendor.objects.count()
    total_inquiries = Inquiry.objects.count()
    
    # Monthly growth data
    monthly_data = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        month_users = User.objects.filter(date_joined__range=[month_start, month_end])
        month_cars = Car.objects.filter(created_at__range=[month_start, month_end])
        month_inquiries = Inquiry.objects.filter(created_at__range=[month_start, month_end])
        
        monthly_data.append({
            'month': month_start.strftime('%B'),
            'users': month_users.count(),
            'cars': month_cars.count(),
            'inquiries': month_inquiries.count(),
        })
    
    context = {
        'total_users': total_users,
        'total_cars': total_cars,
        'total_vendors': total_vendors,
        'total_inquiries': total_inquiries,
        'monthly_data': monthly_data,
        'top_brands': CarBrand.objects.annotate(
            car_count=Count('car')
        ).order_by('-car_count')[:5],
        'recent_activity': [],  # This would include recent system activities
    }
    
    return render(request, 'core/dashboard/admin_analytics.html', context)


# Lazy Loading Views for HTMX
@login_required
def vendor_recent_listings_lazy(request):
    """HTMX endpoint for vendor recent listings"""
    if request.user.role != 'vendor':
        return HttpResponse('Unauthorized', status=403)

    try:
        vendor = request.user.vendor
        vendor_cars = Car.objects.filter(vendor=vendor).order_by('-created_at')[:5]

        context = {
            'vendor_cars': vendor_cars,
        }

        return render(request, 'core/dashboard/partials/recent_listings.html', context)

    except Vendor.DoesNotExist:
        return HttpResponse('<div class="text-center py-8"><p class="text-gray-600">Please complete your vendor profile.</p></div>')


@login_required
def admin_quick_actions_lazy(request):
    """HTMX endpoint for admin quick actions"""
    if request.user.role != 'admin':
        return HttpResponse('Unauthorized', status=403)

    # Get admin stats
    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_vendors = Vendor.objects.count()
    pending_approvals = Car.objects.filter(is_approved=False).count()

    context = {
        'total_users': total_users,
        'total_cars': total_cars,
        'total_vendors': total_vendors,
        'pending_approvals': pending_approvals,
    }

    return render(request, 'core/dashboard/partials/admin_quick_actions.html', context)


# Spare Parts Dashboard Views


@login_required
def vendor_spare_parts_view(request):
    """Vendor spare parts dashboard"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor
        spare_parts = SparePart.objects.filter(vendor=vendor).select_related('supplier', 'category_new')

        # Apply filters
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        stock_status = request.GET.get('stock_status', '')

        if search:
            spare_parts = spare_parts.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(part_number__icontains=search)
            )

        if category:
            spare_parts = spare_parts.filter(category_new_id=category)

        if stock_status == 'low':
            spare_parts = [part for part in spare_parts if part.is_low_stock]
        elif stock_status == 'out':
            spare_parts = spare_parts.filter(stock_quantity=0)
        elif stock_status == 'available':
            spare_parts = spare_parts.filter(stock_quantity__gt=0)

        # Calculate stats
        total_parts = spare_parts.count() if isinstance(spare_parts, type(SparePart.objects.all())) else len(spare_parts)
        total_stock_value = sum(part.stock_value for part in spare_parts)
        low_stock_count = len([part for part in spare_parts if hasattr(part, 'is_low_stock') and part.is_low_stock])
        out_of_stock_count = spare_parts.filter(stock_quantity=0).count() if isinstance(spare_parts, type(SparePart.objects.all())) else len([part for part in spare_parts if part.stock_quantity == 0])

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(spare_parts, 20)
        page_number = request.GET.get('page')
        parts_page = paginator.get_page(page_number)

        context = {
            'vendor': vendor,
            'spare_parts': parts_page,
            'total_parts': total_parts,
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'categories': SparePartCategory.objects.filter(is_active=True),
            'search': search,
            'selected_category': category,
            'selected_stock_status': stock_status,
        }

        return render(request, 'core/dashboard/vendor_spare_parts_simple.html', context)

    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')


@login_required
def vendor_orders_view(request):
    """Vendor orders dashboard"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor
        orders = Order.objects.filter(
            items__vendor=vendor
        ).distinct().prefetch_related('items', 'payments').order_by('-created_at')

        # Calculate stats
        total_orders = orders.count()
        total_revenue = sum(
            sum(item.total_price for item in order.items.filter(vendor=vendor))
            for order in orders if order.payment_status == 'completed'
        )
        pending_orders = orders.filter(status='pending').count()
        processing_orders = orders.filter(status='processing').count()

        context = {
            'vendor': vendor,
            'orders': orders[:20],  # Recent 20 orders
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
        }

        return render(request, 'core/dashboard/vendor_orders.html', context)

    except Vendor.DoesNotExist:
        messages.warning(request, 'Please complete your vendor profile.')
        return redirect('core:vendor_profile_create')


@login_required
def admin_spare_parts_overview(request):
    """Admin spare parts overview"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Calculate system-wide spare parts analytics
    total_parts = SparePart.objects.count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    total_categories = SparePartCategory.objects.filter(is_active=True).count()
    total_stock_value = sum(part.stock_value for part in SparePart.objects.all())

    # Low stock alerts
    low_stock_parts = [part for part in SparePart.objects.all() if part.is_low_stock]
    active_alerts = InventoryAlert.objects.filter(status='active').count()

    # Recent orders
    recent_orders = Order.objects.filter(
        items__spare_part__isnull=False
    ).distinct().order_by('-created_at')[:10]

    # Monthly data
    monthly_data = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)

        month_orders = Order.objects.filter(
            created_at__range=[month_start, month_end],
            items__spare_part__isnull=False
        ).distinct()

        month_revenue = sum(
            sum(item.total_price for item in order.items.all())
            for order in month_orders if order.payment_status == 'completed'
        )

        monthly_data.append({
            'month': month_start.strftime('%B'),
            'orders': month_orders.count(),
            'revenue': month_revenue,
            'parts_sold': sum(
                sum(item.quantity for item in order.items.all())
                for order in month_orders
            ),
        })

    context = {
        'total_parts': total_parts,
        'total_suppliers': total_suppliers,
        'total_categories': total_categories,
        'total_stock_value': total_stock_value,
        'low_stock_count': len(low_stock_parts),
        'active_alerts': active_alerts,
        'recent_orders': recent_orders,
        'monthly_data': monthly_data,
        'top_selling_parts': SparePart.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).order_by('-total_sold')[:10],
    }

    return render(request, 'core/dashboard/admin_spare_parts.html', context)


@login_required
def user_quick_actions_lazy(request):
    """HTMX endpoint for user quick actions"""
    if request.user.role == 'admin' or request.user.role == 'vendor':
        return HttpResponse('Unauthorized', status=403)

    # Get user stats
    import_orders = ImportOrder.objects.filter(customer=request.user).order_by('-created_at')[:5]
    customer_inquiries = Inquiry.objects.filter(customer=request.user)[:5]

    context = {
        'import_orders': import_orders,
        'customer_inquiries': customer_inquiries,
    }

    return render(request, 'core/dashboard/partials/user_quick_actions.html', context)


@login_required
def approve_car_listing(request, car_id):
    """Approve a car listing (Admin only)"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    car = get_object_or_404(Car, id=car_id)
    car.is_approved = True
    car.approval_date = timezone.now()
    car.save()
    
    messages.success(request, f'Car listing "{car.title}" has been approved.')
    
    if request.headers.get('HX-Request'):
        return JsonResponse({'status': 'approved'})
    
    return redirect('core:admin_listings')


@login_required
def reject_car_listing(request, car_id):
    """Reject a car listing (Admin only)"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    car = get_object_or_404(Car, id=car_id)
    # For now, we'll just delete rejected listings
    # In a real system, you might want to keep them with a 'rejected' status
    car.delete()
    
    messages.success(request, 'Car listing has been rejected and removed.')
    
    if request.headers.get('HX-Request'):
        return JsonResponse({'status': 'rejected'})
    
    return redirect('core:admin_listings')


@login_required
def approve_vendor(request, vendor_id):
    """Approve a vendor (Admin only)"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.is_approved = True
    vendor.approval_date = timezone.now()
    vendor.save()

    messages.success(request, f'Vendor "{vendor.company_name}" has been approved.')

    if request.headers.get('HX-Request'):
        return JsonResponse({'status': 'approved'})

    return redirect('core:admin_vendors')


@login_required
def respond_to_inquiry(request):
    """HTMX endpoint for responding to inquiries"""
    if request.method != 'POST' or request.user.role != 'vendor':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    inquiry_id = request.POST.get('inquiry_id')
    response_text = request.POST.get('response')
    status = request.POST.get('status')
    send_email = request.POST.get('send_email') == 'on'

    try:
        vendor = request.user.vendor
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, car__vendor=vendor)

        # Since response is not a model field, we'll handle it differently
        # For now, we'll just update the status and add a note to the message
        inquiry.status = status
        inquiry.save()

        # TODO: Implement a proper response system with a separate model

        # TODO: Send email notification if send_email is True

        messages.success(request, 'Response sent successfully!')

        # Return updated inquiry list
        inquiries = Inquiry.objects.filter(car__vendor=vendor).order_by('-created_at')
        from django.core.paginator import Paginator
        paginator = Paginator(inquiries, 10)
        inquiries_page = paginator.get_page(1)

        context = {
            'vendor': vendor,
            'inquiries': inquiries_page,
            'vendor_cars': Car.objects.filter(vendor=vendor),
        }

        return render(request, 'core/dashboard/partials/inquiry_list.html', context)

    except Vendor.DoesNotExist:
        return JsonResponse({'error': 'Vendor profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def update_inquiry_status(request):
    """HTMX endpoint for updating inquiry status"""
    if request.method != 'POST' or request.user.role != 'vendor':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    inquiry_id = request.POST.get('inquiry_id')
    status = request.POST.get('status')

    try:
        vendor = request.user.vendor
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, car__vendor=vendor)

        inquiry.status = status
        if status == 'resolved' and not inquiry.response_date:
            inquiry.response_date = timezone.now()
        inquiry.save()

        messages.success(request, f'Inquiry status updated to {inquiry.get_status_display()}!')

        # Return updated inquiry card
        context = {'inquiry': inquiry}
        return render(request, 'core/dashboard/partials/inquiry_card.html', context)

    except Vendor.DoesNotExist:
        return JsonResponse({'error': 'Vendor profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== EXPORT FUNCTIONALITY =====

@login_required
def export_users_csv(request):
    """Export users data to CSV format"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Role', 'Phone', 'Date Joined', 'Is Active', 'Is Verified'])

    users = User.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.role,
            user.phone,
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.is_active,
            user.is_verified
        ])

    return response


@login_required
def export_cars_csv(request):
    """Export car listings data to CSV format"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cars_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Brand', 'Model', 'Year', 'Price', 'Mileage', 'Fuel Type', 'Transmission', 'Condition', 'Vendor', 'Is Approved', 'Created At'])

    cars = Car.objects.select_related('brand', 'model', 'vendor').all().order_by('-created_at')
    for car in cars:
        writer.writerow([
            car.id,
            car.brand.name if car.brand else '',
            car.model.name if car.model else '',
            car.year,
            car.price,
            car.mileage,
            car.fuel_type,
            car.transmission,
            car.condition,
            car.vendor.company_name if car.vendor else '',
            car.is_approved,
            car.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response


@login_required
def export_vendors_csv(request):
    """Export vendors data to CSV format"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendors_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Company Name', 'User Email', 'Business License', 'Website', 'Is Approved', 'Approval Date', 'Created At'])

    vendors = Vendor.objects.select_related('user').all().order_by('-created_at')
    for vendor in vendors:
        writer.writerow([
            vendor.id,
            vendor.company_name,
            vendor.user.email,
            vendor.business_license,
            vendor.website,
            vendor.is_approved,
            vendor.approval_date.strftime('%Y-%m-%d %H:%M:%S') if vendor.approval_date else '',
            vendor.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response


@login_required
def export_analytics_json(request):
    """Export analytics data to JSON format"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Gather analytics data
    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_vendors = Vendor.objects.count()
    total_inquiries = Inquiry.objects.count()

    # Monthly data for the last 12 months
    monthly_data = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'users': User.objects.filter(date_joined__range=[month_start, month_end]).count(),
            'cars': Car.objects.filter(created_at__range=[month_start, month_end]).count(),
            'vendors': Vendor.objects.filter(created_at__range=[month_start, month_end]).count(),
        })

    # Top brands
    top_brands = list(CarBrand.objects.annotate(
        car_count=Count('car')
    ).order_by('-car_count')[:10].values('name', 'car_count'))

    analytics_data = {
        'export_date': timezone.now().isoformat(),
        'summary': {
            'total_users': total_users,
            'total_cars': total_cars,
            'total_vendors': total_vendors,
            'total_inquiries': total_inquiries,
        },
        'monthly_data': monthly_data,
        'top_brands': top_brands,
    }

    response = HttpResponse(
        json.dumps(analytics_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="analytics_export.json"'

    return response


# ===== NOTIFICATION SYSTEM =====

@login_required
def notifications_view(request):
    """Display user notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }

    return render(request, 'core/dashboard/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read via HTMX"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_read()

        return JsonResponse({'success': True, 'message': 'Notification marked as read'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read via HTMX"""
    if request.method == 'POST':
        try:
            Notification.objects.filter(recipient=request.user, is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )

            return JsonResponse({'success': True, 'message': 'All notifications marked as read'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def notifications_count_htmx(request):
    """Get unread notifications count via HTMX"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    context = {'unread_count': unread_count}
    return render(request, 'core/dashboard/partials/notification_count.html', context)


def create_notification(recipient, title, message, notification_type='info', action_url='', action_text=''):
    """Helper function to create notifications"""
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        action_url=action_url,
        action_text=action_text
    )


@login_required
def activity_logs_view(request):
    """View user's activity logs"""
    from .activity_manager import ActivityManager

    # Get user's activities
    activities = ActivityManager.get_user_activities(request.user, limit=100)

    # Filter by action if specified
    action_filter = request.GET.get('action')
    if action_filter:
        activities = activities.filter(action=action_filter)

    # Get available actions for filter
    available_actions = ActivityLog.objects.filter(user=request.user).values_list('action', flat=True).distinct()

    context = {
        'activities': activities,
        'available_actions': available_actions,
        'current_filter': action_filter,
    }

    return render(request, 'core/dashboard/activity_logs.html', context)


@login_required
def admin_activity_logs_view(request):
    """Admin view for all activity logs"""
    if not request.user.role == 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    from .activity_manager import ActivityManager

    # Get system activities
    activities = ActivityManager.get_system_activities(limit=200)

    # Apply filters
    user_filter = request.GET.get('user')
    action_filter = request.GET.get('action')
    date_filter = request.GET.get('date')

    if user_filter:
        try:
            user = User.objects.get(username=user_filter)
            activities = activities.filter(user=user)
        except User.DoesNotExist:
            pass

    if action_filter:
        activities = activities.filter(action=action_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            activities = activities.filter(timestamp__date=filter_date)
        except ValueError:
            pass

    # Get filter options
    available_actions = ActivityLog.objects.values_list('action', flat=True).distinct()
    recent_users = User.objects.filter(activity_logs__isnull=False).distinct()[:20]

    context = {
        'activities': activities,
        'available_actions': available_actions,
        'recent_users': recent_users,
        'current_filters': {
            'user': user_filter,
            'action': action_filter,
            'date': date_filter,
        }
    }

    return render(request, 'core/dashboard/admin_activity_logs.html', context)


@login_required
def admin_audit_logs_view(request):
    """Admin view for audit logs"""
    if not request.user.role == 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    from .activity_manager import AuditManager

    # Get audit logs
    audit_logs = AuditManager.get_audit_trail(limit=200)

    # Apply filters
    action_filter = request.GET.get('action_type')
    severity_filter = request.GET.get('severity')
    table_filter = request.GET.get('table_name')

    if action_filter:
        audit_logs = audit_logs.filter(action_type=action_filter)

    if severity_filter:
        audit_logs = audit_logs.filter(severity=severity_filter)

    if table_filter:
        audit_logs = audit_logs.filter(table_name=table_filter)

    # Get filter options
    available_actions = AuditLog.objects.values_list('action_type', flat=True).distinct()
    available_tables = AuditLog.objects.exclude(table_name='').values_list('table_name', flat=True).distinct()

    context = {
        'audit_logs': audit_logs,
        'available_actions': available_actions,
        'available_tables': available_tables,
        'severity_choices': AuditLog.SEVERITY_LEVELS,
        'current_filters': {
            'action_type': action_filter,
            'severity': severity_filter,
            'table_name': table_filter,
        }
    }

    return render(request, 'core/dashboard/admin_audit_logs.html', context)


@login_required
def notification_preferences_view(request):
    """View and update notification preferences"""
    from .notification_manager import NotificationManager

    preferences = NotificationManager.get_user_preferences(request.user)

    if request.method == 'POST':
        # Update preferences
        preferences.email_enabled = request.POST.get('email_enabled') == 'on'
        preferences.email_order_updates = request.POST.get('email_order_updates') == 'on'
        preferences.email_import_updates = request.POST.get('email_import_updates') == 'on'
        preferences.email_inquiry_responses = request.POST.get('email_inquiry_responses') == 'on'
        preferences.email_marketing = request.POST.get('email_marketing') == 'on'
        preferences.email_security_alerts = request.POST.get('email_security_alerts') == 'on'

        preferences.sms_enabled = request.POST.get('sms_enabled') == 'on'
        preferences.sms_order_updates = request.POST.get('sms_order_updates') == 'on'
        preferences.sms_import_updates = request.POST.get('sms_import_updates') == 'on'
        preferences.sms_security_alerts = request.POST.get('sms_security_alerts') == 'on'

        preferences.push_enabled = request.POST.get('push_enabled') == 'on'
        preferences.push_order_updates = request.POST.get('push_order_updates') == 'on'
        preferences.push_import_updates = request.POST.get('push_import_updates') == 'on'
        preferences.push_inquiry_responses = request.POST.get('push_inquiry_responses') == 'on'
        preferences.push_marketing = request.POST.get('push_marketing') == 'on'

        preferences.in_app_enabled = request.POST.get('in_app_enabled') == 'on'
        preferences.in_app_order_updates = request.POST.get('in_app_order_updates') == 'on'
        preferences.in_app_import_updates = request.POST.get('in_app_import_updates') == 'on'
        preferences.in_app_inquiry_responses = request.POST.get('in_app_inquiry_responses') == 'on'
        preferences.in_app_system_updates = request.POST.get('in_app_system_updates') == 'on'

        preferences.digest_frequency = request.POST.get('digest_frequency', 'immediate')
        preferences.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'

        if preferences.quiet_hours_enabled:
            quiet_start = request.POST.get('quiet_hours_start')
            quiet_end = request.POST.get('quiet_hours_end')
            if quiet_start:
                preferences.quiet_hours_start = quiet_start
            if quiet_end:
                preferences.quiet_hours_end = quiet_end

        preferences.save()
        messages.success(request, 'Notification preferences updated successfully!')

        if request.headers.get('HX-Request'):
            return JsonResponse({'success': True, 'message': 'Preferences updated!'})

        return redirect('core:notification_preferences')

    context = {
        'preferences': preferences,
    }

    return render(request, 'core/dashboard/notification_preferences.html', context)


@login_required
def admin_notification_queue_view(request):
    """Admin view for notification queue management"""
    if not request.user.role == 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get notification queue
    queue_items = NotificationQueue.objects.all()[:100]

    # Apply filters
    status_filter = request.GET.get('status')
    channel_filter = request.GET.get('channel')

    if status_filter:
        queue_items = queue_items.filter(status=status_filter)

    if channel_filter:
        queue_items = queue_items.filter(channel=channel_filter)

    # Get statistics
    stats = {
        'total': NotificationQueue.objects.count(),
        'pending': NotificationQueue.objects.filter(status='pending').count(),
        'processing': NotificationQueue.objects.filter(status='processing').count(),
        'sent': NotificationQueue.objects.filter(status='sent').count(),
        'failed': NotificationQueue.objects.filter(status='failed').count(),
    }

    context = {
        'queue_items': queue_items,
        'stats': stats,
        'status_choices': NotificationQueue.STATUS_CHOICES,
        'channel_choices': NotificationQueue.CHANNEL_CHOICES,
        'current_filters': {
            'status': status_filter,
            'channel': channel_filter,
        }
    }

    return render(request, 'core/dashboard/admin_notification_queue.html', context)


# ===== ADD NEW FUNCTIONALITY =====

@login_required
def add_new_modal(request):
    """Display Add New modal content via HTMX"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    context = {
        'user': request.user,
    }

    return render(request, 'core/dashboard/partials/add_new_modal.html', context)


# ===== NEW ADMIN PAGES =====

@login_required
def admin_import_requests_view(request):
    """Admin import requests management view with enhanced filtering and search"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Base queryset with optimized select_related
    import_requests = ImportRequest.objects.select_related('customer').all().order_by('-created_at')

    # Apply filters
    import_requests = apply_import_request_filters(request, import_requests)

    # Calculate stats (unfiltered for dashboard overview)
    total_imports = ImportRequest.objects.count()
    pending_imports = ImportRequest.objects.filter(status='pending').count()
    in_transit_imports = ImportRequest.objects.filter(status__in=['processing', 'shipped']).count()
    completed_imports = ImportRequest.objects.filter(status='completed').count()

    # Get unique values for filter dropdowns
    brands = ImportRequest.objects.values_list('brand', flat=True).distinct().order_by('brand')
    countries = ImportRequest.objects.values_list('origin_country', flat=True).distinct().order_by('origin_country')

    context = {
        'import_requests': import_requests[:20],  # Limit to 20 for performance
        'total_imports': total_imports,
        'pending_imports': pending_imports,
        'in_transit_imports': in_transit_imports,
        'completed_imports': completed_imports,
        'status_choices': ImportRequest.STATUS_CHOICES,
        'brands': brands,
        'countries': countries,
        # Preserve filter values
        'current_status': request.GET.get('status', ''),
        'current_search': request.GET.get('search', ''),
        'current_brand': request.GET.get('brand', ''),
        'current_country': request.GET.get('country', ''),
        'current_date_from': request.GET.get('date_from', ''),
        'current_date_to': request.GET.get('date_to', ''),
    }

    return render(request, 'core/dashboard/admin_import_requests.html', context)


@login_required
def admin_import_requests_table_partial(request):
    """Return just the import requests table for HTMX updates with filtering"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Base queryset with optimized select_related
    import_requests = ImportRequest.objects.select_related('customer').all().order_by('-created_at')

    # Apply the same filters as the main view
    import_requests = apply_import_request_filters(request, import_requests)

    context = {
        'import_requests': import_requests[:20],  # Limit to 20 for performance
    }

    return render(request, 'core/dashboard/partials/admin_import_requests_table.html', context)


@login_required
def admin_import_requests_export(request):
    """Export import requests to CSV with current filters applied"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Get filtered queryset
    import_requests = ImportRequest.objects.select_related('customer').all().order_by('-created_at')
    import_requests = apply_import_request_filters(request, import_requests)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="import_requests.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Order ID', 'Customer Name', 'Customer Email', 'Brand', 'Model', 'Year',
        'Origin Country', 'Status', 'Budget Min', 'Budget Max', 'Estimated Cost',
        'Created Date', 'Updated Date', 'Tracking Number'
    ])

    # Write data
    for request_obj in import_requests:
        writer.writerow([
            f"#{request_obj.id:05d}",
            request_obj.customer.get_full_name() or request_obj.customer.username,
            request_obj.customer.email,
            request_obj.brand,
            request_obj.model,
            request_obj.year,
            request_obj.origin_country,
            request_obj.get_status_display(),
            request_obj.budget_min,
            request_obj.budget_max,
            request_obj.estimated_cost or '',
            request_obj.created_at.strftime('%Y-%m-%d %H:%M'),
            request_obj.updated_at.strftime('%Y-%m-%d %H:%M'),
            request_obj.tracking_number or ''
        ])

    return response


@login_required
def admin_import_requests_refresh(request):
    """Refresh import requests table while maintaining current filters"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Simply return the updated table partial with current filters
    return admin_import_requests_table_partial(request)


@login_required
def admin_tracking_management_table_partial(request):
    """Return just the tracking management table for HTMX updates"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Get import orders with tracking information
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        import_orders = import_orders.filter(status=status_filter)

    context = {
        'import_orders': import_orders[:20],  # Limit to 20 for performance
    }

    return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', context)


# ===== IMPORT ORDER MANAGEMENT VIEWS =====

@login_required
def admin_import_order_add_modal(request):
    """Show add import order modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Get all customers for the dropdown
    customers = User.objects.filter(role='customer').order_by('first_name', 'last_name', 'username')

    context = {
        'customers': customers,
    }

    return render(request, 'core/modals/admin_import_order_add.html', context)


@login_required
def admin_import_order_add(request):
    """Handle adding new import order"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        try:
            # Get form data
            customer_id = request.POST.get('customer')
            brand = request.POST.get('brand')
            model = request.POST.get('model')
            year = request.POST.get('year')
            color = request.POST.get('color', '')
            engine_size = request.POST.get('engine_size', '')
            fuel_type = request.POST.get('fuel_type', '')
            total_cost = request.POST.get('total_cost')
            initial_status = request.POST.get('initial_status', 'confirmed')
            admin_notes = request.POST.get('admin_notes', '')

            # Validate required fields
            if not all([customer_id, brand, model, year, total_cost]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                    'import_orders': ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
                })

            # Get customer
            try:
                customer = User.objects.get(id=customer_id, role='customer')
            except User.DoesNotExist:
                messages.error(request, 'Selected customer not found.')
                return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                    'import_orders': ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
                })

            # Generate unique order number
            import uuid
            order_number = f"IO{uuid.uuid4().hex[:8].upper()}"
            while ImportOrder.objects.filter(order_number=order_number).exists():
                order_number = f"IO{uuid.uuid4().hex[:8].upper()}"

            # Create import order
            import_order = ImportOrder.objects.create(
                order_number=order_number,
                customer=customer,
                brand=brand,
                model=model,
                year=int(year),
                color=color,
                engine_size=engine_size,
                fuel_type=fuel_type,
                total_cost=float(total_cost),
                status=initial_status,
                admin_notes=admin_notes,
                created_by=request.user
            )

            # Create initial status history entry
            ImportOrderStatusHistory.objects.create(
                import_order=import_order,
                previous_status='',
                new_status=initial_status,
                changed_by=request.user,
                change_reason=f'Initial order creation with status: {initial_status}',
                admin_notes=admin_notes,
                customer_notification_sent=False
            )

            messages.success(request, f'Import order {order_number} created successfully!')

            # Return updated table
            import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
            return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                'import_orders': import_orders
            })

        except Exception as e:
            messages.error(request, f'Error creating import order: {str(e)}')
            import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
            return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                'import_orders': import_orders
            })

    return HttpResponse('Method not allowed', status=405)


@login_required
def admin_import_order_edit_modal(request, order_id):
    """Show edit import order modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    try:
        import_order = get_object_or_404(ImportOrder, id=order_id)

        # Get status choices for the dropdown
        status_choices = ImportOrder.STATUS_CHOICES

        context = {
            'import_order': import_order,
            'status_choices': status_choices,
        }

        return render(request, 'core/modals/admin_import_order_edit.html', context)

    except ImportOrder.DoesNotExist:
        return HttpResponse('Import order not found', status=404)


@login_required
def admin_import_order_edit(request, order_id):
    """Handle editing import order"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        try:
            import_order = get_object_or_404(ImportOrder, id=order_id)

            # Get form data
            brand = request.POST.get('brand')
            model = request.POST.get('model')
            year = request.POST.get('year')
            color = request.POST.get('color', '')
            engine_size = request.POST.get('engine_size', '')
            fuel_type = request.POST.get('fuel_type', '')
            total_cost = request.POST.get('total_cost')
            status = request.POST.get('status')
            chassis_number = request.POST.get('chassis_number', '')
            bill_of_lading = request.POST.get('bill_of_lading', '')
            vessel_name = request.POST.get('vessel_name', '')
            estimated_arrival = request.POST.get('estimated_arrival')
            admin_notes = request.POST.get('admin_notes', '')

            # Validate required fields
            if not all([brand, model, year, total_cost, status]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                    'import_orders': ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
                })

            # Store previous status for history
            previous_status = import_order.status

            # Update import order
            import_order.brand = brand
            import_order.model = model
            import_order.year = int(year)
            import_order.color = color
            import_order.engine_size = engine_size
            import_order.fuel_type = fuel_type
            import_order.total_cost = float(total_cost)
            import_order.status = status
            import_order.chassis_number = chassis_number
            import_order.bill_of_lading = bill_of_lading
            import_order.vessel_name = vessel_name
            import_order.admin_notes = admin_notes

            if estimated_arrival:
                from datetime import datetime
                import_order.estimated_arrival = datetime.strptime(estimated_arrival, '%Y-%m-%d').date()

            import_order.save()

            # Create status history entry if status changed
            if previous_status != status:
                ImportOrderStatusHistory.objects.create(
                    import_order=import_order,
                    previous_status=previous_status,
                    new_status=status,
                    changed_by=request.user,
                    change_reason=f'Status updated via edit modal from {previous_status} to {status}',
                    admin_notes=admin_notes,
                    customer_notification_sent=False
                )

            messages.success(request, f'Import order {import_order.order_number} updated successfully!')

            # Return updated table
            import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
            return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                'import_orders': import_orders
            })

        except Exception as e:
            messages.error(request, f'Error updating import order: {str(e)}')
            import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')[:20]
            return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', {
                'import_orders': import_orders
            })

    return HttpResponse('Method not allowed', status=405)


# ===== TRACKING MANAGEMENT MODAL VIEWS (Placeholders) =====

@login_required
def admin_tracking_status_modal(request, order_id):
    """Show tracking status update modal (placeholder)"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Placeholder - return simple modal
    return HttpResponse('<div class="modal">Status update modal for order {}</div>'.format(order_id))


@login_required
def admin_tracking_timeline_modal(request, order_id):
    """Show tracking timeline modal with complete status history"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    try:
        import_order = get_object_or_404(ImportOrder, id=order_id)

        # Get status history ordered by creation date (newest first)
        status_history = import_order.status_history.all().order_by('-created_at')

        context = {
            'import_order': import_order,
            'status_history': status_history,
        }

        return render(request, 'core/modals/admin_import_order_timeline.html', context)

    except ImportOrder.DoesNotExist:
        return HttpResponse('Import order not found', status=404)


@login_required
def admin_tracking_location_modal(request, order_id):
    """Show tracking location modal with geolocation features"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    try:
        import_order = get_object_or_404(ImportOrder, id=order_id)

        context = {
            'import_order': import_order,
        }

        return render(request, 'core/modals/admin_import_order_location.html', context)

    except ImportOrder.DoesNotExist:
        return HttpResponse('Import order not found', status=404)


@login_required
def admin_tracking_details_modal(request, order_id):
    """Show comprehensive tracking details modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    try:
        import_order = get_object_or_404(ImportOrder, id=order_id)

        context = {
            'import_order': import_order,
        }

        return render(request, 'core/modals/admin_import_order_view.html', context)

    except ImportOrder.DoesNotExist:
        return HttpResponse('Import order not found', status=404)





@login_required
def admin_queries_view(request):
    """Admin queries/inquiries management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    inquiries = Inquiry.objects.all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        inquiries = inquiries.filter(status=status_filter)

    # Calculate stats
    total_inquiries = Inquiry.objects.count()
    new_inquiries = Inquiry.objects.filter(status='new').count()
    in_progress_inquiries = Inquiry.objects.filter(status='in_progress').count()
    resolved_inquiries = Inquiry.objects.filter(status='resolved').count()

    context = {
        'inquiries': inquiries[:20],
        'total_inquiries': total_inquiries,
        'new_inquiries': new_inquiries,
        'in_progress_inquiries': in_progress_inquiries,
        'resolved_inquiries': resolved_inquiries,
        'current_filter': status_filter,
    }

    return render(request, 'core/dashboard/admin_queries.html', context)


@login_required
def admin_content_management_view(request):
    """Admin content management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    blog_posts = BlogPost.objects.all().order_by('-created_at')
    testimonials = Testimonial.objects.all().order_by('-created_at')

    # Calculate stats
    total_posts = BlogPost.objects.count()
    published_posts = BlogPost.objects.filter(is_published=True).count()
    draft_posts = BlogPost.objects.filter(is_published=False).count()
    total_testimonials = Testimonial.objects.count()

    context = {
        'blog_posts': blog_posts[:10],
        'testimonials': testimonials[:10],
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_testimonials': total_testimonials,
    }

    return render(request, 'core/dashboard/admin_content_management.html', context)


@login_required
def admin_system_settings_view(request):
    """Admin system settings view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    settings = SystemSetting.objects.all().order_by('key')

    context = {
        'settings': settings,
    }

    return render(request, 'core/dashboard/admin_system_settings.html', context)


@login_required
def admin_spare_shop_view(request):
    """Admin spare shop management view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    spare_parts = SparePart.objects.select_related('category_new', 'supplier').all().order_by('-created_at')

    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        spare_parts = spare_parts.filter(category_new_id=category_filter)

    # Filter by availability
    availability_filter = request.GET.get('availability')
    if availability_filter == 'in_stock':
        spare_parts = spare_parts.filter(stock_quantity__gt=0)
    elif availability_filter == 'low_stock':
        spare_parts = spare_parts.filter(stock_quantity__lte=10, stock_quantity__gt=0)
    elif availability_filter == 'out_of_stock':
        spare_parts = spare_parts.filter(stock_quantity=0)

    # Calculate stats
    total_parts = SparePart.objects.count()
    in_stock_parts = SparePart.objects.filter(stock_quantity__gt=0).count()
    low_stock_parts = SparePart.objects.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    out_of_stock_parts = SparePart.objects.filter(stock_quantity=0).count()

    # Get categories for filter
    categories = SparePartCategory.objects.all()

    # Get recent orders
    recent_orders = Order.objects.filter(
        items__spare_part__isnull=False
    ).distinct().order_by('-created_at')[:5]

    context = {
        'spare_parts': spare_parts[:20],
        'total_parts': total_parts,
        'in_stock_parts': in_stock_parts,
        'low_stock_parts': low_stock_parts,
        'out_of_stock_parts': out_of_stock_parts,
        'categories': categories,
        'recent_orders': recent_orders,
        'current_category': category_filter,
        'current_availability': availability_filter,
    }

    return render(request, 'core/dashboard/admin_spare_shop.html', context)


@login_required
def admin_tracking_management_view(request):
    """Admin tracking management view for 7-stage import workflow"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get import orders with tracking information
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        import_orders = import_orders.filter(status=status_filter)

    # Define workflow stages for the UI
    workflow_stages = [
        {'key': 'confirmed', 'name': 'Confirmed', 'icon': 'fas fa-check-circle', 'color': 'blue'},
        {'key': 'auction_won', 'name': 'Auction Won', 'icon': 'fas fa-gavel', 'color': 'green'},
        {'key': 'shipped', 'name': 'Shipped', 'icon': 'fas fa-ship', 'color': 'indigo'},
        {'key': 'in_transit', 'name': 'In Transit', 'icon': 'fas fa-route', 'color': 'yellow'},
        {'key': 'arrived_docked', 'name': 'Arrived - Docked', 'icon': 'fas fa-anchor', 'color': 'purple'},
        {'key': 'under_clearance', 'name': 'Under Clearance', 'icon': 'fas fa-file-signature', 'color': 'orange'},
        {'key': 'registered', 'name': 'Registered', 'icon': 'fas fa-certificate', 'color': 'teal'},
        {'key': 'ready_for_dispatch', 'name': 'Ready for Dispatch', 'icon': 'fas fa-truck', 'color': 'pink'},
        {'key': 'delivered', 'name': 'Delivered', 'icon': 'fas fa-flag-checkered', 'color': 'green'},
    ]

    # Calculate tracking stats
    total_orders = ImportOrder.objects.count()
    confirmed_orders = ImportOrder.objects.filter(status='confirmed').count()
    in_transit_orders = ImportOrder.objects.filter(status__in=['shipped', 'in_transit']).count()
    arrived_orders = ImportOrder.objects.filter(status='arrived_docked').count()
    completed_orders = ImportOrder.objects.filter(status='delivered').count()

    context = {
        'import_orders': import_orders[:20],
        'total_orders': total_orders,
        'confirmed_orders': confirmed_orders,
        'in_transit_orders': in_transit_orders,
        'arrived_orders': arrived_orders,
        'completed_orders': completed_orders,
        'workflow_stages': workflow_stages,
        'current_filter': status_filter,
    }

    return render(request, 'core/dashboard/admin_tracking_management.html', context)


@login_required
def update_tracking_status(request, order_id):
    """Update tracking status for an import order via HTMX"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        try:
            order = get_object_or_404(ImportOrder, id=order_id)
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            # Update order status
            old_status = order.status
            order.status = new_status
            order.save()

            # Create status history entry
            ImportOrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                notes=notes,
                updated_by=request.user
            )

            # Create notification for customer
            create_notification(
                recipient=order.customer,
                title=f"Import Order Status Updated",
                message=f"Your import order #{order.id:05d} status has been updated to {new_status.replace('_', ' ').title()}",
                notification_type='info',
                action_url=f"/dashboard/orders/{order.id}/",
                action_text="View Order"
            )

            return JsonResponse({
                'success': True,
                'message': f'Status updated from {old_status} to {new_status}',
                'new_status': new_status
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


# ===== IMPORT REQUEST MODAL VIEWS =====

@login_required
def admin_import_request_add_modal(request):
    """Show add import request modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    customers = User.objects.filter(role='customer').order_by('username')

    context = {
        'customers': customers,
    }

    return render(request, 'core/modals/admin_import_request_add.html', context)


@login_required
def admin_import_request_add(request):
    """Add new import request via HTMX"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    if request.method == 'POST':
        try:
            # Create new import request
            import_request = ImportRequest.objects.create(
                customer_id=request.POST.get('customer'),
                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                year=int(request.POST.get('year')),
                preferred_color=request.POST.get('preferred_color', ''),
                origin_country=request.POST.get('origin_country'),
                budget_min=float(request.POST.get('budget_min')),
                budget_max=float(request.POST.get('budget_max')),
                estimated_cost=float(request.POST.get('estimated_cost', 0)) or None,
                special_requirements=request.POST.get('special_requirements', ''),
                admin_notes=request.POST.get('admin_notes', ''),
                status='pending'
            )

            # Create notification for customer
            create_notification(
                recipient=import_request.customer,
                title="New Import Request Created",
                message=f"Your import request for {import_request.year} {import_request.brand} {import_request.model} has been created.",
                notification_type='info',
                action_url=f"/dashboard/import-requests/{import_request.id}/",
                action_text="View Request"
            )

            messages.success(request, f'Import request #{import_request.id:05d} created successfully.')

            # Return updated table
            return admin_import_requests_table_partial(request)

        except Exception as e:
            messages.error(request, f'Error creating import request: {str(e)}')
            return admin_import_requests_table_partial(request)

    return HttpResponse('Invalid request method', status=405)


@login_required
def admin_import_request_view_modal(request, request_id):
    """Show view import request modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    import_request = get_object_or_404(ImportRequest, id=request_id)

    context = {
        'import_request': import_request,
        'status_choices': ImportRequest.STATUS_CHOICES,
    }

    return render(request, 'core/modals/admin_import_request_view.html', context)


@login_required
def admin_import_request_edit_modal(request, request_id):
    """Show edit import request modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    import_request = get_object_or_404(ImportRequest, id=request_id)
    customers = User.objects.filter(role='customer').order_by('username')

    context = {
        'import_request': import_request,
        'customers': customers,
        'status_choices': ImportRequest.STATUS_CHOICES,
    }

    return render(request, 'core/modals/admin_import_request_edit.html', context)


@login_required
def admin_import_request_edit(request, request_id):
    """Edit import request via HTMX"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    if request.method == 'POST':
        try:
            import_request = get_object_or_404(ImportRequest, id=request_id)

            # Update import request
            import_request.customer_id = request.POST.get('customer')
            import_request.brand = request.POST.get('brand')
            import_request.model = request.POST.get('model')
            import_request.year = int(request.POST.get('year'))
            import_request.preferred_color = request.POST.get('preferred_color', '')
            import_request.origin_country = request.POST.get('origin_country')
            import_request.budget_min = float(request.POST.get('budget_min'))
            import_request.budget_max = float(request.POST.get('budget_max'))
            import_request.status = request.POST.get('status')

            estimated_cost = request.POST.get('estimated_cost')
            if estimated_cost:
                import_request.estimated_cost = float(estimated_cost)

            estimated_delivery = request.POST.get('estimated_delivery')
            if estimated_delivery:
                from datetime import datetime
                import_request.estimated_delivery = datetime.strptime(estimated_delivery, '%Y-%m-%d').date()

            import_request.tracking_number = request.POST.get('tracking_number', '')
            import_request.special_requirements = request.POST.get('special_requirements', '')
            import_request.admin_notes = request.POST.get('admin_notes', '')

            import_request.save()

            # Create notification for customer if status changed
            if 'status' in request.POST:
                create_notification(
                    recipient=import_request.customer,
                    title="Import Request Updated",
                    message=f"Your import request #{import_request.id:05d} has been updated. Status: {import_request.get_status_display()}",
                    notification_type='info',
                    action_url=f"/dashboard/import-requests/{import_request.id}/",
                    action_text="View Request"
                )

            messages.success(request, f'Import request #{import_request.id:05d} updated successfully.')

            # Return updated table
            return admin_import_requests_table_partial(request)

        except Exception as e:
            messages.error(request, f'Error updating import request: {str(e)}')
            return admin_import_requests_table_partial(request)

    return HttpResponse('Invalid request method', status=405)


@login_required
def admin_import_request_delete_modal(request, request_id):
    """Show delete import request confirmation modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    import_request = get_object_or_404(ImportRequest, id=request_id)

    context = {
        'import_request': import_request,
    }

    return render(request, 'core/modals/admin_import_request_delete.html', context)


@login_required
def admin_import_request_delete(request, request_id):
    """Delete import request via HTMX"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    if request.method == 'DELETE':
        try:
            import_request = get_object_or_404(ImportRequest, id=request_id)
            customer = import_request.customer
            request_info = f"#{import_request.id:05d} - {import_request.year} {import_request.brand} {import_request.model}"

            # Delete the import request
            import_request.delete()

            # Create notification for customer
            create_notification(
                recipient=customer,
                title="Import Request Cancelled",
                message=f"Your import request {request_info} has been cancelled by admin.",
                notification_type='warning'
            )

            messages.success(request, f'Import request {request_info} deleted successfully.')

            # Return updated table
            return admin_import_requests_table_partial(request)

        except Exception as e:
            messages.error(request, f'Error deleting import request: {str(e)}')
            return admin_import_requests_table_partial(request)

    return HttpResponse('Invalid request method', status=405)


@login_required
def admin_import_request_track(request, request_id):
    """Move import request to tracking management"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    if request.method == 'POST':
        try:
            import_request = get_object_or_404(ImportRequest, id=request_id)

            # Check if already has an import order
            if hasattr(import_request, 'import_order'):
                messages.warning(request, f'Import request #{import_request.id:05d} is already being tracked.')
                return admin_import_requests_table_partial(request)

            # Create import order for tracking with comprehensive data transfer
            import_order = ImportOrder.objects.create(
                import_request=import_request,
                customer=import_request.customer,
                brand=import_request.brand,
                model=import_request.model,
                year=import_request.year,
                color=import_request.preferred_color or '',
                origin_country=import_request.origin_country,
                quotation_amount=import_request.estimated_cost or 0,
                total_cost=import_request.estimated_cost or 0,
                special_requirements=import_request.special_requirements,
                admin_notes=import_request.admin_notes,
                status='confirmed',  # Start with confirmed status in 7-stage workflow
                payment_status='pending'
            )

            # Keep import request as completed but mark it as being tracked
            import_request.tracking_number = import_order.order_number
            import_request.save()

            # Create initial status history entry with proper field names
            ImportOrderStatusHistory.objects.create(
                import_order=import_order,
                previous_status='',  # No previous status for initial entry
                new_status='confirmed',
                changed_by=request.user,
                change_reason='Import request moved to tracking management - 7-stage workflow initiated',
                admin_notes=f'Converted from Import Request #{import_request.id:05d}',
                customer_notification_sent=True,
                actual_date=timezone.now().date()
            )

            # Create notification for customer
            create_notification(
                recipient=import_request.customer,
                title="Import Request Now Being Tracked",
                message=f"Your import request #{import_request.id:05d} is now being tracked. Order number: {import_order.order_number}",
                notification_type='success',
                action_url=f"/import/tracking/{import_order.order_number}/",
                action_text="Track Order"
            )

            messages.success(request, f'Import request #{import_request.id:05d} moved to tracking management. Order number: {import_order.order_number}')

            # For HTMX requests, return a response that triggers both table updates
            if request.headers.get('HX-Request'):
                # Return the import requests table with HX-Trigger header to update tracking table
                response = admin_import_requests_table_partial(request)
                response['HX-Trigger'] = 'updateTrackingTable'
                return response
            else:
                # For non-HTMX requests, redirect to import requests page
                return redirect('core:admin_import_requests')

        except Exception as e:
            messages.error(request, f'Error moving to tracking: {str(e)}')
            return admin_import_requests_table_partial(request)

    return HttpResponse('Invalid request method', status=405)


@login_required
def admin_import_request_status_modal(request, request_id):
    """Show status update modal"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    import_request = get_object_or_404(ImportRequest, id=request_id)

    context = {
        'import_request': import_request,
    }

    return render(request, 'core/modals/admin_import_request_status_update.html', context)


@login_required
def admin_import_request_status_update(request, request_id):
    """Update import request status with workflow management"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        try:
            import_request = get_object_or_404(ImportRequest, id=request_id)
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            # Define 6-stage status workflow (removed shipped and arrived)
            status_workflow = {
                'pending': ['on_quotation', 'cancelled'],
                'on_quotation': ['processing', 'pending', 'cancelled'],
                'processing': ['fee_paid', 'on_quotation', 'cancelled'],
                'fee_paid': ['completed', 'processing', 'cancelled'],
                'completed': ['fee_paid'],  # Allow going back for corrections
                'cancelled': ['pending']   # Allow reactivation
            }

            # Validate status transition
            current_status = import_request.status
            if new_status not in status_workflow.get(current_status, []):
                messages.error(request, f'Invalid status transition from {current_status} to {new_status}')
                return admin_import_requests_view(request)

            # Update status
            old_status = import_request.status
            import_request.status = new_status
            import_request.save()

            # Create notification for customer
            status_messages = {
                'pending': 'Your import request is pending review.',
                'on_quotation': 'We are preparing a quotation for your import request.',
                'processing': 'Your import request is now being processed.',
                'fee_paid': 'Payment received. Your order is being prepared for import.',
                'completed': 'Your import request has been completed successfully.',
                'cancelled': 'Your import request has been cancelled.'
            }

            create_notification(
                recipient=import_request.customer,
                title=f"Import Request Status Updated",
                message=f"Request #{import_request.id:05d}: {status_messages.get(new_status, f'Status updated to {new_status}')}",
                notification_type='info' if new_status != 'cancelled' else 'warning',
                action_url=f"/dashboard/import-requests/{import_request.id}/",
                action_text="View Request"
            )

            messages.success(request, f'Status updated from {old_status} to {new_status}')

            # Return updated table HTML for HTMX
            return admin_import_requests_table_partial(request)

        except Exception as e:
            messages.error(request, f'Error updating status: {str(e)}')
            return admin_import_requests_table_partial(request)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
