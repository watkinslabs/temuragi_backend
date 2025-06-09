#!/usr/bin/env python3
"""
Permission CLI Management Tool
Manage  permissions (service:action format) from command line
"""

import argparse
import sys
import os
from tabulate import tabulate

# Add your app path to import the model and config
sys.path.append('/web/temuragi')
from app.register_db import register_models_for_cli, get_model
from app.base_cli import BaseCLI

CLI_DESCRIPTION = "Manages  permissions (service:action format)"

class PermissionCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="permission",
            log_file="logs/permission_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting permission CLI initialization")

        try:
            # Get models from registry
            self.permission_model = self.get_model('Permission')
            self.role_model = self.get_model('Role')
            self.role_permission_model = self.get_model('RolePermission')

            if not self.permission_model:
                self.log_error("Permission model not found in registry")
                raise Exception("Permission model not found in registry")

            if not self.role_model:
                self.log_error("Role model not found in registry")
                raise Exception("Role model not found in registry")

            if not self.role_permission_model:
                self.log_error("RolePermission model not found in registry")
                raise Exception("RolePermission model not found in registry")

            # MenuLink is optional since we moved to  permissions
            self.menu_link_model = self.get_model('MenuLink')
            if not self.menu_link_model:
                self.log_info("MenuLink model not available - using  permissions only")

            self.log_info("Permission models loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize permission CLI: {e}")
            raise

    def list_permissions(self, service_filter=None, show_inactive=False):
        """List all  permissions"""
        if service_filter:
            self.log_info(f"Listing permissions for service: {service_filter}")
        else:
            self.log_info("Listing all permissions")

        try:
            query = self.session.query(self.permission_model)

            if not show_inactive:
                query = query.filter(self.permission_model.is_active == True)
                self.log_debug("Filtering for active permissions only")

            if service_filter:
                query = query.filter(self.permission_model.service == service_filter)
                self.log_debug(f"Filtering for service: {service_filter}")

            permissions = query.order_by(self.permission_model.service, self.permission_model.action).all()

            self.log_info(f"Found {len(permissions)} permissions")

            if not permissions:
                self.output_info("No permissions found")
                return 0

            headers = ['UUID', 'Permission Name', 'Service', 'Action', 'Resource', 'Description', 'Active']
            rows = []

            for perm in permissions:
                description = (perm.description or '')[:50] + ('...' if perm.description and len(perm.description) > 50 else '')
                rows.append([
                    str(perm.uuid),
                    perm.name,
                    perm.service,
                    perm.action,
                    perm.resource or '',
                    description,
                    'Yes' if perm.is_active else 'No'
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing permissions: {e}")
            self.output_error(f"Error listing permissions: {e}")
            return 1


    def add_permission(self, service, action, resource=None, description=None):
        """Add a new  permission"""
        self.log_info(f"Adding permission: {service}:{action}" + (f":{resource}" if resource else ""))

        try:
            success, result = self.permission_model.create_permission(
                self.session, service, action, resource, description
            )

            if success:
                permission = result
                self.log_info(f"Permission added successfully: {permission.name} (UUID: {permission.uuid})")
                self.output_success(f"Permission created: {permission.name}")
                self.output_info(f"UUID: {permission.uuid}")
                return 0
            else:
                self.log_warning(f"Failed to add permission: {result}")
                self.output_error(f"{result}")
                return 1

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error adding permission: {e}")
            self.output_error(f"Error adding permission: {e}")
            return 1

    
    def delete_permission(self, permission_name, hard_delete=False):
        """Delete an  permission"""
        delete_type = "hard" if hard_delete else "soft"
        self.log_info(f"Deleting permission {permission_name} ({delete_type} delete)")

        try:
            permission = self.permission_model.find_by_name(self.session, permission_name)
            if not permission:
                self.log_warning(f"Permission not found: {permission_name}")
                self.output_error(f"Permission not found: {permission_name}")
                return 1

            # Check if permission is assigned to any roles
            role_count = len(permission.role_permissions) if permission.role_permissions else 0
            if role_count > 0 and hard_delete:
                self.log_warning(f"Cannot hard delete permission {permission_name}: assigned to {role_count} roles")
                self.output_error(f"Cannot delete permission {permission_name}: assigned to {role_count} roles")
                return 1

            if hard_delete:
                self.log_warning(f"Performing HARD delete on permission {permission_name}")
                self.session.delete(permission)
            else:
                self.log_debug(f"Performing soft delete on permission {permission_name}")
                permission.is_active = False

            self.session.commit()

            action = "deleted permanently" if hard_delete else "deactivated"
            self.log_info(f"Permission {action} successfully: {permission_name}")
            self.output_success(f"Permission {action}: {permission_name}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error deleting permission {permission_name}: {e}")
            self.output_error(f"Error deleting permission: {e}")
            return 1

    def show_permission_details(self, permission_name):
        """Show detailed  permission information"""
        self.log_info(f"Showing details for permission {permission_name}")

        try:
            permission = self.permission_model.find_by_name(self.session, permission_name)
            if not permission:
                self.log_warning(f"Permission not found: {permission_name}")
                self.output_error(f"Permission not found: {permission_name}")
                return 1

            role_count = len(permission.role_permissions) if permission.role_permissions else 0

            headers = ['Field', 'Value']
            rows = [
                ['UUID', str(permission.uuid)],
                ['Permission Name', permission.name],
                ['Service', permission.service],
                ['Action', permission.action],
                ['Resource', permission.resource or 'None'],
                ['Description', permission.description or 'None'],
                ['Active', 'Yes' if permission.is_active else 'No'],
                ['Assigned to Roles', str(role_count)],
                ['Created', permission.created_at.strftime('%Y-%m-%d %H:%M:%S') if permission.created_at else 'N/A'],
                ['Updated', permission.updated_at.strftime('%Y-%m-%d %H:%M:%S') if permission.updated_at else 'N/A']
            ]

            self.output_table(rows, headers=headers)

            # Show roles that have this permission
            if role_count > 0:
                self.output_info(f"\nRoles with this permission ({role_count}):")
                role_headers = ['Role Name', 'Display', 'Admin']
                role_rows = []
                for rp in permission.role_permissions:
                    if rp.role:
                        role_rows.append([
                            rp.role.name,
                            rp.role.display,
                            'Yes' if rp.role.is_admin else 'No'
                        ])
                self.output_table(role_rows, headers=role_headers)

            self.log_debug("Permission details displayed")
            return 0

        except Exception as e:
            self.log_error(f"Error showing permission details for {permission_name}: {e}")
            self.output_error(f"Error showing permission details: {e}")
            return 1

    def list_services(self):
        """List all services that have permissions"""
        self.log_info("Listing services with permissions")

        try:
            services = self.session.query(self.permission_model.service).distinct().order_by(self.permission_model.service).all()

            if not services:
                self.output_info("No services found")
                return 0

            self.output_info("Services with permissions:")
            for service in services:
                service_name = service[0]
                perm_count = self.session.query(self.permission_model).filter(
                    self.permission_model.service == service_name,
                    self.permission_model.is_active == True
                ).count()
                self.output_info(f"  {service_name} ({perm_count} permissions)")

            return 0

        except Exception as e:
            self.log_error(f"Error listing services: {e}")
            self.output_error(f"Error listing services: {e}")
            return 1

    def grant_permission(self, role_name, permission_name):
        """Grant an  permission to a role"""
        self.log_info(f"Granting permission {permission_name} to role {role_name}")

        try:
            # Find role
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            success, result = self.role_permission_model.grant_permission(
                self.session, role.uuid, permission_name
            )

            if success:
                role_permission = result
                self.log_info(f"Permission granted successfully: {permission_name} to {role_name} (RolePermission UUID: {role_permission.uuid})")
                self.output_success(f"Permission granted to role: {role_name}")
                self.output_info(f"Permission: {permission_name}")
                self.output_info(f"RolePermission UUID: {role_permission.uuid}")
                return 0
            else:
                self.log_warning(f"Failed to grant permission: {result}")
                self.output_error(f"{result}")
                return 1

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error granting permission: {e}")
            self.output_error(f"Error granting permission: {e}")
            return 1

    def revoke_permission(self, role_name, permission_name):
        """Revoke an  permission from a role"""
        self.log_info(f"Revoking permission {permission_name} from role {role_name}")

        try:
            # Find role
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            success, message = self.role_permission_model.revoke_permission(
                self.session, role.uuid, permission_name
            )

            if success:
                self.log_info(f"Permission revoked successfully: {permission_name} from {role_name}")
                self.output_success(f"Permission revoked from role: {role_name}")
                self.output_info(f"Permission: {permission_name}")
                return 0
            else:
                self.log_warning(f"Failed to revoke permission: {message}")
                self.output_error(f"{message}")
                return 1

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error revoking permission: {e}")
            self.output_error(f"Error revoking permission: {e}")
            return 1

    def list_role_permissions(self, role_name):
        """List all  permissions for a specific role"""
        self.log_info(f"Listing permissions for role: {role_name}")

        try:
            role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
            if not role:
                self.log_warning(f"Role not found: {role_name}")
                self.output_error(f"Role not found: {role_name}")
                return 1

            permissions = role.get_permissions(self.session)

            if not permissions:
                self.output_info(f"No permissions found for role: {role_name}")
                return 0

            self.output_info(f"Permissions for role '{role_name}' ({len(permissions)}):")

            headers = ['Permission Name', 'Service', 'Action', 'Resource', 'Description']
            rows = []

            for perm in permissions:
                description = (perm.description or '')[:50] + ('...' if perm.description and len(perm.description) > 50 else '')
                rows.append([
                    perm.name,
                    perm.service,
                    perm.action,
                    perm.resource or '',
                    description
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing role permissions: {e}")
            self.output_error(f"Error listing role permissions: {e}")
            return 1

    def check_user_permission(self, user_identity, permission_name):
        """Check if a user has a specific  permission"""
        self.log_info(f"Checking permission {permission_name} for user {user_identity}")

        try:
            # Get User model
            user_model = self.get_model('User')
            if not user_model:
                self.output_error("User model not available")
                return 1

            # Find user
            user = user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            has_permission = self.role_permission_model.user_has_permission(
                self.session, user.uuid, permission_name
            )

            status = "GRANTED" if has_permission else "DENIED"
            role_name = user.role.name if user.role else 'No Role'

            self.log_info(f"Permission check for {user.username}: {permission_name} = {status}")

            self.output_info(f"User: {user.username}")
            self.output_info(f"Role: {role_name}")
            self.output_info(f"Permission: {permission_name}")
            self.output_info(f"Status: {status}")

            return 0

        except Exception as e:
            self.log_error(f"Error checking user permission: {e}")
            self.output_error(f"Error checking user permission: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing permission CLI")
        super().close()


def main():
    """Entry point for permission CLI"""
    parser = argparse.ArgumentParser(description=' Permission CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List permissions command
    list_parser = subparsers.add_parser('list', help='List  permissions')
    list_parser.add_argument('--service', help='Filter by service name')
    list_parser.add_argument('--all', action='store_true', help='Show inactive permissions too')

    # Add permission command
    add_parser = subparsers.add_parser('add', help='Add new  permission (service:action)')
    add_parser.add_argument('service', help='Service name (e.g., accounting, customer)')
    add_parser.add_argument('action', help='Action name (e.g., read, write, create, delete)')
    add_parser.add_argument('--resource', help='Optional resource specifier')
    add_parser.add_argument('--description', help='Permission description')

    # Delete permission command
    delete_parser = subparsers.add_parser('delete', help='Delete  permission')
    delete_parser.add_argument('permission_name', help='Permission name (e.g., accounting:read)')
    delete_parser.add_argument('--hard', action='store_true', help='Permanently delete (default: deactivate)')

    # Show permission details command
    show_parser = subparsers.add_parser('show', help='Show  permission details')
    show_parser.add_argument('permission_name', help='Permission name (e.g., accounting:read)')

    # List services command
    services_parser = subparsers.add_parser('services', help='List all services with permissions')

    # Grant permission to role command
    grant_parser = subparsers.add_parser('grant', help='Grant  permission to role')
    grant_parser.add_argument('role_name', help='Role name')
    grant_parser.add_argument('permission_name', help='Permission name (e.g., accounting:read)')

    # Revoke permission from role command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke  permission from role')
    revoke_parser.add_argument('role_name', help='Role name')
    revoke_parser.add_argument('permission_name', help='Permission name (e.g., accounting:read)')

    # List role permissions command
    role_perms_parser = subparsers.add_parser('role-permissions', help='List  permissions for a role')
    role_perms_parser.add_argument('role_name', help='Role name')

    # Check user permission command
    check_parser = subparsers.add_parser('check-user', help='Check if user has  permission')
    check_parser.add_argument('user', help='Username or email')
    check_parser.add_argument('permission_name', help='Permission name (e.g., accounting:read)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = PermissionCLI(
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
            return cli.list_permissions(service_filter=args.service, show_inactive=args.all)

        elif args.command == 'add':
            return cli.add_permission(args.service, args.action, args.resource, args.description)


        elif args.command == 'delete':
            return cli.delete_permission(args.permission_name, args.hard)

        elif args.command == 'show':
            return cli.show_permission_details(args.permission_name)

        elif args.command == 'services':
            return cli.list_services()

        elif args.command == 'grant':
            return cli.grant_permission(args.role_name, args.permission_name)

        elif args.command == 'revoke':
            return cli.revoke_permission(args.role_name, args.permission_name)

        elif args.command == 'role-permissions':
            return cli.list_role_permissions(args.role_name)

        elif args.command == 'check-user':
            return cli.check_user_permission(args.user, args.permission_name)

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