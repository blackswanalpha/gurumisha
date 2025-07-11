"""
Analytics utilities for the promotion system
"""
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Car, HotDeal, CarRating, PromotionAnalytics, 
    Vendor, VendorSubscription, FeaturedCarTier
)


class PromotionAnalyticsManager:
    """Manager for promotion analytics and reporting"""
    
    def __init__(self):
        self.now = timezone.now()
    
    def record_metric(self, metric_type, car=None, vendor=None, metric_value=1, metric_data=None):
        """Record a promotion metric"""
        PromotionAnalytics.objects.create(
            metric_type=metric_type,
            car=car,
            vendor=vendor,
            metric_value=metric_value,
            metric_data=metric_data or {},
            date=self.now.date(),
            hour=self.now.hour
        )
    
    def get_featured_cars_performance(self, days=30):
        """Get featured cars performance metrics"""
        start_date = self.now.date() - timedelta(days=days)
        
        # Get featured cars metrics
        featured_metrics = PromotionAnalytics.objects.filter(
            metric_type__in=['featured_views', 'featured_clicks'],
            date__gte=start_date
        ).values('car__featured_tier', 'metric_type').annotate(
            total_value=Sum('metric_value')
        )
        
        # Organize by tier
        tier_performance = {}
        for tier in ['bronze', 'silver', 'gold', 'platinum']:
            tier_performance[tier] = {
                'views': 0,
                'clicks': 0,
                'ctr': 0.0  # Click-through rate
            }
        
        for metric in featured_metrics:
            tier = metric['car__featured_tier']
            if tier in tier_performance:
                if metric['metric_type'] == 'featured_views':
                    tier_performance[tier]['views'] = metric['total_value']
                elif metric['metric_type'] == 'featured_clicks':
                    tier_performance[tier]['clicks'] = metric['total_value']
        
        # Calculate CTR
        for tier_data in tier_performance.values():
            if tier_data['views'] > 0:
                tier_data['ctr'] = (tier_data['clicks'] / tier_data['views']) * 100
        
        return tier_performance
    
    def get_hot_deals_performance(self, days=30):
        """Get hot deals performance metrics"""
        start_date = self.now.date() - timedelta(days=days)
        
        # Get active hot deals in the period
        hot_deals = HotDeal.objects.filter(
            created_at__date__gte=start_date
        ).select_related('car')
        
        performance_data = []
        for deal in hot_deals:
            # Get metrics for this deal
            deal_metrics = PromotionAnalytics.objects.filter(
                metric_type__in=['hot_deal_views', 'hot_deal_clicks'],
                car=deal.car,
                date__gte=start_date
            ).values('metric_type').annotate(
                total_value=Sum('metric_value')
            )
            
            views = 0
            clicks = 0
            for metric in deal_metrics:
                if metric['metric_type'] == 'hot_deal_views':
                    views = metric['total_value']
                elif metric['metric_type'] == 'hot_deal_clicks':
                    clicks = metric['total_value']
            
            # Calculate savings and conversion
            savings = deal.original_price - deal.discounted_price
            savings_percentage = (savings / deal.original_price) * 100 if deal.original_price > 0 else 0
            
            performance_data.append({
                'deal': deal,
                'views': views,
                'clicks': clicks,
                'ctr': (clicks / views * 100) if views > 0 else 0,
                'savings': savings,
                'savings_percentage': savings_percentage,
                'is_active': deal.is_currently_active()
            })
        
        return performance_data
    
    def get_rating_distribution(self, days=30):
        """Get star rating distribution"""
        start_date = self.now.date() - timedelta(days=days)
        
        # Get rating distribution
        ratings = CarRating.objects.filter(
            created_at__date__gte=start_date,
            is_approved=True
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        # Create distribution data
        distribution = {}
        for i in range(1, 11):  # 0.5 to 5.0 in 0.5 increments
            rating_value = i * 0.5
            distribution[rating_value] = 0
        
        for rating_data in ratings:
            rating_value = float(rating_data['rating'])
            distribution[rating_value] = rating_data['count']
        
        return distribution
    
    def get_vendor_promotion_stats(self, vendor, days=30):
        """Get promotion statistics for a specific vendor"""
        start_date = self.now.date() - timedelta(days=days)
        
        # Get vendor's cars
        vendor_cars = Car.objects.filter(vendor=vendor)
        
        # Featured cars stats
        featured_cars = vendor_cars.exclude(featured_tier='none')
        featured_metrics = PromotionAnalytics.objects.filter(
            car__in=featured_cars,
            metric_type__in=['featured_views', 'featured_clicks'],
            date__gte=start_date
        ).aggregate(
            total_views=Sum('metric_value', filter=Q(metric_type='featured_views')),
            total_clicks=Sum('metric_value', filter=Q(metric_type='featured_clicks'))
        )
        
        # Hot deals stats
        hot_deals = HotDeal.objects.filter(
            car__in=vendor_cars,
            created_at__date__gte=start_date
        )
        hot_deal_metrics = PromotionAnalytics.objects.filter(
            car__in=vendor_cars,
            metric_type__in=['hot_deal_views', 'hot_deal_clicks'],
            date__gte=start_date
        ).aggregate(
            total_views=Sum('metric_value', filter=Q(metric_type='hot_deal_views')),
            total_clicks=Sum('metric_value', filter=Q(metric_type='hot_deal_clicks'))
        )
        
        # Rating stats
        rating_stats = CarRating.objects.filter(
            car__in=vendor_cars,
            created_at__date__gte=start_date,
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('id')
        )
        
        return {
            'featured_cars_count': featured_cars.count(),
            'featured_views': featured_metrics['total_views'] or 0,
            'featured_clicks': featured_metrics['total_clicks'] or 0,
            'hot_deals_count': hot_deals.count(),
            'hot_deal_views': hot_deal_metrics['total_views'] or 0,
            'hot_deal_clicks': hot_deal_metrics['total_clicks'] or 0,
            'average_rating': rating_stats['avg_rating'] or 0,
            'total_ratings': rating_stats['total_ratings'] or 0,
            'subscription_tier': vendor.get_subscription_tier()
        }
    
    def get_daily_metrics(self, days=7):
        """Get daily promotion metrics for charts"""
        start_date = self.now.date() - timedelta(days=days)
        
        daily_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            day_metrics = PromotionAnalytics.objects.filter(
                date=date
            ).values('metric_type').annotate(
                total_value=Sum('metric_value')
            )
            
            metrics_dict = {metric['metric_type']: metric['total_value'] for metric in day_metrics}
            
            daily_data.append({
                'date': date,
                'featured_views': metrics_dict.get('featured_views', 0),
                'featured_clicks': metrics_dict.get('featured_clicks', 0),
                'hot_deal_views': metrics_dict.get('hot_deal_views', 0),
                'hot_deal_clicks': metrics_dict.get('hot_deal_clicks', 0),
            })
        
        return daily_data
    
    def get_tier_comparison(self):
        """Compare performance across featured tiers"""
        tiers = FeaturedCarTier.objects.filter(is_active=True).order_by('priority_order')
        
        comparison_data = []
        for tier in tiers:
            # Get cars in this tier
            tier_cars = Car.objects.filter(featured_tier=tier.name, is_approved=True)
            
            # Get metrics for last 30 days
            start_date = self.now.date() - timedelta(days=30)
            tier_metrics = PromotionAnalytics.objects.filter(
                car__in=tier_cars,
                metric_type__in=['featured_views', 'featured_clicks'],
                date__gte=start_date
            ).aggregate(
                total_views=Sum('metric_value', filter=Q(metric_type='featured_views')),
                total_clicks=Sum('metric_value', filter=Q(metric_type='featured_clicks'))
            )
            
            views = tier_metrics['total_views'] or 0
            clicks = tier_metrics['total_clicks'] or 0
            
            comparison_data.append({
                'tier': tier,
                'cars_count': tier_cars.count(),
                'views': views,
                'clicks': clicks,
                'ctr': (clicks / views * 100) if views > 0 else 0,
                'avg_views_per_car': views / tier_cars.count() if tier_cars.count() > 0 else 0
            })
        
        return comparison_data
    
    def get_conversion_funnel(self, days=30):
        """Get conversion funnel data"""
        start_date = self.now.date() - timedelta(days=days)
        
        # Get total metrics
        total_metrics = PromotionAnalytics.objects.filter(
            date__gte=start_date
        ).values('metric_type').annotate(
            total_value=Sum('metric_value')
        )
        
        metrics_dict = {metric['metric_type']: metric['total_value'] for metric in total_metrics}
        
        # Calculate funnel stages
        featured_views = metrics_dict.get('featured_views', 0)
        featured_clicks = metrics_dict.get('featured_clicks', 0)
        hot_deal_views = metrics_dict.get('hot_deal_views', 0)
        hot_deal_clicks = metrics_dict.get('hot_deal_clicks', 0)
        
        # Get inquiries (assuming inquiries are tracked)
        total_inquiries = Car.objects.filter(
            created_at__date__gte=start_date
        ).aggregate(
            total_inquiries=Sum('inquiry_count')
        )['total_inquiries'] or 0
        
        return {
            'featured_views': featured_views,
            'featured_clicks': featured_clicks,
            'hot_deal_views': hot_deal_views,
            'hot_deal_clicks': hot_deal_clicks,
            'inquiries': total_inquiries,
            'featured_ctr': (featured_clicks / featured_views * 100) if featured_views > 0 else 0,
            'hot_deal_ctr': (hot_deal_clicks / hot_deal_views * 100) if hot_deal_views > 0 else 0,
        }
