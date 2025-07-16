"""
Enhanced Admin Views for Spare Parts Management
Provides comprehensive CRUD operations and inventory management for administrators
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import csv
from datetime import datetime, timedelta

from .models import (
    SparePart, SparePartCategory, Supplier, PurchaseOrder, PurchaseOrderItem,
    StockMovement, InventoryAlert, Order, OrderItem, Payment, Vendor
)
from .forms import SparePartForm, SupplierForm, PurchaseOrderForm


@staff_member_required
def admin_spare_parts_dashboard(request):
    """Enhanced admin spare parts dashboard with comprehensive analytics"""
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    supplier_filter = request.GET.get('supplier')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    spare_parts = SparePart.objects.select_related('vendor', 'supplier', 'category_new')
    
    # Apply filters
    if category_filter:
        spare_parts = spare_parts.filter(category_new_id=category_filter)
    
    if supplier_filter:
        spare_parts = spare_parts.filter(supplier_id=supplier_filter)
    
    if status_filter:
        if status_filter == 'in_stock':
            spare_parts = spare_parts.filter(stock_quantity__gt=10)
        elif status_filter == 'low_stock':
            spare_parts = spare_parts.filter(stock_quantity__lte=10, stock_quantity__gt=0)
        elif status_filter == 'out_of_stock':
            spare_parts = spare_parts.filter(stock_quantity=0)
    
    if search_query:
        spare_parts = spare_parts.filter(
            Q(name__icontains=search_query) |
            Q(part_number__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Calculate statistics
    total_parts = spare_parts.count()
    in_stock_parts = spare_parts.filter(stock_quantity__gt=10).count()
    low_stock_parts = spare_parts.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    out_of_stock_parts = spare_parts.filter(stock_quantity=0).count()
    
    # Total inventory value
    inventory_value = spare_parts.aggregate(
        total_value=Sum('stock_quantity') * Sum('cost_price')
    )['total_value'] or 0
    
    # Recent orders
    recent_orders = Order.objects.filter(
        items__spare_part__isnull=False
    ).distinct().select_related('customer').order_by('-created_at')[:10]
    
    # Low stock alerts
    low_stock_alerts = spare_parts.filter(
        stock_quantity__lte=F('minimum_stock')
    ).order_by('stock_quantity')[:10]
    
    # Pagination
    paginator = Paginator(spare_parts.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'spare_parts': page_obj,
        'total_parts': total_parts,
        'in_stock_parts': in_stock_parts,
        'low_stock_parts': low_stock_parts,
        'out_of_stock_parts': out_of_stock_parts,
        'inventory_value': inventory_value,
        'recent_orders': recent_orders,
        'low_stock_alerts': low_stock_alerts,
        'categories': SparePartCategory.objects.filter(is_active=True),
        'suppliers': Supplier.objects.filter(is_active=True),
        'current_category': category_filter,
        'current_supplier': supplier_filter,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'core/dashboard/admin_spare_parts_enhanced.html', context)


@staff_member_required
def admin_spare_part_detail(request, part_id):
    """Detailed view of a spare part with full information"""
    spare_part = get_object_or_404(SparePart, id=part_id)
    
    # Get stock movements for this part
    stock_movements = StockMovement.objects.filter(
        spare_part=spare_part
    ).order_by('-created_at')[:20]
    
    # Get recent orders containing this part
    recent_orders = OrderItem.objects.filter(
        spare_part=spare_part
    ).select_related('order', 'order__customer').order_by('-order__created_at')[:10]
    
    # Calculate analytics
    total_sold = OrderItem.objects.filter(spare_part=spare_part).aggregate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    )
    
    context = {
        'spare_part': spare_part,
        'stock_movements': stock_movements,
        'recent_orders': recent_orders,
        'total_sold': total_sold['total_quantity'] or 0,
        'total_revenue': total_sold['total_revenue'] or 0,
    }
    
    return render(request, 'core/dashboard/admin_spare_part_detail.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_spare_part_create(request):
    """Create new spare part via HTMX"""
    if request.method == 'POST':
        form = SparePartForm(request.POST, request.FILES)
        if form.is_valid():
            spare_part = form.save()
            
            # Create initial stock movement
            StockMovement.objects.create(
                spare_part=spare_part,
                movement_type='in',
                reason='initial',
                quantity=spare_part.stock_quantity,
                quantity_before=0,
                quantity_after=spare_part.stock_quantity,
                notes=f'Initial stock for {spare_part.name}',
                created_by=request.user
            )
            
            messages.success(request, f'Spare part "{spare_part.name}" created successfully.')
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': 'Spare part created successfully',
                    'part_id': spare_part.id
                })
            
            return redirect('core:admin_spare_parts_dashboard')
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@staff_member_required
@require_http_methods(["POST"])
def admin_spare_part_update_stock(request, part_id):
    """Update spare part stock levels"""
    spare_part = get_object_or_404(SparePart, id=part_id)
    
    try:
        data = json.loads(request.body)
        movement_type = data.get('movement_type')  # 'restock', 'adjustment', 'sale_return'
        quantity = int(data.get('quantity', 0))
        notes = data.get('notes', '')
        
        if movement_type == 'restock':
            spare_part.stock_quantity += quantity
        elif movement_type == 'adjustment':
            spare_part.stock_quantity = quantity
        elif movement_type == 'sale_return':
            spare_part.stock_quantity += quantity
        
        spare_part.save()
        
        # Create stock movement record
        old_quantity = spare_part.stock_quantity - quantity if movement_type == 'restock' else spare_part.stock_quantity
        new_quantity = spare_part.stock_quantity

        # Map movement types to valid choices
        movement_type_map = {
            'restock': 'in',
            'adjustment': 'adjustment',
            'sale_return': 'in'
        }

        # Map reason based on movement type
        reason_map = {
            'restock': 'purchase',
            'adjustment': 'adjustment',
            'sale_return': 'return'
        }

        StockMovement.objects.create(
            spare_part=spare_part,
            movement_type=movement_type_map.get(movement_type, 'in'),
            reason=reason_map.get(movement_type, 'adjustment'),
            quantity=quantity,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            notes=notes,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Stock updated successfully',
            'new_stock': spare_part.stock_quantity
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating stock: {str(e)}'
        })


@staff_member_required
def admin_spare_parts_export(request):
    """Export spare parts data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="spare_parts_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Name', 'SKU', 'Part Number', 'Category', 'Supplier', 'Stock Quantity',
        'Price', 'Cost Price', 'Vendor', 'Created Date'
    ])
    
    spare_parts = SparePart.objects.select_related(
        'vendor', 'supplier', 'category_new'
    ).all()
    
    for part in spare_parts:
        writer.writerow([
            part.name,
            part.sku,
            part.part_number,
            part.category_new.name if part.category_new else part.category,
            part.supplier.name if part.supplier else '',
            part.stock_quantity,
            part.price,
            part.cost_price or '',
            part.vendor.company_name,
            part.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


@staff_member_required
def admin_suppliers_management(request):
    """Supplier management dashboard"""
    suppliers = Supplier.objects.annotate(
        parts_count=Count('spare_parts'),
        total_value=Sum('spare_parts__stock_quantity') * Sum('spare_parts__cost_price')
    ).order_by('name')
    
    # Pagination
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'suppliers': page_obj,
        'total_suppliers': suppliers.count(),
        'active_suppliers': suppliers.filter(is_active=True).count(),
    }
    
    return render(request, 'core/dashboard/admin_suppliers.html', context)


@staff_member_required
def admin_inventory_alerts(request):
    """Inventory alerts and notifications"""
    # Low stock alerts
    low_stock_parts = SparePart.objects.filter(
        stock_quantity__lte=F('minimum_stock')
    ).select_related('vendor', 'supplier').order_by('stock_quantity')
    
    # Out of stock parts
    out_of_stock_parts = SparePart.objects.filter(
        stock_quantity=0
    ).select_related('vendor', 'supplier').order_by('-updated_at')
    
    # Overstock alerts (optional)
    overstock_parts = SparePart.objects.filter(
        stock_quantity__gte=F('maximum_stock')
    ).select_related('vendor', 'supplier').order_by('-stock_quantity')
    
    context = {
        'low_stock_parts': low_stock_parts,
        'out_of_stock_parts': out_of_stock_parts,
        'overstock_parts': overstock_parts,
    }
    
    return render(request, 'core/dashboard/admin_inventory_alerts.html', context)


@staff_member_required
def admin_spare_parts_analytics(request):
    """Comprehensive analytics for spare parts"""
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Sales analytics
    sales_data = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        spare_part__isnull=False
    ).aggregate(
        total_orders=Count('order', distinct=True),
        total_items_sold=Sum('quantity'),
        total_revenue=Sum('total_price'),
        average_order_value=Avg('total_price')
    )
    
    # Top selling parts
    top_selling_parts = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        spare_part__isnull=False
    ).values(
        'spare_part__name', 'spare_part__id'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:10]
    
    # Category performance
    category_performance = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        spare_part__category_new__isnull=False
    ).values(
        'spare_part__category_new__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')
    
    context = {
        'sales_data': sales_data,
        'top_selling_parts': top_selling_parts,
        'category_performance': category_performance,
        'days': days,
    }
    
    return render(request, 'core/dashboard/admin_spare_parts_analytics.html', context)
