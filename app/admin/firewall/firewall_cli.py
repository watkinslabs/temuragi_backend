#!/usr/bin/env python3
"""
Firewall CLI Management Tool
Manage IP whitelist/blacklist patterns from command line
"""

import argparse
import sys
import os
from tabulate import tabulate

# Add your app path to import the model and config
sys.path.append('/web/temuragi')
from app.register_db import register_models_for_cli, get_model
from app.base_cli import  BaseCLI


class FirewallCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="firewall", 
            log_file="logs/firewall_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )
        
        self.log_info("Starting firewall CLI initialization")
        
        try:
            # Get the Firewall model from registry
            self.firewall_model = self.get_model('Firewall')
            if not self.firewall_model:
                self.log_error("Firewall model not found in registry")
                raise Exception("Firewall model not found in registry")
            
            self.log_info("Firewall model loaded successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize firewall CLI: {e}")
            raise

    def list_patterns(self, pattern_type=None, show_inactive=False):
        """List all firewall patterns"""
        self.log_info(f"Listing patterns: type={pattern_type}, show_inactive={show_inactive}")
        
        try:
            query = self.session.query(self.firewall_model)

            if not show_inactive:
                query = query.filter(self.firewall_model.is_active == True)
                self.log_debug("Filtering for active patterns only")

            if pattern_type:
                query = query.filter(self.firewall_model.ip_type == pattern_type)
                self.log_debug(f"Filtering for pattern type: {pattern_type}")

            patterns = query.order_by(self.firewall_model.order, self.firewall_model.ip_pattern).all()
            
            self.log_info(f"Found {len(patterns)} patterns")

            if not patterns:
                self.log_debug("No patterns found matching criteria")
                self.output_info("No patterns found")
                return 0

            headers = ['ID', 'Pattern', 'Type', 'Order', 'Description', 'Active']
            rows = []

            for pattern in patterns:
                rows.append([
                    str(pattern.uuid)[:8] + '...',
                    pattern.ip_pattern,
                    pattern.ip_type,
                    pattern.order,
                    pattern.description or '',
                    'Yes' if pattern.is_active else 'No'
                ])

            self.output_table(rows, headers=headers)
            self.log_debug("Pattern list displayed to user")
            return 0
            
        except Exception as e:
            self.log_error(f"Error listing patterns: {e}")
            self.output_error(f"Error listing patterns: {e}")
            return 1

    def add_pattern(self, ip_pattern, ip_type, description=None, order=100):
        """Add a new firewall pattern"""
        self.log_info(f"Adding pattern: {ip_pattern} ({ip_type}), order={order}")
        self.log_debug(f"Pattern details: description='{description}'")
        
        try:
            success, message = self.firewall_model.add_pattern(
                self.session, ip_pattern, ip_type, description, order
            )

            if success:
                self.log_info(f"Pattern added successfully: {ip_pattern}")
                self.output_success(f"{message}: {ip_pattern}")
                return 0
            else:
                self.log_warning(f"Failed to add pattern: {message}")
                self.output_error(f"{message}: {ip_pattern}")
                return 1
                
        except Exception as e:
            self.log_error(f"Error adding pattern {ip_pattern}: {e}")
            self.output_error(f"Error adding pattern: {e}")
            return 1

    def delete_pattern(self, pattern_id, hard_delete=False):
        """Delete a firewall pattern"""
        delete_type = "hard" if hard_delete else "soft"
        self.log_info(f"Deleting pattern {pattern_id} ({delete_type} delete)")
        
        try:
            if hard_delete:
                self.log_warning(f"Performing HARD delete on pattern {pattern_id}")
                success, message = self.firewall_model.hard_delete_pattern(self.session, pattern_id)
            else:
                self.log_debug(f"Performing soft delete on pattern {pattern_id}")
                success, message = self.firewall_model.delete_pattern(self.session, pattern_id)

            if success:
                self.log_info(f"Pattern deleted successfully: {pattern_id}")
                self.output_success(message)
                return 0
            else:
                self.log_warning(f"Failed to delete pattern: {message}")
                self.output_error(message)
                return 1
                
        except Exception as e:
            self.log_error(f"Error deleting pattern {pattern_id}: {e}")
            self.output_error(f"Error deleting pattern: {e}")
            return 1

    def update_pattern(self, pattern_id, ip_type=None, description=None, active=None, order=None):
        """Update a firewall pattern"""
        updates = []
        if ip_type: updates.append(f"type={ip_type}")
        if description: updates.append(f"description={description}")
        if active is not None: updates.append(f"active={active}")
        if order is not None: updates.append(f"order={order}")
        
        self.log_info(f"Updating pattern {pattern_id}: {', '.join(updates) if updates else 'no changes'}")
        
        try:
            success, message = self.firewall_model.update_pattern(
                self.session, pattern_id, ip_type, description, active, order
            )

            if success:
                self.log_info(f"Pattern updated successfully: {pattern_id}")
                self.output_success(message)
                return 0
            else:
                self.log_warning(f"Failed to update pattern: {message}")
                self.output_error(message)
                return 1
                
        except Exception as e:
            self.log_error(f"Error updating pattern {pattern_id}: {e}")
            self.output_error(f"Error updating pattern: {e}")
            return 1

    def check_ip(self, ip_address):
        """Check if an IP would be allowed or blocked"""
        self.log_info(f"Checking IP access: {ip_address}")
        
        try:
            allowed, reason = self.firewall_model.check_ip_access(self.session, ip_address)

            status = "ALLOWED" if allowed else "BLOCKED"
            self.log_info(f"IP {ip_address} check result: {status} - {reason}")
            
            self.output_info(f"IP {ip_address}: {status}")
            self.output_info(f"Reason: {reason}")
            return 0
            
        except Exception as e:
            self.log_error(f"Error checking IP {ip_address}: {e}")
            self.output_error(f"Error checking IP: {e}")
            return 1

    def find_pattern(self, search_term):
        """Find patterns by ID or IP pattern"""
        self.log_info(f"Finding pattern: {search_term}")
        
        try:
            self.log_debug("Attempting to find by UUID first")
            # Try to find by UUID first
            pattern = self.firewall_model.find_by_id(self.session, search_term)

            if not pattern:
                self.log_debug("UUID search failed, trying IP pattern search")
                # Try to find by IP pattern
                pattern = self.firewall_model.find_by_pattern(self.session, search_term)

            if pattern:
                self.log_info(f"Pattern found: {pattern.ip_pattern} (ID: {pattern.uuid})")
                
                headers = ['Field', 'Value']
                rows = [
                    ['ID', str(pattern.uuid)],
                    ['Pattern', pattern.ip_pattern],
                    ['Type', pattern.ip_type],
                    ['Order', pattern.order],
                    ['Description', pattern.description or ''],
                    ['Active', 'Yes' if pattern.is_active else 'No'],
                    ['Created', pattern.created_at.strftime('%Y-%m-%d %H:%M:%S')],
                    ['Updated', pattern.updated_at.strftime('%Y-%m-%d %H:%M:%S')]
                ]
                self.output_table(rows, headers=headers)
                return 0
            else:
                self.log_warning(f"Pattern not found: {search_term}")
                self.output_warning(f"Pattern not found: {search_term}")
                return 1
                
        except Exception as e:
            self.log_error(f"Error finding pattern {search_term}: {e}")
            self.output_error(f"Error finding pattern: {e}")
            return 1

    def emergency_unban(self, ip_pattern):
        """Emergency unban - remove blocking rules for an IP"""
        self.log_warning(f"EMERGENCY UNBAN requested for: {ip_pattern}")
        
        try:
            patterns = self.session.query(self.firewall_model).filter(
                self.firewall_model.ip_pattern == ip_pattern,
                self.firewall_model.ip_type == 'block',
                self.firewall_model.is_active == True
            ).all()

            self.log_debug(f"Found {len(patterns)} active blocking rules for {ip_pattern}")

            if not patterns:
                self.log_info(f"No active blocking rules found for {ip_pattern}")
                self.output_info(f"No active blocking rules found for {ip_pattern}")
                return 0

            for pattern in patterns:
                self.log_debug(f"Deactivating blocking rule: {pattern.uuid}")
                pattern.is_active = False

            self.session.commit()
            self.log_critical(f"EMERGENCY UNBAN COMPLETED: removed {len(patterns)} rule(s) for {ip_pattern}")
            self.output_success(f"Removed {len(patterns)} blocking rule(s) for {ip_pattern}")
            return 0
            
        except Exception as e:
            self.log_error(f"Error during emergency unban for {ip_pattern}: {e}")
            self.output_error(f"Error during emergency unban: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing firewall CLI")
        super().close()


def main():
    """Entry point for master CLI loader"""
    parser = argparse.ArgumentParser(description='Firewall CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'], 
                       help='Override table format (default from config)')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List firewall patterns')
    list_parser.add_argument('--type', choices=['allow', 'block'], help='Filter by pattern type')
    list_parser.add_argument('--all', action='store_true', help='Show inactive patterns too')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add firewall pattern')
    add_parser.add_argument('pattern', help='IP address or CIDR pattern')
    add_parser.add_argument('type', choices=['allow', 'block'], help='Pattern type')
    add_parser.add_argument('--description', help='Pattern description')
    add_parser.add_argument('--order', type=int, default=100, help='Priority order (lower = higher priority)')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete firewall pattern')
    delete_parser.add_argument('pattern_id', help='Pattern ID or IP pattern')
    delete_parser.add_argument('--hard', action='store_true', help='Permanently delete (default: soft delete)')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update firewall pattern')
    update_parser.add_argument('pattern_id', help='Pattern ID')
    update_parser.add_argument('--type', choices=['allow', 'block'], help='Update pattern type')
    update_parser.add_argument('--description', help='Update description')
    update_parser.add_argument('--active', choices=['true', 'false'], help='Set active status')
    update_parser.add_argument('--order', type=int, help='Update priority order')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check IP access')
    check_parser.add_argument('ip', help='IP address to check')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find pattern by ID or IP')
    find_parser.add_argument('search', help='Pattern ID or IP pattern')

    # Emergency unban command
    unban_parser = subparsers.add_parser('unban', help='Emergency unban IP (remove block rules)')
    unban_parser.add_argument('ip', help='IP address to unban')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = FirewallCLI(
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
            return cli.list_patterns(args.type, args.all)

        elif args.command == 'add':
            return cli.add_pattern(args.pattern, args.type, args.description, args.order)

        elif args.command == 'delete':
            return cli.delete_pattern(args.pattern_id, args.hard)

        elif args.command == 'update':
            active = None
            if args.active:
                active = args.active.lower() == 'true'
            return cli.update_pattern(args.pattern_id, args.type, args.description, active, args.order)

        elif args.command == 'check':
            return cli.check_ip(args.ip)

        elif args.command == 'find':
            return cli.find_pattern(args.search)

        elif args.command == 'unban':
            return cli.emergency_unban(args.ip)

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