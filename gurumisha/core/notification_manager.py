"""
Notification Manager for Gurumisha Motors
Comprehensive notification system with multiple delivery channels
"""

import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationQueue, NotificationDeliveryLog
)

User = get_user_model()


class NotificationManager:
    """Central manager for all notification operations"""
    
    @staticmethod
    def create_notification(recipient, title, message, notification_type='info', 
                          action_url='', action_text='', priority=1):
        """
        Create an in-app notification
        
        Args:
            recipient: User instance
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            action_url: Optional URL for action button
            action_text: Text for action button
            priority: Priority level (1-4)
        """
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            action_text=action_text
        )
    
    @staticmethod
    def send_notification(recipient, title, message, channels=None, template_name=None, 
                         context=None, priority=1, scheduled_at=None):
        """
        Send notification through multiple channels
        
        Args:
            recipient: User instance
            title: Notification title
            message: Notification message
            channels: List of channels ['email', 'sms', 'push', 'in_app']
            template_name: Template name for formatting
            context: Template context data
            priority: Priority level (1-4)
            scheduled_at: Schedule for later delivery
        """
        if channels is None:
            channels = ['in_app']
        
        context = context or {}
        context.update({
            'recipient': recipient,
            'title': title,
            'message': message,
        })
        
        # Get user preferences
        preferences = NotificationManager.get_user_preferences(recipient)
        
        notifications_sent = []
        
        for channel in channels:
            # Check if user has enabled this channel
            if not NotificationManager.is_channel_enabled(preferences, channel):
                continue
            
            # Create notification queue entry
            queue_entry = NotificationQueue.objects.create(
                recipient=recipient,
                channel=channel,
                template=NotificationManager.get_template(template_name, channel) if template_name else None,
                subject=title,
                message=message,
                priority=priority,
                scheduled_at=scheduled_at,
                context_data=context
            )
            
            # Send immediately if not scheduled
            if not scheduled_at:
                NotificationManager.process_queue_entry(queue_entry)
            
            notifications_sent.append(queue_entry)
        
        return notifications_sent
    
    @staticmethod
    def get_user_preferences(user):
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'in_app_enabled': True,
            }
        )
        return preferences
    
    @staticmethod
    def is_channel_enabled(preferences, channel):
        """Check if a notification channel is enabled for user"""
        channel_mapping = {
            'email': preferences.email_enabled,
            'sms': preferences.sms_enabled,
            'push': preferences.push_enabled,
            'in_app': preferences.in_app_enabled,
        }
        return channel_mapping.get(channel, False)
    
    @staticmethod
    def get_template(template_name, channel):
        """Get notification template for specific channel"""
        try:
            return NotificationTemplate.objects.get(
                name=template_name,
                template_type=channel,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
    
    @staticmethod
    def process_queue_entry(queue_entry):
        """Process a single notification queue entry"""
        try:
            queue_entry.status = 'processing'
            queue_entry.save()
            
            success = False
            error_message = ''
            
            if queue_entry.channel == 'email':
                success, error_message = NotificationManager.send_email(queue_entry)
            elif queue_entry.channel == 'sms':
                success, error_message = NotificationManager.send_sms(queue_entry)
            elif queue_entry.channel == 'push':
                success, error_message = NotificationManager.send_push(queue_entry)
            elif queue_entry.channel == 'in_app':
                success, error_message = NotificationManager.send_in_app(queue_entry)
            
            # Update queue entry status
            if success:
                queue_entry.status = 'sent'
                queue_entry.sent_at = timezone.now()
            else:
                queue_entry.status = 'failed'
                queue_entry.error_message = error_message
                queue_entry.retry_count += 1
            
            queue_entry.save()
            
            # Log delivery attempt
            NotificationDeliveryLog.objects.create(
                notification_queue=queue_entry,
                attempt_number=queue_entry.retry_count,
                delivery_status='success' if success else 'failed',
                response_message=error_message
            )
            
            return success
            
        except Exception as e:
            queue_entry.status = 'failed'
            queue_entry.error_message = str(e)
            queue_entry.retry_count += 1
            queue_entry.save()
            
            NotificationDeliveryLog.objects.create(
                notification_queue=queue_entry,
                attempt_number=queue_entry.retry_count,
                delivery_status='failed',
                response_message=str(e)
            )
            
            return False
    
    @staticmethod
    def send_email(queue_entry):
        """Send email notification"""
        try:
            recipient = queue_entry.recipient
            subject = queue_entry.subject
            message = queue_entry.message
            
            # Use template if available
            if queue_entry.template:
                subject = queue_entry.template.subject_template.format(**queue_entry.context_data)
                message = queue_entry.template.body_template.format(**queue_entry.context_data)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            
            return True, ''
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_sms(queue_entry):
        """Send SMS notification"""
        try:
            # Implement SMS sending logic here
            # This would integrate with SMS providers like Twilio, Africa's Talking, etc.
            
            # For now, return success (implement actual SMS logic)
            return True, ''
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_push(queue_entry):
        """Send push notification"""
        try:
            # Implement push notification logic here
            # This would integrate with Firebase, OneSignal, etc.
            
            # For now, return success (implement actual push logic)
            return True, ''
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_in_app(queue_entry):
        """Send in-app notification"""
        try:
            NotificationManager.create_notification(
                recipient=queue_entry.recipient,
                title=queue_entry.subject,
                message=queue_entry.message,
                notification_type='info'
            )
            
            return True, ''
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def process_scheduled_notifications():
        """Process notifications scheduled for delivery"""
        now = timezone.now()
        scheduled_notifications = NotificationQueue.objects.filter(
            status='pending',
            scheduled_at__lte=now
        ).order_by('priority', 'scheduled_at')
        
        for notification in scheduled_notifications:
            NotificationManager.process_queue_entry(notification)
    
    @staticmethod
    def retry_failed_notifications():
        """Retry failed notifications that haven't exceeded max retries"""
        failed_notifications = NotificationQueue.objects.filter(
            status='failed',
            retry_count__lt=models.F('max_retries')
        )
        
        for notification in failed_notifications:
            NotificationManager.process_queue_entry(notification)
    
    @staticmethod
    def mark_notification_read(notification_id, user):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_all_notifications_read(user):
        """Mark all notifications as read for a user"""
        Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @staticmethod
    def get_user_notifications(user, limit=50, unread_only=False):
        """Get notifications for a user"""
        queryset = Notification.objects.filter(recipient=user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset[:limit]
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user"""
        return Notification.objects.filter(recipient=user, is_read=False).count()
    
    @staticmethod
    def clean_old_notifications(days=30):
        """Clean up old notifications"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old read notifications
        Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()
        
        # Delete old queue entries
        NotificationQueue.objects.filter(
            status='sent',
            sent_at__lt=cutoff_date
        ).delete()


# Notification shortcuts for common use cases
class NotificationShortcuts:
    """Common notification patterns"""
    
    @staticmethod
    def notify_order_status_change(order, new_status):
        """Notify user about order status change"""
        title = f"Order #{order.id} Status Update"
        message = f"Your order status has been updated to: {new_status}"
        
        NotificationManager.send_notification(
            recipient=order.customer,
            title=title,
            message=message,
            channels=['email', 'in_app'],
            template_name='order_status_change',
            context={'order': order, 'new_status': new_status},
            priority=2
        )
    
    @staticmethod
    def notify_import_status_change(import_order, new_status):
        """Notify user about import status change"""
        title = f"Import Order {import_order.order_number} Update"
        message = f"Your import order status has been updated to: {new_status}"
        
        NotificationManager.send_notification(
            recipient=import_order.customer,
            title=title,
            message=message,
            channels=['email', 'sms', 'in_app'],
            template_name='import_status_change',
            context={'import_order': import_order, 'new_status': new_status},
            priority=3
        )
    
    @staticmethod
    def notify_inquiry_response(inquiry, response_message):
        """Notify user about inquiry response"""
        title = f"Response to Your Inquiry: {inquiry.subject}"
        message = f"You have received a response to your inquiry."
        
        NotificationManager.send_notification(
            recipient=inquiry.customer,
            title=title,
            message=message,
            channels=['email', 'in_app'],
            template_name='inquiry_response',
            context={'inquiry': inquiry, 'response': response_message},
            priority=2
        )
    
    @staticmethod
    def notify_car_approval(car, approved=True):
        """Notify vendor about car listing approval/rejection"""
        status = "approved" if approved else "rejected"
        title = f"Car Listing {status.title()}"
        message = f"Your car listing '{car.make} {car.model}' has been {status}."
        
        NotificationManager.send_notification(
            recipient=car.vendor.user,
            title=title,
            message=message,
            channels=['email', 'in_app'],
            template_name='car_approval',
            context={'car': car, 'approved': approved},
            priority=2
        )
