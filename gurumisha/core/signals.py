"""
Django signals for automatic activity and audit logging
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Car, ImportRequest, ImportOrder, Order, SparePart, Inquiry, 
    ActivityLog, AuditLog, Notification
)
from .activity_manager import ActivityManager, AuditManager
from .notification_manager import NotificationManager, NotificationShortcuts

User = get_user_model()


# Authentication Signals
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login activity"""
    try:
        ActivityManager.log_login(user, request)
        AuditManager.log_audit(
            user=user,
            action_type='login',
            description=f"User {user.username} logged in",
            severity='low',
            request=request
        )
    except Exception as e:
        # Silently fail to avoid breaking authentication
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log user login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout activity"""
    try:
        if user:  # User might be None in some cases
            ActivityManager.log_logout(user, request)
            AuditManager.log_audit(
                user=user,
                action_type='logout',
                description=f"User {user.username} logged out",
                severity='low',
                request=request
            )
    except Exception as e:
        # Silently fail to avoid breaking authentication
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log user logout: {e}")


# Car Model Signals - DISABLED to prevent recursion
# @receiver(post_save, sender=Car)
def log_car_activity_disabled(sender, instance, created, **kwargs):
    """Log car-related activities - DISABLED"""
    pass


# @receiver(post_delete, sender=Car)
def log_car_deletion_disabled(sender, instance, **kwargs):
    """Log car deletion - DISABLED"""
    pass


# Import Request Signals
@receiver(post_save, sender=ImportRequest)
def log_import_request_activity(sender, instance, created, **kwargs):
    """Log import request activities"""
    if created:
        ActivityManager.log_import_action(
            user=instance.customer,
            action='import_request_create',
            import_obj=instance
        )
        AuditManager.log_model_change(
            user=instance.customer,
            instance=instance,
            action_type='create'
        )
        
        # Send notification to admins
        admin_users = User.objects.filter(role='admin')
        for admin in admin_users:
            NotificationManager.create_notification(
                recipient=admin,
                title='New Import Request',
                message=f'New import request from {instance.customer.username}: {instance.vehicle_details}',
                notification_type='info',
                action_url=f'/dashboard/admin/import-requests/{instance.id}/',
                action_text='View Request'
            )


# Import Order Status Change - Temporarily disabled to prevent database locks
# @receiver(post_save, sender=ImportOrder)
def log_import_order_status_change_disabled(sender, instance, created, **kwargs):
    """Log import order status changes and send notifications"""
    if not created:
        # Check if status changed
        try:
            old_instance = ImportOrder.objects.get(pk=instance.pk)
            if hasattr(old_instance, '_original_status') and old_instance._original_status != instance.status:
                ActivityManager.log_import_action(
                    user=instance.customer,
                    action='import_status_change',
                    import_obj=instance
                )

                # Send status change notification
                NotificationShortcuts.notify_import_status_change(instance, instance.status)

                # GPS Tracking Integration: Create location tracking entry for status changes
                if instance.tracking_enabled:
                    try:
                        from .models import LocationTrackingHistory

                        # Create tracking history entry for status change
                        LocationTrackingHistory.objects.create(
                            import_order=instance,
                            latitude=instance.current_latitude or 0,
                            longitude=instance.current_longitude or 0,
                            tracking_source='manual',
                            status_at_time=instance.status,
                            notes=f"Status changed from {old_instance._original_status} to {instance.status}",
                            recorded_at=timezone.now(),
                            created_by=None  # System-generated
                        )

                        # Auto-update location based on status if no current location
                        if not instance.current_latitude or not instance.current_longitude:
                            auto_update_location_for_status(instance)
                    except Exception as e:
                        print(f"Error in GPS tracking integration for order {instance.order_number}: {e}")

        except ImportOrder.DoesNotExist:
            pass

    # GPS Tracking Integration: Create default route for new import orders
    if created and instance.tracking_enabled:
        try:
            # Create default route and waypoints for new orders
            create_default_route_for_order(instance)
        except Exception as e:
            print(f"Error creating default route for new order {instance.order_number}: {e}")


@receiver(pre_save, sender=ImportOrder)
def store_original_import_order_status(sender, instance, **kwargs):
    """Store original status before save"""
    if instance.pk:
        try:
            original = ImportOrder.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except ImportOrder.DoesNotExist:
            instance._original_status = None


# Order Signals
@receiver(post_save, sender=Order)
def log_order_activity(sender, instance, created, **kwargs):
    """Log order activities"""
    if created:
        ActivityManager.log_order_action(
            user=instance.customer,
            action='order_create',
            order=instance
        )
        AuditManager.log_model_change(
            user=instance.customer,
            instance=instance,
            action_type='create'
        )
        
        # Send order confirmation notification
        NotificationShortcuts.notify_order_status_change(instance, 'created')
    else:
        # Check if status changed
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if hasattr(old_instance, '_original_status') and old_instance._original_status != instance.status:
                ActivityManager.log_order_action(
                    user=instance.customer,
                    action='order_update',
                    order=instance
                )
                
                # Send status change notification
                NotificationShortcuts.notify_order_status_change(instance, instance.status)
        except Order.DoesNotExist:
            pass


@receiver(pre_save, sender=Order)
def store_original_order_status(sender, instance, **kwargs):
    """Store original status before save"""
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Order.DoesNotExist:
            instance._original_status = None


# Spare Part Signals
@receiver(post_save, sender=SparePart)
def log_spare_part_activity(sender, instance, created, **kwargs):
    """Log spare part activities"""
    if created:
        # Get the user - either from vendor or use None for admin-created parts
        user = instance.vendor.user if instance.vendor else None

        if user:  # Only log if we have a user
            ActivityManager.log_activity(
                user=user,
                action='spare_part_create',
                description=f"Created spare part: {instance.name}",
                content_object=instance
            )
            AuditManager.log_model_change(
                user=user,
                instance=instance,
                action_type='create'
            )


@receiver(post_delete, sender=SparePart)
def log_spare_part_deletion(sender, instance, **kwargs):
    """Log spare part deletion"""
    # Get the user - either from vendor or use None for admin-created parts
    user = instance.vendor.user if instance.vendor else None

    if user:  # Only log if we have a user
        ActivityManager.log_activity(
            user=user,
            action='spare_part_delete',
            description=f"Deleted spare part: {instance.name}",
            content_object=instance
        )
        AuditManager.log_model_change(
            user=user,
            instance=instance,
            action_type='delete'
        )


# Inquiry Signals
@receiver(post_save, sender=Inquiry)
def log_inquiry_activity(sender, instance, created, **kwargs):
    """Log inquiry activities"""
    if created:
        ActivityManager.log_activity(
            user=instance.customer,
            action='inquiry_create',
            description=f"Created inquiry: {instance.subject}",
            content_object=instance
        )
        AuditManager.log_model_change(
            user=instance.customer,
            instance=instance,
            action_type='create'
        )
        
        # Notify relevant vendors or admins
        if instance.inquiry_type == 'car':
            # Notify car vendors
            vendors = User.objects.filter(role='vendor', vendor__is_approved=True)
            for vendor in vendors:
                NotificationManager.create_notification(
                    recipient=vendor,
                    title='New Car Inquiry',
                    message=f'New inquiry about cars: {instance.subject}',
                    notification_type='info',
                    action_url=f'/dashboard/vendor/inquiries/{instance.id}/',
                    action_text='View Inquiry'
                )
        elif instance.inquiry_type == 'spare_part':
            # Notify spare part vendors
            vendors = User.objects.filter(role='vendor', vendor__is_approved=True)
            for vendor in vendors:
                NotificationManager.create_notification(
                    recipient=vendor,
                    title='New Spare Part Inquiry',
                    message=f'New inquiry about spare parts: {instance.subject}',
                    notification_type='info',
                    action_url=f'/dashboard/vendor/inquiries/{instance.id}/',
                    action_text='View Inquiry'
                )


# User Model Signals
# Temporarily disabled to fix JSON serialization issue
# @receiver(post_save, sender=User)
def log_user_changes_disabled(sender, instance, created, **kwargs):
    """Log user account changes - DISABLED"""
    pass
    # if created:
    #     ActivityManager.log_activity(
    #         user=instance,
    #         action='register',
    #         description=f"User account created: {instance.username}"
    #     )
    #     AuditManager.log_model_change(
    #         user=instance,
    #         instance=instance,
    #         action_type='create'
    #     )
    #
    #     # Send welcome notification
    #     NotificationManager.send_notification(
    #         recipient=instance,
    #         title='Welcome to Gurumisha Motors!',
    #         message='Your account has been successfully created. Welcome to our automotive community!',
    #         channels=['email', 'in_app'],
    #         template_name='welcome_user',
    #         context={'dashboard_url': '/dashboard/'},
    #         priority=2
    #     )


# Security Event Signals
def log_security_event(user, event_type, description, request=None):
    """Helper function to log security events"""
    ActivityManager.log_activity(
        user=user,
        action='security_event',
        description=f"Security Event: {event_type} - {description}",
        request=request
    )
    AuditManager.log_security_event(
        user=user,
        event_type=event_type,
        description=description,
        request=request
    )
    
    # Send security alert notification
    if user:
        NotificationManager.send_notification(
            recipient=user,
            title='Security Alert',
            message=f'Security event detected: {description}',
            channels=['email', 'in_app'],
            priority=4
        )


# Model Change Tracking
def track_model_changes(sender, instance, **kwargs):
    """Generic model change tracking"""
    if hasattr(instance, '_track_changes') and instance._track_changes:
        # Get the user from thread local storage or request
        user = getattr(instance, '_changed_by', None)
        if user:
            AuditManager.log_model_change(
                user=user,
                instance=instance,
                action_type='update'
            )


# ALL SIGNALS DISABLED to prevent recursion issues
# Connect signals for models that need change tracking (excluding User to prevent recursion)
# models_to_track = [Car, ImportRequest, ImportOrder, Order, SparePart, Inquiry]
# for model in models_to_track:
#     post_save.connect(track_model_changes, sender=model)
#     post_delete.connect(track_model_changes, sender=model)


# ===== GPS TRACKING INTEGRATION FUNCTIONS =====

def auto_update_location_for_status(import_order):
    """Auto-update location based on import order status"""
    from .models import ImportOrderLocation, ImportOrder

    # Default locations for different statuses (example coordinates)
    status_locations = {
        'import_request': {
            'name': 'Import Request Processing Center',
            'lat': -1.2921, 'lng': 36.8219,  # Nairobi
            'type': 'origin'
        },
        'auction_won': {
            'name': 'Auction House - Japan',
            'lat': 35.6762, 'lng': 139.6503,  # Tokyo
            'type': 'auction_house'
        },
        'shipped': {
            'name': 'Departure Port - Japan',
            'lat': 35.4437, 'lng': 139.6380,  # Yokohama Port
            'type': 'departure_port'
        },
        'in_transit': {
            'name': 'In Transit - Indian Ocean',
            'lat': -10.0, 'lng': 60.0,  # Indian Ocean
            'type': 'current_position'
        },
        'arrived_docked': {
            'name': 'Mombasa Port - Kenya',
            'lat': -4.0435, 'lng': 39.6682,  # Mombasa
            'type': 'arrival_port'
        },
        'under_clearance': {
            'name': 'Customs Clearance - Mombasa',
            'lat': -4.0435, 'lng': 39.6682,  # Mombasa
            'type': 'customs_facility'
        },
        'registered': {
            'name': 'Vehicle Registration Office',
            'lat': -1.2921, 'lng': 36.8219,  # Nairobi
            'type': 'registration_office'
        },
        'ready_for_dispatch': {
            'name': 'Dispatch Center - Nairobi',
            'lat': -1.2921, 'lng': 36.8219,  # Nairobi
            'type': 'dispatch_center'
        },
        'delivered': {
            'name': 'Customer Delivery Location',
            'lat': -1.2921, 'lng': 36.8219,  # Default to Nairobi
            'type': 'delivery_address'
        },
    }

    location_data = status_locations.get(import_order.status)
    if location_data:
        try:
            # Update current location on import order using update() to avoid model validation
            from django.db import transaction
            with transaction.atomic():
                ImportOrder.objects.filter(id=import_order.id).update(
                    current_latitude=location_data['lat'],
                    current_longitude=location_data['lng'],
                    current_location_name=location_data['name'],
                    last_location_update=timezone.now()
                )
                # Refresh the instance to get updated values
                import_order.refresh_from_db(fields=[
                    'current_latitude', 'current_longitude',
                    'current_location_name', 'last_location_update'
                ])
        except Exception as e:
            # Log error but don't fail the entire operation
            print(f"Error updating location for order {import_order.order_number}: {e}")
            return

        # Create or update location record
        location, created = ImportOrderLocation.objects.get_or_create(
            import_order=import_order,
            location_type=location_data['type'],
            defaults={
                'name': location_data['name'],
                'latitude': location_data['lat'],
                'longitude': location_data['lng'],
                'is_current_location': True,
                'created_by_id': 1,  # System user
            }
        )

        if not created:
            # Update existing location
            location.latitude = location_data['lat']
            location.longitude = location_data['lng']
            location.name = location_data['name']
            location.is_current_location = True
            location.save()


def create_default_route_for_order(import_order):
    """Create a default route with waypoints for a new import order"""
    from .models import ImportOrderRoute, ImportOrderLocation, RouteWaypoint

    try:
        # Check if route already exists
        if hasattr(import_order, 'route') and import_order.route:
            return

        # Create origin and destination locations
        origin_location = ImportOrderLocation.objects.create(
            import_order=import_order,
            location_type='origin',
            name='Origin - Japan',
            latitude=35.6762,
            longitude=139.6503,
            created_by_id=1
        )

        destination_location = ImportOrderLocation.objects.create(
            import_order=import_order,
            location_type='delivery_address',
            name='Destination - Kenya',
            latitude=-1.2921,
            longitude=36.8219,
            created_by_id=1
        )

        # Create route
        route = ImportOrderRoute.objects.create(
            import_order=import_order,
            route_name=f"Import Route - {import_order.order_number}",
            route_type='sea_freight',
            origin_location=origin_location,
            destination_location=destination_location,
            route_status='planned',
            created_by_id=1
        )

        # Create default waypoints
        waypoints_data = [
            {'name': 'Auction House', 'type': 'departure', 'lat': 35.6762, 'lng': 139.6503},
            {'name': 'Yokohama Port', 'type': 'departure', 'lat': 35.4437, 'lng': 139.6380},
            {'name': 'Mombasa Port', 'type': 'arrival', 'lat': -4.0435, 'lng': 39.6682},
            {'name': 'Customs Office', 'type': 'customs', 'lat': -4.0435, 'lng': 39.6682},
            {'name': 'Final Destination', 'type': 'delivery', 'lat': -1.2921, 'lng': 36.8219},
        ]

        for i, waypoint_data in enumerate(waypoints_data, 1):
            # Create location for waypoint
            waypoint_location = ImportOrderLocation.objects.create(
                import_order=import_order,
                location_type='transit_port',
                name=waypoint_data['name'],
                latitude=waypoint_data['lat'],
                longitude=waypoint_data['lng'],
                is_waypoint=True,
                created_by_id=1
            )

            # Create waypoint
            RouteWaypoint.objects.create(
                route=route,
                location=waypoint_location,
                waypoint_type=waypoint_data['type'],
                sequence_order=i,
                name=waypoint_data['name'],
                is_current=(i == 1)  # First waypoint is current
            )

    except Exception as e:
        # Log error but don't fail the entire operation
        print(f"Error creating default route for order {import_order.order_number}: {e}")
        return
