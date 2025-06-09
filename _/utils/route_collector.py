
def collect_blueprint_routes(app):
    """
    Collect routes from all registered blueprints in the app
    Returns a structured list of dictionaries containing route information
    """
    routes = []
    
    # Get the URL map from the app
    for rule in app.url_map.iter_rules():
        # Skip static routes and other special routes
        if rule.endpoint.startswith('static') or '.' not in rule.endpoint:
            continue
            
        # Extract blueprint name and view function name
        blueprint_name, view_name = rule.endpoint.split('.', 1)
        
        # Skip routes that start with underscore (internal)
        if view_name.startswith('_'):
            continue
        
        # Get the HTTP methods for this rule
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        
        # Create a route info dictionary
        route_info = {
            'endpoint': rule.endpoint,
            'blueprint': blueprint_name,
            'view': view_name,
            'url': str(rule),
            'methods': methods,
            'path': rule.rule,
            'defaults': rule.defaults,
        }
        
        # Try to get the view function to extract metadata
        try:
            view_func = app.view_functions[rule.endpoint]
            
            # Check for menu metadata on the view function
            if hasattr(view_func, 'menu_metadata'):
                route_info.update(view_func.menu_metadata)
            else:
                # Set defaults
                route_info.update({
                    'title': view_name.replace('_', ' ').title(),
                    'menu_visible': False,  # Default to not visible in menu
                    'menu_order': 100,      # Default order
                    'menu_icon': 'fa-link', # Default icon
                    'menu_category': None,  # No category by default
                })
        except:
            pass
        routes.append(route_info)
    
    return routes
