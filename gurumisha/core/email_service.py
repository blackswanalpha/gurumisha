"""
Email service for promotion notifications and marketing campaigns
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.sites.models import Site
from .models import User, HotDeal, Car, Vendor
import logging

logger = logging.getLogger(__name__)


class PromotionEmailService:
    """Service for sending promotion-related emails"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kamandembugua18@gmail.com')
        self.site_url = self.get_site_url()
    
    def get_site_url(self):
        """Get the site URL for email links"""
        try:
            site = Site.objects.get_current()
            return f"http://{site.domain}"
        except:
            return "http://localhost:8000"  # Fallback for development
    
    def send_hot_deal_notification(self, hot_deal, recipients=None):
        """Send hot deal notification email"""
        if not recipients:
            # Get users who opted in for hot deal notifications
            recipients = User.objects.filter(
                notification_preferences__email_enabled=True,
                notification_preferences__email_marketing=True,
                role__in=['customer', 'vendor']
            ).values_list('email', flat=True)
        
        if not recipients:
            logger.warning("No recipients found for hot deal notification")
            return False
        
        try:
            # Prepare email context
            context = {
                'deal': hot_deal,
                'site_url': self.site_url,
                'current_year': timezone.now().year
            }
            
            # Render email templates
            html_content = render_to_string('emails/hot_deal_notification.html', context)
            text_content = render_to_string('emails/hot_deal_notification.txt', context)
            
            subject = f"🔥 Hot Deal Alert: {hot_deal.title} - Save KSh {hot_deal.original_price - hot_deal.discounted_price:,.0f}!"
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                bcc=list(recipients)  # Use BCC to protect recipient privacy
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent_count = msg.send()
            
            # Update deal notification status
            if sent_count > 0:
                hot_deal.email_sent = True
                hot_deal.save(update_fields=['email_sent'])
                logger.info(f"Hot deal notification sent to {len(recipients)} recipients")
            
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send hot deal notification: {str(e)}")
            return False
    
    def send_featured_car_notification(self, car, tier):
        """Send notification when a car gets featured"""
        try:
            # Notify the vendor
            vendor_email = car.vendor.user.email
            
            context = {
                'car': car,
                'tier': tier,
                'vendor': car.vendor,
                'site_url': self.site_url
            }
            
            html_content = render_to_string('emails/featured_car_notification.html', context)
            text_content = render_to_string('emails/featured_car_notification.txt', context)
            
            subject = f"🌟 Your car '{car.title}' is now {tier.title()} Featured!"
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[vendor_email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent = msg.send()
            logger.info(f"Featured car notification sent to vendor: {vendor_email}")
            return sent > 0
            
        except Exception as e:
            logger.error(f"Failed to send featured car notification: {str(e)}")
            return False
    
    def send_weekly_promotion_digest(self):
        """Send weekly digest of promotions to subscribers"""
        try:
            # Get active hot deals
            active_deals = HotDeal.objects.filter(
                is_active=True,
                car__is_approved=True
            ).select_related('car', 'car__brand', 'car__model')[:5]
            
            # Get newly featured cars
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            new_featured = Car.objects.filter(
                is_approved=True,
                featured_tier__in=['bronze', 'silver', 'gold', 'platinum'],
                updated_at__gte=week_ago
            ).select_related('brand', 'model', 'vendor')[:5]
            
            # Get top-rated cars
            top_rated = Car.objects.filter(
                is_approved=True,
                calculated_rating__gte=4.5
            ).order_by('-calculated_rating', '-views_count')[:5]
            
            if not (active_deals or new_featured or top_rated):
                logger.info("No content for weekly digest")
                return False
            
            # Get subscribers
            subscribers = User.objects.filter(
                notification_preferences__email_enabled=True,
                notification_preferences__email_marketing=True,
                role__in=['customer', 'vendor']
            ).values_list('email', flat=True)
            
            if not subscribers:
                logger.warning("No subscribers for weekly digest")
                return False
            
            context = {
                'active_deals': active_deals,
                'new_featured': new_featured,
                'top_rated': top_rated,
                'site_url': self.site_url,
                'current_year': timezone.now().year
            }
            
            html_content = render_to_string('emails/weekly_promotion_digest.html', context)
            text_content = render_to_string('emails/weekly_promotion_digest.txt', context)
            
            subject = f"🚗 Weekly Car Deals & Featured Vehicles - {timezone.now().strftime('%B %d, %Y')}"
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                bcc=list(subscribers)
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent_count = msg.send()
            logger.info(f"Weekly digest sent to {len(subscribers)} subscribers")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send weekly digest: {str(e)}")
            return False
    
    def send_vendor_promotion_summary(self, vendor):
        """Send monthly promotion performance summary to vendor"""
        try:
            from .analytics_utils import PromotionAnalyticsManager
            
            analytics = PromotionAnalyticsManager()
            vendor_stats = analytics.get_vendor_promotion_stats(vendor, days=30)
            
            # Get vendor's featured cars
            featured_cars = Car.objects.filter(
                vendor=vendor,
                featured_tier__in=['bronze', 'silver', 'gold', 'platinum']
            )
            
            # Get vendor's hot deals
            vendor_deals = HotDeal.objects.filter(
                car__vendor=vendor,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            )
            
            context = {
                'vendor': vendor,
                'stats': vendor_stats,
                'featured_cars': featured_cars,
                'hot_deals': vendor_deals,
                'site_url': self.site_url
            }
            
            html_content = render_to_string('emails/vendor_promotion_summary.html', context)
            text_content = render_to_string('emails/vendor_promotion_summary.txt', context)
            
            subject = f"📊 Monthly Promotion Summary - {timezone.now().strftime('%B %Y')}"
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[vendor.user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent = msg.send()
            logger.info(f"Vendor promotion summary sent to: {vendor.user.email}")
            return sent > 0
            
        except Exception as e:
            logger.error(f"Failed to send vendor promotion summary: {str(e)}")
            return False
    
    def send_personalized_recommendations(self, user):
        """Send personalized car recommendations based on user behavior"""
        try:
            from .models import CarRating
            
            # Get user's rating history
            user_ratings = CarRating.objects.filter(
                customer=user,
                rating__gte=4.0
            ).select_related('car')
            
            if not user_ratings:
                return False  # No data for recommendations
            
            # Analyze preferences
            liked_brands = set(rating.car.brand_id for rating in user_ratings)
            price_range = [rating.car.price for rating in user_ratings]
            avg_price = sum(price_range) / len(price_range) if price_range else 0
            
            # Find similar cars
            recommendations = Car.objects.filter(
                is_approved=True,
                status__in=['available', 'featured'],
                brand_id__in=liked_brands,
                price__gte=avg_price * 0.8,
                price__lte=avg_price * 1.2
            ).exclude(
                id__in=user_ratings.values_list('car_id', flat=True)
            ).order_by('-calculated_rating', '-views_count')[:6]
            
            if not recommendations:
                return False
            
            context = {
                'user': user,
                'recommendations': recommendations,
                'site_url': self.site_url
            }
            
            html_content = render_to_string('emails/personalized_recommendations.html', context)
            text_content = render_to_string('emails/personalized_recommendations.txt', context)
            
            subject = f"🎯 Personalized Car Recommendations for {user.first_name or user.username}"
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent = msg.send()
            logger.info(f"Personalized recommendations sent to: {user.email}")
            return sent > 0
            
        except Exception as e:
            logger.error(f"Failed to send personalized recommendations: {str(e)}")
            return False


# Convenience functions
def send_hot_deal_notification(hot_deal, recipients=None):
    """Send hot deal notification"""
    service = PromotionEmailService()
    return service.send_hot_deal_notification(hot_deal, recipients)


def send_featured_car_notification(car, tier):
    """Send featured car notification"""
    service = PromotionEmailService()
    return service.send_featured_car_notification(car, tier)


def send_weekly_promotion_digest():
    """Send weekly promotion digest"""
    service = PromotionEmailService()
    return service.send_weekly_promotion_digest()


def send_vendor_promotion_summary(vendor):
    """Send vendor promotion summary"""
    service = PromotionEmailService()
    return service.send_vendor_promotion_summary(vendor)
