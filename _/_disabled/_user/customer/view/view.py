from flask import Blueprint, render_template, abort, request, Response, session, redirect, url_for, current_app, flash, g, jsonify
import requests
from typing import Dict, Any, List


bp = Blueprint('customer_view', __name__, url_prefix='/customer/view', template_folder="templates")



@bp.route('/')
@bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Route to display and process customer creation form
    """
    # Get region from query param or default to GPACIFIC
    region = request.args.get('region', 'pacific')
    
    
    return render_template('customer_view/dashboard.html')