"""
WSGI config for Gurumisha Motors production deployment.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

For cPanel VPS deployment, this file should be placed in the public_html directory
or configured as the WSGI application entry point.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'gurumisha'))

# Set the Django settings module for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gurumisha_project.settings_production')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except ImportError:
    # Handle import errors gracefully
    import traceback
    import logging
    
    # Log the error
    logging.error("Failed to import Django WSGI application: %s", traceback.format_exc())
    
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html')]
        start_response(status, headers)
        return [b'<h1>Server Error</h1><p>Unable to load Django application. Please check server logs.</p>']

# Optional: Add WSGI middleware for additional functionality
class WSGIMiddleware:
    """
    Custom WSGI middleware for production enhancements
    """
    def __init__(self, application):
        self.application = application
    
    def __call__(self, environ, start_response):
        # Add custom headers or processing here if needed
        return self.application(environ, start_response)

# Wrap the application with middleware if needed
# application = WSGIMiddleware(application)
