# Gurumisha Django Application - Codebase Analysis

## Project Overview

**Project Name:** Gurumisha Motors  
**Framework:** Django 5.2.4  
**Python Version:** 3.10+  
**Architecture:** Monolithic Django application with HTMX for dynamic interactions  
**Database:** SQLite (development), PostgreSQL-ready (production)  

## Technology Stack

### Backend
- **Django 5.2.4** - Web framework
- **Python 3.10+** - Programming language
- **SQLite/PostgreSQL** - Database systems
- **Django REST Framework** - API development
- **Celery + Redis** - Background task processing
- **Gunicorn** - WSGI HTTP Server

### Frontend
- **Tailwind CSS 3.3.0** - Utility-first CSS framework
- **HTMX 1.9.2** - Dynamic interactions without JavaScript
- **Alpine.js 3.12.0** - Lightweight JavaScript framework
- **Font Awesome** - Icon library
- **Chart.js 4.3.0** - Data visualization
- **AOS 2.3.4** - Animate On Scroll library

### Authentication & Security
- **Custom User Model** - Extended AbstractUser with role-based access
- **Email Verification System** - Custom verification workflow
- **Role-based Access Control** - Customer, Vendor, Admin roles
- **Session Security** - Custom middleware for session management

### Payment Integration
- **M-Pesa Integration** - Safaricom mobile payment system
- **Python-mpesa 1.2.0** - M-Pesa SDK

### File Storage & Media
- **Local Storage** - Development media handling
- **AWS S3 Ready** - Production file storage configuration
- **Pillow 9.5.0** - Image processing

## Project Structure

```
gurumisha/
├── gurumisha_project/          # Django project configuration
│   ├── settings.py            # Main settings file
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application
│   └── asgi.py               # ASGI application
├── core/                      # Main application
│   ├── models.py             # 50+ database models
│   ├── views.py              # View controllers
│   ├── admin.py              # Django admin configuration
│   ├── forms.py              # Form definitions
│   ├── urls.py               # App URL patterns
│   ├── middleware.py         # Custom middleware
│   ├── services/             # Business logic services
│   ├── management/           # Custom Django commands
│   └── templatetags/         # Custom template tags
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   ├── core/                 # Core app templates
│   ├── components/           # Reusable components
│   └── emails/               # Email templates
├── static/                    # Static files
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   └── images/               # Image assets
├── media/                     # User uploaded files
├── server.py                  # Enhanced development server
├── manage.py                  # Django management script
└── requirements.txt           # Python dependencies
```

## Database Schema

### Core Models (50+ models)

#### User Management
- **User** - Extended AbstractUser with roles, email verification
- **Vendor** - Vendor profile with business information
- **VerificationCode** - Email verification system

#### Vehicle System
- **CarBrand** - Vehicle manufacturers (Toyota, Honda, etc.)
- **CarModel** - Specific vehicle models
- **Car** - Individual vehicle listings
- **CarImage** - Vehicle photo gallery
- **VehicleCondition** - New, Used, Certified conditions

#### E-commerce System
- **SparePart** - Spare parts catalog
- **SparePartCategory** - Hierarchical categories
- **Cart/CartItem** - Shopping cart functionality
- **Order/OrderItem** - Order management
- **Payment** - Payment tracking with M-Pesa

#### Import/Export System
- **ImportRequest** - Car import requests
- **ImportOrder** - Import order tracking (7-stage workflow)
- **ImportOrderStatusHistory** - Status change tracking

#### Communication System
- **Message** - System messaging
- **Notification** - User notifications
- **Inquiry** - Customer inquiries

#### Content Management
- **BlogPost** - Blog articles
- **ContentCategory** - Content categorization
- **Testimonial** - Customer testimonials
- **StaticPage** - CMS pages

#### Analytics & Tracking
- **ActivityLog** - User activity tracking
- **AuditLog** - System audit trail
- **PromotionAnalytics** - Marketing analytics

## Dependencies Analysis

### Production Dependencies (107 packages)
- **Core Framework:** Django 4.2.0-5.0, DRF 3.14.0+
- **Database:** psycopg2-binary 2.9.0+ (PostgreSQL)
- **Web Server:** gunicorn 20.1.0+
- **Caching:** django-redis 5.2.0+, redis 4.5.0+
- **Background Tasks:** celery 5.2.0+, django-rq 2.7.0+
- **File Storage:** django-storages 1.13.0+, boto3 1.26.0+
- **Security:** cryptography 3.4.8+
- **Monitoring:** sentry-sdk 1.20.0+, psutil 5.9.0+

### Development Dependencies
- **Testing:** pytest-django 4.5.0+, coverage 7.2.0+
- **Code Quality:** black 23.0.0+, flake8 6.0.0+, isort 5.12.0+
- **Debugging:** django-debug-toolbar 4.0.0+

## Configuration Analysis

### Current Settings (Development)
- **DEBUG:** True (needs False for production)
- **SECRET_KEY:** Hardcoded (needs environment variable)
- **ALLOWED_HOSTS:** ['*'] (needs specific domains)
- **Database:** SQLite (needs PostgreSQL for production)
- **Static Files:** Local serving (needs collection for production)
- **Email:** Gmail SMTP configured (kamandembugua18@gmail.com)

### Security Considerations
- Secret key exposed in settings.py
- Debug mode enabled
- Broad ALLOWED_HOSTS configuration
- Missing security headers for production
- No SSL/HTTPS enforcement

### Performance Considerations
- SQLite database (single-threaded)
- No caching configuration
- Static files served by Django (development)
- No CDN configuration
- Missing database connection pooling

## Deployment Requirements

### System Requirements
- **Python:** 3.10+
- **Node.js:** 16.0.0+ (for frontend build)
- **Database:** PostgreSQL 12+ (recommended)
- **Web Server:** Nginx + Gunicorn
- **Cache:** Redis 6.0+
- **SSL:** Let's Encrypt or commercial certificate

### Environment Variables Needed
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- DATABASE_URL
- EMAIL_HOST_PASSWORD
- MPESA_CONSUMER_KEY/SECRET
- AWS_ACCESS_KEY_ID (if using S3)

### Build Process Requirements
1. Install Python dependencies
2. Install Node.js dependencies
3. Build Tailwind CSS assets
4. Collect Django static files
5. Run database migrations
6. Create superuser account

### cPanel VPS Specific Considerations
- Python application setup
- Database creation and configuration
- Domain/subdomain configuration
- SSL certificate installation
- File permissions setup
- WSGI application configuration
- Email service configuration
- Backup strategy implementation

## Critical Files for Deployment

### Configuration Files
- `gurumisha_project/settings.py` - Main Django settings
- `gurumisha_project/wsgi.py` - WSGI application entry point
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies and build scripts
- `.env.example` - Environment variables template

### Static Assets
- `static/css/` - Custom stylesheets
- `static/js/` - JavaScript files
- `static/images/` - Image assets
- Tailwind CSS build process

### Database
- Migration files in `core/migrations/`
- Initial data fixtures (if any)
- Custom management commands

### Templates
- Base templates with responsive design
- Component templates for reusability
- Email templates for notifications

## Deployment Challenges & Solutions

### Challenge 1: Complex Dependencies
**Solution:** Create frozen requirements with exact versions

### Challenge 2: Frontend Build Process
**Solution:** Automated build scripts for Tailwind CSS compilation

### Challenge 3: Database Migration
**Solution:** Comprehensive migration strategy with rollback plans

### Challenge 4: Static File Serving
**Solution:** Nginx configuration for static file serving

### Challenge 5: Email Configuration
**Solution:** Production SMTP configuration with error handling

### Challenge 6: Security Hardening
**Solution:** Production settings with security best practices

This analysis provides the foundation for creating a comprehensive deployment strategy tailored to cPanel VPS hosting requirements.
