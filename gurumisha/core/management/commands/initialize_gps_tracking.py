"""
Management command to initialize GPS tracking for existing import orders
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import ImportOrder, ImportOrderLocation, LocationTrackingHistory
from core.signals import auto_update_location_for_status, create_default_route_for_order


class Command(BaseCommand):
    help = 'Initialize GPS tracking for existing import orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if tracking data already exists',
        )
        parser.add_argument(
            '--order-number',
            type=str,
            help='Initialize tracking for a specific order number',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        order_number = options['order_number']

        self.stdout.write(
            self.style.SUCCESS('Starting GPS tracking initialization...')
        )

        # Get import orders to process
        if order_number:
            orders = ImportOrder.objects.filter(order_number=order_number)
            if not orders.exists():
                self.stdout.write(
                    self.style.ERROR(f'Order {order_number} not found')
                )
                return
        else:
            orders = ImportOrder.objects.filter(
                status__in=['confirmed', 'import_request', 'auction_won', 'shipped', 'in_transit',
                           'arrived_docked', 'under_clearance', 'registered', 'ready_for_dispatch']
            ).exclude(status='delivered')

        total_orders = orders.count()
        self.stdout.write(f'Found {total_orders} orders to process')

        processed = 0
        skipped = 0
        errors = 0

        for order in orders:
            try:
                # Check if tracking is already enabled
                if not order.tracking_enabled:
                    if dry_run:
                        self.stdout.write(f'Would enable tracking for {order.order_number}')
                    else:
                        order.tracking_enabled = True
                        order.save(update_fields=['tracking_enabled'])
                        self.stdout.write(f'Enabled tracking for {order.order_number}')

                # Check if location data exists
                has_location = (order.current_latitude and order.current_longitude) or \
                              order.locations.exists()

                if not has_location or force:
                    if dry_run:
                        self.stdout.write(f'Would initialize location for {order.order_number}')
                    else:
                        # Initialize location based on current status
                        auto_update_location_for_status(order)
                        
                        # Create initial tracking history entry
                        LocationTrackingHistory.objects.get_or_create(
                            import_order=order,
                            status_at_time=order.status,
                            defaults={
                                'latitude': order.current_latitude or 0,
                                'longitude': order.current_longitude or 0,
                                'tracking_source': 'manual',
                                'notes': f'Initial GPS tracking setup for status: {order.status}',
                                'recorded_at': timezone.now(),
                            }
                        )
                        
                        self.stdout.write(f'Initialized location for {order.order_number}')

                # Check if route exists
                if not hasattr(order, 'route') or not order.route:
                    if dry_run:
                        self.stdout.write(f'Would create route for {order.order_number}')
                    else:
                        create_default_route_for_order(order)
                        self.stdout.write(f'Created route for {order.order_number}')
                else:
                    if not force:
                        self.stdout.write(f'Route already exists for {order.order_number}')
                        skipped += 1
                        continue

                processed += 1

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing {order.order_number}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('GPS Tracking Initialization Complete'))
        self.stdout.write(f'Total orders found: {total_orders}')
        self.stdout.write(f'Successfully processed: {processed}')
        self.stdout.write(f'Skipped (already configured): {skipped}')
        self.stdout.write(f'Errors: {errors}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('GPS tracking has been initialized for import orders')
            )

        # Additional statistics
        if not dry_run:
            total_tracked = ImportOrder.objects.filter(tracking_enabled=True).count()
            total_with_location = ImportOrder.objects.filter(
                tracking_enabled=True,
                current_latitude__isnull=False,
                current_longitude__isnull=False
            ).count()
            total_with_routes = ImportOrder.objects.filter(
                tracking_enabled=True,
                route__isnull=False
            ).count()

            self.stdout.write('\nCurrent GPS Tracking Statistics:')
            self.stdout.write(f'Orders with tracking enabled: {total_tracked}')
            self.stdout.write(f'Orders with location data: {total_with_location}')
            self.stdout.write(f'Orders with routes: {total_with_routes}')
            
            if total_tracked > 0:
                coverage = (total_with_location / total_tracked) * 100
                self.stdout.write(f'Location coverage: {coverage:.1f}%')
