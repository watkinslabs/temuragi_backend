import time
from flask import request, g
from functools import wraps
from datetime import datetime, timezone

from app.register.classes import get_model

class RbacPermissionChecker:
    """
    Centralized RBAC permission checker with automatic audit logging
    Use this for ALL permission checks across the entire system
    """
    __depends_on_ = []
    def __init__(self):
        self.role_permission_model = get_model('RolePermission')
        self.rbac_audit_model = get_model('RbacAuditLog')
        self.user_model = get_model('User')

    def check_permission(self, user_id, permission_name, **context):
        """
        Check if user has permission and automatically audit the result
        
        Args:
            user_id: UUID of user to check
            permission_name: Permission string like "users:read"
            **context: Additional context for auditing
            
        Returns:
            bool: True if permission granted, False otherwise
        """
        start_time = time.time()
        
        # Default context values
        audit_context = {
            'user_id': user_id,
            'permission_name': permission_name,
            'interface_type': context.get('interface_type', 'unknown'),
            'resource_type': context.get('resource_type'),
            'resource_name': context.get('resource_name'),
            'resource_id': context.get('resource_id'),
            'action_attempted': context.get('action_attempted'),
            'endpoint': context.get('endpoint'),
            'request_method': context.get('request_method'),
            'ip_address': context.get('ip_address'),
            'user_agent': context.get('user_agent'),
            'token_id': context.get('token_id'),
            'request_id': context.get('request_id'),
            'context_data': context.get('context_data')
        }
        
        try:
            # Perform the actual permission check
            if not self.role_permission_model:
                # If RBAC system not available, deny by default
                granted = False
                audit_context['access_denied_reason'] = 'RBAC system unavailable'
            elif not user_id:
                granted = False
                audit_context['access_denied_reason'] = 'No user provided'
            else:
                # First check exact permission
                granted = self.role_permission_model.user_has_permission(
                    user_id, permission_name
                )
                
                # If not granted, check wildcard permissions
                if not granted:
                    granted = self._check_wildcard_permission(user_id, permission_name)
                
                if not granted:
                    audit_context['access_denied_reason'] = f'User lacks permission: {permission_name}'
            
            # Calculate check duration
            check_duration_ms = int((time.time() - start_time) * 1000)
            audit_context['check_duration_ms'] = check_duration_ms
            audit_context['permission_granted'] = granted
            
            # Log the permission check
            self._log_audit(audit_context)
            
            return granted
            
        except Exception as e:
            # Log the error
            audit_context.update({
                'permission_granted': False,
                'access_denied_reason': f'Permission check failed: {str(e)}',
                'check_duration_ms': int((time.time() - start_time) * 1000)
            })
            self._log_audit(audit_context)
            
            # Deny by default on errors
            return False

    def _check_wildcard_permission(self, user_id, permission_name):
        """
        Check if user has any wildcard permissions that match the requested permission
        
        Args:
            user_id: UUID of user to check
            permission_name: Permission string like "api:users:read"
            
        Returns:
            bool: True if wildcard permission found, False otherwise
        """
        # Split the requested permission into parts
        parts = permission_name.split(':')
        if len(parts) != 3:
            return False
        
        service, resource, action = parts
        
        # Generate all possible wildcard combinations
        wildcard_patterns = [
            '*:*:*',                    # Full wildcard
            f'{service}:*:*',          # Service wildcard
            f'*:{resource}:*',         # Resource wildcard
            f'*:*:{action}',           # Action wildcard
            f'{service}:{resource}:*', # Service+Resource wildcard
            f'{service}:*:{action}',   # Service+Action wildcard
            f'*:{resource}:{action}',  # Resource+Action wildcard
        ]
        
        # Check each wildcard pattern
        for pattern in wildcard_patterns:
            if self.role_permission_model.user_has_permission(
                user_id, pattern
            ):
                return True
        
        return False

    def check_api_permission(self, user_id, permission_name, model_name=None, 
                           action=None, record_id=None, token_id=None):
        """
        Check permission for API operations
        Auto-detects Flask request context
        """
        context = {
            'interface_type': 'api',
            'resource_type': 'model',
            'resource_name': model_name,
            'resource_id': record_id,
            'action_attempted': action,
            'endpoint': '/api/data',
            'request_method': 'POST',
            'token_id': token_id
        }
        
        # Auto-detect request context if available
        if request:
            context.update({
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'request_id': getattr(request, 'id', None)
            })
        
        return self.check_permission(user_id, permission_name, **context)

    def check_web_permission(self, user_id, permission_name, view_name=None, 
                           action=None, resource_id=None):
        """
        Check permission for web interface operations
        Auto-detects Flask request context
        """
        context = {
            'interface_type': 'web',
            'resource_type': 'view',
            'resource_name': view_name,
            'resource_id': resource_id,
            'action_attempted': action
        }
        
        # Auto-detect request context if available
        if request:
            context.update({
                'endpoint': request.endpoint,
                'request_method': request.method,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
            })
        
        return self.check_permission(user_id, permission_name, **context)

    def check_cli_permission(self, user_id, permission_name, cli_name=None, 
                           command=None, resource_name=None, action=None):
        """
        Check permission for CLI operations
        """
        context = {
            'interface_type': 'cli',
            'resource_type': 'cli',
            'resource_name': resource_name or cli_name,
            'action_attempted': action or command,
            'endpoint': f"{cli_name} {command}" if cli_name and command else None,
            'request_method': 'CLI'
        }
        
        return self.check_permission(user_id, permission_name, **context)

    def require_permission(self, permission_name, **kwargs):
        """
        Decorator for requiring permissions on functions
        
        Usage:
        @rbac.require_permission("users:read", resource_name="User", action="list")
        def list_users():
            ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **func_kwargs):
                # Get user from context
                user_id = getattr(g, 'user_id', None) if hasattr(g, 'user_id') else None
                
                if not user_id:
                    raise PermissionError("Authentication required")
                
                # Determine interface type from context
                interface_type = 'web'  # Default
                if hasattr(g, 'auth_context'):
                    interface_type = 'api'
                elif not request:
                    interface_type = 'cli'
                
                # Build context
                context = kwargs.copy()
                context['interface_type'] = interface_type
                
                # Check permission
                if not self.check_permission(user_id, permission_name, **context):
                    raise PermissionError(f"Permission denied: {permission_name}")
                
                return func(*args, **func_kwargs)
            return wrapper
        return decorator

    def _log_audit(self, audit_context):
        """Log the permission check"""
        try:
            if self.rbac_audit_model:
                self.rbac_audit_model.log_permission_check( **audit_context)
        except Exception as e:
            # Don't let audit logging break the main flow
            print(f"Permission Checker RBAC audit logging failed: {e}")


class RbacMiddleware:
    """
    Middleware to automatically inject RBAC checker into request context
    """
    
    __depends_on__ = ['RbacPermissionChecker']
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.rbac = self
        
        @app.before_request
        def setup_rbac():
            """Setup RBAC checker for each request"""
            g.rbac = RbacPermissionChecker()


# Convenience functions for common permission checks
def check_model_permission(user_id, model_name, action,  record_id=None):
    """
    Check permission for model operations
    """
    permission_name = f"{model_name.lower()}:{action}"
    checker = RbacPermissionChecker()
    
    # Determine interface type
    interface_type = 'api' if hasattr(g, 'auth_context') else 'web'
    
    return checker.check_permission(
        user_id, 
        permission_name,
        interface_type=interface_type,
        resource_type='model',
        resource_name=model_name,
        resource_id=record_id,
        action_attempted=action
    )


def require_model_permission(model_name, action):
    """
    Decorator for requiring model permissions
    
    Usage:
    @require_model_permission("User", "read")
    def get_user(user_id):
        ...
    """
    permission_name = f"{model_name.lower()}:{action}"
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                raise PermissionError("Authentication required")
            
            
            
            if not check_model_permission(user_id, model_name, action):
                raise PermissionError(f"Permission denied: {permission_name}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

