#!/usr/bin/env python3
"""
User Token CLI Management Tool
Manage user tokens for API authentication
"""

import argparse
import sys
from tabulate import tabulate

from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Manages user tokens for API authentication"

class TokenCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        super().__init__(
            name="token",
            log_file="logs/token_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting token CLI initialization")

        try:
            # Get models from registry
            self.user_token_model = self.get_model('UserToken')
            self.user_model = self.get_model('User')

            if not self.user_token_model:
                self.log_error("UserToken model not found in registry")
                raise Exception("UserToken model not found in registry")

            if not self.user_model:
                self.log_error("User model not found in registry")
                raise Exception("User model not found in registry")

            self.log_info("Token models loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize token CLI: {e}")
            raise

    def list_tokens(self, user_identity=None, show_inactive=False):
        """List tokens"""
        if user_identity:
            self.log_info(f"Listing tokens for user: {user_identity}")
        else:
            self.log_info("Listing all tokens")

        try:
            query = self.session.query(self.user_token_model)

            if not show_inactive:
                query = query.filter(self.user_token_model.is_active == True)

            if user_identity:
                user = self.user_model.find_by_identity(self.session, user_identity)
                if not user:
                    self.output_error(f"User not found: {user_identity}")
                    return 1
                query = query.filter(self.user_token_model.user_uuid == user.uuid)

            tokens = query.order_by(self.user_token_model.created_at.desc()).all()

            if not tokens:
                self.output_info("No tokens found")
                return 0

            headers = ['UUID', 'User', 'Name', 'Application', 'Type', 'Expires', 'Active', 'Last Used']
            rows = []

            for token in tokens:
                user_name = token.user.username if token.user else 'N/A'
                expires = token.expires_at.strftime('%Y-%m-%d') if token.expires_at else 'Never'
                last_used = token.last_used_at.strftime('%Y-%m-%d %H:%M') if token.last_used_at else 'Never'
                
                rows.append([
                    str(token.uuid),
                    user_name,
                    token.name or '',
                    token.application or '',
                    token.token_type,
                    expires,
                    'Yes' if token.is_active else 'No',
                    last_used
                ])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing tokens: {e}")
            self.output_error(f"Error listing tokens: {e}")
            return 1

    def create_user_token(self, user_identity, name=None, application=None, expires_in_days=None):
        """Create a new user token"""
        self.log_info(f"Creating token for user: {user_identity}")

        try:
            # Find user
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.output_error(f"User not found: {user_identity}")
                return 1

            token = self.user_token_model.create_user_token(
                self.session, user.uuid, name, application, expires_in_days
            )

            self.log_info(f"Token created successfully: {token.uuid}")
            self.output_success(f"Token created for user: {user.username}")
            self.output_info(f"Token UUID: {token.uuid}")
            self.output_info(f"Token Value: {token.token}")
            self.output_warning("Store this token securely - it will not be shown again!")
            
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating token: {e}")
            self.output_error(f"Error creating token: {e}")
            return 1

    def create_service_token(self, name=None, application=None, expires_in_days=None):
        """Create a new service token"""
        self.log_info(f"Creating service token: {name}")

        try:
            token = self.user_token_model.create_service_token(
                self.session, name, application, expires_in_days
            )

            self.log_info(f"Service token created successfully: {token.uuid}")
            self.output_success(f"Service token created: {name or 'Unnamed'}")
            self.output_info(f"Token UUID: {token.uuid}")
            self.output_info(f"Token Value: {token.token}")
            self.output_warning("Store this token securely - it will not be shown again!")
            
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating service token: {e}")
            self.output_error(f"Error creating service token: {e}")
            return 1

    def revoke_token(self, token_uuid):
        """Revoke a token"""
        self.log_info(f"Revoking token: {token_uuid}")

        try:
            token = self.session.query(self.user_token_model).filter(
                self.user_token_model.uuid == token_uuid
            ).first()
            
            if not token:
                self.output_error(f"Token not found: {token_uuid}")
                return 1

            token.revoke()
            self.session.commit()

            self.log_info(f"Token revoked successfully: {token_uuid}")
            self.output_success(f"Token revoked: {token.name or token_uuid}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error revoking token: {e}")
            self.output_error(f"Error revoking token: {e}")
            return 1

    def show_token_details(self, token_uuid):
        """Show detailed token information"""
        self.log_info(f"Showing details for token: {token_uuid}")

        try:
            token = self.session.query(self.user_token_model).filter(
                self.user_token_model.uuid == token_uuid
            ).first()
            
            if not token:
                self.output_error(f"Token not found: {token_uuid}")
                return 1

            headers = ['Field', 'Value']
            rows = [
                ['UUID', str(token.uuid)],
                ['User', token.user.username if token.user else 'Service Token'],
                ['Name', token.name or 'None'],
                ['Application', token.application or 'None'],
                ['Token Type', token.token_type],
                ['Expires At', token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if token.expires_at else 'Never'],
                ['Ignore Expiration', 'Yes' if token.ignore_expiration else 'No'],
                ['Is Expired', 'Yes' if token.is_expired() else 'No'],
                ['Active', 'Yes' if token.is_active else 'No'],
                ['Last Used', token.last_used_at.strftime('%Y-%m-%d %H:%M:%S UTC') if token.last_used_at else 'Never'],
                ['Created', token.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if token.created_at else 'N/A'],
                ['Updated', token.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC') if token.updated_at else 'N/A']
            ]

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error showing token details: {e}")
            self.output_error(f"Error showing token details: {e}")
            return 1

    def validate_token(self, token_value):
        """Validate a token"""
        self.log_info("Validating token")

        try:
            token = self.user_token_model.validate_token(self.session, token_value)
            
            if token:
                self.output_success("Token is valid")
                self.output_info(f"Token belongs to: {token.username if hasattr(token, 'username') else 'Service Account'}")
                return 0
            else:
                self.output_error("Token is invalid or expired")
                return 1

        except Exception as e:
            self.log_error(f"Error validating token: {e}")
            self.output_error(f"Error validating token: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing token CLI")
        super().close()


def main():
    """Entry point for token CLI"""
    parser = argparse.ArgumentParser(description='User Token CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List tokens command
    list_parser = subparsers.add_parser('list', help='List tokens')
    list_parser.add_argument('--user', help='Filter by user (username or email)')
    list_parser.add_argument('--all', action='store_true', help='Show inactive tokens too')

    # Create user token command
    create_user_parser = subparsers.add_parser('create-user', help='Create user token')
    create_user_parser.add_argument('user', help='Username or email')
    create_user_parser.add_argument('--name', help='Token name/description')
    create_user_parser.add_argument('--app', help='Application name')
    create_user_parser.add_argument('--expires', type=int, help='Expires in days (default: never)')

    # Create service token command
    create_service_parser = subparsers.add_parser('create-service', help='Create service token')
    create_service_parser.add_argument('--name', help='Token name/description')
    create_service_parser.add_argument('--app', help='Application name')
    create_service_parser.add_argument('--expires', type=int, help='Expires in days (default: never)')

    # Revoke token command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke token')
    revoke_parser.add_argument('token_uuid', help='Token UUID')

    # Show token details command
    show_parser = subparsers.add_parser('show', help='Show token details')
    show_parser.add_argument('token_uuid', help='Token UUID')

    # Validate token command
    validate_parser = subparsers.add_parser('validate', help='Validate token')
    validate_parser.add_argument('token', help='Token value to validate')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = TokenCLI(
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
            return cli.list_tokens(user_identity=args.user, show_inactive=args.all)

        elif args.command == 'create-user':
            return cli.create_user_token(args.user, args.name, args.app, args.expires)

        elif args.command == 'create-service':
            return cli.create_service_token(args.name, args.app, args.expires)

        elif args.command == 'revoke':
            return cli.revoke_token(args.token_uuid)

        elif args.command == 'show':
            return cli.show_token_details(args.token_uuid)

        elif args.command == 'validate':
            return cli.validate_token(args.token)

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
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())