from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    SparePartCategory, Supplier, SparePart, Vendor, CarBrand,
    PurchaseOrder, PurchaseOrderItem, StockMovement, InventoryAlert
)
from django.utils import timezone
from decimal import Decimal
import random
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate enhanced spare parts data for Gurumisha Motors'

    def handle(self, *args, **options):
        self.stdout.write('Creating enhanced spare parts data...')

        # Create spare part categories
        categories_data = [
            {'name': 'Engine Parts', 'description': 'Engine components and accessories'},
            {'name': 'Suspension', 'description': 'Suspension system components'},
            {'name': 'Brakes', 'description': 'Brake system parts'},
            {'name': 'Electrical', 'description': 'Electrical components and wiring'},
            {'name': 'Body Parts', 'description': 'Exterior and interior body components'},
            {'name': 'Transmission', 'description': 'Transmission and drivetrain parts'},
            {'name': 'Cooling System', 'description': 'Radiator, cooling fans, and related parts'},
            {'name': 'Exhaust System', 'description': 'Exhaust pipes, mufflers, and catalytic converters'},
        ]

        categories = []
        for cat_data in categories_data:
            category, created = SparePartCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create subcategories
        subcategories_data = [
            {'name': 'Oil Filters', 'parent': 'Engine Parts'},
            {'name': 'Air Filters', 'parent': 'Engine Parts'},
            {'name': 'Spark Plugs', 'parent': 'Engine Parts'},
            {'name': 'Shock Absorbers', 'parent': 'Suspension'},
            {'name': 'Springs', 'parent': 'Suspension'},
            {'name': 'Brake Pads', 'parent': 'Brakes'},
            {'name': 'Brake Discs', 'parent': 'Brakes'},
            {'name': 'Headlights', 'parent': 'Electrical'},
            {'name': 'Batteries', 'parent': 'Electrical'},
        ]

        for subcat_data in subcategories_data:
            parent = SparePartCategory.objects.get(name=subcat_data['parent'])
            subcategory, created = SparePartCategory.objects.get_or_create(
                name=subcat_data['name'],
                parent=parent
            )
            if created:
                self.stdout.write(f'Created subcategory: {subcategory.name}')

        # Create suppliers
        suppliers_data = [
            {
                'name': 'AutoParts Kenya Ltd',
                'contact_person': 'John Mwangi',
                'email': 'john@autopartskenya.com',
                'phone': '+254712345678',
                'payment_terms': 'Net 30 days',
                'rating': Decimal('4.5')
            },
            {
                'name': 'East Africa Motors Supply',
                'contact_person': 'Sarah Wanjiku',
                'email': 'sarah@eamotors.co.ke',
                'phone': '+254723456789',
                'payment_terms': 'Net 15 days',
                'rating': Decimal('4.2')
            },
            {
                'name': 'Global Auto Parts',
                'contact_person': 'David Kimani',
                'email': 'david@globalauto.com',
                'phone': '+254734567890',
                'payment_terms': 'Cash on delivery',
                'rating': Decimal('4.8')
            },
            {
                'name': 'Nairobi Spare Parts Hub',
                'contact_person': 'Grace Njeri',
                'email': 'grace@nrbspares.co.ke',
                'phone': '+254745678901',
                'payment_terms': 'Net 21 days',
                'rating': Decimal('4.0')
            }
        ]

        suppliers = []
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults=supplier_data
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')

        # Update existing spare parts with enhanced data
        spare_parts = SparePart.objects.all()
        vendors = list(Vendor.objects.all())
        
        for part in spare_parts:
            # Assign random supplier
            part.supplier = random.choice(suppliers)
            
            # Assign category_new based on existing category
            category_mapping = {
                'Engine': categories[0],  # Engine Parts
                'Suspension': categories[1],  # Suspension
                'Brakes': categories[2],  # Brakes
                'Electrical': categories[3],  # Electrical
                'Body': categories[4],  # Body Parts
                'Transmission': categories[5],  # Transmission
            }
            
            # Try to map existing category to new category
            for key, cat in category_mapping.items():
                if key.lower() in part.category.lower():
                    part.category_new = cat
                    break
            else:
                # Default to first category if no match
                part.category_new = categories[0]
            
            # Add enhanced inventory data
            part.cost_price = part.price * Decimal('0.7')  # 30% markup
            part.minimum_stock = random.randint(5, 15)
            part.maximum_stock = random.randint(50, 200)
            part.reorder_point = random.randint(10, 25)
            part.reorder_quantity = random.randint(20, 50)
            part.warehouse_location = f"A{random.randint(1, 10)}-{random.randint(1, 20)}"
            part.weight = Decimal(str(random.uniform(0.1, 50.0)))
            part.dimensions = f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(5, 50)}"
            
            # Generate unique barcode for some parts
            if random.choice([True, False]):
                part.barcode = f"BC{random.randint(100000000000, 999999999999)}"
            
            part.save()

        self.stdout.write(f'Updated {spare_parts.count()} spare parts with enhanced data')

        # Create some purchase orders
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user and vendors:
            for i in range(5):
                po = PurchaseOrder.objects.create(
                    order_number=f"PO-{timezone.now().year}-{i+1:04d}",
                    supplier=random.choice(suppliers),
                    vendor=random.choice(vendors),
                    status=random.choice(['draft', 'sent', 'confirmed']),
                    expected_delivery=timezone.now().date() + timezone.timedelta(days=random.randint(7, 30)),
                    tax_amount=Decimal('0'),
                    shipping_cost=Decimal(str(random.uniform(500, 2000))),
                    created_by=admin_user
                )
                
                # Add some items to the purchase order
                selected_parts = random.sample(list(spare_parts), random.randint(2, 5))
                for part in selected_parts:
                    quantity = random.randint(5, 50)
                    unit_cost = part.cost_price or part.price * Decimal('0.7')
                    
                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        spare_part=part,
                        quantity_ordered=quantity,
                        unit_cost=unit_cost,
                        total_amount=quantity * unit_cost
                    )
                
                po.calculate_totals()
                self.stdout.write(f'Created purchase order: {po.order_number}')

        # Create some inventory alerts for low stock items
        low_stock_parts = [part for part in spare_parts if part.stock_quantity <= part.minimum_stock]
        for part in low_stock_parts[:10]:  # Create alerts for first 10 low stock items
            InventoryAlert.objects.get_or_create(
                spare_part=part,
                alert_type='low_stock',
                defaults={
                    'message': f'Stock level for {part.name} is below minimum threshold',
                    'current_stock': part.stock_quantity,
                    'threshold_value': part.minimum_stock
                }
            )

        self.stdout.write(f'Created inventory alerts for {len(low_stock_parts[:10])} low stock items')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated enhanced spare parts data!')
        )
