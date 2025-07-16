"""
Management command to display the spare parts category tree structure
"""
from django.core.management.base import BaseCommand
from core.models import SparePartCategory


class Command(BaseCommand):
    help = 'Display the spare parts category tree structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed descriptions for each category',
        )

    def handle(self, *args, **options):
        self.detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS('Spare Parts Category Tree Structure'))
        self.stdout.write('=' * 60)
        
        # Get root categories (no parent)
        root_categories = SparePartCategory.objects.filter(parent=None).order_by('name')
        
        for category in root_categories:
            self.display_category(category, level=0)
        
        total_categories = SparePartCategory.objects.count()
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Total Categories: {total_categories}'))

    def display_category(self, category, level=0):
        """Display category with proper indentation"""
        indent = '  ' * level
        prefix = '├─ ' if level > 0 else ''
        
        if self.detailed and category.description:
            self.stdout.write(f'{indent}{prefix}{category.name}')
            self.stdout.write(f'{indent}   └─ {category.description}')
        else:
            self.stdout.write(f'{indent}{prefix}{category.name}')
        
        # Display subcategories
        subcategories = category.subcategories.all().order_by('name')
        for subcategory in subcategories:
            self.display_category(subcategory, level + 1)
