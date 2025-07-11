"""
Template tags for the promotion system
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import math

register = template.Library()


@register.simple_tag
def star_rating_display(rating, show_number=True, size='text-base'):
    """
    Display star rating with half-star support
    Args:
        rating: Decimal rating (0.0 to 5.0)
        show_number: Whether to show the numeric rating
        size: CSS class for star size
    """
    if not rating:
        rating = 0.0
    
    rating = float(rating)
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    html = f'<div class="flex items-center">'
    
    # Full stars
    for _ in range(full_stars):
        html += f'<i class="fas fa-star text-yellow-400 {size}"></i>'
    
    # Half star
    if half_star:
        html += f'<i class="fas fa-star-half-alt text-yellow-400 {size}"></i>'
    
    # Empty stars
    for _ in range(empty_stars):
        html += f'<i class="far fa-star text-gray-300 {size}"></i>'
    
    # Show numeric rating
    if show_number:
        html += f'<span class="ml-2 text-sm text-gray-600">({rating:.1f})</span>'
    
    html += '</div>'
    return mark_safe(html)


@register.simple_tag
def interactive_star_rating(rating, car_id, size='text-lg'):
    """
    Display interactive star rating for rating input
    """
    if not rating:
        rating = 0.0
    
    rating = float(rating)
    html = f'<div class="flex items-center star-rating-input" data-car-id="{car_id}" data-current-rating="{rating}">'
    
    # Create 10 half-star buttons (0.5, 1.0, 1.5, 2.0, etc.)
    for i in range(1, 11):
        star_value = i * 0.5
        is_filled = star_value <= rating
        is_half = (i % 2 == 1) and is_filled and (star_value > rating - 0.5)
        
        if i % 2 == 1:  # Half star positions
            icon_class = 'fas fa-star-half-alt' if is_half else 'far fa-star'
        else:  # Full star positions
            icon_class = 'fas fa-star' if is_filled else 'far fa-star'
        
        color_class = 'text-yellow-400' if is_filled or is_half else 'text-gray-300'
        
        html += f'''
        <button type="button" 
                class="star-btn {icon_class} {color_class} {size} hover:text-yellow-500 transition-colors cursor-pointer" 
                data-rating="{star_value}"
                title="{star_value} stars">
        </button>
        '''
    
    html += '</div>'
    return mark_safe(html)


@register.simple_tag
def promotion_badge(car):
    """
    Display promotion badges for a car
    """
    badges = car.get_promotion_badges()
    if not badges:
        return ''
    
    html = '<div class="absolute top-3 left-3 flex flex-col space-y-1">'
    
    for badge in badges:
        html += f'''
        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold text-white {badge['class']} shadow-lg">
            <i class="{badge['icon']} mr-1"></i>
            {badge['text']}
        </span>
        '''
    
    html += '</div>'
    return mark_safe(html)


@register.simple_tag
def tier_badge(tier, size='normal'):
    """
    Display tier badge with appropriate styling
    """
    if tier == 'none' or not tier:
        return ''
    
    tier_config = {
        'bronze': {
            'text': 'Bronze',
            'class': 'bg-amber-600',
            'icon': 'fas fa-medal'
        },
        'silver': {
            'text': 'Silver',
            'class': 'bg-gray-400',
            'icon': 'fas fa-medal'
        },
        'gold': {
            'text': 'Gold',
            'class': 'bg-yellow-500',
            'icon': 'fas fa-crown'
        },
        'platinum': {
            'text': 'Platinum',
            'class': 'bg-purple-600',
            'icon': 'fas fa-gem'
        }
    }
    
    if tier not in tier_config:
        return ''
    
    config = tier_config[tier]
    size_class = 'text-xs px-2 py-1' if size == 'small' else 'text-sm px-3 py-1'
    
    html = f'''
    <span class="inline-flex items-center {size_class} rounded-full text-white {config['class']} font-bold shadow-lg">
        <i class="{config['icon']} mr-1"></i>
        {config['text']}
    </span>
    '''
    
    return mark_safe(html)


@register.simple_tag
def hot_deal_countdown(hot_deal):
    """
    Display countdown timer for hot deals
    """
    if not hot_deal or not hot_deal.is_currently_active():
        return ''
    
    time_remaining = hot_deal.time_remaining_formatted()
    
    html = f'''
    <div class="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold animate-pulse">
        <i class="fas fa-fire mr-1"></i>
        {time_remaining} left
    </div>
    '''
    
    return mark_safe(html)


@register.filter
def rating_to_stars(rating):
    """
    Convert numeric rating to star string
    """
    if not rating:
        return '☆☆☆☆☆'
    
    rating = float(rating)
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    result = '★' * full_stars
    if half_star:
        result += '☆'  # Half star representation
    result += '☆' * empty_stars
    
    return result


@register.filter
def rating_percentage(rating):
    """
    Convert rating to percentage for progress bars
    """
    if not rating:
        return 0
    return (float(rating) / 5.0) * 100


@register.inclusion_tag('components/star_rating_breakdown.html')
def star_rating_breakdown(car):
    """
    Display detailed star rating breakdown
    """
    ratings = car.ratings.filter(is_approved=True)
    
    # Count ratings by star level
    rating_counts = {i: 0 for i in [5, 4, 3, 2, 1]}
    total_ratings = ratings.count()
    
    if total_ratings > 0:
        for rating in ratings:
            star_level = int(rating.rating)
            if star_level in rating_counts:
                rating_counts[star_level] += 1
    
    # Calculate percentages
    rating_percentages = {}
    for star, count in rating_counts.items():
        rating_percentages[star] = (count / total_ratings * 100) if total_ratings > 0 else 0
    
    return {
        'car': car,
        'rating_counts': rating_counts,
        'rating_percentages': rating_percentages,
        'total_ratings': total_ratings,
        'average_rating': car.calculated_rating
    }


@register.simple_tag
def rating_filter_options():
    """
    Generate rating filter options for forms
    """
    options = [
        (4.5, '4.5+ stars'),
        (4.0, '4+ stars'),
        (3.5, '3.5+ stars'),
        (3.0, '3+ stars'),
        (2.5, '2.5+ stars'),
        (2.0, '2+ stars'),
        (1.5, '1.5+ stars'),
        (1.0, '1+ stars'),
        (0.5, '0.5+ stars'),
    ]
    return options


@register.simple_tag
def featured_filter_options():
    """
    Generate featured filter options for forms
    """
    options = [
        ('featured', 'Featured Cars'),
        ('certified', 'Certified Cars'),
        ('hot_deals', 'Hot Deals'),
    ]
    return options
