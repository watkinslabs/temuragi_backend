#!/usr/bin/env python3
"""
Report-based DataTable Configuration Generator
Generates JavaScript configuration for DataTableWrapper from existing Report records
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class ReportDataTableGenerator:
    """Generate DataTable configuration from existing Report records"""

    def __init__(self, session, logger=None):
        self.session = session
        self.logger = logger
        
        # Import and create ReportService instance
        try:
            from app.classes import ReportService
            self.report_service = ReportService(logger=logger)
        except Exception as e:
            self._log(f"Failed to import ReportService: {e}", level='error')
            self.report_service = None

    def _log(self, message: str, level: str = 'info'):
        """Log a message if logger is available"""
        if self.logger:
            getattr(self.logger, level)(message)

    def load_report_by_slug(self, slug: str):
        """Load a report by its slug"""
        from app.models import Report

        report = self.session.query(Report).filter_by(slug=slug).first()
        if not report:
            raise ValueError(f"Report with slug '{slug}' not found")

        return report

    def _generate_column_render(self, column) -> Optional[str]:
        """Generate render function based on column configuration"""

        # Check data type
        data_type_name = column.data_type.name if column.data_type else 'string'

        # If column has custom format string, use it
        if column.format_string:
            if '{' in column.format_string:
                # Python format string - convert to JS
                if column.format_string == '${:,.2f}':
                    return r'''function(data) {
                    return data ? '$' + parseFloat(data).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,') : '';
                }'''
                elif column.format_string == '{:.1%}':
                    return '''function(data) {
                    return data ? (parseFloat(data) * 100).toFixed(1) + '%' : '';
                }'''

        # Check if this is the first visible column (likely the "name" column)
        # Make first column clickable if it's a name-like column
        #if column.name in ['name', 'title', 'display_name', 'label']:
         #   return '''function(data, type, row) {
         #           return data;
         #       }'''

        # Handle different data types
        if data_type_name == 'boolean':
            return '''function(data) {
                    return data ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>';
                }'''

        elif data_type_name == 'date':
            return '''function(data) {
                    if (!data) return '';
                    const date = new Date(data);
                    if (isNaN(date)) return data;
                    return date.toISOString().split('T')[0];
                }'''

        elif data_type_name == 'datetime':
            return '''function(data) {
                    if (!data) return '';
                    const date = new Date(data);
                    if (isNaN(date)) return data;
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    const hours = String(date.getHours()).padStart(2, '0');
                    const minutes = String(date.getMinutes()).padStart(2, '0');
                    return `${year}-${month}-${day} ${hours}:${minutes}`;
                }'''

        elif data_type_name == 'json':
            return '''function(data) {
                    return data ? '<code>' + JSON.stringify(data).substring(0, 50) + '...</code>' : '';
                }'''

        elif data_type_name == 'url':
            return '''function(data) {
                    return data ? `<a href="${data}" target="_blank"><i class="fas fa-external-link-alt"></i> Link</a>` : '';
                }'''

        elif data_type_name == 'email':
            return '''function(data) {
                    return data ? `<a href="mailto:${data}">${data}</a>` : '';
                }'''

        elif data_type_name == 'money':
            return r'''function(data) {
                    return data ? '$' + parseFloat(data).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,') : '';
                }'''

        elif data_type_name == 'percentage':
            return '''function(data) {
                    return data ? parseFloat(data).toFixed(1) + '%' : '';
                }'''

        elif data_type_name == 'color':
            return '''function(data) {
                    return data ? `<span class="color-box" style="background-color: ${data}; width: 20px; height: 20px; display: inline-block; border: 1px solid #ccc;"></span> ${data}` : '';
                }'''

        elif data_type_name == 'html':
            return '''function(data) {
                    return data ? data : '';  // Allow HTML rendering
                }'''

        elif data_type_name == 'markdown':
            return '''function(data) {
                    // This would need a markdown parser
                    return data ? `<div class="markdown-preview">${data.substring(0, 100)}...</div>` : '';
                }'''

        # Check column name patterns
        if column.name in ['status', 'state']:
            return '''function(data) {
                    const statusColors = {
                        'active': 'success',
                        'inactive': 'secondary',
                        'pending': 'warning',
                        'completed': 'info',
                        'failed': 'danger',
                        'draft': 'secondary',
                        'published': 'success'
                    };
                    const color = statusColors[data?.toLowerCase()] || 'secondary';
                    return `<span class="badge bg-${color}">${data}</span>`;
                }'''

        # Text columns might need truncation
        if data_type_name in ['text', 'string']:
            # Check if we should truncate long text
            if column.options and column.options.get('truncate'):
                return '''function(data) {
                    return data ? data.substring(0, 100) + (data.length > 100 ? '...' : '') : '';
                }'''

        return None

    def _generate_column_config(self, column) -> Dict[str, Any]:
        """Generate column configuration from ReportColumn"""
        config = {
            'name': column.name,
            'order': column.order_index,
            'searchable': column.is_searchable,
            'label': column.display_name,
            'visible': column.is_visible,
            'sortable': column.is_sortable,
        }

        # Add data type format
        if column.data_type:
            data_type_name = column.data_type.name
            if data_type_name != 'string':
                config['format'] = data_type_name

        # Add alignment if specified
        if column.alignment and column.alignment != 'left':
            config['className'] = f'text-{column.alignment}'

        # Add width if specified
        if column.width:
            config['width'] = column.width

        # Add custom render function
        render_func = self._generate_column_render(column)
        if render_func:
            config['render'] = render_func

        # Add default content for all columns to handle nulls
        config['defaultContent'] = ''

        return config

    def _generate_filters_from_variables(self, report) -> List[Dict]:
        """Generate filters from report variables"""
        filters = []

        for variable in report.variables:
            # Skip system variables that shouldn't be filters
            var_type = variable.variable_type.name if variable.variable_type else 'text'

            # Skip the standard search_term and limit variables
            if variable.name in ['search_term', 'limit']:
                continue

            filter_config = {
                'id': f'{variable.name}_filter',
                'label': variable.display_name,
                'column': variable.name,
                'required': variable.is_required
            }

            # Map variable types to filter types
            if var_type == 'select':
                filter_config['type'] = 'select'
                if variable.options:
                    # Parse options if stored as JSON
                    try:
                        options = json.loads(variable.options) if isinstance(variable.options, str) else variable.options
                        filter_config['options'] = [{'value': opt.get('value', opt), 'text': opt.get('text', opt)}
                                                   for opt in options]
                    except:
                        filter_config['options'] = [{'value': '', 'text': 'All'}]

            elif var_type == 'date':
                filter_config['type'] = 'date'

            elif var_type == 'daterange' or (variable.name.endswith('_from') or variable.name.endswith('_to')):
                # Detect date range pairs
                base_name = variable.name.replace('_from', '').replace('_to', '')
                if not any(f['id'] == f'{base_name}_range' for f in filters):
                    filter_config = {
                        'id': f'{base_name}_range',
                        'label': f'{base_name.replace("_", " ").title()} Range',
                        'type': 'daterange',
                        'column': base_name
                    }
                else:
                    continue  # Skip the _to variable if we already added the range

            elif var_type == 'boolean':
                filter_config['type'] = 'select'
                filter_config['options'] = [
                    {'value': '', 'text': 'All'},
                    {'value': 'true', 'text': 'Yes'},
                    {'value': 'false', 'text': 'No'}
                ]

            elif var_type == 'number':
                filter_config['type'] = 'number'

            else:
                filter_config['type'] = 'text'

            # Add placeholder if available
            if variable.placeholder:
                filter_config['placeholder'] = variable.placeholder

            # Add default value if available
            if variable.default_value:
                filter_config['default'] = variable.default_value

            filters.append(filter_config)

        return filters

    def generate_datatable_config(self, report_slug: str,
                         data_url: Optional[str] = None,
                         show_actions: bool = False,
                         custom_actions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate DataTable configuration from a Report record

        Args:
            report_slug: Slug of the report to load
            data_url: Override the data URL (default: /api/report/{slug}/data)
            show_actions: Whether to show row actions
            custom_actions: Additional custom actions

        Returns:
            Dictionary containing the complete configuration
        """
        # Load the report with page_actions
        report = self.load_report_by_slug(report_slug)

        self._log(f"Generating DataTable config for report: {report.name}")

        # Convert page_actions to DataTable format
        actions = []
        if report.page_actions:
            self._log(f"Found {len(report.page_actions)} page actions for report")
            for action in sorted(report.page_actions, key=lambda a: a.order_index):
                action_config = {
                    'name': action.name,
                    'mode': action.mode or 'row',  # Default to 'row' if not specified
                    'action_type': action.action_type or 'htmx',  # Include action type
                    'url': action.url or action.url_for,
                    'icon': action.icon,
                    'data_index': action.data_index,
                    'color': action.color,
                    'title': action.display,
                }

                # Add confirmation if needed
                if action.confirm and action.confirm_message:
                    action_config['confirm'] = action.confirm_message

                # Add method if not GET
                if action.method and action.method != 'GET':
                    action_config['method'] = action.method.lower()

                # Add target if not _self
                if action.target and action.target != '_self':
                    action_config['target'] = action.target

                # Add javascript code if action type is javascript
                if action.action_type == 'javascript' and action.javascript_code:
                    action_config['javascript'] = action.javascript_code

                # Add headers and payload for API actions
                if action.action_type == 'api':
                    if action.headers:
                        action_config['headers'] = action.headers
                    if action.payload:
                        action_config['payload'] = action.payload

                actions.append(action_config)
                self._log(f"Added action: {action.name} (mode: {action.mode}, type: {action.action_type})")

        # Merge with custom_actions if provided
        if custom_actions:
            self._log(f"Merging {len(custom_actions)} custom actions")
            actions.extend(custom_actions)

        # Rest of the method remains the same...
        # Determine model name and data URL based on report type
        model_name = None
        
        # Always use miner.data unless explicitly overridden
        if not data_url:
            data_url = "{{ url_for('miner.data') }}"

        if report.is_model:
            self._log(f"Report {report.slug} is marked as model report", level='info')
            self._log(f"Model ID: {report.model_id}", level='info')

            if report.model_id and self.report_service:
                try:
                    model = self.report_service.get_model(report.model_id)
                    if model:
                        model_name = model.name
                        self._log(f"Found model: {model.name}", level='info')
                    else:
                        self._log(f"Model not found for model_id: {report.model_id}", level='error')
                        raise ValueError(f"Model not found for report {report.slug}")
                except Exception as e:
                    self._log(f"Error fetching model: {e}", level='error')
                    raise
            elif not self.report_service:
                self._log("Report service not available - cannot fetch model for model report", level='error')
                raise ValueError("Report service required for model reports")
            elif not report.model_id:
                self._log(f"Model report {report.slug} has no model_id", level='error')
                raise ValueError(f"Model report {report.slug} has no model_id")

        # Set model_name for non-model reports
        if not model_name:
            model_name = report.slug

        # Build column configurations
        columns = {}
        visible_columns = []

        # Sort columns by order_index
        sorted_columns = sorted(report.columns, key=lambda c: c.order_index)

        for column in sorted_columns:
            if not column.is_visible:
                continue

            col_config = self._generate_column_config(column)
            columns[column.name] = col_config
            visible_columns.append(column.name)

        # Generate filters from variables
        custom_filters = self._generate_filters_from_variables(report)

        # Build the configuration
        config = {
            'report_slug': report.slug,
            'report_name': report.name,
            'report_id': report.id,  # Add report ID
            'model_name': model_name,  # Add this for use in template
            'table_title': report.display or report.name,
            'table_description': report.description or f'Data from {report.name}',
            'columns': columns,
            'visible_columns': visible_columns,
            'data_url': data_url,
            'is_searchable': report.is_searchable,
            'is_ajax': report.is_ajax,
            'is_download_csv': report.is_download_csv,
            'is_download_xlsx': report.is_download_xlsx,
            'custom_filters': custom_filters,
            'id': report.id,
            'category': report.category,
            'tags': report.tags,
            'is_model': report.is_model,
            'actions': actions,
        }

        # Add actions if requested
        if show_actions:
            config['actions'] = ['view', 'export']

        if custom_actions:
            config['custom_actions'] = custom_actions

        # Add connection info
        if report.connection:
            config['connection_name'] = report.connection.name

        return config

    def generate_jinja_template(self, report_slug: str, **kwargs) -> str:
        """Generate a complete Jinja2 template for a report"""
        config = self.generate_datatable_config(report_slug, **kwargs)

        # Convert columns to JavaScript
        columns_js = self._dict_to_js_object(config['columns'], indent=24)
        filters_js = self._generate_filters_js(config['custom_filters']) if config['custom_filters'] else '[]'

        # Create safe variable name by replacing hyphens with underscores
        safe_var_name = config['report_slug'].replace('-', '_').replace('/', '__')

        template = f'''<!-- Report DataTable: {config['report_name']} -->
    <div id="report_table_container"></div>

    <script>
        $(document).ready(function() {{
            // Create report table instance
            window.report_{safe_var_name}_table = new DynamicDataTable('report_table_container', '{config['model_name']}','report_{safe_var_name}_table', '{config['data_url']}', {{
                    table_title: '{config['table_title']}',
                    table_description: '{config['table_description']}',
                    report_slug: '{config['report_slug']}',
                    report_id: '{config['report_id']}',  // Pass report_id
                    is_model: {str(config['is_model']).lower()},  // Pass is_model
                    responsive: true,
                    responsive: {{
                        details: {{
                            type: 'column',  // or 'inline', 'column-control'
                            target: 'tr'
                        }}
                    }},

                    // Column definitions from report
                    columns: {columns_js},

                    // Report features
                    is_searchable: {str(config['is_searchable']).lower()},
                    is_ajax: {str(config['is_ajax']).lower()},
                    is_download_csv: {str(config['is_download_csv']).lower()},
                    is_download_xlsx: {str(config['is_download_xlsx']).lower()},'''

        # Handle custom actions more intelligently
        if config.get('actions') is not None:
            # Use the actions from the report (and any custom additions)
            actions_js = json.dumps(config['actions'])
            template += f'''

                    // Actions from report configuration
                    actions: {actions_js},'''
        else:
            # No actions at all
            template += f'''

                    // No actions configured
                    actions: [],'''


        if config.get('custom_filters'):
            template += f'''

                    // Custom filters from report variables
                    custom_filters: {filters_js},'''

        if config.get('is_model') and config.get('model_name'):
            # Only add model URLs if we have actions enabled
            if config.get('custom_actions') is None or config.get('custom_actions'):
                template += f'''

                    // Model-based URLs
                    create_url: "{{{{ model_url('{config['model_name']}.create') }}}}",
                    edit_url: "{{{{ model_url('{config['model_name']}.edit') }}}}",'''

        template += f'''

                    // Additional options
                    pageLength: 25,
                    processing: true,
                    serverSide: {str(config['is_ajax']).lower()},

                    // Custom initialization
                    init_complete: function(table) {{
                        console.log('Report table initialized: {config['report_slug']}');

                        // Add export buttons if enabled
                        if ({str(config['is_download_csv']).lower()} || {str(config['is_download_xlsx']).lower()}) {{
                            const exportButtons = [];
                            if ({str(config['is_download_csv']).lower()}) {{
                                exportButtons.push({{
                                    text: '<i class="fas fa-file-csv"></i> CSV',
                                    className: 'btn btn-sm btn-outline-secondary',
                                    action: function() {{
                                        window.location.href = '{config['data_url']}?format=csv';
                                    }}
                                }});
                            }}
                            if ({str(config['is_download_xlsx']).lower()}) {{
                                exportButtons.push({{
                                    text: '<i class="fas fa-file-excel"></i> Excel',
                                    className: 'btn btn-sm btn-outline-secondary',
                                    action: function() {{
                                        window.location.href = '{config['data_url']}?format=xlsx';
                                    }}
                                }});
                            }}

                            new $.fn.dataTable.Buttons(table, {{
                                buttons: exportButtons
                            }});
                            table.buttons().container().appendTo($('.dataTables_wrapper .col-md-6:eq(0)'));
                        }}
                    }}
                }}
            );

            // Initialize the table
            window.report_{safe_var_name}_table.init();
        }});
    </script>'''

        return template

    def _process_custom_actions(self, actions: List) -> str:
        """
        Process custom actions into JavaScript format
        
        Actions can be:
        - Simple strings: ['edit', 'delete']
        - Dicts with properties: [{'name': 'edit', 'url': '/custom/edit', 'icon': 'fa-edit'}]
        """
        processed_actions = []
        
        for action in actions:
            if isinstance(action, str):
                # Simple action name
                processed_actions.append({
                    'name': action,
                    'icon': self._get_default_icon(action),
                    'class': self._get_default_class(action)
                })
            elif isinstance(action, dict):
                # Complex action with properties
                processed = {
                    'name': action.get('name', 'action'),
                    'icon': action.get('icon', self._get_default_icon(action.get('name', ''))),
                    'class': action.get('class', self._get_default_class(action.get('name', ''))),
                }
                
                # Add optional properties
                if 'url' in action:
                    processed['url'] = action['url']
                if 'label' in action:
                    processed['label'] = action['label']
                if 'method' in action:
                    processed['method'] = action['method']
                if 'confirm' in action:
                    processed['confirm'] = action['confirm']
                if 'callback' in action:
                    processed['callback'] = action['callback']
                    
                processed_actions.append(processed)
        
        return self._dict_to_js_object(processed_actions, indent=16)

    def _get_default_icon(self, action_name: str) -> str:
        """Get default icon for common action names"""
        icons = {
            'view': 'fa-eye',
            'edit': 'fa-edit',
            'delete': 'fa-trash',
            'create': 'fa-plus',
            'copy': 'fa-copy',
            'duplicate': 'fa-clone',
            'export': 'fa-download',
            'print': 'fa-print',
            'archive': 'fa-archive',
            'restore': 'fa-undo',
            'lock': 'fa-lock',
            'unlock': 'fa-unlock',
            'approve': 'fa-check',
            'reject': 'fa-times',
            'email': 'fa-envelope',
            'share': 'fa-share',
        }
        return icons.get(action_name.lower(), 'fa-cog')

    def _get_default_class(self, action_name: str) -> str:
        """Get default button class for common action names"""
        classes = {
            'view': 'btn-info',
            'edit': 'btn-primary',
            'delete': 'btn-danger',
            'create': 'btn-success',
            'copy': 'btn-secondary',
            'duplicate': 'btn-secondary',
            'export': 'btn-outline-primary',
            'print': 'btn-outline-secondary',
            'archive': 'btn-warning',
            'restore': 'btn-success',
            'approve': 'btn-success',
            'reject': 'btn-danger',
        }
        return classes.get(action_name.lower(), 'btn-secondary')

    def _dict_to_js_object(self, data: Any, indent: int = 0) -> str:
        """Convert Python dict to JavaScript object notation"""
        if isinstance(data, dict):
            if not data:
                return '{}'

            lines = ['{']
            items = list(data.items())
            for i, (key, value) in enumerate(items):
                if key == 'render' and isinstance(value, str):
                    lines.append(f"{' ' * (indent + 4)}{key}: {value}")
                else:
                    value_str = self._dict_to_js_object(value, indent + 4)
                    lines.append(f"{' ' * (indent + 4)}{key}: {value_str}")

                if i < len(items) - 1:
                    lines[-1] += ','

            lines.append(f"{' ' * indent}}}")
            return '\n'.join(lines)

        elif isinstance(data, list):
            if not data:
                return '[]'
            return json.dumps(data)

        elif isinstance(data, bool):
            return 'true' if data else 'false'

        elif isinstance(data, (int, float)):
            return str(data)

        elif data is None:
            return 'null'

        else:
            return json.dumps(str(data))

    def _generate_filters_js(self, filters: List[Dict]) -> str:
        """Generate JavaScript array for filters"""
        if not filters:
            return '[]'

        js_filters = []
        for filter_config in filters:
            js_filters.append(self._dict_to_js_object(filter_config, indent=12))

        return '[\n' + ',\n'.join(js_filters) + '\n            ]'

    def generate_standalone_page(self, report_slug: str, **kwargs) -> str:
        """Generate a complete standalone HTML page for a report"""
        config = self.generate_datatable_config(report_slug, **kwargs)
        table_template = self.generate_jinja_template(report_slug, **kwargs)

        page_template = f'''
{{% extends "base.html" %}}

{{% block title %}}{config['table_title']}{{% endblock %}}

{{% block content %}}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            {table_template}
        </div>
    </div>
</div>
{{% endblock %}}

{{% block extra_js %}}
<!-- Additional JS for report-specific functionality -->
<script>
    // Handle report result row clicks
    $(document).on('click', '.view-report-result', function(e) {{
        e.preventDefault();
        const id = $(this).data('id');
        // Implement view logic here
        console.log('View report result:', id);
    }});
</script>
{{% endblock %}}
'''

        return page_template


# Convenience functions
def generate_report_datatable(session, report_slug: str, **kwargs):
    """Generate DataTable config for a report"""
    generator = ReportDataTableGenerator(session)
    return generator.generate_datatable_config(report_slug, **kwargs)


def generate_report_template(session, report_slug: str, **kwargs):
    """Generate Jinja2 template for a report"""
    generator = ReportDataTableGenerator(session)
    return generator.generate_jinja_template(report_slug, **kwargs)


if __name__ == '__main__':
    print("Report-based DataTable Generator")
    print("This module generates DataTable configurations from existing Report records")
    print("\nUsage:")
    print("  from report_datatable_generator import generate_report_datatable, generate_report_template")
    print("  ")
    print("  # Generate configuration")
    print("  config = generate_report_datatable(session, 'user-activity-report')")
    print("  ")
    print("  # Generate template")
    print("  template = generate_report_template(session, 'user-activity-report')")