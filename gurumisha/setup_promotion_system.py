#!/usr/bin/env python3
"""
Setup script for the enhanced car listing promotion system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from django.core.management import call_command
from django.db import transaction
from core.models import (
    FeaturedCarTier, VendorSubscription, Car, Vendor, User, CarBrand, CarModel
)
import random
from decimal import Decimal


def setup_featured_tiers():
    """Setup default featured car tiers"""
    print("Setting up featured car tiers...")
    
    tiers_data = [
        {
            'name': 'bronze',
            'display_name': 'Bronze Featured',
            'priority_order': 4,
            'badge_color': 'bg-amber-600',
            'badge_icon': 'fas fa-medal',
            'homepage_slots': 2,
            'listing_boost_percentage': 10,
            'monthly_price': Decimal('2500.00'),
        },
        {
            'name': 'silver',
            'display_name': 'Silver Featured',
            'priority_order': 3,
            'badge_color': 'bg-gray-400',
            'badge_icon': 'fas fa-medal',
            'homepage_slots': 4,
            'listing_boost_percentage': 25,
            'monthly_price': Decimal('5000.00'),
        },
        {
            'name': 'gold',
            'display_name': 'Gold Featured',
            'priority_order': 2,
            'badge_color': 'bg-yellow-500',
            'badge_icon': 'fas fa-crown',
            'homepage_slots': 6,
            'listing_boost_percentage': 50,
            'monthly_price': Decimal('10000.00'),
        },
        {
            'name': 'platinum',
            'display_name': 'Platinum Featured',
            'priority_order': 1,
            'badge_color': 'bg-purple-600',
            'badge_icon': 'fas fa-gem',
            'homepage_slots': 8,
            'listing_boost_percentage': 100,
            'monthly_price': Decimal('20000.00'),
        },
    ]
    
    created_count = 0
    for tier_data in tiers_data:
        tier, created = FeaturedCarTier.objects.get_or_create(
            name=tier_data['name'],
            defaults=tier_data
        )
        if created:
            created_count += 1
            print(f"✓ Created tier: {tier.display_name}")
        else:
            print(f"- Tier already exists: {tier.display_name}")
    
    print(f"Featured tiers setup complete! Created {created_count} new tiers.")


def setup_sample_subscriptions():
    """Setup sample vendor subscriptions"""
    print("Setting up sample vendor subscriptions...")
    
    vendors = Vendor.objects.filter(is_approved=True)[:5]
    if not vendors:
        print("No approved vendors found. Skipping subscription setup.")
        return
    
    subscription_tiers = ['bronze', 'silver', 'gold', 'platinum', 'basic']
    created_count = 0
    
    for i, vendor in enumerate(vendors):
        tier = subscription_tiers[i % len(subscription_tiers)]
        
        # Skip basic tier for subscription creation
        if tier == 'basic':
            continue
            
        subscription, created = VendorSubscription.objects.get_or_create(
            vendor=vendor,
            defaults={
                'tier': tier,
                'is_active': True,
                'max_featured_cars': (i + 1) * 2,
                'max_hot_deals': i + 1,
                'auto_renew': True
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Created {tier} subscription for {vendor.company_name}")
        else:
            print(f"- Subscription already exists for {vendor.company_name}")
    
    print(f"Sample subscriptions setup complete! Created {created_count} new subscriptions.")


def setup_sample_ratings():
    """Setup sample car ratings"""
    print("Setting up sample car ratings...")
    
    cars = Car.objects.filter(is_approved=True)[:20]
    if not cars:
        print("No approved cars found. Skipping ratings setup.")
        return
    
    updated_count = 0
    for car in cars:
        # Generate realistic ratings
        base_rating = random.uniform(3.0, 5.0)
        car.calculated_rating = round(base_rating * 2) / 2  # Round to nearest 0.5
        car.views_count = random.randint(50, 1000)
        car.inquiry_count = random.randint(5, 50)
        car.save(update_fields=['calculated_rating', 'views_count', 'inquiry_count'])
        updated_count += 1
    
    print(f"Sample ratings setup complete! Updated {updated_count} cars.")


def setup_sample_featured_cars():
    """Setup sample featured cars"""
    print("Setting up sample featured cars...")
    
    # Get cars from vendors with subscriptions
    subscribed_vendors = VendorSubscription.objects.filter(is_active=True).values_list('vendor_id', flat=True)
    cars = Car.objects.filter(
        is_approved=True,
        vendor_id__in=subscribed_vendors
    )[:10]
    
    if not cars:
        print("No cars from subscribed vendors found. Skipping featured cars setup.")
        return
    
    tiers = ['bronze', 'silver', 'gold', 'platinum']
    featured_count = 0
    
    for i, car in enumerate(cars):
        tier = tiers[i % len(tiers)]
        car.featured_tier = tier
        car.auto_featured = True
        car.save(update_fields=['featured_tier', 'auto_featured'])
        featured_count += 1
        print(f"✓ Featured {car.title} as {tier}")
    
    print(f"Sample featured cars setup complete! Featured {featured_count} cars.")


def run_system_checks():
    """Run system checks to ensure everything is working"""
    print("Running system checks...")
    
    # Check database integrity
    print("- Checking database integrity...")
    try:
        call_command('check')
        print("✓ Django system check passed")
    except Exception as e:
        print(f"✗ Django system check failed: {e}")
        return False
    
    # Check promotion system
    print("- Testing promotion system...")
    try:
        from core.analytics_utils import PromotionAnalyticsManager
        analytics = PromotionAnalyticsManager()
        
        # Test analytics
        featured_performance = analytics.get_featured_cars_performance(7)
        print(f"✓ Analytics working - {len(featured_performance)} tiers analyzed")
        
        # Test email templates
        from django.template.loader import render_to_string
        from core.models import HotDeal
        
        hot_deal = HotDeal.objects.first()
        if hot_deal:
            context = {'deal': hot_deal, 'site_url': 'http://localhost:8000'}
            html_content = render_to_string('emails/hot_deal_notification.html', context)
            print("✓ Email templates working")
        
        print("✓ Promotion system tests passed")
        
    except Exception as e:
        print(f"✗ Promotion system test failed: {e}")
        return False
    
    return True


def main():
    """Main setup function"""
    print("=" * 60)
    print("GURUMISHA MOTORS - ENHANCED PROMOTION SYSTEM SETUP")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Setup featured tiers
            setup_featured_tiers()
            print()
            
            # Setup sample subscriptions
            setup_sample_subscriptions()
            print()
            
            # Setup sample ratings
            setup_sample_ratings()
            print()
            
            # Setup sample featured cars
            setup_sample_featured_cars()
            print()
            
            # Run system checks
            if run_system_checks():
                print()
                print("=" * 60)
                print("✅ PROMOTION SYSTEM SETUP COMPLETED SUCCESSFULLY!")
                print("=" * 60)
                print()
                print("Next steps:")
                print("1. Run: python manage.py runserver")
                print("2. Visit the admin panel to manage promotions")
                print("3. Test the promotion features on the frontend")
                print("4. Set up email configuration for notifications")
                print()
                print("Management commands available:")
                print("- python manage.py setup_featured_tiers")
                print("- python manage.py update_auto_featured_cars")
                print("- python manage.py update_hot_deals")
                print("- python manage.py bulk_promotion_actions --action=update_ratings")
                print("- python manage.py send_promotional_emails --type=hot_deals --dry-run")
                print("- python manage.py test_promotion_system --test-all")
                
            else:
                print()
                print("=" * 60)
                print("❌ SETUP COMPLETED WITH ERRORS")
                print("=" * 60)
                print("Please check the error messages above and fix any issues.")
                
    except Exception as e:
        print(f)
        print("=" * 60)
        print("❌ SETUP FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print("Please check the error and try again.")


if __name__ == '__main__':
    main()
