"""
Management command to test the promotion system functionality
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Car, Vendor, VendorSubscription, FeaturedCarTier, HotDeal, 
    CarRating, PromotionAnalytics, User, CarBrand, CarModel
)
from core.analytics_utils import PromotionAnalyticsManager
from core.email_service import PromotionEmailService
import random


class Command(BaseCommand):
    help = 'Test the promotion system functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test data for promotion system',
        )
        parser.add_argument(
            '--test-analytics',
            action='store_true',
            help='Test analytics functionality',
        )
        parser.add_argument(
            '--test-emails',
            action='store_true',
            help='Test email functionality (dry run)',
        )
        parser.add_argument(
            '--test-ratings',
            action='store_true',
            help='Test rating system',
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Run all tests',
        )

    def handle(self, *args, **options):
        if options['test_all']:
            options.update({
                'create_test_data': True,
                'test_analytics': True,
                'test_emails': True,
                'test_ratings': True
            })

        if options['create_test_data']:
            self.create_test_data()
        
        if options['test_analytics']:
            self.test_analytics()
        
        if options['test_emails']:
            self.test_emails()
        
        if options['test_ratings']:
            self.test_ratings()

    def create_test_data(self):
        """Create test data for promotion system"""
        self.stdout.write('Creating test data for promotion system...')
        
        # Create featured car tiers if they don't exist
        tiers_data = [
            {'name': 'bronze', 'display_name': 'Bronze Featured', 'priority_order': 4, 'badge_color': 'bg-amber-600'},
            {'name': 'silver', 'display_name': 'Silver Featured', 'priority_order': 3, 'badge_color': 'bg-gray-400'},
            {'name': 'gold', 'display_name': 'Gold Featured', 'priority_order': 2, 'badge_color': 'bg-yellow-500'},
            {'name': 'platinum', 'display_name': 'Platinum Featured', 'priority_order': 1, 'badge_color': 'bg-purple-600'},
        ]
        
        for tier_data in tiers_data:
            tier, created = FeaturedCarTier.objects.get_or_create(
                name=tier_data['name'],
                defaults=tier_data
            )
            if created:
                self.stdout.write(f'✓ Created tier: {tier.display_name}')
        
        # Create test vendor subscriptions
        vendors = Vendor.objects.filter(is_approved=True)[:5]
        subscription_tiers = ['bronze', 'silver', 'gold', 'platinum']
        
        for i, vendor in enumerate(vendors):
            tier = subscription_tiers[i % len(subscription_tiers)]
            subscription, created = VendorSubscription.objects.get_or_create(
                vendor=vendor,
                defaults={
                    'tier': tier,
                    'is_active': True,
                    'max_featured_cars': (i + 1) * 2,
                    'max_hot_deals': i + 1
                }
            )
            if created:
                self.stdout.write(f'✓ Created {tier} subscription for {vendor.company_name}')
        
        # Update some cars with calculated ratings
        cars = Car.objects.filter(is_approved=True)[:20]
        for car in cars:
            car.calculated_rating = round(random.uniform(3.0, 5.0) * 2) / 2  # Round to nearest 0.5
            car.views_count = random.randint(50, 1000)
            car.inquiry_count = random.randint(5, 50)
            car.save(update_fields=['calculated_rating', 'views_count', 'inquiry_count'])
        
        self.stdout.write(f'✓ Updated ratings for {len(cars)} cars')
        
        # Create some hot deals
        available_cars = Car.objects.filter(
            is_approved=True,
            vendor__subscription__is_active=True
        ).exclude(is_hot_deal=True)[:3]
        
        for car in available_cars:
            original_price = car.price
            discount_value = random.randint(10, 30)  # 10-30% discount
            
            hot_deal, created = HotDeal.objects.get_or_create(
                car=car,
                defaults={
                    'title': f'Limited Time Offer - {car.title}',
                    'description': f'Special discount on this amazing {car.brand.name} {car.model.name}',
                    'discount_type': 'percentage',
                    'discount_value': discount_value,
                    'original_price': original_price,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=7),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'✓ Created hot deal for {car.title}')
        
        self.stdout.write(self.style.SUCCESS('Test data creation completed!'))

    def test_analytics(self):
        """Test analytics functionality"""
        self.stdout.write('Testing analytics functionality...')
        
        try:
            analytics = PromotionAnalyticsManager()
            
            # Test featured cars performance
            featured_performance = analytics.get_featured_cars_performance(30)
            self.stdout.write(f'✓ Featured cars performance: {len(featured_performance)} tiers analyzed')
            
            # Test hot deals performance
            hot_deals_performance = analytics.get_hot_deals_performance(30)
            self.stdout.write(f'✓ Hot deals performance: {len(hot_deals_performance)} deals analyzed')
            
            # Test rating distribution
            rating_distribution = analytics.get_rating_distribution(30)
            self.stdout.write(f'✓ Rating distribution: {len(rating_distribution)} rating levels')
            
            # Test daily metrics
            daily_metrics = analytics.get_daily_metrics(7)
            self.stdout.write(f'✓ Daily metrics: {len(daily_metrics)} days of data')
            
            # Test vendor stats
            vendor = Vendor.objects.filter(is_approved=True).first()
            if vendor:
                vendor_stats = analytics.get_vendor_promotion_stats(vendor, 30)
                self.stdout.write(f'✓ Vendor stats for {vendor.company_name}: {vendor_stats}')
            
            self.stdout.write(self.style.SUCCESS('Analytics tests passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Analytics test failed: {str(e)}'))

    def test_emails(self):
        """Test email functionality (dry run)"""
        self.stdout.write('Testing email functionality (dry run)...')
        
        try:
            email_service = PromotionEmailService()
            
            # Test hot deal notification
            hot_deal = HotDeal.objects.filter(is_active=True).first()
            if hot_deal:
                # Don't actually send, just test template rendering
                from django.template.loader import render_to_string
                
                context = {
                    'deal': hot_deal,
                    'site_url': 'http://localhost:8000'
                }
                
                html_content = render_to_string('emails/hot_deal_notification.html', context)
                text_content = render_to_string('emails/hot_deal_notification.txt', context)
                
                self.stdout.write(f'✓ Hot deal email templates rendered successfully')
                self.stdout.write(f'  - HTML content length: {len(html_content)} chars')
                self.stdout.write(f'  - Text content length: {len(text_content)} chars')
            
            # Test weekly digest
            self.stdout.write('✓ Email service initialized successfully')
            
            self.stdout.write(self.style.SUCCESS('Email tests passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Email test failed: {str(e)}'))

    def test_ratings(self):
        """Test rating system"""
        self.stdout.write('Testing rating system...')
        
        try:
            # Test automatic rating calculation
            car = Car.objects.filter(is_approved=True).first()
            if car:
                old_rating = car.calculated_rating
                new_rating = car.calculate_automatic_rating()
                
                self.stdout.write(f'✓ Rating calculation: {old_rating} → {new_rating}')
                
                # Test star display
                star_display = car.get_star_display()
                self.stdout.write(f'✓ Star display: {star_display}')
                
                # Test promotion badges
                badges = car.get_promotion_badges()
                self.stdout.write(f'✓ Promotion badges: {len(badges)} badges')
                
                # Test vendor rating update
                if hasattr(car.vendor, 'update_average_rating'):
                    car.vendor.update_average_rating()
                    self.stdout.write(f'✓ Vendor average rating updated: {car.vendor.average_rating}')
            
            # Test rating validation
            test_ratings = [0.5, 1.0, 2.5, 4.0, 5.0]
            for rating in test_ratings:
                rounded = round(rating * 2) / 2
                self.stdout.write(f'✓ Rating {rating} rounds to {rounded}')
            
            self.stdout.write(self.style.SUCCESS('Rating tests passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Rating test failed: {str(e)}'))

    def run_integration_tests(self):
        """Run integration tests"""
        self.stdout.write('Running integration tests...')
        
        try:
            # Test featured car workflow
            car = Car.objects.filter(is_approved=True, featured_tier='none').first()
            if car:
                # Feature the car
                car.featured_tier = 'gold'
                car.auto_featured = False
                car.save()
                
                # Check if it appears in featured queries
                featured_cars = Car.objects.exclude(featured_tier='none')
                assert car in featured_cars
                self.stdout.write('✓ Featured car workflow test passed')
                
                # Reset
                car.featured_tier = 'none'
                car.save()
            
            # Test hot deal workflow
            available_car = Car.objects.filter(
                is_approved=True,
                is_hot_deal=False
            ).first()
            
            if available_car:
                # Create hot deal
                hot_deal = HotDeal.objects.create(
                    car=available_car,
                    title='Test Hot Deal',
                    discount_type='percentage',
                    discount_value=20,
                    original_price=available_car.price,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=1),
                    is_active=True
                )
                
                # Check if car is marked as hot deal
                available_car.refresh_from_db()
                assert available_car.is_hot_deal == True
                self.stdout.write('✓ Hot deal workflow test passed')
                
                # Cleanup
                hot_deal.delete()
                available_car.is_hot_deal = False
                available_car.save()
            
            self.stdout.write(self.style.SUCCESS('Integration tests passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Integration test failed: {str(e)}'))

    def validate_database_integrity(self):
        """Validate database integrity"""
        self.stdout.write('Validating database integrity...')
        
        issues = []
        
        # Check for orphaned hot deals
        orphaned_deals = HotDeal.objects.filter(car__isnull=True)
        if orphaned_deals.exists():
            issues.append(f'Found {orphaned_deals.count()} orphaned hot deals')
        
        # Check for cars with hot deal status but no active deal
        orphaned_hot_cars = Car.objects.filter(
            is_hot_deal=True
        ).exclude(
            id__in=HotDeal.objects.filter(is_active=True).values_list('car_id', flat=True)
        )
        if orphaned_hot_cars.exists():
            issues.append(f'Found {orphaned_hot_cars.count()} cars with hot deal status but no active deal')
        
        # Check for invalid ratings
        invalid_ratings = Car.objects.filter(calculated_rating__lt=0) | Car.objects.filter(calculated_rating__gt=5)
        if invalid_ratings.exists():
            issues.append(f'Found {invalid_ratings.count()} cars with invalid ratings')
        
        # Check for expired featured cars
        expired_featured = Car.objects.filter(
            featured_until__lt=timezone.now(),
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum']
        )
        if expired_featured.exists():
            issues.append(f'Found {expired_featured.count()} expired featured cars')
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.WARNING(f'⚠ {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Database integrity check passed'))
        
        return len(issues) == 0
