"""
Management command to automatically feature cars based on vendor subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Car, Vendor, VendorSubscription, FeaturedCarTier


class Command(BaseCommand):
    help = 'Automatically feature cars based on vendor subscription levels'

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

        # Get all active vendors with subscriptions
        vendors_with_subscriptions = Vendor.objects.filter(
            subscription__is_active=True,
            subscription__tier__in=['bronze', 'silver', 'gold', 'platinum']
        ).select_related('subscription')

        total_featured = 0
        total_unfeatured = 0

        for vendor in vendors_with_subscriptions:
            subscription = vendor.subscription
            
            # Skip if subscription is expired
            if subscription.is_expired():
                continue

            # Get vendor's approved cars
            vendor_cars = Car.objects.filter(
                vendor=vendor,
                is_approved=True,
                status__in=['available', 'featured']
            ).order_by('-calculated_rating', '-views_count', '-created_at')

            # Determine how many cars can be featured
            max_featured = subscription.max_featured_cars
            
            # Get tier configuration
            try:
                tier_config = FeaturedCarTier.objects.get(name=subscription.tier)
            except FeaturedCarTier.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tier configuration not found for {subscription.tier}')
                )
                continue

            # Feature top cars up to the limit
            cars_to_feature = vendor_cars[:max_featured]
            cars_to_unfeature = vendor_cars[max_featured:]

            # Feature cars
            for car in cars_to_feature:
                if car.featured_tier != subscription.tier or not car.auto_featured:
                    if not dry_run:
                        car.featured_tier = subscription.tier
                        car.auto_featured = True
                        car.featured_until = None  # No expiry for auto-featured
                        car.save(update_fields=['featured_tier', 'auto_featured', 'featured_until'])
                    
                    total_featured += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{"[DRY RUN] " if dry_run else ""}Featured: {car.title} as {subscription.tier.title()}'
                        )
                    )

            # Unfeature excess cars (only auto-featured ones)
            for car in cars_to_unfeature:
                if car.auto_featured and car.featured_tier != 'none':
                    if not dry_run:
                        car.featured_tier = 'none'
                        car.auto_featured = False
                        car.featured_until = None
                        car.save(update_fields=['featured_tier', 'auto_featured', 'featured_until'])
                    
                    total_unfeatured += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'{"[DRY RUN] " if dry_run else ""}Unfeatured: {car.title} (exceeded limit)'
                        )
                    )

        # Handle vendors without active subscriptions
        vendors_without_subscriptions = Vendor.objects.exclude(
            subscription__is_active=True,
            subscription__tier__in=['bronze', 'silver', 'gold', 'platinum']
        )

        for vendor in vendors_without_subscriptions:
            # Unfeature all auto-featured cars for vendors without subscriptions
            auto_featured_cars = Car.objects.filter(
                vendor=vendor,
                auto_featured=True,
                featured_tier__in=['bronze', 'silver', 'gold', 'platinum']
            )

            for car in auto_featured_cars:
                if not dry_run:
                    car.featured_tier = 'none'
                    car.auto_featured = False
                    car.featured_until = None
                    car.save(update_fields=['featured_tier', 'auto_featured', 'featured_until'])
                
                total_unfeatured += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{"[DRY RUN] " if dry_run else ""}Unfeatured: {car.title} (no active subscription)'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"[DRY RUN] " if dry_run else ""}Summary:'
                f'\n- Cars featured: {total_featured}'
                f'\n- Cars unfeatured: {total_unfeatured}'
            )
        )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('Auto-featuring update completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Dry run completed. Use without --dry-run to apply changes.')
            )
