from flask import session, redirect, url_for, request

def require_login_except_paths(exempt_paths):
    """
    Creates a function to require login on all paths except those specified
    
    Args:
        exempt_paths: List of path prefixes that don't require login
    """
    @app.before_request
    def before_request():
        exempt_paths = [
            url_for('auth.login'),     
            url_for('auth.register'),   
            url_for('auth.forgot-password'),
            url_for('auth.reset_password'),
            url_for('auth.check-username'),
            '/static/',         
        ]

        # Skip check if path is exempt
        path = request.path
        
        # Check if current path is in exempt paths
        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return None
                
        # Check login status
        if not session or 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
            
        # Update last activity time for session timeout management
        session['_last_activity'] = time.time()
            
        return None
        
    return check_login

