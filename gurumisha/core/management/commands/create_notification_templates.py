"""
Management command to create default notification templates
"""

from django.core.management.base import BaseCommand
from core.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create default notification templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating default notification templates...')

        templates = [
            {
                'name': 'order_status_change',
                'template_type': 'email',
                'subject_template': 'Order #{order.id} Status Update - Gurumisha Motors',
                'body_template': '''
Dear {recipient.first_name},

Your order #{order.id} status has been updated to: {new_status}

Order Details:
- Order Number: #{order.id}
- Total Amount: KES {order.total_amount}
- Status: {new_status}

You can track your order at: {tracking_url}

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'order', 'new_status', 'tracking_url'],
                'priority': 2,
            },
            {
                'name': 'order_status_change',
                'template_type': 'in_app',
                'subject_template': 'Order #{order.id} Status Update',
                'body_template': 'Your order status has been updated to: {new_status}',
                'available_variables': ['order', 'new_status'],
                'priority': 2,
            },
            {
                'name': 'import_status_change',
                'template_type': 'email',
                'subject_template': 'Import Order {import_order.order_number} Update - Gurumisha Motors',
                'body_template': '''
Dear {recipient.first_name},

Your import order {import_order.order_number} status has been updated.

Import Details:
- Order Number: {import_order.order_number}
- Vehicle: {import_order.vehicle_details}
- Status: {new_status}
- Estimated Arrival: {import_order.estimated_arrival_date}

Track your import: {tracking_url}

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'import_order', 'new_status', 'tracking_url'],
                'priority': 3,
            },
            {
                'name': 'import_status_change',
                'template_type': 'sms',
                'subject_template': '',
                'body_template': 'Gurumisha Motors: Your import order {import_order.order_number} status: {new_status}. Track: {tracking_url}',
                'available_variables': ['import_order', 'new_status', 'tracking_url'],
                'priority': 3,
            },
            {
                'name': 'inquiry_response',
                'template_type': 'email',
                'subject_template': 'Response to Your Inquiry - {inquiry.subject}',
                'body_template': '''
Dear {recipient.first_name},

You have received a response to your inquiry about: {inquiry.subject}

Response:
{response}

Original Inquiry:
{inquiry.message}

You can view the full conversation in your dashboard: {dashboard_url}

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'inquiry', 'response', 'dashboard_url'],
                'priority': 2,
            },
            {
                'name': 'car_approval',
                'template_type': 'email',
                'subject_template': 'Car Listing {status} - {car.make} {car.model}',
                'body_template': '''
Dear {recipient.first_name},

Your car listing has been {status}.

Vehicle Details:
- Make: {car.make}
- Model: {car.model}
- Year: {car.year}
- Price: KES {car.price}

{approval_message}

Manage your listings: {dashboard_url}

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'car', 'status', 'approval_message', 'dashboard_url'],
                'priority': 2,
            },
            {
                'name': 'welcome_user',
                'template_type': 'email',
                'subject_template': 'Welcome to Gurumisha Motors!',
                'body_template': '''
Dear {recipient.first_name},

Welcome to Gurumisha Motors! We're excited to have you join our automotive community.

Your account has been successfully created. You can now:
- Browse our extensive car inventory
- Request car imports from Japan
- Shop for genuine spare parts
- Connect with trusted vendors

Get started: {dashboard_url}

If you have any questions, our support team is here to help.

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'dashboard_url'],
                'priority': 1,
            },
            {
                'name': 'payment_confirmation',
                'template_type': 'email',
                'subject_template': 'Payment Confirmation - Order #{order.id}',
                'body_template': '''
Dear {recipient.first_name},

Your payment has been successfully processed.

Payment Details:
- Order Number: #{order.id}
- Amount Paid: KES {payment.amount}
- Payment Method: {payment.payment_method}
- Transaction ID: {payment.transaction_id}
- Date: {payment.created_at}

Your order is now being processed.

Best regards,
Gurumisha Motors Team
                ''',
                'available_variables': ['recipient', 'order', 'payment'],
                'priority': 3,
            },
            {
                'name': 'low_stock_alert',
                'template_type': 'email',
                'subject_template': 'Low Stock Alert - {spare_part.name}',
                'body_template': '''
Dear {recipient.first_name},

This is an automated alert to inform you that the following spare part is running low on stock:

Part Details:
- Name: {spare_part.name}
- SKU: {spare_part.sku}
- Current Stock: {current_stock}
- Minimum Threshold: {threshold}

Please restock this item to avoid stockouts.

Manage inventory: {inventory_url}

Best regards,
Gurumisha Motors System
                ''',
                'available_variables': ['recipient', 'spare_part', 'current_stock', 'threshold', 'inventory_url'],
                'priority': 2,
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                template_type=template_data['template_type'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created template: {template.name} ({template.template_type})'
                    )
                )
            else:
                # Update existing template
                for key, value in template_data.items():
                    setattr(template, key, value)
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'↻ Updated template: {template.name} ({template.template_type})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new templates, updated {updated_count} existing templates.'
            )
        )
