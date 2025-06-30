from flask import Blueprint
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('SPA', __name__, url_prefix='/')

@bp.route('/')
def test_page():
    """Simple Single Page App Entrypoint using the TemplateRenderer"""
    renderer = TemplateRenderer()
    return renderer.render_template("/", fragment_only=None)
