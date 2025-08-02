"""
HTMX Helper Functions for Enhanced Error Handling and Response Management
"""
import logging
import json
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DatabaseError
from functools import wraps

logger = logging.getLogger(__name__)


def htmx_error_handler(template_name='components/htmx_error.html'):
    """
    Decorator for HTMX views to handle errors gracefully
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {view_func.__name__}: {e}")
                return htmx_error_response(
                    request, 
                    str(e), 
                    template_name=template_name,
                    error_type='validation'
                )
            except IntegrityError as e:
                logger.error(f"Database integrity error in {view_func.__name__}: {e}")
                return htmx_error_response(
                    request, 
                    "A database error occurred. Please try again.", 
                    template_name=template_name,
                    error_type='database'
                )
            except DatabaseError as e:
                logger.error(f"Database error in {view_func.__name__}: {e}")
                return htmx_error_response(
                    request, 
                    "Database connection error. Please try again later.", 
                    template_name=template_name,
                    error_type='database'
                )
            except PermissionError as e:
                logger.warning(f"Permission error in {view_func.__name__}: {e}")
                return htmx_error_response(
                    request, 
                    "You don't have permission to perform this action.", 
                    template_name=template_name,
                    error_type='permission'
                )
            except Exception as e:
                logger.error(f"Unexpected error in {view_func.__name__}: {e}", exc_info=True)
                return htmx_error_response(
                    request, 
                    "An unexpected error occurred. Please try again.", 
                    template_name=template_name,
                    error_type='general'
                )
        return wrapper
    return decorator


def htmx_error_response(request, message, template_name='components/htmx_error.html', error_type='general', status_code=400):
    """
    Generate standardized HTMX error response
    """
    context = {
        'error_message': message,
        'error_type': error_type,
        'is_htmx': request.headers.get('HX-Request'),
    }
    
    # Add error-specific styling
    error_styles = {
        'validation': 'border-yellow-500 bg-yellow-50 text-yellow-800',
        'database': 'border-red-500 bg-red-50 text-red-800',
        'permission': 'border-orange-500 bg-orange-50 text-orange-800',
        'general': 'border-gray-500 bg-gray-50 text-gray-800',
    }
    context['error_style'] = error_styles.get(error_type, error_styles['general'])
    
    if request.headers.get('HX-Request'):
        # Return HTML fragment for HTMX
        html = render_to_string(template_name, context, request=request)
        response = HttpResponse(html, status=status_code)
        response['HX-Retarget'] = '#error-container'
        response['HX-Reswap'] = 'innerHTML'
        return response
    else:
        # Return JSON for regular AJAX requests
        return JsonResponse({
            'success': False,
            'error': message,
            'error_type': error_type
        }, status=status_code)


def htmx_success_response(request, message, template_name=None, context=None, target=None):
    """
    Generate standardized HTMX success response
    """
    if context is None:
        context = {}
    
    context.update({
        'success_message': message,
        'is_htmx': request.headers.get('HX-Request'),
    })
    
    if request.headers.get('HX-Request') and template_name:
        # Return HTML fragment for HTMX
        html = render_to_string(template_name, context, request=request)
        response = HttpResponse(html)
        if target:
            response['HX-Retarget'] = target
        return response
    else:
        # Return JSON for regular AJAX requests
        return JsonResponse({
            'success': True,
            'message': message,
            **context
        })


def htmx_modal_response(request, modal_id, content_template, context=None, modal_title=None, auto_show=True):
    """
    Generate HTMX out-of-band modal response

    Args:
        request: HTTP request object
        modal_id: ID of the modal to update
        content_template: Template for modal content
        context: Template context
        modal_title: Optional modal title
        auto_show: Whether to auto-show the modal
    """
    if context is None:
        context = {}

    context.update({
        'modal_id': modal_id,
        'modal_title': modal_title,
        'is_htmx': request.headers.get('HX-Request'),
    })

    # Render modal content
    modal_content = render_to_string(content_template, context, request=request)

    # Create OOB response
    oob_attributes = ['hx-swap-oob="innerHTML"']
    if auto_show:
        oob_attributes.append('data-auto-show="true"')

    oob_response = f'''
    <div id="{modal_id}-body" {' '.join(oob_attributes)}>
        {modal_content}
    </div>
    '''

    return HttpResponse(oob_response)


def htmx_modal_form_response(request, form, modal_id, success_template, error_template,
                           success_message=None, context=None):
    """
    Handle form responses for modal submissions with OOB updates
    """
    if context is None:
        context = {}

    context['form'] = form
    context['modal_id'] = modal_id

    if form.is_valid():
        # Success response with OOB update
        if success_message:
            context['success_message'] = success_message

        modal_content = render_to_string(success_template, context, request=request)

        oob_response = f'''
        <div id="{modal_id}-body" hx-swap-oob="innerHTML">
            {modal_content}
        </div>
        '''

        response = HttpResponse(oob_response)

        # Optionally close modal after success
        if context.get('close_modal_on_success', True):
            response['HX-Trigger'] = f'closeModal:{modal_id}'

        return response
    else:
        # Error response with form errors
        context['form_errors'] = get_htmx_form_errors(form)
        modal_content = render_to_string(error_template, context, request=request)

        oob_response = f'''
        <div id="{modal_id}-body" hx-swap-oob="innerHTML">
            {modal_content}
        </div>
        '''

        return HttpResponse(oob_response, status=400)


def htmx_oob_update(target_id, content, swap_type='innerHTML'):
    """
    Create an out-of-band update for any element

    Args:
        target_id: ID of element to update
        content: HTML content to swap
        swap_type: Type of swap (innerHTML, outerHTML, afterend, beforeend)
    """
    return f'<div id="{target_id}" hx-swap-oob="{swap_type}">{content}</div>'


def htmx_multiple_oob_response(updates):
    """
    Create response with multiple out-of-band updates

    Args:
        updates: List of dicts with 'target_id', 'content', and optional 'swap_type'
    """
    oob_parts = []

    for update in updates:
        target_id = update['target_id']
        content = update['content']
        swap_type = update.get('swap_type', 'innerHTML')

        oob_parts.append(htmx_oob_update(target_id, content, swap_type))

    return HttpResponse('\n'.join(oob_parts))


def htmx_toast_oob_response(message, toast_type='info', additional_updates=None):
    """
    Create OOB response that shows a toast notification

    Args:
        message: Toast message
        toast_type: Type of toast (success, error, warning, info)
        additional_updates: Optional list of additional OOB updates
    """
    toast_html = f'''
    <div class="toast toast-{toast_type} animate-slide-in-right"
         x-data="{{ show: true }}"
         x-show="show"
         x-init="setTimeout(() => show = false, 5000)">
        <div class="toast-content">
            <i class="fas fa-{get_toast_icon(toast_type)} mr-2"></i>
            {message}
        </div>
        <button @click="show = false" class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    </div>
    '''

    updates = [{'target_id': 'toast-container', 'content': toast_html, 'swap_type': 'afterbegin'}]

    if additional_updates:
        updates.extend(additional_updates)

    return htmx_multiple_oob_response(updates)


def get_toast_icon(toast_type):
    """Get appropriate icon for toast type"""
    icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    }
    return icons.get(toast_type, 'info-circle')


def htmx_button_update_oob(button_id, new_text, new_class='', disabled=False):
    """
    Create OOB update for button state without replacing the entire button
    """
    disabled_attr = 'disabled' if disabled else ''

    button_content = f'''
    <span class="button-text">{new_text}</span>
    '''

    # Update button content and attributes
    updates = [
        {
            'target_id': f'{button_id}-content',
            'content': button_content,
            'swap_type': 'innerHTML'
        }
    ]

    if new_class:
        # Update button class via attribute
        class_update = f'<div hx-swap-oob="setAttribute:class:{new_class}" id="{button_id}"></div>'
        updates.append({
            'target_id': 'temp-class-update',
            'content': class_update,
            'swap_type': 'innerHTML'
        })

    return htmx_multiple_oob_response(updates)


def validate_htmx_request(request, required_method='POST'):
    """
    Validate HTMX request and method
    """
    if not request.headers.get('HX-Request'):
        raise ValidationError("This endpoint only accepts HTMX requests")
    
    if request.method != required_method:
        raise ValidationError(f"This endpoint only accepts {required_method} requests")
    
    return True


def get_htmx_form_errors(form):
    """
    Extract form errors in a format suitable for HTMX responses
    """
    errors = {}
    for field, error_list in form.errors.items():
        errors[field] = [str(error) for error in error_list]
    return errors


def htmx_form_response(request, form, template_name, success_message=None, context=None):
    """
    Handle form responses for HTMX requests
    """
    if context is None:
        context = {}
    
    context['form'] = form
    
    if form.is_valid():
        if success_message:
            context['success_message'] = success_message
        return htmx_success_response(request, success_message or "Form submitted successfully", template_name, context)
    else:
        context['form_errors'] = get_htmx_form_errors(form)
        return htmx_error_response(request, "Please correct the errors below", template_name)


def log_htmx_request(request, view_name, extra_data=None):
    """
    Log HTMX request for debugging
    """
    log_data = {
        'view': view_name,
        'method': request.method,
        'user': request.user.username if request.user.is_authenticated else 'Anonymous',
        'ip': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
        'htmx_request': bool(request.headers.get('HX-Request')),
        'htmx_target': request.headers.get('HX-Target'),
        'htmx_trigger': request.headers.get('HX-Trigger'),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"HTMX Request: {json.dumps(log_data)}")


def htmx_redirect(url, push_url=True):
    """
    Create HTMX redirect response
    """
    response = HttpResponse()
    response['HX-Redirect'] = url
    if push_url:
        response['HX-Push-Url'] = url
    return response


def htmx_refresh():
    """
    Create HTMX refresh response
    """
    response = HttpResponse()
    response['HX-Refresh'] = 'true'
    return response


def htmx_trigger_event(event_name, event_data=None):
    """
    Create HTMX trigger event response
    """
    response = HttpResponse()
    if event_data:
        response['HX-Trigger'] = json.dumps({event_name: event_data})
    else:
        response['HX-Trigger'] = event_name
    return response
