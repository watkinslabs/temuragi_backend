#!/usr/bin/env python3
"""
Database Management CLI Tool
"""

import argparse
import sys
import inspect
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app path
sys.path.append('/web/temuragi')
from app.base.cli_v1 import BaseCLI

try:
    from app.config import config
except ImportError:
    print("Error: Could not import app.config")
    sys.exit(1)

CLI_DESCRIPTION = "Database Init"


class DatabaseCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with database connection enabled
        super().__init__(
            name="database",
            log_file="logs/database_cli.log",
            connect_db=True,  # Let base class handle DB connection
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting database CLI initialization")
        
        # Create engine from the session's bind for operations that need it
        if self.session and self.session.bind:
            self.engine = self.session.bind
            self.log_info("Engine reference created from session")
        else:
            # Create engine directly if session doesn't have one
            self.engine = create_engine(config['DATABASE_URI'])
            self.log_info("Engine created directly from DATABASE_URI")

    def discover_models_with_initial_data(self):
        """Discover all models that have create_initial_data method using base class methods"""
        self.log_info("Discovering models with initial data methods")

        try:
            from app.register.database import get_all_models

            self.output_info("Discovering and importing models...")

            # Get all models from the registry
            all_models = get_all_models()

            self.output_info("Checking models for initial data methods...")

            models_with_initial_data = []

            # Check each model in the registry for create_initial_data method
            for name, model_class in all_models.items():
                # Skip table name aliases (only process actual class names)
                if hasattr(model_class, '__name__') and name == model_class.__name__:
                    if hasattr(model_class, 'create_initial_data'):
                        method = getattr(model_class, 'create_initial_data')
                        # Ensure it's a callable method
                        if callable(method):
                            models_with_initial_data.append({
                                'class': model_class,
                                'class_name': name,
                                'module_path': model_class.__module__,
                                'table_name': model_class.__tablename__,
                                'method': method
                            })
                            self.log_debug(f"Found {name}.create_initial_data() in {model_class.__module__}")

            self.log_info(f"Found {len(models_with_initial_data)} models with create_initial_data methods")

            return models_with_initial_data

        except Exception as e:
            self.log_error(f"Error discovering models: {e}")
            self.output_error(f"Error discovering models: {e}")
            return []

    def list_tables(self):
        """List all current database tables with row counts"""
        self.log_info("Listing database tables")

        try:
            # Get tables with row counts
            query = text("""
                SELECT
                    t.table_name,
                    COALESCE(s.n_tup_ins, 0) as estimated_rows
                FROM information_schema.tables t
                LEFT JOIN pg_stat_user_tables s ON t.table_name = s.relname
                WHERE t.table_schema = current_schema()
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """)

            results = self.session.execute(query).fetchall()

            if not results:
                self.output_warning("No tables found in database")
                return 0

            headers = ['Table Name', 'Est. Rows']
            rows = []
            total_tables = 0
            total_rows = 0

            for table_name, row_count in results:
                rows.append([table_name, f"{row_count:,}"])
                total_tables += 1
                total_rows += row_count or 0

            self.output_info("Current Database Tables:")
            self.output_table(rows, headers=headers)
            self.output_info(f"Summary: {total_tables} tables, {total_rows:,} total rows")

            return 0

        except Exception as e:
            self.log_error(f"Error listing tables: {e}")
            self.output_error(f"Error listing tables: {e}")
            return 1

    def drop_tables(self, skip_permission_errors=True):
        """Drop all tables in reverse dependency order"""
        self.log_info("Dropping all database tables")

        try:
            # Get all table names with owner info
            result = self.session.execute(text("""
                SELECT t.table_name, t.table_schema, pg_tables.tableowner
                FROM information_schema.tables t
                LEFT JOIN pg_tables ON t.table_name = pg_tables.tablename
                    AND t.table_schema = pg_tables.schemaname
                WHERE t.table_schema = current_schema()
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """))

            table_info = [(row[0], row[1], row[2]) for row in result.fetchall()]

            if not table_info:
                self.output_warning("No tables found to drop")
                return 0

            self.output_info(f"Found {len(table_info)} tables to drop:")
            for table_name, schema, owner in table_info:
                owner_info = f" (owner: {owner})" if owner else ""
                self.log_debug(f"Table: {table_name}{owner_info}")

            # Get current user for comparison
            current_user_result = self.session.execute(text("SELECT current_user"))
            current_user = current_user_result.scalar()
            self.log_info(f"Current database user: {current_user}")

            # Drop tables, handling permission errors
            self.output_info("Dropping tables with CASCADE...")
            dropped_count = 0
            permission_errors = []

            for table_name, schema, owner in table_info:
                try:
                    self.session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    self.log_debug(f"Dropped: {table_name}")
                    dropped_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if "InsufficientPrivilege" in error_msg or "must be owner" in error_msg:
                        permission_errors.append((table_name, owner))
                        if skip_permission_errors:
                            self.output_warning(f"Skipped {table_name}: insufficient privileges (owner: {owner})")
                        else:
                            self.output_error(f"Failed to drop {table_name}: {e}")
                    else:
                        self.output_error(f"Failed to drop {table_name}: {e}")
                        self.log_error(f"Failed to drop {table_name}: {e}")

            self.session.commit()

            # Summary report
            self.output_info(f"Drop Summary:")
            self.output_info(f"  Successfully dropped: {dropped_count} tables")

            if permission_errors:
                self.output_warning(f"  Permission denied: {len(permission_errors)} tables")
                self.output_info("Tables requiring elevated privileges:")
                for table_name, owner in permission_errors:
                    self.output_info(f"    - {table_name} (owner: {owner})")

                self.output_info(f"To drop these tables, either:")
                self.output_info(f"  1. Connect as superuser or table owner")
                self.output_info(f"  2. Have the owner grant DROP privileges")
                self.output_info(f"  3. Use: ALTER TABLE {permission_errors[0][0]} OWNER TO {current_user};")

            # Verify remaining tables
            result = self.session.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
            """))
            remaining = result.scalar()

            if remaining == 0:
                self.output_success("All tables dropped successfully!")
                return 0
            elif permission_errors and skip_permission_errors:
                self.output_warning(f"{remaining} tables remain (permission issues)")
                return 0  # Success with warnings
            else:
                self.output_error(f"{remaining} tables still remain")
                return 1

        except Exception as e:
            self.log_error(f"Error dropping tables: {e}")
            self.output_error(f"Error dropping tables: {e}")
            self.session.rollback()
            return 1

    def force_drop_tables(self):
        """Attempt to force drop tables by changing ownership first"""
        self.log_warning("Attempting forced table drop")

        try:
            self.output_info("Attempting forced table drop (requires elevated privileges)...")

            # Get current user
            current_user_result = self.session.execute(text("SELECT current_user"))
            current_user = current_user_result.scalar()

            # Get all tables
            result = self.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))

            table_names = [row[0] for row in result.fetchall()]

            if not table_names:
                self.output_warning("No tables found to drop")
                return 0

            self.output_info(f"Attempting to take ownership and drop {len(table_names)} tables...")

            for table_name in table_names:
                try:
                    # Try to change ownership first
                    self.session.execute(text(f"ALTER TABLE {table_name} OWNER TO {current_user}"))
                    self.log_debug(f"Changed owner: {table_name}")
                except Exception as e:
                    self.output_warning(f"Could not change owner for {table_name}: {e}")

                try:
                    # Now try to drop
                    self.session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    self.log_debug(f"Dropped: {table_name}")
                except Exception as e:
                    self.output_error(f"Still failed to drop {table_name}: {e}")

            self.session.commit()

            # Check what remains
            result = self.session.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
            """))
            remaining = result.scalar()

            if remaining == 0:
                self.output_success("Force drop completed successfully!")
                return 0
            else:
                self.output_warning(f"{remaining} tables still remain after force attempt")
                return 1

        except Exception as e:
            self.log_error(f"Error in force drop: {e}")
            self.output_error(f"Error in force drop: {e}")
            self.session.rollback()
            return 1

    def create_tables(self):
        """Create all tables using the model discovery system"""
        self.log_info("Creating database tables")

        try:
            from app.register.database import create_all_tables

            self.output_info("Creating database tables...")
            create_all_tables(self.app, self.engine)

            self.output_success("Tables created successfully!")
            return 0

        except Exception as e:
            self.log_error(f"Error creating tables: {e}")
            self.output_error(f"Error creating tables: {e}")
            return 1

    def rebuild_tables(self):
        """Drop all tables then recreate them"""
        self.log_info("Rebuilding database tables")

        try:
            self.output_info("Rebuilding database tables...")

            # Step 1: Drop all tables
            self.output_info("STEP 1: Dropping existing tables")
            drop_result = self.drop_tables()

            if drop_result != 0:
                self.output_error("Failed to drop tables, aborting rebuild")
                return 1

            self.output_info("STEP 2: Creating fresh tables")
            create_result = self.create_tables()

            if create_result == 0:
                self.output_success("Database rebuild completed successfully!")
                return 0
            else:
                self.output_error("Failed to recreate tables")
                return 1

        except Exception as e:
            self.log_error(f"Error during rebuild: {e}")
            self.output_error(f"Error during rebuild: {e}")
            return 1

    def setup_database(self):
        """Complete database setup with users, permissions, and seed data"""
        self.log_info("Setting up complete database environment")

        try:
            self.output_info("Setting up complete database environment...")

            # Step 1: Create database users/roles
            self.output_info("STEP 1: Creating database users and roles")
            users_result = self.create_database_users()

            # Step 2: Create all tables
            self.output_info("STEP 2: Creating database tables")
            tables_result = self.create_tables()

            if tables_result != 0:
                self.output_error("Failed to create tables, aborting setup")
                return 1

            # Step 3: Set up table permissions
            self.output_info("STEP 3: Setting up table permissions")
            perms_result = self.setup_table_permissions()

            # Step 4: Insert seed data
            self.output_info("STEP 4: Inserting seed data")
            seed_result = self.insert_seed_data()

            if all(result == 0 for result in [tables_result, perms_result, seed_result]):
                self.output_success("Complete database setup finished successfully!")
                return 0
            else:
                self.output_warning("Setup completed with some warnings")
                return 1

        except Exception as e:
            self.log_error(f"Error during database setup: {e}")
            self.output_error(f"Error during database setup: {e}")
            return 1

    def create_database_users(self):
        """Create database users and roles"""
        self.log_info("Creating database users and roles")

        try:
            users_to_create = [
                ('app_admin', 'Administrative user for application'),
                ('app_user', 'Standard application user'),
                ('app_readonly', 'Read-only user for reports'),
            ]

            for username, description in users_to_create:
                try:
                    # Check if user exists
                    result = self.session.execute(
                        text("SELECT 1 FROM pg_roles WHERE rolname = :username"),
                        {"username": username}
                    )

                    if result.fetchone():
                        self.log_debug(f"User {username} already exists")
                    else:
                        # Create user with login capability
                        self.session.execute(text(f"CREATE USER {username} WITH LOGIN"))
                        self.log_info(f"Created user: {username} ({description})")

                except Exception as e:
                    self.log_warning(f"Could not create user {username}: {e}")

            self.session.commit()
            return 0

        except Exception as e:
            self.log_error(f"Error creating users: {e}")
            self.output_error(f"Error creating users: {e}")
            self.session.rollback()
            return 1

    def setup_table_permissions(self):
        """Set up table permissions for users"""
        self.log_info("Setting up table permissions")

        try:
            # Get all tables
            result = self.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
            """))

            tables = [row[0] for row in result.fetchall()]

            if not tables:
                self.output_warning("No tables found to set permissions on")
                return 0

            # Permission sets
            permissions = [
                ('app_admin', 'ALL', 'Full administrative access'),
                ('app_user', 'SELECT, INSERT, UPDATE, DELETE', 'Standard CRUD operations'),
                ('app_readonly', 'SELECT', 'Read-only access'),
            ]

            for username, perms, description in permissions:
                self.log_debug(f"Setting {description.lower()} for {username}")

                for table in tables:
                    try:
                        self.session.execute(text(f"GRANT {perms} ON {table} TO {username}"))
                    except Exception as e:
                        self.log_warning(f"Failed to grant {perms} on {table} to {username}: {e}")

                self.log_info(f"Permissions set for {username}")

            self.session.commit()
            return 0

        except Exception as e:
            self.log_error(f"Error setting permissions: {e}")
            self.output_error(f"Error setting permissions: {e}")
            self.session.rollback()
            return 1

    def insert_seed_data(self):
        """Insert seed data - placeholder for now"""
        self.log_info("Inserting seed data")
        self.output_warning("Seed data insertion not implemented yet")
        return 0

    def preview_model_order(self):
        """Preview global model loading order with range information"""
        self.log_info("Previewing model loading order")

        try:
            from app.register.database import preview_model_registry

            self.output_info("Previewing model registry...")

            # Preview the registry
            registry = preview_model_registry()

            if not registry:
                self.output_warning("No models found in registry")
                return 1

            # Create a summary of the models
            model_classes = {}
            table_aliases = {}

            for name, model_class in registry.items():
                if hasattr(model_class, '__tablename__'):
                    if name == model_class.__name__:
                        # This is the actual class name
                        model_classes[name] = model_class
                    elif name == model_class.__tablename__:
                        # This is a table name alias
                        table_aliases[name] = model_class

            # Display model information
            self.output_info("Model Classes in Registry:")
            headers = ['Class Name', 'Table Name', 'Module', 'Dependencies']
            rows = []

            for name, model_class in sorted(model_classes.items()):
                table = model_class.__tablename__
                module = model_class.__module__.split('.')[-1]
                deps = getattr(model_class, '__depends_on__', None)
                deps_str = str(deps) if deps else ''

                rows.append([name, table, module, deps_str])

            self.output_table(rows, headers=headers)

            self.output_info(f"Summary:")
            self.output_info(f"  Model Classes: {len(model_classes)}")
            self.output_info(f"  Table Aliases: {len(table_aliases)}")
            self.output_info(f"  Total Registry: {len(registry)} entries")

            return 0

        except Exception as e:
            self.log_error(f"Error previewing model order: {e}")
            self.output_error(f"Error previewing model order: {e}")
            return 1

    def drop_database(self, database_name):
        """Drop entire database (requires superuser privileges)"""
        self.log_warning(f"Dropping database: {database_name}")

        try:
            self.output_warning(f"Dropping database: {database_name}")
            self.output_warning("WARNING: This will permanently delete the entire database!")

            # Confirm action
            confirm = input("Type 'DROP DATABASE' to confirm: ")
            if confirm != 'DROP DATABASE':
                self.output_info("Operation cancelled")
                return 1

            # Close current session
            self.session.close()

            # Create connection to postgres database for admin operations
            from urllib.parse import urlparse
            db_url = config['DATABASE_URI']
            parsed = urlparse(db_url)

            # Connect to postgres database instead of target database
            admin_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            admin_engine = create_engine(admin_url, isolation_level='AUTOCOMMIT')

            with admin_engine.connect() as conn:
                # Terminate existing connections to the database
                self.output_info(f"Terminating connections to {database_name}...")
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                """), {"db_name": database_name})

                # Drop the database
                self.output_info(f"Dropping database {database_name}...")
                conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))

            self.output_success(f"Database '{database_name}' dropped successfully!")
            return 0

        except Exception as e:
            self.log_error(f"Error dropping database: {e}")
            self.output_error(f"Error dropping database: {e}")
            return 1

    def create_database(self, database_name, owner=None):
        """Create new database (requires superuser privileges)"""
        self.log_info(f"Creating database: {database_name}")

        try:
            # Close current session
            self.session.close()

            # Create connection to postgres database for admin operations
            from urllib.parse import urlparse
            db_url = config['DATABASE_URI']
            parsed = urlparse(db_url)

            # Connect to postgres database instead of target database
            admin_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
            admin_engine = create_engine(admin_url, isolation_level='AUTOCOMMIT')

            with admin_engine.connect() as conn:
                # Check if database already exists
                result = conn.execute(text("""
                    SELECT 1 FROM pg_database WHERE datname = :db_name
                """), {"db_name": database_name})

                if result.fetchone():
                    self.output_warning(f"Database '{database_name}' already exists")
                    return 1

                # Create the database
                owner_clause = f' OWNER "{owner}"' if owner else ''
                create_sql = f'CREATE DATABASE "{database_name}"{owner_clause}'

                self.log_info(f"Creating database with SQL: {create_sql}")
                conn.execute(text(create_sql))

            self.output_success(f"Database '{database_name}' created successfully!")

            # Reconnect to the new database
            new_db_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{database_name}"
            self.engine = create_engine(new_db_url)
            session_factory = sessionmaker(bind=self.engine)
            self.session = session_factory()

            return 0

        except Exception as e:
            self.log_error(f"Error creating database: {e}")
            self.output_error(f"Error creating database: {e}")
            return 1

    def recreate_database(self, database_name, owner=None):
        """Drop and recreate database"""
        self.log_info(f"Recreating database: {database_name}")

        try:
            self.output_info(f"Recreating database: {database_name}")

            # Step 1: Drop existing database
            self.output_info("STEP 1: Dropping existing database")
            drop_result = self.drop_database(database_name)

            # Continue even if drop fails (database might not exist)

            self.output_info("STEP 2: Creating fresh database")
            create_result = self.create_database(database_name, owner)

            if create_result == 0:
                self.output_success(f"Database '{database_name}' recreated successfully!")
                return 0
            else:
                self.output_error(f"Failed to recreate database '{database_name}'")
                return 1

        except Exception as e:
            self.log_error(f"Error during database recreation: {e}")
            self.output_error(f"Error during database recreation: {e}")
            return 1

    def create_initial_data(self, model_filter=None):
        """Create initial data for all models that support it"""
        self.log_info("Creating initial data from model methods")

        try:
            self.output_info("Creating initial data from model methods...")

            models_with_data = self.discover_models_with_initial_data()

            if not models_with_data:
                self.output_warning("No models found with create_initial_data method")
                return 0

            self.output_info(f"Found {len(models_with_data)} models with initial data methods:")
            for model_info in models_with_data:
                self.log_debug(f"Model: {model_info['class_name']} ({model_info['table_name']})")

            self.output_info("Creating initial data...")

            success_count = 0
            error_count = 0

            for model_info in models_with_data:
                model_class = model_info['class']
                model_name = model_info['class_name']
                table_name = model_info['table_name']

                # Apply filter if specified
                if model_filter and model_filter.lower() not in model_name.lower():
                    continue

                try:
                    self.log_debug(f"Processing {model_name} ({table_name})")

                    # Check if method expects session parameter
                    sig = inspect.signature(model_class.create_initial_data)
                    if 'session' in sig.parameters:
                        result = model_class.create_initial_data(session=self.session)
                    else:
                        result = model_class.create_initial_data()

                    if result is False:
                        self.output_warning(f"{model_name}: create_initial_data returned False")
                    else:
                        self.log_info(f"{model_name}: Initial data created")
                        success_count += 1

                except Exception as e:
                    self.log_error(f"{model_name}: Error - {e}")
                    self.output_error(f"{model_name}: Error - {e}")
                    error_count += 1

            # Commit all changes
            try:
                self.session.commit()
                self.log_info("All changes committed to database")
            except Exception as e:
                self.log_error(f"Error committing changes: {e}")
                self.output_error(f"Error committing changes: {e}")
                self.session.rollback()
                return 1

            # Summary
            self.output_info(f"Summary:")
            self.output_info(f"  Success: {success_count} models")
            self.output_info(f"  Errors:  {error_count} models")

            if error_count == 0:
                self.output_success("All initial data created successfully!")
                return 0
            else:
                self.output_warning(f"Completed with {error_count} errors")
                return 1

        except Exception as e:
            self.log_error(f"Error creating initial data: {e}")
            self.output_error(f"Error creating initial data: {e}")
            self.session.rollback()
            return 1

    def list_models_with_initial_data(self):
        """List all models that have create_initial_data method"""
        self.log_info("Listing models with initial data support")

        try:
            models_with_data = self.discover_models_with_initial_data()

            if not models_with_data:
                self.output_warning("No models found with create_initial_data method")
                return 0

            self.output_info("Models with Initial Data Support:")

            headers = ['Model', 'Table', 'Module', 'Method Info']
            rows = []

            for model_info in models_with_data:
                model_class = model_info['class']
                method = getattr(model_class, 'create_initial_data')

                # Get method signature info
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                method_info = f"({', '.join(params)})"

                rows.append([
                    model_info['class_name'],
                    model_info['table_name'],
                    model_info['module_path'].split('.')[-1],  # Just the last part
                    method_info
                ])

            self.output_table(rows, headers=headers)
            self.output_info(f"Total: {len(models_with_data)} models support initial data creation")

            return 0

        except Exception as e:
            self.log_error(f"Error listing models: {e}")
            self.output_error(f"Error listing models: {e}")
            return 1

    def setup_complete_database(self):
        """Complete database setup including initial data"""
        self.log_info("Setting up complete database with initial data")

        try:
            self.output_info("Setting up complete database with initial data...")

            # Step 1: Create database users/roles
            self.output_info("STEP 1: Creating database users and roles")
            users_result = self.create_database_users()

            # Step 2: Create all tables
            self.output_info("STEP 2: Creating database tables")
            tables_result = self.create_tables()

            if tables_result != 0:
                self.output_error("Failed to create tables, aborting setup")
                return 1

            # Step 3: Set up table permissions
            self.output_info("STEP 3: Setting up table permissions")
            perms_result = self.setup_table_permissions()

            # Step 4: Create model initial data
            self.output_info("STEP 4: Creating model initial data")
            initial_data_result = self.create_initial_data()

            if all(result == 0 for result in [tables_result, perms_result, initial_data_result]):
                self.output_success("Complete database setup with initial data finished successfully!")
                return 0
            else:
                self.output_warning("Setup completed with some warnings")
                return 1

        except Exception as e:
            self.log_error(f"Error during complete database setup: {e}")
            self.output_error(f"Error during complete database setup: {e}")
            return 1

    def list_models(self):
        """List all discovered models and their details"""
        self.log_info("Listing discovered models")

        try:
            from app.register.database import get_all_models

            self.output_info("Discovering and importing models...")

            # Get all models from the registry
            all_models = get_all_models()

            if not all_models:
                self.output_warning("No models found in registry")
                return 0

            self.output_info(f"Found {len(all_models)} entries in model registry:")

            # Separate actual model classes from table name aliases
            model_classes = {}
            table_aliases = {}

            for name, model_class in all_models.items():
                if hasattr(model_class, '__tablename__') and hasattr(model_class, '__name__'):
                    if name == model_class.__name__:
                        # This is the actual class name
                        model_classes[name] = model_class
                    elif name == model_class.__tablename__:
                        # This is a table name alias
                        table_aliases[name] = model_class

            # Display model classes
            if model_classes:
                headers = ['Class Name', 'Table Name', 'Module', 'Dependencies', 'Methods']
                rows = []

                for name, model_class in sorted(model_classes.items()):
                    table_name = model_class.__tablename__
                    module = model_class.__module__

                    # Get dependencies
                    deps = getattr(model_class, '__depends_on__', None)
                    deps_str = str(deps) if deps else 'None'

                    # Check for common methods
                    methods = []
                    if hasattr(model_class, 'create_initial_data'):
                        methods.append('initial_data')
                    if hasattr(model_class, '__str__'):
                        methods.append('__str__')
                    if hasattr(model_class, '__repr__'):
                        methods.append('__repr__')

                    methods_str = ', '.join(methods) if methods else 'None'

                    rows.append([name, table_name, module, deps_str, methods_str])

                self.output_info("Model Classes:")
                self.output_table(rows, headers=headers)

            # Display summary
            self.output_info(f"Summary:")
            self.output_info(f"  Model Classes: {len(model_classes)}")
            self.output_info(f"  Table Aliases: {len(table_aliases)}")
            self.output_info(f"  Total Registry: {len(all_models)} entries")

            # Show table aliases if any
            if table_aliases:
                self.output_info(f"Table Name Aliases: {', '.join(sorted(table_aliases.keys()))}")

            return 0

        except Exception as e:
            self.log_error(f"Error listing models: {e}")
            self.output_error(f"Error listing models: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def debug_model_discovery(self):
        """Debug model discovery process"""
        self.log_info("Debugging model discovery process")

        try:
            self.output_info("=== DEBUG MODEL DISCOVERY ===")

            # Check config
            try:
                from app.config import config
                scan_paths = config.get('SYSTEM_SCAN_PATHS', [])
                self.output_success(f"✓ SYSTEM_SCAN_PATHS found: {scan_paths}")
            except KeyError:
                self.output_error("✗ SYSTEM_SCAN_PATHS not found in config")
                return 1
            except Exception as e:
                self.output_error(f"✗ Error importing config: {e}")
                return 1

            # Check current working directory and __package__
            import os
            self.output_info(f"Current working directory: {os.getcwd()}")

            # Try to use base class method to get models
            try:
                model = self.get_model('User')
                if model:
                    self.output_success("✓ Can retrieve models through base class method")
                else:
                    self.output_warning("⚠ Base class get_model returned None for 'User'")
            except Exception as e:
                self.output_error(f"✗ Error using base class get_model: {e}")

            # Check registry state using base class methods
            from app.register.database import get_all_models
            all_models = get_all_models()
            self.output_info(f"\n--- Registry State ---")
            self.output_info(f"Total models in registry: {len(all_models)}")
            
            if all_models:
                self.output_info("Sample models in registry:")
                for i, (name, cls) in enumerate(all_models.items()):
                    if i >= 5:  # Show first 5 only
                        break
                    self.output_info(f"  {name}: {cls} (from {cls.__module__})")
            
            self.output_info("=== END DEBUG ===")
            return 0

        except Exception as e:
            self.log_error(f"Error during debug: {e}")
            self.output_error(f"Error during debug: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Database Management CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format (default from config)')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Database management
    create_db_parser = subparsers.add_parser('create', help='Create new database')
    create_db_parser.add_argument('name', help='Database name')
    create_db_parser.add_argument('--owner', help='Database owner')

    drop_db_parser = subparsers.add_parser('drop', help='Drop database')
    drop_db_parser.add_argument('name', help='Database name')

    recreate_db_parser = subparsers.add_parser('recreate', help='Drop and recreate database')
    recreate_db_parser.add_argument('name', help='Database name')
    recreate_db_parser.add_argument('--owner', help='Database owner')

    # List tables
    subparsers.add_parser('list-tables', help='List all current database tables with row counts')

    # List Models
    subparsers.add_parser('list-models', help='List all loaded python model classes')

    subparsers.add_parser('debug-discovery', help='Debug the model discovery process')

    # Preview model order
    subparsers.add_parser('preview-order', help='Preview model loading order')

    # Create tables
    subparsers.add_parser('create-tables', help='Create all database tables')

    # Drop tables
    drop_parser = subparsers.add_parser('drop-tables', help='Drop all database tables')
    drop_parser.add_argument('--force', action='store_true', help='Attempt to force drop by changing ownership first')

    # Rebuild tables
    subparsers.add_parser('rebuild-tables', help='Drop and recreate all database tables')

    # Setup complete database
    subparsers.add_parser('setup', help='Complete database setup with users, permissions, and seed data')
    subparsers.add_parser('setup-complete', help='Complete database setup including model initial data')

    # Initial data commands
    initial_data_parser = subparsers.add_parser('create-initial-data', help='Create initial data from all model methods')
    initial_data_parser.add_argument('--filter', help='Filter models by name (partial match)')

    subparsers.add_parser('list-initial-data', help='List all models that support initial data creation')

    # User management
    user_parser = subparsers.add_parser('users', help='User management commands')
    user_subs = user_parser.add_subparsers(dest='user_action')
    user_subs.add_parser('create', help='Create database users and roles')
    user_subs.add_parser('permissions', help='Set up table permissions')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = DatabaseCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'create':
            return cli.create_database(args.name, args.owner)

        elif args.command == 'drop':
            return cli.drop_database(args.name)

        elif args.command == 'recreate':
            return cli.recreate_database(args.name, args.owner)

        elif args.command == 'list-tables':
            return cli.list_tables()
        elif args.command == 'list-models':
            return cli.list_models()

        elif args.command == 'debug-discovery':
            return cli.debug_model_discovery()

        elif args.command == 'preview-order':
            return cli.preview_model_order()

        elif args.command == 'create-tables':
            return cli.create_tables()

        elif args.command == 'drop-tables':
            if args.force:
                return cli.force_drop_tables()
            else:
                return cli.drop_tables()

        elif args.command == 'rebuild-tables':
            return cli.rebuild_tables()

        elif args.command == 'setup':
            return cli.setup_database()

        elif args.command == 'setup-complete':
            return cli.setup_complete_database()

        elif args.command == 'create-initial-data':
            model_filter = getattr(args, 'filter', None)
            return cli.create_initial_data(model_filter)

        elif args.command == 'list-initial-data':
            return cli.list_models_with_initial_data()

        elif args.command == 'users':
            if args.user_action == 'create':
                return cli.create_database_users()
            elif args.user_action == 'permissions':
                return cli.setup_table_permissions()
            else:
                user_parser.print_help()
                return 1

        else:
            parser.print_help()
            return 1

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