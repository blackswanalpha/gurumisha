# Generated manually for status migration

from django.db import migrations


def migrate_status_data(apps, schema_editor):
    """Migrate existing status data from old values to new values"""
    ImportOrder = apps.get_model('core', 'ImportOrder')
    ImportOrderStatusHistory = apps.get_model('core', 'ImportOrderStatusHistory')
    
    # Update ImportOrder status values
    ImportOrder.objects.filter(status='quotation_pending').update(status='import_request')
    ImportOrder.objects.filter(status='confirmed').update(status='import_request')
    
    # Update ImportOrderStatusHistory status values
    ImportOrderStatusHistory.objects.filter(new_status='quotation_pending').update(new_status='import_request')
    ImportOrderStatusHistory.objects.filter(new_status='confirmed').update(new_status='import_request')
    ImportOrderStatusHistory.objects.filter(previous_status='quotation_pending').update(previous_status='import_request')
    ImportOrderStatusHistory.objects.filter(previous_status='confirmed').update(previous_status='import_request')


def reverse_migrate_status_data(apps, schema_editor):
    """Reverse migration - restore old status values"""
    ImportOrder = apps.get_model('core', 'ImportOrder')
    ImportOrderStatusHistory = apps.get_model('core', 'ImportOrderStatusHistory')
    
    # Note: We can't perfectly reverse this since we're merging two statuses into one
    # We'll restore to 'confirmed' as it's the more common case
    ImportOrder.objects.filter(status='import_request').update(status='confirmed')
    
    ImportOrderStatusHistory.objects.filter(new_status='import_request').update(new_status='confirmed')
    ImportOrderStatusHistory.objects.filter(previous_status='import_request').update(previous_status='confirmed')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_update_import_order_status'),
    ]

    operations = [
        migrations.RunPython(migrate_status_data, reverse_migrate_status_data),
    ]
