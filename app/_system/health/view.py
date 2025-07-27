
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, g, jsonify
from datetime import datetime

from app.classes import AuthService

# Create auth blueprint
bp = Blueprint('api_health', __name__, url_prefix='/api')


@bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200