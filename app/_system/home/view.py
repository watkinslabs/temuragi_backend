from flask import Blueprint, render_template_string, g
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('/')
def index():
        session = g.session
        
        # Create template renderer
        renderer = TemplateRenderer(session)
        
        from app.models import Page
        page = session.query(Page).filter_by(slug='Home').first()
        
        # Render the page using the template system
        rendered_content = renderer.render_page(page.uuid)
        
        return rendered_content
        
