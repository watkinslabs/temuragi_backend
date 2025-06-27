import functools
from typing import Optional, List
from flask import g, session, request


# Global permission registry for auto-discovery
_DISCOVERED_PERMISSIONS = set()

from app.classes import RolePermission,Permission

def _get_current_user():
    """Get current user from Flask context"""
    try:
        return getattr(g, 'current_user', None)
    except RuntimeError:
        return None


def _check_permission(permission_name: str) -> bool:
    """Check if current user has permission"""
    user = _get_current_user()
    if not user:
        return False
    
    try:
        
        return RolePermission.user_has_permission(
            g.session, user.id, permission_name
        )
    except Exception:
        return True  # Fail open on errors


class PermissionDenied(Exception):
    """Permission denied exception"""
    def __init__(self, permission):
        self.permission = permission
        super().__init__(f"Missing permission: {permission}")


def requires_permission(permission_name: str):
    """Require specific permission"""
    _DISCOVERED_PERMISSIONS.add(permission_name)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not _check_permission(permission_name):
                raise PermissionDenied(permission_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def admin_required():
    """Require admin role"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = _get_current_user()
            if not user or not getattr(user.role, 'is_admin', False):
                raise PermissionDenied('admin')
            return func(*args, **kwargs)
        return wrapper
    return decorator


def permission_optional(permission_name: str):
    """Add has_permission to kwargs"""
    _DISCOVERED_PERMISSIONS.add(permission_name)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['has_permission'] = _check_permission(permission_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def auto_create_permissions():
    """Create discovered permissions in database"""
    try:
        from flask import current_app
        
        
        session = current_app.db_session()
        created = 0
        
        for perm_name in _DISCOVERED_PERMISSIONS:
            if ':' in perm_name and perm_name != 'admin':
                parts = perm_name.split(':')
                service, action = parts[0], parts[1]
                resource = parts[2] if len(parts) > 2 else None
                
                existing = Permission.find_by_name(session, perm_name)
                if not existing:
                    success, result = Permission.create_permission(
                        session, service, action, resource,
                        "Auto-discovered permission"
                    )
                    if success:
                        created += 1
        
        if created > 0:
            current_app.logger.info(f"Auto-created {created} permissions")
            
    except Exception as e:
        pass  # Fail silently


# Error handler for Flask
def handle_permission_error(error):
    """Handle permission denied errors"""
    return {"error": "Permission denied", "permission": error.permission}, 403



def register_rbac(app):
    """Setup RBAC after all modules are loaded"""
    try:
        # Import after modules are discovered

        with app.app_context():
            auto_create_permissions()
        
        # Register error handler
        app.register_error_handler(PermissionDenied, handle_permission_error)
        
        app.logger.info("RBAC system initialized")
    except ImportError:
        app.logger.info("RBAC system not available")
