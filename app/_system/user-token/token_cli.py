#!/usr/bin/env python3
import argparse
import sys
from tabulate import tabulate

from app.base.cli import BaseCLI


CLI_DESCRIPTION = "Manages user tokens for API authentication"


class TokenCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
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

    def list_tokens(self, user_identity=None, token_type=None, show_inactive=False):
        self.log_info(f"Listing tokens for user: {user_identity}" if user_identity else "Listing all tokens")

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

            if token_type:
                query = query.filter(self.user_token_model.token_type == token_type)

            tokens = query.order_by(self.user_token_model.created_at.desc()).all()

            if not tokens:
                self.output_info("No tokens found")
                return 0

            headers = ['UUID', 'User', 'Name', 'Application', 'Type', 'Temporary', 'Expires', 'Active', 'Last Used']
            rows = []

            for token in tokens:
                user_name = token.user.username if token.user else 'N/A'
                expires = token.expires_at.strftime('%Y-%m-%d %H:%M') if token.expires_at else 'Never'
                last_used = token.last_used_at.strftime('%Y-%m-%d %H:%M') if token.last_used_at else 'Never'

                rows.append([
                    str(token.uuid),
                    user_name,
                    token.name or '',
                    token.application or '',
                    token.token_type,
                    'Yes' if token.is_system_temporary else 'No',
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

    def create_access_token(self, user_identity, name=None, application=None, refresh_token_uuid=None, is_system_temporary=False):
        self.log_info(f"Creating access token for user: {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.output_error(f"User not found: {user_identity}")
                return 1

            token = self.user_token_model.create_access_token(
                self.session, user.uuid, name, application, refresh_token_uuid, is_system_temporary
            )

            self.log_info(f"Access token created successfully: {token.uuid}")
            self.output_success(f"Access token created for user: {user.username}")
            self.output_info(f"Token UUID: {token.uuid}")
            self.output_info(f"Token Value: {token.token}")
            self.output_info(f"Expires at: {token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.output_warning("Store this token securely - it will not be shown again!")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating access token: {e}")
            self.output_error(f"Error creating access token: {e}")
            return 1

    def create_refresh_token(self, user_identity, name=None, application=None, is_system_temporary=False):
        self.log_info(f"Creating refresh token for user: {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.output_error(f"User not found: {user_identity}")
                return 1

            token = self.user_token_model.create_refresh_token(
                self.session, user.uuid, name, application, is_system_temporary
            )

            self.log_info(f"Refresh token created successfully: {token.uuid}")
            self.output_success(f"Refresh token created for user: {user.username}")
            self.output_info(f"Token UUID: {token.uuid}")
            self.output_info(f"Token Value: {token.token}")
            self.output_info(f"Expires at: {token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.output_warning("Store this token securely - it will not be shown again!")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating refresh token: {e}")
            self.output_error(f"Error creating refresh token: {e}")
            return 1

    def create_token_pair(self, user_identity, name=None, application=None, is_system_temporary=False):
        self.log_info(f"Creating token pair for user: {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.output_error(f"User not found: {user_identity}")
                return 1

            tokens = self.user_token_model.create_token_pair(
                self.session, user.uuid, name, application, is_system_temporary
            )

            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']

            self.log_info(f"Token pair created successfully")
            self.output_success(f"Token pair created for user: {user.username}")
            self.output_info("\nAccess Token:")
            self.output_info(f"  UUID: {access_token.uuid}")
            self.output_info(f"  Value: {access_token.token}")
            self.output_info(f"  Expires at: {access_token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.output_info("\nRefresh Token:")
            self.output_info(f"  UUID: {refresh_token.uuid}")
            self.output_info(f"  Value: {refresh_token.token}")
            self.output_info(f"  Expires at: {refresh_token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.output_warning("\nStore these tokens securely - they will not be shown again!")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating token pair: {e}")
            self.output_error(f"Error creating token pair: {e}")
            return 1

    def create_service_token(self, user_identity, name=None, application=None, expires_in_days=None, is_system_temporary=False):
        self.log_info(f"Creating service token for user: {user_identity}")

        try:
            user = self.user_model.find_by_identity(self.session, user_identity)
            if not user:
                self.output_error(f"User not found: {user_identity}")
                return 1

            # Create a service token (long-lived token for service/API use)
            token_value = self.user_token_model.generate_token()
            expires_at = None
            if expires_in_days is not None:
                from datetime import datetime, timezone, timedelta
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

            token = self.user_token_model(
                user_uuid=user.uuid,
                token=token_value,
                name=name,
                application=application,
                token_type='service',
                expires_at=expires_at,
                is_system_temporary=is_system_temporary
            )

            self.session.add(token)
            self.session.commit()

            self.log_info(f"Service token created successfully: {token.uuid}")
            self.output_success(f"Service token created for user: {user.username}")
            self.output_info(f"Token UUID: {token.uuid}")
            self.output_info(f"Token Value: {token.token}")
            if token.expires_at:
                self.output_info(f"Expires at: {token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            else:
                self.output_info("Expires: Never")
            self.output_warning("Store this token securely - it will not be shown again!")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating service token: {e}")
            self.output_error(f"Error creating service token: {e}")
            return 1

    def refresh_access_token(self, refresh_token_value):
        self.log_info("Refreshing access token")

        try:
            refresh_token = self.user_token_model.find_by_token(self.session, refresh_token_value)
            if not refresh_token:
                self.output_error("Refresh token not found")
                return 1

            if refresh_token.token_type != 'refresh':
                self.output_error("Token is not a refresh token")
                return 1

            if refresh_token.is_expired():
                self.output_error("Refresh token is expired")
                return 1

            new_access_token = refresh_token.refresh_access_token(self.session)

            self.log_info(f"Access token refreshed successfully: {new_access_token.uuid}")
            self.output_success("Access token refreshed successfully")
            self.output_info(f"Token UUID: {new_access_token.uuid}")
            self.output_info(f"Token Value: {new_access_token.token}")
            self.output_info(f"Expires at: {new_access_token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            self.output_warning("Store this token securely - it will not be shown again!")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error refreshing access token: {e}")
            self.output_error(f"Error refreshing access token: {e}")
            return 1

    def revoke_token(self, token_uuid):
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
            if token.token_type == 'refresh':
                self.output_info("All associated access tokens have been revoked")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error revoking token: {e}")
            self.output_error(f"Error revoking token: {e}")
            return 1

    def show_token_details(self, token_uuid):
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
                ['Refresh Token UUID', str(token.refresh_token_uuid) if token.refresh_token_uuid else 'None'],
                ['Temporary', 'Yes' if token.is_system_temporary else 'No'],
                ['Expires At', token.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if token.expires_at else 'Never'],
                ['Expires In', f"{token.expires_in_seconds()} seconds" if token.expires_in_seconds() else 'Never'],
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

    def cleanup_expired(self, days_old=7, dry_run=False):
        """Clean up expired tokens older than specified days"""
        self.log_info(f"Cleaning up expired tokens older than {days_old} days (dry_run={dry_run})")

        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find expired tokens to clean up
            expired_query = self.session.query(self.user_token_model).filter(
                self.user_token_model.expires_at < cutoff_date,
                self.user_token_model.ignore_expiration == False
            )
            
            # Find soft-deleted tokens to clean up
            deleted_query = self.session.query(self.user_token_model).filter(
                self.user_token_model.is_active == False,
                self.user_token_model.updated_at < cutoff_date
            )
            
            expired_count = expired_query.count()
            deleted_count = deleted_query.count()
            total_count = expired_count + deleted_count
            
            if dry_run:
                self.output_info(f"Would delete {expired_count} expired tokens")
                self.output_info(f"Would delete {deleted_count} soft-deleted tokens")
                self.output_info(f"Total: {total_count} tokens")
                
                if self.verbose and total_count > 0:
                    # Show sample of tokens that would be deleted
                    sample_tokens = expired_query.limit(10).all()
                    if sample_tokens:
                        headers = ['UUID', 'User', 'Type', 'Application', 'Expired At']
                        rows = []
                        
                        for token in sample_tokens:
                            user_name = token.user.username if token.user else 'N/A'
                            rows.append([
                                str(token.uuid)[:8] + '...',
                                user_name,
                                token.token_type,
                                token.application or 'N/A',
                                token.expires_at.strftime('%Y-%m-%d %H:%M')
                            ])
                        
                        self.output_info("\nSample of tokens to be deleted:")
                        self.output_table(rows, headers=headers)
                        if expired_count > 10:
                            self.output_info(f"... and {expired_count - 10} more expired tokens")
                
                return 0
            
            # Perform actual cleanup
            self.log_info(f"Deleting {total_count} tokens")
            
            # Delete expired tokens
            expired_query.delete(synchronize_session=False)
            
            # Delete soft-deleted tokens
            deleted_query.delete(synchronize_session=False)
            
            self.session.commit()
            
            self.log_info(f"Successfully cleaned up {total_count} tokens")
            self.output_success(f"Cleaned up {total_count} tokens ({expired_count} expired, {deleted_count} soft-deleted)")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error during cleanup: {e}")
            self.output_error(f"Error during cleanup: {e}")
            return 1
        

    def validate_token(self, token_value, token_type=None):
        self.log_info("Validating token")

        try:
            if token_type == 'access':
                token = self.user_token_model.validate_access_token(self.session, token_value)
            elif token_type == 'refresh':
                token = self.user_token_model.validate_refresh_token(self.session, token_value)
            else:
                token = self.user_token_model.validate_token(self.session, token_value)

            if token:
                self.output_success(f"Token is valid ({token.token_type} token)")
                self.output_info(f"Token belongs to: {token.user.username if token.user else 'Service Account'}")
                if token.expires_at:
                    self.output_info(f"Expires in: {token.expires_in_seconds()} seconds")
                return 0
            else:
                self.output_error("Token is invalid or expired")
                return 1

        except Exception as e:
            self.log_error(f"Error validating token: {e}")
            self.output_error(f"Error validating token: {e}")
            return 1

    def close(self):
        self.log_debug("Closing token CLI")
        super().close()


def main():
    parser = argparse.ArgumentParser(description='User Token CLI Management Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List tokens')
    list_parser.add_argument('--user', help='Filter by user (username or email)')
    list_parser.add_argument('--type', choices=['access', 'refresh', 'service'], help='Filter by token type')
    list_parser.add_argument('--all', action='store_true', help='Show inactive tokens too')

    # Create access token
    create_access_parser = subparsers.add_parser('create-access', help='Create access token')
    create_access_parser.add_argument('user', help='Username or email')
    create_access_parser.add_argument('--name', help='Token name/description')
    create_access_parser.add_argument('--app', help='Application name')
    create_access_parser.add_argument('--refresh-token', help='Link to refresh token UUID')
    create_access_parser.add_argument('--temporary', action='store_true', help='Mark token as system temporary')

    # Create refresh token
    create_refresh_parser = subparsers.add_parser('create-refresh', help='Create refresh token')
    create_refresh_parser.add_argument('user', help='Username or email')
    create_refresh_parser.add_argument('--name', help='Token name/description')
    create_refresh_parser.add_argument('--app', help='Application name')
    create_refresh_parser.add_argument('--temporary', action='store_true', help='Mark token as system temporary')

    # Create token pair
    create_pair_parser = subparsers.add_parser('create-pair', help='Create access and refresh token pair')
    create_pair_parser.add_argument('user', help='Username or email')
    create_pair_parser.add_argument('--name', help='Token name/description')
    create_pair_parser.add_argument('--app', help='Application name')
    create_pair_parser.add_argument('--temporary', action='store_true', help='Mark tokens as system temporary')

    # Create service token
    create_service_parser = subparsers.add_parser('create-service', help='Create service token')
    create_service_parser.add_argument('user', help='Username or email')
    create_service_parser.add_argument('--name', help='Token name/description')
    create_service_parser.add_argument('--app', help='Application name')
    create_service_parser.add_argument('--expires', type=int, help='Expires in days (default: never)')
    create_service_parser.add_argument('--temporary', action='store_true', help='Mark token as system temporary')

    # Refresh access token
    refresh_parser = subparsers.add_parser('refresh', help='Refresh access token using refresh token')
    refresh_parser.add_argument('token', help='Refresh token value')

    # Revoke token
    revoke_parser = subparsers.add_parser('revoke', help='Revoke token')
    revoke_parser.add_argument('token_uuid', help='Token UUID')

    # Show token details
    show_parser = subparsers.add_parser('show', help='Show token details')
    show_parser.add_argument('token_uuid', help='Token UUID')

    # Validate token
    validate_parser = subparsers.add_parser('validate', help='Validate token')
    validate_parser.add_argument('token', help='Token value to validate')
    validate_parser.add_argument('--type', choices=['access', 'refresh'], help='Expected token type')

    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up expired tokens')
    cleanup_parser.add_argument('--days', type=int, default=7, help='Delete tokens expired more than N days ago (default: 7)')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')


    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = None
    try:
        cli = TokenCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )

        if args.command == 'list':
            return cli.list_tokens(user_identity=args.user, token_type=args.type, show_inactive=args.all)

        elif args.command == 'create-access':
            return cli.create_access_token(
                args.user, args.name, args.app, args.refresh_token, is_system_temporary=args.temporary
            )

        elif args.command == 'create-refresh':
            return cli.create_refresh_token(
                args.user, args.name, args.app, is_system_temporary=args.temporary
            )

        elif args.command == 'create-pair':
            return cli.create_token_pair(
                args.user, args.name, args.app, is_system_temporary=args.temporary
            )

        elif args.command == 'create-service':
            return cli.create_service_token(
                args.user, args.name, args.app, args.expires, is_system_temporary=args.temporary
            )

        elif args.command == 'refresh':
            return cli.refresh_access_token(args.token)

        elif args.command == 'revoke':
            return cli.revoke_token(args.token_uuid)

        elif args.command == 'show':
            return cli.show_token_details(args.token_uuid)

        elif args.command == 'validate':
            return cli.validate_token(args.token, args.type)

        elif args.command == 'cleanup':
            return cli.cleanup_expired(days_old=args.days, dry_run=args.dry_run)
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