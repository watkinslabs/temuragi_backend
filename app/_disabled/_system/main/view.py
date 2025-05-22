import datetime
from flask import Blueprint, render_template, url_for, session, redirect, request, jsonify, current_app

# Create blueprint
bp = Blueprint('main', __name__, url_prefix="/", template_folder="templates")




@bp.route('/')
@bp.route('/home')
def home():
    from datetime import datetime
    current_year = datetime.now().year
    
    return render_template('main/home.html')



