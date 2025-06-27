"""
Report HTML Views/Routes
HTML page routes for report viewing and editing
"""

from flask import Blueprint, render_template_string, g, request
from app.classes import ReportService

# Create blueprint for report pages
bp = Blueprint('report', __name__, url_prefix='/reports')


def get_service():
    """Get report service instance"""
    return ReportService(g.session)


# =====================================================================
# PAGE ROUTES (HTML VIEWS)
# =====================================================================


@bp.route('/<report_id>', methods=['POST'])
def view_report(report_id):
    """Render individual report page"""
    try:
        service = get_service()
        
        # Get the report
        from app.models import Report
        report = g.session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return "<h1>Report not found</h1>", 404
        
        # Check if report has a template
        if report.report_template:
            # Use template renderer with the report's template
            from app.classes import TemplateRenderer
            renderer = TemplateRenderer(g.session)
            
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
        else:
            # Fallback to basic DataTables HTML
            return render_report_html(report)
            
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
    renderer = TemplateRenderer(g.session)
    
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
        
        report_id = request.get_json().get('id')
        
        if not report_id:
            return {'success':False}
        
            
        from app.models import Report
        report = g.session.query(Report).filter_by(id=report_id).first()
        
        if not report:
            return "<h1>Report not found</h1>", 404
        
        # Get template renderer
        from app.classes import TemplateRenderer
        renderer = TemplateRenderer(g.session)
        
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
