
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, g, jsonify
from datetime import datetime

from app.classes import AuthService

# Create auth blueprint
bp = Blueprint('api_auth', __name__, url_prefix='/api/auth')



@bp.route('/', methods=['POST'])
def login():
  if request.is_json:
            data = request.get_json()
            identity = data.get('username')
            password = data.get('password')
            remember = data.get('remember', False)
            
            # Get auth service and perform API login
            auth = AuthService()
            result = auth.login_api(identity, password, remember, application='web')
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 401


@bp.route('/validate', methods=['GET'])
def validate():
    """Validate current access token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization header'}), 401
    
    token = auth_header.split(' ')[1]
    
    auth = AuthService()
    result = auth.validate_api_token(token)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'refresh_token is required'}), 400
    
    auth = AuthService()
    result = auth.refresh_token(refresh_token)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout view - handles both traditional and API logout"""
    if request.method == 'POST' and request.is_json:
        # API logout
        data = request.get_json()
        access_token = data.get('access_token')
        user_id = data.get('user_id')
        
        auth = AuthService()
        result = auth.logout_api(access_token, user_id)
        
        return jsonify(result), 200
    
    # Traditional logout (GET or non-JSON POST)
    auth = AuthService()
    result = auth.logout()
    flash(result['message'], 'info')
    return redirect(url_for('auth.login'))

@bp.route('/status', methods=['GET'])
def status():
    """Quick auth status check"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'authenticated': False}), 200
    
    token = auth_header.split(' ')[1]
    auth = AuthService()
    result = auth.validate_api_token(token)
    
    return jsonify({
        'authenticated': result['success'],
        'user': result.get('user_info') if result['success'] else None
    }), 200

@bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200