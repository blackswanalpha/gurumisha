# 📊 Gurumisha Activity Log, Audit & Notification System

## 🎯 Overview

A comprehensive system for tracking user activities, maintaining audit trails, and managing notifications across the Gurumisha Motors platform. This system provides complete visibility into user actions, security compliance, and automated communication.

## 🏗️ System Architecture

### Core Components

1. **Activity Log Manager** - Tracks user activities and interactions
2. **Audit Log System** - Maintains compliance and security audit trails  
3. **Notification Manager** - Multi-channel notification delivery system
4. **Signal Handlers** - Automatic tracking of model changes
5. **Middleware** - Request-level activity and audit tracking

## 📋 Features

### 🔍 Activity Logging
- **User Actions**: Login, logout, page views, searches
- **CRUD Operations**: Create, read, update, delete tracking
- **Business Logic**: Order processing, import tracking, inquiries
- **Context Data**: IP addresses, user agents, session information
- **Object Relations**: Links activities to specific database objects

### 🛡️ Audit Logging
- **Security Events**: Login attempts, permission changes, data access
- **Data Changes**: Field-level change tracking with before/after values
- **Compliance**: Regulatory compliance and data governance
- **Severity Levels**: Critical, High, Medium, Low classification
- **Forensic Analysis**: Complete audit trail for investigations

### 📢 Notification System
- **Multi-Channel**: Email, SMS, Push, In-App notifications
- **Templates**: Customizable notification templates
- **Preferences**: User-configurable notification settings
- **Queue Management**: Reliable delivery with retry logic
- **Scheduling**: Delayed and scheduled notifications

## 📁 File Structure

```
gurumisha/
├── core/
│   ├── models.py                    # Activity, Audit, Notification models
│   ├── activity_manager.py          # Activity logging manager
│   ├── notification_manager.py      # Notification system manager
│   ├── signals.py                   # Automatic model change tracking
│   ├── middleware.py                # Request-level tracking
│   └── management/commands/
│       ├── process_notifications.py # Notification queue processor
│       └── create_notification_templates.py
├── templates/core/dashboard/
│   ├── activity_logs.html           # User activity view
│   ├── admin_activity_logs.html     # Admin activity overview
│   ├── admin_audit_logs.html        # Audit trail interface
│   ├── notification_preferences.html # User notification settings
│   └── admin_notification_queue.html # Admin queue management
└── docs/
    └── ACTIVITY_AUDIT_NOTIFICATION_SYSTEM.md
```

## 🚀 Quick Start

### 1. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Notification Templates

```bash
python manage.py create_notification_templates
```

### 3. Process Notification Queue

```bash
# Process pending notifications
python manage.py process_notifications

# Include failed retry and cleanup
python manage.py process_notifications --retry-failed --cleanup
```

## 📊 Models Overview

### ActivityLog
Tracks user activities across the platform:

```python
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    content_object = GenericForeignKey()
    extra_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

### AuditLog
Maintains security and compliance audit trails:

```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    table_name = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField()
    new_value = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True)
```

### NotificationQueue
Manages notification delivery:

```python
class NotificationQueue(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.IntegerField()
    scheduled_at = models.DateTimeField()
    retry_count = models.PositiveIntegerField()
```

## 🔧 Usage Examples

### Activity Logging

```python
from core.activity_manager import ActivityManager

# Log user activity
ActivityManager.log_activity(
    user=request.user,
    action='car_view',
    description=f"Viewed car: {car.make} {car.model}",
    content_object=car,
    request=request
)

# Log search activity
ActivityManager.log_search_activity(
    user=request.user,
    search_query="Toyota Camry",
    filters={'year': 2020, 'price_max': 2000000},
    results_count=15,
    request=request
)
```

### Audit Logging

```python
from core.activity_manager import AuditManager

# Log security event
AuditManager.log_security_event(
    user=request.user,
    event_type='failed_login',
    description="Multiple failed login attempts",
    severity='high',
    request=request
)

# Log data change
AuditManager.log_model_change(
    user=request.user,
    instance=car,
    action_type='update',
    changed_fields={'price': ('2000000', '1800000')},
    request=request
)
```

### Notification Management

```python
from core.notification_manager import NotificationManager, NotificationShortcuts

# Send multi-channel notification
NotificationManager.send_notification(
    recipient=user,
    title='Order Status Update',
    message='Your order has been shipped!',
    channels=['email', 'sms', 'in_app'],
    template_name='order_status_change',
    context={'order': order, 'new_status': 'shipped'},
    priority=3
)

# Use shortcuts for common notifications
NotificationShortcuts.notify_order_status_change(order, 'delivered')
NotificationShortcuts.notify_import_status_change(import_order, 'arrived_docked')
```

## 🎛️ Dashboard Views

### User Activity Logs (`/dashboard/activity-logs/`)
- Personal activity timeline
- Action filtering
- IP address and session tracking
- Related object links

### Admin Activity Overview (`/dashboard/admin/activity-logs/`)
- System-wide activity monitoring
- User and action filtering
- Date range selection
- Export capabilities

### Audit Trail (`/dashboard/admin/audit-logs/`)
- Security and compliance monitoring
- Severity-based filtering
- Field-level change tracking
- Forensic investigation tools

### Notification Preferences (`/dashboard/notification-preferences/`)
- Channel preferences (Email, SMS, Push, In-App)
- Notification type settings
- Quiet hours configuration
- Delivery frequency options

## 🔄 Automatic Tracking

### Signal-Based Tracking
Automatic activity and audit logging for:

- **User Authentication**: Login/logout events
- **Model Changes**: CRUD operations on all major models
- **Security Events**: Permission changes, failed attempts
- **Business Events**: Order status changes, import updates

### Middleware Tracking
Request-level tracking includes:

- **Page Views**: Automatic page visit logging
- **Admin Operations**: Administrative action tracking
- **Security Monitoring**: Suspicious activity detection

## 📧 Notification Channels

### Email Notifications
- HTML templates with branding
- Automatic fallback to plain text
- Delivery confirmation tracking
- Bounce and failure handling

### SMS Notifications
- Critical alerts and updates
- Character limit optimization
- Delivery status tracking
- Provider integration ready

### Push Notifications
- Browser and mobile push
- Real-time delivery
- Click-through tracking
- Subscription management

### In-App Notifications
- Dashboard notification center
- Real-time updates via WebSocket
- Read/unread status tracking
- Action buttons and links

## 🛠️ Configuration

### Notification Templates
Create custom templates for different notification types:

```python
NotificationTemplate.objects.create(
    name='custom_alert',
    template_type='email',
    subject_template='Alert: {alert_type}',
    body_template='Dear {recipient.first_name}, {message}',
    available_variables=['recipient', 'alert_type', 'message'],
    priority=3
)
```

### User Preferences
Users can configure:

- Channel preferences (Email, SMS, Push, In-App)
- Notification types (Orders, Imports, Security, Marketing)
- Delivery frequency (Immediate, Hourly, Daily, Weekly)
- Quiet hours (Start/end times)

## 📈 Analytics & Reporting

### Activity Analytics
- User engagement metrics
- Feature usage statistics
- Peak activity periods
- Geographic distribution

### Audit Reports
- Security event summaries
- Compliance reports
- Data access logs
- Change history reports

### Notification Metrics
- Delivery success rates
- Channel performance
- User engagement rates
- Bounce and failure analysis

## 🔒 Security & Privacy

### Data Protection
- Personal data anonymization options
- GDPR compliance features
- Data retention policies
- Secure data transmission

### Access Control
- Role-based access to logs
- Audit trail protection
- Administrative oversight
- Security event alerting

## 🚀 Performance Optimization

### Database Optimization
- Indexed fields for fast queries
- Partitioning for large datasets
- Archival strategies
- Query optimization

### Notification Queue
- Batch processing
- Priority-based delivery
- Retry mechanisms
- Dead letter handling

## 📋 Maintenance

### Regular Tasks
```bash
# Daily: Process notification queue
python manage.py process_notifications --retry-failed

# Weekly: Clean old notifications
python manage.py process_notifications --cleanup --cleanup-days 30

# Monthly: Archive old activity logs
python manage.py archive_old_logs --days 90
```

### Monitoring
- Queue length monitoring
- Delivery failure alerts
- Performance metrics
- Error rate tracking

## 🎯 Best Practices

### Activity Logging
- Log meaningful user actions
- Include relevant context data
- Use appropriate action types
- Avoid logging sensitive data

### Audit Logging
- Log all security-relevant events
- Include before/after values for changes
- Use appropriate severity levels
- Maintain data integrity

### Notifications
- Respect user preferences
- Use appropriate channels for content
- Implement proper retry logic
- Monitor delivery success

---

**🎉 The Activity Log, Audit & Notification System provides comprehensive tracking and communication capabilities for the Gurumisha Motors platform!**
