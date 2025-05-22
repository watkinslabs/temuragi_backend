
"""
Messages Blueprint for Performance Radiator application
BSD 3-Clause License
"""
import datetime
from flask import Blueprint, render_template, url_for, session, redirect, request, jsonify, current_app

# Create blueprint
bp = Blueprint('messages', __name__ ,url_prefix="/messages", template_folder="templates")



@bp.route('/')
@bp.route('/home')
def home():
    """Display message inbox"""
    messages = get_user_messages(session['user_id'])
    return render_template('home.html', 
                          messages=messages)
