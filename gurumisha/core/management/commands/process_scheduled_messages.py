"""
Django management command to process scheduled messages
Run this command periodically (e.g., via cron) to handle message scheduling
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from core.models import Message, MessageSchedule, MessageAnalytics
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled messages and update their status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS('Starting scheduled message processing...')
            )

        # Process scheduled messages
        activated_count = self.activate_scheduled_messages(dry_run, verbose)
        expired_count = self.expire_active_messages(dry_run, verbose)
        recurring_count = self.process_recurring_messages(dry_run, verbose)
        
        # Create daily analytics
        analytics_count = self.create_daily_analytics(dry_run, verbose)

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Processing complete:\n'
                f'  - Activated messages: {activated_count}\n'
                f'  - Expired messages: {expired_count}\n'
                f'  - Recurring messages processed: {recurring_count}\n'
                f'  - Analytics records created: {analytics_count}'
            )
        )

    def activate_scheduled_messages(self, dry_run=False, verbose=False):
        """Activate messages that are scheduled to start now"""
        now = timezone.now()
        
        # Find scheduled messages that should be activated
        scheduled_messages = Message.objects.filter(
            status='scheduled',
            publication_date__lte=now
        )
        
        count = 0
        for message in scheduled_messages:
            if verbose:
                self.stdout.write(f'Activating message: {message.title}')
            
            if not dry_run:
                message.status = 'active'
                message.save()
                
                # Log the activation
                logger.info(f'Activated scheduled message: {message.title} (ID: {message.id})')
            
            count += 1
        
        return count

    def expire_active_messages(self, dry_run=False, verbose=False):
        """Expire messages that have reached their expiration date"""
        now = timezone.now()
        
        # Find active messages that should be expired
        expired_messages = Message.objects.filter(
            status='active',
            expiration_date__lte=now
        )
        
        count = 0
        for message in expired_messages:
            if verbose:
                self.stdout.write(f'Expiring message: {message.title}')
            
            if not dry_run:
                message.status = 'expired'
                message.save()
                
                # Log the expiration
                logger.info(f'Expired message: {message.title} (ID: {message.id})')
            
            count += 1
        
        return count

    def process_recurring_messages(self, dry_run=False, verbose=False):
        """Process recurring message schedules"""
        now = timezone.now()
        
        # Find schedules that need to be processed
        schedules = MessageSchedule.objects.filter(
            is_active=True,
            next_send_at__lte=now
        ).select_related('message')
        
        count = 0
        for schedule in schedules:
            if verbose:
                self.stdout.write(f'Processing recurring schedule for: {schedule.message.title}')
            
            if not dry_run:
                # Create a new message instance for recurring messages
                if schedule.frequency != 'once':
                    original_message = schedule.message
                    
                    # Create new message instance
                    new_message = Message.objects.create(
                        title=f"{original_message.title} ({now.strftime('%Y-%m-%d')})",
                        content=original_message.content,
                        excerpt=original_message.excerpt,
                        message_type=original_message.message_type,
                        target_audience=original_message.target_audience,
                        priority=original_message.priority,
                        status='active',
                        show_as_popup=original_message.show_as_popup,
                        show_as_banner=original_message.show_as_banner,
                        show_in_dashboard=original_message.show_in_dashboard,
                        background_color=original_message.background_color,
                        text_color=original_message.text_color,
                        icon_class=original_message.icon_class,
                        action_button_text=original_message.action_button_text,
                        action_button_url=original_message.action_button_url,
                        action_button_color=original_message.action_button_color,
                        publication_date=now,
                        created_by=original_message.created_by
                    )
                    
                    logger.info(f'Created recurring message: {new_message.title} (ID: {new_message.id})')
                
                # Update schedule
                schedule.mark_sent()
                
                # Check if schedule should be deactivated
                if schedule.max_occurrences and schedule.occurrences_sent >= schedule.max_occurrences:
                    schedule.is_active = False
                    schedule.save()
                    logger.info(f'Deactivated completed schedule for: {schedule.message.title}')
                elif schedule.end_date and now.date() > schedule.end_date:
                    schedule.is_active = False
                    schedule.save()
                    logger.info(f'Deactivated expired schedule for: {schedule.message.title}')
            
            count += 1
        
        return count

    def create_daily_analytics(self, dry_run=False, verbose=False):
        """Create daily analytics records for active messages"""
        from datetime import date
        today = date.today()
        
        # Find active messages that don't have analytics for today
        active_messages = Message.objects.filter(status='active')
        
        count = 0
        for message in active_messages:
            # Check if analytics already exist for today
            if not MessageAnalytics.objects.filter(message=message, date=today).exists():
                if verbose:
                    self.stdout.write(f'Creating analytics for: {message.title}')
                
                if not dry_run:
                    MessageAnalytics.objects.create(
                        message=message,
                        date=today
                    )
                
                count += 1
        
        return count

    def cleanup_old_analytics(self, dry_run=False, verbose=False, days=90):
        """Clean up old analytics records (optional)"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        old_analytics = MessageAnalytics.objects.filter(date__lt=cutoff_date)
        count = old_analytics.count()
        
        if count > 0:
            if verbose:
                self.stdout.write(f'Cleaning up {count} old analytics records')
            
            if not dry_run:
                old_analytics.delete()
                logger.info(f'Cleaned up {count} analytics records older than {days} days')
        
        return count

    def validate_message_targeting(self, dry_run=False, verbose=False):
        """Validate and process advanced message targeting rules"""
        from core.models import MessageTarget
        
        # Find messages with targeting rules
        messages_with_rules = Message.objects.filter(
            status='active',
            targeting_rules__isnull=False
        ).distinct()
        
        count = 0
        for message in messages_with_rules:
            if verbose:
                self.stdout.write(f'Validating targeting for: {message.title}')
            
            # This could be expanded to pre-calculate target user lists
            # for performance optimization
            count += 1
        
        return count
