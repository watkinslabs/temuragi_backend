import yaml
from pathlib import Path
from collections import OrderedDict


class ComponentExporter:
    """Unified model object export utility"""
    
    def __init__(self, session, output_manager):
        """Initialize with database session and output manager"""
        self.session = session
        self.output_manager = output_manager
        
        # Fields to comment out in template mode
        self.auto_generated_fields = {
            'uuid', 'created_at', 'updated_at', 'created_on', 'updated_on',
            'date_created', 'date_modified', 'timestamp', 'last_modified'
        }
    
    def _convert_value_to_exportable(self, value):
        """Convert database values to exportable format"""
        if value is None:
            return None
        
        # Convert UUID objects to strings
        if hasattr(value, 'hex'):
            return str(value)
        
        # Convert datetime objects to ISO format strings
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        
        return value
    
    def _get_foreign_key_name(self, model_instance, uuid_field, name_field='name'):
        """Get the name for a foreign key UUID field"""
        relation_attr = uuid_field.replace('_uuid', '')
        if not hasattr(model_instance, relation_attr):
            return None
        
        related_obj = getattr(model_instance, relation_attr)
        if related_obj and hasattr(related_obj, name_field):
            return getattr(related_obj, name_field)
        
        return None
    
    def _format_yaml_with_comments(self, data, template_mode=False):
        """Format YAML with comments for auto-generated fields in template mode"""
        if not template_mode:
            return yaml.dump(data, default_flow_style=False)
        
        # Convert to YAML string first
        yaml_content = yaml.dump(data, default_flow_style=False)
        
        # Process line by line to add comments
        lines = yaml_content.split('\n')
        processed_lines = []
        
        for line in lines:
            if ':' in line:
                # Extract field name (handle indentation)
                stripped = line.lstrip()
                if stripped and not stripped.startswith('#'):
                    field_name = stripped.split(':')[0].strip()
                    
                    # Check if this field should be commented out
                    if field_name.lower() in self.auto_generated_fields:
                        # Comment out the line and add explanation
                        indent = line[:len(line) - len(line.lstrip())]
                        processed_lines.append(f"{indent}# {stripped}  # Auto-generated - remove this line before importing")
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
        Export any model object to YAML file
        
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
            
            # Build ordered data from model object
            data = OrderedDict()
            
            # First pass: add all column data in order
            for column in model_object.__table__.columns:
                value = getattr(model_object, column.name)
                converted_value = self._convert_value_to_exportable(value)
                if converted_value is not None:
                    data[column.name] = converted_value
            
            # Second pass: insert foreign key names after their UUID fields
            if foreign_key_mappings:
                items = list(data.items())
                new_items = []
                
                for key, val in items:
                    new_items.append((key, val))
                    
                    # Check if this is a UUID field that should have a name field added
                    if key in foreign_key_mappings:
                        name_field = foreign_key_mappings[key]
                        related_name = self._get_foreign_key_name(model_object, key, name_field)
                        if related_name:
                            name_key = key.replace('_uuid', f'_{name_field}')
                            new_items.append((name_key, related_name))
                
                data = OrderedDict(new_items)
            
            # Configure YAML dumper for OrderedDict
            yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
            
            # Format YAML with optional comments
            yaml_content = self._format_yaml_with_comments(data, template_mode)
            
            # Generate header
            if header_title is None:
                model_name = model_object.__class__.__name__
                object_name = getattr(model_object, 'name', str(model_object.uuid)[:8])
                header_title = f"{model_name} '{object_name}'"
            
            # Add template mode indicator to header
            header_suffix = " (Template)" if template_mode else ""
            
            # Write file with header
            with open(output_path, 'w') as f:
                f.write(f"# {header_title}{header_suffix}\n")
                if not template_mode:
                    f.write(f"# UUID: {model_object.uuid}\n")
                else:
                    f.write(f"# Template file - edit values before importing\n")
                if header_description:
                    f.write(f"# {header_description}\n")
                f.write(f"# Exported from template CLI\n")
                if template_mode:
                    f.write(f"# Remove commented auto-generated fields before importing\n")
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