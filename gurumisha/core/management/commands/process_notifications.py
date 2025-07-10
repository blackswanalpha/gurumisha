"""
Management command to process notification queue
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.notification_manager import NotificationManager


class Command(BaseCommand):
    help = 'Process pending notifications in the queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Also retry failed notifications',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old notifications',
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=30,
            help='Number of days to keep old notifications (default: 30)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting notification processing at {timezone.now()}')
        )

        # Process scheduled notifications
        self.stdout.write('Processing scheduled notifications...')
        NotificationManager.process_scheduled_notifications()
        self.stdout.write(self.style.SUCCESS('✓ Scheduled notifications processed'))

        # Retry failed notifications if requested
        if options['retry_failed']:
            self.stdout.write('Retrying failed notifications...')
            NotificationManager.retry_failed_notifications()
            self.stdout.write(self.style.SUCCESS('✓ Failed notifications retried'))

        # Clean up old notifications if requested
        if options['cleanup']:
            days = options['cleanup_days']
            self.stdout.write(f'Cleaning up notifications older than {days} days...')
            NotificationManager.clean_old_notifications(days=days)
            self.stdout.write(self.style.SUCCESS('✓ Old notifications cleaned up'))

        self.stdout.write(
            self.style.SUCCESS(f'Notification processing completed at {timezone.now()}')
        )
