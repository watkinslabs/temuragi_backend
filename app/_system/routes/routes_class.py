
import threading
import logging
from typing import Callable, Optional, List, Dict, Any
from functools import wraps
from flask import Flask, abort
from werkzeug.routing import Rule
from datetime import datetime


class DynamicRouteManager:
    """
    Production-ready dynamic route manager for Flask applications.
    Supports adding, removing, enabling/disabling routes with thread safety.
    """
    
    def __init__(self, app: Flask, logger: Optional[logging.Logger] = None):
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._managed_routes: Dict[str, Dict[str, Any]] = {}
        self._route_states: Dict[str, bool] = {}  # For enable/disable functionality
        
    def add_route(self, 
                  rule: str, 
                  endpoint: str, 
                  view_func: Callable,
                  methods: Optional[List[str]] = None,
                  defaults: Optional[Dict] = None,
                  **options) -> bool:
        """
        Add a new route to the Flask application.
        
        Args:
            rule: URL rule string (e.g., '/users/<int:id>')
            endpoint: Unique endpoint name
            view_func: Function to handle the route
            methods: HTTP methods (default: ['GET'])
            defaults: Default values for URL parameters
            **options: Additional route options
            
        Returns:
            bool: True if route was added successfully
        """
        with self._lock:
            try:
                # Check if endpoint already exists
                if endpoint in self.app.view_functions:
                    self.logger.warning(f"Endpoint '{endpoint}' already exists. Skipping.")
                    return False
                
                # Wrap view function to check if route is enabled
                @wraps(view_func)
                def wrapped_view(*args, **kwargs):
                    if not self._route_states.get(endpoint, True):
                        self.logger.debug(f"Route '{endpoint}' is disabled. Returning 404.")
                        abort(404)
                    return view_func(*args, **kwargs)
                
                # Set default methods
                if methods is None:
                    methods = ['GET']
                
                # Add the route
                self.app.add_url_rule(
                    rule=rule,
                    endpoint=endpoint,
                    view_func=wrapped_view,
                    methods=methods,
                    defaults=defaults,
                    **options
                )
                
                # Track the route
                self._managed_routes[endpoint] = {
                    'rule': rule,
                    'view_func': view_func,
                    'wrapped_func': wrapped_view,
                    'methods': methods,
                    'defaults': defaults,
                    'options': options,
                    'added_at': datetime.utcnow(),
                    'enabled': True
                }
                self._route_states[endpoint] = True
                
                self.logger.info(f"Successfully added route: {rule} -> {endpoint}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add route '{rule}': {str(e)}")
                return False
    
    def remove_route(self, endpoint: str) -> bool:
        """
        Remove a route from the Flask application.
        
        Args:
            endpoint: The endpoint name to remove
            
        Returns:
            bool: True if route was removed successfully
        """
        with self._lock:
            try:
                # Check if we manage this route
                if endpoint not in self._managed_routes:
                    self.logger.warning(f"Endpoint '{endpoint}' is not managed by this manager.")
                    return False
                
                # Check if endpoint exists in Flask
                if endpoint not in self.app.view_functions:
                    self.logger.warning(f"Endpoint '{endpoint}' not found in Flask app.")
                    # Clean up our tracking anyway
                    del self._managed_routes[endpoint]
                    self._route_states.pop(endpoint, None)
                    return False
                
                # Store old state for potential rollback
                old_rules = list(self.app.url_map._rules)
                old_view_funcs = dict(self.app.view_functions)
                
                try:
                    # Remove from Flask's URL map
                    self.app.url_map._rules = [
                        rule for rule in self.app.url_map._rules 
                        if rule.endpoint != endpoint
                    ]
                    
                    # Remove from view functions
                    del self.app.view_functions[endpoint]
                    
                    # Force URL map to rebuild
                    self._rebuild_url_map()
                    
                    # Remove from our tracking
                    route_info = self._managed_routes[endpoint]
                    del self._managed_routes[endpoint]
                    self._route_states.pop(endpoint, None)
                    
                    self.logger.info(
                        f"Successfully removed route: {route_info['rule']} -> {endpoint}"
                    )
                    return True
                    
                except Exception as e:
                    # Rollback on error
                    self.logger.error(f"Error removing route, rolling back: {str(e)}")
                    self.app.url_map._rules = old_rules
                    self.app.view_functions = old_view_funcs
                    self._rebuild_url_map()
                    raise
                    
            except Exception as e:
                self.logger.error(f"Failed to remove route '{endpoint}': {str(e)}")
                return False
    
    def remove_routes_by_prefix(self, prefix: str) -> List[str]:
        """
        Remove all routes with endpoints starting with a prefix.
        
        Args:
            prefix: The endpoint prefix
            
        Returns:
            List of removed endpoint names
        """
        with self._lock:
            endpoints_to_remove = [
                endpoint for endpoint in self._managed_routes
                if endpoint.startswith(prefix)
            ]
            
            removed = []
            for endpoint in endpoints_to_remove:
                if self.remove_route(endpoint):
                    removed.append(endpoint)
            
            return removed
    
    def enable_route(self, endpoint: str) -> bool:
        """Enable a previously disabled route."""
        with self._lock:
            if endpoint not in self._managed_routes:
                self.logger.warning(f"Endpoint '{endpoint}' is not managed.")
                return False
            
            self._route_states[endpoint] = True
            self._managed_routes[endpoint]['enabled'] = True
            self.logger.info(f"Enabled route: {endpoint}")
            return True
    
    def disable_route(self, endpoint: str) -> bool:
        """Disable a route (returns 404) without removing it."""
        with self._lock:
            if endpoint not in self._managed_routes:
                self.logger.warning(f"Endpoint '{endpoint}' is not managed.")
                return False
            
            self._route_states[endpoint] = False
            self._managed_routes[endpoint]['enabled'] = False
            self.logger.info(f"Disabled route: {endpoint}")
            return True
    
    def is_enabled(self, endpoint: str) -> bool:
        """Check if a route is enabled."""
        return self._route_states.get(endpoint, False)
    
    def get_route_info(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get information about a managed route."""
        with self._lock:
            if endpoint in self._managed_routes:
                info = self._managed_routes[endpoint].copy()
                # Don't expose internal functions
                info.pop('wrapped_func', None)
                info.pop('view_func', None)
                return info
            return None
    
    def list_routes(self) -> Dict[str, Dict[str, Any]]:
        """List all managed routes with their information."""
        with self._lock:
            routes = {}
            for endpoint, info in self._managed_routes.items():
                routes[endpoint] = {
                    'rule': info['rule'],
                    'methods': info['methods'],
                    'enabled': info['enabled'],
                    'added_at': info['added_at'].isoformat()
                }
            return routes
    
    def clear_all_routes(self) -> int:
        """
        Remove all managed routes.
        
        Returns:
            Number of routes removed
        """
        with self._lock:
            endpoints = list(self._managed_routes.keys())
            removed_count = 0
            
            for endpoint in endpoints:
                if self.remove_route(endpoint):
                    removed_count += 1
            
            return removed_count
    
    def _rebuild_url_map(self):
        """Force Flask to rebuild its URL map."""
        self.app.url_map._rules_by_endpoint = {}
        self.app.url_map._remap = True
        self.app.url_map.update()
    
    def update_route(self,
                     endpoint: str,
                     view_func: Optional[Callable] = None,
                     methods: Optional[List[str]] = None,
                     **options) -> bool:
        """
        Update an existing route's view function or options.
        
        Args:
            endpoint: The endpoint to update
            view_func: New view function (optional)
            methods: New HTTP methods (optional)
            **options: Other route options to update
            
        Returns:
            bool: True if route was updated successfully
        """
        with self._lock:
            if endpoint not in self._managed_routes:
                self.logger.warning(f"Endpoint '{endpoint}' is not managed.")
                return False
            
            route_info = self._managed_routes[endpoint]
            
            # Remove the old route
            if not self.remove_route(endpoint):
                return False
            
            # Update with new values
            new_view_func = view_func or route_info['view_func']
            new_methods = methods or route_info['methods']
            new_options = {**route_info['options'], **options}
            
            # Re-add the route with updated values
            return self.add_route(
                rule=route_info['rule'],
                endpoint=endpoint,
                view_func=new_view_func,
                methods=new_methods,
                defaults=route_info['defaults'],
                **new_options
            )
    
    def healthcheck(self) -> Dict[str, Any]:
        """Get health status of the route manager."""
        with self._lock:
            return {
                'total_managed_routes': len(self._managed_routes),
                'enabled_routes': sum(1 for enabled in self._route_states.values() if enabled),
                'disabled_routes': sum(1 for enabled in self._route_states.values() if not enabled),
                'flask_total_routes': len(self.app.url_map._rules),
                'status': 'healthy'
            }
