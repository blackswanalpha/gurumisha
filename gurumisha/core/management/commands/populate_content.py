from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from core.models import (
    BlogPost, ContentCategory, ContentTag, ContentSeries, 
    ContentSeriesItem, ContentView, ContentLike, ContentComment
)
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with sample content management data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--posts',
            type=int,
            default=20,
            help='Number of blog posts to create',
        )
        parser.add_argument(
            '--categories',
            type=int,
            default=8,
            help='Number of categories to create',
        )
        parser.add_argument(
            '--tags',
            type=int,
            default=15,
            help='Number of tags to create',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting content population...'))
        
        # Create categories
        self.create_categories(options['categories'])
        
        # Create tags
        self.create_tags(options['tags'])
        
        # Create content series
        self.create_content_series()
        
        # Create blog posts
        self.create_blog_posts(options['posts'])
        
        # Create engagement data
        self.create_engagement_data()
        
        self.stdout.write(self.style.SUCCESS('Content population completed successfully!'))

    def create_categories(self, count):
        self.stdout.write('Creating content categories...')
        
        categories_data = [
            {'name': 'Car Reviews', 'description': 'In-depth reviews of vehicles and automotive products', 'icon': 'fa-car', 'color': '#3B82F6'},
            {'name': 'Maintenance Tips', 'description': 'Vehicle maintenance guides and tips', 'icon': 'fa-tools', 'color': '#10B981'},
            {'name': 'Buying Guides', 'description': 'Comprehensive guides for car buyers', 'icon': 'fa-shopping-cart', 'color': '#F59E0B'},
            {'name': 'Electric Vehicles', 'description': 'Everything about electric and hybrid vehicles', 'icon': 'fa-bolt', 'color': '#8B5CF6'},
            {'name': 'Safety & Security', 'description': 'Vehicle safety features and security tips', 'icon': 'fa-shield-alt', 'color': '#EF4444'},
            {'name': 'Industry News', 'description': 'Latest automotive industry news and trends', 'icon': 'fa-newspaper', 'color': '#06B6D4'},
            {'name': 'Technology', 'description': 'Automotive technology and innovations', 'icon': 'fa-microchip', 'color': '#84CC16'},
            {'name': 'Financing', 'description': 'Car financing and insurance information', 'icon': 'fa-credit-card', 'color': '#F97316'},
        ]
        
        for i, cat_data in enumerate(categories_data[:count]):
            category, created = ContentCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'sort_order': i + 1,
                }
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')

    def create_tags(self, count):
        self.stdout.write('Creating content tags...')
        
        tags_data = [
            'Electric Vehicles', 'Hybrid Cars', 'Fuel Efficiency', 'Safety Features',
            'Luxury Cars', 'Budget Cars', 'SUVs', 'Sedans', 'Hatchbacks',
            'Maintenance', 'Insurance', 'Financing', 'Technology', 'Innovation',
            'Performance', 'Reliability', 'Resale Value', 'First-Time Buyers',
            'Family Cars', 'Sports Cars', 'Off-Road', 'City Driving',
            'Long Distance', 'Eco-Friendly', 'Autonomous Driving'
        ]
        
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#84CC16', '#F97316']
        
        for i, tag_name in enumerate(tags_data[:count]):
            tag, created = ContentTag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'slug': slugify(tag_name),
                    'description': f'Content related to {tag_name.lower()}',
                    'color': random.choice(colors),
                }
            )
            if created:
                self.stdout.write(f'  Created tag: {tag.name}')

    def create_content_series(self):
        self.stdout.write('Creating content series...')
        
        series_data = [
            {
                'title': 'Electric Vehicle Complete Guide',
                'description': 'Everything you need to know about electric vehicles, from basics to advanced topics',
            },
            {
                'title': 'First-Time Car Buyer Series',
                'description': 'A comprehensive guide for first-time car buyers covering all aspects of the buying process',
            },
            {
                'title': 'Car Maintenance Mastery',
                'description': 'Learn how to maintain your vehicle like a pro with our step-by-step guides',
            },
        ]
        
        for series_info in series_data:
            series, created = ContentSeries.objects.get_or_create(
                title=series_info['title'],
                defaults={
                    'slug': slugify(series_info['title']),
                    'description': series_info['description'],
                }
            )
            if created:
                self.stdout.write(f'  Created series: {series.title}')

    def create_blog_posts(self, count):
        self.stdout.write(f'Creating {count} blog posts...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gurumisha.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        categories = list(ContentCategory.objects.all())
        tags = list(ContentTag.objects.all())
        content_types = ['article', 'guide', 'infographic', 'opinion', 'news', 'review']
        difficulty_levels = ['beginner', 'intermediate', 'advanced']
        
        posts_data = [
            {
                'title': 'Complete Guide to Electric Vehicle Charging',
                'content_type': 'guide',
                'excerpt': 'Learn everything about EV charging stations, home charging, and charging etiquette.',
                'difficulty': 'beginner',
                'read_time': 8,
            },
            {
                'title': '2024 Toyota Camry Review: Reliability Meets Innovation',
                'content_type': 'review',
                'excerpt': 'Our comprehensive review of the 2024 Toyota Camry covering performance, features, and value.',
                'difficulty': 'intermediate',
                'read_time': 12,
            },
            {
                'title': 'Top 10 Safety Features Every Car Should Have',
                'content_type': 'article',
                'excerpt': 'Essential safety features that can save lives and prevent accidents.',
                'difficulty': 'beginner',
                'read_time': 6,
            },
            {
                'title': 'Understanding Car Insurance: A Beginner\'s Guide',
                'content_type': 'guide',
                'excerpt': 'Navigate the complex world of car insurance with our comprehensive beginner\'s guide.',
                'difficulty': 'beginner',
                'read_time': 10,
            },
            {
                'title': 'The Future of Autonomous Driving Technology',
                'content_type': 'opinion',
                'excerpt': 'Exploring the current state and future prospects of self-driving car technology.',
                'difficulty': 'advanced',
                'read_time': 15,
            },
        ]
        
        # Extend posts_data with more generated content
        for i in range(len(posts_data), count):
            posts_data.append({
                'title': f'Automotive Insight #{i+1}: {random.choice(["Performance", "Efficiency", "Innovation", "Safety", "Technology"])} Focus',
                'content_type': random.choice(content_types),
                'excerpt': f'Detailed analysis of automotive {random.choice(["trends", "features", "innovations", "challenges"])} in the modern market.',
                'difficulty': random.choice(difficulty_levels),
                'read_time': random.randint(5, 20),
            })
        
        for i, post_data in enumerate(posts_data[:count]):
            # Create detailed content
            content = self.generate_content(post_data['title'], post_data['content_type'])
            
            post = BlogPost.objects.create(
                title=post_data['title'],
                slug=slugify(post_data['title']),
                content=content,
                excerpt=post_data['excerpt'],
                content_type=post_data['content_type'],
                difficulty_level=post_data['difficulty'],
                estimated_read_time=post_data['read_time'],
                author=admin_user,
                category=random.choice(categories) if categories else None,
                is_published=random.choice([True, True, True, False]),  # 75% published
                is_featured=random.choice([True, False, False, False]),  # 25% featured
                published_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                views_count=random.randint(50, 2000),
                likes_count=random.randint(5, 200),
                shares_count=random.randint(1, 50),
                meta_description=post_data['excerpt'][:160],
                meta_keywords=', '.join([tag.name for tag in random.sample(tags, min(5, len(tags)))] if tags else []),
            )
            
            # Add random tags
            if tags:
                post.tags.set(random.sample(tags, random.randint(2, min(5, len(tags)))))
            
            self.stdout.write(f'  Created post: {post.title}')

    def generate_content(self, title, content_type):
        """Generate realistic content based on title and type"""
        base_content = f"""
        <h2>Introduction</h2>
        <p>Welcome to our comprehensive {content_type} on {title.lower()}. This content provides valuable insights for automotive enthusiasts and everyday drivers alike.</p>
        
        <h2>Key Points</h2>
        <ul>
            <li>Expert analysis and recommendations</li>
            <li>Real-world testing and evaluation</li>
            <li>Practical tips and advice</li>
            <li>Industry insights and trends</li>
        </ul>
        
        <h2>Detailed Analysis</h2>
        <p>Our team of automotive experts has thoroughly researched and tested various aspects to bring you this comprehensive {content_type}. Whether you're a first-time buyer or an experienced car owner, this information will help you make informed decisions.</p>
        
        <h2>Conclusion</h2>
        <p>Understanding the automotive landscape is crucial for making the right choices. We hope this {content_type} has provided valuable insights to help you on your automotive journey.</p>
        """
        
        return base_content

    def create_engagement_data(self):
        self.stdout.write('Creating engagement data...')
        
        posts = BlogPost.objects.filter(is_published=True)
        admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            return
        
        for post in posts[:10]:  # Add engagement to first 10 posts
            # Create some views
            for _ in range(random.randint(10, 100)):
                ContentView.objects.create(
                    post=post,
                    user=admin_user if random.choice([True, False]) else None,
                    ip_address=f'192.168.1.{random.randint(1, 255)}',
                    viewed_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )
            
            # Create some likes
            if random.choice([True, False]):
                ContentLike.objects.create(
                    post=post,
                    user=admin_user
                )
            
            # Create some comments
            if random.choice([True, False]):
                ContentComment.objects.create(
                    post=post,
                    user=admin_user,
                    content=f'Great {post.content_type}! Very informative and well-written.',
                    is_approved=True
                )
        
        self.stdout.write('  Created engagement data for posts')
