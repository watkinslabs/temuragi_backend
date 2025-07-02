import yaml
from pathlib import Path
from datetime import datetime
import uuid

from app.register.database import db_registry

class ComponentImporter:
    """Unified model object import utility"""

    def __init__(self,  output_manager, model_registry_getter):
        """Initialize output manager, and model getter"""
        self.db_session=db_registry._routing_session()

        self.output_manager = output_manager
        self.get_model = model_registry_getter

        # Fields that should be skipped during import (auto-generated)
        self.skip_fields = {
            'created_at', 'updated_at', 'created_on', 'updated_on',
            'date_created', 'date_modified', 'timestamp', 'last_modified'
        }
        
        # Track UUID mappings across imports
        self._uuid_mappings = {}  # old_uuid -> new_uuid

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

        except Exception as e:
            self.output_manager.log_error(f"Error loading YAML file {file_path}: {e}")
            raise

    def _convert_import_value(self, value, column_type=None):
        """Convert imported values to appropriate database types"""
        if value is None:
            return None

        # Handle UUID strings
        if isinstance(value, str) and len(value) == 36 and '-' in value:
            try:
                import uuid
                return uuid.UUID(value)
            except ValueError:
                pass

        # Handle datetime strings
        if isinstance(value, str) and 'T' in value:
            try:
                from datetime import datetime
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                pass

        return value

    def _filter_import_data(self, data_dict, model_class):
        """Filter and validate data for import"""
        filtered_data = {}
        table_columns = {col.name: col for col in model_class.__table__.columns}

        # Get all model attributes (including those with underscores)
        model_attrs = set(dir(model_class))

        for key, value in data_dict.items():
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
                            filtered_data[key] = converted_value  # Use the model attribute name
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
                self.output_manager.log_warning(f"Field '{key}' not found in model attributes or table columns, skipping")

        return filtered_data

    def _find_existing_record_by_unique_fields(self, model_class, data, match_field=None):
        """Find existing record by unique fields (name, email, etc.)"""
        # If specific match field is provided, use it
        if match_field and match_field in data:
            return self.db_session.query(model_class).filter(
                getattr(model_class, match_field) == data[match_field]
            ).first()
        
        # Otherwise, try common unique fields in order
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

    def _find_all_matching_records(self, model_class, data, match_field=None):
        """Find ALL records that might conflict, not just by primary unique field"""
        matching_records = []
        
        # Special handling for PageFragment which has composite unique constraint
        if model_class.__name__ == 'PageFragment':
            # Check for the composite unique constraint: (page_id, fragment_key, is_active)
            if all(field in data for field in ['page_id', 'fragment_key', 'is_active']):
                existing = self.db_session.query(model_class).filter(
                    model_class.page_id == data['page_id'],
                    model_class.fragment_key == data['fragment_key'],
                    model_class.is_active == data['is_active']
                ).first()
                if existing:
                    matching_records.append(existing)
                    self.output_manager.log_debug(f"Found PageFragment by composite key: page_id={data['page_id']}, fragment_key={data['fragment_key']}, is_active={data['is_active']}")
        
        # Check all unique constraints on the model
        for constraint in model_class.__table__.constraints:
            if hasattr(constraint, 'columns'):
                # Check if all columns in this constraint match our data
                matches_constraint = True
                constraint_data = {}
                
                for col in constraint.columns:
                    col_name = col.name
                    if col_name in data:
                        constraint_data[col_name] = data[col_name]
                    else:
                        matches_constraint = False
                        break
                
                if matches_constraint and constraint_data:
                    # Build query for this constraint
                    query = self.db_session.query(model_class)
                    for col_name, value in constraint_data.items():
                        query = query.filter(getattr(model_class, col_name) == value)
                    
                    existing = query.first()
                    if existing and existing not in matching_records:
                        matching_records.append(existing)
                        self.output_manager.log_debug(f"Found conflicting record by constraint: {constraint_data}")
        
        # Also check by common unique fields
        existing_by_field = self._find_existing_record_by_unique_fields(model_class, data, match_field)
        if existing_by_field and existing_by_field not in matching_records:
            matching_records.append(existing_by_field)
        
        return matching_records

    def import_yaml_file(self, file_path, dry_run=False, update_existing=False, 
                        replace_existing=False, match_field=None):
        """
        Import YAML file with nested model structure

        Args:
            file_path: Path to YAML file
            dry_run: If True, validate but don't save to database
            update_existing: If True, update existing records by UUID
            replace_existing: If True, delete and recreate existing records by unique field
            match_field: Field to match for replace operations (default: auto-detect)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.output_manager.output_error(f"File not found: {file_path}")
                return 1

            self.output_manager.log_info(f"Importing from: {file_path}")

            # Load YAML data
            yaml_data = self._load_yaml_file(file_path)

            if not yaml_data:
                self.output_manager.output_error("Empty or invalid YAML file")
                return 1

            # Process each model in the file
            results = []
            for model_name, model_data in yaml_data.items():
                result = self._import_single_model(
                    model_name, model_data, dry_run, update_existing, 
                    replace_existing, match_field
                )
                results.append(result)

            # Summary
            successful = sum(1 for r in results if r == 0)
            failed = len(results) - successful

            if dry_run:
                self.output_manager.output_info(f"DRY RUN: {successful} models validated, {failed} failed validation")
            else:
                if failed == 0:
                    self.output_manager.output_success(f"Successfully imported {successful} models")
                else:
                    self.output_manager.output_warning(f"Imported {successful} models, {failed} failed")

            return 0 if failed == 0 else 1

        except Exception as e:
            self.output_manager.log_error(f"Error importing file {file_path}: {e}")
            self.output_manager.output_error(f"Import failed: {e}")
            return 1

    def _import_single_model(self, model_name, model_data, dry_run, update_existing,
                           replace_existing=False, match_field=None):
        """Import a single model from YAML data"""
        try:
            self.output_manager.log_info(f"Processing model: {model_name}")

            # Validate structure
            if not isinstance(model_data, dict) or 'meta' not in model_data or 'data' not in model_data:
                self.output_manager.output_error(f"Invalid structure for {model_name}: missing 'meta' or 'data' sections")
                return 1

            # Get model class
            model_class = self.get_model(model_name)
            if not model_class:
                self.output_manager.output_error(f"Model class '{model_name}' not found in registry")
                return 1

            # Validate metadata
            meta = model_data['meta']
            expected_table = model_class.__tablename__
            actual_table = meta.get('tablename')

            if actual_table != expected_table:
                self.output_manager.output_error(f"Table mismatch for {model_name}: expected '{expected_table}', got '{actual_table}'")
                return 1

            # Process data
            data = model_data['data']
            if isinstance(data, list):
                # Multiple records
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
            self.output_manager.log_error(f"Error processing model {model_name}: {e}")
            self.output_manager.output_error(f"Failed to process {model_name}: {e}")
            return 1

    def _import_single_record(self, model_class, data, dry_run, update_existing,
                            replace_existing=False, match_field=None):
        """Import a single record with improved update/replace logic"""
        try:
            # Filter and prepare data
            import_data = self._filter_import_data(data, model_class)

            if not import_data:
                self.output_manager.output_warning("No valid data to import")
                return 1

            # Clear session to avoid state issues
            self.db_session.expire_all()

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

            # Check for existing record
            existing_record = None
            existing_by_uuid = None
            existing_by_unique = None
            
            # First check by UUID if provided
            if 'id' in direct_data:
                existing_by_uuid = self.db_session.query(model_class).filter(
                    model_class.id == direct_data['id']
                ).first()
                
            # Also check by unique fields
            existing_by_unique = self._find_existing_record_by_unique_fields(
                model_class, direct_data, match_field
            )
            
            # Determine which existing record to use based on mode
            if replace_existing:
                # For replace, prefer unique field matches over UUID
                existing_record = existing_by_unique or existing_by_uuid
            elif update_existing:
                # For update, check both UUID and unique fields
                existing_record = existing_by_uuid or existing_by_unique
            else:
                # For create-only mode, UUID takes precedence
                existing_record = existing_by_uuid

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
                    old_id = existing_record.id
                    identifier = self._get_record_identifier(existing_record)
                    
                    # Store the UUID mapping for child records
                    self._uuid_replacements = getattr(self, '_uuid_replacements', {})
                    new_uuid = direct_data.get('id', uuid.uuid4())
                    self._uuid_replacements[str(old_id)] = new_uuid
                    
                    self.db_session.delete(existing_record)
                    self.db_session.flush()  # Flush but don't commit yet
                    
                    self.output_manager.log_info(f"Deleted existing {model_class.__name__}: {identifier} (ID: {old_id})")
                    
                    # Use the provided ID or generate new one
                    if 'id' not in direct_data:
                        direct_data['id'] = new_uuid
                    
                    existing_record = None  # Clear so we create new record
                    
                except Exception as e:
                    self.db_session.rollback()
                    self.output_manager.output_error(f"Cannot delete existing record: {e}")
                    self.output_manager.output_warning("Record may have foreign key dependencies")
                    return 1

            # For update mode or when record exists
            if existing_record and not replace_existing:
                if update_existing or (existing_by_uuid and direct_data.get('id') == existing_by_uuid.id):
                    # Update existing record
                    try:
                        # Track UUID mapping if the incoming data has a different UUID than existing
                        if 'id' in direct_data and direct_data['id'] != existing_record.id:
                            self._uuid_mappings[str(direct_data['id'])] = existing_record.id
                            self.output_manager.log_debug(f"Mapping UUID: {direct_data['id']} -> {existing_record.id}")
                        
                        # If we found by unique field but UUID doesn't match, update the found record
                        if existing_by_unique and not existing_by_uuid:
                            self.output_manager.log_info(f"Found existing record by unique field, updating it")
                            existing_record = existing_by_unique
                        
                        # Update fields directly on the existing record
                        for key, value in direct_data.items():
                            if key != 'id':  # Don't update UUID
                                setattr(existing_record, key, value)
                        
                        # Set property-mapped fields
                        for prop_name, value in property_data.items():
                            setattr(existing_record, prop_name, value)
                        
                        self.db_session.flush()
                        self.db_session.commit()
                        
                        self.output_manager.output_success(f"Updated {model_class.__name__} record: {existing_record.id}")
                        return 0
                        
                    except Exception as e:
                        self.db_session.rollback()
                        self.output_manager.log_error(f"Update failed: {e}")
                        self.output_manager.output_error(f"Failed to update record: {e}")
                        return 1
                else:
                    # Record exists but we're not in update mode
                    if existing_by_unique:
                        self.output_manager.output_error(f"Record already exists with same unique values. Use --update to modify or --replace to recreate.")
                    else:
                        self.output_manager.output_error(f"Record with UUID {direct_data.get('id')} already exists. Use --update to modify it.")
                    return 1
                        
            else:
                # Create new record
                try:
                    # Check for UUID mappings (for references to updated parent records)
                    for field, value in list(direct_data.items()):
                        if field.endswith('_id') and value:
                            # Check both _uuid_replacements (for replace mode) and _uuid_mappings (for update mode)
                            if hasattr(self, '_uuid_replacements') and str(value) in self._uuid_replacements:
                                direct_data[field] = self._uuid_replacements[str(value)]
                                self.output_manager.log_debug(f"Replaced UUID reference in {field}: {value} -> {direct_data[field]}")
                            elif str(value) in self._uuid_mappings:
                                direct_data[field] = self._uuid_mappings[str(value)]
                                self.output_manager.log_debug(f"Mapped UUID reference in {field}: {value} -> {direct_data[field]}")
                    
                    # For new records, generate new UUID if not provided
                    if 'id' not in direct_data:
                        direct_data['id'] = uuid.uuid4()
                    
                    # Check for any conflicting records before creating
                    conflicts = self._find_all_matching_records(model_class, direct_data)
                    if conflicts:
                        # In update mode, try to update the conflicting record instead
                        if update_existing and len(conflicts) == 1:
                            conflict = conflicts[0]
                            self.output_manager.log_info(f"Found conflicting {model_class.__name__} record, updating it instead")
                            
                            # Update the conflicting record
                            for key, value in direct_data.items():
                                if key != 'id':  # Don't change the UUID
                                    setattr(conflict, key, value)
                            
                            # Set property-mapped fields
                            for prop_name, value in property_data.items():
                                setattr(conflict, prop_name, value)
                            
                            self.db_session.flush()
                            self.db_session.commit()
                            
                            self.output_manager.output_success(f"Updated {model_class.__name__} record: {conflict.id}")
                            return 0
                        else:
                            # Not in update mode or multiple conflicts
                            conflict_info = []
                            for conflict in conflicts:
                                conflict_info.append(f"{self._get_record_identifier(conflict)} (ID: {conflict.id})")
                            self.output_manager.output_error(f"Cannot create {model_class.__name__}: conflicts with existing records: {', '.join(conflict_info)}")
                            if not update_existing:
                                self.output_manager.output_info("Use --update to modify existing or --replace to delete and recreate")
                            return 1
                    
                    new_record = model_class(**direct_data)

                    # Set property-mapped fields after creation
                    for prop_name, value in property_data.items():
                        setattr(new_record, prop_name, value)

                    self.db_session.add(new_record)
                    self.db_session.flush()
                    self.db_session.commit()

                    action = "Replaced" if replace_existing else "Created"
                    self.output_manager.output_success(f"{action} {model_class.__name__} record: {new_record.id}")
                    return 0
                    
                except Exception as e:
                    self.db_session.rollback()
                    self.output_manager.log_error(f"Failed to create record: {e}")
                    self.output_manager.output_error(f"Failed to create record: {e}")
                    return 1

        except Exception as e:
            self.db_session.rollback()
            self.output_manager.log_error(f"Error importing record: {e}")
            self.output_manager.output_error(f"Failed to import record: {e}")
            return 1

    def _import_multiple_records(self, model_class, data_list, dry_run, update_existing,
                               replace_existing=False, match_field=None):
        """Import multiple records"""
        try:
            successful = 0
            failed = 0

            for i, record_data in enumerate(data_list):
                try:
                    result = self._import_single_record(
                        model_class, record_data, dry_run, update_existing,
                        replace_existing, match_field
                    )
                    if result == 0:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    self.output_manager.log_error(f"Error importing record {i}: {e}")
                    failed += 1

            if dry_run:
                self.output_manager.output_info(f"DRY RUN: {successful} records validated, {failed} failed for {model_class.__name__}")
            else:
                if failed == 0:
                    self.output_manager.output_success(f"Imported {successful} {model_class.__name__} records")
                else:
                    self.output_manager.output_warning(f"Imported {successful} {model_class.__name__} records, {failed} failed")

            return 0 if failed == 0 else 1

        except Exception as e:
            self.output_manager.log_error(f"Error importing multiple records: {e}")
            return 1

    def _get_record_identifier(self, record):
        """Get a human-readable identifier for a record"""
        for attr in ['name', 'title', 'email', 'username', 'slug']:
            if hasattr(record, attr):
                value = getattr(record, attr)
                if value:
                    return str(value)
        return str(record.id)[:8]