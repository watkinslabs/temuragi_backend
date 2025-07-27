#!/usr/bin/env python3
"""
Routes CLI - Query and display application routes
Provides commands to discover, search, and analyze Flask application routes
"""

import argparse
import json
import sys
from typing import Dict, List, Any, Optional
from app.base.cli import BaseCLI
from tabulate import tabulate

# CLI description for discovery
CLI_DESCRIPTION = "Query and analyze Flask application routes"


class RoutesCLI(BaseCLI):
    """CLI for querying and displaying application routes"""
    
    def __init__(self, **kwargs):
        # Force remote backend for routes CLI
        kwargs['backend_type'] = kwargs.get('backend_type', 'remote')
        super().__init__(name="routes", **kwargs)

        
    def list_all_routes(self, format_type: str = 'table', sort_by: str = 'path'):
        """List all routes in the application"""
        self.log_operation_start("list_all_routes")
        
        try:
            # Execute API call
            result = self.execute_operation('routes', 'all')
            
            if not result.get('success'):
                self.output_error(f"Failed to get routes: {result.get('error', 'Unknown error')}")
                return False
            
            routes = result.get('routes', [])
            
            if not routes:
                self.output_warning("No routes found")
                return True
            
            # Sort routes
            if sort_by == 'path':
                routes.sort(key=lambda x: x['rule'])
            elif sort_by == 'endpoint':
                routes.sort(key=lambda x: x['endpoint'])
            elif sort_by == 'blueprint':
                routes.sort(key=lambda x: (x.get('blueprint', ''), x['rule']))
            
            # Display based on format
            if format_type == 'table':
                self._display_routes_table(routes)
            elif format_type == 'json':
                print(json.dumps(routes, indent=2))
            elif format_type == 'tree':
                self._display_routes_tree(routes)
            else:
                self._display_routes_simple(routes)
            
            self.output_success(f"Found {len(routes)} routes")
            return True
            
        except Exception as e:
            self.output_error(f"Error listing routes: {e}")
            return False
    
    def list_blueprints(self, verbose: bool = False):
        """List all registered blueprints"""
        self.log_operation_start("list_blueprints")
        
        try:
            result = self.execute_operation('routes', 'blueprints')
            
            if not result.get('success'):
                self.output_error(f"Failed to get blueprints: {result.get('error', 'Unknown error')}")
                return False
            
            blueprints = result.get('blueprints', {})
            
            if not blueprints:
                self.output_warning("No blueprints found")
                return True
            
            # Display blueprints
            headers = ['Blueprint', 'URL Prefix', 'Routes', 'Import Name']
            rows = []
            
            for name, info in sorted(blueprints.items()):
                rows.append([
                    name,
                    info.get('url_prefix', 'N/A'),
                    info.get('route_count', 0),
                    info.get('import_name', 'N/A')
                ])
                
                if verbose and info.get('routes'):
                    # Show routes under each blueprint
                    print(f"\n{name} routes:")
                    route_rows = []
                    for route in info['routes']:
                        route_rows.append([
                            f"  {route['rule']}",
                            ', '.join(route['methods']),
                            route['endpoint'].split('.')[-1]
                        ])
                    print(tabulate(route_rows, headers=['Path', 'Methods', 'Function']))
            
            self.output_table(rows, headers)
            self.output_success(f"Found {len(blueprints)} blueprints")
            return True
            
        except Exception as e:
            self.output_error(f"Error listing blueprints: {e}")
            return False
    
    def get_summary(self):
        """Get routes summary statistics"""
        self.log_operation_start("get_summary")
        
        try:
            result = self.execute_operation('routes', 'summary')
            
            if not result.get('success'):
                self.output_error(f"Failed to get summary: {result.get('error', 'Unknown error')}")
                return False
            
            summary = result.get('summary', {})
            
            # Display summary
            self.output_info("Routes Summary")
            self.output("=" * 50)
            self.output(f"Total Routes: {summary.get('total_routes', 0)}")
            self.output(f"Total Blueprints: {summary.get('total_blueprints', 0)}")
            self.output(f"Static Routes: {summary.get('static_routes', 0)}")
            self.output(f"Dynamic Routes: {summary.get('dynamic_routes', 0)}")
            self.output(f"WebSocket Routes: {summary.get('websocket_routes', 0)}")
            
            # Routes by method
            self.output("\nRoutes by HTTP Method:")
            for method, count in sorted(summary.get('routes_by_method', {}).items()):
                self.output(f"  {method}: {count}")
            
            # Routes by blueprint
            self.output("\nRoutes by Blueprint:")
            for blueprint, count in sorted(summary.get('routes_by_blueprint', {}).items()):
                self.output(f"  {blueprint}: {count}")
            
            return True
            
        except Exception as e:
            self.output_error(f"Error getting summary: {e}")
            return False
    
    def search_routes(self, pattern: str):
        """Search routes by pattern"""
        self.log_operation_start(f"search_routes: {pattern}")
        
        try:
            result = self.execute_operation('routes', 'search', {'pattern': pattern})
            
            if not result.get('success'):
                self.output_error(f"Failed to search routes: {result.get('error', 'Unknown error')}")
                return False
            
            routes = result.get('routes', [])
            
            if not routes:
                self.output_warning(f"No routes found matching '{pattern}'")
                return True
            
            # Display found routes
            self.output_info(f"Routes matching '{pattern}':")
            self._display_routes_table(routes)
            self.output_success(f"Found {len(routes)} matching routes")
            return True
            
        except Exception as e:
            self.output_error(f"Error searching routes: {e}")
            return False
    
    def export_routes(self, output_file: str = None):
        """Export routes for documentation"""
        self.log_operation_start("export_routes")
        
        try:
            result = self.execute_operation('routes', 'export')
            
            if not result.get('success'):
                self.output_error(f"Failed to export routes: {result.get('error', 'Unknown error')}")
                return False
            
            export_data = result.get('export', {})
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                self.output_success(f"Routes exported to {output_file}")
            else:
                print(json.dumps(export_data, indent=2))
            
            return True
            
        except Exception as e:
            self.output_error(f"Error exporting routes: {e}")
            return False
    
    def _display_routes_table(self, routes: List[Dict]):
        """Display routes in table format"""
        headers = ['Path', 'Methods', 'Endpoint', 'Blueprint', 'Args']
        rows = []
        
        for route in routes:
            methods = ', '.join(route.get('methods', []))
            endpoint = route.get('endpoint', '')
            blueprint = route.get('blueprint', 'app')
            args = ', '.join(route.get('arguments', []))
            
            rows.append([
                route.get('rule', ''),
                methods,
                endpoint.split('.')[-1] if '.' in endpoint else endpoint,
                blueprint,
                args or '-'
            ])
        
        self.output_table(rows, headers)
    
    def _display_routes_simple(self, routes: List[Dict]):
        """Display routes in simple format"""
        for route in routes:
            methods = ', '.join(route.get('methods', []))
            print(f"{route['rule']} [{methods}] -> {route['endpoint']}")
    
    def _display_routes_tree(self, routes: List[Dict]):
        """Display routes in tree format (simplified)"""
        # Group by blueprint
        by_blueprint = {}
        for route in routes:
            bp = route.get('blueprint', 'app')
            if bp not in by_blueprint:
                by_blueprint[bp] = []
            by_blueprint[bp].append(route)
        
        # Display tree
        for bp, bp_routes in sorted(by_blueprint.items()):
            print(f"\n{bp}/")
            for route in sorted(bp_routes, key=lambda x: x['rule']):
                methods = ', '.join(route.get('methods', []))
                print(f"  {route['rule']} [{methods}]")
    
    def execute_operation(self, model: str, operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Override to handle routes API calls"""
        if model == 'routes':
            # Debug: Check backend type
            self.log_debug(f"Backend type: {type(self.backend).__name__}")
            self.log_debug(f"Backend has base_url: {hasattr(self.backend, 'base_url')}")
            
            # Check if we're using RemoteBackend
            if hasattr(self.backend, 'base_url') and hasattr(self.backend, 'session'):
                # Remote backend - make direct HTTP calls
                endpoint_map = {
                    'all': '/api/routes/all',
                    'blueprints': '/api/routes/blueprints', 
                    'summary': '/api/routes/summary',
                    'export': '/api/routes/export'
                }
                
                if operation == 'search' and data and 'pattern' in data:
                    endpoint = f"/api/routes/search/{data['pattern']}"
                elif operation in endpoint_map:
                    endpoint = endpoint_map[operation]
                else:
                    return {'success': False, 'error': f'Unknown operation: {operation}'}
                
                try:
                    # Build full URL
                    base_url = self.backend.base_url
                    route_prefix = self.backend.config.get('route_prefix', '')
                    url = f"{base_url}{route_prefix}{endpoint}"
                    
                    self.log_debug(f"Making request to: {url}")
                    
                    headers = self.backend._build_headers()
                    response = self.backend.session.get(url, headers=headers, timeout=self.backend.timeout)
                    
                    self.log_debug(f"Response status: {response.status_code}")
                    self.log_debug(f"Response headers: {response.headers}")
                    
                    if response.status_code == 401:
                        return {
                            'success': False,
                            'error': 'Authentication required. Please login with: tmcli login'
                        }
                    elif response.status_code == 404:
                        return {
                            'success': False,
                            'error': f'Route not found: {url}'
                        }
                    elif response.status_code == 200:
                        try:
                            return response.json()
                        except json.JSONDecodeError as e:
                            self.log_error(f"Failed to parse JSON response: {e}")
                            self.log_error(f"Response content: {response.text[:200]}...")
                            return {
                                'success': False,
                                'error': f'Invalid JSON response from server. Content: {response.text[:100]}...'
                            }
                    else:
                        return {
                            'success': False, 
                            'error': f'HTTP {response.status_code}: {response.text}'
                        }
                except Exception as e:
                    self.log_error(f"Remote backend request failed: {e}")
                    return {'success': False, 'error': str(e)}
            else:
                # This shouldn't happen if you're using remote backend
                self.log_error(f"Backend missing required attributes. Type: {type(self.backend).__name__}")
                self.log_error(f"Has base_url: {hasattr(self.backend, 'base_url')}")
                self.log_error(f"Has session: {hasattr(self.backend, 'session')}")
                return {'success': False, 'error': 'Remote backend not properly initialized'}
        
        # Fall back to normal operation execution
        return super().execute_operation(model, operation, data)
    
    def _get_route_details_local(self, rule, app):
        """Get route details for local backend"""
        endpoint_func = app.view_functions.get(rule.endpoint)
        
        func_info = {}
        if endpoint_func:
            import inspect
            func_info['docstring'] = inspect.getdoc(endpoint_func)
            func_info['module'] = getattr(endpoint_func, '__module__', 'Unknown')
            func_info['function'] = getattr(endpoint_func, '__name__', 'Unknown')
            func_info['is_class_based'] = hasattr(endpoint_func, 'view_class')
        
        route_details = {
            'rule': rule.rule,
            'endpoint': rule.endpoint,
            'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
            'arguments': list(rule.arguments) if rule.arguments else [],
            'function_info': func_info
        }
        
        if '.' in rule.endpoint:
            route_details['blueprint'] = rule.endpoint.split('.')[0]
        else:
            route_details['blueprint'] = None
            
        return route_details


def create_parser():
    """Create argument parser for routes CLI"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List all routes
    list_parser = subparsers.add_parser('list', help='List all routes')
    list_parser.add_argument(
        '-f', '--format',
        choices=['table', 'json', 'tree', 'simple'],
        default='table',
        help='Output format'
    )
    list_parser.add_argument(
        '-s', '--sort',
        choices=['path', 'endpoint', 'blueprint'],
        default='path',
        help='Sort routes by'
    )
    
    # List blueprints
    bp_parser = subparsers.add_parser('blueprints', help='List all blueprints')
    bp_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show routes for each blueprint'
    )
    
    # Summary
    subparsers.add_parser('summary', help='Show routes summary statistics')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search routes by pattern')
    search_parser.add_argument('pattern', help='Search pattern')
    
    # Export
    export_parser = subparsers.add_parser('export', help='Export routes for documentation')
    export_parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    
    return parser


def main():
    """Main entry point for routes CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create CLI instance
    cli = RoutesCLI()
    
    try:
        # Execute command
        if args.command == 'list':
            success = cli.list_all_routes(
                format_type=args.format,
                sort_by=args.sort
            )
        elif args.command == 'blueprints':
            success = cli.list_blueprints(verbose=args.verbose)
        elif args.command == 'summary':
            success = cli.get_summary()
        elif args.command == 'search':
            success = cli.search_routes(args.pattern)
        elif args.command == 'export':
            success = cli.export_routes(output_file=args.output)
        else:
            parser.print_help()
            success = False
        
        return 0 if success else 1
        
    except Exception as e:
        cli.output_error(f"Command failed: {e}")
        return 1
    finally:
        cli.close()


if __name__ == '__main__':
    sys.exit(main())