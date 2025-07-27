import secrets
import hmac
import hashlib
import time
from datetime import datetime, date
from flask import current_app, abort, request,jsonify

class CSRFProtection:
    """Simple CSRF protection with daily token validation"""
    
    def __init__(self, app=None, csrf_secret=None):
        self.csrf_secret = csrf_secret
        self.exempt_endpoints = set()
        self.exempt_blueprints = set()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app and register before_request hook"""
        if not self.csrf_secret:
            self.csrf_secret = app.config.get('csrf_secret')
        if not self.csrf_secret:
            raise ValueError("csrf_secret must be set")
        
        # Register global before_request handler
        app.before_request(self._before_request)
    
    def _before_request(self):
        """Check CSRF on every request"""
        # Only check on state-changing methods

        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return
        
        # Exempt localhost requests
        if request.remote_addr in ['127.0.0.1', 'localhost', '::1']:
            current_app.logger.debug(f"CSRF check skipped for localhost request from {request.remote_addr}")
            return
        
        # Also check for forwarded IPs if behind a proxy
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Get the first IP in the chain (original client)
            client_ip = forwarded_for.split(',')[0].strip()
            if client_ip in ['127.0.0.1', 'localhost', '::1']:
                current_app.logger.debug(f"CSRF check skipped for localhost request from {client_ip} (via X-Forwarded-For)")
                return
        
        # Exempt internal requests with specific headers
        if (request.headers.get('X-Internal-Request') == 'true' and 
            request.headers.get('X-Source') == 'temuragi-web-init'):
            current_app.logger.debug("CSRF check skipped for internal request (X-Internal-Request + X-Source headers)")
            return
        
        # Check if endpoint is exempt
        if request.endpoint in self.exempt_endpoints:
            return
        
        # Check if blueprint is exempt
        if request.endpoint and '.' in request.endpoint:
            blueprint = request.endpoint.split('.')[0]
            if blueprint in self.exempt_blueprints:
                return
        
        # Validate CSRF token
        self.protect(request)
        
    def exempt(self, endpoint):
        """Exempt an endpoint from CSRF protection"""
        self.exempt_endpoints.add(endpoint)
    
    def exempt_blueprint(self, blueprint_name):
        """Exempt entire blueprint from CSRF protection"""
        self.exempt_blueprints.add(blueprint_name)
    
    def generate_token(self):
        """Generate unique token that's valid for the day"""
        # Random component for uniqueness
        random_part = secrets.token_hex(16)
        
        # Daily component for validation
        daily_salt = date.today().isoformat()
        
        # Create signature for the daily validation
        message = f"{self.csrf_secret}:{daily_salt}:{random_part}".encode('utf-8')
        signature = hashlib.sha256(message).hexdigest()[:16]  # First 16 chars is enough
        
        # Combine random part with signature
        token = f"{random_part}{signature}"
        
        return token
    
    def validate_token(self, token):
        """Validate CSRF token - check if it was generated today"""
        if not token or len(token) < 48:  # 32 chars random + 16 chars signature
            return False
        
        # Split token
        random_part = token[:32]
        provided_signature = token[32:48]
        
        # Recreate signature with today's date
        daily_salt = date.today().isoformat()
        message = f"{self.csrf_secret}:{daily_salt}:{random_part}".encode('utf-8')
        expected_signature = hashlib.sha256(message).hexdigest()[:16]
        
        # Compare signatures
        return hmac.compare_digest(provided_signature, expected_signature)
    
    def get_token_from_request(self, request):
        """Extract token from request"""
        # Check headers first (AJAX)
        if request.headers.get('X-CSRF-Token'):
            return request.headers.get('X-CSRF-Token')
        
        # Check form data
        if request.form:
            return request.form.get('csrf_token')
        
        # Check JSON body
        if request.is_json and request.json:
            return request.headers.get('X-CSRF-Token')

        return None
    
    def protect(self, request):
        """Validate CSRF token from request"""
        token = self.get_token_from_request(request)
        results=jsonify({'success':False,'csrf_invalid':True})
        if not self.validate_token(token):
            abort(403, results)
        
        return True