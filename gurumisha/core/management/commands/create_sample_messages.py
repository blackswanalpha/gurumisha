"""
Django management command to create sample messages for testing
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Message
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample messages for testing the messaging system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of sample messages to create (default: 5)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create an admin user to be the message creator
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='admin').first()
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No admin user found. Please create an admin user first.')
            )
            return

        # Sample message data
        sample_messages = [
            {
                'title': 'Welcome to Gurumisha Motors!',
                'content': '<p>Welcome to Gurumisha Motors, your trusted partner for quality vehicles and automotive services. We\'re excited to have you join our community!</p><p>Explore our wide range of vehicles and services designed to meet all your automotive needs.</p>',
                'excerpt': 'Welcome to Gurumisha Motors - your trusted automotive partner',
                'message_type': 'welcome',
                'target_audience': 'all',
                'priority': 2,
                'status': 'active',
                'show_as_popup': True,
                'show_as_banner': False,
                'show_in_dashboard': True,
                'background_color': '#ffffff',
                'text_color': '#000000',
                'icon_class': 'fas fa-car',
                'action_button_text': 'Explore Vehicles',
                'action_button_url': '/cars/',
                'action_button_color': '#dc2626',
            },
            {
                'title': 'New Vehicle Import Service Available',
                'content': '<p>We\'re excited to announce our new vehicle import service! Now you can order your dream car from Japan with full support and tracking.</p><p>Our import service includes:</p><ul><li>Professional vehicle sourcing</li><li>Complete documentation handling</li><li>Real-time tracking</li><li>Quality assurance</li></ul>',
                'excerpt': 'New vehicle import service now available with full tracking support',
                'message_type': 'announcement',
                'target_audience': 'customers',
                'priority': 3,
                'status': 'active',
                'show_as_popup': True,
                'show_as_banner': True,
                'show_in_dashboard': True,
                'background_color': '#f0f9ff',
                'text_color': '#1e40af',
                'icon_class': 'fas fa-ship',
                'action_button_text': 'Learn More',
                'action_button_url': '/import-request/',
                'action_button_color': '#1e40af',
            },
            {
                'title': 'System Maintenance Scheduled',
                'content': '<p>We will be performing scheduled maintenance on our systems this weekend to improve performance and add new features.</p><p><strong>Maintenance Window:</strong> Saturday 2:00 AM - 6:00 AM EAT</p><p>During this time, some services may be temporarily unavailable. We apologize for any inconvenience.</p>',
                'excerpt': 'Scheduled system maintenance this weekend - some services may be temporarily unavailable',
                'message_type': 'maintenance',
                'target_audience': 'all',
                'priority': 4,
                'status': 'active',
                'show_as_popup': True,
                'show_as_banner': True,
                'show_in_dashboard': True,
                'background_color': '#fef3c7',
                'text_color': '#92400e',
                'icon_class': 'fas fa-tools',
                'expiration_date': timezone.now() + timedelta(days=7),
            },
            {
                'title': 'Special Promotion: 10% Off Spare Parts',
                'content': '<p>🎉 <strong>Limited Time Offer!</strong> Get 10% off all genuine spare parts this month.</p><p>Whether you need engine parts, brake components, or accessories, we have you covered with authentic parts at great prices.</p><p><em>Offer valid until the end of this month. Terms and conditions apply.</em></p>',
                'excerpt': 'Limited time: 10% off all genuine spare parts this month',
                'message_type': 'promotion',
                'target_audience': 'customers',
                'priority': 3,
                'status': 'active',
                'show_as_popup': True,
                'show_as_banner': False,
                'show_in_dashboard': True,
                'background_color': '#f0fdf4',
                'text_color': '#166534',
                'icon_class': 'fas fa-percentage',
                'action_button_text': 'Shop Now',
                'action_button_url': '/spare-parts/',
                'action_button_color': '#16a34a',
                'expiration_date': timezone.now() + timedelta(days=30),
            },
            {
                'title': 'Vendor Dashboard Updates',
                'content': '<p>We\'ve updated the vendor dashboard with new features to help you manage your listings more effectively:</p><ul><li>Enhanced analytics and reporting</li><li>Improved inventory management</li><li>New customer communication tools</li><li>Mobile-optimized interface</li></ul><p>Log in to your vendor dashboard to explore these new features!</p>',
                'excerpt': 'New vendor dashboard features: enhanced analytics, inventory management, and more',
                'message_type': 'feature',
                'target_audience': 'vendors',
                'priority': 2,
                'status': 'active',
                'show_as_popup': False,
                'show_as_banner': False,
                'show_in_dashboard': True,
                'background_color': '#fdf4ff',
                'text_color': '#7c2d12',
                'icon_class': 'fas fa-chart-line',
                'action_button_text': 'View Dashboard',
                'action_button_url': '/dashboard/vendor/',
                'action_button_color': '#9333ea',
            },
        ]

        created_count = 0
        for i, message_data in enumerate(sample_messages[:count]):
            # Check if message with this title already exists
            if Message.objects.filter(title=message_data['title']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Message "{message_data["title"]}" already exists, skipping...')
                )
                continue

            # Create the message
            message_data['created_by'] = admin_user
            message = Message.objects.create(**message_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'Created message: "{message.title}"')
            )
            created_count += 1

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully created {created_count} sample messages!')
            )
            self.stdout.write(
                'You can now visit /dashboard/admin/message-management/ to view and manage these messages.'
            )
        else:
            self.stdout.write(
                self.style.WARNING('No new messages were created (they may already exist).')
            )
