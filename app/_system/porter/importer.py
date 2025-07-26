import yaml
from pathlib import Path
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
import uuid
from collections import defaultdict, deque
import traceback
import json

from app.register.database import db_registry

class ComponentImporter:
    """Unified model object import utility"""

    def __init__(self, output_manager, model_registry_getter):
        """Initialize output manager, and model getter"""
        self.db_session = db_registry._routing_session()
        self.output_manager = output_manager
        self.get_model = model_registry_getter

        # Fields that should be skipped during import (auto-generated)
        self.skip_fields = {
            'created_at', 'updated_at', 'created_on', 'updated_on',
            'date_created', 'date_modified', 'timestamp', 'last_modified'
        }
        
        # Track all errors for summary
        self.import_errors = []

    def _log_error_context(self, operation, model_name, record_data, error, extra_context=None):
        """Log structured error with full context for container debugging"""
        error_info = {
            'operation': operation,
            'model': model_name,
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'record_identifier': self._get_import_record_identifier(record_data) if record_data else 'N/A',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add record data sample (first few fields to avoid huge logs)
        if record_data:
            sample_fields = {}
            for key, value in list(record_data.items())[:5]:
                if isinstance(value, (str, int, float, bool, type(None))):
                    sample_fields[key] = value
                else:
                    sample_fields[key] = str(type(value))
            error_info['record_sample'] = sample_fields
        
        # Add extra context if provided
        if extra_context:
            error_info.update(extra_context)
        
        # Add stack trace for debugging
        error_info['traceback'] = traceback.format_exc()
        
        # Store for summary
        self.import_errors.append(error_info)
        
        # Log as structured JSON for container log parsing
        self.output_manager.log_error(f"IMPORT_ERROR: {json.dumps(error_info, indent=2)}")
        
        # Also output user-friendly message
        self.output_manager.output_error(
            f"❌ {operation} failed for {model_name} ({error_info['record_identifier']}): "
            f"{error.__class__.__name__}: {str(error)}"
        )

    def _load_yaml_file(self, file_path):
        """Load and parse YAML file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove comment lines for cleaner parsing
            lines = content.split('\n')
            cleaned_lines = []
            in_multiline_string = False
            string_delimiter = None

            for line in lines:
                # Skip full comment lines
                if line.strip().startswith('#'):
                    continue

                # Track if we're inside a multi-line string (literal | or folded >)
                stripped_line = line.strip()
                if not in_multiline_string:
                    # Check for start of multi-line string
                    if ':' in line and ('|' in line or '>' in line):
                        # This starts a multi-line string block
                        yaml_key_part = line[:line.find(':')]
                        if '|' in line.split(':')[1] or '>' in line.split(':')[1]:
                            in_multiline_string = True
                            cleaned_lines.append(line)
                            continue

                    # Check for quoted strings that might contain #
                    if ':' in line:
                        value_part = line[line.find(':')+1:].strip()
                        if (value_part.startswith('"') and not value_part.endswith('"')) or \
                           (value_part.startswith("'") and not value_part.endswith("'")):
                            # Start of quoted multi-line string
                            string_delimiter = value_part[0]
                            in_multiline_string = True
                            cleaned_lines.append(line)
                            continue

                    # Normal line processing - remove inline comments carefully
                    if ' #' in line and ':' in line:
                        # Check if # appears in a value context (after colon)
                        colon_pos = line.find(':')
                        comment_pos = line.find(' #')

                        if comment_pos > colon_pos:
                            value_part = line[colon_pos+1:comment_pos].strip()
                            # If the value contains # without space (like #0066cc), keep it
                            if '#' in value_part and ' #' not in value_part:
                                cleaned_lines.append(line)
                            elif value_part:  # Normal value with comment
                                cleaned_lines.append(line[:comment_pos].rstrip())
                            else:
                                cleaned_lines.append(line)
                        else:
                            cleaned_lines.append(line)
                    else:
                        cleaned_lines.append(line)
                else:
                    # We're inside a multi-line string
                    if string_delimiter:
                        # Check for end of quoted string
                        if line.rstrip().endswith(string_delimiter):
                            in_multiline_string = False
                            string_delimiter = None
                    else:
                        # Check for end of literal/folded block (dedent)
                        if stripped_line and not line.startswith(' ') and not line.startswith('\t'):
                            in_multiline_string = False

                    # Always preserve content inside multi-line strings
                    cleaned_lines.append(line)

            cleaned_content = '\n'.join(cleaned_lines)
            return yaml.safe_load(cleaned_content)

        except yaml.YAMLError as e:
            self._log_error_context(
                'yaml_parse',
                'N/A',
                None,
                e,
                {
                    'file_path': str(file_path),
                    'yaml_error_details': str(e),
                    'line_number': getattr(e, 'problem_mark', {}).get('line', 'unknown') if hasattr(e, 'problem_mark') else 'unknown'
                }
            )
            raise
        except Exception as e:
            self._log_error_context(
                'file_load',
                'N/A',
                None,
                e,
                {'file_path': str(file_path)}
            )
            raise

    def _convert_import_value(self, value, column_type=None):
        """Convert imported values to appropriate database types"""
        if value is None:
            return None

        try:
            # Handle UUID strings
            if isinstance(value, str) and len(value) == 36 and '-' in value:
                try:
                    return uuid.UUID(value)
                except ValueError as e:
                    self.output_manager.log_warning(f"Invalid UUID format '{value}': {e}")
                    pass

            # Handle datetime strings
            if isinstance(value, str) and 'T' in value:
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError as e:
                    self.output_manager.log_warning(f"Invalid datetime format '{value}': {e}")
                    pass

            return value
            
        except Exception as e:
            self.output_manager.log_error(
                f"Value conversion error for '{value}' (type: {type(value).__name__}): {e}"
            )
            raise

    def _filter_import_data(self, data_dict, model_class):
        """Filter and validate data for import"""
        filtered_data = {}
        validation_errors = []
        
        try:
            table_columns = {col.name: col for col in model_class.__table__.columns}
            model_attrs = set(dir(model_class))

            for key, value in data_dict.items():
                try:
                    # Skip auto-generated fields
                    if key.lower() in self.skip_fields:
                        self.output_manager.log_debug(f"Skipping auto-generated field: {key}")
                        continue

                    # Skip foreign key name fields (they're just for reference)
                    if key.endswith('_name') and key.replace('_name', '_id') in data_dict:
                        self.output_manager.log_debug(f"Skipping reference field: {key}")
                        continue

                    # Check if this is a model attribute (could be mapped to a different column name)
                    if key in model_attrs and hasattr(model_class, key):
                        # Try to determine the actual column name
                        attr = getattr(model_class, key)

                        # Check if it's a column property
                        if hasattr(attr, 'property') and hasattr(attr.property, 'columns'):
                            # It's a column property, get the actual column name
                            actual_columns = list(attr.property.columns)
                            if actual_columns:
                                column_name = actual_columns[0].name
                                if column_name in table_columns:
                                    column = table_columns[column_name]
                                    converted_value = self._convert_import_value(value, column.type)
                                    filtered_data[key] = converted_value
                                    self.output_manager.log_debug(f"Including mapped field: {key} -> column {column_name} = {converted_value}")
                                    continue

                        # If it's a hybrid property or descriptor, we'll still try to set it
                        converted_value = self._convert_import_value(value)
                        filtered_data[key] = converted_value
                        self.output_manager.log_debug(f"Including model attribute: {key} = {converted_value}")

                    elif key in table_columns:
                        # Direct column match
                        column = table_columns[key]
                        converted_value = self._convert_import_value(value, column.type)
                        filtered_data[key] = converted_value
                        self.output_manager.log_debug(f"Including field: {key} = {converted_value}")
                    else:
                        validation_errors.append({
                            'field': key,
                            'value': str(value)[:100],  # Truncate long values
                            'error': 'Field not found in model'
                        })
                        self.output_manager.log_warning(
                            f"Field '{key}' not found in {model_class.__name__} "
                            f"(available: {', '.join(sorted(table_columns.keys())[:10])}...)"
                        )
                        
                except Exception as e:
                    validation_errors.append({
                        'field': key,
                        'value': str(value)[:100],
                        'error': str(e)
                    })
                    self.output_manager.log_error(f"Error processing field '{key}': {e}")

            if validation_errors:
                self.output_manager.log_error(
                    f"Data validation errors for {model_class.__name__}: "
                    f"{json.dumps(validation_errors, indent=2)}"
                )

            return filtered_data
            
        except Exception as e:
            self._log_error_context(
                'data_filter',
                model_class.__name__,
                data_dict,
                e,
                {'validation_errors': validation_errors}
            )
            raise

    def _detect_self_referencing_fks(self, model_class):
        """Detect self-referencing foreign keys in a model"""
        self_refs = []
        try:
            mapper = class_mapper(model_class)
            
            for prop in mapper.iterate_properties:
                if isinstance(prop, RelationshipProperty):
                    # Check if this relationship points to the same model
                    if prop.mapper.class_ == model_class:
                        # Find the foreign key column(s) for this relationship
                        for col in prop._calculated_default_uselist.local_columns:
                            self_refs.append(col.name)
                            self.output_manager.log_debug(
                                f"Found self-referencing FK in {model_class.__name__}: {col.name}"
                            )
            
        except Exception as e:
            self.output_manager.log_error(
                f"Error detecting self-referencing FKs in {model_class.__name__}: {e}"
            )
            
        return self_refs

    def _build_dependency_graph(self, model_class, records_data):
        """Build a dependency graph for records with self-referencing FKs"""
        self_ref_fks = self._detect_self_referencing_fks(model_class)
        if not self_ref_fks:
            return None
        
        self.output_manager.log_info(
            f"Building dependency graph for {model_class.__name__} with self-referencing FKs: {self_ref_fks}"
        )
        
        # Create a mapping of identifiers to records
        record_map = {}
        dependency_graph = defaultdict(set)
        unresolved_refs = []
        
        # First pass: build record map
        for i, record in enumerate(records_data):
            # Use multiple possible identifiers
            identifiers = []
            
            if 'id' in record:
                identifiers.append(('id', record['id']))
            if 'name' in record:
                identifiers.append(('name', record['name']))
            if 'slug' in record:
                identifiers.append(('slug', record['slug']))
            
            # Store record with all its identifiers
            for id_type, id_value in identifiers:
                record_map[(id_type, str(id_value))] = i
            
            # Also store by index for records without identifiers
            record_map[('_index', i)] = i
        
        # Second pass: build dependency graph
        for i, record in enumerate(records_data):
            dependencies = set()
            
            # Check each self-referencing FK
            for fk_col in self_ref_fks:
                if fk_col in record and record[fk_col] is not None:
                    fk_value = record[fk_col]
                    
                    # Try to find the referenced record
                    found = False
                    
                    # First try direct ID match
                    if ('id', str(fk_value)) in record_map:
                        dependencies.add(record_map[('id', str(fk_value))])
                        found = True
                    
                    # If not found and FK is a name reference (common pattern)
                    if not found and fk_col.endswith('_id'):
                        # Check if there's a corresponding name field
                        name_field = fk_col.replace('_id', '_name')
                        if name_field in record:
                            ref_name = record[name_field]
                            if ('name', str(ref_name)) in record_map:
                                dependencies.add(record_map[('name', str(ref_name))])
                                found = True
                    
                    # Try other identifier types
                    if not found:
                        for id_type in ['name', 'slug']:
                            if (id_type, str(fk_value)) in record_map:
                                dependencies.add(record_map[(id_type, str(fk_value))])
                                found = True
                                break
                    
                    if not found:
                        unresolved_refs.append({
                            'record_index': i,
                            'record_identifier': self._get_import_record_identifier(record),
                            'fk_column': fk_col,
                            'fk_value': fk_value,
                            'available_identifiers': list(record_map.keys())[:10]  # Sample
                        })
                        self.output_manager.log_warning(
                            f"Could not resolve FK reference {fk_col}={fk_value} in record {i} "
                            f"({self._get_import_record_identifier(record)})"
                        )
            
            dependency_graph[i] = dependencies
        
        if unresolved_refs:
            self.output_manager.log_error(
                f"Unresolved FK references in {model_class.__name__}: "
                f"{json.dumps(unresolved_refs, indent=2)}"
            )
        
        return dependency_graph

    def _topological_sort(self, dependency_graph):
        """Perform topological sort on dependency graph"""
        if not dependency_graph:
            return None
        
        # Calculate in-degrees
        in_degree = defaultdict(int)
        all_nodes = set()
        
        for node, deps in dependency_graph.items():
            all_nodes.add(node)
            for dep in deps:
                all_nodes.add(dep)
                in_degree[dep] += 1
        
        # Initialize queue with nodes having no dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        sorted_order = []
        
        while queue:
            node = queue.popleft()
            sorted_order.append(node)
            
            # Reduce in-degree for dependent nodes
            for dependent in dependency_graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(sorted_order) != len(all_nodes):
            cycle_nodes = all_nodes - set(sorted_order)
            self.output_manager.log_error(
                f"Circular dependency detected involving records: {cycle_nodes}"
            )
            return None
        
        return sorted_order
    
    def _extract_database_error_details(self, exception):
        """Extract detailed error information from database exceptions"""
        error_details = {
            'type': exception.__class__.__name__,
            'message': str(exception),
            'details': {}
        }
        
        # Handle IntegrityError (FK violations, unique constraints)
        if isinstance(exception, IntegrityError):
            error_str = str(exception.orig) if hasattr(exception, 'orig') else str(exception)
            
            # PostgreSQL patterns
            if "violates foreign key constraint" in error_str:
                # Extract constraint name and details
                if '"' in error_str:
                    parts = error_str.split('"')
                    if len(parts) > 1:
                        error_details['details']['constraint'] = parts[1]
                
                if "Key (" in error_str:
                    key_part = error_str[error_str.find("Key ("):]
                    error_details['details']['failed_reference'] = key_part
                    
                error_details['user_message'] = "Foreign key constraint violated - referenced record doesn't exist"
                
            elif "violates unique constraint" in error_str or "duplicate key value" in error_str:
                if '"' in error_str:
                    parts = error_str.split('"')
                    if len(parts) > 1:
                        error_details['details']['constraint'] = parts[1]
                        
                if "Key (" in error_str:
                    key_part = error_str[error_str.find("Key ("):]
                    error_details['details']['duplicate_values'] = key_part
                    
                error_details['user_message'] = "Unique constraint violated - record with these values already exists"
                
            elif "violates not-null constraint" in error_str:
                if "column" in error_str:
                    parts = error_str.split('"')
                    for i, part in enumerate(parts):
                        if part.endswith("column"):
                            if i + 1 < len(parts):
                                error_details['details']['null_column'] = parts[i + 1]
                                
                error_details['user_message'] = "Required field is missing or null"
                
        # Handle DataError (invalid data types, values out of range)
        elif isinstance(exception, DataError):
            error_str = str(exception.orig) if hasattr(exception, 'orig') else str(exception)
            
            if "invalid input syntax" in error_str:
                error_details['user_message'] = "Invalid data format for database field"
            elif "value too long" in error_str:
                error_details['user_message'] = "Value exceeds maximum length for field"
            elif "out of range" in error_str:
                error_details['user_message'] = "Numeric value out of valid range"
            else:
                error_details['user_message'] = "Invalid data for database field"
                
        # Generic fallback
        else:
            error_details['user_message'] = str(exception)
            
        return error_details

    def _detect_model_dependencies(self, model_class):
        """Detect which other models this model depends on via foreign keys"""
        dependencies = set()
        try:
            mapper = class_mapper(model_class)
            
            for prop in mapper.iterate_properties:
                if isinstance(prop, RelationshipProperty):
                    # Get the target model class
                    target_class = prop.mapper.class_
                    if target_class != model_class:  # Skip self-references
                        dependencies.add(target_class.__name__)
                        self.output_manager.log_debug(
                            f"{model_class.__name__} depends on {target_class.__name__} via {prop.key}"
                        )
                        
        except Exception as e:
            self.output_manager.log_error(
                f"Error detecting dependencies for {model_class.__name__}: {e}"
            )
            
        return dependencies

    def _build_model_dependency_graph(self, yaml_data):
        """Build dependency graph for all models in the YAML"""
        model_graph = {}
        
        for model_name in yaml_data.keys():
            try:
                model_class = self.get_model(model_name)
                if model_class:
                    dependencies = self._detect_model_dependencies(model_class)
                    # Only include dependencies that are also being imported
                    model_graph[model_name] = dependencies & set(yaml_data.keys())
                else:
                    model_graph[model_name] = set()
                    self.output_manager.log_warning(
                        f"Model '{model_name}' not found in registry"
                    )
            except Exception as e:
                self.output_manager.log_error(
                    f"Error processing model '{model_name}': {e}"
                )
                model_graph[model_name] = set()
        
        return model_graph

    def _topological_sort_models(self, model_graph):
        """Sort models by their dependencies"""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        
        for model, deps in model_graph.items():
            for dep in deps:
                in_degree[dep] += 1
        
        # Initialize queue with models having no dependencies
        queue = deque([model for model in model_graph if in_degree[model] == 0])
        sorted_models = []
        
        while queue:
            model = queue.popleft()
            sorted_models.append(model)
            
            # Reduce in-degree for models that depend on this one
            for other_model, deps in model_graph.items():
                if model in deps:
                    in_degree[other_model] -= 1
                    if in_degree[other_model] == 0:
                        queue.append(other_model)
        
        # Check for circular dependencies
        if len(sorted_models) != len(model_graph):
            missing = set(model_graph.keys()) - set(sorted_models)
            circular_deps = []
            for model in missing:
                deps = model_graph.get(model, set())
                circular_deps.append({'model': model, 'depends_on': list(deps)})
                
            self.output_manager.log_error(
                f"Circular dependency detected: {json.dumps(circular_deps, indent=2)}"
            )
            return None
        
        return sorted_models

    def _print_import_summary(self):
        """Print a summary of all import errors"""
        if not self.import_errors:
            return
            
        self.output_manager.output_error("\n=== IMPORT ERROR SUMMARY ===")
        self.output_manager.output_error(f"Total errors: {len(self.import_errors)}")
        
        # Group errors by type
        errors_by_type = defaultdict(list)
        for error in self.import_errors:
            errors_by_type[error['error_type']].append(error)
        
        for error_type, errors in errors_by_type.items():
            self.output_manager.output_error(f"\n{error_type} ({len(errors)} errors):")
            for error in errors[:3]:  # Show first 3 of each type
                self.output_manager.output_error(
                    f"  - {error['model']}: {error['record_identifier']} - {error['error_message']}"
                )
            if len(errors) > 3:
                self.output_manager.output_error(f"  ... and {len(errors) - 3} more")

    def import_yaml_file(self, file_path, dry_run=False, update_existing=False, 
                        replace_existing=False, match_field=None):
        try:
            # Reset error tracking
            self.import_errors = []
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.output_manager.output_error(f"File not found: {file_path}")
                return 1

            self.output_manager.log_info(f"Importing from: {file_path}")
            self.output_manager.log_info(
                f"Import mode: dry_run={dry_run}, update={update_existing}, "
                f"replace={replace_existing}, match_field={match_field}"
            )

            yaml_data = self._load_yaml_file(file_path)

            if not yaml_data:
                self.output_manager.output_error("Empty or invalid YAML file")
                return 1

            # Build model dependency graph and sort
            model_graph = self._build_model_dependency_graph(yaml_data)
            sorted_models = self._topological_sort_models(model_graph)
            
            if sorted_models is None:
                self.output_manager.output_error("Cannot resolve model dependencies")
                return 1
            
            self.output_manager.log_info(f"Import order: {' -> '.join(sorted_models)}")

            results = []
            # Import models in dependency order
            for model_name in sorted_models:
                if model_name in yaml_data:
                    model_data = yaml_data[model_name]
                    result = self._import_single_model(
                        model_name, model_data, dry_run, update_existing, 
                        replace_existing, match_field
                    )
                    results.append(result)

            successful = sum(1 for r in results if r == 0)
            failed = len(results) - successful

            if dry_run:
                self.output_manager.output_info(f"DRY RUN: {successful} models validated, {failed} failed validation")
            else:
                if failed == 0:
                    self.output_manager.output_success(f"Successfully imported {successful} models")
                else:
                    self.output_manager.output_warning(f"Imported {successful} models, {failed} failed")

            # Print error summary
            self._print_import_summary()

            return 0 if failed == 0 else 1

        except Exception as e:
            self._log_error_context(
                'import_file',
                'N/A',
                None,
                e,
                {'file_path': str(file_path)}
            )
            self._print_import_summary()
            return 1

    def _import_single_model(self, model_name, model_data, dry_run, update_existing,
                           replace_existing=False, match_field=None):
        """Import a single model from YAML data"""
        try:
            self.output_manager.log_info(f"Processing model: {model_name}")

            # Validate structure
            if not isinstance(model_data, dict) or 'meta' not in model_data or 'data' not in model_data:
                error = ValueError(f"Invalid structure: missing 'meta' or 'data' sections")
                self._log_error_context(
                    'model_structure_validation',
                    model_name,
                    model_data,
                    error
                )
                return 1

            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                error = ValueError(f"Model class not found in registry")
                self._log_error_context(
                    'model_lookup',
                    model_name,
                    None,
                    error
                )
                return 1

            # Validate metadata
            meta = model_data['meta']
            expected_table = model_class.__tablename__
            actual_table = meta.get('tablename')

            if actual_table != expected_table:
                error = ValueError(f"Table mismatch: expected '{expected_table}', got '{actual_table}'")
                self._log_error_context(
                    'table_validation',
                    model_name,
                    None,
                    error,
                    {'expected': expected_table, 'actual': actual_table}
                )
                return 1

            # Process data
            data = model_data['data']
            
            # Show what we're about to process
            if isinstance(data, list):
                self.output_manager.output_info(f"  Processing {len(data)} {model_name} records...")
            else:
                record_id = self._get_import_record_identifier(data)
                self.output_manager.output_info(f"  Processing {model_name}: {record_id}")
            
            if isinstance(data, list):
                # Multiple records - check for self-referencing FKs
                return self._import_multiple_records(
                    model_class, data, dry_run, update_existing, 
                    replace_existing, match_field
                )
            else:
                # Single record
                return self._import_single_record(
                    model_class, data, dry_run, update_existing, 
                    replace_existing, match_field
                )

        except Exception as e:
            self._log_error_context(
                'model_import',
                model_name,
                None,
                e
            )
            return 1

    def _import_multiple_records(self, model_class, data_list, dry_run, update_existing,
                               replace_existing=False, match_field=None):
        """Import multiple records with dependency ordering for self-referencing FKs"""
        try:
            # Build dependency graph for self-referencing FKs
            dependency_graph = self._build_dependency_graph(model_class, data_list)
            
            # Determine import order
            if dependency_graph:
                import_order = self._topological_sort(dependency_graph)
                if import_order is None:
                    self.output_manager.output_error(
                        f"Cannot import {model_class.__name__}: circular dependencies detected"
                    )
                    return 1
                
                self.output_manager.log_info(
                    f"Importing {len(data_list)} {model_class.__name__} records in dependency order"
                )
            else:
                # No self-referencing FKs, use original order
                import_order = list(range(len(data_list)))
            
            successful = 0
            failed = 0
            
            # Import records in dependency order
            for idx in import_order:
                if idx >= len(data_list):
                    continue
                    
                record_data = data_list[idx]
                
                try:
                    self.output_manager.log_debug(f"Importing record {idx + 1}/{len(data_list)}")
                    
                    result = self._import_single_record(
                        model_class, record_data, dry_run, update_existing,
                        replace_existing, match_field
                    )
                    
                    if result == 0:
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    self._log_error_context(
                        'record_import',
                        model_class.__name__,
                        record_data,
                        e,
                        {'record_index': idx}
                    )
                    failed += 1

            if dry_run:
                self.output_manager.output_info(
                    f"DRY RUN: {successful} records validated, {failed} failed for {model_class.__name__}"
                )
            else:
                if failed == 0:
                    self.output_manager.output_success(f"Imported {successful} {model_class.__name__} records")
                else:
                    self.output_manager.output_warning(
                        f"Imported {successful} {model_class.__name__} records, {failed} failed"
                    )

            return 0 if failed == 0 else 1

        except Exception as e:
            self._log_error_context(
                'batch_import',
                model_class.__name__,
                None,
                e,
                {'total_records': len(data_list)}
            )
            return 1

    def _get_record_identifier(self, record):
        """Get a human-readable identifier for a record"""
        for attr in ['name', 'title', 'email', 'username', 'slug']:
            if hasattr(record, attr):
                value = getattr(record, attr)
                if value:
                    return str(value)
        return str(record.id)[:8]
    
    def _get_import_record_identifier(self, data):
        """Get a human-readable identifier from import data"""
        if not data:
            return "unknown"
            
        # Try common identifier fields
        for field in ['name', 'title', 'slug', 'email', 'username', 'code']:
            if field in data and data[field]:
                return str(data[field])
        
        # Try ID if available
        if 'id' in data:
            return f"ID: {str(data['id'])[:8]}..."
        
        # Fallback to first non-null value
        for key, value in data.items():
            if value and not key.endswith('_id'):
                return f"{key}={str(value)[:20]}"
        
        return "unknown"

    def _find_existing_record_by_unique_fields(self, model_class, data, match_field=None):
        """Find existing record by unique fields or composite unique constraints"""
        try:
            # If specific match field is provided, use it
            if match_field and match_field in data:
                return self.db_session.query(model_class).filter(
                    getattr(model_class, match_field) == data[match_field]
                ).first()

            # Check all unique constraints (single and composite)
            if hasattr(model_class, '__table__'):
                # Look for UniqueConstraint objects and unique indexes
                constraints_to_check = []
                
                # Get UniqueConstraint objects
                from sqlalchemy import UniqueConstraint
                for constraint in model_class.__table__.constraints:
                    if isinstance(constraint, UniqueConstraint):
                        constraints_to_check.append((constraint.name, [col.name for col in constraint.columns]))
                
                # Also check unique indexes (sometimes unique constraints are implemented as indexes)
                for index in model_class.__table__.indexes:
                    if index.unique:
                        constraints_to_check.append((index.name, [col.name for col in index.columns]))
                
                # Try each unique constraint
                for constraint_name, constraint_columns in constraints_to_check:
                    # Check if we have all required fields in data
                    if all(col_name in data and data[col_name] is not None for col_name in constraint_columns):
                        # Build filter conditions
                        filters = []
                        for col_name in constraint_columns:
                            if hasattr(model_class, col_name):
                                filters.append(getattr(model_class, col_name) == data[col_name])
                        
                        if filters and len(filters) == len(constraint_columns):
                            existing = self.db_session.query(model_class).filter(*filters).first()
                            if existing:
                                self.output_manager.log_debug(
                                    f"Found existing record by unique constraint/index '{constraint_name}': "
                                    f"{', '.join([f'{col}={data[col]}' for col in constraint_columns])}"
                                )
                                return existing

            # Try common unique fields in order
            unique_fields = ['name', 'email', 'username', 'slug', 'code', 'identifier']

            for field in unique_fields:
                if field in data and hasattr(model_class, field):
                    existing = self.db_session.query(model_class).filter(
                        getattr(model_class, field) == data[field]
                    ).first()
                    if existing:
                        self.output_manager.log_debug(f"Found existing record by {field}: {data[field]}")
                        return existing

            return None
            
        except Exception as e:
            self.output_manager.log_error(
                f"Error finding existing record for {model_class.__name__}: {e}"
            )
            return None

    def _import_single_record(self, model_class, data, dry_run, update_existing,
                            replace_existing=False, match_field=None):
        """Import a single record with improved update/replace logic"""
        try:
            # Filter and prepare data
            import_data = self._filter_import_data(data, model_class)

            if not import_data:
                self.output_manager.output_warning("No valid data to import after filtering")
                return 1

            # Check for existing record
            existing_record = None

            # First check by UUID if updating and UUID is provided
            if 'id' in import_data and update_existing:
                # Ensure UUID is properly formatted
                record_uuid = import_data['id']
                if isinstance(record_uuid, str):
                    try:
                        record_uuid = uuid.UUID(record_uuid)
                    except ValueError as e:
                        self._log_error_context(
                            'uuid_parse',
                            model_class.__name__,
                            import_data,
                            e,
                            {'uuid_value': record_uuid}
                        )
                        return 1
                
                existing_record = self.db_session.query(model_class).filter(
                    model_class.id == record_uuid
                ).first()
                
                if existing_record:
                    self.output_manager.log_debug(f"Found existing record by UUID: {record_uuid}")

            # Always check for existing records by unique constraints when updating
            # This handles cases where records don't have UUIDs in the import file
            if update_existing and not existing_record:
                existing_record = self._find_existing_record_by_unique_fields(
                    model_class, import_data, match_field
                )
                if existing_record:
                    self.output_manager.log_info(
                        f"Found existing {model_class.__name__} by unique constraints, will update"
                    )

            # If replacing, find by unique fields
            if replace_existing and not existing_record:
                existing_record = self._find_existing_record_by_unique_fields(
                    model_class, import_data, match_field
                )

            if dry_run:
                if existing_record:
                    if replace_existing:
                        action = "REPLACE (delete + create)"
                    else:
                        action = "UPDATE"
                else:
                    action = "CREATE"
                self.output_manager.output_info(f"DRY RUN: Would {action} {model_class.__name__} record")
                return 0

            # Handle replace mode - delete existing record first
            if replace_existing and existing_record:
                try:
                    record_id = existing_record.id
                    identifier = self._get_record_identifier(existing_record)

                    self.db_session.delete(existing_record)
                    self.db_session.flush()  # Flush but don't commit yet

                    self.output_manager.log_info(f"Deleted existing {model_class.__name__}: {identifier} (ID: {record_id})")

                    # Don't use the old UUID for the new record
                    if 'id' in import_data:
                        del import_data['id']

                    existing_record = None  # Clear so we create new record

                except Exception as e:
                    self.db_session.rollback()
                    error_details = self._extract_database_error_details(e)
                    self._log_error_context(
                        'record_delete',
                        model_class.__name__,
                        import_data,
                        e,
                        error_details
                    )
                    return 1

            # Special handling for fields that map to properties
            property_mappings = {
                '_credentials': 'credentials'
            }

            # Separate property-mapped fields from direct fields
            property_data = {}
            direct_data = {}

            for key, value in import_data.items():
                if key in property_mappings:
                    property_data[property_mappings[key]] = value
                else:
                    direct_data[key] = value

            if existing_record and update_existing:
                # Update existing record directly without merge
                try:
                    # Update fields directly on the existing record
                    for key, value in direct_data.items():
                        if key != 'id':  # Don't update UUID
                            setattr(existing_record, key, value)
                            self.output_manager.log_debug(f"Updated field {key} = {value}")

                    # Set property-mapped fields
                    for prop_name, value in property_data.items():
                        setattr(existing_record, prop_name, value)
                        self.output_manager.log_debug(f"Updated property {prop_name}")

                    # Commit the changes
                    self.db_session.commit()

                    self.output_manager.output_success(
                        f"✓ Updated {model_class.__name__}: {self._get_record_identifier(existing_record)}"
                    )
                    return 0

                except Exception as e:
                    self.db_session.rollback()
                    error_details = self._extract_database_error_details(e)
                    self._log_error_context(
                        'record_update',
                        model_class.__name__,
                        import_data,
                        e,
                        error_details
                    )
                    return 1

            else:
                # Create new record
                try:
                    # For new records, generate new UUID if not provided
                    if 'id' not in direct_data:
                        direct_data['id'] = uuid.uuid4()
                    elif isinstance(direct_data['id'], str):
                        # Ensure UUID is properly formatted
                        try:
                            direct_data['id'] = uuid.UUID(direct_data['id'])
                        except ValueError as e:
                            self._log_error_context(
                                'uuid_create',
                                model_class.__name__,
                                direct_data,
                                e
                            )
                            return 1

                    new_record = model_class(**direct_data)

                    # Set property-mapped fields after creation
                    for prop_name, value in property_data.items():
                        setattr(new_record, prop_name, value)

                    self.db_session.add(new_record)
                    self.db_session.commit()

                    action = "Replaced" if replace_existing else "Created"
                    self.output_manager.output_success(
                        f"✓ {action} {model_class.__name__}: {self._get_record_identifier(new_record)}"
                    )
                    return 0

                except Exception as e:
                    self.db_session.rollback()
                    error_details = self._extract_database_error_details(e)
                    self._log_error_context(
                        'record_create',
                        model_class.__name__,
                        import_data,
                        e,
                        error_details
                    )
                    return 1

        except Exception as e:
            self.db_session.rollback()
            self._log_error_context(
                'record_process',
                model_class.__name__,
                data,
                e
            )
            return 1