from flask import Blueprint, render_template, abort, request, Response, session, redirect, url_for, current_app, flash, g, jsonify
import requests
from typing import Dict, Any, List
from .model import CustomerManager


bp = Blueprint('customer_create', __name__, url_prefix='/customer/create', template_folder="templates")

# Helper function to get customer classes for dropdown
def get_customer_classes() -> List[Dict[str, str]]:
    """
    Get list of customer classes for dropdown
    
    Returns:
        List of dictionaries with class value and text
    """
    try:
        db = current_app.db
        query = "select BK_CLASS_CLASS as class, BK_CLASS_DESC  as [desc] from jadvdata.dbo.bkclass ORDER BY BK_CLASS_CLASS ASC"
        classes = db.fetch_all(query)
        return [{"value": cls['class'], "text": f"{cls['class']} - {cls['desc']}"} for cls in classes]
    except Exception as e:
        current_app.logger.error(f"Error getting customer classes: {str(e)}")
        return []

@bp.route('/')
@bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Route to display and process customer creation form
    """
    # Get region from query param or default to GPACIFIC
    region = request.args.get('region', 'pacific')
    
    # Default form data and state variables
    customer_data = {}
    errors = []
    success = False
    customer_code = -1
    password = ""
    
    # Get customer classes for dropdown
    class_list = get_customer_classes()
    
    if request.method == 'POST':
        # Extract all form fields
        customer_data = {
            'customer_name': request.form.get('customer_name', ''),
            'address1': request.form.get('address1', ''),
            'address2': request.form.get('address2', ''),
            'zip_code': request.form.get('zip_code', ''),
            'store_number': request.form.get('store_number', 0),
            'customer_class': request.form.get('customer_class', ''),
            'phone_number': request.form.get('phone_number', ''),
            'phone_ext': request.form.get('phone_ext', ''),
            'phone_desc': request.form.get('phone_desc', ''),
            'fax_number': request.form.get('fax_number', ''),
            'contact_person': request.form.get('contact_person', ''),
            'email': request.form.get('email', ''),
            'comments1': request.form.get('comments1', ''),
            'comments2': request.form.get('comments2', ''),
            'mail_preference': request.form.get('mail_preference', 'N'),
            'po_required': request.form.get('po_required', 'N'),
            'saturday_delivery': request.form.get('saturday_delivery', 'N'),
            'lucky7': request.form.get('lucky7', 'N'),
            'statement_type': request.form.get('statement_type', '')
        }
        
        # Get region from form
        region = request.form.get('region', 'pacific')
        
        # Get user ID from session
        user_id = session.get('user_id', 0)
        
        # Create customer manager
        manager = CustomerManager(region=region)
        
        # Process customer creation
        result = manager.create_customer(customer_data, user_id)
        
        if result['success']:
            success = True
            customer_code = result['customer_code']
            password = result['password']
            flash(f"Customer created successfully. Customer code: {customer_code}", "success")
            
            # Redirect to customer view page if needed
            if customer_code > 0:
                return redirect(url_for('customer_account.view', code=customer_code))
        else:
            errors = result['errors']
            for error in errors:
                flash(error, "error")

    # Prepare data for template
    data = {
        'region': region,
        'customer_data': customer_data,
        'errors': errors,
        'success': success,
        'customer_code': customer_code,
        'password': password,
        'class_list': class_list,
        'code': -1,  # Default code for new customer
        'title': f"Create Customer - {'Canada' if region == 'GCANADA' else 'Pacific'}"
    }
    
    return render_template('cust_create/create.html', **data)

@bp.route('/lookup-zip', methods=['POST'])
def lookup_zip():
    """
    API endpoint to look up zip code data via POST
    """
    # Get POST data
    request_data = request.get_json()
    
    if not request_data or 'zip_code' not in request_data:
        return jsonify({
            'success': False,
            'message': 'Zip code is required'
        }), 400
    
    zip_code = request_data.get('zip_code')
    
    manager = CustomerManager()
    zip_data = manager.get_zip_data(zip_code)
    
    # Set the region based on country
    region = 'pacific'
    if zip_data:
        if zip_data.get('country', '').upper().find('CANADA') >= 0:
            region = 'canada'
        
        return jsonify({
            'success': True,
            'city': zip_data['city'],
            'state': zip_data['state'],
            'country': zip_data['country'],
            'sales_person': zip_data['sales_person'],
            'region': region
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Zip code not found'
        })


@bp.route('/lookup-phone', methods=['POST'])
def lookup_phone():
    """
    API endpoint to look up phone number data
    """
    # Get POST data
    request_data = request.get_json()
    phone_number = request_data.get('phone_number', '')
    
    # Initialize manager and look up phone
    manager = CustomerManager()
    result = manager.lookup_by_phone_number(phone_number)
    print (result)
    # Set appropriate HTTP status code based on result
    status_code = 200
    #if not result['success']:
    #    status_code = 400 if result['status'] == 'invalid' else 404
        
    return jsonify(result), status_code