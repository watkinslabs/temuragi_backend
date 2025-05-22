from flask import Blueprint, render_template, abort, request, Response, session, redirect, url_for, current_app, make_response
import requests
import urllib3
from ahoy2.admin.auth.view import perform_php_login


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

no_prefix=True
bp = Blueprint('legacy', __name__, url_prefix='/')


@bp.route('/', defaults={'path': ''})
@bp.route('/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all_v1(path):
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.path))

    LEGACY_BASE_URL = current_app.config.get('LEGACY_BASE_URL')
    php_session_id = request.cookies.get('PHPSESSID')

    # Set up headers from original request
    headers = {
        'User-Agent': request.headers.get('User-Agent', ''),
        'Accept-Language': request.headers.get('Accept-Language', ''),
        'Referer': request.headers.get('Referer', request.url_root),
        'Content-Type': request.headers.get('Content-Type', '')
    }

    # Set up cookies
    cookies = {}
    if php_session_id:
        cookies['PHPSESSID'] = php_session_id

    try:
        target_url = f'{LEGACY_BASE_URL}/{path}'
        
        # Make a request that matches the original method
        method = request.method
        request_kwargs = {
            'headers': headers,
            'cookies': cookies,
            'allow_redirects': False,
            'verify': False
        }
        
        # Add method-specific parameters
        if method == 'GET':
            request_kwargs['params'] = request.args
        elif method in ['POST', 'PUT', 'PATCH']:
            # Handle different content types
            if request.content_type == 'application/json':
                request_kwargs['json'] = request.get_json()
            elif request.content_type == 'application/x-www-form-urlencoded':
                request_kwargs['data'] = request.form
            elif 'multipart/form-data' in request.content_type:
                # Handle file uploads
                request_kwargs['files'] = {name: file for name, file in request.files.items()}
                request_kwargs['data'] = request.form
            else:
                request_kwargs['data'] = request.get_data()
        
        # Make the request with appropriate method
        r = getattr(requests, method.lower())(target_url, **request_kwargs)

        # Handle redirects
        if r.status_code in [301, 302, 303, 307, 308]:
            location = r.headers.get('Location')
            
            # Check if redirecting to login page
            if 'login' in location:
                # Try to auto-login
                if 'username' in session and 'php_password' in session:
                    try:
                        from cryptography.fernet import Fernet
                        cipher = Fernet(current_app.config['CIPHER_KEY'])
                        decrypted_password = cipher.decrypt(session['php_password'].encode()).decode()
                        
                        # Perform login
                        login_result = perform_php_login(session['username'], decrypted_password, session.permanent)
                        
                        # After successful login, retry the original request
                        if login_result and login_result.status_code == 200:
                            # Get the new PHP session ID
                            new_php_session_id = request.cookies.get('PHPSESSID')
                            if new_php_session_id:
                                cookies['PHPSESSID'] = new_php_session_id
                                request_kwargs['cookies'] = cookies
                            
                            # Retry the original request with the same method
                            r = getattr(requests, method.lower())(target_url, **request_kwargs)
                        else:
                            return login_result or redirect(url_for('auth.login', next=request.path))
                    except Exception as e:
                        current_app.logger.error(f"Auto login failed: {str(e)}")
                        flash('Auto login failed. Please login again.', 'danger')
                        return redirect(url_for('auth.login', next=request.path))
                else:
                    return redirect(url_for('auth.login', next=request.path))
            
            # If still redirecting after login attempt, handle that redirection
            if r.status_code in [301, 302, 303, 307, 308]:
                location = r.headers.get('Location')
                if location.startswith('/'):
                    return redirect(location)
                elif location.startswith(LEGACY_BASE_URL):
                    new_path = location.replace(LEGACY_BASE_URL, '')
                    return redirect(f'/v1/{new_path}')
                else:
                    return redirect(location)

        # Create response with the content
        theme=session['theme']
        print(theme)
        response = make_response(render_template('site-themes/' + theme['system_id'] + '.html', content=r.text))
        
        # Set the response status code
        response.status_code = r.status_code
        
        # Copy response headers
        for name, value in r.headers.items():
            if name.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']:
                response.headers[name] = value

        # Copy cookies from the legacy system
        for cookie_name, cookie_value in r.cookies.items():
            response.set_cookie(
                cookie_name,
                cookie_value,
                max_age=30*24*60*60 if session.permanent else None,
                httponly=True,
                path='/'
            )

        return response

    except Exception as e:
        current_app.logger.error(f"Error in catch-all route: {str(e)}")
        return "Error connecting to legacy system", 500