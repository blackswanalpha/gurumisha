# Generated manually for HotDeal, CarRating, and PromotionAnalytics models
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_enhanced_promotion_system'),
    ]

    operations = [
        # Create HotDeal model
        migrations.CreateModel(
            name='HotDeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], default='percentage', max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='Percentage (0-100) or fixed amount', max_digits=10)),
                ('original_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('discounted_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('auto_activate', models.BooleanField(default=True, help_text='Automatically activate/deactivate based on dates')),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('clicks_count', models.PositiveIntegerField(default=0)),
                ('inquiries_count', models.PositiveIntegerField(default=0)),
                ('email_sent', models.BooleanField(default=False)),
                ('sms_sent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('car', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hot_deal_details', to='core.car')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create CarRating model
        migrations.CreateModel(
            name='CarRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.DecimalField(decimal_places=1, help_text='Rating from 0.5 to 5.0 in 0.5 increments', max_digits=3)),
                ('review', models.TextField(blank=True)),
                ('condition_rating', models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ('value_rating', models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ('service_rating', models.DecimalField(decimal_places=1, default=0.0, max_digits=3)),
                ('is_verified', models.BooleanField(default=False, help_text='Verified purchase')),
                ('is_approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='core.car')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='car_ratings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create PromotionAnalytics model
        migrations.CreateModel(
            name='PromotionAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_type', models.CharField(choices=[('featured_views', 'Featured Car Views'), ('featured_clicks', 'Featured Car Clicks'), ('hot_deal_views', 'Hot Deal Views'), ('hot_deal_clicks', 'Hot Deal Clicks'), ('tier_performance', 'Tier Performance'), ('rating_distribution', 'Rating Distribution')], max_length=30)),
                ('metric_value', models.PositiveIntegerField(default=0)),
                ('metric_data', models.JSONField(default=dict, help_text='Additional metric data')),
                ('date', models.DateField(auto_now_add=True)),
                ('hour', models.PositiveIntegerField(default=0, help_text='Hour of the day (0-23)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('car', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.car')),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.vendor')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Add unique constraint for CarRating
        migrations.AddConstraint(
            model_name='carrating',
            constraint=models.UniqueConstraint(fields=['car', 'customer'], name='unique_car_customer_rating'),
        ),
        
        # Add indexes for PromotionAnalytics
        migrations.AddIndex(
            model_name='promotionanalytics',
            index=models.Index(fields=['metric_type', 'date'], name='core_promotionanalytics_metric_date_idx'),
        ),
        migrations.AddIndex(
            model_name='promotionanalytics',
            index=models.Index(fields=['car', 'metric_type'], name='core_promotionanalytics_car_metric_idx'),
        ),
        migrations.AddIndex(
            model_name='promotionanalytics',
            index=models.Index(fields=['vendor', 'metric_type'], name='core_promotionanalytics_vendor_metric_idx'),
        ),
    ]
