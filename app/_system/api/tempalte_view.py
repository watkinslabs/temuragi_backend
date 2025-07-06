from flask import Blueprint, jsonify

bp = Blueprint('template_api', __name__, url_prefix='/api')


@bp.route('/templates/<slug>')
def react_base_page(slug):
    """Simple Single Page App Entrypoint using the TemplateRenderer"""
    from app.classes import TemplateRenderer
    renderer = TemplateRenderer()
    template= renderer.render_template(slug, fragment_only=True)
    
    if template:
        return jsonify({
            "success": True,
            "html": template,
            "css":None,
            "js": None
        })

0