# Gurumisha Server.py Documentation

## Overview

The `server.py` file is a standalone Python server script designed to run the Gurumisha Django e-commerce platform with enhanced management capabilities and a built-in 4-day kill switch for hosted environments.

## Features

### 🚀 Core Functionality
- **Django Application Hosting**: Runs the complete Gurumisha e-commerce platform
- **Admin User Management**: Create and manage admin users programmatically
- **Custom Messaging System**: Send system-wide messages and notifications
- **4-Day Kill Switch**: Automatic shutdown after 4 days for hosted environments
- **Health Monitoring**: System health checks and database connectivity monitoring
- **Backup System**: Automatic database backups before startup
- **Comprehensive Logging**: Detailed logging with file and console output

### 🔧 Technical Integration

#### Django Integration
- Uses existing Django settings (`gurumisha_project.settings`)
- Integrates with custom User model (`core.User`)
- Leverages existing Message and Notification models
- Compatible with all existing authentication and role systems

#### Database Compatibility
- Works with existing SQLite database
- Maintains all current data and relationships
- Supports existing user roles (customer, vendor, admin)
- Preserves all e-commerce functionality

## Usage

### Basic Server Startup
```bash
# Start server with default settings
python server.py

# Start on custom host/port
python server.py --host 0.0.0.0 --port 8080

# Custom kill switch duration (in days)
python server.py --kill-switch-days 7
```

### Admin Management
```bash
# Create admin user interactively
python server.py --create-admin

# Send system message interactively
python server.py --send-message
```

### Programmatic Usage
```python
from server import GurumishaServer

# Initialize server
server = GurumishaServer(host='127.0.0.1', port=8000, kill_switch_days=4)

# Create admin user
server.create_admin_user('admin', 'admin@example.com', 'password123')

# Send system message
server.send_system_message(
    title='Welcome to Gurumisha',
    content='Platform is now online!',
    target_audience='all'
)

# Start server
server.start()
```

## Kill Switch Implementation

### How It Works
1. **Timer Initialization**: Kill switch timer starts when server initializes
2. **Background Monitoring**: Separate thread monitors elapsed time every minute
3. **Countdown Logging**: Logs remaining time every hour
4. **Notification System**: Sends warnings to users before shutdown
5. **Graceful Shutdown**: Terminates server processes cleanly
6. **Bypass Protection**: Cannot be easily disabled or bypassed

### Kill Switch Features
- **Exact 4-Day Duration**: Shuts down after exactly 4 days (96 hours)
- **Automatic Notifications**: Warns users before shutdown
- **Clean Termination**: Gracefully stops all processes
- **Logging**: Records all kill switch activities
- **Signal Handling**: Responds to system signals (SIGINT, SIGTERM)

### Hosted Environment Design
- Designed specifically for hosted server environments
- Prevents indefinite resource usage
- Ensures automatic cleanup
- Provides audit trail of server usage

## Admin User Management

### Default Admin Creation
- Automatically creates default admin user on startup
- Username: `admin`
- Email: `admin@gurumisha.com`
- Password: `admin123`
- Role: `admin` with full privileges

### Custom Admin Creation
```python
server.create_admin_user(
    username='custom_admin',
    email='admin@company.com',
    password='secure_password',
    force=True  # Update existing user
)
```

### Admin Capabilities
- Full Django admin panel access
- User management (customers, vendors, admins)
- Content management (cars, spare parts, orders)
- System configuration
- Message and notification management

## Messaging System Integration

### System Messages
Uses existing `Message` model with features:
- **Target Audiences**: all, customers, vendors, admins, new_users, active_users
- **Message Types**: announcement, newsletter, alert, promotion, maintenance
- **Priority Levels**: 1 (Low) to 4 (Critical)
- **Status Management**: draft, scheduled, active, paused, expired

### Notifications
Integrates with `NotificationManager` for:
- **Multi-Channel Delivery**: in-app, email, SMS, push notifications
- **User Preferences**: Respects user notification settings
- **Template System**: Uses existing notification templates
- **Analytics**: Tracks delivery and engagement

### Example Usage
```python
# Send system announcement
server.send_system_message(
    title='New Feature Available',
    content='Check out our new car import tracking system!',
    target_audience='customers',
    message_type='feature',
    priority=2
)

# Send notifications to specific roles
server.send_notification_to_users(
    title='System Maintenance',
    message='Scheduled maintenance tonight at 2 AM',
    user_roles=['vendor', 'admin'],
    channels=['email', 'in_app']
)
```

## System Health Monitoring

### Health Checks
- **Database Connectivity**: Tests database connection
- **Migration Status**: Checks for pending migrations
- **System Resources**: Monitors basic system health
- **Error Detection**: Identifies configuration issues

### Statistics Tracking
Monitors key metrics:
- User counts by role
- Content statistics (cars, spare parts, orders)
- Notification and message counts
- System activity levels

### Backup System
- **Automatic Backups**: Creates backup before server start
- **JSON Format**: Uses Django's dumpdata for portability
- **Timestamped Files**: Organized backup files
- **Error Handling**: Graceful failure handling

## Logging System

### Log Levels
- **INFO**: Normal operations, startup/shutdown events
- **WARNING**: Non-critical issues, existing user warnings
- **ERROR**: Recoverable errors, failed operations
- **CRITICAL**: Kill switch activation, system failures

### Log Destinations
- **File Logging**: `gurumisha_server.log` in project directory
- **Console Output**: Real-time console logging
- **Structured Format**: Timestamp, logger name, level, message

### Log Content
- Server startup/shutdown events
- Kill switch countdown and activation
- Admin user operations
- Message and notification activities
- Health check results
- Error conditions and recovery

## Security Considerations

### Kill Switch Security
- **Thread-based Implementation**: Runs in separate thread
- **Time-based Trigger**: Cannot be bypassed by user actions
- **Signal Handling**: Responds to system termination signals
- **Clean Shutdown**: Prevents data corruption

### Admin Security
- **Default Credentials**: Should be changed in production
- **Role-based Access**: Uses Django's permission system
- **Email Verification**: Integrates with existing verification system
- **Audit Logging**: Tracks admin activities

### Production Recommendations
1. Change default admin credentials immediately
2. Use environment variables for sensitive configuration
3. Enable HTTPS in production
4. Configure proper firewall rules
5. Monitor log files regularly
6. Set up external backup systems

## Error Handling

### Graceful Degradation
- **Database Errors**: Continues operation where possible
- **Network Issues**: Retries with exponential backoff
- **Resource Constraints**: Logs warnings and continues
- **Configuration Errors**: Fails fast with clear messages

### Recovery Mechanisms
- **Automatic Retries**: For transient failures
- **Fallback Options**: Alternative execution paths
- **State Preservation**: Maintains system state during errors
- **User Notification**: Informs users of service issues

## Integration with Existing System

### Compatibility
- **Full Django Compatibility**: Uses standard Django patterns
- **Model Integration**: Works with all existing models
- **Authentication System**: Preserves existing auth flow
- **HTMX Functionality**: Maintains all dynamic features

### Data Preservation
- **No Schema Changes**: Uses existing database structure
- **User Data Safety**: Preserves all user accounts and data
- **Content Integrity**: Maintains cars, orders, and transactions
- **Configuration Retention**: Keeps all system settings

### Feature Availability
All existing features remain available:
- Car sales and listings
- Spare parts shop with M-Pesa integration
- Import/export tracking
- User dashboards and profiles
- Admin management panels
- Messaging and notifications
- Email verification system
- Content management system

## Troubleshooting

### Common Issues
1. **Port Already in Use**: Change port with `--port` argument
2. **Database Locked**: Ensure no other Django processes running
3. **Permission Errors**: Check file system permissions
4. **Import Errors**: Verify Django installation and PYTHONPATH

### Debug Mode
Enable Django debug mode by setting `DEBUG=True` in settings for detailed error information.

### Log Analysis
Check `gurumisha_server.log` for detailed operation logs and error messages.

## Conclusion

The `server.py` script provides a robust, production-ready solution for hosting the Gurumisha Django e-commerce platform with enhanced management capabilities and built-in safety mechanisms. The 4-day kill switch ensures responsible resource usage in hosted environments while maintaining full functionality and data integrity.
