class FormGenerator:
    """Generate HTML forms from Miner metadata"""

    def __init__(self, metadata, prefix="", show_required_badge=True, show_optional_badge=True):
        self.metadata = metadata
        self.model_info = metadata.get('model', {})
        self.fields = metadata.get('fields', {})
        self.relationships = metadata.get('relationships', {})
        self.validation = metadata.get('validation', {})
        self.form_config = metadata.get('form_config', {})
        self.prefix = prefix  # Prefix for form element IDs
        self.show_required_badge = show_required_badge  # Show "Required" badge
        self.show_optional_badge = show_optional_badge  # Show "Optional" badge

    def generate_form(self, action_url="/api/data", include_relationships=True, form_mode="both", 
                     include_wrapper=True):
        """
        Generate complete HTML form with optional wrapper and scripts

        Args:
            action_url: URL for form submission
            include_relationships: Whether to include relationship sections
            form_mode: "create", "edit", or "both" - determines which fields to include
            include_wrapper: Whether to include the container wrapper and title
        """
        html = []

        # Add wrapper if requested
        if include_wrapper:
            html.extend(self._generate_wrapper_start())

        # Form header
        form_id = f"{self.prefix}{self.model_info['name'].lower()}_form"
        html.append(f'<form id="{form_id}" ')
        html.append(f'      class="needs-validation" novalidate')
        html.append(f'      data-model="{self.model_info["name"]}"')
        if self.prefix:
            html.append(f'      data-prefix="{self.prefix}"')
        html.append('>')


        # Hidden fields (only ID for edit mode)
        if form_mode in ["edit", "both"]:
            html.extend(self._generate_hidden_fields())
        
        html.append('')

        # Separate fields by type
        regular_fields = []
        boolean_fields = []

        # Get field order
        field_order = self.form_config.get('field_order', [])

        for field_name in field_order:
            if field_name not in self.fields:
                continue

            field = self.fields[field_name]

            # Skip relationships in create mode
            if form_mode == "create" and field_name in self.relationships:
                continue

            # Check if field should be included
            if not self._should_include_field(field_name, field, form_mode):
                continue

            # Separate boolean fields from others
            if field.get('type') == 'checkbox':
                boolean_fields.append((field_name, field))
            else:
                regular_fields.append((field_name, field))

        # Generate regular fields
        if regular_fields:
            for field_name, field in regular_fields:
                html.extend(self._generate_field(field_name, field, form_mode))
                html.append('')

        # Generate boolean fields in a grouped section
        if boolean_fields:
            html.extend(self._generate_boolean_section(boolean_fields, form_mode))

        # Generate relationship sections only in edit mode
        if include_relationships and form_mode == "edit" and self.form_config.get('inline_models'):
            html.extend(self._generate_relationship_sections())

        # Form buttons
        html.extend(self._generate_form_buttons())
        
        
        html.append('</form>')

        html.extend(self._generate_scripts())
            
        # Close wrapper if included
        if include_wrapper:
            html.extend(self._generate_wrapper_end())


        return '\n'.join(html)

    def _generate_wrapper_start(self):
        """Generate the opening wrapper HTML"""
        model_name = self.model_info["name"]
        html = []
        
        html.append('{% block title %}{% if id %}Edit{% else %}New{% endif %} ' + model_name + '{% endblock %}')
        html.append('')
        html.append('{% block content %}')
        html.append('<div class="container-fluid">')
        html.append('  <div class="row">')
        html.append('    <div class="col-lg-8 col-md-10 col-sm-12">')
        html.append('      <h2 class="mb-4">')
        html.append('        {% if id %}')
        html.append(f'          Edit {model_name}')
        html.append('        {% else %}')
        html.append(f'          Create New {model_name}')
        html.append('        {% endif %}')
        html.append('      </h2>')
        html.append('')
        
        return html

    def _generate_wrapper_end(self):
        """Generate the closing wrapper HTML"""
        html = []
        
        html.append('    </div>')
        html.append('  </div>')
        html.append('</div>')
        html.append('{% endblock %}')
        html.append('')
        
        return html

    
    def _should_include_field(self, field_name, field, form_mode):
        """Determine if a field should be included based on form mode"""
        # Always exclude ID field - it's handled separately as a hidden input
        if field_name == 'id':
            return False
            
        # Fields that should never be in create forms
        auto_create_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'deleted_at', 'version', 'last_modified_by'
        ]

        # Fields that should never be in any form
        never_include = ['password_hash', 'salt', 'deleted_at']

        # Check if field should be excluded
        if field_name in never_include:
            return False

        if field_name in self.form_config.get('excluded_fields', []):
            return False

        if field.get('hidden'):
            return False

        # For create mode, exclude auto-populated fields
        if form_mode == "create":
            if field_name in auto_create_fields:
                return False
            if field.get('readonly'):
                return False
            # Skip fields with server-side defaults (like timestamps)
            if field.get('default') and 'function' in str(field.get('default', '')):
                return False

        # For edit mode, include readonly fields but they'll be displayed as readonly
        elif form_mode == "edit":
            # Still exclude certain fields even in edit mode
            if field_name in ['password_hash', 'salt']:
                return False

        return True

    def _generate_hidden_fields(self):
        """Generate hidden input fields - only for edit mode"""
        html = []

        # Only include ID as hidden field with prefix
        if 'id' in self.fields:
            html.append(f'  <input type="hidden" id="{self.prefix}id" name="id" value="{{{{ id | default("", true) }}}}" />')

        return html

    def debug_field_requirements(self):
        """Debug method to show field requirements"""
        print("\n=== Field Requirements Debug ===")
        print(f"Model: {self.model_info.get('name', 'Unknown')}")
        print("\nFields:")
        
        for field_name, field in self.fields.items():
            validation = self.validation.get(field_name, {})
            
            # Check validation required flag
            validation_required = validation.get('required', None)
            
            # Check nullable flag
            nullable = field.get('nullable', None)
            
            # Determine final required status
            if 'required' in validation:
                required = validation['required']
                source = "validation"
            else:
                # If nullable is False, field is required
                if nullable is False:
                    required = True
                    source = "nullable=False"
                else:
                    required = False
                    source = f"nullable={nullable}"
            
            print(f"\n  {field_name}:")
            print(f"    - nullable: {nullable}")
            print(f"    - validation.required: {validation_required}")
            print(f"    - final required: {required} (from {source})")
            print(f"    - type: {field.get('type', 'text')}")
        
        print("\n" + "="*40 + "\n")

    def _humanize(self, text):
        """Convert snake_case to Human Readable"""
        return text.replace('_', ' ').title()

    def _camel_case(self, text):
        """Convert snake_case to CamelCase"""
        parts = text.split('_')
        return ''.join(part.capitalize() for part in parts)

    def _get_field_default(self, field_name, field):
        """Get the default value for a field, handling different types"""
        default = field.get('default', None)
        
        # Skip server-side defaults (functions)
        if default and 'function' in str(default):
            return None
            
        # For boolean fields, ensure proper format
        if field.get('type') == 'checkbox' and default is not None:
            return 'true' if default else 'false'
            
        # For other types, return as-is
        return default

    def _generate_field(self, field_name, field, form_mode="both"):
        """Generate a single form field"""
        html = []

        # Get validation rules for this field
        validation = self.validation.get(field_name, {})
        
        # Determine if field is required
        # Check validation first, then fall back to nullable property
        if 'required' in validation:
            required = validation['required']
        else:
            # If nullable is False, field is required
            # Default to nullable=True if not specified
            nullable = field.get('nullable', True)
            required = not nullable
            
        readonly = field.get('readonly', False)

        # Make timestamp fields readonly in edit mode
        if form_mode == "edit" and field_name in ['created_at', 'updated_at']:
            readonly = True

        # Use prefix for ID but not name
        field_id = f"{self.prefix}{field_name}"

        # Start form group
        html.append('  <div class="mb-3">')

        # Build label with status indicators
        label_html = f'    <label for="{field_id}" class="form-label'
        if required:
            label_html += ' required'
        label_html += f'">{field["label"]}'

        # Add status indicator
        status_parts = []
        if readonly:
            status_parts.append('<span class="badge bg-secondary ms-2">Readonly</span>')
        elif required and self.show_required_badge:
            status_parts.append('<span class="badge bg-danger ms-2">Required</span>')
        elif not required and self.show_optional_badge:
            status_parts.append('<span class="badge bg-info ms-2">Optional</span>')

        label_html += ' ' + ''.join(status_parts)
        label_html += '</label>'
        html.append(label_html)

        # Generate appropriate input based on type
        input_html = self._generate_input(field_name, field, validation, form_mode)
        html.extend(input_html)

        # Help text
        if field.get('help_text'):
            html.append(f'    <div class="form-text">{field["help_text"]}</div>')

        # Validation feedback
        html.append('    <div class="invalid-feedback"></div>')

        html.append('  </div>')

        return html

    def _generate_boolean_section(self, boolean_fields, form_mode="both"):
        """Generate a grouped section for boolean/checkbox fields"""
        html = []

        html.append('  <div class="card mb-4">')
        html.append('    <div class="card-header">')
        html.append('      <h6 class="mb-0">Options & Settings</h6>')
        html.append('    </div>')
        html.append('    <div class="card-body">')
        html.append('      <div class="row">')

        # Arrange checkboxes in columns
        for i, (field_name, field) in enumerate(boolean_fields):
            # Use 2 columns on medium screens, 1 on small
            if i % 2 == 0 and i > 0:
                html.append('      </div>')
                html.append('      <div class="row">')

            html.append('        <div class="col-md-6">')

            # Get validation rules
            validation = self.validation.get(field_name, {})
            
            # Determine if field is required
            if 'required' in validation:
                required = validation['required']
            else:
                nullable = field.get('nullable', True)
                required = not nullable
                
            readonly = field.get('readonly', False)

            # Use prefix for ID but not name
            field_id = f"{self.prefix}{field_name}"

            # Generate checkbox
            attrs = []
            attrs.append(f'id="{field_id}"')
            attrs.append(f'name="{field_name}"')
            attrs.append('type="checkbox"')
            attrs.append('class="form-check-input"')

            if readonly:
                attrs.append('disabled')

            html.append('          <div class="form-check">')
            html.append(f'            <input {" ".join(attrs)}')
            
            # Get default value for checkboxes
            default_value = self._get_field_default(field_name, field)
            
            # Use Jinja2 conditional for checked state
            # For new records (no id), use the default value
            # For existing records, use the actual field value
            if default_value == 'true':
                html.append(f'                   {{% if id %}}{{% if {field_name} %}}checked{{% endif %}}{{% else %}}checked{{% endif %}}>')
            else:
                html.append(f'                   {{% if {field_name} %}}checked{{% endif %}}>')
                
            html.append(f'            <label class="form-check-label" for="{field_id}">')
            html.append(f'              <strong>{field["label"]}</strong>')

            # Add status badge for checkboxes too (respecting the flags)
            # Note: Checkboxes are never "required" in the UI sense since they can be unchecked
            if readonly:
                html.append('              <span class="badge bg-secondary ms-2">Readonly</span>')

            if field.get('help_text'):
                html.append(f'              <br><small class="text-muted">{field["help_text"]}</small>')
            html.append('            </label>')
            html.append('          </div>')

            html.append('        </div>')

        html.append('      </div>')
        html.append('    </div>')
        html.append('  </div>')
        html.append('')

        return html

    def _generate_input(self, field_name, field, validation, form_mode="both"):
        """Generate the appropriate input element"""
        html = []
        field_type = field.get('type', 'text')
        
        # Determine if field is required
        if 'required' in validation:
            required = validation['required']
        else:
            nullable = field.get('nullable', True)
            required = not nullable
            
        readonly = field.get('readonly', False)

        # Make timestamp fields readonly in edit mode
        if form_mode == "edit" and field_name in ['created_at', 'updated_at']:
            readonly = True

        # Use prefix for ID but not name
        field_id = f"{self.prefix}{field_name}"

        # Get default value for the field
        default_value = self._get_field_default(field_name, field)

        # Common attributes
        attrs = []
        attrs.append(f'id="{field_id}"')
        attrs.append(f'name="{field_name}"')

        # Only add 'required' if not a checkbox
        if required and field_type != 'checkbox':
            attrs.append('required')
        if readonly:
            attrs.append('readonly')

        # Handle foreign keys
        if field.get('is_foreign_key'):
            fk = field.get('foreign_key', {})
            model = fk.get('model', '')

            html.append(f'    <select class="form-select fk-select" {" ".join(attrs)} ')
            html.append(f'            data-model="{model}" ')
            html.append(f'            data-display-field="name">')
            html.append(f'      <option value="">Select {field["label"]}...</option>')
            html.append('      <!-- Options loaded dynamically -->')
            html.append('    </select>')

        # Handle different input types
        elif field_type == 'textarea':
            rows = 3
            if 'description' in field_name:
                rows = 4
            html.append(f'    <textarea class="form-control" {" ".join(attrs)} rows="{rows}"')
            if field.get('placeholder'):
                html.append(f'              placeholder="{field["placeholder"]}"')
            
            # Use default value for new records
            if default_value is not None:
                html.append(f'>{{{{ {field_name} if id else "{default_value}" }}}}</textarea>')
            else:
                html.append(f'>{{{{ {field_name} | default("", true) }}}}</textarea>')

        elif field_type == 'checkbox':
            html.append('    <div class="form-check">')
            html.append(f'      <input type="checkbox" class="form-check-input" {" ".join(attrs)}')
            
            # Handle checkbox checked state with defaults
            if default_value == 'true':
                html.append(f'             {{% if id %}}{{% if {field_name} %}}checked{{% endif %}}{{% else %}}checked{{% endif %}}>')
            else:
                html.append(f'             {{% if {field_name} %}}checked{{% endif %}}>')
                
            html.append(f'      <label class="form-check-label" for="{field_id}">')
            html.append(f'        {field.get("help_text", "Enable this option")}')
            html.append('      </label>')
            html.append('    </div>')

        elif field_type == 'date':
            html.append(f'    <input type="date" class="form-control" {" ".join(attrs)}')
            if default_value is not None:
                html.append(f'           value="{{{{ {field_name} if id else "{default_value}" }}}}">')
            else:
                html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        elif field_type == 'datetime-local':
            html.append(f'    <input type="datetime-local" class="form-control" {" ".join(attrs)}')
            # Format datetime for HTML input
            if readonly:
                html.append(f'           value="{{{{ {field_name} | datetime_to_local if {field_name} else "" }}}}">')
            else:
                if default_value is not None:
                    html.append(f'           value="{{{{ {field_name} if id else "{default_value}" }}}}">')
                else:
                    html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        elif field_type == 'number':
            html.append(f'    <input type="number" class="form-control" {" ".join(attrs)}')
            if validation.get('precision'):
                html.append(f'           step="0.{"0" * (validation["precision"] - validation.get("scale", 0)) + "1"}"')
            if default_value is not None:
                html.append(f'           value="{{{{ {field_name} if id else {default_value} }}}}">')
            else:
                html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        elif field_type == 'email':
            html.append(f'    <input type="email" class="form-control" {" ".join(attrs)}')
            if field.get('placeholder'):
                html.append(f'           placeholder="{field["placeholder"]}"')
            if validation.get('max_length'):
                html.append(f'           maxlength="{validation["max_length"]}"')
            if default_value is not None:
                html.append(f'           value="{{{{ {field_name} if id else "{default_value}" }}}}">')
            else:
                html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        elif field_type == 'url':
            html.append(f'    <input type="url" class="form-control" {" ".join(attrs)}')
            if field.get('placeholder'):
                html.append(f'           placeholder="{field["placeholder"]}"')
            if default_value is not None:
                html.append(f'           value="{{{{ {field_name} if id else "{default_value}" }}}}">')
            else:
                html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        elif field_type == 'password':
            html.append(f'    <input type="password" class="form-control" {" ".join(attrs)}')
            html.append(f'           placeholder="Enter password">')

        else:  # Default text input
            html.append(f'    <input type="text" class="form-control" {" ".join(attrs)}')
            if field.get('placeholder'):
                html.append(f'           placeholder="{field["placeholder"]}"')
            if validation.get('max_length'):
                html.append(f'           maxlength="{validation["max_length"]}"')
            if validation.get('pattern'):
                html.append(f'           pattern="{validation["pattern"]}"')
                if validation.get('pattern_message'):
                    html.append(f'           title="{validation["pattern_message"]}"')
            if default_value is not None:
                html.append(f'           value="{{{{ {field_name} if id else "{default_value}" }}}}">')
            else:
                html.append(f'           value="{{{{ {field_name} | default("", true) }}}}">')

        return html

    def _generate_relationship_sections(self):
        """Generate inline relationship sections"""
        html = []

        for rel_name in self.form_config.get('inline_models', []):
            if rel_name not in self.relationships:
                continue

            rel = self.relationships[rel_name]

            # Only generate for owned relationships
            if not rel.get('is_owned'):
                continue

            # Use prefix for container ID
            container_id = f"{self.prefix}{rel_name}_container"

            html.append('  <div class="card mt-4">')
            html.append('    <div class="card-header">')
            html.append(f'      <h5 class="mb-0">{self._humanize(rel_name)}</h5>')
            html.append('    </div>')
            html.append('    <div class="card-body">')
            html.append(f'      <div id="{container_id}">')
            html.append('        <!-- Inline items will be loaded here -->')
            html.append('      </div>')
            html.append(f'      <button type="button" class="btn btn-sm btn-secondary mt-2" ')
            html.append(f'              onclick="add{self._camel_case(rel_name)}()">')
            html.append(f'        <i class="fas fa-plus"></i> Add {self._humanize(rel["model"])}')
            html.append('      </button>')
            html.append('    </div>')
            html.append('  </div>')
            html.append('')

        return html

    def _generate_form_buttons(self):
        """Generate form action buttons"""
        html = []

        html.append('  <div class="d-flex justify-content-between mt-4">')
        html.append('    <button type="button" class="btn btn-secondary" onclick="history.back()">')
        html.append('      <i class="fas fa-arrow-left"></i> Cancel')
        html.append('    </button>')
        html.append('    <div>')
        html.append('      <button type="submit" class="btn btn-primary" id="submit_btn">')
        html.append('        <i class="fas fa-save"></i> Save')
        html.append('      </button>')
        html.append('    </div>')
        html.append('  </div>')

        return html
    
    def _generate_scripts(self):
        """Generate the JavaScript for form handling"""
        model_name = self.model_info["name"]
        form_id = f"{self.prefix}{model_name.lower()}_form"
        
        html = []
        html.append('<script>')
        html.append('$(document).ready(function() {')
        html.append(f'  const form_id = "{form_id}";')
        html.append('  ')
        html.append('  // Try to initialize DataForm')
        html.append('  function init_form() {')
        html.append('    if (typeof DataForm !== "undefined") {')
        html.append("      new DataForm(form_id)")
        html.append('    } else {')
        html.append('      // Retry in 100ms if DataForm not loaded yet')
        html.append('      setTimeout(init_form, 100);')
        html.append('    }')
        html.append('  }')
        html.append('  ')
        html.append('  init_form();')
        html.append('});')
        html.append('</script>')
        
        return html