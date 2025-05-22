from flask import Blueprint, render_template, abort, request, Response, session, redirect, url_for, current_app, make_response
import requests
from datetime import datetime, timedelta
import time
import json

bp = Blueprint('debug', __name__, url_prefix="/debug", template_folder="tpl")



@bp.route('/', defaults={'path': ''})
def home(path):
    """Display all session data and time to live information"""
    
    # Get session lifetime from app config
    session_lifetime = current_app.config.get('SESSION_LIFETIME', 1800)
    if isinstance(session_lifetime, timedelta):
        session_lifetime = session_lifetime.total_seconds()
    
    # Get creation time if available
    session_created = None
    if '_created_at' in session:
        session_created = datetime.fromtimestamp(session['_created_at'])
    else:
        # Set creation time if not available
        session['_created_at'] = time.time()
        session_created = datetime.now()
    
    # Track last activity
    session['_last_activity'] = time.time()
    session_last_activity = datetime.fromtimestamp(session['_last_activity'])
    
    # Calculate expiry time
    session_expires = session_created + timedelta(seconds=session_lifetime)
    
    # Calculate remaining TTL
    current_time = time.time()
    session_ttl = int(session['_created_at'] + session_lifetime - current_time)
    
    # Get individual key expiry times
    session_expiry = {}
    for key in session:
        # Default TTL for all keys is same as session
        session_expiry[key] = 'Same as session'
    
    # Additional debug information
    debug_info = {
        'request_method': request.method,
        'request_path': request.path,
        'request_args': request.args.to_dict(),
        'request_headers': dict(request.headers),
        'request_cookies': request.cookies,
        'app_config': {k: str(v) for k, v in current_app.config.items() if not k.startswith('_')},
        'session_backend': current_app.config.get('SESSION_TYPE', 'filesystem')
    }
    
    # Format the session data for display
    session_data = {}
    for key, value in session.items():
        try:
            # Try to make values JSON serializable for display
            json.dumps(value)
            session_data[key] = value
        except (TypeError, OverflowError):
            # If not serializable, convert to string
            session_data[key] = str(value)
    


    # Handle actions (via query parameters)
    if request.args.get('action') == 'clear':
        session.clear()
        session['_created_at'] = time.time()
        return redirect(url_for('debug.home'))
        
    if request.args.get('action') == 'refresh':
        session['_created_at'] = time.time()
        session.modified = True
        return redirect(url_for('debug.home'))
    
    # Render the template
    return render_template(
        'debug/session.html',
        session=session_data,
        session_ttl=session_ttl,
        session_created=session_created,
        session_last_activity=session_last_activity,
        session_expires=session_expires,
        session_expiry=session_expiry,
        debug_info=debug_info
    )