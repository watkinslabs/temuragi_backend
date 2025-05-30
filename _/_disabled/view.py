"""
Authentication Blueprint for Performance Radiator application
Handles login, logout, registration, and password reset
BSD 3-Clause License
"""
import datetime
from flask import Blueprint, render_template, url_for, session, redirect, make_response
from flask import request, flash, current_app, abort, g
import requests
import time
from .model import AuthDB
from app.utils.office365_mailer import Office365Mailer
from app.admin.theme.model import  Theme
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Create blueprint with URL prefix
bp = Blueprint('auth', __name__, url_prefix="/auth", template_folder="templates")






@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and session setup"""
    # Check if user is already logged in
    if 'user_id' in session:
        return redirect(current_app.config.get('DEFAULT_PAGE'))
            
    session.clear()
    response = make_response(render_template('auth/login.html'))
    response.delete_cookie('PHPSESSID')

    php_cookies = [c for c in request.cookies if c.startswith('PHP') or c == 'PHPSESSID']
    for c in php_cookies:
        response.delete_cookie(c)

    if request.method == 'GET':
        current_app.logger.info("Login page loaded with cleared sessions")
        return response

    username = request.form.get('username')
    password = request.form.get('password')
    remember = 'remember' in request.form

    if not username or not password:
        flash('Please provide both username and password', 'danger')
        return response

    auth_model = AuthDB()
    user = auth_model.verify_credentials(username, password)

    if not user:
        flash('Invalid username or password', 'danger')
        return response

    if user['user_id'] in [111,123]:
        session['is_admin'] =True
    else:
        session['is_admin'] =False
        
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    session['home_loc'] = user['home_loc']

    session['_created_at'] = time.time()
    session['_last_activity'] = time.time()



    Theme.update_session(user['user_id'])
    

    from cryptography.fernet import Fernet
    cipher_key = current_app.config.get('CIPHER_KEY')
    if not cipher_key:
        current_app.logger.error("CIPHER_KEY not configured!")
        flash('Authentication error - please contact system administrator', 'danger')
        return response

    cipher = Fernet(cipher_key)
    encrypted_password = cipher.encrypt(password.encode()).decode()
    session['php_password'] = encrypted_password

    session.permanent = remember
    if remember:
        current_app.permanent_session_lifetime = datetime.timedelta(days=30)

    return perform_php_login(username, password, remember)


def perform_php_login(username, password, remember):
    """Attempt login to the legacy PHP site and set session cookies"""
    LEGACY_BASE_URL = current_app.config.get('LEGACY_BASE_URL')
    if not LEGACY_BASE_URL:
        current_app.logger.error("LEGACY_BASE_URL not configured!")
        flash('Configuration error', 'danger')
        return redirect(url_for('main.home'))

    try:
        php_session = requests.Session()
        current_app.logger.info(f"Attempting PHP login at {LEGACY_BASE_URL}/settings/login")

        headers = {
            'User-Agent': request.headers.get('User-Agent', ''),
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': request.headers.get('Accept-Language', ''),
            'Origin': request.host_url.rstrip('/'),
            'Referer': request.host_url + 'login'
        }

        login_data = {
            'email': username,
            'password': password
        }

        php_session.cookies.clear()
        php_login_response = php_session.post(
            f"{LEGACY_BASE_URL}/settings/login",
            data=login_data,
            headers=headers,
            allow_redirects=True,
            verify=False
        )

        current_app.logger.info(f"PHP login response status: {php_login_response.status_code}")
        current_app.logger.info(f"PHP login cookies: {dict(php_session.cookies)}")

        php_session_id = php_session.cookies.get('PHPSESSID')
        current_app.logger.info(f"PHP session ID: {php_session_id}")

        next_page = request.args.get('next')
        redirect_response = redirect(next_page) if next_page and next_page.startswith('/') else redirect(url_for('main.home'))

        if php_session_id:
            redirect_response.set_cookie(
                'PHPSESSID',
                php_session_id,
                max_age=30*24*60*60 if remember else None,
                httponly=True,
                path='/'
            )
        else:
            current_app.logger.error("No PHP session ID found in response cookies!")

        for cookie_name, cookie_value in php_session.cookies.items():
            if cookie_name != 'PHPSESSID':
                redirect_response.set_cookie(
                    cookie_name,
                    cookie_value,
                    max_age=30*24*60*60 if remember else None,
                    httponly=True,
                    path='/'
                )

        return redirect_response

    except Exception as e:
        current_app.logger.error(f"Error during PHP login: {str(e)}")
        flash('Error connecting to legacy system', 'danger')
        return redirect(url_for('main.home'))

@bp.route('/logout')
def logout():
    """Handle user logout with animation and redirect"""
    # Only show logout page if user is logged in
    if 'user_id' in session:
        username = session.get('username', '')
        # Clear session immediately
        session.clear()
        # Show animation page, which will redirect via JavaScript
        return render_template('auth/logout.html')
    
    # Already logged out, redirect to login
    return redirect(url_for('auth.login'))

@bp.route('/logout/confirm')
def logout_confirm():
    """Process logout after confirmation page"""
    # Clear session
    session.clear()
    flash('You have been successfully logged out', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    # Redirect if already logged in
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        agree_terms = 'agree_terms' in request.form
        
        # Validate input
        if not all([first_name, last_name, username, email, location, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        if not agree_terms:
            flash('You must agree to the Terms & Conditions', 'danger')
            return render_template('auth/register.html')
        
        # Get auth model
        auth_model = AuthDB()
        
        # Check for username availability
        if not auth_model.is_username_available(username):
            flash('Username is already taken', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        success, result = auth_model.create_user(
            username, password, email, first_name, last_name, location
        )
        
        if success:
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f'Error creating account: {result}', 'danger')
    
    return render_template('auth/register.html')


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Please provide your email address', 'danger')
            return render_template('auth/forgot_password.html')
        
        # Get auth model
        auth_model = get_auth_model()
        user = auth_model.get_user_by_email(email)
        
        if user:
            # Create reset token
            token = auth_model.create_reset_token(user['user_id'])
            
            # Generate reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send password reset email
            success, message = send_password_reset_email(email, token, reset_url)
            
            if not success:
                # Log the error but don't expose it to user
                current_app.logger.error(f"Failed to send password reset email: {message}")
            
            # Don't reveal if email was sent successfully for security
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


def send_password_reset_email(email, token, reset_url):
    """
    Send password reset email using Office365Mailer and Jinja templates
    
    Args:
        email: Recipient email address
        token: Reset token
        reset_url: Complete reset URL
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Get email config from app config
        config = current_app.config.get('EMAIL_CONFIG', {})
        app_name = current_app.config.get('APP_NAME', 'Performance Radiator')
        
        # Create mailer
        mailer = Office365Mailer(config)
        
        # Get sender from config or use default
        sender = config.get('default_sender', 'noreply@yourcompany.com')
        
        # Prepare template data
        template_data = {
            'app_name': app_name,
            'reset_url': reset_url,
            'token': token,
            'expires_in': '24 hours',
            'user_email': email,
            'now': datetime.now()
        }
        
        # Render template with Jinja2
        template = current_app.jinja_env.get_template('email/reset.html')
        html_body = template.render(**template_data)
        
        # Create plain text version
        text_body = f"""
        Password Reset Request for {app_name}
        
        A password reset has been requested for your account ({email}).
        
        To reset your password, please visit:
        {reset_url}
        
        This link will expire in 24 hours.
        
        If you did not request this reset, please ignore this email.
        """
        
        # Send email
        success, message = mailer.send_graph_api(
            from_email=sender,
            to_email=email,
            subject=f"{app_name} - Password Reset",
            body_text=text_body,
            body_html=html_body
        )
        
        return success, message
        
    except Exception as e:
        return False, str(e)
        
@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    # Get auth model
    auth_model = get_auth_model()
    
    # Verify token
    user_id = auth_model.verify_reset_token(token)
    
    if not user_id:
        flash('Invalid or expired password reset link', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Please provide both password fields', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Reset password
        success = auth_model.reset_password_with_token(token, password)
        
        if success:
            flash('Your password has been reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Error resetting password', 'danger')
    
    return render_template('auth/reset_password.html', token=token)

@bp.route('/api/check-username/<username>')
def check_username(username):
    """API to check if username is available"""
    from flask import jsonify
    
    auth_model = get_auth_model()
    is_available = auth_model.is_username_available(username)
    return jsonify({'available': is_available})