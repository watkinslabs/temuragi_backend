from flask import Blueprint, render_template_string, g
from app.classes import TemplateRenderer

# Create blueprint
bp = Blueprint('SPA', __name__, url_prefix='/')

@bp.route('/')
def test_page():
    """Simple Single Page App Entrypoint using the TemplateRenderer"""
    session = g.session
    renderer = TemplateRenderer(session)
    return renderer.render_template("/", fragment_only=None)
