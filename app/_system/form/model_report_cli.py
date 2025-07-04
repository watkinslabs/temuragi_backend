#!/usr/bin/env python3
"""
Model Report Generator CLI - Generate reports from SQLAlchemy models
Creates comprehensive reports by introspecting model structure
"""

import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
import importlib
import inspect
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import sqltypes

# Add your app path to import the model and config
sys.path.append('/web/ahoy2.radiatorusa.com')

from app.base.cli_v1 import BaseCLI

CLI_DESCRIPTION = "Generate reports from SQLAlchemy models"


class ModelReportCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection"""
        super().__init__(
            name="model_report_generator",
            log_file="logs/model_report_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting model report generator CLI")

        try:
            from app.classes import ReportService
            from app.models import Connection, DataType, VariableType
            
            # Try to import Model to check if it's available
            try:
                from app.models import Model
                self.model_available = True
                self.log_info("Model class is available")
            except ImportError:
                self.model_available = False
                self.log_warning("Model class not available - model associations will be skipped")

            self.service = ReportService(logger=self.logger)
            self.log_info("Report service initialized successfully")
            
            # Cache data types and variable types
            self.data_types = {dt.name: dt for dt in self.service.list_data_types()}
            self.variable_types = {vt.name: vt for vt in self.service.list_variable_types()}
            
        except Exception as e:
            self.log_error(f"Failed to initialize: {e}")
            raise

    def get_or_create_model_record(self, model_name: str, table_name: str) -> Optional['Model']:
        """Get or create a Model record for the given model"""
        if not self.model_available:
            self.log_warning("Model class not available - skipping model association")
            return None
            
        try:
            from app.models import Model
            
            # Check if Model record exists
            model_record = self.session.query(Model).filter_by(name=model_name).first()
            
            if not model_record:
                self.log_info(f"Creating Model record for {model_name}")
                # Create a new Model record
                model_record = Model(
                    name=model_name,
                    table_name=table_name,
                    display_name=model_name.replace('_', ' ').title(),
                    description=f"Auto-generated model for {table_name} table",
                    is_active=True
                )
                self.session.add(model_record)
                self.session.commit()
                self.log_info(f"Created Model record: {model_record.id}")
            else:
                self.log_info(f"Found existing Model record for {model_name}: {model_record.id}")
            
            return model_record
            
        except ImportError as e:
            self.log_warning(f"Model class not available: {e}")
            self.output_warning("Model table not available - proceeding without model association")
            return None
        except Exception as e:
            self.log_error(f"Error with Model record: {e}")
            self.output_warning(f"Could not create Model record: {e}")
            # Continue without model association if Model table doesn't exist
            return None

    def get_sqlalchemy_to_report_type_mapping(self):
        """Map SQLAlchemy column types to report data types"""
        return {
            sqltypes.String: 'string',
            sqltypes.Text: 'string',
            sqltypes.Integer: 'integer',
            sqltypes.BigInteger: 'integer',
            sqltypes.SmallInteger: 'integer',
            sqltypes.Float: 'number',
            sqltypes.Numeric: 'decimal',
            sqltypes.DECIMAL: 'decimal',
            sqltypes.Boolean: 'boolean',
            sqltypes.Date: 'date',
            sqltypes.DateTime: 'datetime',
            sqltypes.Time: 'time',
            sqltypes.JSON: 'json',
            sqltypes.ARRAY: 'array',
            # PostgreSQL specific
            'UUID': 'id',
            'JSONB': 'json',
            'INET': 'ip_address',
            'MACADDR': 'string',
            'MONEY': 'money',
            # Common encrypted/binary types
            sqltypes.LargeBinary: 'string',
            sqltypes.BINARY: 'string',
            sqltypes.VARBINARY: 'string',
        }

    def get_column_data_type(self, column):
        """Determine report data type from SQLAlchemy column"""
        type_mapping = self.get_sqlalchemy_to_report_type_mapping()
        
        col_type = type(column.type)
        
        # Check direct mapping
        for sql_type, report_type in type_mapping.items():
            if isinstance(sql_type, str):
                if sql_type in str(col_type):
                    return report_type
            elif isinstance(column.type, sql_type):
                return report_type
        
        # Special cases
        if 'UUID' in str(col_type):
            return 'id'
        elif 'JSONB' in str(col_type):
            return 'json'
        elif 'Encrypted' in str(col_type):
            return 'string'
        elif 'password' in column.name.lower():
            return 'string'
        elif 'email' in column.name.lower():
            return 'email'
        elif 'url' in column.name.lower() or 'link' in column.name.lower():
            return 'url'
        elif 'color' in column.name.lower():
            return 'color'
        elif 'html' in column.name.lower():
            return 'html'
        elif 'markdown' in column.name.lower() or 'md' in column.name.lower():
            return 'markdown'
        
        # Default to string
        return 'string'

    def import_model(self, model_name: str):
        """Import a model from app.models"""
        try:
            # Try to import from app.models
            models_module = importlib.import_module('app.models')
            
            # Get the model class
            if hasattr(models_module, model_name):
                return getattr(models_module, model_name)
            
            # Try with different casing
            for attr_name in dir(models_module):
                if attr_name.lower() == model_name.lower():
                    return getattr(models_module, attr_name)
            
            raise ValueError(f"Model '{model_name}' not found in app.models")
            
        except Exception as e:
            self.log_error(f"Failed to import model {model_name}: {e}")
            raise

    def generate_query_for_model(self, model_class, include_relationships: bool = True,
                            relationship_depth: int = 1, is_model: bool = True) -> Dict[str, Any]:
        """Generate SQL query and metadata for a model"""
        
        # Get table name and columns
        mapper = class_mapper(model_class)
        table_name = mapper.mapped_table.name
        
        # Get column to attribute mapping if this is a model-based report
        column_to_attr = self.get_column_to_attribute_map(mapper) if is_model else {}
        
        # Build column list and metadata
        columns = []
        column_metadata = []
        
        # Process regular columns
        for column in mapper.mapped_table.columns:
            col_name = column.name
            
            # Use attribute name if this is a model-based report and mapping exists
            attr_name = column_to_attr.get(col_name, col_name) if is_model else col_name
            
            columns.append(f"t.{col_name}")
            
            # Determine data type
            data_type = self.get_column_data_type(column)
            
            # Create column metadata with attribute name
            col_meta = {
                'name': attr_name,  # Use attribute name here
                'display_name': attr_name.replace('_', ' ').title(),
                'data_type': data_type,
                'is_primary_key': bool(column.primary_key),
                'is_foreign_key': bool(column.foreign_keys),
                'is_nullable': bool(column.nullable),
                'is_unique': bool(column.unique or column.primary_key),
            }
            
            # Special handling for certain columns
            if attr_name in ['password', 'password_hash', 'secret', 'token']:
                col_meta['is_visible'] = False
                col_meta['is_searchable'] = False
            elif column.primary_key:
                col_meta['is_searchable'] = False
            
            column_metadata.append(col_meta)
        
        # Build base query
        query = f"SELECT\n    " + ",\n    ".join(columns) + f"\nFROM {table_name} t"
        
        # Handle relationships if requested
        joins = []
        relationship_columns = []
        
        if include_relationships and relationship_depth > 0:
            try:
                for rel in mapper.relationships:
                    if rel.direction.name == 'MANYTOONE':  # Only handle many-to-one for now
                        try:
                            rel_mapper = rel.mapper
                            rel_table = rel_mapper.mapped_table.name
                            rel_alias = rel.key[:3]  # Short alias
                            
                            # Find the foreign key column
                            local_columns = list(rel.local_columns) if hasattr(rel, 'local_columns') else []
                            fk_col = local_columns[0] if local_columns else None
                            
                            if fk_col:
                                # Add join
                                joins.append(f"LEFT JOIN {rel_table} {rel_alias} ON t.{fk_col.name} = {rel_alias}.id")
                                
                                # Add display column from related table (usually 'name' or 'display')
                                display_cols = ['name', 'display', 'title', 'display_name']
                                rel_columns = [c.name for c in rel_mapper.mapped_table.columns]
                                
                                for display_col in display_cols:
                                    if display_col in rel_columns:
                                        relationship_columns.append({
                                            'name': f"{rel.key}_{display_col}",
                                            'display_name': f"{rel.key.replace('_', ' ').title()} {display_col.title()}",
                                            'data_type': 'string',
                                            'is_relationship': True,
                                            'relationship_name': rel.key,
                                            'query_expression': f"{rel_alias}.{display_col}",
                                            'is_searchable': True,
                                            'is_sortable': True,
                                            'is_visible': True
                                        })
                                        columns.append(f"{rel_alias}.{display_col} as {rel.key}_{display_col}")
                                        break
                        except Exception as e:
                            self.log_warning(f"Skipping relationship {rel.key}: {e}")
                            continue
            except Exception as e:
                self.log_warning(f"Error processing relationships: {e}")
                # Continue without relationships
        
        # Add joins to query
        if joins:
            query = f"SELECT\n    " + ",\n    ".join(columns) + f"\nFROM {table_name} t\n" + "\n".join(joins)
        
        # Add relationship columns to metadata
        column_metadata.extend(relationship_columns)
        
        # Add default WHERE and ORDER BY placeholders
        query += "\nWHERE 1=1"
        
        # Find a good default order column
        order_columns = []
        for col in mapper.mapped_table.columns:
            if col.name == 'created_at':
                order_columns.append(f"t.{col.name} DESC")
                break
            elif col.name == 'name':
                order_columns.append(f"t.{col.name} ASC")
                break
            elif col.name == 'id' and not order_columns:
                order_columns.append(f"t.{col.name} DESC")
        
        if order_columns:
            query += f"\nORDER BY {', '.join(order_columns)}"
        
        return {
            'query': query,
            'columns': column_metadata,
            'table_name': table_name,
            'has_relationships': len(joins) > 0
        }

    def generate_report_from_model(self, model_name: str, connection_name: str,
                                 report_slug: str, report_name: str,
                                 report_description: str,
                                 category: Optional[str] = None,
                                 include_relationships: bool = True,
                                 auto_publish: bool = False,
                                 is_system: bool = False,
                                 is_model: bool = True,  # Default to True for model-generated reports
                                 associate_with_model: bool = True) -> Dict[str, Any]:
        """Generate a complete report from a model with explicit metadata"""
        
        self.log_info(f"Generating report for model: {model_name}")
        self.log_info(f"  Slug: {report_slug}")
        self.log_info(f"  Name: {report_name}")
        self.log_info(f"  Description: {report_description}")
        self.log_info(f"  System: {is_system}")
        self.log_info(f"  Is Model: {is_model}")
        
        try:
            # Import the model
            model_class = self.import_model(model_name)
            
            # Get connection
            from app.models import Connection
            connection = self.session.query(Connection).filter_by(name=connection_name).first()
            if not connection:
                raise ValueError(f"Connection '{connection_name}' not found")
            
            # Generate query and metadata
            query_data = self.generate_query_for_model(model_class, include_relationships, is_model=is_model)

            
            # Get or create Model record if requested
            model_id = None
            if associate_with_model:
                self.log_info(f"Attempting to associate with Model record for {model_name}")
                model_record = self.get_or_create_model_record(model_name, query_data['table_name'])
                if model_record:
                    model_id = model_record.id
                    self.log_info(f"Successfully associated with Model record: {model_id}")
                    self.output_info(f"Model association: {model_name} (ID: {model_id})")
                else:
                    self.log_warning(f"No Model record created/found for {model_name}")
                    self.output_warning("Proceeding without Model association")
            else:
                self.log_info("Skipping Model association as requested")
            
            # Check if report already exists
            existing = self.service.get_report(report_slug)
            if existing:
                self.output_warning(f"Report with slug '{report_slug}' already exists")
                return {'exists': True, 'report': existing}
            
            # Create the report with provided metadata
            self.log_info(f"Creating report with model_id: {model_id}")
            report = self.service.create_report(
                slug=report_slug,
                name=report_name,
                display=report_name,  # Use same as name
                query=query_data['query'],
                connection_id=connection.id,
                model_id=model_id,  # Associate with Model record
                category=category or 'Model Reports',
                description=report_description,
                is_ajax=True,
                is_searchable=True,
                is_download_csv=True,
                is_download_xlsx=True,
                is_model=is_model,
                is_published=auto_publish,
                is_system=is_system,
                tags=[model_name, query_data['table_name']]
            )
            
            # Verify model_id was saved
            if model_id and report.model_id != model_id:
                self.log_error(f"Model ID mismatch: expected {model_id}, got {report.model_id}")
            elif model_id:
                self.log_info(f"Report created with model_id: {report.model_id}")
            
            # Add columns
            for col_data in query_data['columns']:
                data_type = self.data_types.get(col_data['data_type'])
                if not data_type:
                    self.log_warning(f"Unknown data type: {col_data['data_type']}, using string")
                    data_type = self.data_types.get('string')
                
                # Configure column based on type and metadata
                column_config = {
                    'is_searchable': col_data.get('is_searchable', True),
                    'is_sortable': True,
                    'is_visible': col_data.get('is_visible', True),
                }
                
                # Add format strings for specific types
                if col_data['data_type'] == 'money':
                    column_config['format_string'] = '${:,.2f}'
                elif col_data['data_type'] == 'percentage':
                    column_config['format_string'] = '{:.1%}'
                elif col_data['data_type'] in ['date', 'datetime']:
                    column_config['alignment'] = 'center'
                elif col_data['data_type'] in ['integer', 'number', 'decimal']:
                    column_config['alignment'] = 'right'
                
                self.service.add_report_column(
                    report_id=report.id,
                    name=col_data['name'],
                    display_name=col_data['display_name'],
                    data_type_id=data_type.id,
                    **column_config
                )
            
            # Add standard filter variables
            standard_variables = [
                {
                    'name': 'search_term',
                    'display_name': 'Search',
                    'type': 'text',
                    'placeholder': 'Search all columns...',
                    'required': False
                },
                {
                    'name': 'limit',
                    'display_name': 'Results Limit',
                    'type': 'number',
                    'default': '1000',
                    'required': False
                }
            ]
            
            # Add date range filters if model has date columns
            has_created_at = any(col['name'] == 'created_at' for col in query_data['columns'])
            if has_created_at:
                standard_variables.extend([
                    {
                        'name': 'date_from',
                        'display_name': 'Date From',
                        'type': 'date',
                        'required': False
                    },
                    {
                        'name': 'date_to',
                        'display_name': 'Date To',
                        'type': 'date',
                        'required': False
                    }
                ])
            
            # Add variables
            for var_data in standard_variables:
                var_type = self.variable_types.get(var_data['type'])
                if var_type:
                    self.service.add_report_variable(
                        report_id=report.id,
                        name=var_data['name'],
                        display_name=var_data['display_name'],
                        variable_type_id=var_type.id,
                        default_value=var_data.get('default'),
                        placeholder=var_data.get('placeholder'),
                        is_required=var_data.get('required', False)
                    )
            
            return {
                'success': True,
                'report': report,
                'model_id': model_id,
                'columns_created': len(query_data['columns']),
                'variables_created': len(standard_variables),
                'has_relationships': query_data['has_relationships']
            }
            
        except Exception as e:
            self.log_error(f"Failed to generate report for {model_name}: {e}")
            raise

    def list_available_models(self, show_existing_reports: bool = False):
        """List all available models that can be used for report generation"""
        
        self.output_info("Discovering available models...")
        
        try:
            models_module = importlib.import_module('app.models')
            
            # Get existing model reports if requested
            existing_model_reports = {}
            if show_existing_reports:
                from app.models import Report
                reports = self.session.query(Report).filter(
                    Report.is_model == True
                ).all()
                for report in reports:
                    # Try to extract model name from tags
                    if report.tags:
                        for tag in report.tags:
                            if hasattr(models_module, tag):
                                existing_model_reports[tag] = report.slug
                                break
            
            # Get all classes from the module
            models = []
            for name, obj in inspect.getmembers(models_module):
                if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
                    # Check if it's a SQLAlchemy model
                    try:
                        mapper = class_mapper(obj)
                        table_name = mapper.mapped_table.name
                        column_count = len(mapper.mapped_table.columns)
                        relationship_count = len(mapper.relationships)
                        
                        model_info = {
                            'name': name,
                            'table': table_name,
                            'columns': column_count,
                            'relationships': relationship_count
                        }
                        
                        if show_existing_reports:
                            model_info['report_slug'] = existing_model_reports.get(name, '')
                        
                        models.append(model_info)
                    except:
                        # Not a mapped class
                        continue
            
            if not models:
                self.output_warning("No models found")
                return 0
            
            # Sort by name
            models.sort(key=lambda x: x['name'])
            
            # Display table
            if show_existing_reports:
                headers = ['Model Name', 'Table Name', 'Columns', 'Relationships', 'Report Slug']
            else:
                headers = ['Model Name', 'Table Name', 'Columns', 'Relationships']
            
            rows = []
            
            for model in models:
                row = [
                    model['name'],
                    model['table'],
                    model['columns'],
                    model['relationships']
                ]
                
                if show_existing_reports:
                    if model.get('report_slug'):
                        row.append(f"{self.icon('check')} {model['report_slug']}")
                    else:
                        row.append('')
                
                rows.append(row)
            
            self.output_info(f"Available Models ({len(models)} total):")
            self.output_table(rows, headers=headers)
            
            if show_existing_reports:
                existing_count = sum(1 for m in models if m.get('report_slug'))
                self.output_info(f"\nExisting model reports: {existing_count}/{len(models)}")
            
            return 0
            
        except Exception as e:
            self.log_error(f"Error listing models: {e}")
            self.output_error(f"Error listing models: {e}")
            return 1

    def analyze_model(self, model_name: str):
        """Analyze a model and show what report would be generated"""
        
        self.output_info(f"Analyzing model: {model_name}")
        
        try:
            model_class = self.import_model(model_name)
            query_data = self.generate_query_for_model(model_class)
            
            # Check if Model record exists
            from app.models import Model
            model_record = self.session.query(Model).filter_by(name=model_name).first()
            
            # Basic info
            self.output_info(f"\nModel: {model_name}")
            self.output_info(f"Table: {query_data['table_name']}")
            self.output_info(f"Columns: {len(query_data['columns'])}")
            self.output_info(f"Has Relationships: {'Yes' if query_data['has_relationships'] else 'No'}")
            if model_record:
                self.output_info(f"Model Record: {self.icon('check')} Exists (ID: {model_record.id})")
            else:
                self.output_info(f"Model Record: {self.icon('cross')} Not found (will be created)")
            
            # Check for existing reports
            from app.models import Report
            existing_reports = self.session.query(Report).filter(
                Report.tags.contains([model_name])
            ).all()
            
            if existing_reports:
                self.output_warning(f"\nExisting reports for this model:")
                for report in existing_reports:
                    self.output_info(f"  - {report.slug}: {report.name}")
            
            # Show columns
            self.output_info("\nColumns that would be created:")
            headers = ['Column Name', 'Display Name', 'Data Type', 'Special']
            rows = []
            
            for col in query_data['columns']:
                special = []
                if col.get('is_primary_key'):
                    special.append('PK')
                if col.get('is_foreign_key'):
                    special.append('FK')
                if col.get('is_relationship'):
                    special.append('REL')
                if not col.get('is_visible', True):
                    special.append('HIDDEN')
                
                rows.append([
                    col['name'],
                    col['display_name'],
                    col['data_type'],
                    ', '.join(special) if special else ''
                ])
            
            self.output_table(rows, headers=headers)
            
            # Show generated query
            if self.verbose:
                self.output_info("\nGenerated Query:")
                self.output_info("-" * 60)
                self.output(query_data['query'])
            
            return 0
            
        except Exception as e:
            self.log_error(f"Error analyzing model: {e}")
            self.output_error(f"Error analyzing model: {e}")
            return 1

    def get_column_to_attribute_map(self, mapper):
        """Map database column names to class attribute names"""
        column_to_attr = {}
        
        # Iterate through all properties in the mapper
        for prop in mapper.iterate_properties:
            if hasattr(prop, 'columns'):
                # This is a column property
                for col in prop.columns:
                    column_to_attr[col.name] = prop.key  # key is the attribute name
        
        return column_to_attr
    def close(self):
        """Clean up resources"""
        self.log_debug("Closing model report generator CLI")
        super().close()


def main():
    """Main entry point for the model report generator CLI"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available models
  %(prog)s list-models

  # List models showing existing reports
  %(prog)s list-models --show-existing

  # Analyze a specific model (show what would be generated)
  %(prog)s analyze User

  # Generate a report for a single model with all metadata
  %(prog)s generate User \\
    --connection default \\
    --slug user-activity-report \\
    --name "User Activity Report" \\
    --description "Comprehensive user activity tracking and analysis" \\
    --system

  # Generate without model association
  %(prog)s generate Role \\
    --connection default \\
    --slug role-permissions \\
    --name "Role Permissions" \\
    --description "Role and permission mapping" \\
    --no-model-association
        """
    )
    
    # Global options
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--no-icons', action='store_true',
                       help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl'],
                       default=None, help='Table output format')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run', required=True)
    
    # List command
    list_parser = subparsers.add_parser('list-models', help='List all available models')
    list_parser.add_argument('--show-existing', action='store_true',
                           help='Show existing model reports')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a model and show what would be generated')
    analyze_parser.add_argument('model', help='Model name to analyze')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate report from model')
    generate_parser.add_argument('model', help='Model name to generate report for')
    generate_parser.add_argument('-c', '--connection', required=True,
                               help='Database connection name to use')
    generate_parser.add_argument('--slug', required=True,
                               help='Report slug (unique identifier)')
    generate_parser.add_argument('--name', required=True,
                               help='Report name')
    generate_parser.add_argument('--description', required=True,
                               help='Report description')
    generate_parser.add_argument('--category', default=None,
                               help='Report category (default: "Model Reports")')
    generate_parser.add_argument('--no-relationships', action='store_true',
                               help='Disable relationship joins in queries')
    generate_parser.add_argument('-p', '--publish', action='store_true',
                               help='Auto-publish report after creation')
    generate_parser.add_argument('--system', action='store_true',
                               help='Mark report as system report')
    generate_parser.add_argument('--no-model-association', action='store_true',
                               help='Do not associate report with Model record')
    generate_parser.add_argument('--not-model', action='store_true',
                               help='Do not mark report as model report (is_model=False)')
    
    args = parser.parse_args()
    
    # Initialize CLI
    try:
        cli = ModelReportCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}", file=sys.stderr)
        return 1
    
    try:
        # Execute command
        if args.command == 'list-models':
            return cli.list_available_models(show_existing_reports=args.show_existing)
            
        elif args.command == 'analyze':
            return cli.analyze_model(args.model)
            
        elif args.command == 'generate':
            # Generate report with provided metadata
            result = cli.generate_report_from_model(
                model_name=args.model,
                connection_name=args.connection,
                report_slug=args.slug,
                report_name=args.name,
                report_description=args.description,
                category=args.category,
                include_relationships=not args.no_relationships,
                auto_publish=args.publish,
                is_system=args.system,
                is_model=not args.not_model,  # Default True unless --not-model flag
                associate_with_model=not args.no_model_association
            )
            
            if result.get('success'):
                cli.output_success(f"Successfully created report: {result['report'].name}")
                cli.output_info(f"  Slug: {result['report'].slug}")
                cli.output_info(f"  Columns: {result['columns_created']}")
                cli.output_info(f"  Variables: {result['variables_created']}")
                cli.output_info(f"  Has Relationships: {result['has_relationships']}")
                if result.get('model_id'):
                    cli.output_info(f"  Model ID: {result['model_id']}")
                return 0
            elif result.get('exists'):
                cli.output_warning("Report already exists")
                return 1
            else:
                cli.output_error("Failed to create report")
                return 1
        
        else:
            cli.output_error(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        cli.output_warning("\nOperation cancelled by user")
        return 130
    except Exception as e:
        cli.output_error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        cli.close()


if __name__ == '__main__':
    sys.exit(main())