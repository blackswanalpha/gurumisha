"""
Dashboard-specific views for Gurumisha Motors
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg, F, Case, When, IntegerField
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
import csv
import json
from io import StringIO

from .models import (
    Car, CarBrand, CarModel, SparePart, ImportRequest, ImportOrder, ImportOrderStatusHistory,
    Inquiry, Testimonial, BlogPost, Vendor, User,
    Supplier, PurchaseOrder, StockMovement, InventoryAlert,
    Order, OrderItem, Payment, SparePartCategory, Notification, SystemSetting,
    ActivityLog, AuditLog, NotificationPreference, NotificationQueue,
    HotDeal, CarRating, PromotionAnalytics, VendorSubscription, FeaturedCarTier,
    ProfileView, VendorAnalytics, UserActivityLog
)
from .dashboard_forms import (
    UserProfileForm, VendorProfileForm, PasswordChangeForm,
    InquiryResponseForm, CarApprovalForm, VendorApprovalForm,
    UserSearchForm, CarSearchForm, VendorSearchForm, AdminCarEditForm,
    UserPreferencesForm, VendorPreferencesForm, BusinessHoursForm
)
from .utils.image_utils import default_image_handler
from .utils.analytics_utils import (
    track_profile_view, log_user_activity, get_analytics_dashboard_data,
    get_vendor_analytics_summary, get_user_analytics_summary
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
    """Enhanced user profile management view with comprehensive form handling"""
    user = request.user
    vendor = None

    if user.role == 'vendor':
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            # Create vendor profile if it doesn't exist
            vendor = Vendor.objects.create(
                user=user,
                company_name=f"{user.first_name} {user.last_name}".strip() or user.username,
                is_approved=False
            )

    if request.method == 'POST':
        # Handle HTMX auto-save requests
        if request.headers.get('X-Auto-Save') == 'true':
            field_name = request.POST.get('field_name')
            field_value = request.POST.get('field_value')

            try:
                # Update specific field
                if hasattr(user, field_name):
                    setattr(user, field_name, field_value)
                    user.save(update_fields=[field_name])

                    # Log the activity
                    log_user_activity(user, 'profile_update', f'Auto-saved {field_name}', request)

                    return JsonResponse({'success': True, 'message': f'{field_name.title()} saved'})
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid field'})

            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})

        # Handle HTMX validation requests
        if request.headers.get('X-Validate-Only') == 'true':
            field_name = request.POST.get('field_name')
            field_value = request.POST.get('field_value')

            # Create a temporary form instance for validation
            form_data = {field_name: field_value}
            temp_form = UserProfileForm(form_data, instance=user)

            if temp_form.is_valid():
                return JsonResponse({'valid': True})
            else:
                errors = temp_form.errors.get(field_name, [])
                error_message = errors[0] if errors else 'Invalid input'
                return JsonResponse({'valid': False, 'message': error_message})

        # Handle regular form submission
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        vendor_form = VendorProfileForm(request.POST, request.FILES, instance=vendor) if vendor else None

        if user_form.is_valid() and (vendor_form is None or vendor_form.is_valid()):
            try:
                # Handle profile picture processing
                if 'profile_picture' in request.FILES:
                    profile_picture = request.FILES['profile_picture']
                    try:
                        # Process the image
                        processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                            profile_picture, 'profile'
                        )

                        # Delete old profile picture if exists
                        if user.profile_picture:
                            default_image_handler.cleanup(user.profile_picture.path)

                        # Save the processed image
                        user.profile_picture.save(filename, processed_file, save=False)

                    except ValueError as e:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'message': str(e)})
                        messages.error(request, str(e))
                        return render(request, 'core/dashboard/profile.html', {
                            'user': user, 'vendor': vendor, 'user_form': user_form, 'vendor_form': vendor_form
                        })

                user_form.save()

                # Handle vendor form if exists
                if vendor_form:
                    vendor = vendor_form.save(commit=False)

                    # Handle company logo processing
                    if 'company_logo' in request.FILES:
                        company_logo = request.FILES['company_logo']
                        try:
                            processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                                company_logo, 'logo'
                            )

                            # Delete old logo if exists
                            if vendor.company_logo:
                                default_image_handler.cleanup(vendor.company_logo.path)

                            vendor.company_logo.save(filename, processed_file, save=False)

                        except ValueError as e:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({'success': False, 'message': str(e)})
                            messages.error(request, str(e))
                            return render(request, 'core/dashboard/profile.html', {
                                'user': user, 'vendor': vendor, 'user_form': user_form, 'vendor_form': vendor_form
                            })

                    # Handle cover image processing
                    if 'cover_image' in request.FILES:
                        cover_image = request.FILES['cover_image']
                        try:
                            processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                                cover_image, 'cover'
                            )

                            # Delete old cover image if exists
                            if vendor.cover_image:
                                default_image_handler.cleanup(vendor.cover_image.path)

                            vendor.cover_image.save(filename, processed_file, save=False)

                        except ValueError as e:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({'success': False, 'message': str(e)})
                            messages.error(request, str(e))
                            return render(request, 'core/dashboard/profile.html', {
                                'user': user, 'vendor': vendor, 'user_form': user_form, 'vendor_form': vendor_form
                            })

                    vendor.save()

                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})

                messages.success(request, 'Profile updated successfully!')
                return redirect('core:profile')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Error updating profile. Please try again.'})
                messages.error(request, 'Error updating profile. Please try again.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                if user_form.errors:
                    errors.update(user_form.errors)
                if vendor_form and vendor_form.errors:
                    errors.update(vendor_form.errors)
                return JsonResponse({'success': False, 'errors': errors})
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileForm(instance=user)
        vendor_form = VendorProfileForm(instance=vendor) if vendor else None

    # Track profile view
    track_profile_view(request, user)

    # Log profile view activity
    log_user_activity(request.user, 'profile_view', f'Viewed profile page', request)

    # Get analytics data
    analytics_data = get_analytics_dashboard_data(user)

    context = {
        'user': user,
        'vendor': vendor,
        'user_form': user_form,
        'vendor_form': vendor_form,
        'analytics_data': analytics_data,
    }

    return render(request, 'core/dashboard/profile.html', context)


@login_required
def vendor_profile_view(request):
    """Dedicated vendor profile management view"""
    if request.user.role != 'vendor':
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('core:dashboard')

    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        # Create vendor profile if it doesn't exist
        vendor = Vendor.objects.create(
            user=request.user,
            company_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            is_approved=False
        )

    if request.method == 'POST':
        vendor_form = VendorProfileForm(request.POST, request.FILES, instance=vendor)

        if vendor_form.is_valid():
            try:
                vendor_form.save()

                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Business profile updated successfully!'})

                messages.success(request, 'Business profile updated successfully!')
                return redirect('core:vendor_profile')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Error updating business profile. Please try again.'})
                messages.error(request, 'Error updating business profile. Please try again.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': vendor_form.errors})
            messages.error(request, 'Please correct the errors below.')
    else:
        vendor_form = VendorProfileForm(instance=vendor)

    context = {
        'vendor': vendor,
        'vendor_form': vendor_form,
        'user': request.user,
    }

    return render(request, 'core/dashboard/vendor_profile.html', context)


@login_required
def change_password_view(request):
    """Handle password change requests"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            try:
                form.save()

                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Password changed successfully! Please log in again.'
                    })

                messages.success(request, 'Password changed successfully! Please log in again.')
                from django.contrib.auth import logout
                logout(request)
                return redirect('core:login')

            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Error changing password. Please try again.'
                    })
                messages.error(request, 'Error changing password. Please try again.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'message': 'Please correct the errors below.'
                })
            messages.error(request, 'Please correct the errors below.')

    # For GET requests or form errors, return to profile page
    return redirect('core:profile')


@login_required
def user_settings_view(request):
    """Enhanced user settings and preferences management"""
    user = request.user
    vendor = None

    if user.role == 'vendor':
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            vendor = Vendor.objects.create(
                user=user,
                company_name=f"{user.first_name} {user.last_name}".strip() or user.username,
                is_approved=False
            )

    if request.method == 'POST':
        # Handle different form types based on the submitted data
        form_type = request.POST.get('form_type', 'preferences')

        if form_type == 'preferences':
            user_prefs_form = UserPreferencesForm(request.POST, instance=user)
            vendor_prefs_form = VendorPreferencesForm(request.POST, instance=vendor) if vendor else None

            if user_prefs_form.is_valid() and (vendor_prefs_form is None or vendor_prefs_form.is_valid()):
                try:
                    user_prefs_form.save()
                    if vendor_prefs_form:
                        vendor_prefs_form.save()

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Preferences updated successfully!'})

                    messages.success(request, 'Preferences updated successfully!')
                    return redirect('core:user_settings')

                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error updating preferences.'})
                    messages.error(request, 'Error updating preferences.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    errors = {}
                    if user_prefs_form.errors:
                        errors.update(user_prefs_form.errors)
                    if vendor_prefs_form and vendor_prefs_form.errors:
                        errors.update(vendor_prefs_form.errors)
                    return JsonResponse({'success': False, 'errors': errors})
                messages.error(request, 'Please correct the errors below.')

        elif form_type == 'business_hours' and vendor:
            business_hours_form = BusinessHoursForm(request.POST, vendor=vendor)

            if business_hours_form.is_valid():
                try:
                    # Update vendor operating days
                    for day_code, day_name in BusinessHoursForm.DAYS_OF_WEEK:
                        operates_field = f'operates_{day_code}'
                        operates = business_hours_form.cleaned_data.get(f'operates_{day_code}', False)
                        setattr(vendor, operates_field, operates)

                    # Save business hours as JSON
                    business_hours = {}
                    for day_code, day_name in BusinessHoursForm.DAYS_OF_WEEK:
                        if business_hours_form.cleaned_data.get(f'operates_{day_code}'):
                            open_time = business_hours_form.cleaned_data.get(f'{day_code}_open')
                            close_time = business_hours_form.cleaned_data.get(f'{day_code}_close')
                            if open_time and close_time:
                                business_hours[day_code] = {
                                    'open': open_time.strftime('%H:%M'),
                                    'close': close_time.strftime('%H:%M')
                                }

                    import json
                    vendor.business_hours = json.dumps(business_hours)
                    vendor.save()

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Business hours updated successfully!'})

                    messages.success(request, 'Business hours updated successfully!')
                    return redirect('core:user_settings')

                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error updating business hours.'})
                    messages.error(request, 'Error updating business hours.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': business_hours_form.errors})
                messages.error(request, 'Please correct the errors below.')

    # For GET requests, initialize forms
    user_prefs_form = UserPreferencesForm(instance=user)
    vendor_prefs_form = VendorPreferencesForm(instance=vendor) if vendor else None
    business_hours_form = BusinessHoursForm(vendor=vendor) if vendor else None

    context = {
        'user': user,
        'vendor': vendor,
        'user_prefs_form': user_prefs_form,
        'vendor_prefs_form': vendor_prefs_form,
        'business_hours_form': business_hours_form,
    }

    return render(request, 'core/dashboard/settings.html', context)


@login_required
def profile_analytics_view(request):
    """Profile analytics dashboard"""
    user = request.user

    # Get comprehensive analytics data
    analytics_data = get_analytics_dashboard_data(user)

    if not analytics_data:
        messages.error(request, 'Unable to load analytics data.')
        return redirect('core:profile')

    # Handle AJAX requests for chart data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        chart_type = request.GET.get('chart_type')

        if chart_type == 'profile_views' and user.role == 'vendor':
            # Return profile views chart data
            daily_views = analytics_data.get('daily_views', [])
            chart_data = {
                'labels': [item['day'] for item in daily_views],
                'data': [item['views'] for item in daily_views],
                'title': 'Profile Views (Last 30 Days)'
            }
            return JsonResponse(chart_data)

        elif chart_type == 'activity_breakdown':
            # Return activity breakdown chart data
            activity_breakdown = analytics_data.get('activity_breakdown', [])
            chart_data = {
                'labels': [item['action'].replace('_', ' ').title() for item in activity_breakdown],
                'data': [item['count'] for item in activity_breakdown],
                'title': 'Activity Breakdown'
            }
            return JsonResponse(chart_data)

    context = {
        'user': user,
        'analytics_data': analytics_data,
    }

    return render(request, 'core/dashboard/analytics.html', context)


@login_required
def admin_user_detail_view(request, user_id):
    """Admin user detail and management view"""
    # Check admin permissions
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:dashboard')

    # Get the user
    user = get_object_or_404(User, id=user_id)
    vendor = None

    # Get vendor profile if user is a vendor
    if user.role == 'vendor':
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            vendor = None

    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            # Handle profile update
            user_form = UserProfileForm(request.POST, request.FILES, instance=user)
            vendor_form = VendorProfileForm(request.POST, request.FILES, instance=vendor) if vendor else None

            if user_form.is_valid() and (vendor_form is None or vendor_form.is_valid()):
                try:
                    # Handle profile picture processing
                    if 'profile_picture' in request.FILES:
                        profile_picture = request.FILES['profile_picture']
                        try:
                            processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                                profile_picture, 'profile'
                            )

                            if user.profile_picture:
                                default_image_handler.cleanup(user.profile_picture.path)

                            user.profile_picture.save(filename, processed_file, save=False)

                        except ValueError as e:
                            messages.error(request, f'Image processing error: {str(e)}')
                            return redirect('core:admin_user_detail', user_id=user_id)

                    user_form.save()

                    # Handle vendor form if exists
                    if vendor_form:
                        vendor = vendor_form.save(commit=False)

                        # Handle company logo processing
                        if 'company_logo' in request.FILES:
                            company_logo = request.FILES['company_logo']
                            try:
                                processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                                    company_logo, 'logo'
                                )

                                if vendor.company_logo:
                                    default_image_handler.cleanup(vendor.company_logo.path)

                                vendor.company_logo.save(filename, processed_file, save=False)

                            except ValueError as e:
                                messages.error(request, f'Logo processing error: {str(e)}')
                                return redirect('core:admin_user_detail', user_id=user_id)

                        vendor.save()

                    # Log the activity
                    log_user_activity(
                        request.user,
                        'profile_update',
                        f'Admin updated profile for user {user.username}',
                        request,
                        {'target_user_id': user.id}
                    )

                    messages.success(request, f'Profile updated successfully for {user.username}!')
                    return redirect('core:admin_user_detail', user_id=user_id)

                except Exception as e:
                    messages.error(request, f'Error updating profile: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif action == 'change_role':
            # Handle role change
            new_role = request.POST.get('new_role')
            if new_role in ['customer', 'vendor', 'admin']:
                old_role = user.role
                user.role = new_role
                user.save()

                # Create vendor profile if changing to vendor
                if new_role == 'vendor' and not hasattr(user, 'vendor'):
                    Vendor.objects.create(
                        user=user,
                        company_name=f"{user.first_name} {user.last_name}".strip() or user.username,
                        is_approved=False
                    )

                # Log the activity
                log_user_activity(
                    request.user,
                    'role_change',
                    f'Admin changed role for {user.username} from {old_role} to {new_role}',
                    request,
                    {'target_user_id': user.id, 'old_role': old_role, 'new_role': new_role}
                )

                messages.success(request, f'Role changed from {old_role} to {new_role} for {user.username}!')
                return redirect('core:admin_user_detail', user_id=user_id)
            else:
                messages.error(request, 'Invalid role selected.')

        elif action == 'toggle_status':
            # Handle account activation/deactivation
            user.is_active = not user.is_active
            user.save()

            status = 'activated' if user.is_active else 'deactivated'
            log_user_activity(
                request.user,
                'account_status_change',
                f'Admin {status} account for {user.username}',
                request,
                {'target_user_id': user.id, 'new_status': user.is_active}
            )

            messages.success(request, f'Account {status} for {user.username}!')
            return redirect('core:admin_user_detail', user_id=user_id)

        elif action == 'toggle_vendor_approval':
            # Handle vendor approval/disapproval
            if vendor:
                vendor.is_approved = not vendor.is_approved
                if vendor.is_approved:
                    vendor.approval_date = timezone.now()
                    vendor.verification_status = 'verified'
                else:
                    vendor.approval_date = None
                    vendor.verification_status = 'pending'
                vendor.save()

                status = 'approved' if vendor.is_approved else 'disapproved'
                log_user_activity(
                    request.user,
                    'vendor_status_change',
                    f'Admin {status} vendor {vendor.company_name}',
                    request,
                    {'vendor_id': vendor.id, 'new_status': vendor.is_approved}
                )

                messages.success(request, f'Vendor {status} successfully!')
                return redirect('core:admin_user_detail', user_id=user_id)
            else:
                messages.error(request, 'User is not a vendor.')

        elif action == 'update_vendor':
            # Handle vendor profile update
            if vendor and vendor_form.is_valid():
                try:
                    vendor_form.save()
                    log_user_activity(
                        request.user,
                        'vendor_profile_update',
                        f'Admin updated vendor profile for {vendor.company_name}',
                        request,
                        {'vendor_id': vendor.id}
                    )
                    messages.success(request, 'Vendor profile updated successfully!')
                    return redirect('core:admin_user_detail', user_id=user_id)
                except Exception as e:
                    messages.error(request, f'Error updating vendor profile: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors in the vendor form.')

        elif action == 'reset_password':
            # Handle password reset
            new_password = User.objects.make_random_password(length=12)
            user.set_password(new_password)
            user.save()

            # Log the activity
            log_user_activity(
                request.user,
                'password_reset',
                f'Admin reset password for {user.username}',
                request,
                {'target_user_id': user.id}
            )

            messages.success(request, f'Password reset for {user.username}! New password: {new_password}')
            return redirect('core:admin_user_detail', user_id=user_id)

    # For GET requests, initialize forms
    user_form = UserProfileForm(instance=user)
    vendor_form = VendorProfileForm(instance=vendor) if vendor else None

    # Get user analytics and activity
    analytics_data = get_analytics_dashboard_data(user)

    # Get recent activity logs
    recent_activities = UserActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:20]

    # Get profile views if vendor
    profile_views = []
    if vendor:
        profile_views = ProfileView.objects.filter(
            profile_user=user
        ).order_by('-viewed_at')[:10]

    # Get user's orders, listings, etc.
    user_orders = []
    user_listings = []
    user_inquiries = []

    if hasattr(user, 'orders'):
        user_orders = user.orders.all().order_by('-created_at')[:5]

    if user.role == 'vendor' and vendor:
        user_listings = Car.objects.filter(vendor=vendor).order_by('-created_at')[:5]

    if hasattr(user, 'inquiries_sent'):
        user_inquiries = user.inquiries_sent.all().order_by('-created_at')[:5]

    context = {
        'user_profile': user,  # Renamed to avoid conflict with request.user
        'vendor': vendor,
        'user_form': user_form,
        'vendor_form': vendor_form,
        'analytics_data': analytics_data,
        'recent_activities': recent_activities,
        'profile_views': profile_views,
        'user_orders': user_orders,
        'user_listings': user_listings,
        'user_inquiries': user_inquiries,
    }

    return render(request, 'core/dashboard/admin_user_detail.html', context)


@login_required
def admin_vendor_user_detail_view(request, user_id):
    """Enhanced admin vendor user detail and management view"""
    # Check admin permissions
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:dashboard')

    # Get the user and ensure they are a vendor
    user = get_object_or_404(User, id=user_id)

    if user.role != 'vendor':
        messages.error(request, 'This user is not a vendor.')
        return redirect('core:admin_users')

    # Get vendor profile
    try:
        vendor = user.vendor
    except Vendor.DoesNotExist:
        messages.error(request, 'Vendor profile not found.')
        return redirect('core:admin_users')

    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            # Handle profile update
            user_form = UserProfileForm(request.POST, request.FILES, instance=user)
            vendor_form = VendorProfileForm(request.POST, request.FILES, instance=vendor)

            if user_form.is_valid() and vendor_form.is_valid():
                try:
                    # Handle profile picture processing
                    if 'profile_picture' in request.FILES:
                        profile_picture = request.FILES['profile_picture']
                        try:
                            processed_file, filename, thumbnail_file, thumbnail_filename = default_image_handler.process(
                                profile_picture, 'profile'
                            )

                            if user.profile_picture:
                                default_image_handler.cleanup(user.profile_picture.path)

                            user.profile_picture.save(filename, processed_file, save=False)

                        except ValueError as e:
                            messages.error(request, f'Image processing error: {str(e)}')
                            return redirect('core:admin_vendor_user_detail', user_id=user_id)

                    user_form.save()
                    vendor_form.save()

                    log_user_activity(
                        request.user,
                        'vendor_profile_update',
                        f'Admin updated vendor profile for {vendor.company_name}',
                        request,
                        {'vendor_id': vendor.id, 'user_id': user.id}
                    )

                    messages.success(request, 'Vendor profile updated successfully!')
                    return redirect('core:admin_vendor_user_detail', user_id=user_id)

                except Exception as e:
                    messages.error(request, f'Error updating profile: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors in the form.')

        elif action == 'approve_vendor':
            # Approve vendor
            vendor.is_approved = True
            vendor.approval_date = timezone.now()
            vendor.save()

            log_user_activity(
                request.user,
                'vendor_approval',
                f'Admin approved vendor {vendor.company_name}',
                request,
                {'vendor_id': vendor.id, 'user_id': user.id}
            )

            messages.success(request, f'Vendor {vendor.company_name} has been approved successfully.')
            return redirect('core:admin_vendor_user_detail', user_id=user_id)

        elif action == 'suspend_vendor':
            # Suspend vendor
            vendor.is_approved = False
            vendor.approval_date = None
            vendor.save()

            log_user_activity(
                request.user,
                'vendor_suspension',
                f'Admin suspended vendor {vendor.company_name}',
                request,
                {'vendor_id': vendor.id, 'user_id': user.id}
            )

            messages.warning(request, f'Vendor {vendor.company_name} has been suspended.')
            return redirect('core:admin_vendor_user_detail', user_id=user_id)

        elif action == 'toggle_status':
            # Handle account activation/deactivation
            user.is_active = not user.is_active
            user.save()

            status = 'activated' if user.is_active else 'deactivated'
            log_user_activity(
                request.user,
                'account_status_change',
                f'Admin {status} vendor account for {user.username}',
                request,
                {'target_user_id': user.id, 'new_status': user.is_active}
            )

            messages.success(request, f'Vendor account {status} for {user.username}!')
            return redirect('core:admin_vendor_user_detail', user_id=user_id)

        elif action == 'reset_password':
            # Handle password reset
            new_password = User.objects.make_random_password(length=12)
            user.set_password(new_password)
            user.save()

            log_user_activity(
                request.user,
                'password_reset',
                f'Admin reset password for vendor {user.username}',
                request,
                {'target_user_id': user.id}
            )

            messages.success(request, f'Password reset for {user.username}! New password: {new_password}')
            return redirect('core:admin_vendor_user_detail', user_id=user_id)

    # For GET requests, initialize forms
    user_form = UserProfileForm(instance=user)
    vendor_form = VendorProfileForm(instance=vendor)

    # Get vendor analytics and activity
    analytics_data = get_analytics_dashboard_data(user)

    # Get recent activity logs
    recent_activities = UserActivityLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:20]

    # Get profile views
    profile_views = ProfileView.objects.filter(
        profile_user=user
    ).order_by('-viewed_at')[:10]

    # Get vendor's listings
    vendor_listings = Car.objects.filter(vendor=vendor).order_by('-created_at')[:10]

    # Get vendor's inquiries received
    vendor_inquiries = Inquiry.objects.filter(
        car__vendor=vendor
    ).select_related('user', 'car').order_by('-created_at')[:10]

    # Get vendor's orders/sales
    vendor_orders = []
    if hasattr(vendor, 'orders'):
        vendor_orders = vendor.orders.all().order_by('-created_at')[:10]

    # Get subscription info
    subscription = None
    try:
        subscription = vendor.subscription
    except VendorSubscription.DoesNotExist:
        pass

    context = {
        'user_profile': user,
        'vendor': vendor,
        'user_form': user_form,
        'vendor_form': vendor_form,
        'analytics_data': analytics_data,
        'recent_activities': recent_activities,
        'profile_views': profile_views,
        'vendor_listings': vendor_listings,
        'vendor_inquiries': vendor_inquiries,
        'vendor_orders': vendor_orders,
        'subscription': subscription,
        'is_vendor_detail': True,  # Flag to indicate this is vendor-specific view
    }

    return render(request, 'core/dashboard/admin_vendor_user_detail.html', context)


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

        # Get vendor's cars with filtering and sorting
        cars = Car.objects.filter(vendor=vendor).select_related('brand', 'model')

        # Apply status filter
        status_filter = request.GET.get('status_filter', '')
        if status_filter == 'approved':
            cars = cars.filter(is_approved=True)
        elif status_filter == 'pending':
            cars = cars.filter(is_approved=False)
        elif status_filter == 'featured':
            cars = cars.filter(status='featured')
        elif status_filter == 'sold':
            cars = cars.filter(status='sold')

        # Apply search filter
        search = request.GET.get('search', '')
        if search:
            cars = cars.filter(
                Q(title__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(model__name__icontains=search) |
                Q(description__icontains=search)
            )

        # Apply sorting
        sort_by = request.GET.get('sort_by', '-created_at')
        cars = cars.order_by(sort_by)

        # Pagination - 20 cars per page
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(cars, 20)
        page = request.GET.get('page')

        try:
            cars = paginator.page(page)
        except PageNotAnInteger:
            cars = paginator.page(1)
        except EmptyPage:
            cars = paginator.page(paginator.num_pages)

        # Calculate statistics
        vendor_cars_all = Car.objects.filter(vendor=vendor)
        total_cars = vendor_cars_all.count()
        approved_cars = vendor_cars_all.filter(is_approved=True).count()
        pending_cars = vendor_cars_all.filter(is_approved=False).count()
        total_views = vendor_cars_all.aggregate(total=models.Sum('views_count'))['total'] or 0

        context = {
            'vendor': vendor,
            'cars': cars,
            'total_cars': total_cars,
            'approved_cars': approved_cars,
            'pending_cars': pending_cars,
            'total_views': total_views,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'search': search,
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
    # Check admin permissions
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('core:dashboard')

    vendors = Vendor.objects.select_related('user').order_by('-created_at')

    # Filter by approval status
    status_filter = request.GET.get('status')
    if status_filter == 'approved':
        vendors = vendors.filter(is_approved=True)
    elif status_filter == 'pending':
        vendors = vendors.filter(is_approved=False)
    elif status_filter == 'suspended':
        vendors = vendors.filter(user__is_active=False)

    # Filter by business type
    business_type_filter = request.GET.get('business_type')
    if business_type_filter:
        vendors = vendors.filter(business_type=business_type_filter)

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        vendors = vendors.filter(
            Q(company_name__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(business_license__icontains=search)
        )

    # Pagination - 20 vendors per page
    paginator = Paginator(vendors, 20)
    page = request.GET.get('page')
    try:
        vendors = paginator.page(page)
    except PageNotAnInteger:
        vendors = paginator.page(1)
    except EmptyPage:
        vendors = paginator.page(paginator.num_pages)

    context = {
        'vendors': vendors,
        'total_vendors': Vendor.objects.count(),
        'approved_vendors': Vendor.objects.filter(is_approved=True).count(),
        'pending_vendors': Vendor.objects.filter(is_approved=False).count(),
        'suspended_vendors': Vendor.objects.filter(user__is_active=False).count(),
        'current_filter': status_filter,
        'business_type_filter': business_type_filter,
        'search_query': search,
    }

    return render(request, 'core/dashboard/admin_vendors.html', context)


@login_required
def admin_listings_view(request):
    """Admin car listings management view with pagination"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    cars = Car.objects.select_related('brand', 'model', 'vendor', 'vendor__user').order_by('-created_at')

    # Filter by approval status
    status_filter = request.GET.get('status')
    if status_filter == 'approved':
        cars = cars.filter(is_approved=True)
    elif status_filter == 'pending':
        cars = cars.filter(is_approved=False)
    elif status_filter == 'featured':
        cars = cars.filter(is_featured=True)
    elif status_filter == 'hot_deals':
        cars = cars.filter(is_hot_deal=True)
    elif status_filter == 'sold':
        cars = cars.filter(status='sold')

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        cars = cars.filter(
            Q(title__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(model__name__icontains=search) |
            Q(vendor__company_name__icontains=search) |
            Q(vendor__user__first_name__icontains=search) |
            Q(vendor__user__last_name__icontains=search)
        )

    # Pagination - 20 cars per page
    paginator = Paginator(cars, 20)
    page = request.GET.get('page')

    try:
        cars = paginator.page(page)
    except PageNotAnInteger:
        cars = paginator.page(1)
    except EmptyPage:
        cars = paginator.page(paginator.num_pages)

    context = {
        'cars': cars,
        'total_cars': Car.objects.count(),
        'approved_cars': Car.objects.filter(is_approved=True).count(),
        'pending_cars': Car.objects.filter(is_approved=False).count(),
        'featured_cars': Car.get_featured_cars_count(),
        'featured_remaining': Car.get_featured_cars_remaining(),
        'current_filter': status_filter,
        'search': search,
    }

    return render(request, 'core/dashboard/admin_listings.html', context)


@login_required
def admin_car_detail_view(request, car_id):
    """Admin car detail view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    car = get_object_or_404(Car.objects.select_related('brand', 'model', 'vendor', 'vendor__user'), id=car_id)

    # Get car images
    car_images = car.images.all().order_by('order')

    # Get car inquiries
    car_inquiries = Inquiry.objects.filter(car=car).select_related('user').order_by('-created_at')[:5]

    context = {
        'car': car,
        'car_images': car_images,
        'car_inquiries': car_inquiries,
        'features_list': car.get_features_list(),
    }

    return render(request, 'core/dashboard/admin_car_detail.html', context)


@login_required
def admin_car_edit_view(request, car_id):
    """Enhanced admin car edit modal view with proper HTMX handling"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    car = get_object_or_404(Car, id=car_id)
    original_approval_status = car.is_approved

    if request.method == 'POST':
        form = AdminCarEditForm(request.POST, instance=car)
        if form.is_valid():
            updated_car = form.save()

            # Handle hot deals creation/update
            try:
                if updated_car.is_hot_deal:
                    hot_deal_discount = request.POST.get('hot_deal_discount', '10')
                    hot_deal_days = request.POST.get('hot_deal_days', '7')

                    # Validate and convert values
                    try:
                        discount_value = float(hot_deal_discount)
                        days_value = int(hot_deal_days)

                        # Ensure reasonable values
                        discount_value = max(5, min(50, discount_value))  # Between 5% and 50%
                        days_value = max(1, min(30, days_value))  # Between 1 and 30 days

                        from datetime import timedelta

                        # Get or create hot deal
                        hot_deal, created = HotDeal.objects.get_or_create(
                            car=updated_car,
                            defaults={
                                'title': f'Hot Deal: {updated_car.title}',
                                'discount_type': 'percentage',
                                'discount_value': discount_value,
                                'original_price': updated_car.price,
                                'start_date': timezone.now(),
                                'end_date': timezone.now() + timedelta(days=days_value),
                                'is_active': True
                            }
                        )

                        if not created:
                            # Update existing hot deal
                            hot_deal.discount_value = discount_value
                            hot_deal.original_price = updated_car.price
                            hot_deal.end_date = timezone.now() + timedelta(days=days_value)
                            hot_deal.is_active = True
                            hot_deal.save()

                    except (ValueError, TypeError) as e:
                        # If hot deal values are invalid, just mark as hot deal without creating HotDeal object
                        pass
                else:
                    # Remove hot deal if unchecked
                    HotDeal.objects.filter(car=updated_car).update(is_active=False)
            except Exception as e:
                # Log the error but don't fail the entire form submission
                print(f"Hot deal processing error: {e}")
                pass

            # If approval status changed, update approval date
            if updated_car.is_approved and not original_approval_status:
                updated_car.approval_date = timezone.now()
                updated_car.save()

            # Create success message
            success_message = f'Car listing "{updated_car.title}" has been updated successfully.'

            # Add approval status change notification
            if updated_car.is_approved and not original_approval_status:
                success_message += ' Car is now approved and visible to customers.'
            elif not updated_car.is_approved and original_approval_status:
                success_message += ' Car approval has been revoked.'

            # Return JSON response for HTMX with success data
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'status': 'success',
                    'message': success_message,
                    'car_id': updated_car.id,
                    'car_title': updated_car.title,
                    'is_approved': updated_car.is_approved,
                    'is_featured': updated_car.is_featured,
                    'is_certified': updated_car.is_certified,
                    'is_hot_deal': updated_car.is_hot_deal,
                    'reload_required': True
                })

            messages.success(request, success_message)
            return redirect('core:admin_car_detail', car_id=car.id)
        else:
            # Return form with errors for HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'core/modals/admin_car_edit.html', {
                    'form': form,
                    'car': car,
                    'errors': form.errors
                })
    else:
        form = AdminCarEditForm(instance=car)

    return render(request, 'core/modals/admin_car_edit.html', {'form': form, 'car': car})


@login_required
def admin_feature_car(request, car_id):
    """Enhanced admin feature/unfeature car action with tier support and limits"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    car = get_object_or_404(Car, id=car_id)
    action = request.POST.get('action', 'feature')

    try:
        if action == 'feature':
            success, message = car.feature_car()
            if success:
                # Update calculated rating for better visibility
                if car.calculated_rating < 4.0:
                    car.calculated_rating = 4.0
                    car.save(update_fields=['calculated_rating'])

                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'is_featured': car.is_featured,
                    'featured_count': Car.get_featured_cars_count(),
                    'remaining_slots': Car.get_featured_cars_remaining()
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': message,
                    'featured_count': Car.get_featured_cars_count(),
                    'remaining_slots': Car.get_featured_cars_remaining()
                }, status=400)

        elif action == 'unfeature':
            success, message = car.unfeature_car()
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'is_featured': car.is_featured,
                    'featured_count': Car.get_featured_cars_count(),
                    'remaining_slots': Car.get_featured_cars_remaining()
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': message
                }, status=400)

        elif action == 'hot_deal':
            car.is_hot_deal = True
            car.save(update_fields=['is_hot_deal'])
            message = f'Car "{car.title}" has been marked as a hot deal.'
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_hot_deal': car.is_hot_deal
            })

        elif action == 'remove_hot_deal':
            car.is_hot_deal = False
            car.save(update_fields=['is_hot_deal'])
            message = f'Hot deal status removed from "{car.title}".'
            return JsonResponse({
                'status': 'success',
                'message': message,
                'is_hot_deal': car.is_hot_deal
            })
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def admin_car_delete_view(request, car_id):
    """Admin car deletion view with proper cleanup"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        car = get_object_or_404(Car, id=car_id)
        car_title = car.title
        was_featured = car.is_featured()

        # Store information before deletion
        vendor = car.vendor

        # Delete associated images first
        car_images = car.images.all()
        for image in car_images:
            if image.image and hasattr(image.image, 'path'):
                try:
                    import os
                    if os.path.exists(image.image.path):
                        os.remove(image.image.path)
                except Exception as e:
                    print(f"Error deleting image file: {e}")

        # Delete main image if exists
        if car.main_image and hasattr(car.main_image, 'path'):
            try:
                import os
                if os.path.exists(car.main_image.path):
                    os.remove(car.main_image.path)
            except Exception as e:
                print(f"Error deleting main image file: {e}")

        # Delete the car (this will cascade delete related objects)
        car.delete()

        # Get updated featured car stats
        featured_count = Car.get_featured_cars_count()
        remaining_slots = Car.get_featured_cars_remaining()

        # Log the deletion
        print(f"Admin {request.user.username} deleted car: {car_title} (ID: {car_id})")

        return JsonResponse({
            'status': 'success',
            'message': f'Car "{car_title}" has been permanently deleted',
            'car_id': car_id,
            'car_title': car_title,
            'was_featured': was_featured,
            'featured_count': featured_count,
            'remaining_slots': remaining_slots,
            'vendor_id': vendor.id if vendor else None
        })

    except Car.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Car not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting car {car_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred while deleting the car: {str(e)}'
        }, status=500)


@login_required
def admin_analytics_view(request):
    """Enhanced admin analytics and reporting view with promotion metrics"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    from .analytics_utils import PromotionAnalyticsManager

    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Initialize analytics manager
    analytics = PromotionAnalyticsManager()

    # Calculate system-wide analytics
    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_vendors = Vendor.objects.count()
    total_inquiries = Inquiry.objects.count()

    # Promotion metrics
    featured_cars_count = Car.objects.exclude(featured_tier='none').count()
    active_hot_deals = HotDeal.objects.filter(is_active=True).count()
    avg_rating = CarRating.objects.filter(
        created_at__date__gte=start_date,
        is_approved=True
    ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    # Get promotion analytics
    featured_performance = analytics.get_featured_cars_performance(days)
    hot_deals_performance = analytics.get_hot_deals_performance(days)
    rating_distribution = analytics.get_rating_distribution(days)
    tier_comparison = analytics.get_tier_comparison()
    daily_metrics = analytics.get_daily_metrics(days)
    conversion_funnel = analytics.get_conversion_funnel(days)

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

    # Top performing vendors with promotion metrics
    vendor_performance = Vendor.objects.filter(
        is_approved=True
    ).annotate(
        car_count=Count('cars', filter=Q(cars__is_approved=True)),
        featured_count=Count('cars', filter=Q(cars__featured_tier__in=['bronze', 'silver', 'gold', 'platinum'])),
        avg_rating=Avg('cars__calculated_rating', filter=Q(cars__is_approved=True))
    ).order_by('-featured_count', '-car_count')[:10]

    context = {
        'total_users': total_users,
        'total_cars': total_cars,
        'total_vendors': total_vendors,
        'total_inquiries': total_inquiries,
        'featured_cars_count': featured_cars_count,
        'active_hot_deals': active_hot_deals,
        'avg_rating': avg_rating,
        'featured_performance': featured_performance,
        'hot_deals_performance': hot_deals_performance,
        'rating_distribution': rating_distribution,
        'tier_comparison': tier_comparison,
        'daily_metrics': daily_metrics,
        'conversion_funnel': conversion_funnel,
        'monthly_data': monthly_data,
        'vendor_performance': vendor_performance,
        'top_brands': CarBrand.objects.annotate(
            car_count=Count('car')
        ).order_by('-car_count')[:5],
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'core/dashboard/admin_analytics.html', context)


@login_required
def promotion_analytics_api(request):
    """API endpoint for promotion analytics data"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    from .analytics_utils import PromotionAnalyticsManager

    analytics = PromotionAnalyticsManager()
    metric_type = request.GET.get('metric', 'daily')
    days = int(request.GET.get('days', 30))

    if metric_type == 'daily':
        data = analytics.get_daily_metrics(days)
    elif metric_type == 'featured':
        data = analytics.get_featured_cars_performance(days)
    elif metric_type == 'hot_deals':
        data = analytics.get_hot_deals_performance(days)
    elif metric_type == 'ratings':
        data = analytics.get_rating_distribution(days)
    elif metric_type == 'funnel':
        data = analytics.get_conversion_funnel(days)
    else:
        data = {}

    return JsonResponse(data, safe=False)


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
    if not request.user.is_staff and request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.is_approved = True
    vendor.approval_date = timezone.now()
    vendor.verification_status = 'verified'
    vendor.save()

    # Log the activity
    log_user_activity(
        request.user,
        'vendor_approval',
        f'Admin approved vendor {vendor.company_name}',
        request,
        {'vendor_id': vendor.id}
    )

    messages.success(request, f'Vendor "{vendor.company_name}" has been approved.')

    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'approved'})

    return redirect('core:admin_vendors')


@login_required
def disapprove_vendor(request, vendor_id):
    """Disapprove/revoke vendor approval"""
    if not request.user.is_staff and request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.is_approved = False
    vendor.approval_date = None
    vendor.verification_status = 'pending'
    vendor.save()

    # Log the activity
    log_user_activity(
        request.user,
        'vendor_disapproval',
        f'Admin revoked approval for vendor {vendor.company_name}',
        request,
        {'vendor_id': vendor.id}
    )

    messages.success(request, f'Approval revoked for vendor "{vendor.company_name}".')

    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'disapproved'})

    return redirect('core:admin_vendors')


@login_required
def suspend_vendor(request, vendor_id):
    """Suspend a vendor account"""
    if not request.user.is_staff and request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)

    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.user.is_active = False
    vendor.user.save()

    # Log the activity
    log_user_activity(
        request.user,
        'vendor_suspension',
        f'Admin suspended vendor {vendor.company_name}',
        request,
        {'vendor_id': vendor.id, 'user_id': vendor.user.id}
    )

    messages.success(request, f'Vendor "{vendor.company_name}" has been suspended.')

    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'suspended'})

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


@login_required
def notification_badges_api(request):
    """API endpoint for real-time notification badge updates"""
    from .context_processors import notification_badges

    # Get badge data from context processor
    badge_data = notification_badges(request)
    badges = badge_data.get('notification_badges', {})

    # Format for JavaScript consumption
    badge_updates = []

    # Map badge types to their identifiers
    badge_mappings = {
        'unread_notifications': {'selector': '[data-badge="notifications"]', 'type': 'primary'},
        'pending_import_requests': {'selector': '[data-badge="import-requests"]', 'type': 'warning'},
        'active_import_orders': {'selector': '[data-badge="import-orders"]', 'type': 'blue'},
        'new_inquiries': {'selector': '[data-badge="inquiries"]', 'type': 'warning'},
        'pending_approvals': {'selector': '[data-badge="approvals"]', 'type': 'danger'},
        'system_alerts': {'selector': '[data-badge="alerts"]', 'type': 'danger'},
        'vendor_orders': {'selector': '[data-badge="vendor-orders"]', 'type': 'blue'},
        'vendor_inquiries': {'selector': '[data-badge="vendor-inquiries"]', 'type': 'warning'},
        'order_updates': {'selector': '[data-badge="order-updates"]', 'type': 'primary'},
        'import_updates': {'selector': '[data-badge="import-updates"]', 'type': 'blue'},
        'inquiry_responses': {'selector': '[data-badge="inquiry-responses"]', 'type': 'warning'},
    }

    for badge_key, count in badges.items():
        if badge_key in badge_mappings and count > 0:
            mapping = badge_mappings[badge_key]
            badge_updates.append({
                'badgeId': badge_key,
                'selector': mapping['selector'],
                'count': count,
                'type': mapping['type'],
                'options': {
                    'pulse': count > 5,  # Pulse for high counts
                    'urgent': badge_key in ['system_alerts', 'pending_approvals']
                }
            })

    return JsonResponse({
        'badges': badge_updates,
        'timestamp': timezone.now().isoformat(),
        'total_count': badges.get('total_badge_count', 0)
    })


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


def apply_tracking_filters(request, queryset):
    """Apply filters to tracking management queryset"""
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Search filter
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(order_number__icontains=search) |
            Q(customer__username__icontains=search) |
            Q(customer__email__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(brand__icontains=search) |
            Q(model__icontains=search) |
            Q(chassis_number__icontains=search) |
            Q(bill_of_lading__icontains=search) |
            Q(vessel_name__icontains=search)
        )

    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=to_date)
        except ValueError:
            pass

    return queryset


@login_required
def admin_tracking_management_table_partial(request):
    """Return just the tracking management table for HTMX updates with pagination"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Get import orders with tracking information
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')

    # Apply filters
    import_orders = apply_tracking_filters(request, import_orders)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(import_orders, 20)  # 20 items per page

    try:
        import_orders_page = paginator.page(page)
    except PageNotAnInteger:
        import_orders_page = paginator.page(1)
    except EmptyPage:
        import_orders_page = paginator.page(paginator.num_pages)

    context = {
        'import_orders': import_orders_page,
        'paginator': paginator,
        'page_obj': import_orders_page,
        'is_paginated': paginator.num_pages > 1,
        'current_filter': request.GET.get('status', ''),
        'current_search': request.GET.get('search', ''),
        'current_date_from': request.GET.get('date_from', ''),
        'current_date_to': request.GET.get('date_to', ''),
    }

    return render(request, 'core/dashboard/partials/admin_tracking_management_table.html', context)


@login_required
def admin_tracking_management_export_csv(request):
    """Export tracking management data to CSV with current filters applied"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    # Get filtered queryset
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')
    import_orders = apply_tracking_filters(request, import_orders)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="import_orders_tracking.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Order Number', 'Customer Name', 'Customer Email', 'Brand', 'Model', 'Year',
        'Color', 'Engine Size', 'Fuel Type', 'Origin Country', 'Status', 'Payment Status',
        'Total Cost', 'Paid Amount', 'Balance Due', 'Chassis Number', 'Bill of Lading',
        'Vessel Name', 'Departure Port', 'Arrival Port', 'Estimated Arrival', 'Actual Arrival',
        'Progress %', 'Created Date', 'Updated Date'
    ])

    # Write data rows
    for order in import_orders:
        writer.writerow([
            order.order_number,
            order.customer.get_full_name() or order.customer.username,
            order.customer.email,
            order.brand,
            order.model,
            order.year,
            order.color,
            order.engine_size,
            order.fuel_type,
            order.origin_country,
            order.get_status_display(),
            order.get_payment_status_display(),
            order.total_cost or 0,
            order.paid_amount or 0,
            order.balance_due or 0,
            order.chassis_number or '',
            order.bill_of_lading or '',
            order.vessel_name or '',
            order.departure_port or '',
            order.arrival_port or '',
            order.estimated_arrival_date.strftime('%Y-%m-%d') if order.estimated_arrival_date else '',
            order.actual_arrival_date.strftime('%Y-%m-%d') if order.actual_arrival_date else '',
            f"{order.get_progress_percentage()}%",
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response


@login_required
def admin_tracking_management_export_excel(request):
    """Export tracking management data to Excel with current filters applied"""
    if request.user.role != 'admin':
        return HttpResponse('Access denied', status=403)

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        # Fallback to CSV if openpyxl is not available
        return admin_tracking_management_export_csv(request)

    # Get filtered queryset
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')
    import_orders = apply_tracking_filters(request, import_orders)

    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Import Orders Tracking"

    # Define styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    # Write headers
    headers = [
        'Order Number', 'Customer Name', 'Customer Email', 'Brand', 'Model', 'Year',
        'Color', 'Engine Size', 'Fuel Type', 'Origin Country', 'Status', 'Payment Status',
        'Total Cost', 'Paid Amount', 'Balance Due', 'Chassis Number', 'Bill of Lading',
        'Vessel Name', 'Departure Port', 'Arrival Port', 'Estimated Arrival', 'Actual Arrival',
        'Progress %', 'Created Date', 'Updated Date'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    # Write data rows
    for row, order in enumerate(import_orders, 2):
        data = [
            order.order_number,
            order.customer.get_full_name() or order.customer.username,
            order.customer.email,
            order.brand,
            order.model,
            order.year,
            order.color,
            order.engine_size,
            order.fuel_type,
            order.origin_country,
            order.get_status_display(),
            order.get_payment_status_display(),
            order.total_cost or 0,
            order.paid_amount or 0,
            order.balance_due or 0,
            order.chassis_number or '',
            order.bill_of_lading or '',
            order.vessel_name or '',
            order.departure_port or '',
            order.arrival_port or '',
            order.estimated_arrival_date.strftime('%Y-%m-%d') if order.estimated_arrival_date else '',
            order.actual_arrival_date.strftime('%Y-%m-%d') if order.actual_arrival_date else '',
            f"{order.get_progress_percentage()}%",
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ]

        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="import_orders_tracking.xlsx"'

    wb.save(response)
    return response


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
    """Admin tracking management view for 7-stage import workflow with pagination"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('core:dashboard')

    # Get import orders with tracking information
    import_orders = ImportOrder.objects.select_related('customer').prefetch_related('status_history').all().order_by('-created_at')

    # Apply filters
    import_orders = apply_tracking_filters(request, import_orders)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(import_orders, 20)  # 20 items per page

    try:
        import_orders_page = paginator.page(page)
    except PageNotAnInteger:
        import_orders_page = paginator.page(1)
    except EmptyPage:
        import_orders_page = paginator.page(paginator.num_pages)

    # Define workflow stages for the UI
    workflow_stages = [
        {'key': 'import_request', 'name': 'Import Request', 'icon': 'fas fa-file-import', 'color': 'blue'},
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
    import_request_orders = ImportOrder.objects.filter(status='import_request').count()
    in_transit_orders = ImportOrder.objects.filter(status__in=['shipped', 'in_transit']).count()
    arrived_orders = ImportOrder.objects.filter(status='arrived_docked').count()
    completed_orders = ImportOrder.objects.filter(status='delivered').count()

    context = {
        'import_orders': import_orders_page,
        'paginator': paginator,
        'page_obj': import_orders_page,
        'is_paginated': paginator.num_pages > 1,
        'total_orders': total_orders,
        'import_request_orders': import_request_orders,
        'in_transit_orders': in_transit_orders,
        'arrived_orders': arrived_orders,
        'completed_orders': completed_orders,
        'workflow_stages': workflow_stages,
        'current_filter': request.GET.get('status', ''),
        'current_search': request.GET.get('search', ''),
        'current_date_from': request.GET.get('date_from', ''),
        'current_date_to': request.GET.get('date_to', ''),
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
