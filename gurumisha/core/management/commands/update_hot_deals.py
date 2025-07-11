"""
Management command to automatically activate/deactivate hot deals based on schedule
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import HotDeal, Car


class Command(BaseCommand):
    help = 'Automatically activate/deactivate hot deals based on schedule'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        now = timezone.now()
        
        # Activate deals that should be active
        deals_to_activate = HotDeal.objects.filter(
            auto_activate=True,
            start_date__lte=now,
            end_date__gte=now,
            is_active=False
        )
        
        activated_count = 0
        for deal in deals_to_activate:
            if not dry_run:
                deal.is_active = True
                deal.save()
                
                # Update car status
                deal.car.is_hot_deal = True
                deal.car.price = deal.discounted_price
                deal.car.save(update_fields=['is_hot_deal', 'price'])
            
            activated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'{"[DRY RUN] " if dry_run else ""}Activated: {deal.title} for {deal.car.title}'
                )
            )

        # Deactivate expired deals
        deals_to_deactivate = HotDeal.objects.filter(
            auto_activate=True,
            end_date__lt=now,
            is_active=True
        )
        
        deactivated_count = 0
        for deal in deals_to_deactivate:
            if not dry_run:
                deal.is_active = False
                deal.save()
                
                # Update car status
                deal.car.is_hot_deal = False
                deal.car.price = deal.original_price
                deal.car.save(update_fields=['is_hot_deal', 'price'])
            
            deactivated_count += 1
            self.stdout.write(
                self.style.WARNING(
                    f'{"[DRY RUN] " if dry_run else ""}Deactivated: {deal.title} for {deal.car.title} (expired)'
                )
            )

        # Deactivate deals that haven't started yet but are marked active
        deals_not_started = HotDeal.objects.filter(
            auto_activate=True,
            start_date__gt=now,
            is_active=True
        )
        
        for deal in deals_not_started:
            if not dry_run:
                deal.is_active = False
                deal.save()
                
                # Update car status
                deal.car.is_hot_deal = False
                deal.car.price = deal.original_price
                deal.car.save(update_fields=['is_hot_deal', 'price'])
            
            deactivated_count += 1
            self.stdout.write(
                self.style.WARNING(
                    f'{"[DRY RUN] " if dry_run else ""}Deactivated: {deal.title} for {deal.car.title} (not started yet)'
                )
            )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"[DRY RUN] " if dry_run else ""}Summary:'
                f'\n- Deals activated: {activated_count}'
                f'\n- Deals deactivated: {deactivated_count}'
            )
        )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('Hot deals update completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Dry run completed. Use without --dry-run to apply changes.')
            )
