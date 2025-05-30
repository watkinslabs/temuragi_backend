from flask import Blueprint, request, session, render_template, redirect, url_for, flash, current_app, g
from app._system.auth.auth_service import AuthService
from datetime import datetime, timedelta
import functools

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.before_app_request
def bind_session():
    if not hasattr(g, 'session'):
        g.session = current_app.db_session

@auth_bp.teardown_request
def close_session(exc):
    sess = g.pop('session', None)
    if sess:
        sess.close()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        identity = request.form.get('username', '')
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        # Validate form inputs
        if not identity or not password:
            flash('Username and password are required', 'danger')
            return render_template('login.html', 
                                   site_name=current_app.config.get('SITE_NAME', 'Application'),
                                   current_year=datetime.now().year)
        
        # Authenticate user
        db_session = g.session
        success, user_data, error_msg = AuthService.login(db_session, identity, password)
            
        if success:
            # Set session data
            session['user_id'] = user_data['uuid']
            session['username'] = user_data['username']
            session['role_uuid'] = user_data['role_uuid']
            
            # Set session expiry for "remember me" functionality
            if remember:
                # Session will last for 30 days
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
            else:
                # Session will last until browser is closed
                session.permanent = False
            
            # Redirect to dashboard or requested page
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            # Login failed
            flash(error_msg, 'danger')
    
    # Render login form for GET request or failed login
    return render_template('login.html', 
                           site_name=current_app.config.get('SITE_NAME', 'Application'),
                           current_year=datetime.now().year)

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    # Clear session data
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password')
def forgot_password():
    """Stub for forgot password"""
    flash('Password reset functionality coming soon', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password/<token>')
def reset_password(token):
    """Stub for password reset"""
    flash('Password reset functionality coming soon', 'info')
    return redirect(url_for('auth.login'))

# Login required decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view