from flask import Blueprint, render_template_string, request, redirect, url_for, flash, g

from app.classes import AuthService

# Create auth blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')



@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login view - just calls auth service"""
    if request.method == 'POST':
        # Get form data
        identity = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        # Get auth service and perform login
        auth = AuthService(g.session)
        result = auth.login(identity, password, remember)
        
        if result['success']:
            flash('Welcome back!', 'success')
            
            return redirect(url_for('home.index'))
            
        else:
            flash(result['message'], 'danger')

    from app.classes import TemplateRenderer
    from app.models import Page

    page = g.session.query(Page).filter_by(slug='login').first()
    renderer = TemplateRenderer(g.session)
    
    return renderer.render_page(page.uuid)
    

@bp.route('/logout')
def logout():
    "" "Logout view"" "
    auth = AuthService(g.session)
    result = auth.logout()
    flash(result['message'], 'info')
    return redirect(url_for('auth.login'))


@bp.route('/forgot_password')
def forgot_password():
    "" "Logout view"" "
    return ""



