"""
Comprehensive tests for spare parts functionality
Tests models, views, forms, and M-Pesa integration
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json

from core.models import (
    SparePart, SparePartCategory, Supplier, Vendor, Cart, CartItem,
    Order, OrderItem, Payment, StockMovement, InventoryAlert
)
from core.forms import SparePartForm, SupplierForm
from core.mpesa_integration import MPesaAPI, validate_phone_number, validate_amount

User = get_user_model()


class SparePartModelTest(TestCase):
    """Test SparePart model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Vendor',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.user,
            company_name='Test Auto Parts',
            business_registration='BRN123456',
            location='Nairobi',
            is_active=True
        )
        
        self.category = SparePartCategory.objects.create(
            name='Engine Parts',
            description='Engine related spare parts',
            is_active=True
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            email='supplier@test.com',
            phone='+254700000000',
            is_active=True
        )
    
    def test_spare_part_creation(self):
        """Test creating a spare part"""
        spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Engine Oil Filter',
            sku='EOF001',
            part_number='12345',
            category_new=self.category,
            supplier=self.supplier,
            description='High quality engine oil filter',
            condition='new',
            price=Decimal('1500.00'),
            cost_price=Decimal('1000.00'),
            stock_quantity=50,
            minimum_stock=10,
            is_available=True
        )
        
        self.assertEqual(spare_part.name, 'Engine Oil Filter')
        self.assertEqual(spare_part.vendor, self.vendor)
        self.assertEqual(spare_part.category_new, self.category)
        self.assertTrue(spare_part.is_in_stock)
        self.assertEqual(spare_part.available_quantity, 50)
    
    def test_spare_part_stock_management(self):
        """Test stock management functionality"""
        spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Brake Pads',
            sku='BP001',
            price=Decimal('2500.00'),
            stock_quantity=5,
            minimum_stock=10,
            is_available=True
        )
        
        # Test low stock detection
        self.assertTrue(spare_part.is_low_stock)
        
        # Test out of stock
        spare_part.stock_quantity = 0
        spare_part.save()
        self.assertFalse(spare_part.is_in_stock)
    
    def test_spare_part_pricing(self):
        """Test pricing calculations"""
        spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Air Filter',
            sku='AF001',
            price=Decimal('800.00'),
            discount_price=Decimal('600.00'),
            cost_price=Decimal('400.00'),
            stock_quantity=20,
            is_available=True
        )
        
        self.assertEqual(spare_part.effective_price, Decimal('600.00'))
        self.assertEqual(spare_part.profit_margin, Decimal('200.00'))


class SparePartViewTest(TestCase):
    """Test spare parts views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer',
            role='customer'
        )
        
        self.vendor_user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Vendor',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Auto Parts',
            business_registration='BRN123456',
            is_active=True
        )
        
        self.spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Test Part',
            sku='TP001',
            price=Decimal('1000.00'),
            stock_quantity=10,
            is_available=True
        )
    
    def test_spare_parts_list_view(self):
        """Test spare parts listing page"""
        response = self.client.get(reverse('core:spare_parts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Part')
    
    def test_spare_part_detail_view(self):
        """Test spare part detail page"""
        response = self.client.get(
            reverse('core:spare_part_detail', kwargs={'pk': self.spare_part.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Part')
    
    def test_spare_parts_search(self):
        """Test spare parts search functionality"""
        response = self.client.get(reverse('core:spare_parts'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Part')
    
    def test_add_to_cart_authenticated(self):
        """Test adding spare part to cart when authenticated"""
        self.client.login(email='customer@test.com', password='testpass123')
        
        response = self.client.post(reverse('core:add_to_cart'), {
            'part_id': self.spare_part.id,
            'quantity': 2
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check cart was created
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, spare_part=self.spare_part)
        self.assertEqual(cart_item.quantity, 2)
    
    def test_add_to_cart_unauthenticated(self):
        """Test adding spare part to cart when not authenticated"""
        response = self.client.post(reverse('core:add_to_cart'), {
            'part_id': self.spare_part.id,
            'quantity': 1
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class CartFunctionalityTest(TestCase):
    """Test cart functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        
        self.vendor_user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Auto Parts',
            is_active=True
        )
        
        self.spare_part1 = SparePart.objects.create(
            vendor=self.vendor,
            name='Part 1',
            sku='P001',
            price=Decimal('500.00'),
            stock_quantity=10,
            is_available=True
        )
        
        self.spare_part2 = SparePart.objects.create(
            vendor=self.vendor,
            name='Part 2',
            sku='P002',
            price=Decimal('750.00'),
            stock_quantity=5,
            is_available=True
        )
        
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_total_calculation(self):
        """Test cart total calculation"""
        CartItem.objects.create(
            cart=self.cart,
            spare_part=self.spare_part1,
            quantity=2,
            price=self.spare_part1.price
        )
        
        CartItem.objects.create(
            cart=self.cart,
            spare_part=self.spare_part2,
            quantity=1,
            price=self.spare_part2.price
        )
        
        self.assertEqual(self.cart.total_amount, Decimal('1750.00'))
        self.assertEqual(self.cart.total_items, 3)
    
    def test_cart_item_update(self):
        """Test updating cart item quantity"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            spare_part=self.spare_part1,
            quantity=1,
            price=self.spare_part1.price
        )
        
        cart_item.quantity = 3
        cart_item.save()
        
        self.assertEqual(cart_item.total_price, Decimal('1500.00'))


class MPesaIntegrationTest(TestCase):
    """Test M-Pesa integration functionality"""
    
    def test_phone_number_validation(self):
        """Test phone number validation"""
        # Valid formats
        self.assertEqual(validate_phone_number('0700000000'), '254700000000')
        self.assertEqual(validate_phone_number('+254700000000'), '254700000000')
        self.assertEqual(validate_phone_number('254700000000'), '254700000000')
        
        # Invalid formats
        self.assertIsNone(validate_phone_number('070000000'))  # Too short
        self.assertIsNone(validate_phone_number('07000000000'))  # Too long
        self.assertIsNone(validate_phone_number('invalid'))  # Non-numeric
    
    def test_amount_validation(self):
        """Test amount validation"""
        # Valid amounts
        self.assertEqual(validate_amount('100'), 100.0)
        self.assertEqual(validate_amount('1000.50'), 1000.50)
        
        # Invalid amounts
        self.assertIsNone(validate_amount('0'))  # Too low
        self.assertIsNone(validate_amount('100000'))  # Too high
        self.assertIsNone(validate_amount('invalid'))  # Non-numeric


class SparePartFormTest(TestCase):
    """Test spare parts forms"""
    
    def setUp(self):
        self.vendor_user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Auto Parts',
            is_active=True
        )
        
        self.category = SparePartCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            email='supplier@test.com',
            is_active=True
        )
    
    def test_spare_part_form_valid(self):
        """Test valid spare part form"""
        form_data = {
            'name': 'Test Part',
            'sku': 'TP001',
            'part_number': '12345',
            'category_new': self.category.id,
            'supplier': self.supplier.id,
            'description': 'Test description',
            'condition': 'new',
            'price': '1000.00',
            'cost_price': '800.00',
            'stock_quantity': 10,
            'minimum_stock': 5,
            'is_available': True
        }
        
        form = SparePartForm(data=form_data, vendor=self.vendor)
        self.assertTrue(form.is_valid())
    
    def test_spare_part_form_invalid_price(self):
        """Test spare part form with invalid pricing"""
        form_data = {
            'name': 'Test Part',
            'sku': 'TP001',
            'price': '800.00',
            'cost_price': '1000.00',  # Cost higher than price
            'stock_quantity': 10,
            'is_available': True
        }
        
        form = SparePartForm(data=form_data, vendor=self.vendor)
        self.assertFalse(form.is_valid())
        self.assertIn('Cost price cannot be higher than selling price', str(form.errors))


class StockMovementTest(TestCase):
    """Test stock movement tracking"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.vendor_user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Auto Parts',
            is_active=True
        )
        
        self.spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Test Part',
            sku='TP001',
            price=Decimal('1000.00'),
            stock_quantity=20,
            is_available=True
        )
    
    def test_stock_movement_creation(self):
        """Test creating stock movement record"""
        movement = StockMovement.objects.create(
            spare_part=self.spare_part,
            movement_type='in',
            reason='purchase',
            quantity=10,
            quantity_before=0,
            quantity_after=10,
            notes='Restocked from supplier',
            created_by=self.user
        )
        
        self.assertEqual(movement.spare_part, self.spare_part)
        self.assertEqual(movement.movement_type, 'restock')
        self.assertEqual(movement.quantity, 10)
        self.assertEqual(movement.created_by, self.user)
    
    def test_stock_movement_tracking(self):
        """Test stock movement tracking over time"""
        # Initial stock
        initial_movement = StockMovement.objects.create(
            spare_part=self.spare_part,
            movement_type='in',
            reason='initial',
            quantity=20,
            quantity_before=0,
            quantity_after=20,
            created_by=self.user
        )

        # Sale
        sale_movement = StockMovement.objects.create(
            spare_part=self.spare_part,
            movement_type='out',
            reason='sale',
            quantity=-5,
            quantity_before=20,
            quantity_after=15,
            created_by=self.user
        )

        # Restock
        restock_movement = StockMovement.objects.create(
            spare_part=self.spare_part,
            movement_type='in',
            reason='purchase',
            quantity=10,
            quantity_before=15,
            quantity_after=25,
            created_by=self.user
        )
        
        movements = StockMovement.objects.filter(spare_part=self.spare_part).order_by('created_at')
        self.assertEqual(movements.count(), 3)
        self.assertEqual(movements.first().movement_type, 'initial')
        self.assertEqual(movements.last().movement_type, 'restock')


class APIEndpointTest(TestCase):
    """Test API endpoints for spare parts"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role='customer'
        )
        
        self.vendor_user = User.objects.create_user(
            email='vendor@test.com',
            password='testpass123',
            role='vendor'
        )
        
        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            company_name='Test Auto Parts',
            is_active=True
        )
        
        self.spare_part = SparePart.objects.create(
            vendor=self.vendor,
            name='Test Part',
            sku='TP001',
            price=Decimal('1000.00'),
            stock_quantity=10,
            is_available=True
        )
    
    def test_spare_parts_live_search(self):
        """Test live search endpoint"""
        response = self.client.get(reverse('core:spare_parts_live_search'), {
            'search': 'Test'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Part')
    
    def test_spare_parts_quick_view(self):
        """Test quick view endpoint"""
        response = self.client.get(
            reverse('core:spare_parts_quick_view', kwargs={'part_id': self.spare_part.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Part')
    
    def test_add_to_cart_htmx(self):
        """Test HTMX add to cart endpoint"""
        self.client.login(email='customer@test.com', password='testpass123')
        
        response = self.client.post(reverse('core:add_to_cart_htmx'), {
            'part_id': self.spare_part.id,
            'quantity': 1
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Check cart was created
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(CartItem.objects.filter(cart=cart, spare_part=self.spare_part).exists())
