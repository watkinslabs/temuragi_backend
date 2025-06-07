#!/usr/bin/env python3
"""
YAML Component CLI
Import/Export database models as YAML packages
"""

import argparse
import sys
import os
from pathlib import Path

# Add your app path to import the model and config
sys.path.append('/web/temuragi')
from app.register_db import register_models_for_cli, get_model
from app.base_cli import BaseCLI
from app.utils.component_export import ComponentExporter
from app.utils.component_import import ComponentImporter


class YamlCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        super().__init__(
            name="yaml",
            log_file="logs/yaml_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting YAML CLI initialization")

        try:
            # Initialize exporter and importer
            self.exporter = ComponentExporter(self.session, self)
            self.importer = ComponentImporter(self.session, self, self.get_model)
            
            self.log_info("YAML CLI initialized successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize YAML CLI: {e}")
            raise

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
                    model_class.uuid == object_id
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

    def import_yaml(self, file_path, dry_run=False, update_existing=False):
        """Import YAML file"""
        self.log_info(f"Importing from {file_path} (dry_run={dry_run}, update={update_existing})")

        try:
            return self.importer.import_yaml_file(
                file_path=file_path,
                dry_run=dry_run,
                update_existing=update_existing
            )

        except Exception as e:
            self.log_error(f"Error importing {file_path}: {e}")
            self.output_error(f"Import failed: {e}")
            return 1

    def list_models(self):
        """List available models"""
        self.log_info("Listing available models")

        try:
            from app.register_db import list_models
            models = list_models()

            if not models:
                self.output_info("No models found")
                return 0

            # Get additional info for each model
            headers = ['Model Name', 'Table Name', 'Module']
            rows = []

            for model_name in sorted(models):
                model_class = self.get_model(model_name)
                if model_class and hasattr(model_class, '__tablename__'):
                    # Only show actual model classes, not table aliases
                    if model_name == model_class.__name__:
                        table_name = model_class.__tablename__
                        module = model_class.__module__.split('.')[-1]
                        rows.append([model_name, table_name, module])

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
                uuid_short = str(obj.uuid)[:8] + '...'
                identifier = getattr(obj, 'name', getattr(obj, 'title', 'N/A'))
                active = 'Yes' if getattr(obj, 'is_active', True) else 'No'
                rows.append([uuid_short, identifier, active])

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


def main():
    """Entry point for YAML CLI"""
    parser = argparse.ArgumentParser(description='YAML Component Import/Export CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'],
                       help='Override table format')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

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
    import_parser.add_argument('--update', action='store_true', help='Update existing records')

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = YamlCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute command
    try:
        if args.command == 'export':
            return cli.export_model(
                args.model, args.object_id, args.output,
                template_mode=args.template,
                header_title=args.title,
                header_description=args.description
            )

        elif args.command == 'import':
            return cli.import_yaml(args.file, args.dry_run, args.update)

        elif args.command == 'list':
            return cli.list_models()

        elif args.command == 'search':
            return cli.search_objects(args.model, args.term, args.limit)

        elif args.command == 'validate':
            return cli.validate_yaml(args.file)

        elif args.command == 'template':
            return cli.generate_template(args.model, args.output)

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