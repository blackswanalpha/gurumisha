# 🍞 Gurumisha Toast Manager System

## 🎯 Overview

A comprehensive, production-ready toast notification system for the Gurumisha Motors Django application. This system provides unified, consistent, and user-friendly feedback across the entire application with seamless integration for Django messages, HTMX requests, and robust error handling.

## ✨ Features

### 🎨 Design & UX
- **Harrier Design Integration**: Follows the red/black/dark blue/white color scheme
- **Mobile-First Responsive**: Optimized animations and positioning for all devices
- **Accessibility Compliant**: ARIA labels, keyboard navigation, high contrast support
- **Smooth Animations**: CSS3 transitions with reduced motion support

### 🔧 Technical Features
- **Django Messages Integration**: Automatic conversion of Django messages to toasts
- **HTMX Support**: Custom headers and event handling for HTMX requests
- **Error Handling**: Comprehensive error catching with user-friendly messages
- **TypeScript-Ready**: Well-structured JavaScript with clear interfaces
- **Performance Optimized**: Efficient DOM manipulation and memory management

### 🎛️ Configuration Options
- **Auto-dismiss**: Configurable timing (default: 5 seconds)
- **Persistent Toasts**: Option for manual dismissal only
- **Action Buttons**: Support for interactive toast actions
- **Toast Limits**: Maximum number of simultaneous toasts (default: 5)
- **Custom Positioning**: Flexible positioning system

## 📁 File Structure

```
gurumisha/
├── static/
│   ├── js/
│   │   └── toast-manager.js          # Main toast manager class
│   └── css/
│       └── toast-animations.css      # Toast styling and animations
├── core/
│   ├── templatetags/
│   │   └── core_extras.py           # Django template tags
│   ├── middleware.py                # Error handling middleware
│   ├── toast_utils.py              # Utility functions and mixins
│   └── views.py                    # Example implementation
├── templates/
│   ├── components/
│   │   └── toast_messages.html     # Django messages component
│   ├── core/
│   │   └── toast_test.html         # Test page
│   ├── base.html                   # Main base template
│   ├── base_dashboard.html         # Dashboard base template
│   └── base_admin.html             # Admin base template
└── docs/
    └── TOAST_SYSTEM.md             # Detailed documentation
```

## 🚀 Quick Start

### 1. Basic JavaScript Usage

```javascript
// Simple toast notifications
showSuccess('Operation completed successfully!');
showError('An error occurred. Please try again.');
showWarning('Please check your input.');
showInfo('New feature available!');

// Advanced usage
showToast('Custom message', 'success', {
    duration: 10000,
    persistent: false,
    dismissible: true,
    action: {
        text: 'Undo',
        handler: () => console.log('Undo clicked'),
        dismissOnClick: true
    }
});
```

### 2. Django Views Integration

```python
from core.toast_utils import toast_success_response, ToastMixin
from django.contrib import messages

# HTMX/AJAX responses
def my_ajax_view(request):
    try:
        # Your logic here
        return toast_success_response('Operation completed!')
    except Exception as e:
        return toast_error_response('Something went wrong.')

# Using the mixin
class MyView(ToastMixin, View):
    def post(self, request):
        self.add_toast_success('Data saved successfully!')
        return redirect('some_url')

# Traditional Django messages
def my_view(request):
    messages.success(request, 'Operation completed!')
    return render(request, 'template.html')
```

### 3. Template Usage

```html
{% load core_extras %}

<!-- Automatic Django messages (included in base templates) -->
{% render_toast_messages %}

<!-- Manual toast trigger -->
{% show_toast_js "Welcome back!" "success" duration=5000 %}
```

## 🎨 Toast Types & Colors

| Type | Color | Icon | Use Case |
|------|-------|------|----------|
| **Success** | Green | ✅ | Confirm completed actions |
| **Error** | Red | ❌ | Critical issues requiring attention |
| **Warning** | Yellow | ⚠️ | Important information needing consideration |
| **Info** | Blue | ℹ️ | General information or tips |

## 🔧 Configuration

### Default Settings
```javascript
{
    maxToasts: 5,           // Maximum simultaneous toasts
    defaultDuration: 5000,  // Auto-dismiss time (ms)
    dismissible: true,      // Show close button
    persistent: false       // Auto-dismiss enabled
}
```

### Timing Recommendations
- **Success**: 3-5 seconds
- **Error**: 7-10 seconds or persistent
- **Warning**: 5-7 seconds
- **Info**: 3-5 seconds

## 🛠️ Error Handling

### Automatic Error Handling
The system automatically handles:
- JavaScript runtime errors
- Unhandled promise rejections
- HTMX request failures
- Network timeouts
- HTTP error responses (400, 401, 403, 404, 500, etc.)

### Custom Error Messages
```python
from core.toast_utils import get_error_message

error_msg = get_error_message(404)  # "The requested resource was not found."
```

## 🔌 HTMX Integration

### Response Headers
- `X-Toast-Success`: Success message
- `X-Toast-Error`: Error message
- `X-Toast-Warning`: Warning message
- `X-Toast-Info`: Info message

### Example HTMX View
```python
def htmx_view(request):
    if request.headers.get('HX-Request'):
        # Add toast message
        if not hasattr(request, '_toast_messages'):
            request._toast_messages = []
        request._toast_messages.append(('success', 'Data updated!'))
        return render(request, 'partial.html')
```

## 🧪 Testing

Visit the test page at `/toast-test/` to:
- Test all toast types
- Try JavaScript and Django/HTMX integration
- Simulate error conditions
- Test mobile responsiveness
- Verify accessibility features

## 📱 Mobile Support

- **Responsive Positioning**: Adapts to screen size
- **Touch-Friendly**: Optimized for mobile interactions
- **Performance**: Efficient animations on mobile devices
- **Accessibility**: Screen reader and keyboard navigation support

## 🎯 Best Practices

### Message Content
- Keep messages concise and actionable
- Use clear, user-friendly language
- Avoid technical jargon
- Provide helpful next steps

### Usage Guidelines
- Use success toasts to confirm actions
- Use error toasts for critical issues
- Use warning toasts for important information
- Use info toasts for general notifications

### Performance
- Limit simultaneous toasts (max 5)
- Use appropriate durations
- Clear toasts when navigating away
- Avoid toast spam

## 🔄 Migration from Old Systems

The new toast manager replaces all existing toast implementations:

1. Remove old `showMessage` and `showToast` functions
2. Update views to use new utilities
3. Replace inline toast code with global system
4. Update templates to use new template tags

## 🐛 Troubleshooting

### Common Issues

1. **Toasts not appearing**
   - Check browser console for errors
   - Verify toast manager is loaded
   - Ensure template tags are included

2. **Django messages not converting**
   - Check `{% render_toast_messages %}` in template
   - Verify middleware order
   - Check template tag loading

3. **HTMX toasts not working**
   - Verify response headers
   - Check middleware installation
   - Verify HTMX event listeners

### Debug Mode
Enable debug logging in `settings.py`:
```python
LOGGING = {
    'loggers': {
        'core.middleware': {'level': 'DEBUG'}
    }
}
```

## 📊 System Status

✅ **Implemented Features:**
- Complete toast manager system
- Django integration
- HTMX support
- Error handling middleware
- Template tags and utilities
- Mobile responsive design
- Accessibility features
- Test page and documentation

🎯 **Ready for Production:**
- All base templates updated
- Middleware configured
- CSS animations optimized
- Error handling comprehensive
- Documentation complete

## 🤝 Contributing

When adding new features:
1. Update the toast manager class
2. Add corresponding CSS animations
3. Update template tags if needed
4. Add tests to the test page
5. Update documentation

---

**🎉 The Gurumisha Toast Manager is now fully operational and ready to provide excellent user feedback across your entire application!**
