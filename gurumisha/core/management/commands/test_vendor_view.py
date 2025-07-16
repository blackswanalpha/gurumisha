from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.dashboard_views import vendor_listings_view

User = get_user_model()

class Command(BaseCommand):
    help = 'Test vendor listings view for recursion issues'

    def handle(self, *args, **options):
        try:
            # Create a test request
            factory = RequestFactory()
            request = factory.get('/dashboard/vendor/listings/')
            
            # Find a vendor user
            vendor_user = User.objects.filter(role='vendor').first()
            
            if not vendor_user:
                self.stdout.write(self.style.ERROR('No vendor user found'))
                return
            
            # Set the user on the request
            request.user = vendor_user
            
            self.stdout.write(f'Testing with vendor user: {vendor_user.username}')
            
            # Call the view
            response = vendor_listings_view(request)
            
            self.stdout.write(self.style.SUCCESS(f'View executed successfully! Status: {response.status_code}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
