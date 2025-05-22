from flask import Blueprint, render_template


bp = Blueprint('404', __name__, url_prefix='/', template_folder="templates")
@bp.route('<path:subpath>')
def v2_handler(subpath):
    return render_template('404/404.html', content=f"Resource not found: {subpath}"), 404
