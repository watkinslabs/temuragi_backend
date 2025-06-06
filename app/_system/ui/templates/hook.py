from types import SimpleNamespace
from flask import request, url_for, session, current_app
import os
import datetime

def get_client_ip():
    # Get IP from X-Forwarded-For header (HAProxy adds this)
    forwarded_for = request.headers.get('X-Forwarded-For')
    
    if forwarded_for:
        # The leftmost IP in the list is the original client IP
        client_ip = forwarded_for.split(',')[0].strip()
    else:
        # Fallback to remote address if header not present
        client_ip = request.remote_addr
    
    return client_ip


def get_page_data_for_jinja_render(session, page_name):
    """
    Fetch theme, template, and page objects for Jinja templating.
    
    Args:
        session: SQLAlchemy session
        page_name (str): Name/identifier of the page
    
    Returns:
        tuple: (theme, template, page) or (None, None, None) if not found
    """
    theme=None
    template=None
    page=None

    try:
        from app.models import Page,Template,Theme
        # Query the page by name
        page = session.query(Page).filter_by(name=page_name).first()
        if not page:
            return None, None, None
        
        # Get the associated template
        template = session.query(Template).filter_by(id=page.template_id).first()
        if not template:
            return None, None, None
        
        # Get the associated theme
        theme = session.query(Theme).filter_by(id=template.theme_id).first()
    except Exception as ex:
        print(ex)

    return {
        'theme': theme,
        'template': template,
        'page': page
    }
    





def register_template_processor(app):
    """Register session variables context processor with Flask app"""
    
    def add_max_filter(app):
        @app.template_filter('max_value')
        def max_value(a, b):
            return max(a, b)
                
    @app.context_processor
    def inject_session():
        # Determine if user is logged in
        logged_in = 'user_id' in session
        logged_in=True
        template_page_private= "Light-2025/base.html"
        template_page_public= "Light-2025/public_base.html"

        theme="F"
        #theme=get_page_data_for_jinja_render(session, "default"):
    



        #print(thm.system_id)
                
        context = {
            # Session data

            'active_page_path':template_page_private,
            'is_admin': session.get('is_admin', False),
            'user_id': session.get('user_id', None),
            'username': session.get('username', None),
            'logged_in': logged_in,
            'theme': theme,
            'theme_path': "Light-2025/base.html",
            'server_addr': request.host,
            'current_year': datetime.datetime.now().year,
            'client_ip':get_client_ip(),
            'javascripts': [],
            
        }
        

        for key in app.config['site_template']:
            value=app.config['site_template'][key]
            context[key.lower()]=value

        return context

    # Define custom template filters
    @app.template_filter('type')
    def type_filter(value):
        return type(value).__name__
    
    @app.template_filter('pprint')
    def pprint_filter(value):
        import pprint
        return pprint.pformat(value)

    @app.template_filter('datetime')
    def datetime_filter(value, fmt="%Y-%m-%d %H:%M:%S"):
        return value.strftime(fmt)
