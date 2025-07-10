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
