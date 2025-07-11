"""
Analytics utilities for Gurumisha Motors
"""
from django.utils import timezone
from django.db.models import Count, Q, Avg
from datetime import datetime, timedelta
from ..models import ProfileView, VendorAnalytics, UserActivityLog, Vendor, User


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request):
    """Get referrer from request"""
    return request.META.get('HTTP_REFERER', '')


def track_profile_view(request, profile_user):
    """
    Track a profile view for analytics
    
    Args:
        request: Django request object
        profile_user: User whose profile is being viewed
    """
    try:
        # Get viewer information
        viewer = request.user if request.user.is_authenticated else None
        viewer_ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        referrer = get_referrer(request)
        session_key = request.session.session_key or ''
        
        # Don't track self-views
        if viewer and viewer == profile_user:
            return None
        
        # Check if this is a unique view (same IP/session within last hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_view = ProfileView.objects.filter(
            profile_user=profile_user,
            viewer_ip=viewer_ip,
            viewed_at__gte=one_hour_ago
        ).first()
        
        if recent_view:
            return recent_view
        
        # Create new profile view record
        profile_view = ProfileView.objects.create(
            profile_user=profile_user,
            viewer=viewer,
            viewer_ip=viewer_ip,
            user_agent=user_agent,
            referrer=referrer,
            session_key=session_key
        )
        
        # Update vendor analytics if profile user is a vendor
        if hasattr(profile_user, 'vendor'):
            update_vendor_profile_views(profile_user.vendor)
        
        return profile_view
        
    except Exception as e:
        # Log error but don't break the view
        print(f"Error tracking profile view: {e}")
        return None


def update_vendor_profile_views(vendor):
    """Update vendor profile view analytics"""
    try:
        analytics, created = VendorAnalytics.objects.get_or_create(vendor=vendor)
        
        # Count total profile views
        total_views = ProfileView.objects.filter(profile_user=vendor.user).count()
        analytics.total_profile_views = total_views
        
        # Count unique profile views (distinct IP addresses)
        unique_views = ProfileView.objects.filter(
            profile_user=vendor.user
        ).values('viewer_ip').distinct().count()
        analytics.unique_profile_views = unique_views
        
        # Count views this month
        this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        views_this_month = ProfileView.objects.filter(
            profile_user=vendor.user,
            viewed_at__gte=this_month_start
        ).count()
        analytics.profile_views_this_month = views_this_month
        
        # Count views last month
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(seconds=1)
        views_last_month = ProfileView.objects.filter(
            profile_user=vendor.user,
            viewed_at__gte=last_month_start,
            viewed_at__lte=last_month_end
        ).count()
        analytics.profile_views_last_month = views_last_month
        
        analytics.save()
        return analytics
        
    except Exception as e:
        print(f"Error updating vendor profile views: {e}")
        return None


def log_user_activity(user, action, description='', request=None, metadata=None):
    """
    Log user activity for analytics
    
    Args:
        user: User performing the action
        action: Action type (from UserActivityLog.ACTION_CHOICES)
        description: Optional description
        request: Django request object (optional)
        metadata: Additional metadata dict (optional)
    """
    try:
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
        
        UserActivityLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
    except Exception as e:
        print(f"Error logging user activity: {e}")


def get_vendor_analytics_summary(vendor):
    """Get comprehensive analytics summary for a vendor"""
    try:
        analytics, created = VendorAnalytics.objects.get_or_create(vendor=vendor)
        
        if created or not analytics.last_updated or \
           (timezone.now() - analytics.last_updated).total_seconds() > 3600:  # Update hourly
            analytics.update_analytics()
        
        # Get recent activity
        recent_activities = UserActivityLog.objects.filter(
            user=vendor.user
        ).order_by('-timestamp')[:10]
        
        # Get profile view trends (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_views = ProfileView.objects.filter(
            profile_user=vendor.user,
            viewed_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(viewed_at)'}
        ).values('day').annotate(
            views=Count('id')
        ).order_by('day')
        
        # Calculate growth rates
        current_month_views = analytics.profile_views_this_month
        last_month_views = analytics.profile_views_last_month
        
        if last_month_views > 0:
            view_growth_rate = ((current_month_views - last_month_views) / last_month_views) * 100
        else:
            view_growth_rate = 100 if current_month_views > 0 else 0
        
        return {
            'analytics': analytics,
            'recent_activities': recent_activities,
            'daily_views': list(daily_views),
            'view_growth_rate': round(view_growth_rate, 1),
            'performance_level': get_performance_level(analytics.overall_performance_score),
        }
        
    except Exception as e:
        print(f"Error getting vendor analytics summary: {e}")
        return None


def get_performance_level(score):
    """Get performance level based on score"""
    if score >= 90:
        return {'level': 'Excellent', 'color': 'green', 'icon': 'star'}
    elif score >= 75:
        return {'level': 'Good', 'color': 'blue', 'icon': 'thumbs-up'}
    elif score >= 60:
        return {'level': 'Average', 'color': 'yellow', 'icon': 'minus-circle'}
    elif score >= 40:
        return {'level': 'Below Average', 'color': 'orange', 'icon': 'exclamation-triangle'}
    else:
        return {'level': 'Poor', 'color': 'red', 'icon': 'times-circle'}


def get_user_analytics_summary(user):
    """Get analytics summary for regular users"""
    try:
        # Get recent activities
        recent_activities = UserActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # Count various activities
        total_activities = UserActivityLog.objects.filter(user=user).count()
        
        # Activity breakdown
        activity_breakdown = UserActivityLog.objects.filter(
            user=user
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Profile views made by this user
        profile_views_made = ProfileView.objects.filter(viewer=user).count()
        
        return {
            'recent_activities': recent_activities,
            'total_activities': total_activities,
            'activity_breakdown': list(activity_breakdown),
            'profile_views_made': profile_views_made,
        }
        
    except Exception as e:
        print(f"Error getting user analytics summary: {e}")
        return None


def update_all_vendor_analytics():
    """Update analytics for all vendors (for scheduled tasks)"""
    vendors = Vendor.objects.all()
    updated_count = 0
    
    for vendor in vendors:
        try:
            analytics, created = VendorAnalytics.objects.get_or_create(vendor=vendor)
            analytics.update_analytics()
            update_vendor_profile_views(vendor)
            updated_count += 1
        except Exception as e:
            print(f"Error updating analytics for vendor {vendor.id}: {e}")
    
    return updated_count


def get_analytics_dashboard_data(user):
    """Get dashboard data based on user type"""
    if user.role == 'vendor' and hasattr(user, 'vendor'):
        return get_vendor_analytics_summary(user.vendor)
    else:
        return get_user_analytics_summary(user)
