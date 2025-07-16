"""
Management command to create sample resource content with enhanced features
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from core.models import (
    BlogPost, ContentCategory, ContentTag, OpinionPoll, PollOption, 
    OpinionReview, ContentSeries
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample resource content with polls, reviews, and charts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample content before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing sample content...')
            BlogPost.objects.filter(title__startswith='Sample').delete()
            ContentCategory.objects.filter(name__startswith='Sample').delete()
            ContentTag.objects.filter(name__startswith='Sample').delete()

        self.stdout.write('Creating sample resource content...')
        
        # Create sample categories and tags
        self.create_categories_and_tags()
        
        # Create sample content
        self.create_sample_opinions()
        self.create_sample_guides()
        self.create_sample_infographics()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample resource content!')
        )

    def create_categories_and_tags(self):
        """Create sample categories and tags"""
        categories = [
            ('Sample Automotive', 'Sample automotive content'),
            ('Sample Technology', 'Sample technology content'),
            ('Sample Business', 'Sample business content'),
        ]
        
        tags = [
            'Sample Cars', 'Sample Innovation', 'Sample Market', 'Sample Trends',
            'Sample Analysis', 'Sample Guide', 'Sample Opinion', 'Sample Data'
        ]
        
        for name, description in categories:
            category, created = ContentCategory.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slugify(name),
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created category: {name}')
        
        for tag_name in tags:
            tag, created = ContentTag.objects.get_or_create(
                name=tag_name,
                defaults={
                    'slug': slugify(tag_name),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created tag: {tag_name}')

    def create_sample_opinions(self):
        """Create sample opinion posts with polls and reviews"""
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='sample_admin',
                email='admin@sample.com',
                is_staff=True,
                is_superuser=True
            )
        
        category = ContentCategory.objects.filter(name__startswith='Sample').first()
        tags = ContentTag.objects.filter(name__startswith='Sample')[:3]
        
        opinions = [
            {
                'title': 'Sample Opinion: The Future of Electric Vehicles in Kenya',
                'content': '''
                <p>Electric vehicles (EVs) are rapidly gaining traction worldwide, but what does this mean for Kenya's automotive market? This opinion piece explores the potential impact and challenges.</p>
                
                <h3>Current State of EVs in Kenya</h3>
                <p>Kenya's EV market is still in its infancy, with limited charging infrastructure and high import costs. However, government initiatives and growing environmental awareness are driving change.</p>
                
                <h3>Opportunities and Challenges</h3>
                <ul>
                    <li>Government tax incentives for EV imports</li>
                    <li>Growing renewable energy sector</li>
                    <li>Limited charging infrastructure</li>
                    <li>High initial costs</li>
                </ul>
                
                <p>What are your thoughts on the future of electric vehicles in Kenya? Participate in our poll below!</p>
                ''',
                'poll_question': 'When do you think EVs will become mainstream in Kenya?',
                'poll_options': [
                    'Within 2-3 years',
                    'Within 5-7 years', 
                    'Within 10+ years',
                    'Never, due to infrastructure challenges'
                ]
            },
            {
                'title': 'Sample Opinion: Should Kenya Manufacture Cars Locally?',
                'content': '''
                <p>With the growing automotive market in East Africa, there's increasing debate about whether Kenya should establish local car manufacturing plants.</p>
                
                <h3>Benefits of Local Manufacturing</h3>
                <p>Local manufacturing could create jobs, reduce import costs, and boost the economy. Countries like South Africa and Morocco have successfully developed automotive manufacturing sectors.</p>
                
                <h3>Challenges to Consider</h3>
                <p>However, establishing manufacturing requires significant investment, skilled workforce, and supportive policies. The market size and regional integration are also crucial factors.</p>
                
                <p>Share your opinion on this important topic!</p>
                ''',
                'poll_question': 'Should Kenya prioritize local car manufacturing?',
                'poll_options': [
                    'Yes, it will boost the economy',
                    'Yes, but start with assembly plants',
                    'No, focus on importing quality vehicles',
                    'Undecided, need more information'
                ]
            }
        ]
        
        for opinion_data in opinions:
            # Create opinion post
            post = BlogPost.objects.create(
                title=opinion_data['title'],
                slug=slugify(opinion_data['title']),
                content=opinion_data['content'],
                excerpt=f"Sample opinion piece discussing {opinion_data['title'].lower()}",
                content_type='opinion',
                category=category,
                author=admin_user,
                is_published=True,
                published_at=timezone.now(),
                is_featured=True
            )
            
            # Add tags
            post.tags.set(tags)
            
            # Create poll
            poll = OpinionPoll.objects.create(
                opinion_post=post,
                question=opinion_data['poll_question'],
                poll_type='single_choice',
                is_active=True,
                allow_anonymous_voting=True
            )
            
            # Create poll options
            for i, option_text in enumerate(opinion_data['poll_options']):
                PollOption.objects.create(
                    poll=poll,
                    text=option_text,
                    order=i,
                    vote_count=0  # Will be populated with sample votes
                )
            
            self.stdout.write(f'Created opinion with poll: {post.title}')

    def create_sample_guides(self):
        """Create sample guide posts"""
        admin_user = User.objects.filter(is_staff=True).first()
        category = ContentCategory.objects.filter(name__startswith='Sample').first()
        tags = ContentTag.objects.filter(name__startswith='Sample')[:3]
        
        guides = [
            {
                'title': 'Sample Guide: Complete Car Buying Checklist for Kenya',
                'content': '''
                <h2>Introduction</h2>
                <p>Buying a car in Kenya can be overwhelming, especially for first-time buyers. This comprehensive guide will walk you through every step of the process.</p>
                
                <h2>Step 1: Determine Your Budget</h2>
                <p>Before you start shopping, establish a realistic budget that includes:</p>
                <ul>
                    <li>Purchase price</li>
                    <li>Insurance costs</li>
                    <li>Registration fees</li>
                    <li>Maintenance budget</li>
                </ul>
                
                <h2>Step 2: Research Vehicle Options</h2>
                <p>Consider factors like fuel efficiency, reliability, resale value, and availability of spare parts in Kenya.</p>
                
                <h2>Step 3: Inspect the Vehicle</h2>
                <p>Whether buying new or used, always conduct a thorough inspection or hire a qualified mechanic.</p>
                
                <h2>Step 4: Documentation and Legal Requirements</h2>
                <p>Ensure all paperwork is in order, including logbook transfer and insurance.</p>
                
                <h2>Conclusion</h2>
                <p>Following this checklist will help you make an informed decision and avoid common pitfalls in car buying.</p>
                ''',
                'read_time': 15
            },
            {
                'title': 'Sample Guide: Car Maintenance Schedule for Kenyan Conditions',
                'content': '''
                <h2>Understanding Kenyan Driving Conditions</h2>
                <p>Kenya's diverse terrain and climate conditions require specific maintenance approaches for optimal vehicle performance.</p>
                
                <h2>Daily Checks</h2>
                <ul>
                    <li>Engine oil level</li>
                    <li>Coolant level</li>
                    <li>Tire pressure</li>
                    <li>Lights and indicators</li>
                </ul>
                
                <h2>Weekly Maintenance</h2>
                <ul>
                    <li>Brake fluid level</li>
                    <li>Battery terminals</li>
                    <li>Windshield washer fluid</li>
                    <li>Tire condition and tread depth</li>
                </ul>
                
                <h2>Monthly Services</h2>
                <p>Detailed inspection of belts, hoses, air filter, and overall vehicle condition.</p>
                
                <h2>Seasonal Considerations</h2>
                <p>Adjust maintenance schedule based on rainy season, dusty conditions, and long-distance travel.</p>
                ''',
                'read_time': 12
            }
        ]
        
        for guide_data in guides:
            post = BlogPost.objects.create(
                title=guide_data['title'],
                slug=slugify(guide_data['title']),
                content=guide_data['content'],
                excerpt=f"Comprehensive guide covering {guide_data['title'].lower()}",
                content_type='guide',
                category=category,
                author=admin_user,
                estimated_read_time=guide_data['read_time'],
                is_published=True,
                published_at=timezone.now(),
                is_featured=True
            )
            
            post.tags.set(tags)
            self.stdout.write(f'Created guide: {post.title}')

    def create_sample_infographics(self):
        """Create sample infographic posts with chart data"""
        admin_user = User.objects.filter(is_staff=True).first()
        category = ContentCategory.objects.filter(name__startswith='Sample').first()
        tags = ContentTag.objects.filter(name__startswith='Sample')[:3]
        
        infographics = [
            {
                'title': 'Sample Infographic: Kenya Car Sales by Brand 2024',
                'content': '''
                <h2>Kenya's Automotive Market Overview</h2>
                <p>This infographic presents the latest data on car sales by brand in Kenya for 2024, showing market share and trends.</p>
                
                <h3>Key Insights</h3>
                <ul>
                    <li>Toyota maintains its leading position with 35% market share</li>
                    <li>Nissan and Subaru show strong growth in the SUV segment</li>
                    <li>Electric vehicle sales are beginning to emerge</li>
                    <li>Used car imports continue to dominate the market</li>
                </ul>
                
                <h3>Market Trends</h3>
                <p>The data reveals shifting consumer preferences towards fuel-efficient vehicles and SUVs, driven by economic factors and changing lifestyle needs.</p>
                ''',
                'chart_type': 'pie',
                'chart_data': {
                    'labels': ['Toyota', 'Nissan', 'Subaru', 'Mazda', 'Honda', 'Others'],
                    'datasets': [{
                        'label': 'Market Share (%)',
                        'data': [35, 18, 15, 12, 8, 12],
                        'backgroundColor': [
                            '#dc2626', '#991b1b', '#7f1d1d', '#ef4444', '#f87171', '#fca5a5'
                        ]
                    }]
                }
            },
            {
                'title': 'Sample Infographic: Average Car Prices in Kenya (2020-2024)',
                'content': '''
                <h2>Car Price Trends in Kenya</h2>
                <p>Analysis of average car prices across different categories over the past five years, showing the impact of economic factors and market dynamics.</p>
                
                <h3>Price Categories</h3>
                <ul>
                    <li>Economy Cars: KSh 800K - 1.5M</li>
                    <li>Mid-Range: KSh 1.5M - 3M</li>
                    <li>Luxury: KSh 3M - 8M</li>
                    <li>Premium: KSh 8M+</li>
                </ul>
                
                <h3>Factors Affecting Prices</h3>
                <p>Currency fluctuations, import duties, and global supply chain issues have significantly impacted car prices in Kenya.</p>
                ''',
                'chart_type': 'line',
                'chart_data': {
                    'labels': ['2020', '2021', '2022', '2023', '2024'],
                    'datasets': [
                        {
                            'label': 'Economy Cars (KSh Millions)',
                            'data': [1.2, 1.3, 1.5, 1.6, 1.7],
                            'borderColor': '#dc2626',
                            'backgroundColor': 'rgba(220, 38, 38, 0.1)'
                        },
                        {
                            'label': 'Mid-Range (KSh Millions)',
                            'data': [2.2, 2.4, 2.8, 3.0, 3.2],
                            'borderColor': '#991b1b',
                            'backgroundColor': 'rgba(153, 27, 27, 0.1)'
                        },
                        {
                            'label': 'Luxury (KSh Millions)',
                            'data': [5.5, 6.0, 6.8, 7.2, 7.8],
                            'borderColor': '#7f1d1d',
                            'backgroundColor': 'rgba(127, 29, 29, 0.1)'
                        }
                    ]
                }
            }
        ]
        
        for infographic_data in infographics:
            post = BlogPost.objects.create(
                title=infographic_data['title'],
                slug=slugify(infographic_data['title']),
                content=infographic_data['content'],
                excerpt=f"Data visualization showing {infographic_data['title'].lower()}",
                content_type='infographic',
                category=category,
                author=admin_user,
                chart_type=infographic_data['chart_type'],
                chart_data=infographic_data['chart_data'],
                is_published=True,
                published_at=timezone.now(),
                is_featured=True
            )
            
            post.tags.set(tags)
            self.stdout.write(f'Created infographic with chart: {post.title}')
