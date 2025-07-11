from django.urls import path
from . import views, dashboard_views

app_name = 'core'

urlpatterns = [
    # Homepage
    path('', views.homepage, name='homepage'),

    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Password Reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('password-reset-done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete, name='password_reset_complete'),

    # Email Verification URLs (Token-based)
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('email-verification-sent/', views.email_verification_sent, name='email_verification_sent'),
    path('email-verification-required/', views.email_verification_required, name='email_verification_required'),

    # Email Verification URLs (Code-based)
    path('verify-email-code/', views.verify_email_with_code, name='verify_email_code'),
    path('request-verification-code/', views.request_verification_code, name='request_verification_code'),

    # Password Reset URLs (Code-based)
    path('password-reset-code/', views.password_reset_with_code, name='password_reset_code'),
    path('request-password-reset-code/', views.request_password_reset_code, name='request_password_reset_code'),

    # Dashboard URLs
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('dashboard/profile/', dashboard_views.user_profile_view, name='profile'),
    path('dashboard/vendor-profile/', dashboard_views.vendor_profile_view, name='vendor_profile'),
    path('dashboard/change-password/', dashboard_views.change_password_view, name='change_password'),
    path('dashboard/orders/', dashboard_views.user_orders_view, name='user_orders'),
    path('dashboard/addresses/', dashboard_views.user_addresses_view, name='user_addresses'),
    path('dashboard/import-requests/', dashboard_views.user_import_requests_view, name='user_import_requests'),
    path('dashboard/inquiries/', dashboard_views.user_inquiries_view, name='user_inquiries'),
    path('dashboard/wishlist/', dashboard_views.user_wishlist_view, name='user_wishlist'),
    path('dashboard/listings/', dashboard_views.user_listings_view, name='user_listings'),
    path('dashboard/settings/', dashboard_views.user_settings_view, name='user_settings'),
    path('dashboard/analytics/', dashboard_views.profile_analytics_view, name='profile_analytics'),

    # Vendor Dashboard URLs
    path('dashboard/vendor/listings/', dashboard_views.vendor_listings_view, name='vendor_listings'),
    path('dashboard/vendor/inquiries/', dashboard_views.vendor_inquiries_view, name='vendor_inquiries'),
    path('dashboard/vendor/analytics/', dashboard_views.vendor_analytics_view, name='vendor_analytics'),
    path('dashboard/vendor/spare-parts/', dashboard_views.vendor_spare_parts_view, name='vendor_spare_parts'),
    path('dashboard/vendor/orders/', dashboard_views.vendor_orders_view, name='vendor_orders'),
    path('dashboard/vendor/settings/', dashboard_views.vendor_settings_view, name='vendor_settings'),

    # Admin Dashboard URLs
    path('dashboard/admin/users/', dashboard_views.admin_users_view, name='admin_users'),
    path('dashboard/admin/users/<int:user_id>/', dashboard_views.admin_user_detail_view, name='admin_user_detail'),
    path('dashboard/admin/vendors/', dashboard_views.admin_vendors_view, name='admin_vendors'),
    path('dashboard/admin/vendors/user/<int:user_id>/', dashboard_views.admin_vendor_user_detail_view, name='admin_vendor_user_detail'),
    path('dashboard/admin/listings/', dashboard_views.admin_listings_view, name='admin_listings'),
    path('dashboard/admin/car/<int:car_id>/', dashboard_views.admin_car_detail_view, name='admin_car_detail'),
    path('dashboard/admin/car/<int:car_id>/edit/', dashboard_views.admin_car_edit_view, name='admin_car_edit'),
    path('dashboard/admin/car/<int:car_id>/feature/', dashboard_views.admin_feature_car, name='admin_feature_car'),
    path('dashboard/admin/car/<int:car_id>/delete/', dashboard_views.admin_car_delete_view, name='admin_car_delete'),
    path('dashboard/admin/analytics/', dashboard_views.admin_analytics_view, name='admin_analytics'),
    path('dashboard/admin/analytics/api/', dashboard_views.promotion_analytics_api, name='promotion_analytics_api'),
    path('dashboard/admin/spare-parts/', dashboard_views.admin_spare_parts_overview, name='admin_spare_parts'),

    # Admin Actions
    path('dashboard/admin/approve-car/<int:car_id>/', dashboard_views.approve_car_listing, name='approve_car'),
    path('dashboard/admin/reject-car/<int:car_id>/', dashboard_views.reject_car_listing, name='reject_car'),
    path('dashboard/admin/approve-vendor/<int:vendor_id>/', dashboard_views.approve_vendor, name='approve_vendor'),
    path('dashboard/admin/disapprove-vendor/<int:vendor_id>/', dashboard_views.disapprove_vendor, name='disapprove_vendor'),
    path('dashboard/admin/suspend-vendor/<int:vendor_id>/', dashboard_views.suspend_vendor, name='suspend_vendor'),

    # Export Functionality
    path('dashboard/admin/export/users/', dashboard_views.export_users_csv, name='export_users'),
    path('dashboard/admin/export/cars/', dashboard_views.export_cars_csv, name='export_cars'),
    path('dashboard/admin/export/vendors/', dashboard_views.export_vendors_csv, name='export_vendors'),
    path('dashboard/admin/export/analytics/', dashboard_views.export_analytics_json, name='export_analytics'),

    # Notification System
    path('dashboard/notifications/', dashboard_views.notifications_view, name='notifications'),
    path('dashboard/notifications/mark-read/<int:notification_id>/', dashboard_views.mark_notification_read, name='mark_notification_read'),
    path('dashboard/notifications/mark-all-read/', dashboard_views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('dashboard/htmx/notifications-count/', dashboard_views.notifications_count_htmx, name='notifications_count_htmx'),
    path('api/notification-badges/', dashboard_views.notification_badges_api, name='notification_badges_api'),

    # Add New Functionality
    path('dashboard/htmx/add-new-modal/', dashboard_views.add_new_modal, name='add_new_modal'),

    # New Admin Pages
    path('dashboard/admin/import-requests/', dashboard_views.admin_import_requests_view, name='admin_import_requests'),
    path('dashboard/admin/spare-shop/', dashboard_views.admin_spare_shop_view, name='admin_spare_shop'),
    path('dashboard/admin/queries/', dashboard_views.admin_queries_view, name='admin_queries'),
    path('dashboard/admin/content-management/', dashboard_views.admin_content_management_view, name='admin_content_management'),
    path('dashboard/admin/system-settings/', dashboard_views.admin_system_settings_view, name='admin_system_settings'),

    # Import Request HTMX Endpoints
    path('dashboard/admin/import-requests/add-modal/', dashboard_views.admin_import_request_add_modal, name='admin_import_request_add_modal'),
    path('dashboard/admin/import-requests/add/', dashboard_views.admin_import_request_add, name='admin_import_request_add'),
    path('dashboard/admin/import-requests/<int:request_id>/view-modal/', dashboard_views.admin_import_request_view_modal, name='admin_import_request_view_modal'),
    path('dashboard/admin/import-requests/<int:request_id>/edit-modal/', dashboard_views.admin_import_request_edit_modal, name='admin_import_request_edit_modal'),
    path('dashboard/admin/import-requests/<int:request_id>/edit/', dashboard_views.admin_import_request_edit, name='admin_import_request_edit'),
    path('dashboard/admin/import-requests/<int:request_id>/delete-modal/', dashboard_views.admin_import_request_delete_modal, name='admin_import_request_delete_modal'),
    path('dashboard/admin/import-requests/<int:request_id>/delete/', dashboard_views.admin_import_request_delete, name='admin_import_request_delete'),
    path('dashboard/admin/import-requests/<int:request_id>/track/', dashboard_views.admin_import_request_track, name='admin_import_request_track'),
    path('dashboard/admin/import-requests/<int:request_id>/status-modal/', dashboard_views.admin_import_request_status_modal, name='admin_import_request_status_modal'),
    path('dashboard/admin/import-requests/<int:request_id>/status-update/', dashboard_views.admin_import_request_status_update, name='admin_import_request_status_update'),

    # Enhanced Import Request Endpoints
    path('dashboard/admin/import-requests/table/', dashboard_views.admin_import_requests_table_partial, name='admin_import_requests_table_partial'),
    path('dashboard/admin/import-requests/export/', dashboard_views.admin_import_requests_export, name='admin_import_requests_export'),
    path('dashboard/admin/import-requests/refresh/', dashboard_views.admin_import_requests_refresh, name='admin_import_requests_refresh'),

    # Tracking Management
    path('dashboard/admin/tracking-management/', dashboard_views.admin_tracking_management_view, name='admin_tracking_management'),
    path('dashboard/admin/tracking-management/table/', dashboard_views.admin_tracking_management_table_partial, name='admin_tracking_management_table_partial'),
    path('dashboard/admin/tracking-management/export/csv/', dashboard_views.admin_tracking_management_export_csv, name='admin_tracking_management_export_csv'),
    path('dashboard/admin/tracking-management/export/excel/', dashboard_views.admin_tracking_management_export_excel, name='admin_tracking_management_export_excel'),
    path('dashboard/admin/tracking/update-status/<int:order_id>/', dashboard_views.update_tracking_status, name='update_tracking_status'),

    # Import Order Management
    path('dashboard/admin/import-order/add-modal/', dashboard_views.admin_import_order_add_modal, name='admin_import_order_add_modal'),
    path('dashboard/admin/import-order/add/', dashboard_views.admin_import_order_add, name='admin_import_order_add'),
    path('dashboard/admin/import-order/<int:order_id>/edit-modal/', dashboard_views.admin_import_order_edit_modal, name='admin_import_order_edit_modal'),
    path('dashboard/admin/import-order/<int:order_id>/edit/', dashboard_views.admin_import_order_edit, name='admin_import_order_edit'),

    # Tracking Management Modal Endpoints
    path('dashboard/admin/tracking/<int:order_id>/status-modal/', dashboard_views.admin_tracking_status_modal, name='admin_tracking_status_modal'),
    path('dashboard/admin/tracking/<int:order_id>/timeline-modal/', dashboard_views.admin_tracking_timeline_modal, name='admin_tracking_timeline_modal'),
    path('dashboard/admin/tracking/<int:order_id>/location-modal/', dashboard_views.admin_tracking_location_modal, name='admin_tracking_location_modal'),
    path('dashboard/admin/tracking/<int:order_id>/details-modal/', dashboard_views.admin_tracking_details_modal, name='admin_tracking_details_modal'),

    # HTMX Endpoints
    path('dashboard/htmx/respond-inquiry/', dashboard_views.respond_to_inquiry, name='respond_to_inquiry'),
    path('dashboard/htmx/update-inquiry-status/', dashboard_views.update_inquiry_status, name='update_inquiry_status'),

    # Lazy Loading Endpoints
    path('dashboard/htmx/vendor-recent-listings/', dashboard_views.vendor_recent_listings_lazy, name='vendor_recent_listings'),
    path('dashboard/htmx/admin-quick-actions/', dashboard_views.admin_quick_actions_lazy, name='admin_quick_actions'),
    path('dashboard/htmx/user-quick-actions/', dashboard_views.user_quick_actions_lazy, name='user_quick_actions'),

    # Car related URLs
    path('cars/', views.CarListView.as_view(), name='car_list'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car_detail'),
    path('sell-car/', views.sell_car, name='sell_car'),

    # Hot Deals URLs
    path('hot-deals/', views.hot_deals_list, name='hot_deals_list'),
    path('hot-deals/<int:deal_id>/', views.hot_deal_detail, name='hot_deal_detail'),
    path('hot-deals/create/', views.create_hot_deal, name='create_hot_deal'),

    # Promotion Pages URLs
    path('featured-cars/', views.featured_cars_by_tier, name='featured_cars_by_tier'),
    path('featured-cars/<str:tier>/', views.featured_cars_by_tier, name='featured_cars_by_tier'),
    path('top-rated/', views.top_rated_vehicles, name='top_rated_vehicles'),
    path('recommendations/', views.smart_recommendations, name='smart_recommendations'),

    # Import/Export URLs
    path('import/', views.import_listings, name='import_listings'),
    path('import/request/', views.import_request, name='import_request'),

    # Import Order Tracking URLs
    path('import/tracking/', views.import_order_tracking_dashboard, name='import_order_tracking'),
    path('import/tracking/<str:order_number>/', views.import_order_detail, name='import_order_detail'),
    path('import/search/', views.chassis_number_search, name='chassis_number_search'),

    # Spare parts
    path('spare-parts/', views.SparePartListView.as_view(), name='spare_parts'),
    path('spare-parts/<int:pk>/', views.SparePartDetailView.as_view(), name='spare_part_detail'),

    # Resources (formerly Blog)
    path('resources/', views.BlogListView.as_view(), name='resources'),
    path('resources/<slug:slug>/', views.BlogDetailView.as_view(), name='resource_detail'),

    # Static pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),

    # Cart and Checkout
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.orders_list_view, name='orders'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),

    # HTMX endpoints
    path('inquiry/create/', views.create_inquiry, name='create_inquiry'),
    path('spare-parts/search/', views.spare_parts_search, name='spare_parts_search'),
    path('spare-parts/autocomplete/', views.spare_parts_autocomplete, name='spare_parts_autocomplete'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # Rating system endpoints
    path('cars/rate/', views.submit_car_rating, name='submit_car_rating'),

    # HTMX endpoints for dynamic interactions
    path('htmx/featured-cars/filter/', views.htmx_featured_cars_filter, name='htmx_featured_cars_filter'),
    path('htmx/hot-deals/refresh/', views.htmx_hot_deals_refresh, name='htmx_hot_deals_refresh'),
    path('htmx/cars/<int:car_id>/rating/', views.htmx_car_rating_form, name='htmx_car_rating_form'),
    path('htmx/analytics/widget/', views.htmx_promotion_analytics_widget, name='htmx_promotion_analytics_widget'),
    path('htmx/countdown/<int:deal_id>/', views.htmx_countdown_timer_update, name='htmx_countdown_timer_update'),
    path('htmx/cars/filter/', views.htmx_car_list_filter, name='htmx_car_list_filter'),

    # Import Order Tracking HTMX endpoints
    path('import/tracking/<str:order_number>/status/', views.import_order_status_update_htmx, name='import_order_status_htmx'),
    path('import/tracking/<str:order_number>/timeline/', views.import_order_timeline_htmx, name='import_order_timeline_htmx'),

    # Admin Sidebar HTMX endpoints for real-time updates
    path('dashboard/htmx/tracking-stats/', views.admin_tracking_stats_htmx, name='admin_tracking_stats_htmx'),
    path('dashboard/htmx/inquiry-stats/', views.admin_inquiry_stats_htmx, name='admin_inquiry_stats_htmx'),
    path('dashboard/htmx/admin-quick-actions/', views.admin_quick_actions_htmx, name='admin_quick_actions_htmx'),

    # Payment callbacks
    path('payments/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),

    # Test 404 page (for development)
    path('404/', views.test_404_view, name='test_404'),

    # Toast system test page (for development)
    path('toast-test/', views.toast_test, name='toast_test'),

    # System test page (for development)
    path('system-test/', views.system_test, name='system_test'),

    # Activity and Audit Logs
    path('dashboard/activity-logs/', dashboard_views.activity_logs_view, name='activity_logs'),
    path('dashboard/admin/activity-logs/', dashboard_views.admin_activity_logs_view, name='admin_activity_logs'),
    path('dashboard/admin/audit-logs/', dashboard_views.admin_audit_logs_view, name='admin_audit_logs'),

    # Notification Management
    path('dashboard/notification-preferences/', dashboard_views.notification_preferences_view, name='notification_preferences'),
    path('dashboard/admin/notification-queue/', dashboard_views.admin_notification_queue_view, name='admin_notification_queue'),
]
