"""
Custom middleware for Gurumisha Motors
"""
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse
from django.conf import settings
from django.urls import resolve, Resolver404, reverse
from django.contrib import messages
import logging
import traceback


class Custom404Middleware:
    """
    Middleware to handle 404 errors in DEBUG mode
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if we should show custom 404 page
        if (response.status_code == 404 and
            getattr(settings, 'SHOW_CUSTOM_404', False) and
            settings.DEBUG):
            return render(request, 'core/404.html', status=404)

        return response

    def process_exception(self, request, exception):
        """
        Handle 404 exceptions even in DEBUG mode
        """
        if (isinstance(exception, (Http404, Resolver404)) and
            getattr(settings, 'SHOW_CUSTOM_404', False)):
            return render(request, 'core/404.html', status=404)
        return None


class ToastErrorHandlingMiddleware:
    """
    Middleware to handle errors and integrate with toast notification system
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        response = self.get_response(request)

        # Add toast headers for HTMX requests
        if hasattr(request, '_toast_messages'):
            for message_type, message_text in request._toast_messages:
                response[f'X-Toast-{message_type.title()}'] = message_text

        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions and provide appropriate error messages
        """
        self.logger.error(f"Exception in {request.path}: {str(exception)}")
        self.logger.error(traceback.format_exc())

        # For HTMX requests, return JSON with error info
        if request.headers.get('HX-Request'):
            error_message = self.get_user_friendly_error(exception)

            # Add toast message
            if not hasattr(request, '_toast_messages'):
                request._toast_messages = []
            request._toast_messages.append(('error', error_message))

            return JsonResponse({
                'error': True,
                'message': error_message,
                'toast': {
                    'type': 'error',
                    'message': error_message
                }
            }, status=500)

        # For regular requests, add message and let Django handle
        error_message = self.get_user_friendly_error(exception)
        messages.error(request, error_message)

        return None

    def get_user_friendly_error(self, exception):
        """
        Convert technical exceptions to user-friendly messages
        """
        error_messages = {
            'ValidationError': 'Please check your input and try again.',
            'PermissionDenied': 'You do not have permission to perform this action.',
            'ObjectDoesNotExist': 'The requested item was not found.',
            'IntegrityError': 'This action conflicts with existing data.',
            'ConnectionError': 'Unable to connect to the service. Please try again.',
            'TimeoutError': 'The request timed out. Please try again.',
        }

        exception_name = exception.__class__.__name__

        # Return specific message if available
        if exception_name in error_messages:
            return error_messages[exception_name]

        # For development, show more details
        if settings.DEBUG:
            return f"Error: {str(exception)}"

        # Generic message for production
        return "An unexpected error occurred. Please try again or contact support."


def add_toast_message(request, message_type, message_text):
    """
    Helper function to add toast messages to request
    """
    if not hasattr(request, '_toast_messages'):
        request._toast_messages = []
    request._toast_messages.append((message_type, message_text))


class ActivityTrackingMiddleware:
    """
    Middleware to automatically track user activities
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track page views for authenticated users
        if request.user.is_authenticated and request.method == 'GET':
            self.track_page_view(request)

        response = self.get_response(request)
        return response

    def track_page_view(self, request):
        """Track page views"""
        try:
            from .activity_manager import ActivityManager

            # Skip tracking for certain paths
            skip_paths = [
                '/static/',
                '/media/',
                '/favicon.ico',
                '/admin/',
                '/api/',
            ]

            if any(request.path.startswith(path) for path in skip_paths):
                return

            # Skip AJAX/HTMX requests for page views
            if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return

            ActivityManager.log_activity(
                user=request.user,
                action='page_view',
                description=f"Viewed page: {request.path}",
                extra_data={
                    'path': request.path,
                    'query_params': dict(request.GET),
                },
                request=request
            )
        except Exception as e:
            # Silently fail to avoid breaking the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to track page view: {e}")


class AuditTrackingMiddleware:
    """
    Middleware to track audit events for sensitive operations
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Track sensitive operations
        if request.user.is_authenticated:
            self.track_sensitive_operations(request, response)

        return response

    def track_sensitive_operations(self, request, response):
        """Track sensitive operations"""
        from .activity_manager import AuditManager

        # Track admin operations
        if request.path.startswith('/admin/') and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                AuditManager.log_audit(
                    user=request.user,
                    action_type='system_config',
                    description=f"Admin operation: {request.method} {request.path}",
                    severity='medium',
                    request=request
                )
            except Exception:
                pass

        # Track login/logout
        if 'login' in request.path and request.method == 'POST' and response.status_code == 302:
            try:
                AuditManager.log_audit(
                    user=request.user,
                    action_type='login',
                    description=f"User login: {request.user.username}",
                    severity='low',
                    request=request
                )
            except Exception:
                pass


class EmailVerificationMiddleware:
    """
    Middleware to check email verification for authenticated users
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs that don't require email verification
        self.exempt_urls = [
            '/admin/',  # Django admin
            '/static/',  # Static files
            '/media/',   # Media files
        ]

        # URL patterns that don't require email verification
        self.exempt_patterns = [
            'core:homepage',
            'core:login',
            'core:register',
            'core:logout',
            'core:forgot_password',
            'core:password_reset_done',
            'core:password_reset_complete',
            'core:resend_verification',
            'core:email_verification_sent',
            'core:email_verification_required',
            'core:contact_us',
            'core:about_us',
            'core:car_list',
            'core:spare_parts',
            'core:resources',
        ]

    def __call__(self, request):
        # Check if user is authenticated and email verification is required
        if (request.user.is_authenticated and
            hasattr(request.user, 'is_email_verified') and
            not request.user.is_email_verified and
            getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', True)):

            # Check if current URL requires email verification
            current_path = request.path

            # Skip verification check for exempt URLs
            if any(current_path.startswith(exempt_url) for exempt_url in self.exempt_urls):
                response = self.get_response(request)
                return response

            # Skip for verify email URLs (contains token)
            if '/verify-email/' in current_path:
                response = self.get_response(request)
                return response

            # Skip for password reset URLs (contains token)
            if '/password-reset-confirm/' in current_path:
                response = self.get_response(request)
                return response

            # Check URL patterns
            try:
                resolved = resolve(current_path)
                url_name = f"{resolved.namespace}:{resolved.url_name}" if resolved.namespace else resolved.url_name

                if url_name in self.exempt_patterns:
                    response = self.get_response(request)
                    return response
            except:
                pass

            # Skip for AJAX requests
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                messages.warning(
                    request,
                    'Please verify your email address to access this feature. '
                    'Check your inbox for the verification link.'
                )
                return redirect('core:email_verification_required')

        response = self.get_response(request)
        return response


class SessionSecurityMiddleware:
    """
    Enhanced session security middleware for remember me functionality
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Enhanced session security
        if request.user.is_authenticated:
            # Check for session hijacking
            if 'user_agent' in request.session:
                if request.session['user_agent'] != request.META.get('HTTP_USER_AGENT', ''):
                    # Potential session hijacking
                    request.session.flush()
                    messages.error(request, 'Your session has been terminated for security reasons.')
                    return redirect('core:login')
            else:
                # Store user agent for session validation
                request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

            # Update last activity
            request.session['last_activity'] = request.session.get('last_activity', 0)

        response = self.get_response(request)
        return response
