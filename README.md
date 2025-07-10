# Gurumisha - Django E-Commerce Platform

A comprehensive Django-based e-commerce platform specializing in car sales, spare parts, and import/export functionality with modern UI/UX design.

## 🚀 Features

### Core Functionality
- **Multi-User Authentication System**
  - Customer, Vendor, and Admin roles
  - Email verification with code generation
  - Password reset functionality
  - Role-based access control

### Car Sales & Import Management
- **Vehicle Listings**
  - Comprehensive car catalog with filtering
  - Advanced search functionality
  - Image galleries and detailed specifications
  - Price comparison and favorites

- **Import Car Tracking**
  - 7-stage workflow tracking system
  - Real-time status updates with HTMX
  - Progress timeline visualization
  - Email notifications for status changes

### Spare Parts Management
- **Inventory System**
  - Barcode/SKU tracking
  - Supplier management
  - Stock level monitoring
  - Category-based organization

- **M-Pesa Integration**
  - Secure payment processing
  - Transaction tracking
  - Payment confirmation system

### Dashboard Systems
- **Admin Dashboard**
  - Import request management
  - User management
  - Analytics and reporting
  - System settings

- **Vendor Dashboard**
  - Product listing management
  - Order tracking
  - Sales analytics
  - Inventory management

- **Customer Dashboard**
  - Order history
  - Wishlist management
  - Profile settings
  - Purchase tracking

## 🛠 Technology Stack

### Backend
- **Django 4.x** - Web framework
- **Python 3.10+** - Programming language
- **SQLite/PostgreSQL** - Database
- **Django REST Framework** - API development

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **HTMX** - Dynamic interactions without JavaScript
- **HTML5** - Semantic markup
- **JavaScript** - Enhanced interactivity

### Design System
- **Harrier Design Patterns** - Custom design system
- **Color Palette**: Red, Black, Dark Blue, White
- **Typography**: Raleway/Montserrat fonts
- **Mobile-first responsive design**

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js and npm (for Tailwind CSS)
- Git

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/blackswanalpha/gurumisha.git
cd gurumisha
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for Tailwind CSS
cd gurumisha
npm install
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=kamandembugua18@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
```

### 5. Database Setup
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### 6. Build Static Assets
```bash
# Build Tailwind CSS
npm run build

# Collect static files
python manage.py collectstatic
```

## 🚀 Running the Application

### Development Server
```bash
# Start Django development server
python manage.py runserver

# In another terminal, watch for Tailwind changes
npm run dev
```

Visit `http://127.0.0.1:8000` to access the application.

### Default Admin Access
- URL: `http://127.0.0.1:8000/admin/`
- Username: Use the superuser credentials created during setup

## 📁 Project Structure

```
gurumisha/
├── gurumisha/                 # Main Django project
│   ├── settings.py           # Django settings
│   ├── urls.py              # URL configuration
│   └── wsgi.py              # WSGI configuration
├── apps/                     # Django applications
│   ├── authentication/      # User authentication
│   ├── cars/                # Car listings and management
│   ├── spare_parts/         # Spare parts functionality
│   ├── import_export/       # Import/export tracking
│   ├── dashboard/           # Dashboard views
│   └── core/                # Core utilities
├── templates/               # HTML templates
│   ├── base/               # Base templates
│   ├── auth/               # Authentication templates
│   ├── dashboard/          # Dashboard templates
│   └── components/         # Reusable components
├── static/                 # Static files
│   ├── css/               # Compiled CSS
│   ├── js/                # JavaScript files
│   └── images/            # Image assets
├── media/                 # User uploaded files
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
└── README.md             # This file
```

## 🎨 Design System

### Color Palette
- **Primary Red**: #DC2626
- **Black**: #000000
- **Dark Blue**: #1E3A8A
- **White**: #FFFFFF

### Typography
- **Primary Font**: Raleway
- **Secondary Font**: Montserrat

### Components
- Glassmorphism effects
- Smooth transitions and animations
- Micro-interactions
- Mobile-responsive design

## 🔐 User Roles & Permissions

### Customer
- Browse and purchase vehicles
- Manage spare parts orders
- Track import requests
- Access personal dashboard

### Vendor
- List and manage vehicles
- Handle spare parts inventory
- Process customer orders
- Access vendor analytics

### Admin
- Full system access
- User management
- Import/export oversight
- System configuration

## 📊 Import Tracking Workflow

1. **Confirmed** - Order confirmed and payment received
2. **Auction Won** - Vehicle successfully acquired at auction
3. **Shipped** - Vehicle shipped from origin
4. **In Transit** - Vehicle in transit to destination
5. **Arrived-Docked** - Vehicle arrived at port
6. **Under Clearance** - Customs clearance in progress
7. **Registered** - Vehicle registered locally
8. **Ready for Dispatch** - Ready for customer pickup
9. **Delivered** - Vehicle delivered to customer

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in environment variables
2. Configure production database (PostgreSQL recommended)
3. Set up static file serving (WhiteNoise or CDN)
4. Configure email backend
5. Set up SSL certificates

### Environment Variables
```env
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:password@localhost/gurumisha
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Django best practices
- Use semantic HTML5 markup
- Implement mobile-first responsive design
- Write comprehensive tests
- Document new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Developer**: Victor Mbugua (@blackswanalpha)
- **Email**: kamandembugua18@gmail.com

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Email: kamandembugua18@gmail.com

## 🔄 Changelog

### Version 1.0.0 (Current)
- Initial release
- Complete authentication system
- Car sales functionality
- Spare parts management
- Import/export tracking
- Multi-role dashboard system
- Harrier design implementation

## 🚧 Roadmap

- [ ] Mobile application development
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Enhanced payment gateway integration
- [ ] AI-powered recommendation system
- [ ] Real-time chat support
- [ ] Advanced reporting features

---

**Built with ❤️ using Django and modern web technologies**
