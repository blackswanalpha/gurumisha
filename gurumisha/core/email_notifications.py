"""
Email notification system for import order tracking
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import ImportOrder, ImportOrderStatusHistory, VerificationCode


def send_status_update_email(import_order, new_status, previous_status=None, change_reason=None, estimated_date=None):
    """
    Send email notification when import order status changes
    """
    try:
        # Get email template based on status
        template_name = f'core/emails/import_status_{new_status}.html'
        fallback_template = 'core/emails/import_status_generic.html'
        
        # Context for email template
        context = {
            'order': import_order,
            'customer': import_order.customer,
            'new_status': new_status,
            'previous_status': previous_status,
            'change_reason': change_reason,
            'estimated_date': estimated_date,
            'status_display': dict(ImportOrder.STATUS_CHOICES).get(new_status, new_status),
            'progress_percentage': import_order.progress_percentage,
            'current_stage': import_order.current_stage_number,
            'tracking_url': f"{settings.SITE_URL}/import/tracking/{import_order.order_number}/",
        }
        
        # Try to render specific template, fall back to generic
        try:
            html_message = render_to_string(template_name, context)
        except:
            html_message = render_to_string(fallback_template, context)
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Email subject based on status
        subject_map = {
            'confirmed': f'Order Confirmed - {import_order.order_number}',
            'auction_won': f'Auction Won - {import_order.order_number}',
            'shipped': f'Vehicle Shipped - {import_order.order_number}',
            'in_transit': f'In Transit - {import_order.order_number}',
            'arrived_docked': f'Vehicle Arrived - {import_order.order_number}',
            'under_clearance': f'Customs Clearance - {import_order.order_number}',
            'registered': f'Vehicle Registered - {import_order.order_number}',
            'ready_for_dispatch': f'Ready for Delivery - {import_order.order_number}',
            'delivered': f'Vehicle Delivered - {import_order.order_number}',
            'cancelled': f'Order Cancelled - {import_order.order_number}',
        }
        
        subject = subject_map.get(new_status, f'Status Update - {import_order.order_number}')
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[import_order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Failed to send email notification: {e}")
        return False


def send_welcome_email(import_order):
    """
    Send welcome email when import order is created
    """
    try:
        context = {
            'order': import_order,
            'customer': import_order.customer,
            'tracking_url': f"{settings.SITE_URL}/import/tracking/{import_order.order_number}/",
        }
        
        html_message = render_to_string('core/emails/import_welcome.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'Import Order Created - {import_order.order_number}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[import_order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False


def send_document_notification_email(import_order, document):
    """
    Send email notification when new document is uploaded
    """
    try:
        context = {
            'order': import_order,
            'customer': import_order.customer,
            'document': document,
            'tracking_url': f"{settings.SITE_URL}/import/tracking/{import_order.order_number}/",
        }
        
        html_message = render_to_string('core/emails/import_document_uploaded.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'New Document Available - {import_order.order_number}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[import_order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send document notification email: {e}")
        return False


def send_delivery_reminder_email(import_order):
    """
    Send reminder email when vehicle is ready for delivery
    """
    try:
        context = {
            'order': import_order,
            'customer': import_order.customer,
            'tracking_url': f"{settings.SITE_URL}/import/tracking/{import_order.order_number}/",
        }
        
        html_message = render_to_string('core/emails/import_delivery_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'Vehicle Ready for Delivery - {import_order.order_number}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[import_order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send delivery reminder email: {e}")
        return False


def send_weekly_status_digest(customer):
    """
    Send weekly digest of all active import orders for a customer
    """
    try:
        active_orders = ImportOrder.objects.filter(
            customer=customer
        ).exclude(status__in=['delivered', 'cancelled']).order_by('-created_at')
        
        if not active_orders.exists():
            return True  # No active orders, no need to send digest
        
        context = {
            'customer': customer,
            'orders': active_orders,
            'tracking_url': f"{settings.SITE_URL}/import/tracking/",
        }
        
        html_message = render_to_string('core/emails/import_weekly_digest.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Weekly Import Status Update - Gurumisha Motors',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send weekly digest: {e}")
        return False


# Signal handlers for automatic email notifications
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ImportOrder)
def handle_import_order_created(sender, instance, created, **kwargs):
    """
    Send welcome email when new import order is created
    """
    if created:
        send_welcome_email(instance)


@receiver(post_save, sender=ImportOrderStatusHistory)
def handle_status_change(sender, instance, created, **kwargs):
    """
    Send notification email when status changes
    """
    if created:
        send_status_update_email(
            import_order=instance.import_order,
            new_status=instance.new_status,
            previous_status=instance.previous_status,
            change_reason=instance.change_reason,
            estimated_date=instance.estimated_date
        )
        
        # Mark notification as sent
        instance.customer_notification_sent = True
        instance.save(update_fields=['customer_notification_sent'])


# Utility functions for batch operations
def send_bulk_status_notifications(orders_queryset, new_status, change_reason=None):
    """
    Send status update notifications to multiple orders
    """
    success_count = 0
    for order in orders_queryset:
        if send_status_update_email(order, new_status, change_reason=change_reason):
            success_count += 1
    
    return success_count


def send_overdue_notifications():
    """
    Send notifications for orders that are overdue based on estimated dates
    """
    from datetime import timedelta
    
    overdue_orders = ImportOrder.objects.filter(
        estimated_arrival_date__lt=timezone.now().date() - timedelta(days=3),
        status__in=['in_transit', 'shipped']
    )
    
    for order in overdue_orders:
        send_status_update_email(
            order,
            order.status,
            change_reason="Your shipment may be delayed. We're investigating and will update you soon."
        )


def send_verification_code_email(user, verification_code):
    """
    Send email with verification code (alternative to UUID token)
    """
    try:
        context = {
            'user': user,
            'verification_code': verification_code.code,
            'expiry_minutes': 15,  # Code expires in 15 minutes
            'site_name': 'Gurumisha Motors',
        }

        html_message = render_to_string('core/auth/verification_code_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Your Verification Code - Gurumisha Motors',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Failed to send verification code email: {e}")
        return False


def send_password_reset_code_email(user, verification_code):
    """
    Send email with password reset code
    """
    try:
        context = {
            'user': user,
            'verification_code': verification_code.code,
            'expiry_minutes': 15,
            'site_name': 'Gurumisha Motors',
        }

        html_message = render_to_string('core/auth/password_reset_code_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Password Reset Code - Gurumisha Motors',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Failed to send password reset code email: {e}")
        return False


# ============================================================================
# INQUIRY EMAIL NOTIFICATIONS
# ============================================================================

def send_inquiry_response_email(inquiry, response):
    """
    Send email notification to customer when admin responds to their inquiry
    """
    try:
        from django.core.mail import EmailMultiAlternatives

        # Email subject
        subject = f"Response to your inquiry: {inquiry.subject}"

        # Email context
        context = {
            'inquiry': inquiry,
            'response': response,
            'customer': inquiry.customer,
            'admin': response.sender,
            'site_name': 'Gurumisha Motors',
            'site_url': getattr(settings, 'SITE_URL', 'https://gurumisha.com'),
            'inquiry_url': f"{getattr(settings, 'SITE_URL', 'https://gurumisha.com')}/dashboard/customer/inquiries/{inquiry.id}/",
        }

        # Render email templates
        text_content = render_to_string('emails/inquiry_response.txt', context)
        html_content = render_to_string('emails/inquiry_response.html', context)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kamandembugua18@gmail.com'),
            to=[inquiry.customer.email],
            reply_to=[getattr(settings, 'SUPPORT_EMAIL', 'kamandembugua18@gmail.com')]
        )

        # Attach HTML version
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        print(f"Inquiry response email sent to {inquiry.customer.email} for inquiry {inquiry.id}")
        return True

    except Exception as e:
        print(f"Failed to send inquiry response email: {e}")
        return False


def send_inquiry_status_update_email(inquiry, old_status, new_status):
    """
    Send email notification when inquiry status changes
    """
    try:
        from django.core.mail import EmailMultiAlternatives

        # Only send for significant status changes
        significant_statuses = ['resolved', 'closed']
        if new_status not in significant_statuses:
            return True

        # Email subject
        subject_map = {
            'resolved': f"Your inquiry has been resolved: {inquiry.subject}",
            'closed': f"Your inquiry has been closed: {inquiry.subject}",
        }
        subject = subject_map.get(new_status, f"Status update for your inquiry: {inquiry.subject}")

        # Email context
        context = {
            'inquiry': inquiry,
            'old_status': old_status,
            'new_status': new_status,
            'customer': inquiry.customer,
            'site_name': 'Gurumisha Motors',
            'site_url': getattr(settings, 'SITE_URL', 'https://gurumisha.com'),
            'inquiry_url': f"{getattr(settings, 'SITE_URL', 'https://gurumisha.com')}/dashboard/customer/inquiries/{inquiry.id}/",
        }

        # Create simple email for now
        message = f"""
Dear {inquiry.customer.get_full_name() or inquiry.customer.username},

Your inquiry "{inquiry.subject}" has been {new_status}.

You can view the details at: {context['inquiry_url']}

Best regards,
Gurumisha Motors Team
        """

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kamandembugua18@gmail.com'),
            recipient_list=[inquiry.customer.email],
            fail_silently=False,
        )

        print(f"Inquiry status update email sent to {inquiry.customer.email} for inquiry {inquiry.id}")
        return True

    except Exception as e:
        print(f"Failed to send inquiry status update email: {e}")
        return False


def send_inquiry_assignment_notification(inquiry, admin_user):
    """
    Send email notification to admin when inquiry is assigned to them
    """
    try:
        # Email subject
        subject = f"New inquiry assigned to you: {inquiry.subject}"

        # Email message
        message = f"""
Dear {admin_user.get_full_name() or admin_user.username},

A new inquiry has been assigned to you:

Subject: {inquiry.subject}
Customer: {inquiry.customer.get_full_name() or inquiry.customer.username}
Priority: {inquiry.get_priority_display()}
Type: {inquiry.get_inquiry_type_display()}

Please review and respond at: {getattr(settings, 'SITE_URL', 'https://gurumisha.com')}/dashboard/admin/queries/{inquiry.id}/

Best regards,
Gurumisha Motors System
        """

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kamandembugua18@gmail.com'),
            recipient_list=[admin_user.email],
            fail_silently=False,
        )

        print(f"Inquiry assignment email sent to {admin_user.email} for inquiry {inquiry.id}")
        return True

    except Exception as e:
        print(f"Failed to send inquiry assignment email: {e}")
        return False


def send_new_inquiry_notification(inquiry):
    """
    Send email notification to admins when new inquiry is created
    """
    try:
        # Get all admin users
        from .models import User
        admin_users = User.objects.filter(role='admin', is_active=True)

        if not admin_users.exists():
            return True

        # Email subject
        subject = f"New customer inquiry: {inquiry.subject}"

        # Email message
        message = f"""
A new customer inquiry has been received:

Subject: {inquiry.subject}
Customer: {inquiry.customer.get_full_name() or inquiry.customer.username}
Email: {inquiry.customer.email}
Type: {inquiry.get_inquiry_type_display()}
Priority: {inquiry.get_priority_display()}

Message:
{inquiry.message}

Please review and respond at: {getattr(settings, 'SITE_URL', 'https://gurumisha.com')}/dashboard/admin/queries/{inquiry.id}/

Best regards,
Gurumisha Motors System
        """

        # Send to all admin users
        admin_emails = [admin.email for admin in admin_users]

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kamandembugua18@gmail.com'),
            recipient_list=admin_emails,
            fail_silently=False,
        )

        print(f"New inquiry notification emails sent for inquiry {inquiry.id}")
        return True

    except Exception as e:
        print(f"Failed to send new inquiry notification emails: {e}")
        return False
