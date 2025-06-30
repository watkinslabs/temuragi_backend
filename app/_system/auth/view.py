from flask import Blueprint

# Create auth blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')



@bp.route('/login', methods=['GET'])
def login():
    """Login view - just calls auth service"""
    from app.classes import TemplateRenderer
    site_config=None
    renderer = TemplateRenderer()
    
    return renderer.render_page("login")
    
