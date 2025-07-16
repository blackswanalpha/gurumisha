"""
Enhanced HTMX Views for Spare Parts System
Provides real-time updates, dynamic filtering, and interactive elements
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
import json

from .models import (
    SparePart, SparePartCategory, Supplier, Cart, CartItem, 
    Order, OrderItem, StockMovement, InventoryAlert, Vendor
)


@require_http_methods(["GET"])
def spare_parts_live_search(request):
    """Enhanced live search with real-time filtering"""
    query = request.GET.get('search', '').strip()
    category = request.GET.get('category', '')
    supplier = request.GET.get('supplier', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    condition = request.GET.get('condition', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Base queryset
    spare_parts = SparePart.objects.filter(is_available=True).select_related(
        'vendor', 'supplier', 'category_new'
    ).prefetch_related('compatible_brands')
    
    # Apply filters
    if query:
        spare_parts = spare_parts.filter(
            Q(name__icontains=query) |
            Q(part_number__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )
    
    if category:
        spare_parts = spare_parts.filter(
            Q(category=category) | Q(category_new__name=category)
        )
    
    if supplier:
        spare_parts = spare_parts.filter(supplier_id=supplier)
    
    if min_price:
        try:
            spare_parts = spare_parts.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            spare_parts = spare_parts.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    if condition:
        spare_parts = spare_parts.filter(condition=condition)
    
    # Apply sorting
    if sort_by in ['name', '-name', 'price', '-price', 'created_at', '-created_at']:
        spare_parts = spare_parts.order_by(sort_by)
    else:
        spare_parts = spare_parts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(spare_parts, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'spare_parts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'total_results': paginator.count,
    }
    
    return render(request, 'core/partials/spare_parts_grid.html', context)


@require_http_methods(["GET"])
def spare_parts_quick_view(request, part_id):
    """Quick view modal for spare part details"""
    spare_part = get_object_or_404(SparePart, id=part_id, is_available=True)
    
    # Check if user has this part in cart
    in_cart = False
    cart_quantity = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(cart=cart, spare_part=spare_part)
            in_cart = True
            cart_quantity = cart_item.quantity
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass
    
    context = {
        'spare_part': spare_part,
        'in_cart': in_cart,
        'cart_quantity': cart_quantity,
    }
    
    return render(request, 'core/partials/spare_part_quick_view.html', context)


@login_required
@require_http_methods(["POST"])
def add_to_cart_htmx(request):
    """Enhanced add to cart with HTMX response"""
    part_id = request.POST.get('part_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        spare_part = SparePart.objects.get(id=part_id, is_available=True)
        
        # Check stock availability
        if spare_part.available_quantity < quantity:
            return render(request, 'core/partials/cart_error.html', {
                'message': f'Only {spare_part.available_quantity} items available in stock'
            })
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get or create cart item
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            spare_part=spare_part,
            defaults={
                'quantity': quantity,
                'price': spare_part.discount_price or spare_part.price
            }
        )
        
        if not item_created:
            # Update existing item
            new_quantity = cart_item.quantity + quantity
            if spare_part.available_quantity < new_quantity:
                return render(request, 'core/partials/cart_error.html', {
                    'message': f'Cannot add {quantity} more. Only {spare_part.available_quantity - cart_item.quantity} more available'
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Return success response with updated cart info
        context = {
            'success': True,
            'message': f'{spare_part.name} added to cart successfully',
            'cart_total_items': cart.total_items,
            'cart_total_amount': cart.total_amount,
            'part_id': part_id,
            'new_quantity': cart_item.quantity
        }
        
        return render(request, 'core/partials/cart_success.html', context)
        
    except SparePart.DoesNotExist:
        return render(request, 'core/partials/cart_error.html', {
            'message': 'Spare part not found'
        })
    except Exception as e:
        return render(request, 'core/partials/cart_error.html', {
            'message': 'An error occurred while adding to cart'
        })


@login_required
@require_http_methods(["POST"])
def update_cart_quantity_htmx(request):
    """Update cart item quantity with HTMX"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
        
        if quantity <= 0:
            # Remove item
            cart_item.delete()
            context = {
                'success': True,
                'message': 'Item removed from cart',
                'item_removed': True,
                'item_id': item_id
            }
        else:
            # Check stock availability
            if cart_item.spare_part.available_quantity < quantity:
                return render(request, 'core/partials/cart_error.html', {
                    'message': f'Only {cart_item.spare_part.available_quantity} items available'
                })
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()
            
            context = {
                'success': True,
                'message': 'Cart updated successfully',
                'item_id': item_id,
                'new_quantity': quantity,
                'item_total': cart_item.total_price,
                'cart_total': cart_item.cart.total_amount
            }
        
        return render(request, 'core/partials/cart_update_success.html', context)
        
    except CartItem.DoesNotExist:
        return render(request, 'core/partials/cart_error.html', {
            'message': 'Cart item not found'
        })
    except Exception as e:
        return render(request, 'core/partials/cart_error.html', {
            'message': 'An error occurred while updating cart'
        })


@staff_member_required
@require_http_methods(["GET"])
def admin_spare_parts_table_htmx(request):
    """Admin spare parts table with real-time filtering"""
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '')
    supplier = request.GET.get('supplier', '')
    status = request.GET.get('status', '')
    
    # Base queryset
    spare_parts = SparePart.objects.select_related(
        'vendor', 'supplier', 'category_new'
    )
    
    # Apply filters
    if search:
        spare_parts = spare_parts.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(part_number__icontains=search)
        )
    
    if category:
        spare_parts = spare_parts.filter(category_new_id=category)
    
    if supplier:
        spare_parts = spare_parts.filter(supplier_id=supplier)
    
    if status:
        if status == 'in_stock':
            spare_parts = spare_parts.filter(stock_quantity__gt=10)
        elif status == 'low_stock':
            spare_parts = spare_parts.filter(stock_quantity__lte=10, stock_quantity__gt=0)
        elif status == 'out_of_stock':
            spare_parts = spare_parts.filter(stock_quantity=0)
    
    # Pagination
    paginator = Paginator(spare_parts.order_by('-created_at'), 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'spare_parts': page_obj,
        'total_results': paginator.count,
    }
    
    return render(request, 'core/partials/admin_spare_parts_table.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_update_stock_htmx(request, part_id):
    """Update spare part stock with HTMX"""
    spare_part = get_object_or_404(SparePart, id=part_id)
    
    try:
        movement_type = request.POST.get('movement_type', 'adjustment')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        old_quantity = spare_part.stock_quantity
        
        if movement_type == 'restock':
            spare_part.stock_quantity += quantity
        elif movement_type == 'adjustment':
            spare_part.stock_quantity = quantity
        elif movement_type == 'sale_return':
            spare_part.stock_quantity += quantity
        
        spare_part.save()
        
        # Create stock movement record
        StockMovement.objects.create(
            spare_part=spare_part,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
            created_by=request.user
        )
        
        context = {
            'success': True,
            'message': 'Stock updated successfully',
            'spare_part': spare_part,
            'old_quantity': old_quantity,
            'new_quantity': spare_part.stock_quantity
        }
        
        return render(request, 'core/partials/stock_update_success.html', context)
        
    except Exception as e:
        context = {
            'success': False,
            'message': f'Error updating stock: {str(e)}',
            'spare_part': spare_part
        }
        
        return render(request, 'core/partials/stock_update_error.html', context)


@require_http_methods(["GET"])
def spare_parts_category_filter(request, category_id):
    """Filter spare parts by category with HTMX"""
    category = get_object_or_404(SparePartCategory, id=category_id, is_active=True)
    
    spare_parts = SparePart.objects.filter(
        category_new=category,
        is_available=True
    ).select_related('vendor', 'supplier')
    
    # Pagination
    paginator = Paginator(spare_parts.order_by('-created_at'), 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'spare_parts': page_obj,
        'category': category,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'core/partials/spare_parts_grid.html', context)


@require_http_methods(["GET"])
def spare_parts_stats_htmx(request):
    """Real-time spare parts statistics for dashboard"""
    stats = {
        'total_parts': SparePart.objects.filter(is_available=True).count(),
        'in_stock_parts': SparePart.objects.filter(
            is_available=True, 
            stock_quantity__gt=10
        ).count(),
        'low_stock_parts': SparePart.objects.filter(
            is_available=True,
            stock_quantity__lte=10,
            stock_quantity__gt=0
        ).count(),
        'out_of_stock_parts': SparePart.objects.filter(
            is_available=True,
            stock_quantity=0
        ).count(),
        'total_value': SparePart.objects.filter(
            is_available=True
        ).aggregate(
            total=Sum('stock_quantity') * Sum('cost_price')
        )['total'] or 0
    }
    
    return render(request, 'core/partials/spare_parts_stats.html', {'stats': stats})
