# Gurumisha Toast Manager Documentation

## Overview

The Gurumisha Toast Manager is a comprehensive notification system that provides consistent, user-friendly feedback across the entire application. It integrates seamlessly with Django's message framework, HTMX requests, and provides robust error handling.

## Features

- **Unified Notification System**: Consistent toast notifications across all pages
- **Harrier Design Integration**: Follows the red/black/dark blue/white color scheme
- **Django Messages Integration**: Automatically converts Django messages to toasts
- **HTMX Support**: Handles HTMX requests with appropriate headers
- **Error Handling**: Comprehensive error catching and user-friendly messages
- **Mobile Responsive**: Optimized for mobile devices
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Auto-dismiss**: Configurable auto-dismiss timing
- **Action Buttons**: Support for action buttons in toasts
- **Persistent Toasts**: Option for persistent notifications

## Installation

The toast system is automatically included in all base templates:
- `base.html`
- `base_dashboard.html` 
- `base_admin.html`

## Usage

### Basic JavaScript Usage

```javascript
// Show different types of toasts
showSuccess('Operation completed successfully!');
showError('An error occurred. Please try again.');
showWarning('Please check your input.');
showInfo('New feature available!');

// Advanced usage with options
showToast('Custom message', 'success', {
    duration: 10000,        // 10 seconds
    persistent: false,      // Auto-dismiss
    dismissible: true,      // Show close button
    action: {
        text: 'Undo',
        handler: () => {
            // Handle action
        },
        dismissOnClick: true
    }
});
```

### Django Views Integration

#### Using Toast Utilities

```python
from core.toast_utils import toast_success_response, toast_error_response, ToastMixin

# For HTMX/AJAX responses
def my_ajax_view(request):
    try:
        # Your logic here
        return toast_success_response('Operation completed!')
    except Exception as e:
        return toast_error_response('Something went wrong.')

# Using the mixin
class MyView(ToastMixin, View):
    def post(self, request):
        # Your logic here
        self.add_toast_success('Data saved successfully!')
        return redirect('some_url')
```

#### Using Django Messages

```python
from django.contrib import messages

def my_view(request):
    try:
        # Your logic here
        messages.success(request, 'Operation completed successfully!')
    except Exception as e:
        messages.error(request, 'An error occurred.')
    
    return render(request, 'template.html')
```

### Template Usage

#### Render Django Messages as Toasts

```html
{% load core_extras %}

<!-- This is automatically included in base templates -->
{% render_toast_messages %}
```

#### Manual Toast Trigger

```html
{% load core_extras %}

<!-- Show a toast on page load -->
{% show_toast_js "Welcome back!" "success" duration=5000 %}
```

## Configuration

### Toast Types and Colors

- **Success**: Green theme with check icon
- **Error**: Red theme with exclamation icon  
- **Warning**: Yellow theme with warning icon
- **Info**: Blue theme with info icon

### Default Settings

```javascript
{
    maxToasts: 5,           // Maximum number of toasts
    defaultDuration: 5000,  // 5 seconds
    dismissible: true,      // Show close button
    persistent: false       // Auto-dismiss
}
```

## Error Handling

### Automatic Error Handling

The system automatically handles:
- JavaScript errors
- Unhandled promise rejections
- HTMX request errors
- Network timeouts
- HTTP error responses

### Custom Error Messages

```python
# In views.py
from core.toast_utils import get_error_message

def my_view(request):
    try:
        # Your logic
        pass
    except ValidationError:
        error_msg = get_error_message(400)  # "Bad request. Please check your input."
        return toast_error_response(error_msg)
```

## HTMX Integration

### Response Headers

The system uses custom headers for HTMX responses:
- `X-Toast-Success`: Success message
- `X-Toast-Error`: Error message
- `X-Toast-Warning`: Warning message
- `X-Toast-Info`: Info message

### Example HTMX View

```python
def htmx_view(request):
    if request.headers.get('HX-Request'):
        # Add toast message to request
        if not hasattr(request, '_toast_messages'):
            request._toast_messages = []
        request._toast_messages.append(('success', 'Data updated!'))
        
        return render(request, 'partial.html', context)
```

## Middleware Integration

### ToastErrorHandlingMiddleware

Automatically handles exceptions and converts them to user-friendly toast messages:

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'core.middleware.ToastErrorHandlingMiddleware',
    # ... other middleware
]
```

## Form Integration

### Using ToastFormMixin

```python
from core.toast_utils import ToastFormMixin

class MyForm(ToastFormMixin, forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        if some_condition:
            self.add_error_toast('Custom validation error')
        return cleaned_data
```

### Handling Form Errors

```python
from core.toast_utils import handle_form_errors, validate_and_toast

def form_view(request):
    form = MyForm(request.POST or None)
    
    if request.method == 'POST':
        if validate_and_toast(form, request, 'Form saved successfully!'):
            # Form is valid
            return redirect('success_url')
        # Errors automatically converted to toasts
    
    return render(request, 'form.html', {'form': form})
```

## Best Practices

### 1. Message Content
- Keep messages concise and actionable
- Use clear, user-friendly language
- Avoid technical jargon

### 2. Toast Types
- **Success**: Confirm completed actions
- **Error**: Critical issues requiring attention
- **Warning**: Important information that needs consideration
- **Info**: General information or tips

### 3. Timing
- Success messages: 3-5 seconds
- Error messages: 7-10 seconds or persistent
- Warning messages: 5-7 seconds
- Info messages: 3-5 seconds

### 4. Actions
- Provide undo actions for destructive operations
- Include helpful links for error resolution
- Keep action text short and clear

## Troubleshooting

### Common Issues

1. **Toasts not appearing**
   - Check if toast manager is loaded
   - Verify template tags are included
   - Check browser console for errors

2. **Django messages not converting**
   - Ensure `{% render_toast_messages %}` is in template
   - Check middleware order
   - Verify template tag loading

3. **HTMX toasts not working**
   - Check response headers
   - Verify middleware is installed
   - Check HTMX event listeners

### Debug Mode

Enable debug logging:

```python
# settings.py
LOGGING = {
    'loggers': {
        'core.middleware': {
            'level': 'DEBUG',
        }
    }
}
```

## Examples

See the updated `contact_us` view in `core/views.py` for a complete example of toast integration.

## Migration from Old Toast Systems

The new toast manager replaces all existing toast implementations. Remove old `showMessage` and `showToast` functions from individual templates and use the global system instead.
