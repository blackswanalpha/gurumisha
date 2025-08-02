from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import json

from ..models import BlogPost, ContentTag, ContentSeries, OpinionPoll, PollOption, PollVote

User = get_user_model()

class ResourceSystemTestCase(TestCase):
    """Comprehensive test suite for the enhanced resource management system"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create test content
        self.test_tag = ContentTag.objects.create(
            name='Test Tag',
            slug='test-tag'
        )
        
        self.test_series = ContentSeries.objects.create(
            name='Test Series',
            slug='test-series',
            description='Test series description'
        )
        
        # Create test blog posts for different content types
        self.article_post = BlogPost.objects.create(
            title='Test Article',
            slug='test-article',
            content='This is a test article content.',
            content_type='article',
            is_published=True,
            author=self.admin_user,
            excerpt='Test article excerpt',
            reading_time=5
        )
        self.article_post.tags.add(self.test_tag)

        self.guide_post = BlogPost.objects.create(
            title='Test Guide',
            slug='test-guide',
            content='This is a test guide content.',
            content_type='guide',
            is_published=True,
            author=self.admin_user,
            excerpt='Test guide excerpt',
            reading_time=10,
            pdf_file_size=1024000,
            pdf_download_count=5
        )

        self.infographic_post = BlogPost.objects.create(
            title='Test Infographic',
            slug='test-infographic',
            content='This is a test infographic content.',
            content_type='infographic',
            is_published=True,
            author=self.admin_user,
            chart_type='bar',
            chart_title='Test Chart',
            chart_data='{"labels": ["A", "B", "C"], "data": [10, 20, 30]}'
        )

        self.opinion_post = BlogPost.objects.create(
            title='Test Opinion',
            slug='test-opinion',
            content='This is a test opinion content.',
            content_type='opinion',
            is_published=True,
            author=self.admin_user
        )
        
        # Create opinion poll
        self.poll = OpinionPoll.objects.create(
            post=self.opinion_post,
            question='What do you think?',
            description='Test poll description',
            is_active=True
        )
        
        self.poll_option1 = PollOption.objects.create(
            poll=self.poll,
            text='Option 1'
        )
        
        self.poll_option2 = PollOption.objects.create(
            poll=self.poll,
            text='Option 2'
        )
        
        self.news_post = BlogPost.objects.create(
            title='Test News',
            slug='test-news',
            content='This is a test news content.',
            content_type='news',
            is_published=True,
            author=self.admin_user,
            news_source='Test Source',
            news_location='Test Location',
            breaking_news=True,
            news_priority='high'
        )

class PublicResourceViewsTest(ResourceSystemTestCase):
    """Test public resource views and functionality"""
    
    def test_resources_list_view(self):
        """Test the main resources list page"""
        response = self.client.get(reverse('core:resources'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Article')
        self.assertContains(response, 'Test Guide')
        self.assertContains(response, 'Test Infographic')
        self.assertContains(response, 'Test Opinion')
        self.assertContains(response, 'Test News')
    
    def test_resource_detail_views(self):
        """Test individual resource detail pages"""
        # Test article detail
        response = self.client.get(reverse('core:resource_detail', args=[self.article_post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article_post.title)
        self.assertContains(response, self.article_post.content)
        
        # Test guide detail
        response = self.client.get(reverse('core:resource_detail', args=[self.guide_post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PDF')
        
        # Test infographic detail
        response = self.client.get(reverse('core:resource_detail', args=[self.infographic_post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'chart')
        
        # Test opinion detail
        response = self.client.get(reverse('core:resource_detail', args=[self.opinion_post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.question)
        
        # Test news detail
        response = self.client.get(reverse('core:resource_detail', args=[self.news_post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Breaking News')
    
    def test_global_search(self):
        """Test global search functionality"""
        response = self.client.get(reverse('core:global_search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['results']), 0)
    
    def test_mobile_search(self):
        """Test mobile-optimized search"""
        response = self.client.get(reverse('core:mobile_search'), {'q': 'article'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['results']), 0)
    
    def test_resources_by_category(self):
        """Test category-based filtering"""
        response = self.client.get(reverse('core:resources_by_category', args=[self.test_tag.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article_post.title)

class UserInteractionTest(ResourceSystemTestCase):
    """Test user interaction features"""
    
    def test_content_like_toggle_authenticated(self):
        """Test liking content when authenticated"""
        self.client.login(username='user', password='testpass123')
        
        # Like the post
        response = self.client.post(reverse('core:content_like_toggle', args=[self.article_post.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'liked')
        
        # Unlike the post
        response = self.client.post(reverse('core:content_like_toggle', args=[self.article_post.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'unliked')
    
    def test_content_like_toggle_unauthenticated(self):
        """Test liking content when not authenticated"""
        response = self.client.post(reverse('core:content_like_toggle', args=[self.article_post.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_content_bookmark_toggle(self):
        """Test bookmarking content"""
        self.client.login(username='user', password='testpass123')
        
        # Bookmark the post
        response = self.client.post(reverse('core:content_bookmark_toggle', args=[self.article_post.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['action'], 'bookmarked')
    
    def test_engagement_tracking(self):
        """Test engagement tracking"""
        engagement_data = {
            'post_id': self.article_post.id,
            'engagement_data': {
                'timeOnPage': 120,
                'scrollDepth': 75,
                'interactions': [
                    {'type': 'scroll', 'timestamp': 1234567890}
                ]
            }
        }
        
        response = self.client.post(
            reverse('core:track_engagement'),
            data=json.dumps(engagement_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_get_recommendations(self):
        """Test content recommendations"""
        response = self.client.get(reverse('core:get_recommendations', args=[self.article_post.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['recommendations'], list)

class AdminResourceManagementTest(ResourceSystemTestCase):
    """Test admin resource management functionality"""
    
    def test_admin_resource_management_access(self):
        """Test admin access to resource management"""
        # Test unauthenticated access
        response = self.client.get(reverse('core:admin_resource_management'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test regular user access
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('core:admin_resource_management'))
        self.assertEqual(response.status_code, 302)  # Redirect due to lack of permissions
        
        # Test admin access
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('core:admin_resource_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resource Management')
    
    def test_admin_resource_create(self):
        """Test creating new resources via admin"""
        self.client.login(username='admin', password='testpass123')
        
        resource_data = {
            'title': 'New Test Resource',
            'content': 'New test content',
            'content_type': 'article',
            'status': 'draft',
            'excerpt': 'New test excerpt',
            'reading_time': 7,
            'difficulty_level': 'intermediate',
            'is_featured': False,
            'tags': 'test, new'
        }
        
        response = self.client.post(
            reverse('core:admin_resource_create'),
            data=json.dumps(resource_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify the resource was created
        new_post = BlogPost.objects.get(title='New Test Resource')
        self.assertEqual(new_post.content_type, 'article')
        self.assertEqual(new_post.status, 'draft')
    
    def test_admin_resources_table(self):
        """Test admin resources table HTMX endpoint"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('core:admin_resources_table'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article_post.title)
        
        # Test with search
        response = self.client.get(reverse('core:admin_resources_table'), {'search': 'article'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article_post.title)
        self.assertNotContains(response, self.guide_post.title)
    
    def test_analytics_dashboard(self):
        """Test analytics dashboard"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('core:admin_analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
    
    def test_analytics_data_api(self):
        """Test analytics data API"""
        self.client.login(username='admin', password='testpass123')
        
        filters = {
            'timePeriod': '30d',
            'contentType': 'all',
            'category': 'all'
        }
        
        response = self.client.post(
            reverse('core:analytics_data'),
            data=json.dumps({'filters': filters}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('performance', data)
        self.assertIn('contentTypes', data)

class ModelTest(ResourceSystemTestCase):
    """Test model functionality and methods"""
    
    def test_blogpost_model_methods(self):
        """Test BlogPost model methods"""
        # Test content type icon
        self.assertEqual(self.article_post.get_content_type_icon(), 'fas fa-newspaper')
        self.assertEqual(self.guide_post.get_content_type_icon(), 'fas fa-book')
        self.assertEqual(self.infographic_post.get_content_type_icon(), 'fas fa-chart-bar')
        self.assertEqual(self.opinion_post.get_content_type_icon(), 'fas fa-comment-alt')
        self.assertEqual(self.news_post.get_content_type_icon(), 'fas fa-rss')
        
        # Test engagement updates
        initial_likes = self.article_post.likes_count
        self.article_post.update_likes_count()
        self.assertEqual(self.article_post.likes_count, initial_likes)
        
        # Test reading time estimation
        long_content = 'word ' * 1000  # 1000 words
        long_post = BlogPost.objects.create(
            title='Long Post',
            slug='long-post',
            content=long_content,
            author=self.admin_user
        )
        estimated_time = long_post.estimate_reading_time()
        self.assertGreater(estimated_time, 0)
    
    def test_opinion_poll_functionality(self):
        """Test opinion poll voting"""
        # Test poll voting
        vote = PollVote.objects.create(
            poll=self.poll,
            option=self.poll_option1,
            user=self.regular_user
        )
        
        self.assertEqual(vote.poll, self.poll)
        self.assertEqual(vote.option, self.poll_option1)
        self.assertEqual(vote.user, self.regular_user)
        
        # Test vote count
        self.assertEqual(self.poll_option1.votes.count(), 1)
        self.assertEqual(self.poll_option2.votes.count(), 0)

class TemplateRenderingTest(ResourceSystemTestCase):
    """Test template rendering and components"""
    
    def test_enhanced_navigation_component(self):
        """Test enhanced navigation component rendering"""
        response = self.client.get(reverse('core:resources'))
        self.assertEqual(response.status_code, 200)
        # Check for navigation elements
        self.assertContains(response, 'enhanced-navigation')
        self.assertContains(response, 'global-search')
    
    def test_mobile_optimizations_component(self):
        """Test mobile optimizations component"""
        response = self.client.get(reverse('core:resources'))
        self.assertEqual(response.status_code, 200)
        # Check for mobile components
        self.assertContains(response, 'mobile-optimizations')
        self.assertContains(response, 'mobile-nav-overlay')
    
    def test_user_interactions_component(self):
        """Test user interactions component"""
        response = self.client.get(reverse('core:resource_detail', args=[self.article_post.slug]))
        self.assertEqual(response.status_code, 200)
        # Check for interaction elements
        self.assertContains(response, 'user-interactions')
        self.assertContains(response, 'engagement-actions')

class PerformanceTest(ResourceSystemTestCase):
    """Test system performance and optimization"""
    
    def test_database_queries_optimization(self):
        """Test that views use optimized database queries"""
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            # Reset queries
            connection.queries_log.clear()
            
            # Test resources list view
            response = self.client.get(reverse('core:resources'))
            self.assertEqual(response.status_code, 200)
            
            # Check that queries are reasonable (should be less than 10 for a simple list)
            query_count = len(connection.queries)
            self.assertLess(query_count, 15, f"Too many queries: {query_count}")
    
    def test_template_caching(self):
        """Test that templates are properly cached"""
        # First request
        response1 = self.client.get(reverse('core:resources'))
        self.assertEqual(response1.status_code, 200)
        
        # Second request should be faster due to caching
        response2 = self.client.get(reverse('core:resources'))
        self.assertEqual(response2.status_code, 200)
        
        # Content should be identical
        self.assertEqual(response1.content, response2.content)
