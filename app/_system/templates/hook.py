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
        thm=	SimpleNamespace(**{'dark_mode': False,
                'default': False,
                'description': 'Modern Style with traditional Mega Menu on the top of the '
                                'page.',
                'id': 5,
                'menu_location': 'top',
                'name': 'Modern Mega Menu',
                'search': False,
                'show_icons': False,
                'system_id': 'default',
                'wide': False})
        print(thm.system_id)
                
        context = {
            # Session data
            'is_admin': session.get('is_admin', False),
            'user_id': session.get('user_id', None),
            'username': session.get('username', None),
            'home_loc': session.get('home_loc', None),
            'logged_in': logged_in,
            'theme': session.get('theme',thm),
            'server_addr': request.host,
            'mail': {'unread': 0, 'read': 0},
            'current_year': datetime.datetime.now().year,
            'active_customer_switcher': '',
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
