"""
Management command to set up production-ready promotional campaigns
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from decimal import Decimal
import random

from core.models import (
    Vendor, VendorSubscription, Car, HotDeal, CarRating,
    FeaturedCarTier, User, PromotionAnalytics
)


class Command(BaseCommand):
    help = 'Set up production-ready promotional campaigns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-subscriptions',
            action='store_true',
            help='Assign vendor subscriptions based on performance',
        )
        parser.add_argument(
            '--feature-cars',
            action='store_true',
            help='Feature initial cars based on ratings and performance',
        )
        parser.add_argument(
            '--create-hot-deals',
            action='store_true',
            help='Create initial hot deals for featured cars',
        )
        parser.add_argument(
            '--setup-analytics',
            action='store_true',
            help='Initialize analytics tracking',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all setup tasks',
        )

    def handle(self, *args, **options):
        if options['all']:
            options.update({
                'assign_subscriptions': True,
                'feature_cars': True,
                'create_hot_deals': True,
                'setup_analytics': True
            })

        if options['assign_subscriptions']:
            self.assign_vendor_subscriptions()
        
        if options['feature_cars']:
            self.feature_initial_cars()
        
        if options['create_hot_deals']:
            self.create_initial_hot_deals()
        
        if options['setup_analytics']:
            self.setup_analytics_tracking()

        # Display summary
        self.display_summary()

    def assign_vendor_subscriptions(self):
        """Assign vendor subscriptions based on performance metrics"""
        self.stdout.write('Assigning vendor subscriptions...')
        
        vendors = Vendor.objects.filter(is_approved=True)
        if not vendors:
            self.stdout.write(self.style.WARNING('No approved vendors found'))
            return
        
        # Calculate vendor performance scores
        vendor_scores = []
        for vendor in vendors:
            cars_count = vendor.cars.filter(is_approved=True).count()
            avg_rating = vendor.cars.filter(
                is_approved=True, 
                calculated_rating__gt=0
            ).aggregate(avg_rating=models.Avg('calculated_rating'))['avg_rating'] or 0
            
            total_views = vendor.cars.filter(is_approved=True).aggregate(
                total_views=models.Sum('views_count')
            )['total_views'] or 0
            
            # Calculate performance score
            score = (cars_count * 10) + (float(avg_rating) * 20) + (total_views * 0.01)
            vendor_scores.append((vendor, score))
        
        # Sort by performance score
        vendor_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign tiers based on performance
        total_vendors = len(vendor_scores)
        tier_assignments = []
        
        for i, (vendor, score) in enumerate(vendor_scores):
            percentile = (i + 1) / total_vendors
            
            if percentile <= 0.1:  # Top 10%
                tier = 'platinum'
                max_featured = 8
                max_deals = 5
            elif percentile <= 0.25:  # Top 25%
                tier = 'gold'
                max_featured = 6
                max_deals = 3
            elif percentile <= 0.5:  # Top 50%
                tier = 'silver'
                max_featured = 4
                max_deals = 2
            elif percentile <= 0.75:  # Top 75%
                tier = 'bronze'
                max_featured = 2
                max_deals = 1
            else:  # Bottom 25%
                tier = 'basic'
                max_featured = 0
                max_deals = 0
            
            tier_assignments.append((vendor, tier, max_featured, max_deals, score))
        
        # Create or update subscriptions
        created_count = 0
        updated_count = 0
        
        for vendor, tier, max_featured, max_deals, score in tier_assignments:
            subscription, created = VendorSubscription.objects.get_or_create(
                vendor=vendor,
                defaults={
                    'tier': tier,
                    'is_active': True,
                    'max_featured_cars': max_featured,
                    'max_hot_deals': max_deals,
                    'auto_renew': True,
                    'end_date': timezone.now() + timedelta(days=30)
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    f'✓ Created {tier} subscription for {vendor.company_name} (score: {score:.1f})'
                )
            else:
                # Update existing subscription if tier changed
                if subscription.tier != tier:
                    subscription.tier = tier
                    subscription.max_featured_cars = max_featured
                    subscription.max_hot_deals = max_deals
                    subscription.save()
                    updated_count += 1
                    self.stdout.write(
                        f'✓ Updated {vendor.company_name} to {tier} tier (score: {score:.1f})'
                    )
                else:
                    self.stdout.write(
                        f'- {vendor.company_name} already has {tier} subscription'
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Vendor subscriptions complete! Created: {created_count}, Updated: {updated_count}'
            )
        )

    def feature_initial_cars(self):
        """Feature cars based on vendor subscriptions and car performance"""
        self.stdout.write('Featuring initial cars...')
        
        # Get vendors with active subscriptions
        subscriptions = VendorSubscription.objects.filter(
            is_active=True
        ).exclude(tier='basic').select_related('vendor')
        
        if not subscriptions:
            self.stdout.write(self.style.WARNING('No active subscriptions found'))
            return
        
        featured_count = 0
        
        for subscription in subscriptions:
            vendor = subscription.vendor
            max_featured = subscription.max_featured_cars
            
            if max_featured == 0:
                continue
            
            # Get best performing cars from this vendor
            cars = vendor.cars.filter(
                is_approved=True,
                featured_tier='none'
            ).order_by('-calculated_rating', '-views_count', '-inquiry_count')[:max_featured]
            
            for car in cars:
                car.featured_tier = subscription.tier
                car.auto_featured = True
                car.featured_until = timezone.now() + timedelta(days=30)
                car.save(update_fields=['featured_tier', 'auto_featured', 'featured_until'])
                
                featured_count += 1
                self.stdout.write(
                    f'✓ Featured {car.title} as {subscription.tier} for {vendor.company_name}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Featured cars complete! Featured {featured_count} cars')
        )

    def create_initial_hot_deals(self):
        """Create initial hot deals for featured cars"""
        self.stdout.write('Creating initial hot deals...')
        
        # Get featured cars that don't have active hot deals
        featured_cars = Car.objects.filter(
            is_approved=True,
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum'],
            is_hot_deal=False
        ).select_related('vendor', 'brand', 'model')
        
        if not featured_cars:
            self.stdout.write(self.style.WARNING('No featured cars available for hot deals'))
            return
        
        # Select cars for hot deals (limit to prevent overwhelming)
        selected_cars = list(featured_cars[:10])
        random.shuffle(selected_cars)
        
        created_count = 0
        
        for car in selected_cars[:5]:  # Create 5 initial hot deals
            # Check vendor's hot deal limit
            vendor_subscription = getattr(car.vendor, 'subscription', None)
            if not vendor_subscription or vendor_subscription.max_hot_deals == 0:
                continue
            
            # Check if vendor has reached hot deal limit
            active_deals = HotDeal.objects.filter(
                car__vendor=car.vendor,
                is_active=True
            ).count()
            
            if active_deals >= vendor_subscription.max_hot_deals:
                continue
            
            # Create hot deal
            discount_percentage = random.randint(10, 30)  # 10-30% discount
            original_price = car.price
            discount_amount = original_price * Decimal(discount_percentage) / 100
            
            hot_deal = HotDeal.objects.create(
                car=car,
                title=f'Limited Time Offer - {car.title}',
                description=f'Special {discount_percentage}% discount on this premium {car.brand.name} {car.model.name}. Don\'t miss this amazing deal!',
                discount_type='percentage',
                discount_value=discount_percentage,
                original_price=original_price,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=random.randint(3, 14)),
                is_active=True,
                auto_activate=False
            )
            
            # Mark car as having hot deal
            car.is_hot_deal = True
            car.save(update_fields=['is_hot_deal'])
            
            created_count += 1
            self.stdout.write(
                f'✓ Created hot deal for {car.title} - {discount_percentage}% off (KSh {discount_amount:,.0f} savings)'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Hot deals complete! Created {created_count} hot deals')
        )

    def setup_analytics_tracking(self):
        """Initialize analytics tracking for existing data"""
        self.stdout.write('Setting up analytics tracking...')
        
        # Create initial analytics entries for featured cars
        featured_cars = Car.objects.filter(
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum']
        ).select_related('vendor')
        
        analytics_count = 0
        
        for car in featured_cars:
            # Create featured car view analytics
            PromotionAnalytics.objects.get_or_create(
                metric_type='featured_car_views',
                car=car,
                vendor=car.vendor,
                date=timezone.now().date(),
                hour=timezone.now().hour,
                defaults={'metric_value': car.views_count or 0}
            )
            analytics_count += 1
        
        # Create analytics for hot deals
        hot_deals = HotDeal.objects.filter(is_active=True).select_related('car', 'car__vendor')
        
        for deal in hot_deals:
            PromotionAnalytics.objects.get_or_create(
                metric_type='hot_deal_views',
                car=deal.car,
                vendor=deal.car.vendor,
                date=timezone.now().date(),
                hour=timezone.now().hour,
                defaults={'metric_value': deal.views_count or 0}
            )
            analytics_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Analytics setup complete! Created {analytics_count} analytics entries')
        )

    def display_summary(self):
        """Display a summary of the current promotional setup"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('PROMOTIONAL CAMPAIGN SUMMARY')
        self.stdout.write('='*60)
        
        # Vendor subscriptions summary
        subscriptions = VendorSubscription.objects.filter(is_active=True)
        self.stdout.write(f'\n📊 Active Vendor Subscriptions: {subscriptions.count()}')
        
        for tier in ['platinum', 'gold', 'silver', 'bronze']:
            count = subscriptions.filter(tier=tier).count()
            if count > 0:
                self.stdout.write(f'  - {tier.title()}: {count} vendors')
        
        # Featured cars summary
        featured_cars = Car.objects.exclude(featured_tier='none')
        self.stdout.write(f'\n⭐ Featured Cars: {featured_cars.count()}')
        
        for tier in ['platinum', 'gold', 'silver', 'bronze']:
            count = featured_cars.filter(featured_tier=tier).count()
            if count > 0:
                self.stdout.write(f'  - {tier.title()}: {count} cars')
        
        # Hot deals summary
        active_deals = HotDeal.objects.filter(is_active=True)
        self.stdout.write(f'\n🔥 Active Hot Deals: {active_deals.count()}')
        
        if active_deals:
            total_savings = sum(
                deal.original_price - deal.discounted_price 
                for deal in active_deals
            )
            self.stdout.write(f'  - Total Customer Savings: KSh {total_savings:,.0f}')
        
        # Analytics summary
        analytics_count = PromotionAnalytics.objects.count()
        self.stdout.write(f'\n📈 Analytics Entries: {analytics_count}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('✅ PROMOTIONAL CAMPAIGNS ARE READY!')
        self.stdout.write('='*60)
