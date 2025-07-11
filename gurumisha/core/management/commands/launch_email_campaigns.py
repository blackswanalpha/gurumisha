"""
Management command to launch promotional email campaigns
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from core.models import User, HotDeal, Car, Vendor
from core.email_service import PromotionEmailService


class Command(BaseCommand):
    help = 'Launch promotional email campaigns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-type',
            type=str,
            choices=['hot_deals', 'featured_cars', 'weekly_digest', 'welcome_series'],
            help='Type of email campaign to launch',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--target-audience',
            type=str,
            choices=['all', 'customers', 'vendors', 'new_users'],
            default='all',
            help='Target audience for the campaign',
        )

    def handle(self, *args, **options):
        campaign_type = options.get('campaign_type')
        dry_run = options['dry_run']
        target_audience = options['target_audience']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE - No emails will be sent'))
        
        email_service = PromotionEmailService()
        
        if campaign_type == 'hot_deals':
            self.launch_hot_deals_campaign(email_service, dry_run, target_audience)
        elif campaign_type == 'featured_cars':
            self.launch_featured_cars_campaign(email_service, dry_run, target_audience)
        elif campaign_type == 'weekly_digest':
            self.launch_weekly_digest(email_service, dry_run, target_audience)
        elif campaign_type == 'welcome_series':
            self.launch_welcome_series(email_service, dry_run, target_audience)
        else:
            self.show_campaign_options()

    def launch_hot_deals_campaign(self, email_service, dry_run=False, target_audience='all'):
        """Launch hot deals email campaign"""
        self.stdout.write('🔥 Launching Hot Deals Email Campaign...')
        
        # Get active hot deals
        active_deals = HotDeal.objects.filter(
            is_active=True,
            email_sent=False,
            car__is_approved=True
        ).select_related('car', 'car__brand', 'car__model')
        
        if not active_deals:
            self.stdout.write(self.style.WARNING('No new hot deals found to promote'))
            return
        
        # Get target recipients
        recipients = self.get_target_recipients(target_audience)
        if not recipients:
            self.stdout.write(self.style.WARNING('No recipients found for campaign'))
            return
        
        self.stdout.write(f'📧 Target Recipients: {len(recipients)} users')
        self.stdout.write(f'🔥 Hot Deals to Promote: {len(active_deals)}')
        
        sent_count = 0
        for deal in active_deals:
            self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Sending: {deal.title}')
            
            if not dry_run:
                success = email_service.send_hot_deal_notification(deal, recipients)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Sent hot deal email for {deal.title}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to send email for {deal.title}')
                    )
            else:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Would send hot deal email for {deal.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎯 Hot Deals Campaign Complete! {"Would send" if dry_run else "Sent"} {sent_count} emails'
            )
        )

    def launch_featured_cars_campaign(self, email_service, dry_run=False, target_audience='all'):
        """Launch featured cars announcement campaign"""
        self.stdout.write('⭐ Launching Featured Cars Campaign...')
        
        # Get recently featured cars (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        featured_cars = Car.objects.filter(
            is_approved=True,
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum'],
            updated_at__gte=week_ago
        ).select_related('brand', 'model', 'vendor')
        
        if not featured_cars:
            self.stdout.write(self.style.WARNING('No recently featured cars found'))
            return
        
        recipients = self.get_target_recipients(target_audience)
        if not recipients:
            self.stdout.write(self.style.WARNING('No recipients found for campaign'))
            return
        
        self.stdout.write(f'📧 Target Recipients: {len(recipients)} users')
        self.stdout.write(f'⭐ Featured Cars: {len(featured_cars)}')
        
        # Group cars by tier for better email organization
        cars_by_tier = {}
        for car in featured_cars:
            tier = car.featured_tier
            if tier not in cars_by_tier:
                cars_by_tier[tier] = []
            cars_by_tier[tier].append(car)
        
        if not dry_run:
            # Send featured cars digest email
            from django.template.loader import render_to_string
            
            context = {
                'cars_by_tier': cars_by_tier,
                'total_cars': len(featured_cars),
                'site_url': email_service.site_url
            }
            
            # This would need a featured cars email template
            self.stdout.write(
                self.style.SUCCESS(f'✅ Would send featured cars digest to {len(recipients)} recipients')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Would send featured cars digest to {len(recipients)} recipients')
            )

    def launch_weekly_digest(self, email_service, dry_run=False, target_audience='all'):
        """Launch weekly promotional digest"""
        self.stdout.write('📰 Launching Weekly Digest Campaign...')
        
        recipients = self.get_target_recipients(target_audience)
        if not recipients:
            self.stdout.write(self.style.WARNING('No recipients found for weekly digest'))
            return
        
        self.stdout.write(f'📧 Target Recipients: {len(recipients)} users')
        
        if not dry_run:
            success = email_service.send_weekly_promotion_digest()
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Weekly digest sent to {len(recipients)} recipients')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to send weekly digest')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Would send weekly digest to {len(recipients)} recipients')
            )

    def launch_welcome_series(self, email_service, dry_run=False, target_audience='new_users'):
        """Launch welcome email series for new users"""
        self.stdout.write('👋 Launching Welcome Series Campaign...')
        
        # Get users who joined in the last 7 days and haven't received welcome emails
        week_ago = timezone.now() - timedelta(days=7)
        new_users = User.objects.filter(
            date_joined__gte=week_ago,
            notification_preferences__email_enabled=True
        )
        
        if not new_users:
            self.stdout.write(self.style.WARNING('No new users found for welcome series'))
            return
        
        self.stdout.write(f'👋 New Users: {len(new_users)}')
        
        sent_count = 0
        for user in new_users:
            if not dry_run:
                # Send personalized welcome email with recommendations
                success = email_service.send_personalized_recommendations(user)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Sent welcome email to {user.email}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ No recommendations available for {user.email}')
                    )
            else:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Would send welcome email to {user.email}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'👋 Welcome Series Complete! {"Would send" if dry_run else "Sent"} {sent_count} emails'
            )
        )

    def get_target_recipients(self, target_audience):
        """Get email recipients based on target audience"""
        if target_audience == 'customers':
            return User.objects.filter(
                notification_preferences__email_enabled=True,
                notification_preferences__email_marketing=True,
                role='customer'
            ).values_list('email', flat=True)
        elif target_audience == 'vendors':
            return User.objects.filter(
                notification_preferences__email_enabled=True,
                notification_preferences__email_marketing=True,
                role='vendor'
            ).values_list('email', flat=True)
        elif target_audience == 'new_users':
            week_ago = timezone.now() - timedelta(days=7)
            return User.objects.filter(
                notification_preferences__email_enabled=True,
                date_joined__gte=week_ago
            ).values_list('email', flat=True)
        else:  # 'all'
            return User.objects.filter(
                notification_preferences__email_enabled=True,
                notification_preferences__email_marketing=True,
                role__in=['customer', 'vendor']
            ).values_list('email', flat=True)

    def show_campaign_options(self):
        """Show available campaign options"""
        self.stdout.write('📧 Available Email Campaigns:')
        self.stdout.write('')
        self.stdout.write('🔥 Hot Deals Campaign:')
        self.stdout.write('   python manage.py launch_email_campaigns --campaign-type=hot_deals')
        self.stdout.write('')
        self.stdout.write('⭐ Featured Cars Campaign:')
        self.stdout.write('   python manage.py launch_email_campaigns --campaign-type=featured_cars')
        self.stdout.write('')
        self.stdout.write('📰 Weekly Digest:')
        self.stdout.write('   python manage.py launch_email_campaigns --campaign-type=weekly_digest')
        self.stdout.write('')
        self.stdout.write('👋 Welcome Series:')
        self.stdout.write('   python manage.py launch_email_campaigns --campaign-type=welcome_series')
        self.stdout.write('')
        self.stdout.write('🎯 Target Audiences: all, customers, vendors, new_users')
        self.stdout.write('🧪 Add --dry-run to test without sending emails')

    def display_campaign_summary(self):
        """Display summary of current promotional status"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📧 EMAIL CAMPAIGN STATUS')
        self.stdout.write('='*60)
        
        # Hot deals ready for email
        pending_deals = HotDeal.objects.filter(
            is_active=True,
            email_sent=False
        ).count()
        
        # Email subscribers
        total_subscribers = User.objects.filter(
            notification_preferences__email_enabled=True,
            notification_preferences__email_marketing=True
        ).count()
        customer_subscribers = User.objects.filter(
            notification_preferences__email_enabled=True,
            notification_preferences__email_marketing=True,
            role='customer'
        ).count()
        vendor_subscribers = User.objects.filter(
            notification_preferences__email_enabled=True,
            notification_preferences__email_marketing=True,
            role='vendor'
        ).count()
        
        self.stdout.write(f'🔥 Hot Deals Ready for Email: {pending_deals}')
        self.stdout.write(f'📧 Total Email Subscribers: {total_subscribers}')
        self.stdout.write(f'   - Customers: {customer_subscribers}')
        self.stdout.write(f'   - Vendors: {vendor_subscribers}')
        
        # Recent activity
        week_ago = timezone.now() - timedelta(days=7)
        new_users = User.objects.filter(date_joined__gte=week_ago).count()
        new_featured = Car.objects.filter(
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum'],
            updated_at__gte=week_ago
        ).count()
        
        self.stdout.write(f'👋 New Users (Last 7 Days): {new_users}')
        self.stdout.write(f'⭐ Recently Featured Cars: {new_featured}')
        
        self.stdout.write('\n' + '='*60)
