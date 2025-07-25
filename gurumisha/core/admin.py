from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Vendor, CarBrand, CarModel, Car, CarImage,
    ImportRequest, ImportOrder, ImportOrderStatusHistory, ImportOrderDocument,
    SparePart, SparePartCategory, SparePartImage,
    Supplier, PurchaseOrder, PurchaseOrderItem, StockMovement,
    InventoryAlert, Inquiry, Message, MessageRead, MessageSchedule, MessageTarget, MessageAnalytics, MessageTemplate, Testimonial, BlogPost,
    VendorSubscription, FeaturedCarTier, HotDeal, CarRating, PromotionAnalytics,
    ContentCategory, ContentTag, ContentSeries, ContentSeriesItem,
    ContentView, ContentLike, ContentComment, ContentBookmark,
    StaticPage, ContentAnalytics, ContentPerformanceReport, RecentlyViewedCar
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address', 'is_verified')
        }),
    )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'is_approved', 'get_subscription_tier', 'average_rating', 'total_sales', 'created_at')
    list_filter = ('is_approved', 'subscription__tier', 'created_at')
    search_fields = ('company_name', 'user__username', 'user__email')
    actions = ['approve_vendors', 'update_vendor_ratings']

    readonly_fields = ('average_rating', 'total_sales')

    def get_subscription_tier(self, obj):
        return obj.get_subscription_tier().title()
    get_subscription_tier.short_description = 'Subscription Tier'

    def approve_vendors(self, request, queryset):
        queryset.update(is_approved=True)
    approve_vendors.short_description = "Approve selected vendors"

    def update_vendor_ratings(self, request, queryset):
        for vendor in queryset:
            vendor.update_average_rating()
    update_vendor_ratings.short_description = "Update vendor ratings"


@admin.register(VendorSubscription)
class VendorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'tier', 'is_active', 'start_date', 'end_date', 'max_featured_cars', 'max_hot_deals')
    list_filter = ('tier', 'is_active', 'auto_renew', 'start_date')
    search_fields = ('vendor__company_name', 'vendor__user__username')
    actions = ['activate_subscriptions', 'deactivate_subscriptions']

    def activate_subscriptions(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscriptions.short_description = "Activate selected subscriptions"

    def deactivate_subscriptions(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"


@admin.register(FeaturedCarTier)
class FeaturedCarTierAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'priority_order', 'homepage_slots', 'listing_boost_percentage', 'monthly_price', 'is_active')
    list_filter = ('is_active',)
    ordering = ('priority_order',)


@admin.register(HotDeal)
class HotDealAdmin(admin.ModelAdmin):
    list_display = ('title', 'car', 'discount_type', 'discount_value', 'discounted_price', 'start_date', 'end_date', 'is_active')
    list_filter = ('discount_type', 'is_active', 'auto_activate', 'start_date', 'end_date')
    search_fields = ('title', 'car__title', 'car__brand__name')
    actions = ['activate_deals', 'deactivate_deals']

    readonly_fields = ('discounted_price', 'views_count', 'clicks_count', 'inquiries_count')

    def activate_deals(self, request, queryset):
        queryset.update(is_active=True)
    activate_deals.short_description = "Activate selected deals"

    def deactivate_deals(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_deals.short_description = "Deactivate selected deals"


@admin.register(CarRating)
class CarRatingAdmin(admin.ModelAdmin):
    list_display = ('car', 'customer', 'rating', 'is_verified', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified', 'is_approved', 'created_at')
    search_fields = ('car__title', 'customer__username', 'review')
    actions = ['approve_ratings', 'verify_ratings']

    def approve_ratings(self, request, queryset):
        queryset.update(is_approved=True)
    approve_ratings.short_description = "Approve selected ratings"

    def verify_ratings(self, request, queryset):
        queryset.update(is_verified=True)
    verify_ratings.short_description = "Verify selected ratings"


@admin.register(PromotionAnalytics)
class PromotionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('metric_type', 'car', 'vendor', 'metric_value', 'date', 'hour')
    list_filter = ('metric_type', 'date', 'hour')
    search_fields = ('car__title', 'vendor__company_name')
    date_hierarchy = 'date'



@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'is_active')
    list_filter = ('brand', 'is_active')
    search_fields = ('name', 'brand__name')


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 3


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'model', 'year', 'price', 'is_featured', 'is_certified', 'calculated_rating', 'is_approved', 'is_hot_deal', 'views_count', 'created_at')
    list_filter = ('brand', 'status', 'is_approved', 'is_hot_deal', 'is_featured', 'is_certified', 'condition', 'fuel_type', 'auto_featured', 'created_at')
    search_fields = ('title', 'brand__name', 'model__name', 'vendor__company_name')
    inlines = [CarImageInline]
    actions = [
        'approve_cars', 'feature_cars', 'unfeature_cars', 'mark_certified', 'unmark_certified',
        'mark_hot_deals', 'unmark_hot_deals', 'update_ratings', 'bulk_update_ratings'
    ]

    readonly_fields = ('calculated_rating', 'last_rating_update', 'views_count', 'inquiry_count')

    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'title', 'brand', 'model', 'year', 'condition')
        }),
        ('Specifications', {
            'fields': ('engine_size', 'fuel_type', 'transmission', 'mileage', 'body_type', 'color')
        }),
        ('Pricing and Status', {
            'fields': ('price', 'status', 'listing_type', 'negotiable', 'is_approved')
        }),
        ('Promotion System', {
            'fields': ('is_featured', 'featured_until', 'auto_featured', 'is_certified', 'is_hot_deal', 'star_rating', 'calculated_rating', 'last_rating_update'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('views_count', 'inquiry_count'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('description', 'features', 'main_image')
        }),
    )

    def approve_cars(self, request, queryset):
        queryset.update(is_approved=True)
    approve_cars.short_description = "Approve selected cars"

    def feature_bronze(self, request, queryset):
        queryset.update(featured_tier='bronze', auto_featured=False)
    feature_bronze.short_description = "Feature as Bronze"

    def feature_silver(self, request, queryset):
        queryset.update(featured_tier='silver', auto_featured=False)
    feature_silver.short_description = "Feature as Silver"

    def feature_gold(self, request, queryset):
        queryset.update(featured_tier='gold', auto_featured=False)
    feature_gold.short_description = "Feature as Gold"

    def feature_platinum(self, request, queryset):
        queryset.update(featured_tier='platinum', auto_featured=False)
    feature_platinum.short_description = "Feature as Platinum"

    def unfeature_cars(self, request, queryset):
        queryset.update(featured_tier='none', auto_featured=False, featured_until=None)
    unfeature_cars.short_description = "Remove featured status"

    def mark_hot_deals(self, request, queryset):
        queryset.update(is_hot_deal=True)
    mark_hot_deals.short_description = "Mark as Hot Deals"

    def unmark_hot_deals(self, request, queryset):
        queryset.update(is_hot_deal=False)
    unmark_hot_deals.short_description = "Remove Hot Deal status"

    def update_ratings(self, request, queryset):
        for car in queryset:
            car.update_calculated_rating()
    update_ratings.short_description = "Update calculated ratings"

    def bulk_update_ratings(self, request, queryset):
        from django.utils import timezone
        queryset.update(last_rating_update=timezone.now())
        for car in queryset:
            car.calculated_rating = car.calculate_automatic_rating()
            car.save(update_fields=['calculated_rating'])
    bulk_update_ratings.short_description = "Bulk update all ratings"

    def set_3_stars(self, request, queryset):
        queryset.update(star_rating=3)
    set_3_stars.short_description = "Set 3 stars (Standard)"


@admin.register(ImportRequest)
class ImportRequestAdmin(admin.ModelAdmin):
    list_display = ('customer', 'brand', 'model', 'year', 'status', 'estimated_cost', 'created_at')
    list_filter = ('status', 'origin_country', 'created_at')
    search_fields = ('customer__username', 'brand', 'model', 'tracking_number')


class ImportOrderStatusHistoryInline(admin.TabularInline):
    model = ImportOrderStatusHistory
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('previous_status', 'new_status', 'changed_by', 'change_reason', 'estimated_date', 'actual_date', 'customer_notification_sent', 'created_at')


class ImportOrderDocumentInline(admin.TabularInline):
    model = ImportOrderDocument
    extra = 0
    readonly_fields = ('file_size', 'created_at', 'updated_at')
    fields = ('document_type', 'title', 'document_file', 'is_customer_visible', 'is_confidential', 'uploaded_by', 'created_at')


@admin.register(ImportOrder)
class ImportOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'brand', 'model', 'year', 'status',
        'payment_status', 'chassis_number', 'progress_percentage', 'created_at'
    )
    list_filter = (
        'status', 'payment_status', 'origin_country', 'auction_house',
        'arrival_port', 'created_at', 'updated_at'
    )
    search_fields = (
        'order_number', 'customer__username', 'customer__email',
        'brand', 'model', 'chassis_number', 'engine_number',
        'bill_of_lading', 'vessel_name', 'registration_number'
    )
    readonly_fields = ('order_number', 'progress_percentage', 'current_stage_number', 'estimated_days_remaining', 'created_at', 'updated_at')

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'import_request', 'status', 'payment_status')
        }),
        ('Vehicle Details', {
            'fields': ('brand', 'model', 'year', 'color', 'engine_size', 'fuel_type', 'transmission', 'mileage')
        }),
        ('Import Details', {
            'fields': ('origin_country', 'origin_city')
        }),
        ('Financial Information', {
            'fields': ('quotation_amount', 'total_cost', 'paid_amount', 'balance_due')
        }),
        ('Auction Information', {
            'fields': ('auction_house', 'auction_date', 'winning_bid_amount'),
            'classes': ('collapse',)
        }),
        ('Vehicle Identification', {
            'fields': ('chassis_number', 'engine_number')
        }),
        ('Shipping Information', {
            'fields': (
                'bill_of_lading', 'vessel_name', 'departure_port', 'departure_date',
                'arrival_port', 'estimated_arrival_date', 'actual_arrival_date'
            ),
            'classes': ('collapse',)
        }),
        ('Clearance & Registration', {
            'fields': (
                'customs_reference', 'duty_amount', 'duty_paid_date',
                'registration_number', 'registration_date'
            ),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_address', 'delivery_date', 'delivery_contact_person', 'delivery_contact_phone'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('special_requirements', 'admin_notes', 'customer_notes')
        }),
        ('Progress Tracking', {
            'fields': ('progress_percentage', 'current_stage_number', 'estimated_days_remaining'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ImportOrderStatusHistoryInline, ImportOrderDocumentInline]

    def save_model(self, request, obj, form, change):
        """Override save to track status changes"""
        if change:
            # Get the original object to compare status
            original = ImportOrder.objects.get(pk=obj.pk)
            if original.status != obj.status:
                # Create status history entry
                ImportOrderStatusHistory.objects.create(
                    import_order=obj,
                    previous_status=original.status,
                    new_status=obj.status,
                    changed_by=request.user,
                    change_reason=f"Status updated via admin interface"
                )
        super().save_model(request, obj, form, change)


@admin.register(ImportOrderStatusHistory)
class ImportOrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('import_order', 'previous_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'previous_status', 'changed_by', 'customer_notification_sent', 'created_at')
    search_fields = ('import_order__order_number', 'change_reason', 'admin_notes')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Status Change', {
            'fields': ('import_order', 'previous_status', 'new_status', 'changed_by')
        }),
        ('Change Details', {
            'fields': ('change_reason', 'admin_notes', 'customer_notification_sent')
        }),
        ('Dates', {
            'fields': ('estimated_date', 'actual_date', 'created_at')
        }),
    )


@admin.register(ImportOrderDocument)
class ImportOrderDocumentAdmin(admin.ModelAdmin):
    list_display = ('import_order', 'document_type', 'title', 'is_customer_visible', 'is_confidential', 'uploaded_by', 'created_at')
    list_filter = ('document_type', 'is_customer_visible', 'is_confidential', 'uploaded_by', 'created_at')
    search_fields = ('import_order__order_number', 'title', 'description')
    readonly_fields = ('file_size', 'file_size_formatted', 'created_at', 'updated_at')

    fieldsets = (
        ('Document Information', {
            'fields': ('import_order', 'document_type', 'title', 'description')
        }),
        ('File Details', {
            'fields': ('document_file', 'file_size_formatted')
        }),
        ('Access Control', {
            'fields': ('is_customer_visible', 'is_confidential')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(SparePartCategory)
class SparePartCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active', 'rating')
    list_filter = ('is_active', 'rating')
    search_fields = ('name', 'contact_person', 'email')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'email', 'phone', 'address', 'website')
        }),
        ('Business Details', {
            'fields': ('tax_number', 'payment_terms', 'rating')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


class SparePartImageInline(admin.TabularInline):
    model = SparePartImage
    extra = 1


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'vendor', 'category', 'price', 'stock_quantity', 'available_quantity', 'is_low_stock', 'is_available')
    list_filter = ('category', 'condition', 'is_available', 'is_featured', 'is_discontinued', 'vendor', 'supplier')
    search_fields = ('name', 'sku', 'part_number', 'barcode', 'vendor__company_name')
    readonly_fields = ('available_quantity', 'is_low_stock', 'needs_reorder', 'stock_value')
    inlines = [SparePartImageInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'supplier', 'name', 'sku', 'part_number', 'barcode', 'category', 'category_new')
        }),
        ('Compatibility', {
            'fields': ('compatible_brands', 'compatible_models', 'year_from', 'year_to')
        }),
        ('Details', {
            'fields': ('condition', 'description', 'specifications', 'unit', 'weight', 'dimensions')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'price', 'discount_price')
        }),
        ('Inventory Management', {
            'fields': ('stock_quantity', 'reserved_quantity', 'minimum_stock', 'maximum_stock', 'reorder_point', 'reorder_quantity')
        }),
        ('Storage', {
            'fields': ('warehouse_location', 'storage_conditions')
        }),
        ('Status', {
            'fields': ('is_available', 'is_featured', 'is_discontinued')
        }),
        ('Media', {
            'fields': ('main_image',)
        }),
        ('Calculated Fields', {
            'fields': ('available_quantity', 'is_low_stock', 'needs_reorder', 'stock_value'),
            'classes': ('collapse',)
        }),
    )

    def available_quantity(self, obj):
        return obj.available_quantity
    available_quantity.short_description = 'Available Qty'

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'

    def stock_value(self, obj):
        return f"KSh {obj.stock_value:,.2f}"
    stock_value.short_description = 'Stock Value'


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ('total_amount', 'quantity_pending', 'is_fully_received')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'vendor', 'status', 'order_date', 'total_amount')
    list_filter = ('status', 'order_date', 'supplier', 'vendor')
    search_fields = ('order_number', 'supplier__name', 'vendor__company_name')
    readonly_fields = ('subtotal', 'total_amount', 'created_by', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'supplier', 'vendor', 'status')
        }),
        ('Dates', {
            'fields': ('expected_delivery', 'actual_delivery')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_conditions')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('spare_part', 'movement_type', 'reason', 'quantity', 'quantity_after', 'created_by', 'created_at')
    list_filter = ('movement_type', 'reason', 'created_at', 'spare_part__vendor')
    search_fields = ('spare_part__name', 'spare_part__sku', 'reference_number', 'notes')
    readonly_fields = ('created_by', 'created_at')

    fieldsets = (
        ('Movement Details', {
            'fields': ('spare_part', 'movement_type', 'reason', 'quantity')
        }),
        ('Stock Levels', {
            'fields': ('quantity_before', 'quantity_after')
        }),
        ('Reference', {
            'fields': ('reference_number', 'purchase_order_item', 'unit_cost')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ('spare_part', 'alert_type', 'status', 'current_stock', 'threshold_value', 'created_at')
    list_filter = ('alert_type', 'status', 'created_at')
    search_fields = ('spare_part__name', 'spare_part__sku', 'message')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Alert Information', {
            'fields': ('spare_part', 'alert_type', 'status', 'message')
        }),
        ('Stock Details', {
            'fields': ('current_stock', 'threshold_value')
        }),
        ('Actions', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'resolved_by', 'resolved_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('subject', 'customer', 'inquiry_type', 'status', 'created_at')
    list_filter = ('inquiry_type', 'status', 'created_at')
    search_fields = ('subject', 'customer__username', 'message')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'message_type', 'target_audience', 'status', 'priority', 'created_by', 'created_at']
    list_filter = ['status', 'message_type', 'target_audience', 'priority', 'created_at']
    search_fields = ['title', 'content', 'excerpt', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'total_views', 'total_clicks', 'total_dismissals']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'excerpt', 'message_type', 'target_audience', 'priority', 'status')
        }),
        ('Display Settings', {
            'fields': ('show_as_popup', 'show_as_banner', 'show_in_dashboard', 'background_color', 'text_color', 'icon_class')
        }),
        ('Action Button', {
            'fields': ('action_button_text', 'action_button_url', 'action_button_color'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('publication_date', 'expiration_date'),
            'classes': ('collapse',)
        }),
        ('Targeting', {
            'fields': ('min_user_age_days', 'max_user_age_days', 'require_email_verified', 'max_displays_per_user', 'display_frequency_hours'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('total_views', 'total_clicks', 'total_dismissals'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'action', 'display_count', 'first_seen_at', 'last_seen_at']
    list_filter = ['action', 'first_seen_at', 'last_seen_at']
    search_fields = ['message__title', 'user__username']
    readonly_fields = ['first_seen_at', 'last_seen_at', 'action_taken_at']


@admin.register(MessageSchedule)
class MessageScheduleAdmin(admin.ModelAdmin):
    list_display = ['message', 'frequency', 'is_active', 'occurrences_sent', 'next_send_at']
    list_filter = ['frequency', 'is_active', 'next_send_at']
    search_fields = ['message__title']
    readonly_fields = ['occurrences_sent', 'last_sent_at', 'next_send_at', 'created_at', 'updated_at']


@admin.register(MessageTarget)
class MessageTargetAdmin(admin.ModelAdmin):
    list_display = ['message', 'field_name', 'condition', 'value', 'is_required']
    list_filter = ['field_name', 'condition', 'is_required']
    search_fields = ['message__title', 'value']


@admin.register(MessageAnalytics)
class MessageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['message', 'date', 'total_displays', 'total_clicks', 'click_through_rate', 'total_dismissals']
    list_filter = ['date', 'message__message_type']
    search_fields = ['message__title']
    readonly_fields = ['click_through_rate', 'dismissal_rate', 'created_at', 'updated_at']

    def click_through_rate(self, obj):
        return f"{obj.click_through_rate:.1f}%"
    click_through_rate.short_description = "CTR"


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_message_type', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'default_message_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'title_template', 'content_template']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('customer', 'rating', 'is_featured', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_featured', 'is_approved', 'created_at')
    search_fields = ('customer__username', 'content')
    actions = ['approve_testimonials', 'feature_testimonials']

    def approve_testimonials(self, request, queryset):
        queryset.update(is_approved=True)
    approve_testimonials.short_description = "Approve selected testimonials"

    def feature_testimonials(self, request, queryset):
        queryset.update(is_featured=True)
    feature_testimonials.short_description = "Feature selected testimonials"


# Enhanced Content Management Admin

@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')
    list_editable = ('sort_order', 'is_active')


@admin.register(ContentTag)
class ContentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('color', 'is_active')


class ContentSeriesItemInline(admin.TabularInline):
    model = ContentSeriesItem
    extra = 0
    ordering = ('order',)


@admin.register(ContentSeries)
class ContentSeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ContentSeriesItemInline]
    list_editable = ('sort_order', 'is_active')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'content_type', 'category', 'is_published', 'is_featured', 'views_count', 'published_at', 'created_at')
    list_filter = ('content_type', 'category', 'is_published', 'is_featured', 'difficulty_level', 'published_at', 'created_at')
    search_fields = ('title', 'content', 'excerpt', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('views_count', 'likes_count', 'shares_count')
    list_editable = ('is_published', 'is_featured')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'content_type', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'difficulty_level', 'estimated_read_time')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt', 'video_url'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('Metrics', {
            'fields': ('views_count', 'likes_count', 'shares_count'),
            'classes': ('collapse',)
        }),
    )

    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']

    def publish_posts(self, request, queryset):
        queryset.update(is_published=True, published_at=timezone.now())
    publish_posts.short_description = "Publish selected posts"

    def unpublish_posts(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_posts.short_description = "Unpublish selected posts"

    def feature_posts(self, request, queryset):
        queryset.update(is_featured=True)
    feature_posts.short_description = "Feature selected posts"

    def unfeature_posts(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature_posts.short_description = "Unfeature selected posts"


@admin.register(ContentView)
class ContentViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'post__content_type')
    search_fields = ('post__title', 'user__username', 'ip_address')
    readonly_fields = ('post', 'user', 'ip_address', 'user_agent', 'referrer', 'viewed_at')

    def has_add_permission(self, request):
        return False


@admin.register(ContentLike)
class ContentLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at', 'post__content_type')
    search_fields = ('post__title', 'user__username')
    readonly_fields = ('post', 'user', 'created_at')


@admin.register(ContentComment)
class ContentCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'post__content_type')
    search_fields = ('post__title', 'user__username', 'content')
    list_editable = ('is_approved',)
    actions = ['approve_comments', 'disapprove_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_comments.short_description = "Disapprove selected comments"


@admin.register(ContentBookmark)
class ContentBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at', 'post__content_type')
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('user', 'post', 'created_at')


# Static Pages Admin

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'page_type', 'status', 'show_in_menu', 'menu_order', 'is_featured', 'views_count', 'updated_at')
    list_filter = ('page_type', 'status', 'show_in_menu', 'is_featured', 'created_at')
    search_fields = ('title', 'content', 'meta_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'show_in_menu', 'menu_order', 'is_featured')
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'published_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type', 'status', 'author')
        }),
        ('Content', {
            'fields': ('content', 'excerpt')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'show_in_menu', 'menu_order')
        }),
        ('Analytics', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.author = request.user
        super().save_model(request, obj, form, change)


# Content Analytics Admin

@admin.register(ContentAnalytics)
class ContentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('post', 'date', 'views', 'unique_views', 'likes', 'shares', 'comments', 'bounce_rate')
    list_filter = ('date', 'post__category', 'post__content_type')
    search_fields = ('post__title',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('post', 'date')
        }),
        ('Engagement Metrics', {
            'fields': ('views', 'unique_views', 'likes', 'shares', 'comments', 'bookmarks')
        }),
        ('Performance Metrics', {
            'fields': ('avg_time_on_page', 'bounce_rate')
        }),
        ('Traffic Sources', {
            'fields': ('direct_traffic', 'search_traffic', 'social_traffic', 'referral_traffic'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContentPerformanceReport)
class ContentPerformanceReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'start_date', 'end_date', 'is_generated', 'generated_at')
    list_filter = ('report_type', 'is_generated', 'start_date', 'end_date')
    search_fields = ('title',)
    readonly_fields = ('is_generated', 'generated_at', 'generated_by', 'created_at')

    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'report_type', 'start_date', 'end_date')
        }),
        ('Summary Metrics', {
            'fields': ('total_views', 'total_unique_views', 'total_engagement'),
            'classes': ('collapse',)
        }),
        ('Report Data', {
            'fields': ('top_performing_posts', 'report_data'),
            'classes': ('collapse',)
        }),
        ('Generation Status', {
            'fields': ('is_generated', 'generated_at', 'generated_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RecentlyViewedCar)
class RecentlyViewedCarAdmin(admin.ModelAdmin):
    list_display = ['user', 'car', 'viewed_at', 'session_key']
    list_filter = ['viewed_at', 'car__brand']
    search_fields = ['user__username', 'car__title', 'car__brand__name']
    readonly_fields = ['viewed_at']
    ordering = ['-viewed_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'car', 'car__brand')