# routes/menu_routes.py
from flask import session, request
from .menu_builder import MenuBuilder
from app.models import  Menu

# Context processor for Flask application
def register_menu_context_processor(app):
    """Register menu context processor with Flask app"""
    
    @app.context_processor
    def inject_menu():
        """
        Context processor that adds menu object to all templates
        This eliminates the need to pass menu in each render_template call
        """
        

        # Get user information from session
        user_id = session.get('user_id')
        user_name = session.get('username')

        # Generating the menu
        root_id = 0
        current_menu_id = 352

        # Parse URL segments (equivalent to CodeIgniter's URI segments)
        path_parts = request.path.strip('/').split('/')
        controller = path_parts[0] if path_parts and path_parts[0] else 'index'

        segment2 = None
        segment3 = None        
        
        # Handle segment2 and segment3 (page determination)
        if len(path_parts) > 1:
            segment2 = path_parts[1]
            segment3 = path_parts[2] if len(path_parts) > 2 else None

        # Join segments 2 and 3 if they exist
        page = segment2
        if segment3:
            page += '/' + segment3
        else:
            segment2 = None
            segment3 = None
            page = 'index'
        theme=session.get('theme',{'system_id':'modern_top','wide':False,'menu_location':'top','show_icons':True})
        #print(theme)
        # Now we can create our menu
        if  user_id :
            menu_model=Menu()

            menu = MenuBuilder(controller, 
                        page, 
                        user_id, 
                        current_menu_id, 
                        mega_menu=theme['menu_location']=='top', 
                        show_icons=theme['show_icons'],
                        quick_links=menu_model.get_quick_links(),
                        menu_links=menu_model.get_menu() )
        else :
            menu=None
        return {'menu': menu}


