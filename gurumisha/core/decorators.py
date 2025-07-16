from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def htmx_login_required(view_func):
    """
    Decorator for HTMX views that require authentication.
    Returns appropriate response for HTMX requests instead of redirecting.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('HX-Request'):
                # For HTMX requests, return empty response or error message
                return HttpResponse('', status=401)
            else:
                # For regular requests, redirect to login
                return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def htmx_staff_required(view_func):
    """
    Decorator for HTMX views that require staff access.
    Returns appropriate response for HTMX requests instead of redirecting.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('HX-Request'):
                return HttpResponse('', status=401)
            else:
                return redirect('core:login')
        
        if not request.user.is_staff:
            if request.headers.get('HX-Request'):
                return HttpResponse('', status=403)
            else:
                messages.error(request, 'Access denied. Staff privileges required.')
                return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def htmx_admin_required(view_func):
    """
    Decorator for HTMX views that require admin access.
    Returns appropriate response for HTMX requests instead of redirecting.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('HX-Request'):
                return HttpResponse('', status=401)
            else:
                return redirect('core:login')
        
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'admin'):
            if request.headers.get('HX-Request'):
                return HttpResponse('', status=403)
            else:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_login_required(view_func):
    """
    Decorator for AJAX/API views that require authentication.
    Returns JSON response for unauthenticated requests.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required',
                'redirect': '/login/'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def vendor_required(view_func):
    """
    Decorator that requires user to be a vendor.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if not hasattr(request.user, 'vendor') or not request.user.vendor.is_approved:
            messages.error(request, 'Vendor access required.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    """
    Decorator that requires user to be a customer.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        
        if getattr(request.user, 'role', None) not in ['customer', 'vendor']:
            messages.error(request, 'Customer access required.')
            return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
