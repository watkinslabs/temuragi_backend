"""
Routes discovery API endpoint
Provides detailed information about all registered routes, blueprints, and endpoints
"""

from flask import Blueprint, jsonify, current_app
from werkzeug.routing import Rule
import inspect

bp = Blueprint('routes', __name__, url_prefix='/api/routes')


def get_route_details(rule: Rule) -> dict:
    """Extract detailed information from a route rule"""
    # Get the endpoint function
    endpoint_func = current_app.view_functions.get(rule.endpoint)
    
    # Extract function details if available
    func_info = {}
    if endpoint_func:
        # Get docstring
        func_info['docstring'] = inspect.getdoc(endpoint_func)
        
        # Get module and function name
        func_info['module'] = getattr(endpoint_func, '__module__', 'Unknown')
        func_info['function'] = getattr(endpoint_func, '__name__', 'Unknown')
        
        # Check if it's a class-based view
        if hasattr(endpoint_func, 'view_class'):
            func_info['view_class'] = endpoint_func.view_class.__name__
            func_info['is_class_based'] = True
        else:
            func_info['is_class_based'] = False
    
    # Build route details
    route_details = {
        'rule': rule.rule,
        'endpoint': rule.endpoint,
        'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),  # Exclude implicit methods
        'defaults': rule.defaults or {},
        'arguments': list(rule.arguments) if rule.arguments else [],
        'subdomain': rule.subdomain or None,
        'host': rule.host or None,
        'websocket': rule.websocket,
        'merge_slashes': getattr(rule, 'merge_slashes', None),
        'strict_slashes': rule.strict_slashes,
        'build_only': rule.build_only,
        'alias': rule.alias if hasattr(rule, 'alias') else False,
        'provide_automatic_options': rule.provide_automatic_options,
        'function_info': func_info
    }
    
    # Determine blueprint from endpoint
    if '.' in rule.endpoint:
        blueprint_name = rule.endpoint.split('.')[0]
        route_details['blueprint'] = blueprint_name
    else:
        route_details['blueprint'] = None
    
    return route_details


@bp.route('/all', methods=['GET'])
def get_all_routes():
    """Get all registered routes with full details"""
    routes = []
    
    # Get all rules from the app
    for rule in current_app.url_map.iter_rules():
        route_details = get_route_details(rule)
        routes.append(route_details)
    
    # Sort routes by rule for consistency
    routes.sort(key=lambda x: x['rule'])
    
    return jsonify({
        'success': True,
        'count': len(routes),
        'routes': routes
    })


@bp.route('/blueprints', methods=['GET'])
def get_blueprints():
    """Get all registered blueprints with their details"""
    blueprints_info = {}
    
    # Iterate through all registered blueprints
    for name, blueprint in current_app.blueprints.items():
        blueprint_info = {
            'name': blueprint.name,
            'import_name': blueprint.import_name,
            'template_folder': blueprint.template_folder,
            'static_folder': blueprint.static_folder,
            'static_url_path': blueprint.static_url_path,
            'url_prefix': blueprint.url_prefix,
            'subdomain': blueprint.subdomain,
            'url_values_defaults': blueprint.url_values_defaults,
            'root_path': blueprint.root_path,
            'cli_group': getattr(blueprint, 'cli_group', None),
            'routes': []
        }
        
        # Find all routes for this blueprint
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint.startswith(f"{name}."):
                route_details = get_route_details(rule)
                blueprint_info['routes'].append(route_details)
        
        # Sort routes within blueprint
        blueprint_info['routes'].sort(key=lambda x: x['rule'])
        blueprint_info['route_count'] = len(blueprint_info['routes'])
        
        blueprints_info[name] = blueprint_info
    
    return jsonify({
        'success': True,
        'count': len(blueprints_info),
        'blueprints': blueprints_info
    })


@bp.route('/summary', methods=['GET'])
def get_routes_summary():
    """Get a summary of routes grouped by blueprint and method"""
    summary = {
        'total_routes': 0,
        'total_blueprints': len(current_app.blueprints),
        'routes_by_method': {},
        'routes_by_blueprint': {},
        'static_routes': 0,
        'dynamic_routes': 0,
        'websocket_routes': 0
    }
    
    # Analyze all routes
    for rule in current_app.url_map.iter_rules():
        summary['total_routes'] += 1
        
        # Count by HTTP method
        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        for method in methods:
            if method not in summary['routes_by_method']:
                summary['routes_by_method'][method] = 0
            summary['routes_by_method'][method] += 1
        
        # Count by blueprint
        blueprint_name = 'app' if '.' not in rule.endpoint else rule.endpoint.split('.')[0]
        if blueprint_name not in summary['routes_by_blueprint']:
            summary['routes_by_blueprint'][blueprint_name] = 0
        summary['routes_by_blueprint'][blueprint_name] += 1
        
        # Count static vs dynamic
        if '<' in rule.rule:
            summary['dynamic_routes'] += 1
        else:
            summary['static_routes'] += 1
        
        # Count websocket routes
        if rule.websocket:
            summary['websocket_routes'] += 1
    
    return jsonify({
        'success': True,
        'summary': summary
    })


@bp.route('/search/<path:pattern>', methods=['GET'])
def search_routes(pattern):
    """Search routes by pattern in rule, endpoint, or function name"""
    pattern_lower = pattern.lower()
    matching_routes = []
    
    for rule in current_app.url_map.iter_rules():
        route_details = get_route_details(rule)
        
        # Search in multiple fields
        if (pattern_lower in route_details['rule'].lower() or
            pattern_lower in route_details['endpoint'].lower() or
            pattern_lower in route_details['function_info'].get('function', '').lower() or
            pattern_lower in route_details['function_info'].get('module', '').lower()):
            
            matching_routes.append(route_details)
    
    # Sort by relevance (exact rule match first)
    matching_routes.sort(key=lambda x: (
        not x['rule'].lower().startswith(pattern_lower),
        x['rule']
    ))
    
    return jsonify({
        'success': True,
        'pattern': pattern,
        'count': len(matching_routes),
        'routes': matching_routes
    })


@bp.route('/tree', methods=['GET'])
def get_routes_tree():
    """Get routes organized in a tree structure by URL segments"""
    tree = {}
    
    for rule in current_app.url_map.iter_rules():
        # Skip static endpoint
        if rule.endpoint == 'static':
            continue
            
        route_details = get_route_details(rule)
        
        # Split the rule into segments
        segments = [s for s in rule.rule.split('/') if s]
        
        # Build tree structure
        current_level = tree
        for i, segment in enumerate(segments):
            if segment not in current_level:
                current_level[segment] = {
                    '_routes': [],
                    '_children': {}
                }
            
            # If this is the last segment, add the route
            if i == len(segments) - 1:
                current_level[segment]['_routes'].append(route_details)
            
            current_level = current_level[segment]['_children']
    
    return jsonify({
        'success': True,
        'tree': tree
    })


@bp.route('/export', methods=['GET'])
def export_routes():
    """Export all routes in a format suitable for documentation or analysis"""
    export_data = {
        'app_name': current_app.name,
        'total_routes': 0,
        'total_blueprints': len(current_app.blueprints),
        'blueprints': {},
        'routes': []
    }
    
    # Collect blueprint info
    for name, blueprint in current_app.blueprints.items():
        export_data['blueprints'][name] = {
            'name': blueprint.name,
            'url_prefix': blueprint.url_prefix,
            'import_name': blueprint.import_name
        }
    
    # Collect all routes
    for rule in current_app.url_map.iter_rules():
        route_details = get_route_details(rule)
        
        # Simplified export format
        export_route = {
            'path': route_details['rule'],
            'methods': route_details['methods'],
            'endpoint': route_details['endpoint'],
            'blueprint': route_details['blueprint'],
            'description': route_details['function_info'].get('docstring', ''),
            'parameters': route_details['arguments']
        }
        
        export_data['routes'].append(export_route)
        export_data['total_routes'] += 1
    
    # Sort routes for consistent output
    export_data['routes'].sort(key=lambda x: x['path'])
    
    return jsonify({
        'success': True,
        'export': export_data
    })