#!/usr/bin/env python3
"""
User CLI Management Tool
Manage users from command line - add, delete, lock, unlock, etc.
"""

import argparse
import sys
import os
import getpass
from datetime import datetime, timedelta
from tabulate import tabulate

# Add your app path to import the model and config
sys.path.append('/web/temuragi')
from app.register_db import register_models_for_cli, get_model
from app.base_cli import BaseCLI

CLI_DESCRIPTION = "Manages user accounts and authentication"

class UserCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="user",
            log_file="logs/user_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting user CLI initialization")

        try:
            # Get the User and Role models from registry
            self.user_model = self.get_model('User')
            self.role_model = self.get_model('Role')
            
            if not self.user_model:
                self.log_error("User model not found in registry")
                raise Exception("User model not found in registry")
                
            if not self.role_model:
                self.log_error("Role model not found in registry")
                raise Exception("Role model not found in registry")

            self.log_info("User and Role models loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize user CLI: {e}")
            raise

    def list_users(self, show_inactive=False, role_filter=None):
        """List all users"""
        self.log_info(f"Listing users: show_inactive={show_inactive}, role_filter={role_filter}")

        try:
            # Use LEFT JOIN to include users without roles
            query = self.session.query(self.user_model).outerjoin(self.role_model)

            if not show_inactive:
                query = query.filter(self.user_model.is_active == True)
                self.log_debug("Filtering for active users only")

            if role_filter:
                query = query.filter(self.role_model.name == role_filter)
                self.log_debug(f"Filtering for role: {role_filter}")

            users = query.order_by(self.user_model.username).all()

            self.log_info(f"Found {len(users)} users")

            if not users:
                self.log_debug("No users found matching criteria")
                self.output_info("No users found")
                return 0

            headers = ['ID', 'Username', 'Email', 'Role', 'Active', 'Locked', 'Last Login']
            rows = []

            for user in users:
                last_login = user.last_login_date.strftime('%Y-%m-%d %H:%M') if user.last_login_date else 'Never'
                rows.append([
                    str(user.uuid),
                    user.username,
                    user.email,
                    user.role.name if user.role else 'No Role',
                    'Yes' if user.is_active else 'No',
                    'Yes' if user.is_currently_locked else 'No',
                    last_login
                ])

            self.output_table(rows, headers=headers)
            self.log_debug("User list displayed to user")
            return 0

        except Exception as e:
            self.log_error(f"Error listing users: {e}")
            self.output_error(f"Error listing users: {e}")
            return 1

    def add_user(self, username, email, role_name=None, password=None, active=True):
        """Add a new user"""
        role_info = f", role={role_name}" if role_name else ", no role"
        self.log_info(f"Adding user: {username} ({email}){role_info}")

        try:
            # Check if user already exists
            existing_user = self.user_model.find_by_identity(self.session, username)
            if existing_user:
                self.log_warning(f"User already exists: {username}")
                self.output_error(f"User already exists: {username}")
                return 1

            existing_email = self.user_model.find_by_email(self.session, email)
            if existing_email:
                self.log_warning(f"Email already exists: {email}")
                self.output_error(f"Email already exists: {email}")
                return 1

            # Find role if specified
            role_uuid = None
            if role_name:
                role = self.session.query(self.role_model).filter(self.role_model.name == role_name).first()
                if not role:
                    self.log_warning(f"Role not found: {role_name}")
                    self.output_error(f"Role not found: {role_name}")
                    return 1
                role_uuid = role.uuid

            # Get password if not provided
            if not password:
                password = getpass.getpass("Enter password for new user: ")
                confirm_password = getpass.getpass("Confirm password: ")
                if password != confirm_password:
                    self.log_warning("Password confirmation failed")
                    self.output_error("Passwords do not match")
                    return 1

            # Create new user
            new_user = self.user_model(
                username=username,
                email=email,
                role_uuid=role_uuid,
                is_active=active
            )
            new_user.set_password(password)

            self.session.add(new_user)
            self.session.commit()

            role_msg = f" with role {role_name}" if role_name else " with no role"
            self.log_info(f"User added successfully: {username}{role_msg} (UUID: {new_user.uuid})")
            self.output_success(f"User created: {username}{role_msg}")
            self.output_info(f"UUID: {new_user.uuid}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error adding user {username}: {e}")
            self.output_error(f"Error adding user: {e}")
            return 1

    def delete_user(self, user_identity, hard_delete=False):
        """Delete a user (soft or hard delete)"""
        delete_type = "hard" if hard_delete else "soft"
        self.log_info(f"Deleting user {user_identity} ({delete_type} delete)")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            if hard_delete:
                self.log_warning(f"Performing HARD delete on user {user.username}")
                self.session.delete(user)
            else:
                self.log_debug(f"Performing soft delete on user {user.username}")
                user.is_active = False

            self.session.commit()

            action = "deleted permanently" if hard_delete else "deactivated"
            self.log_info(f"User {action} successfully: {user.username}")
            self.output_success(f"User {action}: {user.username}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error deleting user {user_identity}: {e}")
            self.output_error(f"Error deleting user: {e}")
            return 1

    def lock_user(self, user_identity, duration_hours=24):
        """Lock a user account"""
        self.log_info(f"Locking user {user_identity} for {duration_hours} hours")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
            user.failed_login_attempts = 0

            self.session.commit()

            self.log_info(f"User locked successfully: {user.username} until {user.locked_until}")
            self.output_success(f"User locked: {user.username} until {user.locked_until.strftime('%Y-%m-%d %H:%M')}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error locking user {user_identity}: {e}")
            self.output_error(f"Error locking user: {e}")
            return 1

    def unlock_user(self, user_identity):
        """Unlock a user account"""
        self.log_info(f"Unlocking user {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0

            self.session.commit()

            self.log_info(f"User unlocked successfully: {user.username}")
            self.output_success(f"User unlocked: {user.username}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error unlocking user {user_identity}: {e}")
            self.output_error(f"Error unlocking user: {e}")
            return 1

    def activate_user(self, user_identity):
        """Activate a user account"""
        self.log_info(f"Activating user {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            user.is_active = True
            self.session.commit()

            self.log_info(f"User activated successfully: {user.username}")
            self.output_success(f"User activated: {user.username}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error activating user {user_identity}: {e}")
            self.output_error(f"Error activating user: {e}")
            return 1

    def change_password(self, user_identity, new_password=None):
        """Change user password"""
        self.log_info(f"Changing password for user {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            if not new_password:
                new_password = getpass.getpass("Enter new password: ")
                confirm_password = getpass.getpass("Confirm new password: ")
                if new_password != confirm_password:
                    self.log_warning("Password confirmation failed")
                    self.output_error("Passwords do not match")
                    return 1

            user.set_password(new_password)
            # Reset lockout status when password is changed
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0

            self.session.commit()

            self.log_info(f"Password changed successfully for user: {user.username}")
            self.output_success(f"Password changed for user: {user.username}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error changing password for user {user_identity}: {e}")
            self.output_error(f"Error changing password: {e}")
            return 1

    def change_role(self, user_identity, new_role_name):
        """Change user role"""
        self.log_info(f"Changing role for user {user_identity} to {new_role_name}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            new_role = self.session.query(self.role_model).filter(self.role_model.name == new_role_name).first()
            if not new_role:
                self.log_warning(f"Role not found: {new_role_name}")
                self.output_error(f"Role not found: {new_role_name}")
                return 1

            old_role_name = user.role.name if user.role else 'None'
            user.role_uuid = new_role.uuid

            self.session.commit()

            self.log_info(f"Role changed successfully for user {user.username}: {old_role_name} -> {new_role_name}")
            self.output_success(f"Role changed for {user.username}: {old_role_name} -> {new_role_name}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error changing role for user {user_identity}: {e}")
            self.output_error(f"Error changing role: {e}")
            return 1

    def show_user_details(self, user_identity):
        """Show detailed user information"""
        self.log_info(f"Showing details for user {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.log_warning(f"User not found: {user_identity}")
                self.output_error(f"User not found: {user_identity}")
                return 1

            headers = ['Field', 'Value']
            rows = [
                ['UUID', str(user.uuid)],
                ['Username', user.username],
                ['Email', user.email],
                ['Role', user.role.name if user.role else 'No Role'],
                ['Active', 'Yes' if user.is_active else 'No'],
                ['Locked', 'Yes' if user.is_currently_locked else 'No'],
                ['Failed Attempts', str(user.failed_login_attempts)],
                ['Locked Until', user.locked_until.strftime('%Y-%m-%d %H:%M:%S') if user.locked_until else 'N/A'],
                ['Last Login', user.last_login_date.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_date else 'Never'],
                ['Created', user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'],
                ['Updated', user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'N/A']
            ]

            self.output_table(rows, headers=headers)
            self.log_debug("User details displayed")
            return 0

        except Exception as e:
            self.log_error(f"Error showing user details for {user_identity}: {e}")
            self.output_error(f"Error showing user details: {e}")
            return 1

    def list_roles(self):
        """List available roles"""
        self.log_info("Listing available roles")

        try:
            roles = self.session.query(self.role_model).filter(self.role_model.is_active == True).order_by(self.role_model.name).all()

            if not roles:
                self.output_info("No roles found")
                return 0

            headers = ['Name', 'Description', 'Created']
            rows = []

            for role in roles:
                rows.append([
                    role.name,
                    role.description or '',
                    role.created_at.strftime('%Y-%m-%d') if role.created_at else 'N/A'
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing roles: {e}")
            self.output_error(f"Error listing roles: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing user CLI")
        super().close()


def main():
    """Entry point for user CLI"""
    parser = argparse.ArgumentParser(description='User CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List users')
    list_parser.add_argument('--all', action='store_true', help='Show inactive users too')
    list_parser.add_argument('--role', help='Filter by role name')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add new user')
    add_parser.add_argument('username', help='Username')
    add_parser.add_argument('email', help='Email address')
    add_parser.add_argument('--role', help='Role name (optional)')
    add_parser.add_argument('--password', help='Password (will prompt if not provided)')
    add_parser.add_argument('--inactive', action='store_true', help='Create user as inactive')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete user')
    delete_parser.add_argument('user', help='Username or email')
    delete_parser.add_argument('--hard', action='store_true', help='Permanently delete (default: deactivate)')

    # Lock command
    lock_parser = subparsers.add_parser('lock', help='Lock user account')
    lock_parser.add_argument('user', help='Username or email')
    lock_parser.add_argument('--hours', type=int, default=24, help='Lock duration in hours (default: 24)')

    # Unlock command
    unlock_parser = subparsers.add_parser('unlock', help='Unlock user account')
    unlock_parser.add_argument('user', help='Username or email')

    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Activate user account')
    activate_parser.add_argument('user', help='Username or email')

    # Change password command
    passwd_parser = subparsers.add_parser('passwd', help='Change user password')
    passwd_parser.add_argument('user', help='Username or email')
    passwd_parser.add_argument('--password', help='New password (will prompt if not provided)')

    # Change role command
    role_parser = subparsers.add_parser('setrole', help='Change user role')
    role_parser.add_argument('user', help='Username or email')
    role_parser.add_argument('role', help='New role name')

    # Show user details command
    show_parser = subparsers.add_parser('show', help='Show user details')
    show_parser.add_argument('user', help='Username or email')

    # List roles command
    roles_parser = subparsers.add_parser('roles', help='List available roles')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = UserCLI(
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
            return cli.list_users(args.all, args.role)

        elif args.command == 'add':
            return cli.add_user(args.username, args.email, args.role, args.password, not args.inactive)

        elif args.command == 'delete':
            return cli.delete_user(args.user, args.hard)

        elif args.command == 'lock':
            return cli.lock_user(args.user, args.hours)

        elif args.command == 'unlock':
            return cli.unlock_user(args.user)

        elif args.command == 'activate':
            return cli.activate_user(args.user)

        elif args.command == 'passwd':
            return cli.change_password(args.user, args.password)

        elif args.command == 'setrole':
            return cli.change_role(args.user, args.role)

        elif args.command == 'show':
            return cli.show_user_details(args.user)

        elif args.command == 'roles':
            return cli.list_roles()

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