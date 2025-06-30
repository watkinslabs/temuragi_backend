"""
Report HTML Views/Routes
HTML page routes for report viewing and editing
"""

from flask import Blueprint, render_template_string, g, request
from app.classes import ReportService, TemplateRenderer

# Create blueprint for report pages
bp = Blueprint('report', __name__, url_prefix='/reports')

from app.register.database import db_registry

def get_service():
    """Get report service instance"""
    return ReportService()


# =====================================================================
# PAGE ROUTES (HTML VIEWS)
# =====================================================================


@bp.route('/', methods=['GET', 'POST'])
def list():
    slug="report"
    renderer = TemplateRenderer()
    rendered_content = renderer.render_page(slug)
    return rendered_content



@bp.route('/<report_id>', methods=['POST'])
def view_report(report_id):
    """Render individual report page"""
    try:
        service = get_service()
        db_session=db_registry._routing_session()

        # Get the report
        from app.models import Report
        report = db_session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return "<h1>Report not found</h1>", 404
        
        # Check if report has a template
        if report.report_template:
            # Use template renderer with the report's template
            from app.classes import TemplateRenderer
            renderer = TemplateRenderer()
            
            # Create context for the template
            context = {
                'report': report,
                'report_id': str(report.id),
                'report_slug': report.slug,
                'report_name': report.name,
                'report_description': report.description,
                'is_ajax': report.is_ajax,
                'is_auto_run': report.is_auto_run,
                'variables': report.variables,
                'columns': report.columns
            }
            
            # Render using the report's template
            return renderer.render_template(
                template_id=report.report_template.template_id,
                context=context
            )
    except Exception as e:
        return f"""
        <h1>Error rendering report</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <pre>{repr(e)}</pre>
        """




@bp.route('/create', methods=['POST'])
def create():
    """Render report creation page"""
    from app.classes import TemplateRenderer
    renderer = TemplateRenderer()
    
    # Pass empty report_id for create mode
    context = {
        'report_id': None,
        'page_title': 'Create New Report',
        'is_edit_mode': False
    }
    
    return renderer.render_page("report_create", **context)


@bp.route('/edit', methods=['POST'])
def edit():
    """Render report edit page"""
    try:
        service = get_service()
        db_session=db_registry._routing_session()
        
        report_id = request.get_json().get('id')
        
        if not report_id:
            return {'success':False}
        
            
        from app.models import Report
        report = db_session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return "<h1>Report not found</h1>", 404
        
        # Get template renderer
        from app.classes import TemplateRenderer
        renderer = TemplateRenderer()
        
        # Pass report info to template
        context = {
            'report_id': str(report.id),
            'report_name': report.name,
            'page_title': f'Edit Report: {report.name}',
            'is_edit_mode': True
        }
        
        # Use the same template as create, but with edit context
        return renderer.render_page("report_create",**context)
        
    except Exception as e:
        return f"""
        <h1>Error loading report editor</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <pre>{repr(e)}</pre>
        """


@bp.route('/delete', methods=['POST'])
def delete():
    """Delete a report"""
    try:
        service = get_service()
        
        # Get report_id from request
        report_id = request.get_json().get('id')
        
        if not report_id:
            return {'success': False, 'error': 'No report ID provided'}, 400
        
        # Get the report
        from app.models import Report
        report = db_session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return {'success': False, 'error': 'Report not found'}, 404
        
        # Delete the report
        db_session.delete(report)
        db_session.commit()
        
        return {'success': True, 'message': f'Report "{report.name}" deleted successfully'}
        
    except Exception as e:
        db_session.rollback()
        return {'success': False, 'error': str(e)}, 500