# GPS Tracking System Documentation

## Overview

The Gurumisha GPS Tracking System provides comprehensive real-time location tracking for import car orders throughout their journey from origin to final delivery. The system integrates seamlessly with the existing import workflow and provides both customer and admin interfaces for monitoring vehicle locations.

## Features

### Core Features
- **Real-time GPS coordinate tracking** for import orders
- **Interactive live maps** with vehicle position visualization
- **Route planning and waypoint management**
- **Automated location updates** based on import status changes
- **Historical location tracking** with detailed audit trails
- **Mobile-responsive design** with touch-friendly interactions
- **HTMX-powered real-time updates** without page refreshes
- **Server-Sent Events (SSE)** for live notifications

### Customer Features
- Live tracking map with current vehicle location
- Route timeline visualization showing journey progress
- Real-time status updates and notifications
- Estimated arrival times and progress indicators
- Location sharing capabilities
- Mobile-optimized tracking interface

### Admin Features
- Comprehensive GPS tracking management dashboard
- Bulk location updates and route management
- Real-time monitoring of all tracked orders
- Location history and analytics
- Manual coordinate updates and corrections
- Route and waypoint configuration

## Database Schema

### Core Models

#### ImportOrderLocation
Stores GPS coordinates and location information for import orders.

```python
class ImportOrderLocation(models.Model):
    import_order = models.ForeignKey(ImportOrder, related_name='locations')
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    is_current_location = models.BooleanField(default=False)
    is_customer_visible = models.BooleanField(default=True)
    # ... additional fields
```

#### LocationTrackingHistory
Maintains historical tracking data for audit and analysis.

```python
class LocationTrackingHistory(models.Model):
    import_order = models.ForeignKey(ImportOrder, related_name='tracking_history')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    tracking_source = models.CharField(max_length=20, choices=TRACKING_SOURCE_CHOICES)
    status_at_time = models.CharField(max_length=30)
    recorded_at = models.DateTimeField()
    # ... additional fields
```

#### ImportOrderRoute
Defines planned routes with origin, destination, and waypoints.

```python
class ImportOrderRoute(models.Model):
    import_order = models.OneToOneField(ImportOrder, related_name='route')
    route_name = models.CharField(max_length=200)
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPE_CHOICES)
    origin_location = models.ForeignKey(ImportOrderLocation, related_name='routes_as_origin')
    destination_location = models.ForeignKey(ImportOrderLocation, related_name='routes_as_destination')
    # ... additional fields
```

#### RouteWaypoint
Individual waypoints along import order routes.

```python
class RouteWaypoint(models.Model):
    route = models.ForeignKey(ImportOrderRoute, related_name='waypoints')
    location = models.ForeignKey(ImportOrderLocation, related_name='waypoints')
    sequence_order = models.PositiveIntegerField()
    waypoint_type = models.CharField(max_length=20, choices=WAYPOINT_TYPE_CHOICES)
    is_current = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    # ... additional fields
```

### Enhanced ImportOrder Model
The existing ImportOrder model has been extended with GPS tracking fields:

```python
# GPS Tracking Information
current_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
current_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
current_location_name = models.CharField(max_length=200, blank=True)
last_location_update = models.DateTimeField(null=True, blank=True)
tracking_enabled = models.BooleanField(default=True)
```

## API Endpoints

### Customer Endpoints
- `GET /import/tracking/{order_number}/location/` - Get current location data
- `GET /import/tracking/{order_number}/route/` - Get route and waypoint data
- `GET /import/tracking/{order_number}/live/` - Get comprehensive live tracking data
- `GET /import/tracking/{order_number}/history/` - Get location history with pagination
- `GET /import/tracking/{order_number}/sse/` - Server-Sent Events for real-time updates

### Admin Endpoints
- `GET /dashboard/admin/gps-tracking/` - Main GPS tracking management dashboard
- `GET /dashboard/admin/tracking/order/{order_id}/location-modal/` - Location management modal
- `POST /dashboard/admin/tracking/order/{order_id}/update-location/` - Update order location
- `POST /dashboard/admin/tracking/order/{order_id}/create-route/` - Create new route
- `POST /dashboard/admin/tracking/order/{order_id}/add-waypoint/` - Add route waypoint

## Integration Points

### Status Change Integration
The system automatically integrates with import order status changes:

```python
# In signals.py
@receiver(post_save, sender=ImportOrder)
def log_import_order_status_change(sender, instance, created, **kwargs):
    # GPS Tracking Integration
    if instance.tracking_enabled:
        # Create tracking history entry
        LocationTrackingHistory.objects.create(...)
        
        # Auto-update location based on status
        if not instance.current_latitude or not instance.current_longitude:
            auto_update_location_for_status(instance)
```

### Automatic Route Creation
New import orders automatically get default routes and waypoints:

```python
# Create default route for new import orders
if created and instance.tracking_enabled:
    create_default_route_for_order(instance)
```

## Frontend Components

### Live Map Component
Interactive map with real-time updates using Leaflet.js:
- Vehicle marker with current position
- Route visualization with waypoints
- Real-time coordinate updates via HTMX
- Mobile-responsive controls and interactions

### Route Timeline Component
Visual timeline showing import journey progress:
- Interactive stage indicators
- Completion status for each stage
- Location information for each stage
- Mobile-friendly compact view

### Live Status Component
Real-time status updates with progress tracking:
- Current status and progress percentage
- Location information display
- Automatic refresh capabilities
- Action buttons for manual updates

### Live Notifications Component
Real-time notification system for tracking updates:
- Browser notifications for location changes
- Notification badge with unread count
- Dropdown with recent tracking updates
- Auto-refresh with HTMX polling

## Mobile Responsiveness

The GPS tracking system is fully optimized for mobile devices:

### Touch-Friendly Interactions
- Swipe gestures for timeline navigation
- Touch-optimized map controls
- Responsive button sizing and spacing

### Adaptive Layouts
- Automatic compact view on mobile devices
- Responsive grid layouts for different screen sizes
- Optimized map dimensions for mobile viewing

### Performance Optimizations
- Reduced update frequencies on mobile
- Optimized asset loading
- Efficient HTMX request handling

## Management Commands

### Initialize GPS Tracking
Command to set up GPS tracking for existing import orders:

```bash
python manage.py initialize_gps_tracking [--dry-run] [--force] [--order-number ORDER_NUMBER]
```

Options:
- `--dry-run`: Show what would be done without making changes
- `--force`: Force update even if tracking data already exists
- `--order-number`: Initialize tracking for a specific order

## Configuration

### Default Locations
The system includes default locations for different import stages:

```python
status_locations = {
    'import_request': {'name': 'Import Request Processing Center', 'lat': -1.2921, 'lng': 36.8219},
    'auction_won': {'name': 'Auction House - Japan', 'lat': 35.6762, 'lng': 139.6503},
    'shipped': {'name': 'Departure Port - Japan', 'lat': 35.4437, 'lng': 139.6380},
    # ... more locations
}
```

### Update Intervals
- Live map updates: Every 60 seconds
- Dashboard updates: Every 45 seconds
- Notifications: Every 120 seconds
- Status component: Every 30 seconds

## Security Considerations

### Access Control
- Customer access limited to their own orders
- Admin access requires proper role verification
- HTMX requests include CSRF protection

### Data Privacy
- Location data is only visible to authorized users
- Customer visibility flags control data exposure
- Audit trails maintain data integrity

## Future Enhancements

### Planned Features
- Integration with external GPS tracking APIs
- Automated location updates via webhooks
- Advanced analytics and reporting
- Geofencing and alert systems
- Integration with shipping company APIs

### Performance Improvements
- WebSocket implementation for real-time updates
- Caching strategies for frequently accessed data
- Database query optimizations
- CDN integration for map assets

## Troubleshooting

### Common Issues
1. **Location not updating**: Check tracking_enabled flag and status change signals
2. **Map not loading**: Verify Leaflet.js CDN availability and API keys
3. **HTMX requests failing**: Check CSRF tokens and request headers
4. **Mobile responsiveness issues**: Test viewport meta tags and CSS media queries

### Debug Commands
```bash
# Check tracking status for all orders
python manage.py shell -c "from core.models import ImportOrder; print(ImportOrder.objects.filter(tracking_enabled=True).count())"

# Initialize tracking for specific order
python manage.py initialize_gps_tracking --order-number ORD-2024-001

# View tracking history for order
python manage.py shell -c "from core.models import ImportOrder; order = ImportOrder.objects.get(order_number='ORD-2024-001'); print(order.tracking_history.count())"
```
