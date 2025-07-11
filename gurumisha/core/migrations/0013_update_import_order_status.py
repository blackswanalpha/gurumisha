# Generated by Django 5.2 on 2025-07-11 00:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_shipped_arrived_statuses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importorder',
            name='status',
            field=models.CharField(choices=[('import_request', 'Import Request'), ('auction_won', 'Auction Won'), ('shipped', 'Shipped'), ('in_transit', 'In Transit'), ('arrived_docked', 'Arrived - Docked'), ('under_clearance', 'Under Clearance'), ('registered', 'Registered'), ('ready_for_dispatch', 'Ready for Dispatch'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='import_request', max_length=30),
        ),
        migrations.AlterField(
            model_name='importorderstatushistory',
            name='new_status',
            field=models.CharField(choices=[('import_request', 'Import Request'), ('auction_won', 'Auction Won'), ('shipped', 'Shipped'), ('in_transit', 'In Transit'), ('arrived_docked', 'Arrived - Docked'), ('under_clearance', 'Under Clearance'), ('registered', 'Registered'), ('ready_for_dispatch', 'Ready for Dispatch'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], max_length=30),
        ),
        migrations.AlterField(
            model_name='importorderstatushistory',
            name='previous_status',
            field=models.CharField(blank=True, choices=[('import_request', 'Import Request'), ('auction_won', 'Auction Won'), ('shipped', 'Shipped'), ('in_transit', 'In Transit'), ('arrived_docked', 'Arrived - Docked'), ('under_clearance', 'Under Clearance'), ('registered', 'Registered'), ('ready_for_dispatch', 'Ready for Dispatch'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], max_length=30),
        ),
    ]
