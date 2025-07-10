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


# Car Model Signals
@receiver(post_save, sender=Car)
def log_car_activity(sender, instance, created, **kwargs):
    """Log car-related activities"""
    try:
        if created:
            ActivityManager.log_car_action(
                user=instance.vendor.user,
                action='car_create',
                car=instance
            )
            AuditManager.log_model_change(
                user=instance.vendor.user,
                instance=instance,
                action_type='create'
            )
        else:
            ActivityManager.log_car_action(
                user=instance.vendor.user,
                action='car_update',
                car=instance
            )
    except Exception as e:
        # Silently fail to avoid breaking car operations
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log car activity: {e}")


@receiver(post_delete, sender=Car)
def log_car_deletion(sender, instance, **kwargs):
    """Log car deletion"""
    ActivityManager.log_car_action(
        user=instance.vendor.user,
        action='car_delete',
        car=instance
    )
    AuditManager.log_model_change(
        user=instance.vendor.user,
        instance=instance,
        action_type='delete'
    )


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


# Import Order Status Change
@receiver(post_save, sender=ImportOrder)
def log_import_order_status_change(sender, instance, created, **kwargs):
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
        except ImportOrder.DoesNotExist:
            pass


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
        ActivityManager.log_activity(
            user=instance.vendor.user,
            action='spare_part_create',
            description=f"Created spare part: {instance.name}",
            content_object=instance
        )
        AuditManager.log_model_change(
            user=instance.vendor.user,
            instance=instance,
            action_type='create'
        )


@receiver(post_delete, sender=SparePart)
def log_spare_part_deletion(sender, instance, **kwargs):
    """Log spare part deletion"""
    ActivityManager.log_activity(
        user=instance.vendor.user,
        action='spare_part_delete',
        description=f"Deleted spare part: {instance.name}",
        content_object=instance
    )
    AuditManager.log_model_change(
        user=instance.vendor.user,
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


# Connect signals for models that need change tracking
models_to_track = [Car, ImportRequest, ImportOrder, Order, SparePart, Inquiry, User]
for model in models_to_track:
    post_save.connect(track_model_changes, sender=model)
    post_delete.connect(track_model_changes, sender=model)
