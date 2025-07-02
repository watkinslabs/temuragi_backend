#!/usr/bin/env python3
"""
Connection CLI - Manage database connections
Provides comprehensive database connection management capabilities
"""

import sys
import json
import argparse
import getpass
from tabulate import tabulate
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from sqlalchemy import text

from app.base.cli_v1 import BaseCLI

CLI_DESCRIPTION = "Manage database connections"


class ConnectionCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection"""
        super().__init__(
            name="connection",
            log_file="logs/connection_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting connection CLI initialization")

        # Get models
        self.connection_model = self.get_model('Connection')
        self.database_type_model = self.get_model('DatabaseType')

        if not self.connection_model or not self.database_type_model:
            self.log_critical("Failed to load required models")
            raise RuntimeError("Required models not found")

        # Setup connection manager
        try:
            from app._system.connection.connection_manager import setup_connection_manager
            self.db_manager = setup_connection_manager(self.session)
            self.log_info("Connection manager initialized successfully")
        except Exception as e:
            self.log_error(f"Failed to initialize connection manager: {e}")
            raise

    def icon(self, icon_type):
        """Get icon for display"""
        if not self.show_icons:
            return ''
        
        icons = {
            'check': '✓',
            'cross': '✗',
            'warning': '⚠',
            'database': '🗄',
            'key': '🔑',
            'link': '🔗',
            'main': '⭐'
        }
        return icons.get(icon_type, '')

    # =====================================================================
    # LIST OPERATIONS
    # =====================================================================

    def list_connections(self, show_credentials=False, db_type=None):
        """List all database connections"""
        self.log_info(f"Listing connections - show_credentials: {show_credentials}, db_type: {db_type}")

        try:
            query = self.session.query(self.connection_model)
            
            if db_type:
                db_type_obj = self.session.query(self.database_type_model).filter_by(name=db_type).first()
                if not db_type_obj:
                    self.output_error(f"Database type '{db_type}' not found")
                    return 1
                query = query.filter_by(database_type_id=db_type_obj.id)

            connections = query.order_by(self.connection_model.name).all()

            if not connections:
                self.output_warning("No connections found")
                return 0

            # Get main connection ID
            try:
                main_conn_id = self.db_manager.get_main_connection_id()
            except:
                main_conn_id = None

            headers = ['Name', 'Type', 'Active', 'Host/Path', 'Database', 'User']
            if show_credentials:
                headers.append('Password')
            headers.append('Options')

            rows = []
            for conn in connections:
                # Parse connection info
                conn_info = self._parse_connection_info(conn)
                
                # Check if this is the main connection
                is_main = str(conn.id) == str(main_conn_id) if main_conn_id else False
                
                row = [
                    f"{self.icon('main') if is_main else ''} {conn.name}",
                    conn.database_type.display,
                    f"{self.icon('check') if conn.is_active else self.icon('cross')}",
                    conn_info['host'],
                    conn_info['database'],
                    conn.username or 'N/A'
                ]
                
                if show_credentials:
                    if conn.password:
                        row.append('***hidden***')
                    else:
                        row.append('N/A')
                
                # Options count
                option_count = len(conn.options) if conn.options else 0
                row.append(f"{option_count} options" if option_count else 'None')
                
                rows.append(row)

            self.output_info(f"Database Connections ({len(connections)} total):")
            self.output_table(rows, headers=headers)

            # Summary by type
            type_counts = {}
            for conn in connections:
                type_name = conn.database_type.display
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            if len(type_counts) > 1:
                self.output_info("\nConnections by Type:")
                for db_type, count in sorted(type_counts.items()):
                    self.output_info(f"  {db_type}: {count}")

            return 0

        except Exception as e:
            self.log_error(f"Error listing connections: {e}")
            self.output_error(f"Error listing connections: {e}")
            return 1

    def list_database_types(self):
        """List available database types"""
        self.log_info("Listing database types")

        try:
            db_types = self.session.query(self.database_type_model).order_by(self.database_type_model.name).all()

            if not db_types:
                self.output_warning("No database types found")
                return 0

            headers = ['Name', 'Display Name', 'Driver', 'Port', 'Active', 'Connections']
            rows = []

            for db_type in db_types:
                # Count connections using this type
                conn_count = self.session.query(self.connection_model).filter_by(
                    database_type_id=db_type.id
                ).count()

                rows.append([
                    db_type.name,
                    db_type.display,
                    db_type.driver or 'N/A',
                    db_type.default_port or 'N/A',
                    f"{self.icon('check') if db_type.is_active else self.icon('cross')}",
                    conn_count
                ])

            self.output_info(f"Database Types ({len(db_types)} total):")
            self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Error listing database types: {e}")
            self.output_error(f"Error listing database types: {e}")
            return 1

    # =====================================================================
    # SHOW OPERATIONS
    # =====================================================================

    def show_connection(self, name, show_password=False):
        """Show detailed connection information"""
        self.log_info(f"Showing connection: {name}")

        try:
            conn = self.session.query(self.connection_model).filter_by(name=name).first()
            if not conn:
                self.output_error(f"Connection '{name}' not found")
                return 1

            # Check if main connection
            try:
                main_conn_id = self.db_manager.get_main_connection_id()
                is_main = str(conn.id) == str(main_conn_id)
            except:
                is_main = False

            self.output_info(f"Connection: {conn.name} {self.icon('main') if is_main else ''}")
            self.output_info("=" * 60)

            # Basic info
            basic_info = [
                ['UUID', str(conn.id)],
                ['Database Type', conn.database_type.display],
                ['Driver', conn.database_type.driver or 'N/A'],
                ['Active', f"{self.icon('check') if conn.is_active else self.icon('cross')} {'Yes' if conn.is_active else 'No'}"],
                ['Created', conn.created_at.strftime('%Y-%m-%d %H:%M:%S')],
                ['Updated', conn.updated_at.strftime('%Y-%m-%d %H:%M:%S')]
            ]

            if is_main:
                basic_info.append(['Status', f"{self.icon('main')} Main Connection"])

            self.output_table(basic_info, headers=['Property', 'Value'])

            # Connection details
            self.output_info("\nConnection Details:")
            conn_info = self._parse_connection_info(conn)
            
            conn_details = [
                ['Connection String', conn.connection_string],
                ['Host/Path', conn_info['host']],
                ['Database', conn_info['database']],
                ['Port', conn_info['port'] or 'Default']
            ]
            self.output_table(conn_details, headers=['Property', 'Value'])

            # Credentials
            self.output_info("\nCredentials:")
            cred_info = []
            if conn.username:
                cred_info.append(['Username', conn.username])
                cred_info.append(['Password', conn.password if show_password and conn.password else '***hidden***' if conn.password else 'Not set'])
            else:
                cred_info.append(['Status', 'No credentials stored'])
            self.output_table(cred_info, headers=['Property', 'Value'])

            # Options
            if conn.options:
                self.output_info("\nConnection Options:")
                opt_rows = [[k, v] for k, v in conn.options.items()]
                self.output_table(opt_rows, headers=['Option', 'Value'])

            # Engine options
            if conn.options and conn.options.get('engine_options'):
                self.output_info("\nEngine Options:")
                eng_opts = conn.options['engine_options']
                eng_rows = [[k, v] for k, v in eng_opts.items()]
                self.output_table(eng_rows, headers=['Option', 'Value'])

            # Show full connection string if verbose
            if self.verbose:
                self.output_info("\nFull Connection String:")
                try:
                    full_conn_str = conn.get_connection_string()
                    # Mask password in connection string
                    if not show_password and '://' in full_conn_str:
                        parsed = urlparse(full_conn_str)
                        if parsed.password:
                            masked = full_conn_str.replace(f":{parsed.password}@", ":***@")
                            self.output(masked)
                        else:
                            self.output(full_conn_str)
                    else:
                        self.output(full_conn_str)
                except Exception as e:
                    self.output_error(f"Failed to build connection string: {e}")

            return 0

        except Exception as e:
            self.log_error(f"Error showing connection: {e}")
            self.output_error(f"Error showing connection: {e}")
            return 1

    # =====================================================================
    # CREATE OPERATIONS
    # =====================================================================

    def create_connection(self, name, db_type, connection_string, username=None, password=None, options=None):
        """Create a new database connection"""
        self.log_info(f"Creating connection: {name}")

        try:
            # Check if connection already exists
            existing = self.session.query(self.connection_model).filter_by(name=name).first()
            if existing:
                self.output_error(f"Connection '{name}' already exists")
                return 1

            # Get database type
            db_type_obj = self.session.query(self.database_type_model).filter_by(name=db_type).first()
            if not db_type_obj:
                self.output_error(f"Database type '{db_type}' not found")
                self.output_info("Use 'connection types' to see available types")
                return 1

            # Handle password prompt if username provided but no password
            if username and not password:
                password = getpass.getpass(f"Password for {username}: ")

            # Parse options if provided
            parsed_options = {}
            if options:
                for opt in options:
                    if '=' in opt:
                        key, value = opt.split('=', 1)
                        parsed_options[key] = value

            # Create connection
            conn = self.connection_model(
                name=name,
                database_type_id=db_type_obj.id,
                connection_string=connection_string,
                username=username,
                password=password,
                options=parsed_options if parsed_options else None
            )

            self.session.add(conn)
            self.session.commit()

            self.output_success(f"Connection created: {name} ({conn.id})")
            
            # Test connection if requested
            if self.verbose:
                self.output_info("Testing connection...")
                if self._test_connection_internal(conn):
                    self.output_success("Connection test successful!")
                else:
                    self.output_warning("Connection test failed - check your settings")

            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error creating connection: {e}")
            self.output_error(f"Error creating connection: {e}")
            return 1

    def create_connection_interactive(self):
        """Create connection with interactive prompts"""
        self.log_info("Starting interactive connection creation")

        try:
            # Get connection name
            name = input("Connection name: ").strip()
            if not name:
                self.output_error("Connection name is required")
                return 1

            # Check if exists
            existing = self.session.query(self.connection_model).filter_by(name=name).first()
            if existing:
                self.output_error(f"Connection '{name}' already exists")
                return 1

            # List database types
            db_types = self.session.query(self.database_type_model).filter_by(is_active=True).order_by(self.database_type_model.name).all()
            
            self.output_info("\nAvailable database types:")
            for i, db_type in enumerate(db_types, 1):
                self.output(f"  {i}. {db_type.display} ({db_type.name})")
            
            # Get database type selection
            while True:
                try:
                    choice = int(input("\nSelect database type (number): "))
                    if 1 <= choice <= len(db_types):
                        selected_type = db_types[choice - 1]
                        break
                    else:
                        self.output_error("Invalid selection")
                except ValueError:
                    self.output_error("Please enter a number")

            self.output_info(f"\nSelected: {selected_type.display}")

            # Get connection string based on type
            self.output_info(f"\nEnter connection string for {selected_type.display}:")
            
            username = None
            password = None
            
            if selected_type.name == 'sqlite':
                self.output_info("Example: /path/to/database.db")
                connection_string = input("Path: ").strip()
            else:
                # Show examples based on database type
                examples = {
                    'postgres': "postgresql://localhost:5432/mydb",
                    'mysql': "mysql://localhost:3306/mydb",
                    'mssql': "Server=localhost;Database=mydb",
                    'oracle': "localhost:1521/ORCL",
                    'mongodb': "mongodb://localhost:27017/mydb"
                }
                
                example = examples.get(selected_type.name, "")
                if example:
                    self.output_info(f"Example: {example}")
                
                connection_string = input("Connection string: ").strip()
                
                # Get credentials
                self.output_info("\nDatabase credentials:")
                username = input("Username: ").strip()
                if username:
                    password = getpass.getpass("Password: ")

            # Get options
            self.output_info("\nAdditional options (optional):")
            self.output_info("Enter options as key=value, one per line. Press Enter with no input to finish.")
            
            options = {}
            while True:
                opt = input("Option (key=value): ").strip()
                if not opt:
                    break
                if '=' in opt:
                    key, value = opt.split('=', 1)
                    options[key.strip()] = value.strip()
                else:
                    self.output_warning("Invalid format. Use key=value")

            # Create connection
            conn = self.connection_model(
                name=name,
                database_type_id=selected_type.id,
                connection_string=connection_string,
                username=username,
                password=password,
                options=options if options else None
            )

            self.session.add(conn)
            self.session.commit()

            self.output_success(f"\nConnection created: {name} ({conn.id})")

            # Offer to test
            test = input("\nTest connection now? (y/N): ").strip().lower()
            if test == 'y':
                if self._test_connection_internal(conn):
                    self.output_success("Connection test successful!")
                else:
                    self.output_warning("Connection test failed - check your settings")

            return 0

        except KeyboardInterrupt:
            self.output_warning("\nOperation cancelled")
            return 1
        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error in interactive creation: {e}")
            self.output_error(f"Error: {e}")
            return 1

    # =====================================================================
    # UPDATE OPERATIONS
    # =====================================================================

    def update_connection(self, name, **kwargs):
        """Update connection properties"""
        self.log_info(f"Updating connection: {name}")

        try:
            conn = self.session.query(self.connection_model).filter_by(name=name).first()
            if not conn:
                self.output_error(f"Connection '{name}' not found")
                return 1

            updated = []

            # Update connection string
            if kwargs.get('connection_string'):
                conn.connection_string = kwargs['connection_string']
                updated.append('connection_string')

            # Update username
            if kwargs.get('username') is not None:
                conn.username = kwargs['username']
                updated.append('username')

            # Update password
            if kwargs.get('password') is not None:
                conn.password = kwargs['password']
                updated.append('password')

            # Update active status
            if kwargs.get('is_active') is not None:
                conn.is_active = kwargs['is_active']
                updated.append('is_active')

            # Update options
            if kwargs.get('set_option'):
                if not conn.options:
                    conn.options = {}
                for opt in kwargs['set_option']:
                    if '=' in opt:
                        key, value = opt.split('=', 1)
                        conn.options[key] = value
                        updated.append(f'option:{key}')

            if kwargs.get('remove_option'):
                if conn.options:
                    for key in kwargs['remove_option']:
                        if key in conn.options:
                            del conn.options[key]
                            updated.append(f'removed option:{key}')

            if not updated:
                self.output_warning("No updates specified")
                return 1

            self.session.commit()
            self.output_success(f"Connection '{name}' updated: {', '.join(updated)}")

            # Invalidate cache for this connection
            self.db_manager.invalidate_cache(conn.id)
            self.output_info("Connection cache invalidated")

            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error updating connection: {e}")
            self.output_error(f"Error updating connection: {e}")
            return 1

    # =====================================================================
    # DELETE OPERATIONS
    # =====================================================================

    def delete_connection(self, name, force=False):
        """Delete a connection"""
        self.log_info(f"Deleting connection: {name}")

        try:
            conn = self.session.query(self.connection_model).filter_by(name=name).first()
            if not conn:
                self.output_error(f"Connection '{name}' not found")
                return 1

            # Check if this is the main connection
            try:
                main_conn_id = self.db_manager.get_main_connection_id()
                if str(conn.id) == str(main_conn_id):
                    self.output_error("Cannot delete the main connection")
                    self.output_info("Set a different main connection first")
                    return 1
            except:
                pass

            # Check for dependencies (reports, etc.)
            # This would need to be implemented based on your models
            
            if not force:
                self.output_warning(f"This will delete connection '{name}'")
                response = input("Are you sure? (y/N): ")
                if response.lower() != 'y':
                    self.output_info("Deletion cancelled")
                    return 0

            # Invalidate cache before deletion
            self.db_manager.invalidate_cache(conn.id)

            self.session.delete(conn)
            self.session.commit()

            self.output_success(f"Connection deleted: {name}")
            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error deleting connection: {e}")
            self.output_error(f"Error deleting connection: {e}")
            return 1

    # =====================================================================
    # TEST OPERATIONS
    # =====================================================================

    def test_connection(self, name):
        """Test a database connection"""
        self.log_info(f"Testing connection: {name}")

        try:
            conn = self.session.query(self.connection_model).filter_by(name=name).first()
            if not conn:
                self.output_error(f"Connection '{name}' not found")
                return 1

            if self._test_connection_internal(conn):
                self.output_success(f"Connection '{name}' test successful!")
                return 0
            else:
                self.output_error(f"Connection '{name}' test failed")
                return 1

        except Exception as e:
            self.log_error(f"Error testing connection: {e}")
            self.output_error(f"Error testing connection: {e}")
            return 1

    def _test_connection_internal(self, conn):
        """Internal method to test a connection"""
        try:
            self.output_info(f"Testing {conn.database_type.display} connection...")
            
            # Get engine for this connection
            engine = self.db_manager.get_engine(conn.id)
            
            # Test with a simple query
            with engine.connect() as connection:
                if conn.database_type.name in ['postgres', 'postgresql', 'mysql', 'sqlite']:
                    result = connection.execute(text("SELECT 1"))
                elif conn.database_type.name == 'mssql':
                    result = connection.execute(text("SELECT 1 AS test"))
                elif conn.database_type.name == 'oracle':
                    result = connection.execute(text("SELECT 1 FROM DUAL"))
                else:
                    # Generic test
                    result = connection.execute(text("SELECT 1"))
                
                result.fetchone()
                
            return True

        except Exception as e:
            self.log_error(f"Connection test failed: {e}")
            self.output_error(f"Test failed: {str(e)}")
            return False

    # =====================================================================
    # CACHE OPERATIONS
    # =====================================================================

    def manage_cache(self, action, connection_name=None):
        """Manage connection cache"""
        self.log_info(f"Cache management - action: {action}, connection: {connection_name}")

        try:
            if action == 'clear':
                if connection_name:
                    conn = self.session.query(self.connection_model).filter_by(name=connection_name).first()
                    if not conn:
                        self.output_error(f"Connection '{connection_name}' not found")
                        return 1
                    self.db_manager.invalidate_cache(conn.id)
                    self.output_success(f"Cache cleared for connection: {connection_name}")
                else:
                    self.db_manager.invalidate_cache()
                    self.output_success("All connection caches cleared")

            elif action == 'status':
                # Show cache status
                engine_count = len(self.db_manager.engines)
                session_count = len(self.db_manager.sessionmakers)
                
                self.output_info("Connection Cache Status:")
                self.output_info(f"  Cached engines: {engine_count}")
                self.output_info(f"  Cached sessionmakers: {session_count}")
                
                if self.verbose and (engine_count > 0 or session_count > 0):
                    self.output_info("\nCached connections:")
                    for conn_id in self.db_manager.engines.keys():
                        # Try to find connection name
                        conn = self.session.query(self.connection_model).filter_by(id=conn_id).first()
                        if conn:
                            self.output_info(f"  - {conn.name} ({conn_id})")
                        else:
                            self.output_info(f"  - {conn_id}")

            return 0

        except Exception as e:
            self.log_error(f"Error managing cache: {e}")
            self.output_error(f"Error managing cache: {e}")
            return 1

    # =====================================================================
    # MAIN CONNECTION OPERATIONS
    # =====================================================================

    def set_main_connection(self, name):
        """Set the main/default connection"""
        self.log_info(f"Setting main connection: {name}")

        try:
            conn = self.session.query(self.connection_model).filter_by(name=name).first()
            if not conn:
                self.output_error(f"Connection '{name}' not found")
                return 1

            if not conn.is_active:
                self.output_error(f"Connection '{name}' is not active")
                return 1

            # This would typically update a config file or database setting
            # For now, we'll just show what would happen
            self.output_warning("Setting main connection requires updating application configuration")
            self.output_info(f"Add to your config: MAIN_DB_CONNECTION_ID = '{conn.id}'")
            
            # Test the connection first
            if self._test_connection_internal(conn):
                self.output_success(f"Connection '{name}' is valid and can be set as main")
            else:
                self.output_error("Connection test failed - fix issues before setting as main")
                return 1

            return 0

        except Exception as e:
            self.log_error(f"Error setting main connection: {e}")
            self.output_error(f"Error setting main connection: {e}")
            return 1

    # =====================================================================
    # UTILITY METHODS
    # =====================================================================

    def _parse_connection_info(self, conn):
        """Parse connection information for display"""
        info = {
            'host': 'N/A',
            'port': None,
            'database': 'N/A'
        }

        conn_str = conn.connection_string
        
        # URL format
        if '://' in conn_str:
            try:
                parsed = urlparse(conn_str)
                info['host'] = parsed.hostname or 'localhost'
                info['port'] = parsed.port
                info['database'] = parsed.path.lstrip('/') if parsed.path else 'N/A'
            except:
                pass
        
        # SQLite
        elif conn.database_type.name == 'sqlite':
            info['host'] = conn_str
            info['database'] = 'SQLite File'
        
        # Key-value format
        else:
            if '=' in conn_str:
                params = self._parse_key_value_conn_string(conn_str)
                # Common parameter names
                info['host'] = params.get('Server') or params.get('host') or params.get('server') or 'N/A'
                info['port'] = params.get('Port') or params.get('port')
                info['database'] = params.get('Database') or params.get('database') or params.get('dbname') or 'N/A'

        return info

    def _parse_key_value_conn_string(self, conn_str):
        """Parse key-value connection string"""
        delim = ';' if ';' in conn_str and '=' in conn_str else ' '
        parts = conn_str.split(delim)
        params = {}
        for p in parts:
            if '=' in p:
                k, v = p.split('=', 1)
                params[k.strip()] = v.strip()
        return params

    def close(self):
        """Clean up resources"""
        self.log_debug("Closing connection CLI")
        super().close()


def main():
    """Entry point for connection CLI"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  connection list                           # List all connections
  connection show mydb                      # Show connection details
  connection create mydb postgres "localhost:5432/testdb" -u dbuser
  connection test mydb                      # Test database connection
  connection delete mydb                    # Delete connection
  connection cache clear                    # Clear all connection caches
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl'],
                       help='Table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List connections')
    list_parser.add_argument('--show-credentials', action='store_true', help='Show credentials')
    list_parser.add_argument('--type', help='Filter by database type')

    # Types command
    types_parser = subparsers.add_parser('types', help='List database types')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show connection details')
    show_parser.add_argument('name', help='Connection name')
    show_parser.add_argument('--show-password', action='store_true', help='Show password')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new connection')
    create_parser.add_argument('name', help='Connection name')
    create_parser.add_argument('type', help='Database type')
    create_parser.add_argument('connection_string', help='Connection string')
    create_parser.add_argument('--username', '-u', help='Database username')
    create_parser.add_argument('--password', '-p', help='Database password')
    create_parser.add_argument('--option', '-o', action='append', help='Connection option (key=value)')

    # Create interactive command
    create_int_parser = subparsers.add_parser('create-interactive', help='Create connection interactively')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update connection')
    update_parser.add_argument('name', help='Connection name')
    update_parser.add_argument('--connection-string', help='New connection string')
    update_parser.add_argument('--username', '-u', help='New username')
    update_parser.add_argument('--password', '-p', help='New password')
    update_parser.add_argument('--active', type=lambda x: x.lower() == 'true', help='Set active status')
    update_parser.add_argument('--set-option', action='append', help='Set option (key=value)')
    update_parser.add_argument('--remove-option', action='append', help='Remove option (key)')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete connection')
    delete_parser.add_argument('name', help='Connection name')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test connection')
    test_parser.add_argument('name', help='Connection name')

    # Cache command
    cache_parser = subparsers.add_parser('cache', help='Manage connection cache')
    cache_parser.add_argument('action', choices=['status', 'clear'], help='Cache action')
    cache_parser.add_argument('--connection', help='Specific connection name')

    # Set main command
    setmain_parser = subparsers.add_parser('set-main', help='Set main connection')
    setmain_parser.add_argument('name', help='Connection name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = ConnectionCLI(
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
            return cli.list_connections(
                show_credentials=args.show_credentials,
                db_type=args.type
            )

        elif args.command == 'types':
            return cli.list_database_types()

        elif args.command == 'show':
            return cli.show_connection(args.name, args.show_password)

        elif args.command == 'create':
            return cli.create_connection(
                args.name,
                args.type,
                args.connection_string,
                username=args.username,
                password=args.password,
                options=args.option
            )

        elif args.command == 'create-interactive':
            return cli.create_connection_interactive()

        elif args.command == 'update':
            kwargs = {}
            if args.connection_string:
                kwargs['connection_string'] = args.connection_string
            if args.username is not None:
                kwargs['username'] = args.username
            if args.password is not None:
                kwargs['password'] = args.password
            if args.active is not None:
                kwargs['is_active'] = args.active
            if args.set_option:
                kwargs['set_option'] = args.set_option
            if args.remove_option:
                kwargs['remove_option'] = args.remove_option
            
            return cli.update_connection(args.name, **kwargs)

        elif args.command == 'delete':
            return cli.delete_connection(args.name, args.force)

        elif args.command == 'test':
            return cli.test_connection(args.name)

        elif args.command == 'cache':
            return cli.manage_cache(args.action, args.connection)

        elif args.command == 'set-main':
            return cli.set_main_connection(args.name)

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())