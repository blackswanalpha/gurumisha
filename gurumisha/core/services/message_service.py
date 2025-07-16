"""
Message Service
Handles message targeting, scheduling, and delivery logic
"""

from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Message, MessageRead, MessageTarget, MessageSchedule, MessageAnalytics
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class MessageTargetingService:
    """Service for handling message targeting logic"""
    
    @staticmethod
    def get_targeted_users(message):
        """Get all users that should receive this message based on targeting rules"""
        # Start with basic audience filtering
        users_qs = MessageTargetingService._get_base_audience(message)
        
        # Apply advanced targeting rules if they exist
        if message.targeting_rules.exists():
            users_qs = MessageTargetingService._apply_targeting_rules(message, users_qs)
        
        # Apply age restrictions
        if message.min_user_age_days or message.max_user_age_days:
            users_qs = MessageTargetingService._apply_age_restrictions(message, users_qs)
        
        # Apply email verification requirement
        if message.require_email_verified:
            users_qs = users_qs.filter(is_email_verified=True)
        
        return users_qs
    
    @staticmethod
    def _get_base_audience(message):
        """Get base user queryset based on target audience"""
        logger.debug(f"Getting base audience for message '{message.title}' with target_audience: {message.target_audience}")

        if message.target_audience == 'all':
            users = User.objects.filter(is_active=True)
        elif message.target_audience == 'customers':
            users = User.objects.filter(is_active=True, role='customer')
        elif message.target_audience == 'vendors':
            users = User.objects.filter(is_active=True, role='vendor')
        elif message.target_audience == 'admins':
            users = User.objects.filter(is_active=True, role='admin')
        elif message.target_audience == 'new_users':
            # Users registered in the last 30 days
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            users = User.objects.filter(is_active=True, date_joined__gte=cutoff_date)
        elif message.target_audience == 'active_users':
            # Users who logged in within the last 7 days
            cutoff_date = timezone.now() - timezone.timedelta(days=7)
            users = User.objects.filter(is_active=True, last_login__gte=cutoff_date)
        elif message.target_audience == 'inactive_users':
            # Users who haven't logged in for more than 30 days
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            users = User.objects.filter(
                Q(is_active=True) & (Q(last_login__lt=cutoff_date) | Q(last_login__isnull=True))
            )
        else:
            users = User.objects.none()

        logger.debug(f"Base audience for '{message.title}' has {users.count()} users")
        return users
    
    @staticmethod
    def _apply_targeting_rules(message, users_qs):
        """Apply advanced targeting rules to user queryset"""
        for rule in message.targeting_rules.filter(is_required=True):
            # Filter users based on each required rule
            matching_user_ids = []
            
            for user in users_qs:
                if rule.evaluate_for_user(user):
                    matching_user_ids.append(user.id)
            
            users_qs = users_qs.filter(id__in=matching_user_ids)
        
        return users_qs
    
    @staticmethod
    def _apply_age_restrictions(message, users_qs):
        """Apply user account age restrictions"""
        now = timezone.now()
        
        if message.min_user_age_days:
            min_date = now - timezone.timedelta(days=message.min_user_age_days)
            users_qs = users_qs.filter(date_joined__lte=min_date)
        
        if message.max_user_age_days:
            max_date = now - timezone.timedelta(days=message.max_user_age_days)
            users_qs = users_qs.filter(date_joined__gte=max_date)
        
        return users_qs
    
    @staticmethod
    def should_show_message_to_user(message, user):
        """Check if a specific message should be shown to a specific user"""
        # Check if message is active and within date range
        if not message.is_active:
            logger.debug(f"Message '{message.title}' is not active (status: {message.status})")
            return False

        # Check if user is in target audience
        targeted_users = MessageTargetingService.get_targeted_users(message)
        user_in_audience = targeted_users.filter(id=user.id).exists()
        logger.debug(f"Message '{message.title}' target_audience: {message.target_audience}, user role: {getattr(user, 'role', 'unknown')}, user in audience: {user_in_audience}")

        if not user_in_audience:
            return False

        # Check display frequency and limits
        try:
            read_record = MessageRead.objects.get(user=user, message=message)
            logger.debug(f"Message '{message.title}' - user has seen it {read_record.display_count} times (max: {message.max_displays_per_user})")

            # Check max displays per user
            if read_record.display_count >= message.max_displays_per_user:
                logger.debug(f"Message '{message.title}' - max displays reached")
                return False

            # Check display frequency
            if message.display_frequency_hours > 0:
                time_since_last = timezone.now() - read_record.last_seen_at
                hours_since_last = time_since_last.total_seconds() / 3600
                logger.debug(f"Message '{message.title}' - hours since last display: {hours_since_last:.2f}, required: {message.display_frequency_hours}")
                if time_since_last.total_seconds() < (message.display_frequency_hours * 3600):
                    return False

        except MessageRead.DoesNotExist:
            # User hasn't seen this message yet
            logger.debug(f"Message '{message.title}' - user hasn't seen it yet")
            pass

        logger.debug(f"Message '{message.title}' - should be shown to user")
        return True


class MessageSchedulingService:
    """Service for handling message scheduling logic"""
    
    @staticmethod
    def create_schedule(message, schedule_data):
        """Create a schedule for a message"""
        schedule = MessageSchedule.objects.create(
            message=message,
            frequency=schedule_data.get('frequency', 'once'),
            send_time=schedule_data.get('send_time'),
            timezone=schedule_data.get('timezone', 'UTC'),
            weekdays=schedule_data.get('weekdays', []),
            day_of_month=schedule_data.get('day_of_month'),
            max_occurrences=schedule_data.get('max_occurrences'),
            end_date=schedule_data.get('end_date'),
            is_active=True
        )
        
        # Calculate first send time
        schedule.next_send_at = schedule.calculate_next_send_time()
        schedule.save()
        
        return schedule
    
    @staticmethod
    def update_schedule(schedule, schedule_data):
        """Update an existing schedule"""
        for field, value in schedule_data.items():
            if hasattr(schedule, field):
                setattr(schedule, field, value)
        
        # Recalculate next send time
        schedule.next_send_at = schedule.calculate_next_send_time()
        schedule.save()
        
        return schedule
    
    @staticmethod
    def get_due_schedules():
        """Get all schedules that are due for processing"""
        now = timezone.now()
        return MessageSchedule.objects.filter(
            is_active=True,
            next_send_at__lte=now
        ).select_related('message')


class MessageAnalyticsService:
    """Service for handling message analytics"""
    
    @staticmethod
    def record_message_view(message, user, request=None):
        """Record that a user has viewed a message"""
        read_record, created = MessageRead.objects.get_or_create(
            user=user,
            message=message,
            defaults={
                'action': 'viewed',
                'display_count': 1,
                'ip_address': request.META.get('REMOTE_ADDR') if request else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
                'referrer_url': request.META.get('HTTP_REFERER', '') if request else '',
            }
        )
        
        if not created:
            read_record.display_count += 1
            read_record.last_seen_at = timezone.now()
            read_record.save()
        
        # Update message total views
        message.total_views += 1
        message.save()
        
        # Update daily analytics
        MessageAnalyticsService._update_daily_analytics(message, 'view', user)
        
        return read_record
    
    @staticmethod
    def record_message_action(message, user, action, request=None):
        """Record a user action on a message (click, dismiss, etc.)"""
        try:
            read_record = MessageRead.objects.get(user=user, message=message)
            read_record.mark_action(action)
        except MessageRead.DoesNotExist:
            # Create record if it doesn't exist
            read_record = MessageRead.objects.create(
                user=user,
                message=message,
                action=action,
                display_count=1,
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
                referrer_url=request.META.get('HTTP_REFERER', '') if request else '',
                action_taken_at=timezone.now()
            )
        
        # Update daily analytics
        MessageAnalyticsService._update_daily_analytics(message, action, user)
        
        return read_record
    
    @staticmethod
    def _update_daily_analytics(message, action, user):
        """Update daily analytics for a message"""
        from datetime import date
        today = date.today()
        
        analytics, created = MessageAnalytics.objects.get_or_create(
            message=message,
            date=today
        )
        
        if action == 'view':
            analytics.total_displays += 1
            # Update unique users shown (simplified - could be more sophisticated)
            analytics.unique_users_shown = MessageRead.objects.filter(
                message=message,
                first_seen_at__date=today
            ).values('user').distinct().count()
        elif action == 'clicked':
            analytics.total_clicks += 1
            analytics.unique_users_clicked = MessageRead.objects.filter(
                message=message,
                action='clicked',
                action_taken_at__date=today
            ).values('user').distinct().count()
        elif action == 'dismissed':
            analytics.total_dismissals += 1
            analytics.unique_users_dismissed = MessageRead.objects.filter(
                message=message,
                action='dismissed',
                action_taken_at__date=today
            ).values('user').distinct().count()
        
        # Update audience breakdown
        user_role = getattr(user, 'role', 'customer')
        if user_role == 'customer':
            analytics.customers_shown += 1
        elif user_role == 'vendor':
            analytics.vendors_shown += 1
        elif user_role == 'admin':
            analytics.admins_shown += 1
        
        analytics.save()
    
    @staticmethod
    def get_message_performance(message, days=30):
        """Get performance metrics for a message over the last N days"""
        from datetime import date, timedelta
        
        start_date = date.today() - timedelta(days=days)
        
        from django.db.models import Sum

        analytics = MessageAnalytics.objects.filter(
            message=message,
            date__gte=start_date
        ).aggregate(
            total_displays=Sum('total_displays'),
            total_clicks=Sum('total_clicks'),
            total_dismissals=Sum('total_dismissals'),
            unique_users=Sum('unique_users_shown')
        )
        
        # Calculate rates
        total_displays = analytics['total_displays'] or 0
        total_clicks = analytics['total_clicks'] or 0
        total_dismissals = analytics['total_dismissals'] or 0
        
        click_through_rate = (total_clicks / total_displays * 100) if total_displays > 0 else 0
        dismissal_rate = (total_dismissals / total_displays * 100) if total_displays > 0 else 0
        
        return {
            'total_displays': total_displays,
            'total_clicks': total_clicks,
            'total_dismissals': total_dismissals,
            'unique_users': analytics['unique_users'] or 0,
            'click_through_rate': round(click_through_rate, 2),
            'dismissal_rate': round(dismissal_rate, 2),
        }
