"""
Management command for sending promotional emails
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import HotDeal, User, Vendor
from core.email_service import PromotionEmailService


class Command(BaseCommand):
    help = 'Send promotional emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            choices=['hot_deals', 'weekly_digest', 'vendor_summaries', 'recommendations'],
            help='Type of promotional email to send'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--deal-id',
            type=int,
            help='Specific hot deal ID for hot deal notifications'
        )
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Specific vendor ID for vendor summaries'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID for recommendations'
        )

    def handle(self, *args, **options):
        email_type = options['type']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))

        email_service = PromotionEmailService()

        if email_type == 'hot_deals':
            self.send_hot_deal_notifications(email_service, dry_run, options.get('deal_id'))
        elif email_type == 'weekly_digest':
            self.send_weekly_digest(email_service, dry_run)
        elif email_type == 'vendor_summaries':
            self.send_vendor_summaries(email_service, dry_run, options.get('vendor_id'))
        elif email_type == 'recommendations':
            self.send_recommendations(email_service, dry_run, options.get('user_id'))

    def send_hot_deal_notifications(self, email_service, dry_run=False, deal_id=None):
        """Send hot deal notifications"""
        self.stdout.write('Sending hot deal notifications...')
        
        if deal_id:
            # Send for specific deal
            try:
                deal = HotDeal.objects.get(id=deal_id, is_active=True)
                deals = [deal]
            except HotDeal.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Hot deal with ID {deal_id} not found'))
                return
        else:
            # Send for all active deals that haven't been emailed yet
            deals = HotDeal.objects.filter(
                is_active=True,
                email_sent=False,
                car__is_approved=True
            ).select_related('car', 'car__brand', 'car__model')
        
        if not deals:
            self.stdout.write(self.style.WARNING('No hot deals found to send notifications for'))
            return
        
        # Get recipients
        recipients = User.objects.filter(
            email_notifications=True,
            role__in=['customer', 'vendor']
        ).values_list('email', flat=True)
        
        if not recipients:
            self.stdout.write(self.style.WARNING('No recipients found for hot deal notifications'))
            return
        
        sent_count = 0
        for deal in deals:
            self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Sending notification for: {deal.title}')
            
            if not dry_run:
                success = email_service.send_hot_deal_notification(deal, recipients)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sent notification for {deal.title} to {len(recipients)} recipients')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to send notification for {deal.title}')
                    )
            else:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Would send notification for {deal.title} to {len(recipients)} recipients')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{"[DRY RUN] " if dry_run else ""}Sent {sent_count} hot deal notifications')
        )

    def send_weekly_digest(self, email_service, dry_run=False):
        """Send weekly promotion digest"""
        self.stdout.write('Sending weekly promotion digest...')
        
        # Get subscribers
        subscribers = User.objects.filter(
            email_notifications=True,
            role__in=['customer', 'vendor']
        ).values_list('email', flat=True)
        
        if not subscribers:
            self.stdout.write(self.style.WARNING('No subscribers found for weekly digest'))
            return
        
        self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Sending digest to {len(subscribers)} subscribers')
        
        if not dry_run:
            success = email_service.send_weekly_promotion_digest()
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Weekly digest sent successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send weekly digest')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Would send weekly digest to {len(subscribers)} subscribers')
            )

    def send_vendor_summaries(self, email_service, dry_run=False, vendor_id=None):
        """Send vendor promotion summaries"""
        self.stdout.write('Sending vendor promotion summaries...')
        
        if vendor_id:
            # Send for specific vendor
            try:
                vendor = Vendor.objects.get(id=vendor_id, is_approved=True)
                vendors = [vendor]
            except Vendor.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Vendor with ID {vendor_id} not found'))
                return
        else:
            # Send for all approved vendors
            vendors = Vendor.objects.filter(
                is_approved=True,
                email_notifications=True
            ).select_related('user')
        
        if not vendors:
            self.stdout.write(self.style.WARNING('No vendors found for promotion summaries'))
            return
        
        sent_count = 0
        for vendor in vendors:
            self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Sending summary to: {vendor.company_name}')
            
            if not dry_run:
                success = email_service.send_vendor_promotion_summary(vendor)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sent summary to {vendor.company_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to send summary to {vendor.company_name}')
                    )
            else:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Would send summary to {vendor.company_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{"[DRY RUN] " if dry_run else ""}Sent {sent_count} vendor summaries')
        )

    def send_recommendations(self, email_service, dry_run=False, user_id=None):
        """Send personalized recommendations"""
        self.stdout.write('Sending personalized recommendations...')
        
        if user_id:
            # Send for specific user
            try:
                user = User.objects.get(id=user_id, email_notifications=True)
                users = [user]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            # Send for users who have rating history and haven't received recommendations recently
            from core.models import CarRating
            from datetime import timedelta
            
            # Get users with ratings who haven't received recommendations in the last week
            week_ago = timezone.now() - timedelta(days=7)
            users_with_ratings = CarRating.objects.filter(
                created_at__gte=week_ago
            ).values_list('customer_id', flat=True).distinct()
            
            users = User.objects.filter(
                id__in=users_with_ratings,
                email_notifications=True,
                role='customer'
            )
        
        if not users:
            self.stdout.write(self.style.WARNING('No users found for personalized recommendations'))
            return
        
        sent_count = 0
        for user in users:
            self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Sending recommendations to: {user.email}')
            
            if not dry_run:
                success = email_service.send_personalized_recommendations(user)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Sent recommendations to {user.email}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- No recommendations available for {user.email}')
                    )
            else:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Would send recommendations to {user.email}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'{"[DRY RUN] " if dry_run else ""}Sent {sent_count} personalized recommendations')
        )
