#!/usr/bin/env python3
"""
Database Management CLI Tool
"""

import argparse
import sys
import os
import re
import importlib
import inspect
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Add app path
sys.path.append('/web/temuragi')

try:
    from app.config import config
except ImportError:
    print("Error: Could not import app.config")
    sys.exit(1)


class DatabaseCLI:
    def __init__(self, db_config=None):
        """Initialize CLI with database connection"""
        if db_config:
            self.engine = create_engine(db_config)
        else:
            self.engine = create_engine(config['DATABASE_URI'])

        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()

    def discover_models_with_initial_data(self):
        """Discover all models that have create_initial_data method using register_db functions"""
        try:
            from app.register_db import discover_and_import_models
            
            print("🔍 Discovering CLI modules and models...")
            
            # Mock app for logging
            class MockApp:
                def __init__(self):
                    import logging
                    self.logger = logging.getLogger('cli')
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(levelname)s: %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
                    self.logger.setLevel(logging.INFO)

            mock_app = MockApp()
            
            # Use the exact same model discovery and import as register_db
            discover_and_import_models(mock_app)
            
            # Now find models with create_initial_data methods by searching imported modules
            models_with_initial_data = []
            
            print("\nDiscovering models with initial data methods...")
            
            # Search through all loaded modules for SQLAlchemy models
            for module_name in sys.modules:
                if module_name.startswith('app.') and 'model' in module_name:
                    try:
                        module = sys.modules[module_name]
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # Check if it's a model class (has __tablename__)
                            if hasattr(obj, '__tablename__'):
                                # Check if it has create_initial_data method
                                if hasattr(obj, 'create_initial_data'):
                                    method = getattr(obj, 'create_initial_data')
                                    # Ensure it's a classmethod or static method
                                    if (inspect.ismethod(method) or 
                                        (hasattr(method, '__func__') and inspect.isfunction(method.__func__))):
                                        
                                        models_with_initial_data.append({
                                            'class': obj,
                                            'class_name': name,
                                            'module_path': module_name,
                                            'table_name': obj.__tablename__,
                                            'model_order': getattr(obj, '_model_order', 999),
                                            'display_path': module_name,
                                            'method': method
                                        })
                                        print(f"    ✓ Found {name}.create_initial_data() in {module_name}")
                        
                    except Exception as e:
                        continue
            
            print(f"INFO: Found {len(models_with_initial_data)} models with create_initial_data methods")
            
            return models_with_initial_data
            
        except Exception as e:
            print(f"Error discovering models: {e}")
            import traceback
            traceback.print_exc()
            return []

    def list_tables(self):
        """List all current database tables with row counts"""
        try:
            print("Current Database Tables:")
            print("=" * 50)
            
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
                print("No tables found in database")
                return 0
            
            headers = ['Table Name', 'Est. Rows']
            rows = []
            total_tables = 0
            total_rows = 0
            
            for table_name, row_count in results:
                rows.append([table_name, f"{row_count:,}"])
                total_tables += 1
                total_rows += row_count or 0
            
            print(tabulate(rows, headers=headers, tablefmt='simple'))
            print(f"\nSummary: {total_tables} tables, {total_rows:,} total rows")
            
            return 0
            
        except Exception as e:
            print(f"Error listing tables: {e}")
            return 1

    def drop_tables(self, skip_permission_errors=True):
        """Drop all tables in reverse dependency order"""
        try:
            print("Dropping all database tables...")
            
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
                print("No tables found to drop")
                return 0
            
            print(f"Found {len(table_info)} tables to drop:")
            for table_name, schema, owner in table_info:
                owner_info = f" (owner: {owner})" if owner else ""
                print(f"  - {table_name}{owner_info}")
            
            # Get current user for comparison
            current_user_result = self.session.execute(text("SELECT current_user"))
            current_user = current_user_result.scalar()
            print(f"\nCurrent database user: {current_user}")
            
            # Drop tables, handling permission errors
            print("\nDropping tables with CASCADE...")
            dropped_count = 0
            permission_errors = []
            
            for table_name, schema, owner in table_info:
                try:
                    self.session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    print(f"  ✓ Dropped: {table_name}")
                    dropped_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if "InsufficientPrivilege" in error_msg or "must be owner" in error_msg:
                        permission_errors.append((table_name, owner))
                        if skip_permission_errors:
                            print(f"  ⚠️  Skipped {table_name}: insufficient privileges (owner: {owner})")
                        else:
                            print(f"  ✗ Failed to drop {table_name}: {e}")
                    else:
                        print(f"  ✗ Failed to drop {table_name}: {e}")
            
            self.session.commit()
            
            # Summary report
            print(f"\nDrop Summary:")
            print(f"  Successfully dropped: {dropped_count} tables")
            
            if permission_errors:
                print(f"  Permission denied: {len(permission_errors)} tables")
                print("\nTables requiring elevated privileges:")
                for table_name, owner in permission_errors:
                    print(f"    - {table_name} (owner: {owner})")
                
                print(f"\nTo drop these tables, either:")
                print(f"  1. Connect as superuser or table owner")
                print(f"  2. Have the owner grant DROP privileges")
                print(f"  3. Use: ALTER TABLE {permission_errors[0][0]} OWNER TO {current_user};")
            
            # Verify remaining tables
            result = self.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
            """))
            remaining = result.scalar()
            
            if remaining == 0:
                print("\n✓ All tables dropped successfully!")
                return 0
            elif permission_errors and skip_permission_errors:
                print(f"\n⚠️  {remaining} tables remain (permission issues)")
                return 0  # Success with warnings
            else:
                print(f"\n❌ {remaining} tables still remain")
                return 1
                
        except Exception as e:
            print(f"Error dropping tables: {e}")
            self.session.rollback()
            return 1

    def force_drop_tables(self):
        """Attempt to force drop tables by changing ownership first"""
        try:
            print("Attempting forced table drop (requires elevated privileges)...")
            
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
                print("No tables found to drop")
                return 0
            
            print(f"Attempting to take ownership and drop {len(table_names)} tables...")
            
            for table_name in table_names:
                try:
                    # Try to change ownership first
                    self.session.execute(text(f"ALTER TABLE {table_name} OWNER TO {current_user}"))
                    print(f"  ✓ Changed owner: {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not change owner for {table_name}: {e}")
                
                try:
                    # Now try to drop
                    self.session.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    print(f"  ✓ Dropped: {table_name}")
                except Exception as e:
                    print(f"  ✗ Still failed to drop {table_name}: {e}")
            
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
                print("\n✓ Force drop completed successfully!")
                return 0
            else:
                print(f"\n⚠️  {remaining} tables still remain after force attempt")
                return 1
                
        except Exception as e:
            print(f"Error in force drop: {e}")
            self.session.rollback()
            return 1

    def create_tables(self):
        """Create all tables using the model discovery system"""
        try:
            from app.register_db import discover_and_import_models, create_all_tables
            
            # Mock app for logging
            class MockApp:
                def __init__(self):
                    import logging
                    self.logger = logging.getLogger('cli')
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(levelname)s: %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
                    self.logger.setLevel(logging.INFO)
            
            app = MockApp()
            
            print("Discovering and importing models...")
            discover_and_import_models(app)
            
            print("Creating database tables...")
            create_all_tables(app, self.engine)
            
            print("✓ Success!")
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def rebuild_tables(self):
        """Drop all tables then recreate them"""
        try:
            print("Rebuilding database tables...")
            print("=" * 50)
            
            # Step 1: Drop all tables
            print("STEP 1: Dropping existing tables")
            drop_result = self.drop_tables()
            
            if drop_result != 0:
                print("Failed to drop tables, aborting rebuild")
                return 1
            
            print("\nSTEP 2: Creating fresh tables")
            create_result = self.create_tables()
            
            if create_result == 0:
                print("\n🎉 Database rebuild completed successfully!")
                return 0
            else:
                print("\n❌ Failed to recreate tables")
                return 1
                
        except Exception as e:
            print(f"Error during rebuild: {e}")
            return 1

    def setup_database(self):
        """Complete database setup with users, permissions, and seed data"""
        try:
            print("Setting up complete database environment...")
            print("=" * 60)
            
            # Step 1: Create database users/roles
            print("STEP 1: Creating database users and roles")
            users_result = self.create_database_users()
            
            # Step 2: Create all tables
            print("\nSTEP 2: Creating database tables")
            tables_result = self.create_tables()
            
            if tables_result != 0:
                print("Failed to create tables, aborting setup")
                return 1
            
            # Step 3: Set up table permissions
            print("\nSTEP 3: Setting up table permissions")
            perms_result = self.setup_table_permissions()
            
            # Step 4: Insert seed data
            print("\nSTEP 4: Inserting seed data")
            seed_result = self.insert_seed_data()
            
            if all(result == 0 for result in [tables_result, perms_result, seed_result]):
                print("\n🎉 Complete database setup finished successfully!")
                return 0
            else:
                print("\n⚠️  Setup completed with some warnings")
                return 1
                
        except Exception as e:
            print(f"Error during database setup: {e}")
            return 1

    def create_database_users(self):
        """Create database users and roles"""
        try:
            print("Creating database users and roles...")
            
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
                        print(f"  ✓ User {username} already exists")
                    else:
                        # Create user with login capability
                        self.session.execute(text(f"CREATE USER {username} WITH LOGIN"))
                        print(f"  ✓ Created user: {username} ({description})")
                
                except Exception as e:
                    print(f"  ⚠️  Could not create user {username}: {e}")
            
            self.session.commit()
            return 0
            
        except Exception as e:
            print(f"Error creating users: {e}")
            self.session.rollback()
            return 1

    def setup_table_permissions(self):
        """Set up table permissions for users"""
        try:
            print("Setting up table permissions...")
            
            # Get all tables
            result = self.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("  No tables found to set permissions on")
                return 0
            
            # Permission sets
            permissions = [
                ('app_admin', 'ALL', 'Full administrative access'),
                ('app_user', 'SELECT, INSERT, UPDATE, DELETE', 'Standard CRUD operations'),
                ('app_readonly', 'SELECT', 'Read-only access'),
            ]
            
            for username, perms, description in permissions:
                print(f"  Setting {description.lower()} for {username}...")
                
                for table in tables:
                    try:
                        self.session.execute(text(f"GRANT {perms} ON {table} TO {username}"))
                    except Exception as e:
                        print(f"    ⚠️  Failed to grant {perms} on {table} to {username}: {e}")
                
                print(f"    ✓ Permissions set for {username}")
            
            self.session.commit()
            return 0
            
        except Exception as e:
            print(f"Error setting permissions: {e}")
            self.session.rollback()
            return 1

    def preview_model_order(self):
        """Preview global model loading order with range information"""
        try:
            from app.register_db import preview_model_order
            
            print("Global Model Loading Order with Ranges")
            print("=" * 70)
            
            models = preview_model_order()
            
            if not models:
                print("No model files found")
                return 1

            # Group by range
            by_range = {}
            for model in models:
                order = model.get('order', 999)
                
                # Determine range based on order number
                if order < 100:
                    range_key = "0-99"
                    category = "Core System"
                elif order < 120:
                    range_key = "100-119" 
                    category = "User Management"
                elif order < 140:
                    range_key = "120-139"
                    category = "Authentication & Security"
                elif order < 160:
                    range_key = "140-159"
                    category = "Content Management"
                elif order < 180:
                    range_key = "160-179"
                    category = "Menu & Navigation"
                elif order < 200:
                    range_key = "180-199"
                    category = "API & Integration"
                elif order < 300:
                    range_key = "200-299"
                    category = "Business Logic"
                elif order < 400:
                    range_key = "300-399"
                    category = "Customer Management"
                elif order < 500:
                    range_key = "400-499"
                    category = "Financial & Billing"
                elif order < 600:
                    range_key = "500-599"
                    category = "Third-party Integrations"
                else:
                    range_key = "600+"
                    category = "Extensions & Custom"
                
                range_info = {'range': range_key, 'category': category}
                
                if range_key not in by_range:
                    by_range[range_key] = {
                        'info': range_info,
                        'models': []
                    }
                by_range[range_key]['models'].append(model)
            
            # Display by ranges
            range_order = ["0-99", "100-119", "120-139", "140-159", "160-179", "180-199", 
                          "200-299", "300-399", "400-499", "500-599", "600+"]
            
            for range_key in range_order:
                if range_key not in by_range:
                    continue
                    
                range_data = by_range[range_key]
                range_info = range_data['info']
                models_in_range = range_data['models']
                
                print(f"\n{range_info['range']}: {range_info['category']}")
                
                if models_in_range:
                    for model in sorted(models_in_range, key=lambda x: x['order']):
                        print(f"  {model['order']:3d}: {model['display']}")
                else:
                    print("  (no models found)")
            
            # Summary table
            print(f"\nSummary:")
            print("-" * 70)
            headers = ['Range', 'Category', 'Count', 'Models']
            rows = []
            
            for range_key in range_order:
                if range_key not in by_range:
                    continue
                    
                range_data = by_range[range_key]
                range_info = range_data['info']
                models_list = range_data['models']
                
                model_names = [m['filename'] for m in models_list[:2]]
                if len(models_list) > 2:
                    model_names.append(f"... +{len(models_list)-2}")
                
                rows.append([
                    range_info['range'],
                    range_info['category'][:30] + ('...' if len(range_info['category']) > 30 else ''),
                    len(models_list),
                    ', '.join(model_names)
                ])
            
            print(tabulate(rows, headers=headers, tablefmt='simple'))
            
            print(f"\nTotal: {len(models)} model files found")
            
            # Show some example ranges
            print("\nExample Model Naming:")
            examples = [
                ("0_base_model.py", "Core System (0-99)"),
                ("160_menu_type_model.py", "Menu & Navigation (160-179)"),
                ("300_customer_model.py", "Customer Management (300-319)"),
                ("500_stripe_integration_model.py", "Third-party Integrations (500-549)")
            ]
            
            for filename, description in examples:
                print(f"  {filename:<30} -> {description}")
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def drop_database(self, database_name):
        """Drop entire database (requires superuser privileges)"""
        try:
            print(f"Dropping database: {database_name}")
            print("⚠️  WARNING: This will permanently delete the entire database!")
            
            # Confirm action
            confirm = input("Type 'DROP DATABASE' to confirm: ")
            if confirm != 'DROP DATABASE':
                print("Operation cancelled")
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
                print(f"Terminating connections to {database_name}...")
                conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                """), {"db_name": database_name})
                
                # Drop the database
                print(f"Dropping database {database_name}...")
                conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
                
            print(f"✓ Database '{database_name}' dropped successfully!")
            return 0
            
        except Exception as e:
            print(f"Error dropping database: {e}")
            return 1

    def create_database(self, database_name, owner=None):
        """Create new database (requires superuser privileges)"""
        try:
            print(f"Creating database: {database_name}")
            
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
                    print(f"Database '{database_name}' already exists")
                    return 1
                
                # Create the database
                owner_clause = f' OWNER "{owner}"' if owner else ''
                create_sql = f'CREATE DATABASE "{database_name}"{owner_clause}'
                
                print(f"Creating database with SQL: {create_sql}")
                conn.execute(text(create_sql))
                
            print(f"✓ Database '{database_name}' created successfully!")
            
            # Reconnect to the new database
            new_db_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{database_name}"
            self.engine = create_engine(new_db_url)
            session_factory = sessionmaker(bind=self.engine)
            self.session = session_factory()
            
            return 0
            
        except Exception as e:
            print(f"Error creating database: {e}")
            return 1

    def recreate_database(self, database_name, owner=None):
        """Drop and recreate database"""
        try:
            print(f"Recreating database: {database_name}")
            print("=" * 50)
            
            # Step 1: Drop existing database
            print("STEP 1: Dropping existing database")
            drop_result = self.drop_database(database_name)
            
            # Continue even if drop fails (database might not exist)
            
            print("\nSTEP 2: Creating fresh database")
            create_result = self.create_database(database_name, owner)
            
            if create_result == 0:
                print(f"\n🎉 Database '{database_name}' recreated successfully!")
                return 0
            else:
                print(f"\n❌ Failed to recreate database '{database_name}'")
                return 1
                
        except Exception as e:
            print(f"Error during database recreation: {e}")
            return 1

    def create_initial_data(self, model_filter=None):
        """Create initial data for all models that support it"""
        try:
            print("Creating initial data from model methods...")
            print("=" * 60)
            
            models_with_data = self.discover_models_with_initial_data()
            
            if not models_with_data:
                print("No models found with create_initial_data method")
                return 0
            
            print(f"Found {len(models_with_data)} models with initial data methods:")
            for model_info in models_with_data:
                print(f"  - {model_info['class_name']} ({model_info['table_name']})")
            
            print("\nCreating initial data...")
            
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
                    print(f"\n  Processing {model_name} ({table_name})...")
                    
                    # Check if method expects session parameter
                    sig = inspect.signature(model_class.create_initial_data)
                    if 'session' in sig.parameters:
                        result = model_class.create_initial_data(session=self.session)
                    else:
                        result = model_class.create_initial_data()
                    
                    if result is False:
                        print(f"    ⚠️  {model_name}: create_initial_data returned False")
                    else:
                        print(f"    ✓ {model_name}: Initial data created")
                        success_count += 1
                    
                except Exception as e:
                    print(f"    ✗ {model_name}: Error - {e}")
                    error_count += 1
            
            # Commit all changes
            try:
                self.session.commit()
                print(f"\n✓ All changes committed to database")
            except Exception as e:
                print(f"\n✗ Error committing changes: {e}")
                self.session.rollback()
                return 1
            
            # Summary
            print(f"\nSummary:")
            print(f"  Success: {success_count} models")
            print(f"  Errors:  {error_count} models")
            
            if error_count == 0:
                print(f"\n🎉 All initial data created successfully!")
                return 0
            else:
                print(f"\n⚠️  Completed with {error_count} errors")
                return 1
                
        except Exception as e:
            print(f"Error creating initial data: {e}")
            self.session.rollback()
            return 1

    def list_models_with_initial_data(self):
        """List all models that have create_initial_data method"""
        try:
            models_with_data = self.discover_models_with_initial_data()
            
            if not models_with_data:
                print("No models found with create_initial_data method")
                return 0
            
            print("Models with Initial Data Support:")
            print("=" * 60)
            
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
            
            print(tabulate(rows, headers=headers, tablefmt='simple'))
            print(f"\nTotal: {len(models_with_data)} models support initial data creation")
            
            return 0
            
        except Exception as e:
            print(f"Error listing models: {e}")
            return 1

    def setup_complete_database(self):
        """Complete database setup including initial data"""
        try:
            print("Setting up complete database with initial data...")
            print("=" * 70)

            # Step 1: Create database users/roles
            print("STEP 1: Creating database users and roles")
            users_result = self.create_database_users()

            # Step 2: Create all tables
            print("\nSTEP 2: Creating database tables")
            tables_result = self.create_tables()

            if tables_result != 0:
                print("Failed to create tables, aborting setup")
                return 1

            # Step 3: Set up table permissions
            print("\nSTEP 3: Setting up table permissions")
            perms_result = self.setup_table_permissions()

            # Step 4: Create model initial data
            print("\nSTEP 4: Creating model initial data")
            initial_data_result = self.create_initial_data()

            if all(result == 0 for result in [tables_result, perms_result, initial_data_result]):
                print("\n🎉 Complete database setup with initial data finished successfully!")
                return 0
            else:
                print("\n⚠️  Setup completed with some warnings")
                return 1

        except Exception as e:
            print(f"Error during complete database setup: {e}")
            return 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Database Management CLI')
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
    try:
        cli = DatabaseCLI()
    except Exception as e:
        print(f"Error initializing: {e}")
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
        print("\nCancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())