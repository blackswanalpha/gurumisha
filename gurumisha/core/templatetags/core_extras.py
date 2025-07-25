from django import template
from django.contrib import messages
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def range_filter(value):
    """Return a range from 1 to value+1"""
    return range(1, int(value) + 1)

@register.filter
def times(value):
    """Return a range from 0 to value"""
    return range(int(value))

@register.inclusion_tag('components/toast_messages.html', takes_context=True)
def render_toast_messages(context):
    """Render Django messages as toast notifications"""
    request = context.get('request')
    if not request:
        return {'messages': []}

    toast_messages = []
    for message in messages.get_messages(request):
        # Map Django message levels to toast types
        level_mapping = {
            messages.DEBUG: 'info',
            messages.INFO: 'info',
            messages.SUCCESS: 'success',
            messages.WARNING: 'warning',
            messages.ERROR: 'error',
        }

        toast_type = level_mapping.get(message.level, 'info')
        toast_messages.append({
            'message': str(message),
            'type': toast_type,
            'level': message.level,
            'tags': message.tags,
        })

    return {'messages': toast_messages}

@register.simple_tag
def toast_script():
    """Include toast manager script"""
    return mark_safe('''
        <script src="/static/js/toast-manager.js"></script>
    ''')

@register.simple_tag
def show_toast_js(message, toast_type='info', **kwargs):
    """Generate JavaScript to show a toast"""
    options = {}

    # Handle common options
    if 'duration' in kwargs:
        options['duration'] = kwargs['duration']
    if 'persistent' in kwargs:
        options['persistent'] = kwargs['persistent']
    if 'dismissible' in kwargs:
        options['dismissible'] = kwargs['dismissible']

    options_json = json.dumps(options) if options else '{}'

    return mark_safe(f'''
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (window.showToast) {{
                    showToast({json.dumps(message)}, {json.dumps(toast_type)}, {options_json});
                }}
            }});
        </script>
    ''')

@register.filter
def to_toast_type(django_message_level):
    """Convert Django message level to toast type"""
    level_mapping = {
        messages.DEBUG: 'info',
        messages.INFO: 'info',
        messages.SUCCESS: 'success',
        messages.WARNING: 'warning',
        messages.ERROR: 'error',
    }
    return level_mapping.get(django_message_level, 'info')

@register.filter
def currency_ksh(value):
    """Format currency in xxx,xxx,xxx.xx format with comma separators"""
    try:
        # Handle None or empty values
        if value is None or value == '':
            return "0.00"

        # Convert to float if it's a string
        if isinstance(value, str):
            # Remove any existing currency symbols or commas
            value = value.replace('KSH', '').replace('KSh', '').replace(',', '').strip()
            value = float(value)

        # Ensure it's a valid number
        value = float(value)

        # Format with commas and 2 decimal places
        formatted = "{:,.2f}".format(value)
        return formatted
    except (ValueError, TypeError, AttributeError):
        return "0.00"

@register.filter
def currency_ksh_no_decimals(value):
    """Format currency in xxx,xxx,xxx format with comma separators (no decimals)"""
    try:
        # Handle None or empty values
        if value is None or value == '':
            return "0"

        # Convert to float if it's a string
        if isinstance(value, str):
            # Remove any existing currency symbols or commas
            value = value.replace('KSH', '').replace('KSh', '').replace(',', '').strip()
            value = float(value)

        # Ensure it's a valid number
        value = float(value)

        # Format as integer with comma separators (no decimals)
        formatted = "{:,}".format(int(value))
        return formatted
    except (ValueError, TypeError, AttributeError):
        return "0"

@register.filter
def currency_ksh_with_symbol(value):
    """Format currency with KSh symbol in consistent format"""
    try:
        formatted_value = currency_ksh_no_decimals(value)
        return f"KSh {formatted_value}"
    except:
        return "KSh 0"

@register.filter
def add_commas(value):
    """Add comma separators to numbers"""
    try:
        # Handle None or empty values
        if value is None or value == '':
            return "0"

        # Convert to float if it's a string
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            value = float(value)

        # Ensure it's a valid number
        value = float(value)

        # Check if it's a whole number
        if value == int(value):
            return "{:,}".format(int(value))
        else:
            return "{:,.2f}".format(value)
    except (ValueError, TypeError, AttributeError):
        return "0"

@register.filter
def format_price_range(min_price, max_price):
    """Format price range for display"""
    try:
        if min_price and max_price:
            min_formatted = currency_ksh_no_decimals(min_price)
            max_formatted = currency_ksh_no_decimals(max_price)
            return f"KSh {min_formatted} - KSh {max_formatted}"
        elif min_price:
            min_formatted = currency_ksh_no_decimals(min_price)
            return f"From KSh {min_formatted}"
        elif max_price:
            max_formatted = currency_ksh_no_decimals(max_price)
            return f"Up to KSh {max_formatted}"
        else:
            return "Any Price"
    except:
        return "Any Price"
