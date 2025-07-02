#!/usr/bin/env python3
"""
Porter CLI / A Model importer/exporter in YAML CLI
Import/Export database models as YAML packages
"""

import argparse
import sys
from pathlib import Path

sys.path.append('/web/temuragi')

from app.base.cli_v1 import BaseCLI
from .exporter import ComponentExporter
from .importer import ComponentImporter
from .resolver import ImportDependencyResolver

CLI_DESCRIPTION = "Manages import and export of data"


class PorterCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        super().__init__(
            name="porter",
            log_file="logs/porter_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting Porter CLI initialization")

        try:
            # Initialize exporter and importer
            self.exporter = ComponentExporter(self)
            self.importer = ComponentImporter(self, self.get_model)

            # Initialize dependency resolver
            self.dependency_resolver = ImportDependencyResolver( self, self.get_model)

            self.log_info("Porter CLI initialized successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize Porter CLI: {e}")
            raise

    def import_yaml(self, file_path, dry_run=False, update_existing=False, 
                   replace_existing=False, match_field=None):
        """Import YAML file"""
        mode = "replace" if replace_existing else ("update" if update_existing else "create")
        self.log_info(f"Importing from {file_path} (mode={mode}, dry_run={dry_run})")

        try:
            return self.importer.import_yaml_file(
                file_path=file_path,
                dry_run=dry_run,
                update_existing=update_existing,
                replace_existing=replace_existing,
                match_field=match_field
            )

        except Exception as e:
            self.log_error(f"Error importing {file_path}: {e}")
            self.output_error(f"Import failed: {e}")
            return 1

    def import_directory(self, directory_path, dry_run=False, update_existing=False,
                        replace_existing=False, match_field=None):
        """Import all YAML files from directory in dependency order"""
        mode = "replace" if replace_existing else ("update" if update_existing else "create")
        self.log_info(f"Importing directory {directory_path} (mode={mode}, dry_run={dry_run})")

        try:
            # Get ordered files
            ordered_files = self.dependency_resolver.resolve_import_order(directory_path)
            
            if not ordered_files:
                self.output_error("No YAML files found in directory")
                return 1

            # Display import order
            self.output_info("Import order resolved:")
            for i, file_path in enumerate(ordered_files, 1):
                model_name = self.dependency_resolver.get_model_from_file(file_path)
                rel_path = file_path.relative_to(Path(directory_path))
                display_name = f"{model_name} ({rel_path})" if model_name else str(rel_path)
                self.output_info(f"  {i}. {display_name}")

            self.output_info(f"\nFound {len(ordered_files)} files to import")

            # Import each file in order - using same importer instance to preserve UUID mappings
            total_success = 0
            total_failed = 0

            for i, file_path in enumerate(ordered_files, 1):
                self.output_info(f"\n[{i}/{len(ordered_files)}] Processing: {file_path.name}")
                
                result = self.importer.import_yaml_file(
                    file_path=file_path,
                    dry_run=dry_run,
                    update_existing=update_existing,
                    replace_existing=replace_existing,
                    match_field=match_field
                )
                
                if result == 0:
                    total_success += 1
                else:
                    total_failed += 1

            # Summary
            if dry_run:
                self.output_info(f"\nDRY RUN SUMMARY: {total_success} files validated, {total_failed} failed")
            else:
                if total_failed == 0:
                    self.output_success(f"\nSUCCESS: Imported all {total_success} files")
                else:
                    self.output_warning(f"\nPARTIAL SUCCESS: Imported {total_success} files, {total_failed} failed")

            return 0 if total_failed == 0 else 1

        except Exception as e:
            self.log_error(f"Error importing directory {directory_path}: {e}")
            self.output_error(f"Directory import failed: {e}")
            return 1

    def explore_model(self, model_name):
        """Interactive explorer for a specific model"""
        self.log_info(f"Starting interactive exploration of {model_name}")

        try:
            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                self.output_error(f"Model '{model_name}' not found")
                return 1

            self.output_success(f"Exploring model: {model_name}")
            self.output_info(f"Table: {model_class.__tablename__}")

            # Show model info
            columns = [col.name for col in model_class.__table__.columns]
            self.output_info(f"Columns: {', '.join(columns)}")

            # Show dependencies if available
            depends_on = getattr(model_class, '__depends_on__', [])
            if depends_on:
                self.output_info(f"Depends on: {', '.join(depends_on)}")

            print()

            current_objects = None
            current_page = 0
            page_size = 10

            while True:
                try:
                    if current_objects is None:
                        # Load first page
                        current_objects = self._load_objects_page(model_class, current_page, page_size)

                    # Display current objects
                    if current_objects:
                        self._display_objects_table(current_objects, model_class, current_page, page_size)
                    else:
                        self.output_info("No objects found")

                    # Show menu
                    print()
                    self.output_info("Commands:")
                    print("  [n]ext page     [p]revious page    [s]earch")
                    print("  [e]xport <num>  [t]emplate <num>   [r]efresh")
                    print("  [q]uit")
                    print()

                    choice = input("porter> ").strip().lower()

                    if choice == 'q' or choice == 'quit':
                        break
                    elif choice == 'n' or choice == 'next':
                        current_page += 1
                        current_objects = self._load_objects_page(model_class, current_page, page_size)
                        if not current_objects:
                            current_page -= 1
                            self.output_warning("No more pages")
                    elif choice == 'p' or choice == 'prev':
                        if current_page > 0:
                            current_page -= 1
                            current_objects = self._load_objects_page(model_class, current_page, page_size)
                        else:
                            self.output_warning("Already on first page")
                    elif choice == 'r' or choice == 'refresh':
                        current_objects = self._load_objects_page(model_class, current_page, page_size)
                    elif choice == 's' or choice == 'search':
                        search_term = input("Search term: ").strip()
                        if search_term:
                            current_objects = self._search_objects(model_class, search_term, page_size)
                            current_page = 0
                    elif choice.startswith('e '):
                        # Export command
                        try:
                            num = int(choice.split()[1]) - 1
                            if 0 <= num < len(current_objects):
                                self._interactive_export(current_objects[num], model_name)
                            else:
                                self.output_error("Invalid object number")
                        except (ValueError, IndexError):
                            self.output_error("Usage: e <number>")
                    elif choice.startswith('t '):
                        # Template export command
                        try:
                            num = int(choice.split()[1]) - 1
                            if 0 <= num < len(current_objects):
                                self._interactive_template_export(current_objects[num], model_name)
                            else:
                                self.output_error("Invalid object number")
                        except (ValueError, IndexError):
                            self.output_error("Usage: t <number>")
                    else:
                        self.output_warning("Unknown command. Type 'q' to quit")

                except KeyboardInterrupt:
                    print()
                    self.output_info("Use 'q' to quit")
                except EOFError:
                    break

            self.output_info("Exiting explorer")
            return 0

        except Exception as e:
            self.log_error(f"Error in model explorer: {e}")
            self.output_error(f"Explorer failed: {e}")
            return 1

    def _load_objects_page(self, model_class, page, page_size):
        """Load a page of objects from the database"""
        offset = page * page_size
        return self.session.query(model_class).offset(offset).limit(page_size).all()

    def _search_objects(self, model_class, search_term, limit):
        """Search for objects matching term"""
        query = self.session.query(model_class)

        if hasattr(model_class, 'name'):
            query = query.filter(model_class.name.ilike(f'%{search_term}%'))
        elif hasattr(model_class, 'title'):
            query = query.filter(model_class.title.ilike(f'%{search_term}%'))
        else:
            # Search in string columns
            for column in model_class.__table__.columns:
                if 'varchar' in str(column.type).lower() or 'text' in str(column.type).lower():
                    query = query.filter(getattr(model_class, column.name).ilike(f'%{search_term}%'))
                    break

        return query.limit(limit).all()

    def _display_objects_table(self, objects, model_class, page, page_size):
        """Display objects in a table format"""
        if not objects:
            return

        headers = ['#', 'UUID (short)', 'Identifier', 'Status']
        rows = []

        for i, obj in enumerate(objects, 1):
            id_short = str(obj.id)[:8] + '...'
            identifier = self._get_object_identifier(obj)
            status = self._get_object_status(obj)
            rows.append([str(i), id_short, identifier, status])

        self.output_table(rows, headers=headers)

        start_num = page * page_size + 1
        end_num = start_num + len(objects) - 1
        self.output_info(f"Showing items {start_num}-{end_num} (page {page + 1})")

    def _get_object_identifier(self, obj):
        """Get the best identifier for an object"""
        for attr in ['name', 'title', 'email', 'username']:
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                if value:
                    return str(value)
        return 'N/A'

    def _get_object_status(self, obj):
        """Get the status of an object"""
        for attr in ['is_active', 'active', 'enabled', 'status']:
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                if isinstance(value, bool):
                    return 'Active' if value else 'Inactive'
                elif value:
                    return str(value)
        return 'Unknown'

    def _interactive_export(self, obj, model_name):
        """Interactive export process"""
        identifier = self._get_object_identifier(obj)
        default_filename = f"{model_name.lower()}_{identifier.replace(' ', '_')}.yaml"

        print()
        self.output_info(f"Exporting {model_name}: {identifier}")
        self.output_info(f"UUID: {obj.id}")

        filename = input(f"Output filename [{default_filename}]: ").strip()
        if not filename:
            filename = default_filename

        # Ensure .yaml extension
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename += '.yaml'

        try:
            result = self.exporter.export_model_object(
                model_object=obj,
                output_file_path=filename,
                template_mode=False
            )
            if result == 0:
                self.output_success(f"Exported to: {filename}")

        except Exception as e:
            self.output_error(f"Export failed: {e}")

    def _interactive_template_export(self, obj, model_name):
        """Interactive template export process"""
        identifier = self._get_object_identifier(obj)
        default_filename = f"{model_name.lower()}_template.yaml"

        print()
        self.output_info(f"Creating template from {model_name}: {identifier}")

        filename = input(f"Template filename [{default_filename}]: ").strip()
        if not filename:
            filename = default_filename

        # Ensure .yaml extension
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename += '.yaml'

        try:
            result = self.exporter.export_model_object(
                model_object=obj,
                output_file_path=filename,
                template_mode=True,
                header_title=f"{model_name} Template",
                header_description="Template file - edit values before importing"
            )
            if result == 0:
                self.output_success(f"Template created: {filename}")

        except Exception as e:
            self.output_error(f"Template creation failed: {e}")

    def export_model(self, model_name, object_id, output_file, template_mode=False,
                    foreign_key_mappings=None, header_title=None, header_description=None):
        """Export a model object to YAML"""
        self.log_info(f"Exporting {model_name} object {object_id} to {output_file}")

        try:
            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                self.output_error(f"Model '{model_name}' not found")
                return 1

            # Find the object
            if len(object_id) == 36 and '-' in object_id:
                # UUID format
                model_object = self.session.query(model_class).filter(
                    model_class.id == object_id
                ).first()
            else:
                # Try to find by name or other identifier
                if hasattr(model_class, 'name'):
                    model_object = self.session.query(model_class).filter(
                        model_class.name == object_id
                    ).first()
                else:
                    self.output_error(f"Model {model_name} has no 'name' field. Use UUID instead.")
                    return 1

            if not model_object:
                self.output_error(f"Object not found: {object_id}")
                return 1

            # Export the object
            return self.exporter.export_model_object(
                model_object=model_object,
                output_file_path=output_file,
                foreign_key_mappings=foreign_key_mappings,
                header_title=header_title,
                header_description=header_description,
                template_mode=template_mode
            )

        except Exception as e:
            self.log_error(f"Error exporting {model_name}: {e}")
            self.output_error(f"Export failed: {e}")
            return 1

    def analyze_dependencies(self, directory_path):
        """Analyze dependencies in a directory of YAML files"""
        self.log_info(f"Analyzing dependencies in {directory_path}")

        try:
            return self.dependency_resolver.analyze_directory_dependencies(directory_path)
        except Exception as e:
            self.log_error(f"Error analyzing dependencies in {directory_path}: {e}")
            self.output_error(f"Dependency analysis failed: {e}")
            return 1

    def resolve_import_order(self, directory_path):
        """Show the resolved import order for directory"""
        self.log_info(f"Resolving import order for {directory_path}")

        try:
            ordered_files = self.dependency_resolver.resolve_import_order(directory_path)

            if not ordered_files:
                self.output_error("No files found or dependency resolution failed")
                return 1

            self.output_success(f"Import order for {len(ordered_files)} files:")

            for i, file_path in enumerate(ordered_files, 1):
                model_name = self.dependency_resolver.get_model_from_file(file_path)
                rel_path = file_path.relative_to(Path(directory_path))
                display_name = f"{model_name} ({rel_path})" if model_name else str(rel_path)
                self.output_info(f"  {i}. {display_name}")

            return 0

        except Exception as e:
            self.log_error(f"Error resolving import order: {e}")
            self.output_error(f"Order resolution failed: {e}")
            return 1

    def list_models(self):
        """List available models"""
        self.log_info("Listing available models")

        try:
            from app.register.database import list_models
            models = list_models()

            if not models:
                self.output_info("No models found")
                return 0

            # Get additional info for each model
            headers = ['Model Name', 'Table Name', 'Module', 'Dependencies']
            rows = []

            for model_name in sorted(models):
                model_class = self.get_model(model_name)
                if model_class and hasattr(model_class, '__tablename__'):
                    # Only show actual model classes, not table aliases
                    if model_name == model_class.__name__:
                        table_name = model_class.__tablename__
                        module = model_class.__module__.split('.')[-1]
                        depends_on = getattr(model_class, '__depends_on__', [])
                        deps_str = ', '.join(depends_on) if depends_on else 'None'
                        rows.append([model_name, table_name, module, deps_str])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing models: {e}")
            self.output_error(f"Failed to list models: {e}")
            return 1

    def search_objects(self, model_name, search_term=None, limit=10):
        """Search for objects in a model"""
        self.log_info(f"Searching {model_name} for '{search_term}' (limit={limit})")

        try:
            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                self.output_error(f"Model '{model_name}' not found")
                return 1

            # Build query
            query = self.session.query(model_class)

            if search_term:
                # Search in name field if available
                if hasattr(model_class, 'name'):
                    query = query.filter(model_class.name.ilike(f'%{search_term}%'))
                elif hasattr(model_class, 'title'):
                    query = query.filter(model_class.title.ilike(f'%{search_term}%'))
                else:
                    self.output_warning(f"Model {model_name} has no searchable name/title field")

            # Limit results
            objects = query.limit(limit).all()

            if not objects:
                self.output_info(f"No {model_name} objects found")
                return 0

            # Display results
            headers = ['UUID', 'Identifier', 'Active']
            rows = []

            for obj in objects:
                id_short = str(obj.id)[:8] + '...'
                identifier = getattr(obj, 'name', getattr(obj, 'title', 'N/A'))
                active = 'Yes' if getattr(obj, 'is_active', True) else 'No'
                rows.append([id_short, identifier, active])

            self.output_table(rows, headers=headers)
            self.output_info(f"Found {len(objects)} objects (limited to {limit})")
            return 0

        except Exception as e:
            self.log_error(f"Error searching {model_name}: {e}")
            self.output_error(f"Search failed: {e}")
            return 1

    def validate_yaml(self, file_path):
        """Validate YAML file structure without importing"""
        self.log_info(f"Validating YAML file: {file_path}")
        return self.import_yaml(file_path, dry_run=True, update_existing=False)

    def generate_template(self, model_name, output_file):
        """Generate a template YAML file for a model"""
        self.log_info(f"Generating template for {model_name}")

        try:
            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                self.output_error(f"Model '{model_name}' not found")
                return 1

            # Create a dummy object with default values
            dummy_data = {}
            for column in model_class.__table__.columns:
                if column.name in self.exporter.auto_generated_fields:
                    continue

                # Generate example values based on column type
                if column.name == 'name':
                    dummy_data[column.name] = "example_name"
                elif column.name == 'title':
                    dummy_data[column.name] = "Example Title"
                elif column.name == 'description':
                    dummy_data[column.name] = "Example description"
                elif 'email' in column.name:
                    dummy_data[column.name] = "user@example.com"
                elif column.name == 'is_active':
                    dummy_data[column.name] = True
                else:
                    # Generic example based on type
                    column_type = str(column.type).lower()
                    if 'varchar' in column_type or 'text' in column_type:
                        dummy_data[column.name] = "example_value"
                    elif 'integer' in column_type:
                        dummy_data[column.name] = 1
                    elif 'boolean' in column_type:
                        dummy_data[column.name] = True
                    elif 'decimal' in column_type or 'numeric' in column_type:
                        dummy_data[column.name] = 0.0
                    else:
                        dummy_data[column.name] = None

            # Create dummy object
            dummy_object = model_class(**dummy_data)

            # Export as template
            return self.exporter.export_model_object(
                model_object=dummy_object,
                output_file_path=output_file,
                template_mode=True,
                header_title=f"{model_name} Template",
                header_description="Template file - edit values before importing"
            )

        except Exception as e:
            self.log_error(f"Error generating template for {model_name}: {e}")
            self.output_error(f"Template generation failed: {e}")
            return 1

    def export_all(self, model_name, output_file, template_mode=False,
                    filter_field=None, filter_value=None, order_by=None,
                    limit=None, header_title=None, header_description=None):
            """Export all model objects to a single YAML file"""
            self.log_info(f"Exporting all {model_name} objects to {output_file}")

            try:
                # Get model class
                model_class = self.get_model(model_name)
                if not model_class:
                    self.output_error(f"Model '{model_name}' not found")
                    return 1

                # Build filter conditions if provided
                filter_conditions = None
                if filter_field and filter_value:
                    filter_conditions = {filter_field: filter_value}
                    self.log_info(f"Applying filter: {filter_field}={filter_value}")

                # Export all objects
                return self.exporter.export_all_model_objects(
                    model_class=model_class,
                    output_file_path=output_file,
                    header_title=header_title,
                    header_description=header_description,
                    template_mode=template_mode,
                    filter_conditions=filter_conditions,
                    order_by=order_by,
                    limit=limit
                )

            except Exception as e:
                self.log_error(f"Error exporting all {model_name}: {e}")
                self.output_error(f"Export failed: {e}")
                return 1

def main():
    """Entry point for Porter CLI"""
    parser = argparse.ArgumentParser(description='Porter Component Import/Export CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'],
                       help='Override table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Explore command
    explore_parser = subparsers.add_parser('explore', help='Interactive model explorer')
    explore_parser.add_argument('model', help='Model name to explore')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export model object to YAML')
    export_parser.add_argument('model', help='Model name')
    export_parser.add_argument('object_id', help='Object UUID or name')
    export_parser.add_argument('output', help='Output YAML file path')
    export_parser.add_argument('--template', action='store_true', help='Generate as template')
    export_parser.add_argument('--title', help='Custom header title')
    export_parser.add_argument('--description', help='Custom header description')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import YAML file')
    import_parser.add_argument('file', help='YAML file path')
    import_parser.add_argument('--dry-run', action='store_true', help='Validate without importing')
    import_parser.add_argument('--update', action='store_true', help='Update existing records by UUID')
    import_parser.add_argument('--replace', action='store_true', help='Replace existing records by name')
    import_parser.add_argument('--match-field', help='Field to match for replace (default: auto-detect)')

    # Import directory command
    import_dir_parser = subparsers.add_parser('import-dir', help='Import all YAML files from directory')
    import_dir_parser.add_argument('directory', help='Directory containing YAML files')
    import_dir_parser.add_argument('--dry-run', action='store_true', help='Validate without importing')
    import_dir_parser.add_argument('--update', action='store_true', help='Update existing records by UUID')
    import_dir_parser.add_argument('--replace', action='store_true', help='Replace existing records by name')
    import_dir_parser.add_argument('--match-field', help='Field to match for replace (default: auto-detect)')

    # Analyze dependencies command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze dependencies in directory')
    analyze_parser.add_argument('directory', help='Directory containing YAML files')

    # Resolve order command
    order_parser = subparsers.add_parser('order', help='Show resolved import order')
    order_parser.add_argument('directory', help='Directory containing YAML files')

    # List command
    list_parser = subparsers.add_parser('list', help='List available models')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for objects')
    search_parser.add_argument('model', help='Model name')
    search_parser.add_argument('--term', help='Search term')
    search_parser.add_argument('--limit', type=int, default=10, help='Limit results')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate YAML file')
    validate_parser.add_argument('file', help='YAML file path')

    # Template command
    template_parser = subparsers.add_parser('template', help='Generate template YAML')
    template_parser.add_argument('model', help='Model name')
    template_parser.add_argument('output', help='Output template file path')

    # Export all command
    export_all_parser = subparsers.add_parser('export-all', help='Export all model objects to single YAML')
    export_all_parser.add_argument('model', help='Model name')
    export_all_parser.add_argument('output', help='Output YAML file path')
    export_all_parser.add_argument('--template', action='store_true', help='Generate as template')
    export_all_parser.add_argument('--filter-field', help='Field name to filter by')
    export_all_parser.add_argument('--filter-value', help='Value to filter by')
    export_all_parser.add_argument('--order-by', help='Field to order results by')
    export_all_parser.add_argument('--limit', type=int, help='Limit number of records')
    export_all_parser.add_argument('--title', help='Custom header title')
    export_all_parser.add_argument('--description', help='Custom header description')
    
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = PorterCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute command
    try:
        if args.command == 'explore':
            return cli.explore_model(args.model)

        elif args.command == 'export':
            return cli.export_model(
                args.model, args.object_id, args.output,
                template_mode=args.template,
                header_title=args.title,
                header_description=args.description
            )

        elif args.command == 'import':
            # Validate mutually exclusive options
            if args.update and args.replace:
                cli.output_error("Cannot use both --update and --replace. Choose one.")
                return 1
                
            return cli.import_yaml(
                args.file, 
                dry_run=args.dry_run, 
                update_existing=args.update,
                replace_existing=args.replace,
                match_field=args.match_field
            )

        elif args.command == 'import-dir':
            # Validate mutually exclusive options
            if args.update and args.replace:
                cli.output_error("Cannot use both --update and --replace. Choose one.")
                return 1
                
            return cli.import_directory(
                args.directory, 
                dry_run=args.dry_run, 
                update_existing=args.update,
                replace_existing=args.replace,
                match_field=args.match_field
            )

        elif args.command == 'analyze':
            return cli.analyze_dependencies(args.directory)

        elif args.command == 'order':
            return cli.resolve_import_order(args.directory)

        elif args.command == 'list':
            return cli.list_models()

        elif args.command == 'search':
            return cli.search_objects(args.model, args.term, args.limit)

        elif args.command == 'validate':
            return cli.validate_yaml(args.file)

        elif args.command == 'template':
            return cli.generate_template(args.model, args.output)
            
        elif args.command == 'export-all':
            return cli.export_all(
                args.model,
                args.output,
                template_mode=args.template,
                filter_field=args.filter_field,
                filter_value=args.filter_value,
                order_by=args.order_by,
                limit=args.limit,
                header_title=args.title,
                header_description=args.description
            )
            
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