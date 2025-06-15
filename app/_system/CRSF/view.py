from flask import Blueprint, render_template_string, g, current_app

# Create blueprint
bp = Blueprint('crsf', __name__, url_prefix='/api/crsf-token')

@bp.route('/')
def get_csrf_token():
    csrf=current_app.csrf
    return {'csrf_token': csrf.generate_token()}