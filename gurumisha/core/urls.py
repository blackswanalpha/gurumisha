from django.urls import path
from . import views, dashboard_views, resource_views

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
    path('dashboard/import-requests/<int:request_id>/', dashboard_views.customer_import_request_detail_view, name='customer_import_request_detail'),
    path('dashboard/import-requests/<int:request_id>/edit/', dashboard_views.customer_import_request_edit_view, name='customer_import_request_edit'),
    path('dashboard/inquiries/', dashboard_views.user_inquiries_view, name='user_inquiries'),
    path('dashboard/wishlist/', dashboard_views.user_wishlist_view, name='user_wishlist'),
    path('dashboard/listings/', dashboard_views.user_listings_view, name='user_listings'),
    path('dashboard/settings/', dashboard_views.user_settings_view, name='user_settings'),
    path('dashboard/analytics/', dashboard_views.profile_analytics_view, name='profile_analytics'),

    # Vendor Dashboard URLs
    path('dashboard/vendor/listings/', dashboard_views.vendor_listings_view, name='vendor_listings'),
    path('dashboard/vendor/car/view/<int:car_id>/', dashboard_views.vendor_car_view, name='vendor_car_view'),
    path('dashboard/vendor/car/edit/<int:car_id>/', dashboard_views.vendor_car_edit, name='vendor_car_edit'),
    path('dashboard/vendor/car/delete/<int:car_id>/', dashboard_views.vendor_car_delete, name='vendor_car_delete'),
    path('dashboard/vendor/car/duplicate/<int:car_id>/', dashboard_views.vendor_car_duplicate, name='vendor_car_duplicate'),
    path('dashboard/vendor/car/toggle-status/<int:car_id>/', dashboard_views.vendor_car_toggle_status, name='vendor_car_toggle_status'),
    path('dashboard/vendor/car/toggle-feature/<int:car_id>/', dashboard_views.vendor_car_feature_toggle, name='vendor_car_feature_toggle'),
    path('dashboard/vendor/bulk-actions/', dashboard_views.vendor_bulk_actions, name='vendor_bulk_actions'),
    path('dashboard/vendor/export-listings/', dashboard_views.vendor_export_listings, name='vendor_export_listings'),
    path('dashboard/vendor/inquiries/', dashboard_views.vendor_inquiries_view, name='vendor_inquiries'),
    path('dashboard/vendor/analytics/', dashboard_views.vendor_analytics_view, name='vendor_analytics'),
    path('dashboard/vendor/spare-parts/', dashboard_views.vendor_spare_parts_view, name='vendor_spare_parts'),
    path('dashboard/vendor/spare-parts/add/', dashboard_views.vendor_spare_part_add, name='vendor_spare_part_add'),
    path('dashboard/vendor/spare-parts/edit/<int:part_id>/', dashboard_views.vendor_spare_part_edit, name='vendor_spare_part_edit'),
    path('dashboard/vendor/spare-parts/view/<int:part_id>/', dashboard_views.vendor_spare_part_view, name='vendor_spare_part_view'),
    path('dashboard/vendor/spare-parts/delete/<int:part_id>/', dashboard_views.vendor_spare_part_delete, name='vendor_spare_part_delete'),

    # Vendor Spare Parts HTMX endpoints
    path('dashboard/vendor/spare-parts/table-htmx/', dashboard_views.vendor_spare_parts_table_htmx, name='vendor_spare_parts_table_htmx'),
    path('dashboard/vendor/spare-parts/search-htmx/', dashboard_views.vendor_spare_parts_search_htmx, name='vendor_spare_parts_search_htmx'),
    path('dashboard/vendor/spare-parts/stats-htmx/', dashboard_views.vendor_spare_parts_stats_htmx, name='vendor_spare_parts_stats_htmx'),

    path('dashboard/vendor/orders/', dashboard_views.vendor_orders_view, name='vendor_orders'),
    path('dashboard/vendor/import-requests/', dashboard_views.vendor_import_requests_view, name='vendor_import_requests'),
    path('dashboard/vendor/import-requests/<int:request_id>/', dashboard_views.vendor_import_request_detail_view, name='vendor_import_request_detail'),
    path('dashboard/vendor/settings/', dashboard_views.vendor_settings_view, name='vendor_settings'),

    # Admin Dashboard URLs
    path('dashboard/admin/users/', dashboard_views.admin_users_view, name='admin_users'),
    path('dashboard/admin/users/search/', dashboard_views.admin_users_search, name='admin_users_search'),
    path('dashboard/admin/users/refresh/', dashboard_views.admin_users_refresh, name='admin_users_refresh'),
    path('dashboard/admin/users/<int:user_id>/', dashboard_views.admin_user_detail_view, name='admin_user_detail'),
    path('dashboard/admin/users/<int:user_id>/delete/', dashboard_views.admin_user_delete_view, name='admin_user_delete'),
    path('dashboard/admin/users/<int:user_id>/edit-modal/', dashboard_views.admin_user_edit_modal_view, name='admin_user_edit_modal'),
    path('dashboard/admin/vendors/', dashboard_views.admin_vendors_view, name='admin_vendors'),
    path('dashboard/admin/vendors/user/<int:user_id>/', dashboard_views.admin_vendor_user_detail_view, name='admin_vendor_user_detail'),
    path('dashboard/admin/listings/', dashboard_views.admin_listings_view, name='admin_listings'),
    path('dashboard/admin/car/<int:car_id>/', dashboard_views.admin_car_detail_view, name='admin_car_detail'),
    path('dashboard/admin/car/<int:car_id>/edit/', dashboard_views.admin_car_edit_view, name='admin_car_edit'),
    path('dashboard/admin/car/<int:car_id>/feature/', dashboard_views.admin_feature_car, name='admin_feature_car'),
    path('dashboard/admin/car/<int:car_id>/hot-deal/', dashboard_views.admin_hot_deal_management, name='admin_hot_deal_management'),
    path('dashboard/admin/car/<int:car_id>/delete/', dashboard_views.admin_car_delete_view, name='admin_car_delete'),

    # Enhanced Image Gallery Management URLs
    path('car/<int:car_id>/images/upload/', dashboard_views.car_image_upload, name='car_image_upload'),
    path('car/<int:car_id>/images/<int:image_id>/delete/', dashboard_views.car_image_delete, name='car_image_delete'),
    path('car/<int:car_id>/images/<int:image_id>/set-primary/', dashboard_views.car_image_set_primary, name='car_image_set_primary'),
    path('car/<int:car_id>/images/reorder/', dashboard_views.car_image_reorder, name='car_image_reorder'),
    path('dashboard/admin/analytics/', dashboard_views.admin_analytics_view, name='admin_analytics'),
    path('dashboard/admin/analytics/api/', dashboard_views.promotion_analytics_api, name='promotion_analytics_api'),
    path('dashboard/admin/spare-parts/', dashboard_views.admin_spare_parts_overview, name='admin_spare_parts'),

    # Enhanced Admin Resource Management URLs
    path('dashboard/admin/resources/', resource_views.admin_resource_management, name='admin_resource_management'),
    path('dashboard/admin/resources/create/', resource_views.admin_resource_create, name='admin_resource_create'),
    path('dashboard/admin/resources/<int:post_id>/edit/', resource_views.admin_resource_edit, name='admin_resource_edit'),
    path('dashboard/admin/resources/<int:post_id>/update/', resource_views.admin_resource_update, name='admin_resource_update'),
    path('dashboard/admin/resources/<int:post_id>/delete/', resource_views.admin_resource_delete, name='admin_resource_delete'),
    path('dashboard/admin/resources/table/', resource_views.admin_resources_table, name='admin_resources_table'),
    path('dashboard/admin/resources/analytics/', resource_views.admin_analytics_dashboard, name='admin_analytics_dashboard'),

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

    # Enhanced Admin Query Management URLs
    path('dashboard/admin/queries/<int:inquiry_id>/', dashboard_views.admin_query_detail_view, name='admin_query_detail'),
    path('dashboard/admin/queries/<int:inquiry_id>/reply/', dashboard_views.admin_query_reply, name='admin_query_reply'),
    path('dashboard/admin/queries/<int:inquiry_id>/status/', dashboard_views.admin_query_status_update, name='admin_query_status_update'),
    path('dashboard/admin/queries/<int:inquiry_id>/assign/', dashboard_views.admin_query_assign, name='admin_query_assign'),
    path('dashboard/admin/queries/bulk-actions/', dashboard_views.admin_query_bulk_actions, name='admin_query_bulk_actions'),

    # Enhanced Content Management HTMX Endpoints
    path('dashboard/admin/content/posts-tab/', dashboard_views.admin_content_posts_tab, name='admin_content_posts_tab'),
    path('dashboard/admin/content/categories-tab/', dashboard_views.admin_content_categories_tab, name='admin_content_categories_tab'),
    path('dashboard/admin/content/testimonials-tab/', dashboard_views.admin_content_testimonials_tab, name='admin_content_testimonials_tab'),
    path('dashboard/admin/content/static-pages-tab/', dashboard_views.admin_content_static_pages_tab, name='admin_content_static_pages_tab'),
    path('dashboard/admin/content/analytics-tab/', dashboard_views.admin_content_analytics_tab, name='admin_content_analytics_tab'),

    # Content CRUD Operations
    path('dashboard/admin/content/create-modal/', dashboard_views.admin_content_create_modal, name='admin_content_create_modal'),
    path('dashboard/admin/content/create/', dashboard_views.admin_content_create, name='admin_content_create'),

    # Spare Parts Modal HTMX Endpoints
    path('dashboard/admin/spare-parts/add-modal/', dashboard_views.admin_spare_part_add_modal_view, name='admin_spare_part_add_modal'),
    path('dashboard/admin/spare-parts/add/', dashboard_views.admin_spare_part_add_view, name='admin_spare_part_add'),
    path('dashboard/admin/spare-parts/edit/<int:part_id>/modal/', dashboard_views.admin_spare_part_edit_modal_view, name='admin_spare_part_edit_modal'),
    path('dashboard/admin/spare-parts/edit/<int:part_id>/', dashboard_views.admin_spare_part_edit_view, name='admin_spare_part_edit'),
    path('dashboard/admin/spare-parts/restock/<int:part_id>/modal/', dashboard_views.admin_spare_part_restock_modal_view, name='admin_spare_part_restock_modal'),
    path('dashboard/admin/spare-parts/restock/<int:part_id>/', dashboard_views.admin_spare_part_restock_view, name='admin_spare_part_restock'),
    path('dashboard/admin/spare-parts/view/<int:part_id>/modal/', dashboard_views.admin_spare_part_view_modal_view, name='admin_spare_part_view_modal'),
    path('dashboard/admin/spare-parts/delete/<int:part_id>/', dashboard_views.admin_spare_part_delete_view, name='admin_spare_part_delete'),

    # Sales and Order Management Pages
    path('dashboard/admin/sales-management/', dashboard_views.admin_sales_management_view, name='admin_sales_management'),
    path('dashboard/admin/order-management/', dashboard_views.admin_order_management_view, name='admin_order_management'),
    path('dashboard/admin/spare-shop/mpesa-config-modal/', dashboard_views.admin_mpesa_config_modal_view, name='admin_mpesa_config_modal'),

    # Admin Spare Shop Statistics HTMX Endpoints
    path('dashboard/admin/spare-shop/stats/total/', dashboard_views.admin_spare_shop_stats_total, name='admin_spare_shop_stats_total'),
    path('dashboard/admin/spare-shop/stats/in-stock/', dashboard_views.admin_spare_shop_stats_in_stock, name='admin_spare_shop_stats_in_stock'),
    path('dashboard/admin/spare-shop/stats/out-of-stock/', dashboard_views.admin_spare_shop_stats_out_of_stock, name='admin_spare_shop_stats_out_of_stock'),
    path('dashboard/admin/spare-shop/stats/low-stock/', dashboard_views.admin_spare_shop_stats_low_stock, name='admin_spare_shop_stats_low_stock'),

    # Resource Management URLs
    path('dashboard/admin/resource-management/', dashboard_views.admin_resource_management_view, name='admin_resource_management'),

    # Resource Management Tab URLs
    path('dashboard/admin/resource-management/all-content/', dashboard_views.admin_resource_all_content_tab, name='admin_resource_all_content_tab'),
    path('dashboard/admin/resource-management/articles/', dashboard_views.admin_resource_articles_tab, name='admin_resource_articles_tab'),
    path('dashboard/admin/resource-management/guides/', dashboard_views.admin_resource_guides_tab, name='admin_resource_guides_tab'),
    path('dashboard/admin/resource-management/infographics/', dashboard_views.admin_resource_infographics_tab, name='admin_resource_infographics_tab'),
    path('dashboard/admin/resource-management/opinions/', dashboard_views.admin_resource_opinions_tab, name='admin_resource_opinions_tab'),
    path('dashboard/admin/resource-management/news/', dashboard_views.admin_resource_news_tab, name='admin_resource_news_tab'),
    path('dashboard/admin/resource-management/statistics/', dashboard_views.admin_resource_statistics, name='admin_resource_statistics'),
    path('dashboard/admin/resource-management/export/', dashboard_views.admin_resource_export, name='admin_resource_export'),

    # Resource CRUD URLs
    path('dashboard/admin/resource-management/create-modal/', dashboard_views.admin_resource_create_modal, name='admin_resource_create_modal'),
    path('dashboard/admin/resource-management/create/', dashboard_views.admin_resource_create, name='admin_resource_create'),
    path('dashboard/admin/resource-management/<int:post_id>/edit-modal/', dashboard_views.admin_resource_edit_modal, name='admin_resource_edit_modal'),
    path('dashboard/admin/resource-management/<int:post_id>/edit/', dashboard_views.admin_resource_edit, name='admin_resource_edit'),
    path('dashboard/admin/resource-management/<int:post_id>/delete/', dashboard_views.admin_resource_delete, name='admin_resource_delete'),
    path('dashboard/admin/resource-management/<int:post_id>/toggle-publish/', dashboard_views.admin_resource_toggle_publish, name='admin_resource_toggle_publish'),
    path('dashboard/admin/resource-management/<int:post_id>/toggle-featured/', dashboard_views.admin_resource_toggle_featured, name='admin_resource_toggle_featured'),
    path('dashboard/admin/resource-management/<int:post_id>/toggle-published/', dashboard_views.admin_resource_toggle_published, name='admin_resource_toggle_published'),
    path('dashboard/admin/resource-management/search/', dashboard_views.admin_resource_search, name='admin_resource_search'),

    # Message Management URLs
    path('dashboard/admin/message-management/', dashboard_views.admin_message_management_view, name='admin_message_management'),
    path('dashboard/admin/message-management/list/', dashboard_views.admin_message_list_tab, name='admin_message_list_tab'),
    path('dashboard/admin/message-management/create/', dashboard_views.admin_message_create_modal, name='admin_message_create_modal'),
    path('dashboard/admin/message-management/create/submit/', dashboard_views.admin_message_create, name='admin_message_create'),
    path('dashboard/admin/message-management/edit/<int:message_id>/', dashboard_views.admin_message_edit_modal, name='admin_message_edit_modal'),
    path('dashboard/admin/message-management/edit/<int:message_id>/submit/', dashboard_views.admin_message_edit, name='admin_message_edit'),
    path('dashboard/admin/message-management/delete/<int:message_id>/', dashboard_views.admin_message_delete, name='admin_message_delete'),
    path('dashboard/admin/message-management/preview/<int:message_id>/', dashboard_views.admin_message_preview_modal, name='admin_message_preview_modal'),
    path('dashboard/admin/message-management/search/', dashboard_views.admin_message_search, name='admin_message_search'),
    path('dashboard/admin/message-management/analytics/', dashboard_views.admin_message_analytics_tab, name='admin_message_analytics_tab'),
    path('dashboard/admin/message-management/count/', dashboard_views.admin_message_count_htmx, name='admin_message_count_htmx'),
    path('dashboard/admin/message-management/schedule/<int:message_id>/', dashboard_views.admin_message_schedule_modal, name='admin_message_schedule_modal'),
    path('dashboard/admin/message-management/schedule/<int:message_id>/save/', dashboard_views.admin_message_schedule_save, name='admin_message_schedule_save'),
    path('dashboard/admin/message-management/targeting/<int:message_id>/', dashboard_views.admin_message_targeting_modal, name='admin_message_targeting_modal'),
    path('dashboard/admin/message-management/performance/<int:message_id>/', dashboard_views.admin_message_performance_modal, name='admin_message_performance_modal'),

    # Frontend Message Display URLs
    path('messages/popup/', dashboard_views.user_messages_popup, name='user_messages_popup'),
    path('messages/action/<int:message_id>/', dashboard_views.user_message_action, name='user_message_action'),
    path('messages/dashboard/', dashboard_views.user_dashboard_messages, name='user_dashboard_messages'),

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
    path('explore/', views.CarExploreView.as_view(), name='car_explore'),
    path('cars/<int:pk>/', views.CarDetailView.as_view(), name='car_detail'),
    path('sell-car/', views.sell_car, name='sell_car'),

    # Enhanced Image Upload URLs for Car Selling
    path('api/preview-car-images/', views.preview_car_images, name='preview_car_images'),
    path('api/validate-car-image/', views.validate_car_image_upload, name='validate_car_image'),

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
    path('import/tracking/dashboard/', views.import_order_tracking_dashboard, name='import_tracking_dashboard'),
    path('import/tracking/<str:order_number>/', views.import_order_detail, name='import_order_detail'),
    path('import/search/', views.chassis_number_search, name='chassis_number_search'),

    # Spare parts
    path('spare-parts/', views.SparePartListView.as_view(), name='spare_parts'),
    path('spare-parts/<int:pk>/', views.SparePartDetailView.as_view(), name='spare_part_detail'),

    # Resources (formerly Blog)
    path('resources/', views.BlogListView.as_view(), name='resources'),

    # HTMX endpoints for resources (must come before slug pattern)
    path('resources/search/', views.resources_live_search, name='resources_live_search'),
    path('resources/category/<slug:category_slug>/', resource_views.resources_by_category, name='resources_by_category'),
    path('resources/tag/<slug:tag_slug>/', views.resources_filter_by_tag, name='resources_filter_by_tag'),

    # Resource detail (must come after specific patterns)
    path('resources/<slug:slug>/', views.BlogDetailView.as_view(), name='resource_detail'),

    # Enhanced Navigation and Interaction URLs
    path('search/global/', resource_views.global_search, name='global_search'),
    path('search/mobile/', resource_views.mobile_search, name='mobile_search'),
    path('content/like/<int:post_id>/', resource_views.content_like_toggle, name='content_like_toggle'),
    path('content/bookmark/<int:post_id>/', resource_views.content_bookmark_toggle, name='content_bookmark_toggle'),
    path('content/track-engagement/', resource_views.track_engagement, name='track_engagement'),
    path('content/recommendations/<int:post_id>/', resource_views.get_recommendations, name='get_recommendations'),

    # Opinion polling endpoints
    path('poll/vote/<int:poll_id>/', views.poll_vote, name='poll_vote'),
    path('opinion/review/<int:post_id>/', views.opinion_review_submit, name='opinion_review_submit'),
    path('review/helpful/<int:review_id>/', views.review_helpful_vote, name='review_helpful_vote'),

    # PDF management endpoints
    path('guide/pdf/download/<int:post_id>/', views.guide_pdf_download, name='guide_pdf_download'),
    path('guide/pdf/view/<int:post_id>/', views.guide_pdf_viewer, name='guide_pdf_viewer'),
    path('guide/pdf/info/<int:post_id>/', views.guide_pdf_info, name='guide_pdf_info'),

    # Infographic chart endpoints
    path('infographic/chart/data/<int:post_id>/', views.infographic_chart_data, name='infographic_chart_data'),
    path('infographic/chart/update/<int:post_id>/', views.infographic_chart_update, name='infographic_chart_update'),
    path('infographic/chart/preview/<int:post_id>/', views.infographic_chart_preview, name='infographic_chart_preview'),

    # Analytics and Data Endpoints
    path('analytics/data/', resource_views.analytics_data, name='analytics_data'),
    path('analytics/top-content/', resource_views.top_content_data, name='top_content_data'),
    path('analytics/export/', resource_views.export_analytics, name='export_analytics'),

    # Comment System URLs
    path('comments/add/<int:post_id>/', resource_views.add_comment, name='add_comment'),
    path('comments/sorted/<int:post_id>/', resource_views.get_sorted_comments, name='get_sorted_comments'),
    path('comments/load-more/<int:post_id>/', resource_views.load_more_comments, name='load_more_comments'),

    # Debug endpoints
    path('debug/messages/', views.message_debug_view, name='message_debug'),

    # Static pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('customer-service/', views.customer_service, name='customer_service'),
    path('help-center/', views.help_center, name='help_center'),
    path('faqs/', views.faqs, name='faqs'),
    path('payment-options/', views.payment_options, name='payment_options'),
    path('shipping-info/', views.shipping_info, name='shipping_info'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('contact-support/', views.contact_support, name='contact_support'),

    # Public Dealer Profile URLs
    path('dealers/', views.dealer_list, name='dealer_list'),
    path('dealers/<int:vendor_id>/', views.dealer_profile, name='dealer_profile'),

    # Car Comparison URLs
    path('compare/', views.car_compare, name='car_compare'),
    path('compare/add/<int:car_id>/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/<int:car_id>/', views.remove_from_compare, name='remove_from_compare'),
    path('compare/clear/', views.clear_compare, name='clear_compare'),

    # Wishlist URLs
    path('wishlist/add/<int:car_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:car_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/check/<int:car_id>/', views.check_wishlist_status, name='check_wishlist_status'),

    # Car Calculator URLs
    path('calculator/', views.car_calculator, name='car_calculator'),
    path('calculator/calculate/', views.calculate_loan, name='calculate_loan'),

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
    path('htmx/models-by-brand/', views.htmx_models_by_brand, name='htmx_models_by_brand'),
    path('htmx/cars/filter-body-type/', views.htmx_filter_by_body_type, name='htmx_filter_by_body_type'),
    path('htmx/recently-viewed/update/', views.htmx_recently_viewed_update, name='htmx_recently_viewed_update'),

    # Import Order Tracking HTMX endpoints
    path('import/tracking/<str:order_number>/status/', views.import_order_status_update_htmx, name='import_order_status_htmx'),
    path('import/tracking/<str:order_number>/timeline/', views.import_order_timeline_htmx, name='import_order_timeline_htmx'),

    # GPS Tracking HTMX endpoints
    path('import/tracking/<str:order_number>/location/', views.import_order_location_update_htmx, name='import_order_location_htmx'),
    path('import/tracking/<str:order_number>/route/', views.import_order_route_data_htmx, name='import_order_route_htmx'),
    path('import/tracking/<str:order_number>/live/', views.import_order_live_tracking_htmx, name='import_order_live_tracking_htmx'),
    path('import/tracking/<str:order_number>/history/', views.import_order_location_history_htmx, name='import_order_location_history_htmx'),
    path('import/tracking/dashboard/live/', views.import_order_tracking_dashboard_htmx, name='import_tracking_dashboard_htmx'),
    path('import/tracking/<str:order_number>/sse/', views.import_order_sse_tracking, name='import_order_sse_tracking'),
    path('import/tracking/notifications/', views.import_order_tracking_notifications_htmx, name='import_tracking_notifications_htmx'),

    # Admin GPS Tracking Management
    path('dashboard/admin/gps-tracking/', dashboard_views.admin_gps_tracking_management, name='admin_gps_tracking'),
    path('dashboard/admin/tracking/order/<int:order_id>/location-modal/', dashboard_views.admin_location_management_modal, name='admin_location_management_modal'),
    path('dashboard/admin/tracking/order/<int:order_id>/update-location/', dashboard_views.admin_update_order_location, name='admin_update_order_location'),
    path('dashboard/admin/tracking/order/<int:order_id>/create-route/', dashboard_views.admin_create_route, name='admin_create_route'),
    path('dashboard/admin/tracking/order/<int:order_id>/add-waypoint/', dashboard_views.admin_add_waypoint, name='admin_add_waypoint'),

    # Admin Sidebar HTMX endpoints for real-time updates
    path('dashboard/htmx/tracking-stats/', views.admin_tracking_stats_htmx, name='admin_tracking_stats_htmx'),
    path('dashboard/htmx/inquiry-stats/', views.admin_inquiry_stats_htmx, name='admin_inquiry_stats_htmx'),
    path('dashboard/htmx/admin-quick-actions/', dashboard_views.admin_quick_actions_lazy, name='admin_quick_actions_htmx'),

    # Admin Query Management HTMX Endpoints
    path('dashboard/admin/queries/table-htmx/', dashboard_views.admin_queries_table_htmx, name='admin_queries_table_htmx'),
    path('dashboard/admin/queries/search-htmx/', dashboard_views.admin_queries_search_htmx, name='admin_queries_search_htmx'),
    path('dashboard/admin/queries/stats-htmx/', dashboard_views.admin_queries_stats_htmx, name='admin_queries_stats_htmx'),
    path('dashboard/admin/queries/<int:inquiry_id>/quick-reply-htmx/', dashboard_views.admin_query_quick_reply_htmx, name='admin_query_quick_reply_htmx'),
    path('dashboard/admin/queries/<int:inquiry_id>/status-htmx/', dashboard_views.admin_query_status_htmx, name='admin_query_status_htmx'),

    # Payment callbacks
    path('payments/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('payments/mpesa/timeout/', views.mpesa_timeout, name='mpesa_timeout'),

    # Enhanced HTMX endpoints for spare parts
    path('spare-parts/live-search/', views.spare_parts_live_search, name='spare_parts_live_search'),
    path('spare-parts/quick-view/<int:part_id>/', views.spare_parts_quick_view, name='spare_parts_quick_view'),
    path('cart/add-htmx/', views.add_to_cart_htmx, name='add_to_cart_htmx'),
    path('cart/update-htmx/', views.update_cart_quantity_htmx, name='update_cart_quantity_htmx'),
    path('spare-parts/category/<int:category_id>/', views.spare_parts_category_filter, name='spare_parts_category_filter'),
    path('spare-parts/stats/', views.spare_parts_stats_htmx, name='spare_parts_stats_htmx'),

    # HTMX endpoints for sell car form
    # Note: htmx_models_by_brand URL already defined above

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
