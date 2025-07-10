"""
Toast notification utilities for Gurumisha Motors
Provides helper functions for consistent toast messaging across the application
"""

from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string


class ToastMixin:
    """
    Mixin for views to easily add toast notifications
    """
    
    def add_toast_success(self, message, **kwargs):
        """Add success toast message"""
        return self.add_toast_message(message, 'success', **kwargs)
    
    def add_toast_error(self, message, **kwargs):
        """Add error toast message"""
        return self.add_toast_message(message, 'error', **kwargs)
    
    def add_toast_warning(self, message, **kwargs):
        """Add warning toast message"""
        return self.add_toast_message(message, 'warning', **kwargs)
    
    def add_toast_info(self, message, **kwargs):
        """Add info toast message"""
        return self.add_toast_message(message, 'info', **kwargs)
    
    def add_toast_message(self, message, toast_type='info', **kwargs):
        """
        Add toast message that works for both HTMX and regular requests
        """
        request = getattr(self, 'request', None)
        if not request:
            return
        
        # For HTMX requests, add to response headers
        if request.headers.get('HX-Request'):
            if not hasattr(request, '_toast_messages'):
                request._toast_messages = []
            request._toast_messages.append((toast_type, message))
        else:
            # For regular requests, use Django messages
            message_level = {
                'success': messages.SUCCESS,
                'error': messages.ERROR,
                'warning': messages.WARNING,
                'info': messages.INFO,
            }.get(toast_type, messages.INFO)
            
            messages.add_message(request, message_level, message)


def toast_response(message, toast_type='info', data=None, status=200, **kwargs):
    """
    Create a JSON response with toast notification data
    Useful for AJAX/HTMX endpoints
    """
    response_data = {
        'toast': {
            'message': message,
            'type': toast_type,
            **kwargs
        }
    }
    
    if data:
        response_data.update(data)
    
    response = JsonResponse(response_data, status=status)
    
    # Add toast headers for middleware
    response[f'X-Toast-{toast_type.title()}'] = message
    
    return response


def toast_success_response(message, data=None, **kwargs):
    """Create success toast response"""
    return toast_response(message, 'success', data, **kwargs)


def toast_error_response(message, data=None, status=400, **kwargs):
    """Create error toast response"""
    return toast_response(message, 'error', data, status, **kwargs)


def toast_warning_response(message, data=None, **kwargs):
    """Create warning toast response"""
    return toast_response(message, 'warning', data, **kwargs)


def toast_info_response(message, data=None, **kwargs):
    """Create info toast response"""
    return toast_response(message, 'info', data, **kwargs)


def render_toast_partial(template_name, context=None, toast_message=None, toast_type='success'):
    """
    Render a template partial with optional toast message
    Useful for HTMX responses that need both content and notifications
    """
    html = render_to_string(template_name, context or {})
    
    response_data = {'html': html}
    
    if toast_message:
        response_data['toast'] = {
            'message': toast_message,
            'type': toast_type
        }
    
    return JsonResponse(response_data)


class ToastFormMixin:
    """
    Mixin for forms to add toast notifications on validation
    """
    
    def add_error_toast(self, message):
        """Add error toast for form validation"""
        if hasattr(self, '_toast_messages'):
            self._toast_messages.append(('error', message))
        else:
            self._toast_messages = [('error', message)]
    
    def add_success_toast(self, message):
        """Add success toast for form validation"""
        if hasattr(self, '_toast_messages'):
            self._toast_messages.append(('success', message))
        else:
            self._toast_messages = [('success', message)]
    
    def get_toast_messages(self):
        """Get all toast messages for this form"""
        return getattr(self, '_toast_messages', [])


def handle_form_errors(form, request=None):
    """
    Convert form errors to toast notifications
    """
    error_messages = []
    
    # Field errors
    for field, errors in form.errors.items():
        if field == '__all__':
            error_messages.extend(errors)
        else:
            field_label = form.fields.get(field, {}).get('label', field.title())
            for error in errors:
                error_messages.append(f"{field_label}: {error}")
    
    # Non-field errors
    for error in form.non_field_errors():
        error_messages.append(str(error))
    
    # Add to request if provided
    if request and error_messages:
        for error_msg in error_messages:
            if request.headers.get('HX-Request'):
                if not hasattr(request, '_toast_messages'):
                    request._toast_messages = []
                request._toast_messages.append(('error', error_msg))
            else:
                messages.error(request, error_msg)
    
    return error_messages


def validate_and_toast(form, request, success_message=None):
    """
    Validate form and add appropriate toast messages
    Returns True if valid, False otherwise
    """
    if form.is_valid():
        if success_message:
            if request.headers.get('HX-Request'):
                if not hasattr(request, '_toast_messages'):
                    request._toast_messages = []
                request._toast_messages.append(('success', success_message))
            else:
                messages.success(request, success_message)
        return True
    else:
        handle_form_errors(form, request)
        return False


# Decorator for views
def with_toast_messages(view_func):
    """
    Decorator to automatically handle toast messages in view responses
    """
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        
        # Add toast headers if messages exist
        if hasattr(request, '_toast_messages'):
            for message_type, message_text in request._toast_messages:
                response[f'X-Toast-{message_type.title()}'] = message_text
        
        return response
    
    return wrapper


# Context processor for toast messages
def toast_context_processor(request):
    """
    Context processor to make toast utilities available in templates
    """
    return {
        'toast_messages': getattr(request, '_toast_messages', []),
        'has_toast_messages': hasattr(request, '_toast_messages') and bool(request._toast_messages)
    }


# Error code to message mapping
ERROR_MESSAGES = {
    400: "Bad request. Please check your input.",
    401: "You need to log in to access this resource.",
    403: "You don't have permission to access this resource.",
    404: "The requested resource was not found.",
    405: "This action is not allowed.",
    422: "The data provided is invalid.",
    429: "Too many requests. Please wait before trying again.",
    500: "An internal server error occurred. Please try again later.",
    502: "Service temporarily unavailable.",
    503: "Service temporarily unavailable.",
    504: "The request timed out. Please try again.",
}


def get_error_message(status_code, default="An error occurred"):
    """Get user-friendly error message for HTTP status code"""
    return ERROR_MESSAGES.get(status_code, default)
