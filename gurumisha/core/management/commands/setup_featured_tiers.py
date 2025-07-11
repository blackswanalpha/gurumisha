"""
Management command to set up default featured car tiers
"""
from django.core.management.base import BaseCommand
from core.models import FeaturedCarTier


class Command(BaseCommand):
    help = 'Set up default featured car tiers'

    def handle(self, *args, **options):
        # Define default tier configurations
        tiers = [
            {
                'name': 'bronze',
                'display_name': 'Bronze Featured',
                'priority_order': 4,
                'badge_color': 'bg-amber-600',
                'badge_icon': 'fas fa-medal',
                'homepage_slots': 2,
                'listing_boost_percentage': 10,
                'monthly_price': 2500.00,
            },
            {
                'name': 'silver',
                'display_name': 'Silver Featured',
                'priority_order': 3,
                'badge_color': 'bg-gray-400',
                'badge_icon': 'fas fa-medal',
                'homepage_slots': 4,
                'listing_boost_percentage': 25,
                'monthly_price': 5000.00,
            },
            {
                'name': 'gold',
                'display_name': 'Gold Featured',
                'priority_order': 2,
                'badge_color': 'bg-yellow-500',
                'badge_icon': 'fas fa-crown',
                'homepage_slots': 6,
                'listing_boost_percentage': 50,
                'monthly_price': 10000.00,
            },
            {
                'name': 'platinum',
                'display_name': 'Platinum Featured',
                'priority_order': 1,
                'badge_color': 'bg-purple-600',
                'badge_icon': 'fas fa-gem',
                'homepage_slots': 8,
                'listing_boost_percentage': 100,
                'monthly_price': 20000.00,
            },
        ]

        created_count = 0
        updated_count = 0

        for tier_data in tiers:
            tier, created = FeaturedCarTier.objects.get_or_create(
                name=tier_data['name'],
                defaults=tier_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created tier: {tier.display_name}')
                )
            else:
                # Update existing tier with new data
                for key, value in tier_data.items():
                    if key != 'name':  # Don't update the name field
                        setattr(tier, key, value)
                tier.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated tier: {tier.display_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete! Created {created_count} new tiers, updated {updated_count} existing tiers.'
            )
        )
