# 🚗 Gurumisha Motors - Premium Automotive Marketplace

A comprehensive Django monolithic e-commerce system for automotive marketplace, built with modern web technologies and best practices.

## 🌟 Features

### 🏠 **Homepage with 13 Sections**
1. **Navigation Bar** - Responsive with mobile menu
2. **Hero Section** - Video background with search functionality
3. **Browse by Vehicle Type** - Interactive category cards
4. **Site Features Overview** - Key platform benefits
5. **Featured Cars Showcase** - Dynamic car listings
6. **Why Choose Us** - Trust-building elements
7. **Car Brands Display** - Brand showcase
8. **Sell Your Car CTA** - Prominent call-to-action
9. **Hot Deals Section** - Special offers
10. **Spare Parts Preview** - Parts categories
11. **Customer Testimonials** - Reviews and ratings
12. **Blog Preview** - Latest articles
13. **Footer** - Comprehensive links and contact info

### 🚙 **Car Management**
- Advanced car listings with detailed specifications
- Image galleries with multiple photos per car
- Advanced filtering (brand, price, year, fuel type, transmission)
- Car detail pages with inquiry system
- Featured car highlighting
- Vendor management and verification

### 🔧 **Spare Parts System**
- Comprehensive parts catalog
- Brand compatibility tracking
- Category-based organization
- Stock management
- Vendor-specific parts

### 👥 **User Management**
- Role-based access (Customer, Vendor, Admin)
- User authentication and profiles
- Vendor verification system
- Customer inquiry management

### 📝 **Content Management**
- Blog system for automotive content
- Customer testimonials
- SEO-optimized pages
- Contact forms with HTMX

### 🚢 **Import Services**
- Car import request tracking
- Multi-country support
- Status tracking system

## 🛠 **Technology Stack**

### **Backend**
- **Django 5.2.4** - Web framework
- **Python 3.10+** - Programming language
- **SQLite** - Database (development)

### **Frontend**
- **Tailwind CSS** - Utility-first CSS framework
- **HTMX** - Dynamic interactions without JavaScript
- **Font Awesome** - Icons
- **Google Fonts** - Typography (DM Sans, Inter)

### **Design**
- **Semantic HTML5** - Proper markup structure
- **Mobile-first responsive design**
- **Custom color palette** (Midnight, Crimson, Deep Ocean)
- **Smooth animations and transitions**

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10 or higher
- pip (Python package manager)

### **Installation**

1. **Navigate to the project directory:**
   ```bash
   cd gurumisha
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies (already installed):**
   ```bash
   pip install django django-tailwind django-htmx pillow
   ```

4. **Run migrations (already done):**
   ```bash
   python manage.py migrate
   ```

5. **Create test accounts (optional):**
   ```bash
   python manage.py create_auth_test_accounts
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Visit the application:**
   - Homepage: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin/

### **Admin Access**
- **Username:** admin
- **Password:** admin123

## 📁 **Project Structure**

```
gurumisha/
├── core/                          # Main Django app
│   ├── models.py                  # Database models
│   ├── views.py                   # View logic
│   ├── admin.py                   # Admin configuration
│   ├── urls.py                    # URL routing
│   ├── management/commands/       # Custom management commands
│   └── templatetags/              # Custom template filters
├── templates/                     # HTML templates
│   ├── base.html                  # Base template
│   ├── core/                      # App-specific templates
│   └── partials/                  # HTMX partial templates
├── static/                        # Static files
│   └── images/                    # Image assets
├── gurumisha_project/             # Django project settings
└── manage.py                      # Django management script
```

## 🎨 **Design System**

### **Colors**
- **Midnight:** #0A0A0A (Primary dark)
- **Carbon:** #1A1A1A (Secondary dark)
- **Crimson:** #DC2626 (Primary accent)
- **Electric Red:** #EF4444 (Secondary accent)
- **Deep Ocean:** #1E3A8A (Blue primary)
- **Azure:** #3B82F6 (Blue secondary)

### **Typography**
- **Headings:** DM Sans (400, 500, 600, 700, 800)
- **Body:** Inter (300, 400, 500, 600, 700)

### **Components**
- Responsive navigation with mobile menu
- Card-based layouts
- Button variants (primary, secondary)
- Form styling with focus states
- Modal dialogs
- Loading states

## 📊 **Database Models**

### **Core Models**
- **User** - Extended user with roles
- **Vendor** - Dealer profiles
- **CarBrand/CarModel** - Vehicle hierarchy
- **Car** - Vehicle listings
- **CarImage** - Multiple images per car
- **SparePart** - Parts inventory
- **Inquiry/Message** - Communication system
- **Testimonial** - Customer reviews
- **BlogPost** - Content management
- **ImportRequest** - Import tracking

## 🔧 **Key Features**

### **HTMX Integration**
- Dynamic form submissions
- Partial page updates
- Modal interactions
- Real-time feedback

### **Responsive Design**
- Mobile-first approach
- Breakpoint system (sm, md, lg, xl)
- Touch-friendly interfaces
- Optimized images

### **SEO Optimization**
- Semantic HTML structure
- Meta tags and descriptions
- Clean URL structure
- Sitemap ready

## 🧪 **Testing**

Run the test script to verify all pages:
```bash
python test_pages.py
```

## 📈 **Performance**

### **Optimizations**
- Efficient database queries
- Image optimization
- CSS/JS minification ready
- Caching strategies implemented

### **Metrics**
- All pages load successfully (200 status)
- Responsive design tested
- Cross-browser compatibility
- Mobile performance optimized

## 🚀 **Deployment Ready**

The application is production-ready with:
- Environment-based settings
- Static file handling
- Database migrations
- Error handling
- Security best practices

## 📝 **License**

This project is built for educational and demonstration purposes.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Built with ❤️ using Django, Tailwind CSS, and HTMX**
