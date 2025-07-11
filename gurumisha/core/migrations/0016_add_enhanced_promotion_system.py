# Generated manually for enhanced promotion system
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_car_promotion_fields'),
    ]

    operations = [
        # Create VendorSubscription model
        migrations.CreateModel(
            name='VendorSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', models.CharField(choices=[('basic', 'Basic'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], default='basic', max_length=20)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('auto_renew', models.BooleanField(default=False)),
                ('max_featured_cars', models.PositiveIntegerField(default=0)),
                ('max_hot_deals', models.PositiveIntegerField(default=0)),
                ('priority_support', models.BooleanField(default=False)),
                ('analytics_access', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='core.vendor')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create FeaturedCarTier model
        migrations.CreateModel(
            name='FeaturedCarTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], max_length=20, unique=True)),
                ('display_name', models.CharField(max_length=50)),
                ('priority_order', models.PositiveIntegerField(help_text='Lower numbers = higher priority', unique=True)),
                ('badge_color', models.CharField(default='bg-gray-500', max_length=20)),
                ('badge_icon', models.CharField(default='fas fa-star', max_length=50)),
                ('homepage_slots', models.PositiveIntegerField(default=0, help_text='Number of slots on homepage')),
                ('listing_boost_percentage', models.PositiveIntegerField(default=0, help_text='Boost in search results')),
                ('monthly_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['priority_order'],
            },
        ),
        
        # Add new fields to Vendor model
        migrations.AddField(
            model_name='vendor',
            name='total_sales',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='vendor',
            name='average_rating',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=3),
        ),
        migrations.AddField(
            model_name='vendor',
            name='response_time_hours',
            field=models.PositiveIntegerField(default=24, help_text='Average response time in hours'),
        ),
        
        # Add new fields to Car model
        migrations.AddField(
            model_name='car',
            name='inquiry_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='car',
            name='calculated_rating',
            field=models.DecimalField(decimal_places=1, default=0.0, help_text='Calculated rating with half-star precision (0.0-5.0)', max_digits=3),
        ),
        migrations.AddField(
            model_name='car',
            name='featured_tier',
            field=models.CharField(choices=[('none', 'Not Featured'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], default='none', max_length=20),
        ),
        migrations.AddField(
            model_name='car',
            name='featured_until',
            field=models.DateTimeField(blank=True, help_text='When featuring expires', null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='auto_featured',
            field=models.BooleanField(default=False, help_text='Automatically featured based on vendor subscription'),
        ),
        migrations.AddField(
            model_name='car',
            name='last_rating_update',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
