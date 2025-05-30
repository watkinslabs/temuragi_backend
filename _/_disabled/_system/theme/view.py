from flask import Blueprint, render_template, session, request, redirect, url_for, session
from .model import Theme

# Create blueprint with URL prefix
bp = Blueprint('theme', __name__, url_prefix="/theme", template_folder="templates")




@bp.route('/', methods=['GET', 'POST'])
def home():
    """Display theme selection page"""
    
    
    # Initialize theme model
    theme = Theme()
    
    # Get user_id from session
    user_id = session.get('user_id')
    
    # Get data from model
    themes = Theme.get_all_themes()
    user_preferences = Theme.get_user_preference(user_id)
    
    # Prepare data for template
    data = {
        'themes': themes,
        'user_theme': user_preferences.id
    }
    
    return render_template('theme/home.html', **data)


@bp.route('/update_preferences', methods=['POST'])
def update_preferences():
    """Update user theme preferences"""
    user_id = session.get('user_id')
    
    if request.method == 'POST' and user_id:
        theme_id = request.form.get('theme_id')

        print (theme_id)
        
        # Save preference using model
        Theme.save_user_preference(user_id, theme_id)
        Theme.update_session(user_id)

        # Redirect to theme index page
        return redirect(url_for('theme.home'))
    
    # Handle error or unauthorized access
    return "Unauthorized access", 403

