#!/usr/bin/env python3
"""
Routes CLI - Display all registered Flask routes
Shows routes organized by blueprint with detailed information
"""

import sys
import argparse
from tabulate import tabulate
from collections import defaultdict

# Add your app path to import the model and config
sys.path.append('/web/temuragi')

from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Get Route info"


class RoutesCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="routes",
            log_file="logs/routes_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting routes CLI initialization")

        try:
            # Import app factory here to avoid circular imports
            from app.app import create_app
            self.app = create_app()
            self.log_info("Flask application created successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize routes CLI: {e}")
            raise

    def format_route_table(self, routes_by_blueprint, show_details=False):
        """Format routes into a readable table"""
        self.log_debug(f"Formatting route table with {len(routes_by_blueprint)} blueprints")

        if not routes_by_blueprint:
            self.log_warning("No routes found to format")
            return "No routes found"

        output = []

        for blueprint_name, routes in sorted(routes_by_blueprint.items()):
            output.append(f"\n{blueprint_name}:")

            if not routes:
                output.append("  No routes")
                continue

            for route in sorted(routes, key=lambda x: x['rule']):
                methods = ', '.join(sorted(route['methods'] - {'OPTIONS', 'HEAD'}))

                if show_details:
                    # More compact detailed view
                    func_name = route['function_name'].split('.')[-1]  # Just function name
                    output.append(f"  {route['rule']:<30} [{methods:<10}] {route['endpoint']} -> {func_name}")
                else:
                    # Simple view
                    output.append(f"  {route['rule']:<30} [{methods}]")

        return '\n'.join(output)

    def collect_routes(self):
        """Collect all routes organized by blueprint"""
        self.log_info("Collecting application routes")
        routes_by_blueprint = defaultdict(list)

        for rule in self.app.url_map.iter_rules():
            # Get endpoint info
            endpoint = rule.endpoint

            # Determine blueprint
            if '.' in endpoint:
                blueprint_name = endpoint.split('.')[0]
            else:
                blueprint_name = 'main'

            # Get view function
            try:
                view_func = self.app.view_functions.get(endpoint)
                if view_func:
                    function_name = f"{view_func.__module__}.{view_func.__name__}"
                else:
                    function_name = "Unknown"
            except:
                function_name = "Error"

            route_info = {
                'rule': rule.rule,
                'endpoint': endpoint,
                'methods': rule.methods,
                'function_name': function_name,
                'blueprint': blueprint_name
            }

            routes_by_blueprint[blueprint_name].append(route_info)

        route_count = sum(len(routes) for routes in routes_by_blueprint.values())
        self.log_info(f"Collected {route_count} routes across {len(routes_by_blueprint)} blueprints")

        return dict(routes_by_blueprint)

    def show_route_statistics(self, routes_by_blueprint):
        """Display route statistics"""
        self.log_debug("Generating route statistics")
        total_routes = sum(len(routes) for routes in routes_by_blueprint.values())
        blueprint_count = len(routes_by_blueprint)

        self.output_info(f"Route Statistics:")
        self.output_info(f"   Total Routes: {total_routes}")
        self.output_info(f"   Blueprints: {blueprint_count}")

        # Routes per blueprint
        self.output_info(f"Routes per Blueprint:")
        for blueprint, routes in sorted(routes_by_blueprint.items()):
            self.output_info(f"   {blueprint}: {len(routes)} routes")

    def filter_routes(self, routes_by_blueprint, pattern=None, blueprint=None):
        """Filter routes by pattern or blueprint"""
        self.log_debug(f"Filtering routes: pattern={pattern}, blueprint={blueprint}")

        if not pattern and not blueprint:
            return routes_by_blueprint

        filtered = defaultdict(list)

        for bp_name, routes in routes_by_blueprint.items():
            # Filter by blueprint if specified
            if blueprint and bp_name != blueprint:
                continue

            # Filter by pattern if specified
            if pattern:
                matching_routes = [
                    r for r in routes
                    if pattern.lower() in r['rule'].lower() or
                       pattern.lower() in r['endpoint'].lower()
                ]
                if matching_routes:
                    filtered[bp_name] = matching_routes
            else:
                filtered[bp_name] = routes

        filtered_count = sum(len(routes) for routes in filtered.values())
        self.log_debug(f"Filter resulted in {filtered_count} routes")

        return dict(filtered)

    def list_blueprints(self):
        """List available blueprints"""
        self.log_info("Listing available blueprints")

        try:
            with self.app.app_context():
                routes_by_blueprint = self.collect_routes()

                if not routes_by_blueprint:
                    self.output_warning("No blueprints found")
                    return 1

                headers = ['Blueprint', 'Route Count']
                rows = []

                for blueprint in sorted(routes_by_blueprint.keys()):
                    count = len(routes_by_blueprint[blueprint])
                    rows.append([blueprint, count])

                self.output_info("Available Blueprints:")
                self.output_table(rows, headers=headers)

                return 0

        except Exception as e:
            self.log_error(f"Error listing blueprints: {e}")
            self.output_error(f"Error listing blueprints: {e}")
            return 1

    def show_statistics(self):
        """Show route statistics"""
        self.log_info("Generating route statistics")

        try:
            with self.app.app_context():
                routes_by_blueprint = self.collect_routes()

                if not routes_by_blueprint:
                    self.output_warning("No routes found")
                    return 1

                self.show_route_statistics(routes_by_blueprint)
                return 0

        except Exception as e:
            self.log_error(f"Error generating statistics: {e}")
            self.output_error(f"Error generating statistics: {e}")
            return 1

    def show_routes(self, show_details=False, blueprint_filter=None, pattern_filter=None):
        """Show routes with optional filtering"""
        filter_desc = []
        if blueprint_filter:
            filter_desc.append(f"blueprint={blueprint_filter}")
        if pattern_filter:
            filter_desc.append(f"pattern={pattern_filter}")

        filter_str = f" with filters: {', '.join(filter_desc)}" if filter_desc else ""
        self.log_info(f"Showing routes{filter_str}")

        try:
            with self.app.app_context():
                # Collect all routes
                routes_by_blueprint = self.collect_routes()

                if not routes_by_blueprint:
                    self.output_warning("No routes found")
                    return 1

                # Filter routes
                filtered_routes = self.filter_routes(
                    routes_by_blueprint,
                    pattern=pattern_filter,
                    blueprint=blueprint_filter
                )

                if not filtered_routes:
                    self.output_warning("No routes found matching criteria")
                    return 1

                # Display routes
                self.output_info("Application Routes:")
                route_table = self.format_route_table(filtered_routes, show_details)
                print(route_table)

                # Show summary
                total_filtered = sum(len(routes) for routes in filtered_routes.values())
                if pattern_filter or blueprint_filter:
                    total_all = sum(len(routes) for routes in routes_by_blueprint.values())
                    self.output_info(f"Showing {total_filtered} of {total_all} total routes")
                else:
                    self.output_info(f"Total: {total_filtered} routes")

                return 0

        except Exception as e:
            self.log_error(f"Error showing routes: {e}")
            self.output_error(f"Error showing routes: {e}")
            return 1

    def find_route(self, search_term):
        """Find specific route by pattern or endpoint"""
        self.log_info(f"Finding route: {search_term}")

        try:
            with self.app.app_context():
                routes_by_blueprint = self.collect_routes()
                found_routes = []

                # Search through all routes
                for blueprint_name, routes in routes_by_blueprint.items():
                    for route in routes:
                        if (search_term.lower() in route['rule'].lower() or
                            search_term.lower() in route['endpoint'].lower() or
                            search_term.lower() in route['function_name'].lower()):
                            found_routes.append((blueprint_name, route))

                if not found_routes:
                    self.output_warning(f"No routes found matching: {search_term}")
                    return 1

                self.log_info(f"Found {len(found_routes)} matching routes")

                # Display found routes in table format
                headers = ['Blueprint', 'Rule', 'Methods', 'Endpoint', 'Function']
                rows = []

                for blueprint_name, route in found_routes:
                    methods = ', '.join(sorted(route['methods'] - {'OPTIONS', 'HEAD'}))
                    func_name = route['function_name'].split('.')[-1]
                    rows.append([
                        blueprint_name,
                        route['rule'],
                        methods,
                        route['endpoint'],
                        func_name
                    ])

                self.output_info(f"Routes matching '{search_term}':")
                self.output_table(rows, headers=headers)

                return 0

        except Exception as e:
            self.log_error(f"Error finding route {search_term}: {e}")
            self.output_error(f"Error finding route: {e}")
            return 1

    def show_route_details(self, endpoint):
        """Show detailed information about a specific route"""
        self.log_info(f"Showing details for endpoint: {endpoint}")

        try:
            with self.app.app_context():
                # Find the specific route
                for rule in self.app.url_map.iter_rules():
                    if rule.endpoint == endpoint:
                        view_func = self.app.view_functions.get(endpoint)

                        # Get function details
                        if view_func:
                            func_module = view_func.__module__
                            func_name = view_func.__name__
                            func_doc = view_func.__doc__ or "No documentation"
                        else:
                            func_module = "Unknown"
                            func_name = "Unknown"
                            func_doc = "Unknown"

                        # Format methods
                        methods = ', '.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))

                        # Create detail table
                        headers = ['Property', 'Value']
                        rows = [
                            ['Endpoint', rule.endpoint],
                            ['Rule', rule.rule],
                            ['Methods', methods],
                            ['Function Module', func_module],
                            ['Function Name', func_name],
                            ['Documentation', func_doc[:100] + '...' if len(func_doc) > 100 else func_doc]
                        ]

                        self.output_info(f"Route Details: {endpoint}")
                        self.output_table(rows, headers=headers)

                        return 0

                self.output_warning(f"Route endpoint not found: {endpoint}")
                return 1

        except Exception as e:
            self.log_error(f"Error showing route details for {endpoint}: {e}")
            self.output_error(f"Error showing route details: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing routes CLI")
        super().close()


def main():
    """Entry point for routes CLI"""
    parser = argparse.ArgumentParser(
        description="Display Flask application routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  routes list                       # Show all routes (simple view)
  routes details                    # Show detailed route info
  routes stats                      # Show route statistics
  routes blueprints                 # List available blueprints
  routes blueprint admin            # Show only admin routes
  routes filter api                 # Filter routes containing 'api'
  routes find user_profile          # Find specific route
  routes show auth.login            # Show details for specific endpoint
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format (default from config)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command (default behavior)
    list_parser = subparsers.add_parser('list', help='List all routes (simple view)')

    # Details command
    details_parser = subparsers.add_parser('details', help='Show detailed route information')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show route statistics')

    # Blueprints command
    blueprints_parser = subparsers.add_parser('blueprints', help='List available blueprints')

    # Blueprint command
    blueprint_parser = subparsers.add_parser('blueprint', help='Show routes for specific blueprint')
    blueprint_parser.add_argument('name', help='Blueprint name')

    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Filter routes by pattern')
    filter_parser.add_argument('pattern', help='Filter pattern')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find routes by search term')
    find_parser.add_argument('search', help='Search term')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show details for specific endpoint')
    show_parser.add_argument('endpoint', help='Route endpoint')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = RoutesCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute command
    try:
        if args.command == 'list':
            return cli.show_routes()

        elif args.command == 'details':
            return cli.show_routes(show_details=True)

        elif args.command == 'stats':
            return cli.show_statistics()

        elif args.command == 'blueprints':
            return cli.list_blueprints()

        elif args.command == 'blueprint':
            return cli.show_routes(blueprint_filter=args.name)

        elif args.command == 'filter':
            return cli.show_routes(pattern_filter=args.pattern)

        elif args.command == 'find':
            return cli.find_route(args.search)

        elif args.command == 'show':
            return cli.show_route_details(args.endpoint)

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error during command execution: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up session
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())