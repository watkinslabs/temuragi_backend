import yaml
from pathlib import Path
from collections import OrderedDict

from app.register.database import db_registry

class ComponentExporter:
    """Unified model object export utility"""

    def __init__(self,  output_manager):
        """Initialize with database self.db_session and output manager"""
        self.db_session=db_registry._routing_session()

        self.output_manager = output_manager

        # Fields to comment out in template mode
        self.auto_generated_fields = {
            'id', 'created_at', 'updated_at', 'created_on', 'updated_on',
            'date_created', 'date_modified', 'timestamp', 'last_modified',
            'id'  # Often auto-increment primary keys
        }

    def _safe_string_convert(self, value):
        """Safely convert any SQLAlchemy object to string"""
        if value is None:
            return None
            
        # Handle SQLAlchemy quoted_name objects
        if hasattr(value, '__class__') and 'quoted_name' in str(value.__class__):
            return str(value)
            
        # Handle any SQLAlchemy wrapper objects
        if hasattr(value, '__module__') and value.__module__ and 'sqlalchemy' in value.__module__:
            return str(value)
            
        # For any object with explicit string representation
        if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
            return str(value)
            
        return value

    def _convert_value_to_exportable(self, value):
        """Convert database values to exportable format"""
        if value is None:
            return None

        # Handle Python native collections (dict, list) from JSONB columns
        if isinstance(value, (dict, list)):
            return value

        # Check if string value might be JSON and try to parse it
        if isinstance(value, str):
            # Common JSON patterns
            if (value.startswith('{') and value.endswith('}')) or \
               (value.startswith('[') and value.endswith(']')):
                try:
                    import json
                    parsed = json.loads(value)
                    return parsed
                except (json.JSONDecodeError, ValueError):
                    # Not valid JSON, return as string
                    pass

        # Convert UUID objects to strings
        if hasattr(value, 'hex'):
            return str(value)

        # Convert datetime objects to ISO format strings
        if hasattr(value, 'isoformat'):
            return value.isoformat()

        # Convert SQLAlchemy quoted_name objects to plain strings
        if hasattr(value, '__str__') and 'quoted_name' in str(type(value)):
            return str(value)
            
        # Additional safety for any SQLAlchemy objects
        return self._safe_string_convert(value)
    
    def _get_foreign_key_name(self, model_instance, id_field, name_field='name'):
        """Get the name for a foreign key UUID field"""
        relation_attr = id_field.replace('_id', '')
        if not hasattr(model_instance, relation_attr):
            return None

        related_obj = getattr(model_instance, relation_attr)
        if related_obj and hasattr(related_obj, name_field):
            return getattr(related_obj, name_field)

        return None

    def _get_model_meta(self, model_object):
        """Extract metadata from model object"""
        meta = OrderedDict()

        # Get table name - convert to string to avoid SQLAlchemy objects
        table_name = self._safe_string_convert(model_object.__table__.name)
        meta['tablename'] = table_name

        # Get schema if available - convert to string
        if hasattr(model_object.__table__, 'schema') and model_object.__table__.schema:
            schema = self._safe_string_convert(model_object.__table__.schema)
            meta['schema'] = schema
        else:
            meta['schema'] = 'public'  # Default schema

        return meta

    def _format_yaml_with_comments(self, data, template_mode=False):
        """Format YAML with comments for auto-generated fields in template mode"""
        if not template_mode:
            return yaml.dump(data, default_flow_style=False)

        # Convert to YAML string first
        yaml_content = yaml.dump(data, default_flow_style=False)

        # Process line by line to add comments
        lines = yaml_content.split('\n')
        processed_lines = []
        in_data_section = False

        for line in lines:
            if ':' in line and line.strip() == 'data:':
                # We're entering the data section
                processed_lines.append(line)
                in_data_section = True
                continue
            elif in_data_section and ':' in line and not line.startswith(' '):
                # We've left the data section
                in_data_section = False

            if in_data_section and ':' in line:
                # Extract field name (handle indentation)
                stripped = line.lstrip()
                if stripped and not stripped.startswith('#'):
                    field_name = stripped.split(':')[0].strip()

                    # Check if this field should be commented out
                    if field_name.lower() in self.auto_generated_fields:
                        # Comment out the line and add explanation
                        indent = line[:len(line) - len(line.lstrip())]
                        processed_lines.append(f"{indent}# {stripped}  # AUTO-GENERATED: Optional, system will create if not provided")
                    elif '_id' in field_name.lower():
                        # Foreign key UUIDs need special handling
                        indent = line[:len(line) - len(line.lstrip())]
                        processed_lines.append(line)
                        processed_lines.append(f"{indent}# NOTE: {field_name} must reference existing record UUID")
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def export_model_object(self, model_object, output_file_path, foreign_key_mappings=None,
                           header_title=None, header_description=None, template_mode=False):
        """
        Export any model object to YAML file with nested structure

        Args:
            model_object: The model instance to export
            output_file_path: Path where YAML file will be written
            foreign_key_mappings: Dict mapping UUID fields to name fields
            header_title: Custom header title
            header_description: Custom header description
            template_mode: If True, comment out auto-generated fields
        """
        try:
            # Ensure output directory exists
            output_path = Path(output_file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if foreign_key_mappings is None:
                foreign_key_mappings = {}

            # Build nested structure
            model_name = model_object.__class__.__name__
            root_data = OrderedDict()

            # Add model as top level key
            model_data = OrderedDict()

            # Add meta section
            model_data['meta'] = self._get_model_meta(model_object)

            # Build data section
            data_section = OrderedDict()

            # First pass: add all column data in order
            for column in model_object.__table__.columns:
                # Ensure column name is a plain string
                column_name = self._safe_string_convert(column.name)
                
                value = getattr(model_object, column_name)
                converted_value = self._convert_value_to_exportable(value)
                
                # Include ALL fields in templates, even None values for auto-generated fields
                if template_mode or converted_value is not None:
                    # For template mode, provide example values for None fields
                    if template_mode and converted_value is None:
                        if column_name.lower() in self.auto_generated_fields:
                            # Provide example values for auto-generated fields
                            if column_name == 'id':
                                converted_value = "12345678-1234-1234-1234-123456789abc"
                            elif 'created_at' in column_name or 'updated_at' in column_name:
                                converted_value = "2024-01-01T00:00:00"
                            elif 'created_on' in column_name or 'updated_on' in column_name:
                                converted_value = "2024-01-01T00:00:00"
                            else:
                                converted_value = "auto_generated_value"
                        else:
                            # Regular field with None value, keep as None or provide example
                            converted_value = None
                    
                    data_section[column_name] = converted_value

            # Second pass: insert foreign key names after their UUID fields
            if foreign_key_mappings:
                items = list(data_section.items())
                new_items = []

                for key, val in items:
                    new_items.append((key, val))

                    # Check if this is a UUID field that should have a name field added
                    if key in foreign_key_mappings:
                        name_field = foreign_key_mappings[key]
                        related_name = self._get_foreign_key_name(model_object, key, name_field)
                        if related_name:
                            name_key = key.replace('_id', f'_{name_field}')
                            new_items.append((name_key, related_name))

                data_section = OrderedDict(new_items)

            # Add data section to model
            model_data['data'] = data_section

            # Add model to root
            root_data[model_name] = model_data

            # Configure YAML dumper for OrderedDict and prevent Python object tags
            def represent_ordereddict(dumper, data):
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
            
            def represent_str(dumper, data):
                if '\n' in data:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
                return dumper.represent_scalar('tag:yaml.org,2002:str', data)

            yaml.add_representer(OrderedDict, represent_ordereddict)
            yaml.add_representer(str, represent_str)

            # Format YAML with optional comments
            yaml_content = self._format_yaml_with_comments(root_data, template_mode)

            # Generate header
            if header_title is None:
                object_name = getattr(model_object, 'name', str(model_object.id)[:8])
                header_title = f"{model_name} '{object_name}'"

            # Add template mode indicator to header
            header_suffix = " (Template)" if template_mode else ""

            # Write file with header
            with open(output_path, 'w') as f:
                f.write(f"# {header_title}{header_suffix}\n")
                if not template_mode:
                    f.write(f"# UUID: {model_object.id}\n")
                else:
                    f.write(f"# Template file - edit values before importing\n")
                    f.write(f"# \n")
                    f.write(f"# INSTRUCTIONS:\n")
                    f.write(f"# 1. AUTO-GENERATED fields are optional - uncomment to set specific values\n")
                    f.write(f"# 2. Update foreign key UUIDs to reference existing records\n")
                    f.write(f"# 3. Edit all other values as needed\n")
                    f.write(f"# 4. Foreign key constraints must be satisfied before import\n")
                if header_description:
                    f.write(f"# {header_description}\n")
                f.write(f"# Exported from template CLI\n")
                f.write(f"\n")
                f.write(yaml_content)

            if template_mode:
                self.output_manager.output_success(f"Generated template: {output_path}")
            else:
                self.output_manager.output_success(f"Exported to: {output_path}")
            return 0

        except Exception as e:
            self.output_manager.log_error(f"Error exporting model object: {e}")
            self.output_manager.output_error(f"Error exporting: {e}")
            return 1
        
    def export_all_model_objects(self, model_class, output_file_path, 
                                    foreign_key_mappings=None, header_title=None, 
                                    header_description=None, template_mode=False,
                                    filter_conditions=None, order_by=None, limit=None):
            """
            Export all objects from a model class to a single YAML file
            
            Args:
                model_class: The SQLAlchemy model class
                output_file_path: Path where YAML file will be written
                foreign_key_mappings: Dict mapping UUID fields to name fields
                header_title: Custom header title
                header_description: Custom header description
                template_mode: If True, comment out auto-generated fields
                filter_conditions: Optional dict of field:value pairs to filter records
                order_by: Optional field name to order results
                limit: Optional limit on number of records
            """
            try:
                # Ensure output directory exists
                output_path = Path(output_file_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if foreign_key_mappings is None:
                    foreign_key_mappings = {}
                
                # Build query
                query = self.db_session.query(model_class)
                
                # Apply filters if provided
                if filter_conditions:
                    for field, value in filter_conditions.items():
                        if hasattr(model_class, field):
                            query = query.filter(getattr(model_class, field) == value)
                
                # Apply ordering
                if order_by and hasattr(model_class, order_by):
                    query = query.order_by(getattr(model_class, order_by))
                else:
                    # Default ordering by id for consistency
                    if hasattr(model_class, 'id'):
                        query = query.order_by(model_class.id)
                
                # Apply limit if specified
                if limit:
                    query = query.limit(limit)
                
                # Execute query
                objects = query.all()
                
                if not objects:
                    self.output_manager.output_warning(f"No {model_class.__name__} objects found")
                    return 1
                
                # Build nested structure
                model_name = model_class.__name__
                root_data = OrderedDict()
                
                # Add model as top level key
                model_data = OrderedDict()
                
                # Add meta section
                model_data['meta'] = self._get_model_meta(objects[0])
                
                # Build data section with list of objects
                data_list = []
                
                for obj in objects:
                    obj_data = OrderedDict()
                    
                    # First pass: add all column data
                    for column in model_class.__table__.columns:
                        # Ensure column name is a plain string
                        column_name = self._safe_string_convert(column.name)
                        
                        value = getattr(obj, column_name)
                        converted_value = self._convert_value_to_exportable(value)
                        
                        if template_mode or converted_value is not None:
                            if template_mode and converted_value is None:
                                if column_name.lower() in self.auto_generated_fields:
                                    if column_name == 'id':
                                        converted_value = f"id_{data_list.__len__() + 1}"
                                    elif 'created_at' in column_name or 'updated_at' in column_name:
                                        converted_value = "2024-01-01T00:00:00"
                                    else:
                                        converted_value = "auto_generated_value"
                            
                            obj_data[column_name] = converted_value
                    
                    # Second pass: add foreign key names
                    if foreign_key_mappings:
                        items = list(obj_data.items())
                        new_items = []
                        
                        for key, val in items:
                            new_items.append((key, val))
                            
                            if key in foreign_key_mappings:
                                name_field = foreign_key_mappings[key]
                                related_name = self._get_foreign_key_name(obj, key, name_field)
                                if related_name:
                                    name_key = key.replace('_id', f'_{name_field}')
                                    new_items.append((name_key, related_name))
                        
                        obj_data = OrderedDict(new_items)
                    
                    data_list.append(obj_data)
                
                # Add data list to model
                model_data['data'] = data_list
                
                # Add model to root
                root_data[model_name] = model_data
                
                # Configure YAML dumper
                def represent_ordereddict(dumper, data):
                    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
                
                def represent_str(dumper, data):
                    if '\n' in data:
                        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
                
                yaml.add_representer(OrderedDict, represent_ordereddict)
                yaml.add_representer(str, represent_str)
                
                # Format YAML
                yaml_content = yaml.dump(root_data, default_flow_style=False)
                
                # Generate header
                if header_title is None:
                    header_title = f"{model_name} - All Records"
                
                header_suffix = " (Template)" if template_mode else ""
                
                # Write file with header
                with open(output_path, 'w') as f:
                    f.write(f"# {header_title}{header_suffix}\n")
                    f.write(f"# Total records: {len(objects)}\n")
                    if filter_conditions:
                        f.write(f"# Filters applied: {filter_conditions}\n")
                    if template_mode:
                        f.write(f"# Template file - edit values before importing\n")
                    if header_description:
                        f.write(f"# {header_description}\n")
                    f.write(f"# Exported from template CLI\n")
                    f.write(f"\n")
                    f.write(yaml_content)
                
                self.output_manager.output_success(f"Exported {len(objects)} {model_name} records to: {output_path}")
                return 0
                
            except Exception as e:
                self.output_manager.log_error(f"Error exporting all model objects: {e}")
                self.output_manager.output_error(f"Error exporting: {e}")
                return 1