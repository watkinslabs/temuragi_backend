
from app.classes import CSRFProtection


def register_csrf(app):
    """Register CSRF protection for the application"""
    csrf = CSRFProtection(app)
    app.csrf = csrf
    app.extensions['csrf'] = csrf
    
    # Generate token for templates
    @app.context_processor
    def inject_csrf_token():
        token_func = csrf.generate_token
        return {'csrf_token': token_func}
