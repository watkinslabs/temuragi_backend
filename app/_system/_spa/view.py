from flask import Blueprint
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('SPA', __name__, url_prefix='/')

@bp.route('/')
def react_base_page():
    """Simple Single Page App Entrypoint using the TemplateRenderer"""
    #renderer = TemplateRenderer()
    #return renderer.render_template("/", fragment_only=None)

    """Simple Single Page App Entrypoint using the TemplateRenderer"""
    from app.classes import TemplateRenderer
    renderer = TemplateRenderer()
    return renderer.render_template("home", fragment_only=False)

