"""
Report API Views/Routes
JSON API endpoints for report operations
"""

from flask import Blueprint, request, jsonify, g, send_file
from app.classes import ReportService
from app.config import config
import io

# Create blueprint
bp = Blueprint('report_api', __name__, url_prefix='/api/reports')

from app.register.database import db_registry

def get_service():
    """Get report service instance"""
    return ReportService()


def json_response(data=None, error=None, status=200):
    """Standard JSON response format"""
    if error:
        return jsonify({
            'success': False,
            'error': str(error),
            'data': None
        }), status
    return jsonify({
        'success': True,
        'error': None,
        'data': data
    }), status








@bp.route('/config', methods=['POST'])
def get_report_config():
    """
    Get report configuration for ServerDataTable component.
    Returns the config in the format ServerDataTable expects.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        context = data.get('context')
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Get the report with all relationships
        db_session = db_registry._routing_session()

        from app.models import Report
        report = db_session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return json_response(error="Report not found", status=404)
        
        # Check permissions (optional, uncomment if needed)
        # user_id = g.get('user_id')  # Get from auth
        # if not Report.check_permission(user_id, report.slug, 'view'):
        #     return json_response(error="Permission denied", status=403)
        
        # Build the columns configuration
        columns_config = {}
        
        for col in report.columns:
            if col.is_visible:
                columns_config[col.name] = {
                    'label': col.label or col.name,
                    'searchable': col.is_searchable,
                    'orderable': col.is_sortable,
                    'order_index': col.order_index,
                    'type': col.data_type.name if col.data_type else 'string',
                    'format': col.format_string,
                    'width': col.width,
                    'alignment': col.alignment,
                    'search_type': col.search_type,
                    'render': None  # You can add custom render functions here
                }
                
                # Add format-specific rendering hints
                if col.data_type:
                    if col.data_type.name in ['date', 'datetime']:
                        columns_config[col.name]['format'] = 'date'
                    elif col.data_type.name == 'boolean':
                        columns_config[col.name]['format'] = 'boolean'
                    elif col.data_type.name in ['decimal', 'float'] and col.format_string:
                        if '$' in col.format_string:
                            columns_config[col.name]['format'] = 'currency'
                        elif '%' in col.format_string:
                            columns_config[col.name]['format'] = 'percent'
                        else:
                            columns_config[col.name]['format'] = 'number'
        
        # Build actions array
        actions = []
        
        # Add page actions from the report
        for action in report.page_actions:
            action_config = {
                'name': action.name,
                'title': action.label or action.name,
                'icon': action.icon or 'fas fa-cog',
                'color': action.color or 'primary',
                'mode': action.mode or 'row',  # 'page' or 'row'
                'action_type': action.action_type,  # 'htmx', 'api', 'javascript'
                'url': action.url,
                'url_for': action.url_for,  # Template URL with {{variables}}
                'method': action.method or 'GET',
                'target': action.target or '_self',
                'headers': action.headers or {},
                'payload': action.payload or {},
                'confirm': action.confirm,
                'confirm_message': action.confirm_message,
                'data_index': action.data_index,
                'order_index': action.order_index
            }
            
            # Add javascript code if it's a javascript action
            if action.action_type == 'javascript' and action.javascript_code:
                action_config['javascript'] = action.javascript_code
            
            actions.append(action_config)
        
        # Get datatable options from report options
        datatable_options = report.options.get('datatable', {}) if report.options else {}
        
        # Build the complete configuration
        config = {
            'model_name': report.name,
            'report_name': report.slug,
            'api_url': f"{config['route_prefix']}api/data",  # Your data endpoint
            'page_length': datatable_options.get('page_length', 25),
            'show_search': datatable_options.get('is_searchable', True),
            'show_column_search': datatable_options.get('show_column_search', False),
            'show_pagination': True,
            'table_title': report.label or report.name,
            'table_description': report.description,
            'report_id': str(report.id),
            'is_model': report.is_model,
            'columns': columns_config,
            'excluded_columns': [],
            'actions': actions,
            'is_wide': report.is_wide,
            'is_ajax': report.is_ajax,
            'is_auto_run': report.is_auto_run,
            'export_formats': {
                'csv': report.is_download_csv,
                'xlsx': report.is_download_xlsx
            }
        }
        
        # Add any custom options from the report
        if report.options:
            config['custom_options'] = {
                'cache_enabled': report.options.get('cache_enabled', False),
                'refresh_interval': report.options.get('refresh_interval', 0),
                'row_limit': report.options.get('row_limit', 10000)
            }
        
        return json_response(data={
            'success': True,
            'config': config
        })
        
    except Exception as e:
        return json_response(error=str(e), status=500)

# =====================================================================
# REPORT EXECUTION ROUTES
# =====================================================================

@bp.route('/execute', methods=['POST'])
def execute_report():
    """Execute a report"""
    try:
        service = get_service()
        request_data = request.get_json() or {}
        
        report_id = request_data.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Remove report_id from request_data to pass clean params
        execution_params = {k: v for k, v in request_data.items() if k != 'report_id'}
        
        result = service.execute_report(
            report_id=report_id,
            request_data=execution_params,
            user_id=None  # TODO: Add auth later
        )
        
        return json_response(data=result)
    except PermissionError as e:
        return json_response(error=str(e), status=403)
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/test', methods=['POST'])
def test_report():
    """Test a report query"""
    try:
        service = get_service()
        params = request.get_json() or {}
        
        report_id = params.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        columns = service.test_report_query(
            report_id=report_id,
            params=params.get('vars', {})
        )
        
        return json_response(data={'columns': columns})
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/preview', methods=['POST'])
def preview_report():
    """Preview report with limited rows"""
    try:
        service = get_service()
        request_data = request.get_json() or {}
        
        report_id = request_data.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Remove report_id and add limit for preview
        execution_params = {k: v for k, v in request_data.items() if k != 'report_id'}
        if 'limit' not in execution_params:
            execution_params['limit'] = 10
        
        result = service.execute_report(
            report_id=report_id,
            request_data=execution_params,
            user_id=None  # TODO: Add auth later
        )
        
        return json_response(data=result)
    except PermissionError as e:
        return json_response(error=str(e), status=403)
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/export', methods=['POST'])
def export_report():
    """Export report in specified format"""
    try:
        service = get_service()
        request_data = request.get_json() or {}
        
        report_id = request_data.get('report_id')
        format = request_data.get('format')
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        if not format:
            return json_response(error="format is required", status=400)
        
        # Remove report_id and format from execution params
        execution_params = {k: v for k, v in request_data.items() 
                          if k not in ['report_id', 'format']}
        
        # For now, handle JSON export using existing method
        if format.lower() == 'json':
            definition = service.export_report_definition(
                report_id=report_id
            )
            return json_response(data=definition)
        
        # For CSV/Excel, execute report and format results
        elif format.lower() in ['csv', 'xlsx']:
            result = service.execute_report(
                report_id=report_id,
                request_data=execution_params,
                user_id=None  # TODO: Add auth later
            )
            
            # TODO: Implement CSV/Excel formatting
            # For now, return error
            return json_response(
                error=f"Export format '{format}' not yet implemented",
                status=501
            )
        else:
            return json_response(
                error=f"Unsupported export format: {format}",
                status=400
            )
            
    except PermissionError as e:
        return json_response(error=str(e), status=403)
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# PERMISSION ROUTES
# =====================================================================

@bp.route('/permissions', methods=['POST'])
def get_report_permissions():
    """Get user's permissions for a report"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        user_id = data.get('user_id')  # TODO: Get from auth later
        
        if not user_id:
            return json_response(
                error="Authentication required",
                status=401
            )
        
        # Check each permission type
        permissions = {
            'view': service.check_user_permission(user_id, report_id, 'view'),
            'execute': service.check_user_permission(user_id, report_id, 'execute'),
            'edit': service.check_user_permission(user_id, report_id, 'edit'),
            'delete': service.check_user_permission(user_id, report_id, 'delete')
        }
        
        return json_response(data=permissions)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/assign', methods=['POST'])
def assign_report():
    """Assign report to role"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        role_id = data.get('role_id')
        actions = data.get('actions', ['view', 'execute'])
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        if not role_id:
            return json_response(error="role_id is required", status=400)
        
        success, message = service.assign_report_to_role(
            report_id=report_id,
            role_id=role_id,
            actions=actions
        )
        
        if success:
            return json_response(data={'message': message})
        else:
            return json_response(error=message, status=400)
            
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# BUILDER/VALIDATION ROUTES
# =====================================================================

@bp.route('/validate-query', methods=['POST'])
def validate_query():
    """Validate SQL query"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        query = data.get('query')
        connection_id = data.get('connection_id')
        
        if not query or not connection_id:
            return json_response(
                error="query and connection_id are required",
                status=400
            )
        
        # Test connection with query
        success, message = service.test_connection(connection_id)
        
        if not success:
            return json_response(
                error=f"Connection test failed: {message}",
                status=400
            )
        
        # TODO: Implement actual query validation
        # For now, just return success if connection works
        return json_response(data={
            'valid': True,
            'message': 'Query syntax appears valid'
        })
        
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/detect-variables', methods=['POST'])
def detect_variables():
    """Detect variables in SQL query"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '')
        
        # Simple regex to find :variable_name patterns
        import re
        pattern = r':(\w+)'
        variables = re.findall(pattern, query)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_vars = []
        for var in variables:
            if var not in seen:
                seen.add(var)
                unique_vars.append(var)
        
        return json_response(data={'variables': unique_vars})
        
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# TEMPLATE ROUTES
# =====================================================================

@bp.route('/templates/list', methods=['POST'])
def list_report_templates():
    """List report templates"""
    try:
        service = get_service()
        templates = service.list_report_templates()
        
        # Convert to dict for JSON serialization
        template_data = [
            {
                'id': str(t.id),
                'name': t.name,
                'label': t.label,
                'description': t.description,
                'created_at': t.created_at.isoformat() if t.created_at else None
            }
            for t in templates
        ]
        
        return json_response(data=template_data)
        
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/templates/create', methods=['POST'])
def create_report_template():
    """Create report template"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        # Extract required fields
        name = data.get('name')
        label = data.get('label')
        template_id = data.get('template_id')
        
        if not all([name, label, template_id]):
            return json_response(
                error="name, label, and template_id are required",
                status=400
            )
        
        template = service.create_report_template(
            name=name,
            label=label,
            template_id=template_id,
            description=data.get('description'),
            show_filters=data.get('show_filters', True),
            filter_position=data.get('filter_position', 'top'),
            show_export_buttons=data.get('show_export_buttons', True),
            show_pagination=data.get('show_pagination', True),
            pagination_position=data.get('pagination_position', 'bottom'),
            datatable_options=data.get('datatable_options'),
            custom_css=data.get('custom_css'),
            custom_js=data.get('custom_js')
        )
        
        return json_response(data={
            'id': str(template.id),
            'name': template.name,
            'label': template.label
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=400)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/templates/update', methods=['POST'])
def update_report_template():
    """Update report template"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        template_id = data.get('template_id')
        if not template_id:
            return json_response(error="template_id is required", status=400)
        
        # Remove template_id from update params
        update_params = {k: v for k, v in data.items() if k != 'template_id'}
        
        template = service.update_report_template(
            template_id=template_id,
            **update_params
        )
        
        return json_response(data={
            'id': str(template.id),
            'name': template.name,
            'label': template.label
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/templates/delete', methods=['POST'])
def delete_report_template():
    """Delete report template"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        template_id = data.get('template_id')
        if not template_id:
            return json_response(error="template_id is required", status=400)
        
        force = data.get('force', False)
        
        service.delete_report_template(
            template_id=template_id,
            force=force
        )
        
        return json_response(data={'message': 'Template deleted successfully'})
        
    except ValueError as e:
        return json_response(error=str(e), status=400)
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# METADATA ROUTES
# =====================================================================

@bp.route('/connections/test', methods=['POST'])
def test_connection():
    """Test database connection"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        connection_id = data.get('connection_id')
        if not connection_id:
            return json_response(error="connection_id is required", status=400)
        
        success, message = service.test_connection(connection_id)
        
        return json_response(data={
            'success': success,
            'message': message
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/stats', methods=['POST'])
def get_stats():
    """Get report system statistics"""
    try:
        service = get_service()
        stats = service.get_dashboard_stats()
        
        return json_response(data=stats)
        
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# IMPORT/EXPORT ROUTES
# =====================================================================

@bp.route('/definition', methods=['POST'])
def export_report_definition():
    """Export report definition as JSON"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        definition = service.export_report_definition(
            report_id=report_id
        )
        
        return json_response(data=definition)
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/import', methods=['POST'])
def import_report():
    """Import report from definition"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        definition = data.get('definition')
        connection_id = data.get('connection_id')
        
        if not definition or not connection_id:
            return json_response(
                error="definition and connection_id are required",
                status=400
            )
        
        report = service.import_report_definition(
            definition=definition,
            connection_id=connection_id
        )
        
        return json_response(data={
            'id': str(report.id),
            'slug': report.slug,
            'name': report.name
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=400)
    except Exception as e:
        return json_response(error=str(e), status=500)


# =====================================================================
# COLUMN/VARIABLE ROUTES (for report builder UI)
# =====================================================================

@bp.route('/columns/reorder', methods=['POST'])
def reorder_columns():
    """Reorder report columns"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        column_order = data.get('column_order', [])
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        if not column_order:
            return json_response(error="column_order array is required", status=400)
        
        success = service.reorder_columns(
            report_id=report_id,
            column_order=column_order
        )
        
        return json_response(data={'success': success})
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/variables/validate', methods=['POST'])
def validate_variables():
    """Validate report variables against query"""
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Get report
        report = service.get_report(report_id)
        if not report:
            return json_response(error="Report not found", status=404)
        
        # Get variables from query
        import re
        pattern = r':(\w+)'
        query_vars = set(re.findall(pattern, report.query))
        
        # Get defined variables
        defined_vars = set(var.name for var in report.variables)
        
        # Find mismatches
        missing_in_definition = list(query_vars - defined_vars)
        missing_in_query = list(defined_vars - query_vars)
        
        valid = len(missing_in_definition) == 0 and len(missing_in_query) == 0
        
        return json_response(data={
            'valid': valid,
            'missing_in_definition': missing_in_definition,
            'missing_in_query': missing_in_query,
            'query_variables': list(query_vars),
            'defined_variables': list(defined_vars)
        })
        
    except Exception as e:
        return json_response(error=str(e), status=500)
    


    # =====================================================================
# QUERY METADATA ROUTES
# =====================================================================

@bp.route('/query-metadata', methods=['POST'])
def get_query_metadata():
    """
    Extract column metadata from a SQL query without fetching data.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        query = data.get('query')
        connection_id = data.get('connection_id')
        params = data.get('params', {})
        
        if not query:
            return json_response(error="query is required", status=400)
        if not connection_id:
            return json_response(error="connection_id is required", status=400)
        
        # Extract metadata
        metadata = service.get_query_metadata(
            query=query,
            connection_id=connection_id,
            params=params
        )
        
        # Format response
        columns = []
        for col in metadata:
            columns.append({
                'name': col['name'],
                'type': col.get('suggested_type', 'string'),
                'sql_type': col.get('sql_type'),
                'python_type': col.get('python_type'),
                'nullable': col.get('nullable'),
                'precision': col.get('precision'),
                'scale': col.get('scale')
            })
        
        return json_response(data={
            'columns': columns,
            'column_count': len(columns)
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/analyze-columns', methods=['POST'])
def analyze_report_columns():
    """
    Analyze a report's query and compare with existing column definitions.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        auto_update = data.get('auto_update', False)
        dry_run = data.get('dry_run', False)
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Analyze columns
        analysis = service.analyze_report_columns(
            report_id=report_id,
            auto_update=auto_update,
            dry_run=dry_run
        )
        
        # Check if analysis failed
        if analysis.get('analysis_failed'):
            return json_response(
                error=analysis.get('error', 'Analysis failed'),
                status=400
            )
        
        # Format response
        response_data = {
            'compatibility': analysis['compatibility'],
            'existing_columns': analysis['existing_columns'],
            'new_columns': analysis['new_columns'],
            'missing_columns': analysis['missing_columns'],
            'type_changes': analysis['type_changes'],
            'changes_made': analysis.get('changes_made', []),
            'dry_run': analysis['dry_run'],
            'auto_update_enabled': analysis['auto_update_enabled']
        }
        
        # Add summary
        response_data['summary'] = {
            'total_query_columns': len(analysis['query_columns']),
            'total_existing_columns': len(analysis['existing_columns']),
            'new_columns_count': len(analysis['new_columns']),
            'missing_columns_count': len(analysis['missing_columns']),
            'type_changes_count': len(analysis['type_changes']),
            'changes_made_count': len(analysis.get('changes_made', []))
        }
        
        return json_response(data=response_data)
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/sync-columns', methods=['POST'])
def sync_report_columns():
    """
    Synchronize report columns with query metadata.
    More aggressive than analyze - will reorder and optionally remove columns.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        remove_missing = data.get('remove_missing', False)
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Sync columns
        results = service.sync_report_columns_from_query(
            report_id=report_id,
            remove_missing=remove_missing
        )
        
        # Add summary
        results['summary'] = {
            'added_count': len(results['added']),
            'updated_count': len(results['updated']),
            'removed_count': len(results['removed']),
            'columns_reordered': results['reordered']
        }
        
        return json_response(data=results)
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/query/analyze', methods=['POST'])
def analyze_query():
    """
    Analyze a SQL query for compatibility and structure without a specific report.
    Useful for query builder UI.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        query = data.get('query')
        connection_id = data.get('connection_id')
        
        if not query:
            return json_response(error="query is required", status=400)
        if not connection_id:
            return json_response(error="connection_id is required", status=400)
        
        db_session=db_registry._routing_session()
        connection = db_session.query(Connection).filter_by(id=connection_id).first()
        if not connection:
            return json_response(error="Connection not found", status=404)
        
        db_type = connection.database_type.name.lower()
        
        # Analyze query compatibility
        compatibility = service.metadata_extractor.analyze_query_compatibility(query, db_type)
        
        # Try to get metadata if it's a SELECT query
        metadata = None
        if compatibility['is_select']:
            try:
                metadata = service.get_query_metadata(
                    query=query,
                    connection_id=connection_id
                )
            except Exception as e:
                compatibility['warnings'].append(f"Could not extract metadata: {str(e)}")
        
        # Build response
        response_data = {
            'compatibility': compatibility,
            'database_type': db_type
        }
        
        if metadata:
            response_data['columns'] = [
                {
                    'name': col['name'],
                    'type': col.get('suggested_type', 'string'),
                    'sql_type': col.get('sql_type')
                }
                for col in metadata
            ]
            response_data['column_count'] = len(metadata)
        
        return json_response(data=response_data)
        
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/columns/detect-types', methods=['POST'])
def detect_column_types():
    """
    Run a query and detect column types from actual data.
    More thorough than metadata extraction as it samples the data.
    """
    try:
        service = get_service()
        data = request.get_json() or {}
        
        report_id = data.get('report_id')
        sample_size = data.get('sample_size', 100)  # How many rows to sample
        
        if not report_id:
            return json_response(error="report_id is required", status=400)
        
        # Get report
        report = service.get_report(report_id)
        if not report:
            return json_response(error="Report not found", status=404)
        
        # For now, use metadata extraction
        # TODO: Implement actual data sampling for better type detection
        metadata = service.get_query_metadata(
            query=report.query,
            connection_id=report.connection_id
        )
        
        # Format as type detection results
        type_detections = []
        for col in metadata:
            type_detections.append({
                'name': col['name'],
                'detected_type': col.get('suggested_type', 'string'),
                'sql_type': col.get('sql_type'),
                'confidence': 'high' if col.get('python_type') else 'medium',
                'sample_values': []  # TODO: Add actual samples
            })
        
        return json_response(data={
            'columns': type_detections,
            'sample_size': sample_size,
            'detection_method': 'metadata'  # or 'sampling' when implemented
        })
        
    except ValueError as e:
        return json_response(error=str(e), status=404)
    except Exception as e:
        return json_response(error=str(e), status=500)


@bp.route('/columns/suggest', methods=['POST'])
def suggest_column_settings():
    """
    Suggest column settings based on column name and type.
    Useful for auto-configuring new columns.
    """
    try:
        data = request.get_json() or {}
        
        column_name = data.get('column_name', '')
        column_type = data.get('column_type', 'string')
        
        if not column_name:
            return json_response(error="column_name is required", status=400)
        
        # Suggest label name
        label = column_name.replace('_', ' ').title()
        
        # Common patterns for special handling
        suggestions = {
            'label': label,
            'is_searchable': True,
            'is_sortable': True,
            'is_visible': True,
            'alignment': 'left',
            'format_string': None,
            'search_type': 'contains'
        }
        
        # Type-based suggestions
        if column_type in ['integer', 'float', 'decimal']:
            suggestions['alignment'] = 'right'
            suggestions['search_type'] = 'range'
            if column_type in ['float', 'decimal']:
                suggestions['format_string'] = '{:.2f}'
        
        elif column_type in ['date', 'datetime']:
            suggestions['alignment'] = 'center'
            suggestions['search_type'] = 'date_range'
            if column_type == 'date':
                suggestions['format_string'] = '%Y-%m-%d'
            else:
                suggestions['format_string'] = '%Y-%m-%d %H:%M'
        
        elif column_type == 'boolean':
            suggestions['alignment'] = 'center'
            suggestions['search_type'] = 'exact'
        
        # Name-based patterns
        name_lower = column_name.lower()
        
        if 'id' in name_lower and name_lower.endswith('id'):
            suggestions['is_searchable'] = False
            suggestions['alignment'] = 'right'
        
        elif any(pattern in name_lower for pattern in ['password', 'secret', 'token']):
            suggestions['is_visible'] = False
            suggestions['is_searchable'] = False
        
        elif any(pattern in name_lower for pattern in ['email', 'mail']):
            suggestions['search_type'] = 'contains'
        
        elif any(pattern in name_lower for pattern in ['price', 'amount', 'cost', 'total']):
            suggestions['alignment'] = 'right'
            suggestions['format_string'] = '${:.2f}'
        
        elif any(pattern in name_lower for pattern in ['percent', 'rate']):
            suggestions['alignment'] = 'right'
            suggestions['format_string'] = '{:.1f}%'
        
        elif name_lower in ['created_at', 'updated_at', 'deleted_at']:
            suggestions['alignment'] = 'center'
            suggestions['format_string'] = '%Y-%m-%d %H:%M'
            suggestions['search_type'] = 'date_range'
        
        return json_response(data=suggestions)
        
    except Exception as e:
        return json_response(error=str(e), status=500)