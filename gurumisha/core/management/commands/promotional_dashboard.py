"""
Management command to display comprehensive promotional dashboard
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.db import models
from datetime import timedelta

from core.models import (
    User, Vendor, VendorSubscription, Car, HotDeal, CarRating,
    PromotionAnalytics, NotificationPreference
)


class Command(BaseCommand):
    help = 'Display comprehensive promotional dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown by vendor and tier',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.display_header()
        self.display_subscription_overview()
        self.display_featured_cars_overview()
        self.display_hot_deals_overview()
        self.display_email_marketing_overview()
        self.display_analytics_overview()
        
        if detailed:
            self.display_detailed_breakdown()
        
        self.display_recommendations()

    def display_header(self):
        """Display dashboard header"""
        self.stdout.write('\n' + '='*80)
        self.stdout.write('🎯 GURUMISHA MOTORS - PROMOTIONAL DASHBOARD')
        self.stdout.write('='*80)
        self.stdout.write(f'📅 Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('='*80)

    def display_subscription_overview(self):
        """Display vendor subscription overview"""
        self.stdout.write('\n📊 VENDOR SUBSCRIPTION OVERVIEW')
        self.stdout.write('-' * 50)
        
        total_vendors = Vendor.objects.filter(is_approved=True).count()
        active_subscriptions = VendorSubscription.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Total Approved Vendors: {total_vendors}')
        self.stdout.write(f'Active Subscriptions: {active_subscriptions}')
        self.stdout.write(f'Subscription Rate: {(active_subscriptions/total_vendors*100):.1f}%' if total_vendors > 0 else 'Subscription Rate: 0%')
        
        # Subscription breakdown by tier
        tier_breakdown = VendorSubscription.objects.filter(
            is_active=True
        ).values('tier').annotate(count=Count('id')).order_by('-count')
        
        self.stdout.write('\nSubscription Tiers:')
        for tier_data in tier_breakdown:
            tier = tier_data['tier']
            count = tier_data['count']
            self.stdout.write(f'  {tier.title()}: {count} vendors')
        
        # Revenue potential (if pricing was implemented)
        total_revenue_potential = 0
        tier_prices = {'platinum': 20000, 'gold': 10000, 'silver': 5000, 'bronze': 2500}
        
        for tier_data in tier_breakdown:
            tier = tier_data['tier']
            count = tier_data['count']
            if tier in tier_prices:
                total_revenue_potential += tier_prices[tier] * count
        
        self.stdout.write(f'\nMonthly Revenue Potential: KSh {total_revenue_potential:,}')

    def display_featured_cars_overview(self):
        """Display featured cars overview"""
        self.stdout.write('\n⭐ FEATURED CARS OVERVIEW')
        self.stdout.write('-' * 50)
        
        total_cars = Car.objects.filter(is_approved=True).count()
        featured_cars = Car.objects.exclude(featured_tier='none').count()
        
        self.stdout.write(f'Total Approved Cars: {total_cars}')
        self.stdout.write(f'Featured Cars: {featured_cars}')
        self.stdout.write(f'Featured Rate: {(featured_cars/total_cars*100):.1f}%' if total_cars > 0 else 'Featured Rate: 0%')
        
        # Featured cars by tier
        tier_breakdown = Car.objects.exclude(
            featured_tier='none'
        ).values('featured_tier').annotate(count=Count('id')).order_by('-count')

        self.stdout.write('\nFeatured Cars by Tier:')
        for tier_data in tier_breakdown:
            tier = tier_data['featured_tier']
            count = tier_data['count']
            self.stdout.write(f'  {tier.title()}: {count} cars')
        
        # Performance metrics
        avg_rating = Car.objects.exclude(
            featured_tier='none'
        ).aggregate(avg_rating=Avg('calculated_rating'))['avg_rating'] or 0
        
        total_views = Car.objects.exclude(
            featured_tier='none'
        ).aggregate(total_views=Sum('views_count'))['total_views'] or 0
        
        self.stdout.write(f'\nFeatured Cars Performance:')
        self.stdout.write(f'  Average Rating: {avg_rating:.2f}/5.0')
        self.stdout.write(f'  Total Views: {total_views:,}')

    def display_hot_deals_overview(self):
        """Display hot deals overview"""
        self.stdout.write('\n🔥 HOT DEALS OVERVIEW')
        self.stdout.write('-' * 50)
        
        active_deals = HotDeal.objects.filter(is_active=True)
        expired_deals = HotDeal.objects.filter(
            is_active=False,
            end_date__lt=timezone.now()
        )
        
        self.stdout.write(f'Active Hot Deals: {active_deals.count()}')
        self.stdout.write(f'Expired Deals: {expired_deals.count()}')
        
        if active_deals.exists():
            # Calculate total savings
            total_savings = sum(
                deal.original_price - deal.discounted_price 
                for deal in active_deals
            )
            
            # Average discount
            avg_discount = active_deals.aggregate(
                avg_discount=Avg('discount_value')
            )['avg_discount'] or 0
            
            # Performance metrics
            total_views = active_deals.aggregate(
                total_views=Sum('views_count')
            )['total_views'] or 0
            
            total_clicks = active_deals.aggregate(
                total_clicks=Sum('clicks_count')
            )['total_clicks'] or 0
            
            self.stdout.write(f'\nActive Deals Performance:')
            self.stdout.write(f'  Total Customer Savings: KSh {total_savings:,.0f}')
            self.stdout.write(f'  Average Discount: {avg_discount:.1f}%')
            self.stdout.write(f'  Total Views: {total_views:,}')
            self.stdout.write(f'  Total Clicks: {total_clicks:,}')
            
            # Deals expiring soon
            tomorrow = timezone.now() + timedelta(days=1)
            expiring_soon = active_deals.filter(end_date__lte=tomorrow).count()
            if expiring_soon > 0:
                self.stdout.write(f'  ⚠️  Expiring in 24h: {expiring_soon} deals')

    def display_email_marketing_overview(self):
        """Display email marketing overview"""
        self.stdout.write('\n📧 EMAIL MARKETING OVERVIEW')
        self.stdout.write('-' * 50)
        
        # Email subscribers
        total_users = User.objects.count()
        email_enabled = User.objects.filter(
            notification_preferences__email_enabled=True
        ).count()
        marketing_enabled = User.objects.filter(
            notification_preferences__email_marketing=True
        ).count()
        
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'Email Enabled: {email_enabled} ({(email_enabled/total_users*100):.1f}%)' if total_users > 0 else 'Email Enabled: 0')
        self.stdout.write(f'Marketing Enabled: {marketing_enabled} ({(marketing_enabled/total_users*100):.1f}%)' if total_users > 0 else 'Marketing Enabled: 0')
        
        # Subscriber breakdown by role
        customer_subscribers = User.objects.filter(
            notification_preferences__email_marketing=True,
            role='customer'
        ).count()
        
        vendor_subscribers = User.objects.filter(
            notification_preferences__email_marketing=True,
            role='vendor'
        ).count()
        
        self.stdout.write(f'\nMarketing Subscribers by Role:')
        self.stdout.write(f'  Customers: {customer_subscribers}')
        self.stdout.write(f'  Vendors: {vendor_subscribers}')
        
        # Email campaign readiness
        pending_hot_deals = HotDeal.objects.filter(
            is_active=True,
            email_sent=False
        ).count()
        
        self.stdout.write(f'\nCampaign Readiness:')
        self.stdout.write(f'  Hot Deals Ready for Email: {pending_hot_deals}')
        
        # Recent activity for welcome series
        week_ago = timezone.now() - timedelta(days=7)
        new_users = User.objects.filter(date_joined__gte=week_ago).count()
        self.stdout.write(f'  New Users (Last 7 Days): {new_users}')

    def display_analytics_overview(self):
        """Display analytics overview"""
        self.stdout.write('\n📈 ANALYTICS OVERVIEW')
        self.stdout.write('-' * 50)
        
        total_analytics = PromotionAnalytics.objects.count()
        self.stdout.write(f'Total Analytics Entries: {total_analytics}')
        
        # Analytics by metric type
        metric_breakdown = PromotionAnalytics.objects.values(
            'metric_type'
        ).annotate(count=Count('id')).order_by('-count')
        
        self.stdout.write('\nMetrics Tracked:')
        for metric_data in metric_breakdown:
            metric_type = metric_data['metric_type']
            count = metric_data['count']
            self.stdout.write(f'  {metric_type.replace("_", " ").title()}: {count} entries')
        
        # Recent activity (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_analytics = PromotionAnalytics.objects.filter(
            created_at__gte=yesterday
        ).count()
        
        self.stdout.write(f'\nRecent Activity (24h): {recent_analytics} new entries')

    def display_detailed_breakdown(self):
        """Display detailed breakdown by vendor and tier"""
        self.stdout.write('\n🔍 DETAILED BREAKDOWN')
        self.stdout.write('-' * 50)
        
        # Top performing vendors
        self.stdout.write('\nTop Performing Vendors:')
        top_vendors = Vendor.objects.filter(
            is_approved=True
        ).annotate(
            total_cars=Count('cars', filter=Q(cars__is_approved=True)),
            featured_cars=Count('cars', filter=Q(cars__featured_tier__in=['bronze', 'silver', 'gold', 'platinum'])),
            avg_rating=Avg('cars__calculated_rating', filter=Q(cars__is_approved=True))
        ).order_by('-featured_cars', '-avg_rating')[:5]
        
        for vendor in top_vendors:
            subscription = getattr(vendor, 'subscription', None)
            tier = subscription.tier if subscription else 'none'
            self.stdout.write(
                f'  {vendor.company_name}: {vendor.featured_cars} featured cars, '
                f'{vendor.avg_rating:.1f} avg rating ({tier} tier)'
            )
        
        # Featured cars performance by tier
        self.stdout.write('\nFeatured Cars Performance by Tier:')
        for tier in ['platinum', 'gold', 'silver', 'bronze']:
            cars = Car.objects.filter(featured_tier=tier)
            if cars.exists():
                avg_rating = cars.aggregate(avg_rating=Avg('calculated_rating'))['avg_rating'] or 0
                total_views = cars.aggregate(total_views=Sum('views_count'))['total_views'] or 0
                self.stdout.write(
                    f'  {tier.title()}: {cars.count()} cars, '
                    f'{avg_rating:.1f} avg rating, {total_views:,} total views'
                )

    def display_recommendations(self):
        """Display actionable recommendations"""
        self.stdout.write('\n💡 RECOMMENDATIONS')
        self.stdout.write('-' * 50)
        
        recommendations = []
        
        # Check for pending hot deals
        pending_deals = HotDeal.objects.filter(is_active=True, email_sent=False).count()
        if pending_deals > 0:
            recommendations.append(
                f'📧 Send hot deal emails for {pending_deals} pending deals'
            )
        
        # Check for low subscription rate
        total_vendors = Vendor.objects.filter(is_approved=True).count()
        subscribed_vendors = VendorSubscription.objects.filter(is_active=True).count()
        if total_vendors > 0 and (subscribed_vendors / total_vendors) < 0.5:
            recommendations.append(
                '📈 Vendor subscription rate is low - consider promotional campaigns'
            )
        
        # Check for low email marketing opt-in
        total_users = User.objects.count()
        marketing_users = User.objects.filter(
            notification_preferences__email_marketing=True
        ).count()
        if total_users > 0 and (marketing_users / total_users) < 0.3:
            recommendations.append(
                '📧 Email marketing opt-in rate is low - improve onboarding'
            )
        
        # Check for expiring deals
        tomorrow = timezone.now() + timedelta(days=1)
        expiring_deals = HotDeal.objects.filter(
            is_active=True,
            end_date__lte=tomorrow
        ).count()
        if expiring_deals > 0:
            recommendations.append(
                f'⏰ {expiring_deals} deals expiring soon - send urgency emails'
            )
        
        # Check for unrated featured cars
        unrated_featured = Car.objects.filter(
            featured_tier__in=['bronze', 'silver', 'gold', 'platinum'],
            calculated_rating=0
        ).count()
        if unrated_featured > 0:
            recommendations.append(
                f'⭐ {unrated_featured} featured cars have no ratings - encourage reviews'
            )
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                self.stdout.write(f'{i}. {rec}')
        else:
            self.stdout.write('✅ All systems performing well!')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write('🎯 DASHBOARD COMPLETE')
        self.stdout.write('='*80)
