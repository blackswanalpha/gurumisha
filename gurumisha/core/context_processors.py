"""
Context processors for providing global template variables
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import (
    Notification, ImportRequest, ImportOrder, Inquiry,
    Order, Car, Vendor, User, SparePart, InventoryAlert
)


def get_user_message_count(user):
    """Get count of new messages for a user"""
    try:
        from .models import Message, MessageRead

        # Get active messages for this user's role
        user_role = getattr(user, 'role', 'customer')
        messages_qs = Message.objects.filter(
            Q(status='active') & (Q(target_audience='all') | Q(target_audience=user_role))
        )

        # Apply publication/expiration filters
        now = timezone.now()
        messages_qs = messages_qs.filter(
            (Q(publication_date__isnull=True) | Q(publication_date__lte=now)) &
            (Q(expiration_date__isnull=True) | Q(expiration_date__gte=now))
        )

        # Count messages not yet seen by user
        seen_message_ids = MessageRead.objects.filter(
            user=user,
            message__in=messages_qs
        ).values_list('message_id', flat=True)

        return messages_qs.exclude(id__in=seen_message_ids).count()

    except Exception:
        # Handle case where Message model doesn't exist yet (during migrations)
        return 0


def notification_badges(request):
    """
    Context processor to provide notification badge counts for sidebar navigation
    """
    if not request.user.is_authenticated:
        return {'notification_badges': {}}

    try:
        user = request.user
        badges = {}

        # Base notification count (unread notifications)
        try:
            badges['unread_notifications'] = Notification.objects.filter(
                recipient=user,
                is_read=False
            ).count()
        except Exception:
            badges['unread_notifications'] = 0

        # Role-specific badge counts
        if user.role == 'admin':
            # Admin-specific badges
            badges.update({
                # Import requests needing attention
                'pending_import_requests': ImportRequest.objects.filter(
                    status__in=['pending', 'on_quotation']
                ).count(),

                # Import orders needing updates
                'active_import_orders': ImportOrder.objects.filter(
                    status__in=['import_request', 'auction_won', 'shipped', 'in_transit']
                ).count(),

                # New inquiries
                'new_inquiries': Inquiry.objects.filter(
                    status='pending',
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).count(),

                # Pending approvals
                'pending_approvals': (
                    Car.objects.filter(is_approved=False).count() +
                    Vendor.objects.filter(is_approved=False).count()
                ),

                # System alerts
                'system_alerts': InventoryAlert.objects.filter(
                    status='active'
                ).count(),

                # Recent orders needing attention
                'orders_needing_attention': Order.objects.filter(
                    status__in=['pending', 'processing'],
                    created_at__gte=timezone.now() - timedelta(days=3)
                ).count(),
            })
        elif user.role == 'vendor':
            # Vendor-specific badges
            try:
                vendor = user.vendor_profile
                badges.update({
                    # Orders for vendor's products
                    'vendor_orders': Order.objects.filter(
                        items__car__vendor=vendor,
                        status__in=['pending', 'processing']
                    ).distinct().count(),

                    # Inquiries about vendor's cars
                    'vendor_inquiries': Inquiry.objects.filter(
                        car__vendor=vendor,
                        status='pending'
                    ).count(),

                    # Low stock spare parts (if vendor sells parts)
                    'low_stock_parts': SparePart.objects.filter(
                        vendor=vendor,
                        stock_quantity__lte=5
                    ).count() if hasattr(vendor, 'spare_parts') else 0,

                    # Pending car listings
                    'pending_listings': Car.objects.filter(
                        vendor=vendor,
                        is_approved=False
                    ).count(),
                })
            except:
                # Handle case where vendor profile doesn't exist
                badges.update({
                    'vendor_orders': 0,
                    'vendor_inquiries': 0,
                    'low_stock_parts': 0,
                    'pending_listings': 0,
                })
        elif user.role == 'customer':
            # Customer-specific badges
            badges.update({
                # Customer's orders with updates
                'order_updates': Order.objects.filter(
                    customer=user,
                    status__in=['processing', 'shipped', 'delivered'],
                    updated_at__gte=timezone.now() - timedelta(days=7)
                ).count(),

                # Import order updates
                'import_updates': ImportOrder.objects.filter(
                    customer=user,
                    status__in=['auction_won', 'shipped', 'in_transit', 'arrived_docked']
                ).count(),

                # Inquiry responses
                'inquiry_responses': Inquiry.objects.filter(
                    customer=user,
                    status='responded',
                    updated_at__gte=timezone.now() - timedelta(days=7)
                ).count(),

                # Messages/communications - now implemented
                'new_messages': get_user_message_count(user),
            })

        # Calculate total badge count for main notification indicator
        role_specific_counts = [v for k, v in badges.items() if k != 'unread_notifications']
        badges['total_badge_count'] = badges['unread_notifications'] + sum(role_specific_counts)

        return {'notification_badges': badges}

    except Exception as e:
        # If any error occurs during badge calculation, return safe defaults
        return {'notification_badges': {
            'unread_notifications': 0,
            'total_badge_count': 0,
        }}


def dashboard_stats(request):
    """
    Context processor to provide dashboard statistics
    """
    if not request.user.is_authenticated:
        return {'dashboard_stats': {}}

    try:
        user = request.user
        stats = {}

        if user.role == 'admin':
            stats.update({
                'total_users': User.objects.count(),
                'total_cars': Car.objects.count(),
                'total_vendors': Vendor.objects.filter(is_approved=True).count(),
                'total_orders': Order.objects.count(),
                'total_import_requests': ImportRequest.objects.count(),
                'total_import_orders': ImportOrder.objects.count(),
            })
        elif user.role == 'vendor':
            try:
                vendor = user.vendor_profile
                stats.update({
                    'vendor_cars': Car.objects.filter(vendor=vendor).count(),
                    'vendor_orders': Order.objects.filter(
                        items__car__vendor=vendor
                    ).distinct().count(),
                    'vendor_revenue': 0,  # Calculate from orders
                })
            except:
                stats.update({
                    'vendor_cars': 0,
                    'vendor_orders': 0,
                    'vendor_revenue': 0,
                })
        elif user.role == 'customer':
            stats.update({
                'customer_orders': Order.objects.filter(customer=user).count(),
                'customer_imports': ImportOrder.objects.filter(customer=user).count(),
                'customer_inquiries': Inquiry.objects.filter(customer=user).count(),
            })

        return {'dashboard_stats': stats}

    except Exception:
        # Return safe defaults if any error occurs
        return {'dashboard_stats': {}}


def user_preferences(request):
    """
    Context processor to provide user preferences and settings
    """
    if not request.user.is_authenticated:
        return {'user_preferences': {}}

    try:
        preferences = {}

        # Get notification preferences
        try:
            notification_prefs = request.user.notification_preferences
            preferences['notification_preferences'] = {
                'email_enabled': notification_prefs.email_enabled,
                'email_order_updates': notification_prefs.email_order_updates,
                'email_import_updates': notification_prefs.email_import_updates,
                'push_enabled': notification_prefs.push_enabled,
                'sms_enabled': notification_prefs.sms_enabled,
            }
        except:
            # Default preferences if not set
            preferences['notification_preferences'] = {
                'email_enabled': True,
                'email_order_updates': True,
                'email_import_updates': True,
                'push_enabled': True,
                'sms_enabled': False,
            }

        return {'user_preferences': preferences}

    except Exception:
        # Return safe defaults if any error occurs
        return {'user_preferences': {}}


def compare_context(request):
    """
    Add compare list data to all templates.
    """
    compare_list = request.session.get('compare_list', [])
    compare_count = len(compare_list)

    # Get car objects for the floating widget
    all_cars = []
    if compare_list:
        all_cars = Car.objects.filter(
            id__in=compare_list,
            is_approved=True
        ).select_related('make', 'model')

    return {
        'compare_list': compare_list,
        'compare_count': compare_count,
        'all_cars': all_cars,
    }
