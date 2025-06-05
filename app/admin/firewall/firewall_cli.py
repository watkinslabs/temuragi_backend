#!/usr/bin/env python3
"""
Firewall CLI Management Tool
Manage IP whitelist/blacklist patterns from command line
"""

import argparse
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Add your app path to import the model and config
sys.path.append('/web/temuragi')
from app.config import config
from app.admin.firewall.firewall_model import Firewall


class FirewallCLI:
    def __init__(self, db_config=None):
        """Initialize CLI with database connection"""
        if db_config:
            self.engine = create_engine(db_config)
        else:
            # Use config.py database URI
            self.engine = create_engine(config['DATABASE_URI'])
        
        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()
    
    def list_patterns(self, pattern_type=None, show_inactive=False):
        """List all firewall patterns"""
        query = self.session.query(Firewall)
        
        if not show_inactive:
            query = query.filter(Firewall.active == True)
        
        if pattern_type:
            query = query.filter(Firewall.ip_type == pattern_type)
        
        patterns = query.order_by(Firewall.order, Firewall.ip_pattern).all()
        
        if not patterns:
            print("No patterns found")
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
                'Yes' if pattern.active else 'No'
            ])
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        return 0
    
    def add_pattern(self, ip_pattern, ip_type, description=None, order=100):
        """Add a new firewall pattern"""
        success, message = Firewall.add_pattern(
            self.session, ip_pattern, ip_type, description, order
        )
        
        if success:
            print(f"✓ {message}: {ip_pattern}")
            return 0
        else:
            print(f"✗ {message}: {ip_pattern}")
            return 1
    
    def delete_pattern(self, pattern_id, hard_delete=False):
        """Delete a firewall pattern"""
        if hard_delete:
            success, message = Firewall.hard_delete_pattern(self.session, pattern_id)
        else:
            success, message = Firewall.delete_pattern(self.session, pattern_id)
        
        if success:
            print(f"✓ {message}")
            return 0
        else:
            print(f"✗ {message}")
            return 1
    
    def update_pattern(self, pattern_id, ip_type=None, description=None, active=None, order=None):
        """Update a firewall pattern"""
        success, message = Firewall.update_pattern(
            self.session, pattern_id, ip_type, description, active, order
        )
        
        if success:
            print(f"✓ {message}")
            return 0
        else:
            print(f"✗ {message}")
            return 1
    
    def check_ip(self, ip_address):
        """Check if an IP would be allowed or blocked"""
        allowed, reason = Firewall.check_ip_access(self.session, ip_address)
        
        status = "ALLOWED" if allowed else "BLOCKED"
        print(f"IP {ip_address}: {status}")
        print(f"Reason: {reason}")
        return 0
    
    def find_pattern(self, search_term):
        """Find patterns by ID or IP pattern"""
        # Try to find by UUID first
        pattern = Firewall.find_by_id(self.session, search_term)
        
        if not pattern:
            # Try to find by IP pattern
            pattern = Firewall.find_by_pattern(self.session, search_term)
        
        if pattern:
            headers = ['Field', 'Value']
            rows = [
                ['ID', str(pattern.uuid)],
                ['Pattern', pattern.ip_pattern],
                ['Type', pattern.ip_type],
                ['Order', pattern.order],
                ['Description', pattern.description or ''],
                ['Active', 'Yes' if pattern.active else 'No'],
                ['Created', pattern.created_at.strftime('%Y-%m-%d %H:%M:%S')],
                ['Updated', pattern.updated_at.strftime('%Y-%m-%d %H:%M:%S')]
            ]
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            return 0
        else:
            print(f"Pattern not found: {search_term}")
            return 1
    
    def emergency_unban(self, ip_pattern):
        """Emergency unban - remove blocking rules for an IP"""
        patterns = self.session.query(Firewall).filter(
            Firewall.ip_pattern == ip_pattern,
            Firewall.ip_type == 'block',
            Firewall.active == True
        ).all()
        
        if not patterns:
            print(f"No active blocking rules found for {ip_pattern}")
            return 0
        
        for pattern in patterns:
            pattern.active = False
        
        self.session.commit()
        print(f"✓ Removed {len(patterns)} blocking rule(s) for {ip_pattern}")
        return 0


def main():
    """Entry point for master CLI loader"""
    parser = argparse.ArgumentParser(description='Firewall CLI Management Tool')
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
    try:
        cli = FirewallCLI()
    except Exception as e:
        print(f"✗ Error: {e}")
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
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())