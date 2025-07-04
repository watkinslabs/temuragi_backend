#!/usr/bin/env python3
"""
Role CLI Management Tool
Manage roles and permissions from command line
"""

import argparse
import sys
from tabulate import tabulate

# Add your app path to import the model and config
sys.path.append('/web/ahoy2.radiatorusa.com')

from app.base.cli_v1 import BaseCLI

CLI_DESCRIPTION = "Manages roles (use permission CLI for permissions)"

class RoleCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="role",
            log_file="logs/role_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting role CLI initialization")

        try:
            # Get models from registry
            self.role_model = self.get_model('Role')
            
            if not self.role_model:
                self.log_error("Role model not found in registry")
                raise Exception("Role model not found in registry")

            self.log_info("Role model loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize role CLI: {e}")
            raise

    def list_roles(self, show_inactive=False):
        """List all roles"""
        self.log_info(f"Listing roles: show_inactive={show_inactive}")

        try:
            query = self.session.query(self.role_model)

            if not show_inactive:
                query = query.filter(self.role_model.is_active == True)
                self.log_debug("Filtering for active roles only")

            roles = query.order_by(self.role_model.name).all()

            self.log_info(f"Found {len(roles)} roles")

            if not roles:
                self.log_debug("No roles found matching criteria")
                self.output_info("No roles found")
                return 0

            headers = ['UUID', 'Name', 'Display', 'Description', 'Admin', 'Active', 'Users', 'Permissions']
            rows = []

            for role in roles:
                user_count = len(role.users) if role.users else 0
                permission_count = len(role.permissions) if role.permissions else 0
                
                rows.append([
                    str(role.id),
                    role.name,
                    role.display,
                    (role.description or '')[:50] + ('...' if role.description and len(role.description) > 50 else ''),
                    'Yes' if role.is_admin else 'No',
                    'Yes' if role.is_active else 'No',
                    str(user_count),
                    str(permission_count)
                ])

            self.output_table(rows, headers=headers)
            self.log_debug("Role list displayed to user")
            return 0

        except Exception as e:
            self.log_error(f"Error listing roles: {e}")
            self.output_error(f"Error listing roles: {e}")
            return 1

    def add_role(self, name, display, description=None, is_admin=False):
        """Add a new role"""
        self.log_info(f"Adding role: {name} ({display}), admin={is_admin}")

        try:
            # Check if role already exists
            existing_role = self.session.query(self.role_model).filter(self.role_model.name == name).first()
            if existing_role:
                self.log_warning(f"Role already exists: {name}")
                self.output_error(f"Role already exists: {name}")
                return 1

            # Create new role
            new_role = self.role_model(
                name=name,
                display=display,
                description=description,
                is_admin=is_admin
            )

            self.session.add(new_role)
            self.session.commit()

            self.log_info(f"Role added successfully: {name} (UUID: {new_role.id})")
            self.output_success(f"Role created: {name}")
            self.output_info(f"UUID: {new_role.id}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error adding role {name}: {e}")
            self.output_error(f"Error adding role: {e}")
            return 1

    def delete_role(self, role_name, hard_delete=False):
        """Delete a role (soft or hard delete)"""
        delete_type = "hard" if hard_delete else "soft"
        self.log_info(f"Deleting role {role_name} ({delete_type} delete)")

        try:
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            # Check if role has users
            user_count = len(role.users) if role.users else 0
            if user_count > 0 and hard_delete:
                self.log_warning(f"Cannot hard delete role {role_name}: has {user_count} users")
                self.output_error(f"Cannot delete role {role_name}: has {user_count} users assigned")
                return 1

            if hard_delete:
                self.log_warning(f"Performing HARD delete on role {role_name}")
                self.session.delete(role)
            else:
                self.log_debug(f"Performing soft delete on role {role_name}")
                role.is_active = False

            self.session.commit()

            action = "deleted permanently" if hard_delete else "deactivated"
            self.log_info(f"Role {action} successfully: {role_name}")
            self.output_success(f"Role {action}: {role_name}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error deleting role {role_name}: {e}")
            self.output_error(f"Error deleting role: {e}")
            return 1

    def update_role(self, role_name, display=None, description=None, is_admin=None, active=None):
        """Update a role"""
        updates = []
        if display: updates.append(f"display={display}")
        if description: updates.append(f"description={description}")
        if is_admin is not None: updates.append(f"admin={is_admin}")
        if active is not None: updates.append(f"active={active}")

        self.log_info(f"Updating role {role_name}: {', '.join(updates) if updates else 'no changes'}")

        try:
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            # Update fields
            if display:
                role.display = display
            if description:
                role.description = description
            if is_admin is not None:
                role.is_admin = is_admin
            if active is not None:
                role.is_active = active

            self.session.commit()

            self.log_info(f"Role updated successfully: {role_name}")
            self.output_success(f"Role updated: {role_name}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error updating role {role_name}: {e}")
            self.output_error(f"Error updating role: {e}")
            return 1

    def show_role_details(self, role_name):
        """Show detailed role information"""
        self.log_info(f"Showing details for role {role_name}")

        try:
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            user_count = len(role.users) if role.users else 0
            permission_count = len(role.permissions) if role.permissions else 0

            headers = ['Field', 'Value']
            rows = [
                ['UUID', str(role.id)],
                ['Name', role.name],
                ['Display', role.display],
                ['Description', role.description or 'None'],
                ['Admin', 'Yes' if role.is_admin else 'No'],
                ['Active', 'Yes' if role.is_active else 'No'],
                ['User Count', str(user_count)],
                ['Permission Count', str(permission_count)],
                ['Created', role.created_at.strftime('%Y-%m-%d %H:%M:%S') if role.created_at else 'N/A'],
                ['Updated', role.updated_at.strftime('%Y-%m-%d %H:%M:%S') if role.updated_at else 'N/A']
            ]

            self.output_table(rows, headers=headers)
            
            # Show users if any
            if user_count > 0:
                self.output_info(f"\nUsers with this role ({user_count}):")
                user_headers = ['Username', 'Email', 'Active']
                user_rows = []
                for user in role.users:
                    user_rows.append([
                        user.username,
                        user.email,
                        'Yes' if user.is_active else 'No'
                    ])
                self.output_table(user_rows, headers=user_headers)

            # Show permissions if any
            if permission_count > 0:
                self.output_info(f"\nPermissions for this role ({permission_count}):")
                self.output_info("Use 'tmcli permission role-permissions {role_name}' to view permissions")

            self.log_debug("Role details displayed")
            return 0

        except Exception as e:
            self.log_error(f"Error showing role details for {role_name}: {e}")
            self.output_error(f"Error showing role details: {e}")
            return 1

    def list_role_permissions(self, role_name):
        """List permissions for a role (redirects to permission CLI functionality)"""
        self.log_info(f"Listing permissions for role: {role_name}")
        self.output_info(f"To view permissions for role '{role_name}', use:")
        self.output_info(f"tmcli permission role-permissions {role_name}")
        return 0

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing role CLI")
        super().close()


def main():
    """Entry point for role CLI"""
    parser = argparse.ArgumentParser(description='Role CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List roles command
    list_parser = subparsers.add_parser('list', help='List roles')
    list_parser.add_argument('--all', action='store_true', help='Show inactive roles too')

    # Add role command
    add_parser = subparsers.add_parser('add', help='Add new role')
    add_parser.add_argument('name', help='Role name (unique)')
    add_parser.add_argument('display', help='Display name')
    add_parser.add_argument('--description', help='Role description')
    add_parser.add_argument('--admin', action='store_true', help='Mark as admin role')

    # Delete role command
    delete_parser = subparsers.add_parser('delete', help='Delete role')
    delete_parser.add_argument('name', help='Role name')
    delete_parser.add_argument('--hard', action='store_true', help='Permanently delete (default: deactivate)')

    # Update role command
    update_parser = subparsers.add_parser('update', help='Update role')
    update_parser.add_argument('name', help='Role name')
    update_parser.add_argument('--display', help='Update display name')
    update_parser.add_argument('--description', help='Update description')
    update_parser.add_argument('--admin', choices=['true', 'false'], help='Set admin status')
    update_parser.add_argument('--active', choices=['true', 'false'], help='Set active status')

    # Show role details command
    show_parser = subparsers.add_parser('show', help='Show role details')
    show_parser.add_argument('name', help='Role name')

    # List role permissions command (helper)
    perms_parser = subparsers.add_parser('permissions', help='Show how to list role permissions')
    perms_parser.add_argument('name', help='Role name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = RoleCLI(
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
            return cli.list_roles(args.all)

        elif args.command == 'add':
            return cli.add_role(args.name, args.display, args.description, args.admin)

        elif args.command == 'delete':
            return cli.delete_role(args.name, args.hard)

        elif args.command == 'update':
            admin = None
            if args.admin:
                admin = args.admin.lower() == 'true'
            active = None
            if args.active:
                active = args.active.lower() == 'true'
            return cli.update_role(args.name, args.display, args.description, admin, active)

        elif args.command == 'show':
            return cli.show_role_details(args.name)

        elif args.command == 'permissions':
            return cli.list_role_permissions(args.name)

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