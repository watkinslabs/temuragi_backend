import yaml
from pathlib import Path
from collections import OrderedDict


class ComponentImporter:
    """Unified model object import utility"""
    
    def __init__(self, session, output_manager, model_registry_getter):
        """Initialize with database session, output manager, and model getter"""
        self.session = session
        self.output_manager = output_manager
        self.get_model = model_registry_getter
        
        # Fields that should be skipped during import (auto-generated)
        self.skip_fields = {
            'created_at', 'updated_at', 'created_on', 'updated_on',
            'date_created', 'date_modified', 'timestamp', 'last_modified'
        }
    
    def _load_yaml_file(self, file_path):
        """Load and parse YAML file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Remove comment lines for cleaner parsing
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                if line.strip().startswith('#'):
                    continue
                # Remove inline comments but preserve YAML structure
                if ' #' in line and ':' in line:
                    # Only remove comments after field values
                    parts = line.split(' #', 1)
                    cleaned_lines.append(parts[0].rstrip())
                else:
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
        
        for key, value in data_dict.items():
            # Skip auto-generated fields
            if key.lower() in self.skip_fields:
                self.output_manager.log_debug(f"Skipping auto-generated field: {key}")
                continue
            
            # Skip foreign key name fields (they're just for reference)
            if key.endswith('_name') and key.replace('_name', '_uuid') in data_dict:
                self.output_manager.log_debug(f"Skipping reference field: {key}")
                continue
            
            # Only include fields that exist as columns
            if key in table_columns:
                column = table_columns[key]
                converted_value = self._convert_import_value(value, column.type)
                filtered_data[key] = converted_value
                self.output_manager.log_debug(f"Including field: {key} = {converted_value}")
            else:
                self.output_manager.log_warning(f"Field '{key}' not found in table columns, skipping")
        
        return filtered_data
    
    def import_yaml_file(self, file_path, dry_run=False, update_existing=False):
        """
        Import YAML file with nested model structure
        
        Args:
            file_path: Path to YAML file
            dry_run: If True, validate but don't save to database
            update_existing: If True, update existing records by UUID
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
                result = self._import_single_model(model_name, model_data, dry_run, update_existing)
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
    
    def _import_single_model(self, model_name, model_data, dry_run, update_existing):
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
                return self._import_multiple_records(model_class, data, dry_run, update_existing)
            else:
                # Single record
                return self._import_single_record(model_class, data, dry_run, update_existing)
                
        except Exception as e:
            self.output_manager.log_error(f"Error processing model {model_name}: {e}")
            self.output_manager.output_error(f"Failed to process {model_name}: {e}")
            return 1
    
    def _import_single_record(self, model_class, data, dry_run, update_existing):
        """Import a single record"""
        try:
            # Filter and prepare data
            import_data = self._filter_import_data(data, model_class)
            
            if not import_data:
                self.output_manager.output_warning("No valid data to import")
                return 1
            
            # Check for existing record if UUID provided
            existing_record = None
            if 'uuid' in import_data and update_existing:
                existing_record = self.session.query(model_class).filter(
                    model_class.uuid == import_data['uuid']
                ).first()
            
            if dry_run:
                action = "UPDATE" if existing_record else "CREATE"
                self.output_manager.output_info(f"DRY RUN: Would {action} {model_class.__name__} record")
                return 0
            
            if existing_record:
                # Update existing record
                for key, value in import_data.items():
                    if key != 'uuid':  # Don't update UUID
                        setattr(existing_record, key, value)
                
                self.session.commit()
                self.output_manager.output_success(f"Updated {model_class.__name__} record: {existing_record.uuid}")
                return 0
            else:
                # Create new record
                new_record = model_class(**import_data)
                self.session.add(new_record)
                self.session.commit()
                
                self.output_manager.output_success(f"Created {model_class.__name__} record: {new_record.uuid}")
                return 0
                
        except Exception as e:
            self.session.rollback()
            self.output_manager.log_error(f"Error importing record: {e}")
            self.output_manager.output_error(f"Failed to import record: {e}")
            return 1
    
    def _import_multiple_records(self, model_class, data_list, dry_run, update_existing):
        """Import multiple records"""
        try:
            successful = 0
            failed = 0
            
            for i, record_data in enumerate(data_list):
                try:
                    result = self._import_single_record(model_class, record_data, dry_run, update_existing)
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