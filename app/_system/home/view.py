from flask import Blueprint
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('/')
def index():
        renderer = TemplateRenderer()
        
        # Render the page using the template system
        rendered_content = renderer.render_page('home')
        
        return rendered_content
        
