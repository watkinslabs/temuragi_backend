from flask import Blueprint
from app.classes import TemplateRenderer


bp = Blueprint('404', __name__, url_prefix='/', template_folder="tpl")
@bp.route('<path:subpath>')
def v2_handler(subpath):
    """Simple test route that renders a page using the TemplateRenderer"""
    renderer = TemplateRenderer()
    
    rendered_content = renderer.render_page('not-found')
    
    return rendered_content
