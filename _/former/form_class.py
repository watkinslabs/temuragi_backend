import inspect
from typing import Dict, List, Any, Optional, Type
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from datetime import datetime
import html


class FormFieldConfig:
    """Configuration for individual form fields"""
    
    def __init__(self, field_name: str, column_info: Dict[str, Any]):
        self.field_name = field_name
        self.column_info = column_info
        self.column = column_info.get('column')
        self.is_relationship = column_info.get('is_relationship', False)
        
    @property
    def field_type(self) -> str:
        """Determine Bootstrap input type based on SQLAlchemy column type"""
        if self.is_relationship:
            return 'select'
            
        column = self.column
        field_name_lower = self.field_name.lower()
        
        # Handle specific SQLAlchemy types with proper validation
        if isinstance(column.type, Boolean):
            return 'checkbox'
        elif isinstance(column.type, (Text,)):
            return 'textarea'
        elif isinstance(column.type, DateTime):
            # Check if it's date-only or datetime
            if 'date' in field_name_lower and 'time' not in field_name_lower:
                return 'date'
            return 'datetime-local'
        elif isinstance(column.type, Integer):
            return 'number'
        elif isinstance(column.type, (Float, Numeric)):
            return 'decimal'
        elif isinstance(column.type, UUID):
            return 'hidden'  # UUIDs usually auto-generated
        elif isinstance(column.type, JSON):
            return 'json'
        elif isinstance(column.type, String):
            # Check length for text vs textarea
            if hasattr(column.type, 'length') and column.type.length and column.type.length > 255:
                return 'textarea'
            
            # Special string field types based on field name
            if 'email' in field_name_lower:
                return 'email'
            elif 'url' in field_name_lower or 'link' in field_name_lower:
                return 'url'
            elif 'phone' in field_name_lower or 'tel' in field_name_lower:
                return 'tel'
            elif 'password' in field_name_lower:
                return 'password'
            elif 'color' in field_name_lower or 'colour' in field_name_lower:
                return 'color'
            elif ('date' in field_name_lower and 'time' not in field_name_lower and 
                  'update' not in field_name_lower and 'create' not in field_name_lower):
                return 'date'
            elif ('time' in field_name_lower or 'datetime' in field_name_lower) and \
                 'update' not in field_name_lower and 'create' not in field_name_lower:
                return 'datetime-local'
            
            return 'text'
        else:
            return 'text'
    
    @property
    def is_required(self) -> bool:
        """Check if field is required"""
        if self.is_relationship:
            return False  # Handle relationship requirements separately
        return not self.column.nullable and not self.column.default and not self.column.server_default
    
    @property
    def max_length(self) -> Optional[int]:
        """Get max length if applicable"""
        if not self.is_relationship and hasattr(self.column.type, 'length'):
            return self.column.type.length
        return None
    
    @property
    def description(self) -> str:
        """Get field description from comment"""
        if self.is_relationship:
            return f"Select {self.field_name.replace('_uuid', '').replace('_', ' ').title()}"
        return self.column.comment or self.field_name.replace('_', ' ').title()
    
    @property
    def tooltip_text(self) -> Optional[str]:
        """Get tooltip text from column comment"""
        if self.is_relationship:
            # Try to extract foreign table name for tooltip
            return f"Select a related {self.field_name.replace('_uuid', '').replace('_', ' ').title()}"
        
        comment = self.column.comment
        if comment:
            # Clean up the comment for tooltip display
            return html.escape(comment.strip())
        return None
    
    @property 
    def validation_attributes(self) -> Dict[str, str]:
        """Get HTML5 validation attributes based on column type"""
        attrs = {}
        
        if self.is_relationship:
            return attrs
            
        column = self.column
        
        # Required validation
        if self.is_required:
            attrs['required'] = 'required'
        
        # Length validation for strings
        if isinstance(column.type, String) and hasattr(column.type, 'length') and column.type.length:
            attrs['maxlength'] = str(column.type.length)
        
        # Numeric validation
        if isinstance(column.type, Integer):
            attrs['step'] = '1'
            # Add min/max if we can determine from constraints
        elif isinstance(column.type, (Float, Numeric)):
            attrs['step'] = 'any'
            
        # Pattern validation for specific field types
        if self.field_type == 'email':
            attrs['pattern'] = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'


class BootstrapFormGenerator:
    """Generates Bootstrap HTML forms from SQLAlchemy models"""
    
    def __init__(self, bootstrap_version: str = "5"):
        self.bootstrap_version = bootstrap_version
        self.excluded_fields = {'uuid', 'created_at', 'updated_at', 'is_active'}
        
    def generate_form_html(self, model_class: Type, 
                          form_id: str = None,
                          form_title: str = None,
                          include_submit: bool = True,
                          field_overrides: Dict[str, Dict[str, Any]] = None) -> str:
        """Generate complete Bootstrap form HTML for a model"""
        
        form_id = form_id or f"{model_class.__name__.lower()}_form"
        form_title = form_title or f"{model_class.__name__} Form"
        field_overrides = field_overrides or {}
        
        # Get model information
        model_info = self._introspect_model(model_class)
        
        # Generate form fields
        form_fields_html = []
        for field_name, field_config in model_info['fields'].items():
            if field_name in self.excluded_fields:
                continue
                
            # Apply any field overrides
            override_config = field_overrides.get(field_name, {})
            field_html = self._generate_field_html(field_config, override_config)
            form_fields_html.append(field_html)
        
        # Combine into complete form
        form_html = self._build_complete_form(
            form_id=form_id,
            form_title=form_title,
            fields_html=form_fields_html,
            include_submit=include_submit
        )
        
        return form_html
    
    def _introspect_model(self, model_class: Type) -> Dict[str, Any]:
        """Introspect SQLAlchemy model to extract field information"""
        inspector = sqlalchemy_inspect(model_class)
        
        model_info = {
            'table_name': model_class.__tablename__,
            'fields': {}
        }
        
        # Process regular columns
        for column in inspector.columns:
            field_config = FormFieldConfig(column.name, {
                'column': column,
                'is_relationship': False
            })
            model_info['fields'][column.name] = field_config
        
        # Process relationships (Foreign Keys)
        for rel_name, relationship_obj in inspector.relationships.items():
            # Only include many-to-one relationships (foreign keys)
            if relationship_obj.direction.name in ['MANYTOONE', 'ONETOONE']:
                field_config = FormFieldConfig(rel_name, {
                    'relationship': relationship_obj,
                    'is_relationship': True
                })
                model_info['fields'][rel_name] = field_config
        
        return model_info
    
    def _generate_field_html(self, field_config: FormFieldConfig, 
                            overrides: Dict[str, Any] = None) -> str:
        """Generate HTML for a single form field"""
        overrides = overrides or {}
        
        field_type = overrides.get('type', field_config.field_type)
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Skip hidden fields (like UUID)
        if field_type == 'hidden':
            return f'<input type="hidden" id="{field_id}" name="{field_name}">'
        
        # Build field based on type
        if field_type == 'checkbox':
            return self._generate_checkbox_field(field_config, overrides)
        elif field_type == 'textarea':
            return self._generate_textarea_field(field_config, overrides)
        elif field_type == 'select':
            return self._generate_select_field(field_config, overrides)
        elif field_type == 'json':
            return self._generate_json_field(field_config, overrides)
        elif field_type == 'decimal':
            return self._generate_decimal_field(field_config, overrides)
        elif field_type == 'color':
            return self._generate_color_field(field_config, overrides)
        elif field_type == 'date':
            return self._generate_date_field(field_config, overrides)
        elif field_type == 'datetime-local':
            return self._generate_datetime_field(field_config, overrides)
        else:
            return self._generate_input_field(field_config, overrides)
    
    def _generate_input_field(self, field_config: FormFieldConfig, 
                             overrides: Dict[str, Any]) -> str:
        """Generate standard input field with proper validation"""
        field_type = overrides.get('type', field_config.field_type)
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build input attributes
        attrs = [
            f'type="{field_type}"',
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add placeholder if available
        placeholder = overrides.get('placeholder', field_config.placeholder_text)
        if placeholder:
            attrs.append(f'placeholder="{html.escape(placeholder)}"')
        
        # Add default value
        if field_config.default_value is not None:
            attrs.append(f'value="{html.escape(str(field_config.default_value))}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        input_html = f'<input {" ".join(attrs)}>'
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=input_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _generate_decimal_field(self, field_config: FormFieldConfig, 
                               overrides: Dict[str, Any]) -> str:
        """Generate decimal/float input field with proper step and validation"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build input attributes for decimal
        attrs = [
            f'type="number"',
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"',
            f'step="any"'  # Allow any decimal precision
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add placeholder
        placeholder = overrides.get('placeholder', field_config.placeholder_text)
        if placeholder:
            attrs.append(f'placeholder="{html.escape(placeholder)}"')
        
        # Add default value
        if field_config.default_value is not None:
            attrs.append(f'value="{field_config.default_value}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        input_html = f'<input {" ".join(attrs)}>'
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=input_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    def _generate_color_field(self, field_config: FormFieldConfig, 
                             overrides: Dict[str, Any]) -> str:
        """Generate color picker field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build color input with preview
        attrs = [
            f'type="color"',
            f'class="form-control form-control-color"',
            f'id="{field_id}"',
            f'name="{field_name}"',
            f'style="width: 60px; height: 40px;"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Default color value
        default_color = field_config.default_value or '#000000'
        attrs.append(f'value="{default_color}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        # Create color input with text input for hex value
        color_html = f'''
        <div class="input-group">
            <input {" ".join(attrs)}>
            <input type="text" class="form-control" id="{field_id}_hex" 
                   placeholder="#000000" pattern="^#[0-9A-Fa-f]{{6}}$"
                   title="Enter hex color code (e.g., #FF0000)"
                   value="{default_color}">
        </div>
        <div class="form-text">
            <i class="bi bi-palette"></i> Pick a color or enter hex code
        </div>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=color_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _generate_date_field(self, field_config: FormFieldConfig, 
                            overrides: Dict[str, Any]) -> str:
        """Generate date picker field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build date input attributes
        attrs = [
            f'type="date"',
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add date constraints if specified in overrides
        if 'min_date' in overrides:
            attrs.append(f'min="{overrides["min_date"]}"')
        if 'max_date' in overrides:
            attrs.append(f'max="{overrides["max_date"]}"')
        
        # Add default value if it's a date
        if field_config.default_value:
            if hasattr(field_config.default_value, 'strftime'):
                attrs.append(f'value="{field_config.default_value.strftime("%Y-%m-%d")}"')
            else:
                attrs.append(f'value="{field_config.default_value}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        date_html = f'''
        <input {" ".join(attrs)}>
        <div class="form-text">
            <i class="bi bi-calendar"></i> Select a date
        </div>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=date_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _generate_datetime_field(self, field_config: FormFieldConfig, 
                                overrides: Dict[str, Any]) -> str:
        """Generate datetime picker field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build datetime-local input attributes
        attrs = [
            f'type="datetime-local"',
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add datetime constraints if specified in overrides
        if 'min_datetime' in overrides:
            attrs.append(f'min="{overrides["min_datetime"]}"')
        if 'max_datetime' in overrides:
            attrs.append(f'max="{overrides["max_datetime"]}"')
        
        # Add default value if it's a datetime
        if field_config.default_value:
            if hasattr(field_config.default_value, 'strftime'):
                # Format for datetime-local input (YYYY-MM-DDTHH:MM)
                attrs.append(f'value="{field_config.default_value.strftime("%Y-%m-%dT%H:%M")}"')
            else:
                attrs.append(f'value="{field_config.default_value}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        datetime_html = f'''
        <input {" ".join(attrs)}>
        <div class="form-text">
            <i class="bi bi-calendar-event"></i> Select date and time
        </div>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=datetime_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
        """Generate textarea field with proper validation"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build textarea attributes
        attrs = [
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"',
            'rows="4"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add placeholder
        placeholder = overrides.get('placeholder', field_config.placeholder_text)
        if placeholder:
            attrs.append(f'placeholder="{html.escape(placeholder)}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{html.escape(str(value))}"')
        
        default_content = html.escape(str(field_config.default_value)) if field_config.default_value else ''
        textarea_html = f'<textarea {" ".join(attrs)}>{default_content}</textarea>'
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=textarea_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _generate_checkbox_field(self, field_config: FormFieldConfig, 
                                overrides: Dict[str, Any]) -> str:
        """Generate checkbox field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        checked = 'checked' if field_config.default_value else ''
        
        checkbox_html = f'''
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="{field_id}" name="{field_name}" {checked}>
            <label class="form-check-label" for="{field_id}">
                {field_config.description}
            </label>
        </div>'''
        
        return f'<div class="mb-3">{checkbox_html}</div>'
    
    def _generate_select_field(self, field_config: FormFieldConfig, 
                              overrides: Dict[str, Any]) -> str:
        """Generate select field for foreign key relationships"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Extract the related table/model name for the placeholder
        related_table = field_name.replace('_uuid', '').replace('_', ' ').title()
        
        # Build select with proper validation
        attrs = [
            f'class="form-select"',
            f'id="{field_id}"',
            f'name="{field_name}"'
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        # Add data attributes for dynamic loading
        attrs.append(f'data-related-table="{related_table.lower()}"')
        
        select_html = f'''
        <select {" ".join(attrs)}>
            <option value="">-- Select {related_table} --</option>
            <!-- Options will be populated dynamically via AJAX -->
        </select>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=select_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _generate_json_field(self, field_config: FormFieldConfig, 
                            overrides: Dict[str, Any]) -> str:
        """Generate JSON field with textarea and validation helper"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build textarea attributes for JSON
        attrs = [
            f'class="form-control font-monospace"',
            f'id="{field_id}"',
            f'name="{field_name}"',
            'rows="6"',
            'data-json-field="true"'  # For client-side JSON validation
        ]
        
        # Add validation attributes
        validation_attrs = field_config.validation_attributes
        for attr, value in validation_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        placeholder = overrides.get('placeholder', '{"key": "value"}')
        attrs.append(f'placeholder=\'{placeholder}\'')
        
        default_content = ''
        if field_config.default_value:
            if isinstance(field_config.default_value, (dict, list)):
                import json
                default_content = json.dumps(field_config.default_value, indent=2)
            else:
                default_content = str(field_config.default_value)
        
        textarea_html = f'''
        <textarea {" ".join(attrs)}>{html.escape(default_content)}</textarea>
        <div class="form-text">
            <i class="bi bi-info-circle"></i> Enter valid JSON data. 
            <span class="text-muted">Use proper quotes and syntax.</span>
        </div>
        <div class="invalid-feedback" id="{field_id}_json_error" style="display:none;">
            Invalid JSON format. Please check your syntax.
        </div>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=textarea_html,
            description=field_config.description,
            is_required=field_config.is_required,
            tooltip=field_config.tooltip_text
        )
    
    def _wrap_field_with_label(self, field_name: str, field_id: str, 
                              field_html: str, description: str, 
                              is_required: bool, tooltip: Optional[str] = None) -> str:
        """Wrap field with Bootstrap form group structure and tooltip"""
        required_asterisk = ' <span class="text-danger">*</span>' if is_required else ''
        
        # Add tooltip icon and data if tooltip text is available
        tooltip_html = ''
        if tooltip:
            tooltip_html = f'''
            <i class="bi bi-question-circle text-muted ms-1" 
               data-bs-toggle="tooltip" 
               data-bs-placement="top" 
               title="{html.escape(tooltip)}"
               style="cursor: help;"></i>'''
        
        return f'''
        <div class="mb-3">
            <label for="{field_id}" class="form-label">
                {description}{required_asterisk}{tooltip_html}
            </label>
            {field_html}
        </div>'''
    
    def _build_complete_form(self, form_id: str, form_title: str, 
                            fields_html: List[str], include_submit: bool) -> str:
        """Build complete Bootstrap form structure with validation scripts"""
        fields_joined = '\n'.join(fields_html)
        
        submit_buttons = ''
        if include_submit:
            submit_buttons = '''
            <div class="mb-3">
                <button type="submit" class="btn btn-primary me-2">
                    <i class="bi bi-check-lg"></i> Save
                </button>
                <button type="button" class="btn btn-secondary">
                    <i class="bi bi-x-lg"></i> Cancel
                </button>
            </div>'''
        
        # Add JavaScript for tooltips, JSON validation, and color picker sync
        validation_script = '''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize Bootstrap tooltips
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            
            // Color picker and hex input synchronization
            document.querySelectorAll('input[type="color"]').forEach(function(colorInput) {
                const hexInput = document.getElementById(colorInput.id + '_hex');
                if (hexInput) {
                    // Update hex when color picker changes
                    colorInput.addEventListener('input', function() {
                        hexInput.value = this.value.toUpperCase();
                    });
                    
                    // Update color picker when hex input changes
                    hexInput.addEventListener('input', function() {
                        const hexValue = this.value;
                        if (/^#[0-9A-Fa-f]{6}$/.test(hexValue)) {
                            colorInput.value = hexValue;
                            this.classList.remove('is-invalid');
                            this.classList.add('is-valid');
                        } else {
                            this.classList.remove('is-valid');
                            this.classList.add('is-invalid');
                        }
                    });
                    
                    // Validate hex on blur
                    hexInput.addEventListener('blur', function() {
                        const hexValue = this.value;
                        if (hexValue && !/^#[0-9A-Fa-f]{6}$/.test(hexValue)) {
                            this.classList.add('is-invalid');
                        }
                    });
                }
            });
            
            // JSON field validation
            document.querySelectorAll('[data-json-field="true"]').forEach(function(field) {
                field.addEventListener('blur', function() {
                    const value = this.value.trim();
                    const errorDiv = document.getElementById(this.id + '_json_error');
                    
                    if (value === '') {
                        this.classList.remove('is-invalid');
                        errorDiv.style.display = 'none';
                        return;
                    }
                    
                    try {
                        JSON.parse(value);
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                        errorDiv.style.display = 'none';
                    } catch (e) {
                        this.classList.remove('is-valid');
                        this.classList.add('is-invalid');
                        errorDiv.style.display = 'block';
                        errorDiv.textContent = 'Invalid JSON: ' + e.message;
                    }
                });
            });
            
            // Date/DateTime field enhancements
            document.querySelectorAll('input[type="date"], input[type="datetime-local"]').forEach(function(field) {
                // Add today button for date fields
                if (field.type === 'date') {
                    const todayBtn = document.createElement('button');
                    todayBtn.type = 'button';
                    todayBtn.className = 'btn btn-outline-secondary btn-sm mt-1';
                    todayBtn.innerHTML = '<i class="bi bi-calendar-day"></i> Today';
                    todayBtn.addEventListener('click', function() {
                        field.value = new Date().toISOString().split('T')[0];
                    });
                    field.parentNode.appendChild(todayBtn);
                }
                
                // Add now button for datetime fields
                if (field.type === 'datetime-local') {
                    const nowBtn = document.createElement('button');
                    nowBtn.type = 'button';
                    nowBtn.className = 'btn btn-outline-secondary btn-sm mt-1';
                    nowBtn.innerHTML = '<i class="bi bi-clock"></i> Now';
                    nowBtn.addEventListener('click', function() {
                        const now = new Date();
                        const offset = now.getTimezoneOffset() * 60000;
                        const localTime = new Date(now.getTime() - offset);
                        field.value = localTime.toISOString().slice(0, 16);
                    });
                    field.parentNode.appendChild(nowBtn);
                }
            });
            
            // Form validation on submit
            document.getElementById('{{form_id}}').addEventListener('submit', function(e) {
                let hasErrors = false;
                
                // Check JSON fields
                this.querySelectorAll('[data-json-field="true"]').forEach(function(field) {
                    if (field.classList.contains('is-invalid')) {
                        hasErrors = true;
                    }
                });
                
                // Check hex color fields
                this.querySelectorAll('input[pattern*="A-Fa-f"]').forEach(function(field) {
                    if (field.classList.contains('is-invalid')) {
                        hasErrors = true;
                    }
                });
                
                if (hasErrors) {
                    e.preventDefault();
                    alert('Please fix validation errors before submitting.');
                }
            });
        });
        </script>'''.replace('{{form_id}}', form_id)
        
        return f'''
<div class="card">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="bi bi-pencil-square"></i> {form_title}
        </h5>
    </div>
    <div class="card-body">
        <form id="{form_id}" method="post" novalidate>
            {fields_joined}
            {submit_buttons}
        </form>
    </div>
</div>
{validation_script}'''


# Usage example function
def generate_model_forms():
    """Example usage of the form generator"""
    
    # Import your models (assuming they're available)
    # from app._system.templates.page_model import Page
    # from app._system.templates.template_model import Template
    
    generator = BootstrapFormGenerator()
    
    # Example field overrides for specific customizations
    page_field_overrides = {
        'slug': {
            'attributes': {
                'pattern': '[a-z0-9-]+',
                'title': 'Only lowercase letters, numbers, and hyphens allowed'
            }
        },
        'meta_description': {
            'attributes': {
                'placeholder': 'Brief description for search engines (150-160 characters)'
            }
        },
        'published': {
            'type': 'checkbox'
        },
        'publish_date': {
            'min_datetime': '2020-01-01T00:00',
            'max_datetime': '2030-12-31T23:59'
        },
        'expire_date': {
            'min_datetime': '2020-01-01T00:00'
        }
    }
    
    # Example for template with color fields
    template_field_overrides = {
        'primary_color': {
            'attributes': {
                'data-color-role': 'primary'
            }
        },
        'background_color': {
            'attributes': {
                'data-color-role': 'background'
            }
        }
    }
    
    # Generate form for Page model
    # page_form_html = generator.generate_form_html(
    #     Page, 
    #     form_id="page_form",
    #     form_title="Create/Edit Page",
    #     field_overrides=page_field_overrides
    # )
    
    # Generate form for Template model  
    # template_form_html = generator.generate_form_html(
    #     Template,
    #     form_id="template_form", 
    #     form_title="Create/Edit Template"
    # )
    
    # return page_form_html, template_form_html
    
    return "Form generation functions ready - uncomment model imports to use"


if __name__ == "__main__":
    # Example of how to use the generator
    result = generate_model_forms()
    print(result)

        elif 'slug' in self.field_name.lower():
            attrs['pattern'] = r'^[a-z0-9-]+


class BootstrapFormGenerator:
    """Generates Bootstrap HTML forms from SQLAlchemy models"""
    
    def __init__(self, bootstrap_version: str = "5"):
        self.bootstrap_version = bootstrap_version
        self.excluded_fields = {'uuid', 'created_at', 'updated_at', 'is_active'}
        
    def generate_form_html(self, model_class: Type, 
                          form_id: str = None,
                          form_title: str = None,
                          include_submit: bool = True,
                          field_overrides: Dict[str, Dict[str, Any]] = None) -> str:
        """Generate complete Bootstrap form HTML for a model"""
        
        form_id = form_id or f"{model_class.__name__.lower()}_form"
        form_title = form_title or f"{model_class.__name__} Form"
        field_overrides = field_overrides or {}
        
        # Get model information
        model_info = self._introspect_model(model_class)
        
        # Generate form fields
        form_fields_html = []
        for field_name, field_config in model_info['fields'].items():
            if field_name in self.excluded_fields:
                continue
                
            # Apply any field overrides
            override_config = field_overrides.get(field_name, {})
            field_html = self._generate_field_html(field_config, override_config)
            form_fields_html.append(field_html)
        
        # Combine into complete form
        form_html = self._build_complete_form(
            form_id=form_id,
            form_title=form_title,
            fields_html=form_fields_html,
            include_submit=include_submit
        )
        
        return form_html
    
    def _introspect_model(self, model_class: Type) -> Dict[str, Any]:
        """Introspect SQLAlchemy model to extract field information"""
        inspector = sqlalchemy_inspect(model_class)
        
        model_info = {
            'table_name': model_class.__tablename__,
            'fields': {}
        }
        
        # Process regular columns
        for column in inspector.columns:
            field_config = FormFieldConfig(column.name, {
                'column': column,
                'is_relationship': False
            })
            model_info['fields'][column.name] = field_config
        
        # Process relationships
        for rel_name, relationship_obj in inspector.relationships.items():
            # Skip back_populates relationships to avoid duplicates
            if hasattr(relationship_obj, 'back_populates') and relationship_obj.back_populates:
                continue
                
            field_config = FormFieldConfig(rel_name, {
                'relationship': relationship_obj,
                'is_relationship': True
            })
            model_info['fields'][rel_name] = field_config
        
        return model_info
    
    def _generate_field_html(self, field_config: FormFieldConfig, 
                            overrides: Dict[str, Any] = None) -> str:
        """Generate HTML for a single form field"""
        overrides = overrides or {}
        
        field_type = overrides.get('type', field_config.field_type)
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Skip hidden fields (like UUID)
        if field_type == 'hidden':
            return f'<input type="hidden" id="{field_id}" name="{field_name}">'
        
        # Build field based on type
        if field_type == 'checkbox':
            return self._generate_checkbox_field(field_config, overrides)
        elif field_type == 'textarea':
            return self._generate_textarea_field(field_config, overrides)
        elif field_type == 'select':
            return self._generate_select_field(field_config, overrides)
        elif field_type == 'json':
            return self._generate_json_field(field_config, overrides)
        else:
            return self._generate_input_field(field_config, overrides)
    
    def _generate_input_field(self, field_config: FormFieldConfig, 
                             overrides: Dict[str, Any]) -> str:
        """Generate standard input field"""
        field_type = overrides.get('type', field_config.field_type)
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build input attributes
        attrs = [
            f'type="{field_type}"',
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"'
        ]
        
        if field_config.is_required:
            attrs.append('required')
        
        if field_config.max_length:
            attrs.append(f'maxlength="{field_config.max_length}"')
        
        if field_config.default_value is not None:
            attrs.append(f'value="{field_config.default_value}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{value}"')
        
        input_html = f'<input {" ".join(attrs)}>'
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=input_html,
            description=field_config.description,
            is_required=field_config.is_required
        )
    
    def _generate_textarea_field(self, field_config: FormFieldConfig, 
                                overrides: Dict[str, Any]) -> str:
        """Generate textarea field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build textarea attributes
        attrs = [
            f'class="form-control"',
            f'id="{field_id}"',
            f'name="{field_name}"',
            'rows="4"'
        ]
        
        if field_config.is_required:
            attrs.append('required')
        
        if field_config.max_length:
            attrs.append(f'maxlength="{field_config.max_length}"')
        
        # Add any override attributes
        for attr, value in overrides.get('attributes', {}).items():
            attrs.append(f'{attr}="{value}"')
        
        default_content = field_config.default_value or ''
        textarea_html = f'<textarea {" ".join(attrs)}>{default_content}</textarea>'
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=textarea_html,
            description=field_config.description,
            is_required=field_config.is_required
        )
    
    def _generate_checkbox_field(self, field_config: FormFieldConfig, 
                                overrides: Dict[str, Any]) -> str:
        """Generate checkbox field"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        checked = 'checked' if field_config.default_value else ''
        
        checkbox_html = f'''
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="{field_id}" name="{field_name}" {checked}>
            <label class="form-check-label" for="{field_id}">
                {field_config.description}
            </label>
        </div>'''
        
        return f'<div class="mb-3">{checkbox_html}</div>'
    
    def _generate_select_field(self, field_config: FormFieldConfig, 
                              overrides: Dict[str, Any]) -> str:
        """Generate select field for relationships"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        # Build select with placeholder option
        select_html = f'''
        <select class="form-select" id="{field_id}" name="{field_name}">
            <option value="">-- Select {field_config.description} --</option>
            <!-- Options will be populated dynamically -->
        </select>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=select_html,
            description=field_config.description,
            is_required=field_config.is_required
        )
    
    def _generate_json_field(self, field_config: FormFieldConfig, 
                            overrides: Dict[str, Any]) -> str:
        """Generate JSON field with textarea and helper text"""
        field_name = field_config.field_name
        field_id = f"id_{field_name}"
        
        textarea_html = f'''
        <textarea class="form-control font-monospace" id="{field_id}" name="{field_name}" 
                  rows="6" placeholder='{{"key": "value"}}'></textarea>
        <div class="form-text">Enter valid JSON data</div>'''
        
        return self._wrap_field_with_label(
            field_name=field_name,
            field_id=field_id,
            field_html=textarea_html,
            description=field_config.description,
            is_required=field_config.is_required
        )
    
    def _wrap_field_with_label(self, field_name: str, field_id: str, 
                              field_html: str, description: str, 
                              is_required: bool) -> str:
        """Wrap field with Bootstrap form group structure"""
        required_asterisk = ' <span class="text-danger">*</span>' if is_required else ''
        
        return f'''
        <div class="mb-3">
            <label for="{field_id}" class="form-label">{description}{required_asterisk}</label>
            {field_html}
        </div>'''
    
    def _build_complete_form(self, form_id: str, form_title: str, 
                            fields_html: List[str], include_submit: bool) -> str:
        """Build complete Bootstrap form structure"""
        fields_joined = '\n'.join(fields_html)
        
        submit_buttons = ''
        if include_submit:
            submit_buttons = '''
            <div class="mb-3">
                <button type="submit" class="btn btn-primary me-2">Save</button>
                <button type="button" class="btn btn-secondary">Cancel</button>
            </div>'''
        
        return f'''
<div class="card">
    <div class="card-header">
        <h5 class="card-title mb-0">{form_title}</h5>
    </div>
    <div class="card-body">
        <form id="{form_id}" method="post">
            {fields_joined}
            {submit_buttons}
        </form>
    </div>
</div>'''


# Usage example function
def generate_model_forms():
    """Example usage of the form generator"""
    
    # Import your models (assuming they're available)
    # from app._system.templates.page_model import Page
    # from app._system.templates.template_model import Template
    
    generator = BootstrapFormGenerator()
    
    # Example field overrides for specific customizations
    page_field_overrides = {
        'slug': {
            'attributes': {
                'pattern': '[a-z0-9-]+',
                'title': 'Only lowercase letters, numbers, and hyphens allowed'
            }
        },
        'meta_description': {
            'attributes': {
                'placeholder': 'Brief description for search engines (150-160 characters)'
            }
        },
        'published': {
            'type': 'checkbox'
        }
    }
    
    # Generate form for Page model
    # page_form_html = generator.generate_form_html(
    #     Page, 
    #     form_id="page_form",
    #     form_title="Create/Edit Page",
    #     field_overrides=page_field_overrides
    # )
    
    # Generate form for Template model  
    # template_form_html = generator.generate_form_html(
    #     Template,
    #     form_id="template_form", 
    #     form_title="Create/Edit Template"
    # )
    
    # return page_form_html, template_form_html
    
    return "Form generation functions ready - uncomment model imports to use"


if __name__ == "__main__":
    # Example of how to use the generator
    result = generate_model_forms()
    print(result)

            attrs['title'] = 'Only lowercase letters, numbers, and hyphens allowed'
            
        return attrs

