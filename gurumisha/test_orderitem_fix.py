#!/usr/bin/env python3
"""
Test script to verify the OrderItem vendor_id fix
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/hp/Documents/augment-projects/gurumisha/gurumisha')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings')
django.setup()

from core.models import SparePart, OrderItem, Order, User
from decimal import Decimal

def test_orderitem_creation():
    """Test creating OrderItem with spare part that has no vendor"""
    print("Testing OrderItem creation with null vendor...")
    
    # Get a spare part with no vendor
    spare_part = SparePart.objects.filter(vendor__isnull=True).first()
    if not spare_part:
        print("No spare parts found with null vendor")
        return False
    
    print(f"Found spare part: {spare_part.name} (ID: {spare_part.id}) with vendor: {spare_part.vendor}")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+254700000000',
            'role': 'customer'
        }
    )
    
    # Create a test order
    order = Order.objects.create(
        order_number='TEST-ORDER-001',
        customer=user,
        customer_name='Test User',
        customer_email='test@example.com',
        customer_phone='+254700000000',
        shipping_address='Test Address',
        shipping_city='Nairobi',
        shipping_postal_code='00100',
        subtotal=Decimal('1000.00'),
        shipping_cost=Decimal('500.00'),
        total_amount=Decimal('1500.00')
    )
    
    try:
        # Try to create OrderItem with spare part that has no vendor
        order_item = OrderItem.objects.create(
            order=order,
            spare_part=spare_part,
            vendor=spare_part.vendor,  # This should be None
            part_name=spare_part.name,
            part_sku=spare_part.sku,
            part_description=spare_part.description or '',
            quantity=1,
            unit_price=spare_part.price,
            total_price=spare_part.price
        )
        
        print(f"✅ SUCCESS: OrderItem created successfully!")
        print(f"   OrderItem ID: {order_item.id}")
        print(f"   Vendor: {order_item.vendor}")
        print(f"   Part: {order_item.part_name}")
        
        # Clean up
        order_item.delete()
        order.delete()
        if created:
            user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to create OrderItem: {e}")
        
        # Clean up
        order.delete()
        if created:
            user.delete()
        
        return False

if __name__ == '__main__':
    success = test_orderitem_creation()
    if success:
        print("\n🎉 Test passed! The OrderItem vendor_id fix is working correctly.")
    else:
        print("\n💥 Test failed! There's still an issue with OrderItem creation.")
    
    sys.exit(0 if success else 1)
