from flask import Blueprint, render_template_string, request, redirect, url_for, flash, g, jsonify

from app.classes import AuthService

# Create auth blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')



@bp.route('/login', methods=['GET'])
def login():
    """Login view - just calls auth service"""
    from app.classes import TemplateRenderer
    from app.models import Page

    page = g.session.query(Page).filter_by(slug='login').first()
    renderer = TemplateRenderer(g.session)
    
    return renderer.render_page(page.id)
    
