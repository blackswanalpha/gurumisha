"""
Activity Log Manager for Gurumisha Motors
Comprehensive activity tracking and logging system
"""

import json
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ActivityLog, AuditLog

User = get_user_model()


class ActivityManager:
    """Manager for tracking user activities across the system"""
    
    @staticmethod
    def log_activity(user, action, description, content_object=None, extra_data=None, request=None):
        """
        Log a user activity

        Args:
            user: User instance
            action: Action type (from ActivityLog.ACTION_CHOICES)
            description: Human-readable description
            content_object: Related object (optional)
            extra_data: Additional context data (dict)
            request: HTTP request object for IP/user agent
        """
        try:
            activity_data = {
                'user': user,
                'action': action,
                'description': description,
                'extra_data': extra_data or {},
            }

            # Add content object if provided
            if content_object:
                activity_data['content_object'] = content_object

            # Extract request information
            if request:
                activity_data.update({
                    'ip_address': ActivityManager.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'session_key': request.session.session_key or '',
                })

            return ActivityLog.objects.create(**activity_data)
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the main operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log activity: {e}")
            return None
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_login(user, request=None):
        """Log user login activity"""
        return ActivityManager.log_activity(
            user=user,
            action='login',
            description=f"User {user.username} logged in",
            request=request
        )
    
    @staticmethod
    def log_logout(user, request=None):
        """Log user logout activity"""
        return ActivityManager.log_activity(
            user=user,
            action='logout',
            description=f"User {user.username} logged out",
            request=request
        )
    
    @staticmethod
    def log_car_action(user, action, car, request=None):
        """Log car-related activities"""
        car_brand = car.brand.name if car.brand else 'Unknown'
        car_model = car.model.name if car.model else 'Unknown'

        action_descriptions = {
            'car_create': f"Created car listing: {car_brand} {car_model}",
            'car_update': f"Updated car listing: {car_brand} {car_model}",
            'car_delete': f"Deleted car listing: {car_brand} {car_model}",
            'car_view': f"Viewed car listing: {car_brand} {car_model}",
            'car_approve': f"Approved car listing: {car_brand} {car_model}",
            'car_reject': f"Rejected car listing: {car_brand} {car_model}",
        }

        return ActivityManager.log_activity(
            user=user,
            action=action,
            description=action_descriptions.get(action, f"Car action: {action}"),
            content_object=car,
            extra_data={'car_id': car.id, 'car_brand': car_brand, 'car_model': car_model},
            request=request
        )
    
    @staticmethod
    def log_import_action(user, action, import_obj, request=None):
        """Log import-related activities"""
        action_descriptions = {
            'import_request_create': f"Created import request: {import_obj.vehicle_details}",
            'import_request_update': f"Updated import request: {import_obj.vehicle_details}",
            'import_status_change': f"Changed import status to: {import_obj.status}",
        }

        extra_data = {
            'import_id': import_obj.id,
            'vehicle_details': import_obj.vehicle_details,
        }
        
        if hasattr(import_obj, 'status'):
            extra_data['status'] = import_obj.status
        
        return ActivityManager.log_activity(
            user=user,
            action=action,
            description=action_descriptions.get(action, f"Import action: {action}"),
            content_object=import_obj,
            extra_data=extra_data,
            request=request
        )
    
    @staticmethod
    def log_order_action(user, action, order, request=None):
        """Log order-related activities"""
        action_descriptions = {
            'order_create': f"Created order #{order.id}",
            'order_update': f"Updated order #{order.id}",
            'order_cancel': f"Cancelled order #{order.id}",
            'payment_made': f"Payment made for order #{order.id}",
            'payment_failed': f"Payment failed for order #{order.id}",
        }
        
        return ActivityManager.log_activity(
            user=user,
            action=action,
            description=action_descriptions.get(action, f"Order action: {action}"),
            content_object=order,
            extra_data={'order_id': order.id, 'total_amount': str(order.total_amount)},
            request=request
        )
    
    @staticmethod
    def log_search_activity(user, search_query, filters=None, results_count=0, request=None):
        """Log search activities"""
        extra_data = {
            'search_query': search_query,
            'results_count': results_count,
        }
        
        if filters:
            extra_data['filters'] = filters
        
        return ActivityManager.log_activity(
            user=user,
            action='search_performed',
            description=f"Searched for: {search_query}",
            extra_data=extra_data,
            request=request
        )
    
    @staticmethod
    def get_user_activities(user, limit=50, action_filter=None):
        """Get recent activities for a user"""
        queryset = ActivityLog.objects.filter(user=user)
        
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        return queryset[:limit]
    
    @staticmethod
    def get_object_activities(content_object, limit=20):
        """Get activities related to a specific object"""
        content_type = ContentType.objects.get_for_model(content_object)
        return ActivityLog.objects.filter(
            content_type=content_type,
            object_id=content_object.id
        )[:limit]
    
    @staticmethod
    def get_system_activities(limit=100, action_filter=None):
        """Get recent system-wide activities"""
        queryset = ActivityLog.objects.all()
        
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        return queryset[:limit]


class AuditManager:
    """Manager for audit logging and compliance tracking"""
    
    @staticmethod
    def log_audit(user, action_type, description, table_name=None, record_id=None,
                  field_name=None, old_value=None, new_value=None, severity='low',
                  request=None, extra_data=None):
        """
        Log an audit event

        Args:
            user: User instance (can be None for system events)
            action_type: Type of action (from AuditLog.ACTION_TYPES)
            description: Description of the action
            table_name: Database table name
            record_id: Record ID
            field_name: Field that was changed
            old_value: Previous value
            new_value: New value
            severity: Severity level
            request: HTTP request object
            extra_data: Additional context data
        """
        try:
            audit_data = {
                'user': user,
                'action_type': action_type,
                'description': description,
                'table_name': table_name or '',
                'record_id': str(record_id) if record_id else '',
                'field_name': field_name or '',
                'old_value': str(old_value) if old_value else '',
                'new_value': str(new_value) if new_value else '',
                'severity': severity,
                'extra_data': extra_data or {},
            }

            # Extract request information
            if request:
                audit_data.update({
                    'ip_address': ActivityManager.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    'request_path': request.path,
                    'request_method': request.method,
                })

            return AuditLog.objects.create(**audit_data)
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the main operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log audit event: {e}")
            return None
    
    @staticmethod
    def log_model_change(user, instance, action_type, changed_fields=None, request=None):
        """Log model instance changes"""
        table_name = instance._meta.db_table
        record_id = instance.pk
        
        if action_type == 'create':
            return AuditManager.log_audit(
                user=user,
                action_type=action_type,
                description=f"Created {instance._meta.verbose_name}: {str(instance)}",
                table_name=table_name,
                record_id=record_id,
                request=request
            )
        
        elif action_type == 'update' and changed_fields:
            audit_logs = []
            for field_name, (old_value, new_value) in changed_fields.items():
                audit_logs.append(AuditManager.log_audit(
                    user=user,
                    action_type=action_type,
                    description=f"Updated {instance._meta.verbose_name}: {str(instance)}",
                    table_name=table_name,
                    record_id=record_id,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    request=request
                ))
            return audit_logs
        
        elif action_type == 'delete':
            return AuditManager.log_audit(
                user=user,
                action_type=action_type,
                description=f"Deleted {instance._meta.verbose_name}: {str(instance)}",
                table_name=table_name,
                record_id=record_id,
                severity='medium',
                request=request
            )
    
    @staticmethod
    def log_security_event(user, event_type, description, severity='high', request=None):
        """Log security-related events"""
        return AuditManager.log_audit(
            user=user,
            action_type='security_event',
            description=f"Security Event: {event_type} - {description}",
            severity=severity,
            request=request,
            extra_data={'event_type': event_type}
        )
    
    @staticmethod
    def log_permission_change(user, target_user, permission_change, request=None):
        """Log permission changes"""
        return AuditManager.log_audit(
            user=user,
            action_type='permission_change',
            description=f"Changed permissions for {target_user.username}: {permission_change}",
            table_name='auth_user',
            record_id=target_user.id,
            severity='high',
            request=request,
            extra_data={'target_user': target_user.username, 'change': permission_change}
        )
    
    @staticmethod
    def get_audit_trail(table_name=None, record_id=None, user=None, limit=100):
        """Get audit trail with optional filters"""
        queryset = AuditLog.objects.all()
        
        if table_name:
            queryset = queryset.filter(table_name=table_name)
        
        if record_id:
            queryset = queryset.filter(record_id=str(record_id))
        
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset[:limit]
    
    @staticmethod
    def get_security_events(severity=None, limit=50):
        """Get security events"""
        queryset = AuditLog.objects.filter(action_type='security_event')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset[:limit]
