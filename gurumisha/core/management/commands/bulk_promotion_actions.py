"""
Management command for bulk promotion actions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Car, Vendor, HotDeal, CarRating, FeaturedCarTier


class Command(BaseCommand):
    help = 'Perform bulk promotion actions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            required=True,
            choices=['update_ratings', 'expire_deals', 'auto_feature', 'cleanup_expired'],
            help='Action to perform'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Specific vendor ID for vendor-specific actions'
        )

    def handle(self, *args, **options):
        action = options['action']
        dry_run = options['dry_run']
        vendor_id = options.get('vendor_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        if action == 'update_ratings':
            self.update_all_ratings(dry_run)
        elif action == 'expire_deals':
            self.expire_old_deals(dry_run)
        elif action == 'auto_feature':
            self.auto_feature_cars(dry_run, vendor_id)
        elif action == 'cleanup_expired':
            self.cleanup_expired_promotions(dry_run)

    def update_all_ratings(self, dry_run=False):
        """Update calculated ratings for all cars"""
        self.stdout.write('Updating calculated ratings for all cars...')
        
        cars = Car.objects.filter(is_approved=True)
        updated_count = 0
        
        for car in cars:
            old_rating = car.calculated_rating
            new_rating = car.calculate_automatic_rating()
            
            if abs(old_rating - new_rating) > 0.1:  # Only update if significant change
                if not dry_run:
                    car.calculated_rating = new_rating
                    car.last_rating_update = timezone.now()
                    car.save(update_fields=['calculated_rating', 'last_rating_update'])
                
                updated_count += 1
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Updated {car.title}: {old_rating} → {new_rating}'
                )
        
        # Update vendor average ratings
        vendors = Vendor.objects.filter(is_approved=True)
        for vendor in vendors:
            if not dry_run:
                vendor.update_average_rating()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Updated ratings for {updated_count} cars'
            )
        )

    def expire_old_deals(self, dry_run=False):
        """Expire old hot deals"""
        self.stdout.write('Expiring old hot deals...')
        
        now = timezone.now()
        expired_deals = HotDeal.objects.filter(
            end_date__lt=now,
            is_active=True
        )
        
        expired_count = 0
        for deal in expired_deals:
            if not dry_run:
                deal.is_active = False
                deal.save()
                
                # Update car status
                deal.car.is_hot_deal = False
                deal.car.price = deal.original_price
                deal.car.save(update_fields=['is_hot_deal', 'price'])
            
            expired_count += 1
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}Expired deal: {deal.title} for {deal.car.title}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Expired {expired_count} deals'
            )
        )

    def auto_feature_cars(self, dry_run=False, vendor_id=None):
        """Automatically feature cars based on performance"""
        self.stdout.write('Auto-featuring high-performing cars...')
        
        # Get cars that should be auto-featured based on performance
        cars_query = Car.objects.filter(
            is_approved=True,
            status__in=['available', 'featured'],
            calculated_rating__gte=4.0,
            views_count__gte=100
        ).exclude(featured_tier__in=['gold', 'platinum'])  # Don't override premium tiers
        
        if vendor_id:
            cars_query = cars_query.filter(vendor_id=vendor_id)
        
        # Order by performance metrics
        high_performing_cars = cars_query.order_by(
            '-calculated_rating', 
            '-views_count', 
            '-inquiry_count'
        )[:20]  # Limit to top 20
        
        featured_count = 0
        for car in high_performing_cars:
            # Determine tier based on performance
            if car.calculated_rating >= 4.5 and car.views_count >= 500:
                new_tier = 'silver'
            elif car.calculated_rating >= 4.0 and car.views_count >= 200:
                new_tier = 'bronze'
            else:
                continue
            
            if car.featured_tier != new_tier:
                if not dry_run:
                    car.featured_tier = new_tier
                    car.auto_featured = True
                    car.save(update_fields=['featured_tier', 'auto_featured'])
                
                featured_count += 1
                self.stdout.write(
                    f'{"[DRY RUN] " if dry_run else ""}Auto-featured {car.title} as {new_tier}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Auto-featured {featured_count} cars'
            )
        )

    def cleanup_expired_promotions(self, dry_run=False):
        """Clean up expired promotions and reset car statuses"""
        self.stdout.write('Cleaning up expired promotions...')
        
        now = timezone.now()
        cleanup_count = 0
        
        # Clean up expired featured cars
        expired_featured = Car.objects.filter(
            featured_until__lt=now,
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum']
        )
        
        for car in expired_featured:
            if not dry_run:
                car.featured_tier = 'none'
                car.featured_until = None
                car.auto_featured = False
                car.save(update_fields=['featured_tier', 'featured_until', 'auto_featured'])
            
            cleanup_count += 1
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}Removed expired featuring from {car.title}'
            )
        
        # Clean up cars with hot deal status but no active deal
        orphaned_hot_deals = Car.objects.filter(
            is_hot_deal=True
        ).exclude(
            id__in=HotDeal.objects.filter(is_active=True).values_list('car_id', flat=True)
        )
        
        for car in orphaned_hot_deals:
            if not dry_run:
                car.is_hot_deal = False
                car.save(update_fields=['is_hot_deal'])
            
            cleanup_count += 1
            self.stdout.write(
                f'{"[DRY RUN] " if dry_run else ""}Removed orphaned hot deal status from {car.title}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Cleaned up {cleanup_count} expired promotions'
            )
        )

    def get_performance_score(self, car):
        """Calculate performance score for a car"""
        score = 0
        
        # Rating component (0-50 points)
        score += (car.calculated_rating / 5.0) * 50
        
        # Views component (0-30 points)
        views_score = min(car.views_count / 1000, 1.0) * 30
        score += views_score
        
        # Inquiry component (0-20 points)
        inquiry_score = min(car.inquiry_count / 100, 1.0) * 20
        score += inquiry_score
        
        return score
