from flask import Blueprint, render_template_string, g
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('theme', __name__, url_prefix='/theme')

@bp.route('/')
def test_page():
    """Simple test route that renders a page using the TemplateRenderer"""
    try:
        # Get database session from Flask g context
        session = g.session
        
        # Create template renderer
        renderer = TemplateRenderer(session)
        
        # Try to find a page by slug 'Home' and render it
        from app.models import Page
        page = session.query(Page).filter_by(slug='theme').first()
        
        # Render the page using the template system
        rendered_content = renderer.render_page(page.uuid)
        
        return rendered_content
        
    except Exception as e:
        # Return error info for debugging
        return f"""
        <h1>Error rendering page</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Type:</strong> {type(e).__name__}</p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">
        {repr(e)}
        </pre>
        """