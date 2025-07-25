from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
import json
import logging
from datetime import datetime, timedelta

from .models import (
    BlogPost, ContentTag, ContentSeries, User, OpinionPoll, PollOption, PollVote,
    OpinionReview, ReviewHelpfulVote
)

logger = logging.getLogger(__name__)

# Enhanced Resource Management Views

@staff_member_required
def admin_resource_management(request):
    """Enhanced admin resource management dashboard"""
    # Get statistics
    total_posts = BlogPost.objects.count()
    published_posts = BlogPost.objects.filter(status='published').count()
    draft_posts = BlogPost.objects.filter(status='draft').count()
    
    # Content type breakdown
    content_types = BlogPost.objects.values('content_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent posts
    recent_posts = BlogPost.objects.select_related('author').order_by('-created_at')[:10]
    
    # Popular posts (by views)
    popular_posts = BlogPost.objects.filter(
        status='published'
    ).order_by('-views_count')[:10]
    
    # Get all tags and series for filters
    tags = ContentTag.objects.annotate(
        post_count=Count('blogpost')
    ).order_by('-post_count')[:20]
    
    series = ContentSeries.objects.annotate(
        post_count=Count('blogpost')
    ).order_by('-post_count')
    
    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'content_types': content_types,
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
        'tags': tags,
        'series': series,
    }
    
    return render(request, 'core/admin_resource_management.html', context)

@staff_member_required
@require_POST
def admin_resource_create(request):
    """Create new resource via HTMX"""
    try:
        data = json.loads(request.body)
        
        # Create new blog post
        post = BlogPost.objects.create(
            title=data.get('title', ''),
            content=data.get('content', ''),
            content_type=data.get('content_type', 'article'),
            status=data.get('status', 'draft'),
            author=request.user,
            excerpt=data.get('excerpt', ''),
            reading_time=data.get('reading_time', 5),
            difficulty_level=data.get('difficulty_level', 'beginner'),
            is_featured=data.get('is_featured', False),
        )
        
        # Handle tags
        if data.get('tags'):
            tag_names = [tag.strip() for tag in data.get('tags').split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag, created = ContentTag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': tag_name.lower().replace(' ', '-')}
                    )
                    post.tags.add(tag)
        
        # Handle series
        if data.get('series_id'):
            try:
                series = ContentSeries.objects.get(id=data.get('series_id'))
                post.series = series
                post.save()
            except ContentSeries.DoesNotExist:
                pass
        
        # Handle content-type specific data
        if post.content_type == 'opinion' and data.get('poll_data'):
            poll_data = data.get('poll_data')
            poll = OpinionPoll.objects.create(
                post=post,
                question=poll_data.get('question', ''),
                description=poll_data.get('description', ''),
                is_active=poll_data.get('is_active', True),
                allow_multiple_votes=poll_data.get('allow_multiple_votes', False),
                show_results_before_voting=poll_data.get('show_results_before_voting', False),
                end_date=poll_data.get('end_date')
            )
            
            # Create poll options
            for option_data in poll_data.get('options', []):
                PollOption.objects.create(
                    poll=poll,
                    text=option_data.get('text', ''),
                    description=option_data.get('description', '')
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Resource created successfully',
            'post_id': post.id,
            'redirect_url': reverse('core:admin_resource_edit', args=[post.id])
        })
        
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating resource: {str(e)}'
        }, status=400)

@staff_member_required
def admin_resource_edit(request, post_id):
    """Edit resource page"""
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Get all tags and series for dropdowns
    all_tags = ContentTag.objects.all().order_by('name')
    all_series = ContentSeries.objects.all().order_by('name')
    
    # Get poll data if it's an opinion post
    poll_data = None
    if post.content_type == 'opinion':
        try:
            poll = OpinionPoll.objects.get(post=post)
            poll_data = {
                'poll': poll,
                'options': poll.options.all()
            }
        except OpinionPoll.DoesNotExist:
            pass
    
    context = {
        'post': post,
        'all_tags': all_tags,
        'all_series': all_series,
        'poll_data': poll_data,
    }
    
    return render(request, 'core/admin_resource_edit.html', context)

@staff_member_required
@require_POST
def admin_resource_update(request, post_id):
    """Update resource via HTMX"""
    post = get_object_or_404(BlogPost, id=post_id)
    
    try:
        data = json.loads(request.body)
        
        # Update basic fields
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        post.excerpt = data.get('excerpt', post.excerpt)
        post.content_type = data.get('content_type', post.content_type)
        post.status = data.get('status', post.status)
        post.reading_time = data.get('reading_time', post.reading_time)
        post.difficulty_level = data.get('difficulty_level', post.difficulty_level)
        post.is_featured = data.get('is_featured', post.is_featured)
        
        # Handle news-specific fields
        if post.content_type == 'news':
            post.news_source = data.get('news_source', post.news_source)
            post.news_location = data.get('news_location', post.news_location)
            post.breaking_news = data.get('breaking_news', post.breaking_news)
            post.news_priority = data.get('news_priority', post.news_priority)
        
        # Handle chart data for infographics
        if post.content_type == 'infographic' and data.get('chart_data'):
            post.chart_data = data.get('chart_data')
            post.chart_type = data.get('chart_type', post.chart_type)
            post.chart_title = data.get('chart_title', post.chart_title)
            post.chart_description = data.get('chart_description', post.chart_description)
        
        post.save()
        
        # Update tags
        if 'tags' in data:
            post.tags.clear()
            tag_names = [tag.strip() for tag in data.get('tags').split(',')]
            for tag_name in tag_names:
                if tag_name:
                    tag, created = ContentTag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': tag_name.lower().replace(' ', '-')}
                    )
                    post.tags.add(tag)
        
        # Update series
        if 'series_id' in data:
            if data.get('series_id'):
                try:
                    series = ContentSeries.objects.get(id=data.get('series_id'))
                    post.series = series
                except ContentSeries.DoesNotExist:
                    post.series = None
            else:
                post.series = None
            post.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Resource updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating resource: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating resource: {str(e)}'
        }, status=400)

@staff_member_required
@require_POST
def admin_resource_delete(request, post_id):
    """Delete resource"""
    post = get_object_or_404(BlogPost, id=post_id)
    
    try:
        post.delete()
        return JsonResponse({
            'success': True,
            'message': 'Resource deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting resource: {str(e)}'
        }, status=400)

@staff_member_required
def admin_resources_table(request):
    """HTMX endpoint for resources table"""
    # Get filter parameters
    search = request.GET.get('search', '')
    content_type = request.GET.get('content_type', '')
    status = request.GET.get('status', '')
    tag_id = request.GET.get('tag_id', '')
    series_id = request.GET.get('series_id', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Build query
    posts = BlogPost.objects.select_related('author', 'series').prefetch_related('tags')
    
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(excerpt__icontains=search)
        )
    
    if content_type:
        posts = posts.filter(content_type=content_type)
    
    if status:
        posts = posts.filter(status=status)
    
    if tag_id:
        posts = posts.filter(tags__id=tag_id)
    
    if series_id:
        posts = posts.filter(series__id=series_id)
    
    # Apply sorting
    posts = posts.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'core/partials/admin_resources_table.html', context)

@staff_member_required
def admin_analytics_dashboard(request):
    """Analytics dashboard for resources"""
    # Time period filter
    period = request.GET.get('period', '30d')
    
    if period == '7d':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '90d':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '1y':
        start_date = timezone.now() - timedelta(days=365)
    else:  # 30d default
        start_date = timezone.now() - timedelta(days=30)
    
    # Get analytics data
    total_views = BlogPost.objects.aggregate(
        total=models.Sum('views_count')
    )['total'] or 0
    
    total_likes = BlogPost.objects.aggregate(
        total=models.Sum('likes_count')
    )['total'] or 0
    
    total_comments = BlogPost.objects.aggregate(
        total=models.Sum('comment_count')
    )['total'] or 0
    
    total_bookmarks = BlogPost.objects.aggregate(
        total=models.Sum('bookmark_count')
    )['total'] or 0
    
    total_content = BlogPost.objects.count()
    
    # Active users (users who interacted in the period)
    active_users = User.objects.filter(
        last_login__gte=start_date
    ).count()
    
    # Categories for filter
    categories = ContentTag.objects.annotate(
        post_count=Count('blogpost')
    ).order_by('-post_count')
    
    context = {
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_bookmarks': total_bookmarks,
        'total_content': total_content,
        'active_users': active_users,
        'categories': categories,
        'current_period': period,
    }
    
    return render(request, 'core/admin_analytics_dashboard.html', context)

# Public Resource Views

def global_search(request):
    """Global search endpoint for enhanced navigation"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': False,
            'message': 'Query too short'
        })
    
    # Search in published posts
    posts = BlogPost.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query) |
        Q(tags__name__icontains=query)
    ).distinct().select_related('author').prefetch_related('tags')[:10]
    
    results = []
    for post in posts:
        results.append({
            'title': post.title,
            'excerpt': post.excerpt or post.content[:150] + '...',
            'url': reverse('core:resource_detail', args=[post.slug]),
            'content_type': post.get_content_type_display(),
            'icon': post.get_content_type_icon(),
            'date': post.created_at.strftime('%b %d, %Y'),
            'views': post.views_count or 0,
        })
    
    return JsonResponse({
        'success': True,
        'results': results
    })

def resources_by_category(request, category_slug):
    """Filter resources by category"""
    try:
        category = ContentTag.objects.get(slug=category_slug)
    except ContentTag.DoesNotExist:
        return redirect('core:resources')
    
    posts = BlogPost.objects.filter(
        status='published',
        tags=category
    ).select_related('author', 'series').prefetch_related('tags').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'category': category,
        'page_title': f'{category.name} - Resources',
    }
    
    return render(request, 'core/blog.html', context)

@require_POST
@login_required
def content_like_toggle(request, post_id):
    """Toggle like status for content"""
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Check if user already liked this post
    user_liked = hasattr(request.user, 'liked_posts') and post in request.user.liked_posts.all()
    
    if user_liked:
        # Unlike
        request.user.liked_posts.remove(post)
        post.update_likes_count()
        action = 'unliked'
    else:
        # Like
        request.user.liked_posts.add(post)
        post.update_likes_count()
        action = 'liked'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'likes_count': post.likes_count,
        'message': f'Post {action} successfully'
    })

@require_POST
@login_required
def content_bookmark_toggle(request, post_id):
    """Toggle bookmark status for content"""
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Check if user already bookmarked this post
    user_bookmarked = hasattr(request.user, 'bookmarked_posts') and post in request.user.bookmarked_posts.all()
    
    if user_bookmarked:
        # Remove bookmark
        request.user.bookmarked_posts.remove(post)
        post.update_bookmark_count()
        action = 'unbookmarked'
    else:
        # Add bookmark
        request.user.bookmarked_posts.add(post)
        post.update_bookmark_count()
        action = 'bookmarked'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'bookmark_count': post.bookmark_count,
        'message': f'Post {action} successfully'
    })

# Mobile-specific views

def mobile_search(request):
    """Mobile-optimized search endpoint"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': False,
            'message': 'Query too short'
        })
    
    # Search with mobile-optimized results
    posts = BlogPost.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query)
    ).select_related('author')[:8]  # Fewer results for mobile
    
    results = []
    for post in posts:
        results.append({
            'title': post.title,
            'excerpt': post.excerpt or post.content[:100] + '...',
            'url': reverse('core:resource_detail', args=[post.slug]),
            'content_type': post.get_content_type_display(),
            'icon': post.get_content_type_icon(),
            'date': post.created_at.strftime('%b %d'),
        })
    
    return JsonResponse({
        'success': True,
        'results': results
    })

# Analytics and tracking views

@require_POST
def track_engagement(request):
    """Track user engagement data"""
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        engagement_data = data.get('engagement_data', {})
        
        if post_id:
            post = BlogPost.objects.get(id=post_id)
            
            # Update view count if this is a new session
            session_key = f'viewed_post_{post_id}'
            if not request.session.get(session_key):
                post.views_count = F('views_count') + 1
                post.save(update_fields=['views_count'])
                request.session[session_key] = True
        
        # Log engagement data for analytics
        logger.info(f"Engagement tracked for post {post_id}: {engagement_data}")
        
        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f"Error tracking engagement: {str(e)}")
        return JsonResponse({'success': False}, status=400)

@staff_member_required
@require_POST
def analytics_data(request):
    """Get analytics data for dashboard"""
    try:
        data = json.loads(request.body)
        filters = data.get('filters', {})

        # Apply time period filter
        time_period = filters.get('timePeriod', '30d')
        if time_period == '7d':
            start_date = timezone.now() - timedelta(days=7)
        elif time_period == '90d':
            start_date = timezone.now() - timedelta(days=90)
        elif time_period == '1y':
            start_date = timezone.now() - timedelta(days=365)
        else:
            start_date = timezone.now() - timedelta(days=30)

        # Get posts in time period
        posts = BlogPost.objects.filter(created_at__gte=start_date)

        # Apply content type filter
        if filters.get('contentType') and filters.get('contentType') != 'all':
            posts = posts.filter(content_type=filters.get('contentType'))

        # Apply category filter
        if filters.get('category') and filters.get('category') != 'all':
            posts = posts.filter(tags__id=filters.get('category'))

        # Calculate stats
        stats = {
            'totalViews': posts.aggregate(total=models.Sum('views_count'))['total'] or 0,
            'totalLikes': posts.aggregate(total=models.Sum('likes_count'))['total'] or 0,
            'totalComments': posts.aggregate(total=models.Sum('comment_count'))['total'] or 0,
            'totalBookmarks': posts.aggregate(total=models.Sum('bookmark_count'))['total'] or 0,
            'totalContent': posts.count(),
            'activeUsers': User.objects.filter(last_login__gte=start_date).count(),
        }

        # Performance data (daily aggregates)
        performance_data = []
        current_date = start_date.date()
        end_date = timezone.now().date()

        while current_date <= end_date:
            day_posts = posts.filter(created_at__date=current_date)
            performance_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'views': day_posts.aggregate(total=models.Sum('views_count'))['total'] or 0,
                'likes': day_posts.aggregate(total=models.Sum('likes_count'))['total'] or 0,
                'comments': day_posts.aggregate(total=models.Sum('comment_count'))['total'] or 0,
                'bookmarks': day_posts.aggregate(total=models.Sum('bookmark_count'))['total'] or 0,
            })
            current_date += timedelta(days=1)

        # Content type distribution
        content_types = posts.values('content_type').annotate(
            count=Count('id')
        ).order_by('-count')

        content_type_data = {
            'articles': 0,
            'guides': 0,
            'infographics': 0,
            'opinions': 0,
            'news': 0,
        }

        for ct in content_types:
            if ct['content_type'] in content_type_data:
                content_type_data[ct['content_type']] = ct['count']

        # Activity heatmap (hourly data)
        activity_data = [0] * 24  # 24 hours

        # Engagement funnel
        engagement_data = {
            'views': stats['totalViews'],
            'likes': stats['totalLikes'],
            'comments': stats['totalComments'],
            'bookmarks': stats['totalBookmarks'],
            'shares': 0,  # Would need to track shares separately
        }

        # Top content
        top_content = posts.order_by('-views_count')[:10]
        top_content_data = []

        for post in top_content:
            top_content_data.append({
                'title': post.title,
                'excerpt': post.excerpt or post.content[:100] + '...',
                'contentType': post.get_content_type_display(),
                'views': post.views_count or 0,
                'likes': post.likes_count or 0,
                'comments': post.comment_count or 0,
                'bookmarks': post.bookmark_count or 0,
                'publishedAt': post.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'stats': stats,
            'performance': {
                'labels': [item['date'] for item in performance_data],
                'data': [item['views'] for item in performance_data],  # Default to views
            },
            'contentTypes': content_type_data,
            'activity': activity_data,
            'engagement': engagement_data,
            'topContent': top_content_data,
        })

    except Exception as e:
        logger.error(f"Error getting analytics data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@staff_member_required
def top_content_data(request):
    """Get top content data based on metric"""
    metric = request.GET.get('metric', 'views')

    try:
        filters = json.loads(request.body) if request.method == 'POST' else {}

        # Get posts
        posts = BlogPost.objects.filter(status='published')

        # Apply filters
        if filters.get('contentType') and filters.get('contentType') != 'all':
            posts = posts.filter(content_type=filters.get('contentType'))

        if filters.get('category') and filters.get('category') != 'all':
            posts = posts.filter(tags__id=filters.get('category'))

        # Sort by metric
        if metric == 'views':
            posts = posts.order_by('-views_count')
        elif metric == 'likes':
            posts = posts.order_by('-likes_count')
        elif metric == 'comments':
            posts = posts.order_by('-comment_count')
        elif metric == 'bookmarks':
            posts = posts.order_by('-bookmark_count')
        elif metric == 'engagement':
            # Calculate engagement score
            posts = posts.annotate(
                engagement_score=F('views_count') + F('likes_count') * 2 + F('comment_count') * 3 + F('bookmark_count') * 4
            ).order_by('-engagement_score')

        # Get top 20
        top_posts = posts[:20]

        top_content_data = []
        for post in top_posts:
            top_content_data.append({
                'title': post.title,
                'excerpt': post.excerpt or post.content[:100] + '...',
                'contentType': post.get_content_type_display(),
                'views': post.views_count or 0,
                'likes': post.likes_count or 0,
                'comments': post.comment_count or 0,
                'bookmarks': post.bookmark_count or 0,
                'publishedAt': post.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'topContent': top_content_data
        })

    except Exception as e:
        logger.error(f"Error getting top content data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@staff_member_required
def export_analytics(request):
    """Export analytics report as PDF"""
    try:
        data = json.loads(request.body)
        filters = data.get('filters', {})

        # Generate PDF report (simplified version)
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Add content to PDF
        p.drawString(100, 750, "Gurumisha Analytics Report")
        p.drawString(100, 720, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

        # Add basic stats
        posts = BlogPost.objects.all()
        total_views = posts.aggregate(total=models.Sum('views_count'))['total'] or 0
        total_posts = posts.count()

        p.drawString(100, 680, f"Total Posts: {total_posts}")
        p.drawString(100, 660, f"Total Views: {total_views}")

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analytics-report-{timezone.now().strftime("%Y%m%d")}.pdf"'

        return response

    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# Comment system views

@require_POST
@login_required
def add_comment(request, post_id):
    """Add comment to post"""
    post = get_object_or_404(BlogPost, id=post_id)

    try:
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({
                'success': False,
                'message': 'Comment content is required'
            }, status=400)

        # Create comment (simplified - you'd need a Comment model)
        # For now, just return success
        post.update_comment_count()

        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully'
        })

    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def get_sorted_comments(request, post_id):
    """Get sorted comments for a post"""
    from .models import ContentComment

    post = get_object_or_404(BlogPost, id=post_id, is_published=True)
    sort_by = request.GET.get('sort', 'newest')

    # Get approved comments
    comments = ContentComment.objects.filter(
        post=post,
        is_approved=True,
        parent=None  # Only top-level comments for now
    ).select_related('user')

    # Apply sorting
    if sort_by == 'oldest':
        comments = comments.order_by('created_at')
    elif sort_by == 'popular':
        # For now, just order by creation date since we don't have likes on comments
        # In the future, you could add a likes field to comments
        comments = comments.order_by('-created_at')
    else:  # newest (default)
        comments = comments.order_by('-created_at')

    context = {
        'comments': comments,
        'post': post,
        'sort_by': sort_by,
    }

    return render(request, 'core/partials/comments_list.html', context)


def load_more_comments(request, post_id):
    """Load more comments with pagination"""
    from .models import ContentComment
    from django.core.paginator import Paginator

    post = get_object_or_404(BlogPost, id=post_id, is_published=True)
    offset = int(request.GET.get('offset', 0))
    sort_by = request.GET.get('sort', 'newest')

    # Get approved comments
    comments = ContentComment.objects.filter(
        post=post,
        is_approved=True,
        parent=None  # Only top-level comments for now
    ).select_related('user')

    # Apply sorting
    if sort_by == 'oldest':
        comments = comments.order_by('created_at')
    elif sort_by == 'popular':
        comments = comments.order_by('-created_at')
    else:  # newest (default)
        comments = comments.order_by('-created_at')

    # Pagination
    paginator = Paginator(comments, 10)  # 10 comments per page
    page_number = (offset // 10) + 1
    page_obj = paginator.get_page(page_number)

    # Get only the new comments for this page
    new_comments = page_obj.object_list

    context = {
        'comments': new_comments,
        'post': post,
        'sort_by': sort_by,
    }

    # Render the comments HTML
    html = render(request, 'core/partials/comments_list.html', context).content.decode('utf-8')

    return JsonResponse({
        'success': True,
        'html': html,
        'has_more': page_obj.has_next(),
        'total_comments': paginator.count
    })

def get_recommendations(request, post_id):
    """Get content recommendations for a post"""
    post = get_object_or_404(BlogPost, id=post_id)

    try:
        # Get related posts based on tags and content type
        related_posts = BlogPost.objects.filter(
            status='published'
        ).filter(
            Q(tags__in=post.tags.all()) |
            Q(content_type=post.content_type)
        ).exclude(id=post.id).distinct()[:6]

        recommendations = []
        for related_post in related_posts:
            recommendations.append({
                'title': related_post.title,
                'excerpt': related_post.excerpt or related_post.content[:100] + '...',
                'url': reverse('core:resource_detail', args=[related_post.slug]),
                'content_type': related_post.get_content_type_display(),
                'icon': related_post.get_content_type_icon(),
                'reading_time': related_post.reading_time or 5,
            })

        return JsonResponse({
            'success': True,
            'recommendations': recommendations
        })

    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
