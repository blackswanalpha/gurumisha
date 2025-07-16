# Gurumisha Server.py Usage Guide

## Quick Start

### Prerequisites
- Python 3.10+ installed
- Django project dependencies installed
- Database migrations completed
- Virtual environment activated (recommended)

### Basic Usage
```bash
# Navigate to project directory
cd gurumisha

# Start server with default settings
python server.py

# Server will start on http://127.0.0.1:8000
# Admin panel available at http://127.0.0.1:8000/admin/
```

## Command Line Options

### Server Configuration
```bash
# Custom host and port
python server.py --host 0.0.0.0 --port 8080

# Custom kill switch duration (default: 4 days)
python server.py --kill-switch-days 7

# Combine options
python server.py --host 0.0.0.0 --port 8080 --kill-switch-days 2
```

### Admin Management
```bash
# Create admin user interactively
python server.py --create-admin
# Prompts for: username, email, password

# Send system message interactively
python server.py --send-message
# Prompts for: title, content, target audience
```

### Help and Information
```bash
# Show all available options
python server.py --help
```

## Server Startup Process

### 1. Environment Setup
- Checks for manage.py in current directory
- Validates Django configuration
- Tests database connectivity
- Checks for pending migrations

### 2. Pre-startup Backup
- Creates automatic database backup
- Saves to `backups/` directory
- Timestamped filename format: `db_backup_YYYYMMDD_HHMMSS.json`

### 3. System Statistics
- Logs current user counts by role
- Reports content statistics
- Shows notification and message counts

### 4. Default Admin Creation
- Creates default admin user if none exists
- Username: `admin`
- Email: `admin@gurumisha.com`
- Password: `admin123`
- **⚠️ Change default credentials immediately in production**

### 5. Kill Switch Activation
- Starts background monitoring thread
- Logs countdown every hour
- Calculates exact shutdown time (4 days from start)

### 6. Django Server Launch
- Starts Django development server
- Serves on specified host and port
- Maintains all existing functionality

## Kill Switch Behavior

### Timeline
```
Day 1-3: Normal operation with hourly countdown logs
Day 4:   Shutdown warnings sent to users
Hour 96: Automatic server termination
```

### Warning System
- **24 hours before**: System message to all users
- **1 hour before**: Email notifications sent
- **Shutdown**: Graceful process termination

### Bypass Protection
- Cannot be disabled through user interface
- Runs in separate thread
- Responds to system signals
- Time-based trigger (not user-action based)

## Admin User Management

### Default Admin Access
```
URL: http://127.0.0.1:8000/admin/
Username: admin
Password: admin123
```

### Creating Custom Admins

#### Interactive Method
```bash
python server.py --create-admin
```
Prompts for:
- Username
- Email address
- Password

#### Programmatic Method
```python
from server import GurumishaServer

server = GurumishaServer()
server.create_admin_user(
    username='custom_admin',
    email='admin@company.com',
    password='secure_password123',
    force=True  # Update if exists
)
```

### Admin Capabilities
- Full Django admin panel access
- User management (all roles)
- Content management (cars, spare parts)
- Order and import request management
- System message creation
- Notification management
- Analytics and reporting

## Messaging System

### System Messages

#### Interactive Creation
```bash
python server.py --send-message
```
Prompts for:
- Message title
- Message content
- Target audience (all/customers/vendors/admins)

#### Programmatic Creation
```python
server.send_system_message(
    title='Platform Update',
    content='New features are now available!',
    target_audience='customers',
    message_type='feature',
    priority=2
)
```

### Target Audiences
- `all`: All registered users
- `customers`: Customer role users only
- `vendors`: Vendor role users only
- `admins`: Admin role users only
- `new_users`: Users registered < 30 days
- `active_users`: Recently active users

### Message Types
- `announcement`: General announcements
- `newsletter`: Newsletter content
- `alert`: Important alerts
- `promotion`: Promotional messages
- `maintenance`: Maintenance notices
- `feature`: Feature updates
- `policy`: Policy changes
- `welcome`: Welcome messages

### Priority Levels
- `1`: Low priority
- `2`: Normal priority (default)
- `3`: High priority
- `4`: Critical priority

## Notification System

### Multi-Channel Notifications
```python
server.send_notification_to_users(
    title='System Maintenance',
    message='Scheduled maintenance tonight at 2 AM',
    user_roles=['vendor', 'admin'],
    channels=['email', 'in_app']
)
```

### Available Channels
- `in_app`: In-application notifications
- `email`: Email notifications
- `sms`: SMS notifications (requires provider setup)
- `push`: Push notifications (requires service setup)

### User Role Targeting
- `customer`: End users
- `vendor`: Dealers and sellers
- `admin`: System administrators

## Monitoring and Logging

### Log File Location
- File: `gurumisha_server.log`
- Location: Project root directory
- Format: Timestamp - Logger - Level - Message

### Log Levels
- **INFO**: Normal operations, startup/shutdown
- **WARNING**: Non-critical issues
- **ERROR**: Recoverable errors
- **CRITICAL**: Kill switch activation, system failures

### Key Log Events
- Server startup and configuration
- Kill switch countdown updates
- Admin user operations
- Message and notification activities
- Health check results
- Error conditions and recovery
- Shutdown sequence

### Real-time Monitoring
```bash
# Follow log file in real-time
tail -f gurumisha_server.log

# Filter for specific log levels
grep "ERROR\|CRITICAL" gurumisha_server.log
```

## Health Monitoring

### System Health Checks
- Database connectivity test
- Migration status verification
- Basic system resource checks
- Configuration validation

### Statistics Tracking
- User counts by role
- Content statistics (cars, spare parts, orders)
- Notification and message counts
- System activity levels

### Backup System
- Automatic pre-startup backup
- JSON format for portability
- Timestamped files for organization
- Error handling for backup failures

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Error: [Errno 48] Address already in use
# Solution: Use different port
python server.py --port 8001
```

#### Database Locked
```bash
# Error: database is locked
# Solution: Stop other Django processes
ps aux | grep python
kill <process_id>
```

#### Permission Errors
```bash
# Error: Permission denied
# Solution: Check file permissions
chmod +x server.py
```

#### Import Errors
```bash
# Error: No module named 'django'
# Solution: Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Debug Mode
Enable detailed error information:
1. Set `DEBUG=True` in Django settings
2. Check console output for detailed tracebacks
3. Review `gurumisha_server.log` for error details

### Health Check Failures
If system health check fails:
1. Verify database file exists and is accessible
2. Check Django settings configuration
3. Ensure all migrations are applied
4. Verify virtual environment is activated

## Production Deployment

### Security Checklist
- [ ] Change default admin credentials
- [ ] Set `DEBUG=False` in settings
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Set up external backup system

### Hosting Considerations
- Use reverse proxy (Nginx/Apache) for production
- Configure proper static file serving
- Set up SSL/TLS certificates
- Monitor resource usage
- Implement external logging
- Configure automated backups

### Environment Variables
```bash
# Recommended production environment
export DEBUG=False
export SECRET_KEY=your-secret-key
export ALLOWED_HOSTS=yourdomain.com
export DATABASE_URL=your-database-url
```

## Integration with Existing System

### Compatibility
- Full compatibility with existing Django project
- Preserves all user data and configurations
- Maintains all existing functionality
- No database schema changes required

### Feature Preservation
All existing features remain available:
- Car sales and listings
- Spare parts e-commerce
- Import/export tracking
- User dashboards
- Admin management
- HTMX dynamic interactions
- Email verification system

### Data Safety
- No data loss or corruption
- Preserves user accounts and roles
- Maintains all business data
- Keeps system configurations

## Support and Maintenance

### Log Analysis
Regular log review helps identify:
- Performance issues
- Security concerns
- User behavior patterns
- System errors

### Backup Management
- Regular backup verification
- Backup retention policies
- Recovery testing
- Off-site backup storage

### Update Procedures
1. Stop server gracefully
2. Create backup
3. Apply updates
4. Test functionality
5. Restart server

For additional support, refer to the comprehensive documentation in `SERVER_DOCUMENTATION.md` and `PLATFORM_ANALYSIS.md`.
