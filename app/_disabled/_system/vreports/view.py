# routes/virtual_reports.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Response, current_app, flash
from .model import VirtualReport
import datetime
import base64
import json
import csv
from io import StringIO
from app.utils.forms import parse_form
import logging
bp = Blueprint('virtual_reports', __name__,  url_prefix="/report", template_folder="templates")
model = VirtualReport()

            


@bp.route('/', methods=['GET', 'POST'])
def index():
    print(request.form)
    
    # Get report statistics for dashboard
    stats = model.get_report_stats()
    
    return render_template('vreports/home.html', stats=stats)

@bp.route('/get_reports', methods=['POST'])
def get_reports():
    # Get pagination parameters
    limit = int(request.form.get('length', 10))
    offset = int(request.form.get('start', 0))
    
    # Get search value
    search_value = request.form.get('search[value]', '').strip()
    
    # Get column-specific search values
    column_search = {}
    columns_search_data = request.form.get('columnsSearch', None)
    
    if columns_search_data:
        # If it's JSON, parse it
        if isinstance(columns_search_data, str):
            try:
                column_search = json.loads(columns_search_data)
            except:
                pass
        # If it's already a dict
        elif isinstance(columns_search_data, dict):
            column_search = columns_search_data
    
    # Manually check for individual columnsSearch[index] parameters
    for i in range(4):  # 4 searchable columns
        column_key = f'columnsSearch[{i}]'
        if column_key in request.form:
            column_search[str(i)] = request.form[column_key]
    
    # Print debug information
    #print("Column search data:", column_search)
    
    # Sorting
    columns = ["r.id", "p1.title", "p2.controller", "r.name"]
    order_column_index = int(request.form.get('order[0][column]', 0))
    order_dir = request.form.get('order[0][dir]', 'asc').upper()
    order_column = columns[order_column_index]
    
    # Get reports with pagination
    result = model.get_reports(limit, offset, search_value, order_column, order_dir, column_search)
    
    # Return JSON response
    return jsonify({
        "draw": int(request.form.get('draw', 0)),
        "recordsTotal": result['recordsTotal'],
        "recordsFiltered": result['recordsFiltered'],
        "data": result['data']
    })

@bp.route('/edit', methods=['POST'])
def edit():
    new_report= request.form.get('new',None)

    
    data = {}
    if new_report:
        print("NEW")
        results = model.create_new_report({})
        if not results['success']:
            return

        id=results['report_id']
        report = model.get_report_by_id(id)
        print(report)
        if report:
            # Check if link_id is missing and create if needed
            if not report.get('link_id'):
                model.create_permission_for_report(id)
                report = model.get_report_by_id(id)

        data['report'] = report
        data['variables'] = report.get('variables', [])
        data['columns'] = report.get('columns', [])

            

    else:
        id=request.form.get('id',None)
        print (f"IN EDIT {id}")
        # POST request - Parse the form data
        form_data = parse_form(request.form)
        
        if 'run' in form_data:
            # Handle "Run" button press
            query = form_data.get('query', '').strip()
            query = query.rstrip(';')
            
            # Create report object from form data
            report = {
                'id': form_data.get('id'),
                'query': query,
                'name': form_data.get('name'),
                'description': form_data.get('description'),
                'link_id': form_data.get('link_id'),
                'link_parent': form_data.get('link_parent'),
                'link_text': form_data.get('link_text'),
                'related_report': form_data.get('related'),
                'is_ajax': 1 if form_data.get('is_ajax') == 'on' else 0,
                'limit_by_user': 1 if form_data.get('limit_by_user') == 'on' else 0,
                'is_wide': 1 if form_data.get('is_wide') == 'on' else 0,
                'limit_display': 1 if form_data.get('limit_display') == 'on' else 0,
                'is_public': 1 if form_data.get('is_public') == 'on' else 0,
                'is_auto_run': 1 if form_data.get('is_auto_run') == 'on' else 0,
                'is_searchable': 1 if form_data.get('is_searchable') == 'on' else 0,
                'display': form_data.get('display', form_data.get('name', ''))
            }            
            # Process variables from the form
            variables = []
            variable_names = set()  # Keep track of existing variable names
            params = {}  # Dictionary to hold parameter values for query execution
            
            for variable in form_data.get('variables', []):
                if not variable.get('name') or not variable['name'].strip():
                    continue
                
                # Clean up the variable
                variable_name = variable['name'].strip()
                variable_names.add(variable_name)
                
                if variable.get('query'):
                    variable['query'] = variable['query'].strip()
                
                # Add to variables list
                variables.append(variable)
                
                # Add parameter value (using default)
                params[variable_name] = variable.get('default', '')
            
            # Extract parameters from the query that don't have variables yet
            import re
            # Find all placeholders in format :param or %(param)s
            param_pattern = r':([a-zA-Z0-9_]+)|%\(([a-zA-Z0-9_]+)\)s'
            param_matches = re.finditer(param_pattern, query)
            
            for match in param_matches:
                # Get the parameter name (could be in group 1 or 2 depending on format)
                param_name = match.group(1) if match.group(1) else match.group(2)
                
                # If this parameter doesn't have a variable yet, create one
                if param_name not in variable_names:
                    # Create display name by replacing underscores/dashes with spaces and capitalizing first letter
                    display_name = param_name.replace('_', ' ').replace('-', ' ')
                    display_name = ' '.join(word.capitalize() for word in display_name.split())
                    
                    # Determine appropriate type and default value based on parameter name
                    var_type = 'text'  # Default type
                    default_value = ''
                    
                    # Try to infer type from name
                    lower_name = param_name.lower()
                    
                    # Date/Time related
                    if any(kw in lower_name for kw in ['datetime', 'timestamp']):
                        var_type = 'datetime'
                        from datetime import datetime
                        default_value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    elif any(kw in lower_name for kw in ['date', 'day', 'month', 'year']):
                        var_type = 'date'
                        from datetime import date
                        default_value = date.today().strftime('%Y-%m-%d')
                    
                    # Money related
                    elif any(kw in lower_name for kw in ['amount', 'price', 'cost', 'fee', 'salary', 'revenue', 'budget']):
                        var_type = 'money'
                        default_value = '0.00'
                    
                    # Numeric related
                    elif any(kw in lower_name for kw in ['id', 'num', 'count', 'qty', 'quantity', 'total']):
                        var_type = 'int'
                        default_value = '0'
                    elif any(kw in lower_name for kw in ['percent', 'rate', 'ratio', 'factor', 'multiplier', 'decimal']):
                        var_type = 'numeric'
                        default_value = '0'
                    
                    # Boolean related
                    elif any(kw in lower_name for kw in ['is_', 'has_', 'can_', 'enable', 'active', 'status', 'flag']):
                        var_type = 'bool'
                        default_value = 'false'
                    
                    # URL related
                    elif any(kw in lower_name for kw in ['url', 'link', 'website', 'site', 'domain', 'http']):
                        var_type = 'url'
                        default_value = 'https://'
                    
                    # Alpha (letters only) related
                    elif any(kw in lower_name for kw in ['code', 'abbr', 'abbrev', 'symbol', 'alpha']):
                        var_type = 'alpha'
                        default_value = ''
                    
                    # Create new variable
                    new_variable = {
                        'name': param_name,
                        'display': display_name,
                        'type': var_type,
                        'default': default_value,
                        'order': len(variables)  # Add at the end
                    }
                    
                    variables.append(new_variable)
                    variable_names.add(param_name)
                    
                    # Add parameter value
                    params[param_name] = default_value
            
            # Get columns from test run with parameters
            try:
                columns = model.get_columns_from_test_query(query, params)
            except Exception as e:
                # Handle query execution error
                flash(f"Error executing query: {str(e)}", 'error')
                columns = []
            
            data['report'] = report
            data['columns'] = columns
            data['variables'] = variables
            
        elif 'save' in form_data:
            # Handle "Save" button press
            print("SAVE")
            
            # Create a report object with main form fields
            report = {
                'id': form_data.get('id'),
                'name': form_data.get('name'),
                'display': form_data.get('display', form_data.get('name', '')),
                'description': form_data.get('description'),
                'link_id': form_data.get('link_id'),
                'link_parent': form_data.get('link_parent'),
                'link_text': form_data.get('link_text'),
                'related_report': form_data.get('related_report'),
                'query': form_data.get('query', '').strip(),
                'is_ajax': 1 if form_data.get('is_ajax') == 'on' else 0,
                'limit_by_user': 1 if form_data.get('limit_by_user') == 'on' else 0,
                'is_wide': 1 if form_data.get('is_wide') == 'on' else 0,
                'limit_display': 1 if form_data.get('limit_display') == 'on' else 0,
                'is_public': 1 if form_data.get('is_public') == 'on' else 0,
                'is_auto_run': 1 if form_data.get('is_auto_run') == 'on' else 0,
                'is_searchable': 1 if form_data.get('is_searchable') == 'on' else 0
            }
            
            # Process columns - now directly available as a list
            columns = []
            for column in form_data.get('columns', []):
                if not column.get('name') or not column['name'].strip():
                    continue
                columns.append(column)
            
            # Process variables - now directly available as a list
            variables = []
            for variable in form_data.get('variables', []):
                if not variable.get('name') or not variable['name'].strip():
                    continue
                
                if variable.get('query'):
                    variable['query'] = base64.b64encode(variable['query'].strip().encode()).decode()
                
                variables.append(variable)

            report['columns'] = columns
            report['variables'] = variables
            data['report'] = report
            data['variables'] = report.get('variables', [])
            data['columns'] = report.get('columns', [])

            # Update report in da tabase
            model.update_report(report)
        else:            
            # Reload report data
            print(f"ID: {id}")
            report = model.get_report_by_id(id)
            data['report'] = report
            data['variables'] = report.get('variables', [])
            data['columns'] = report.get('columns', [])


    # Get groupers and reports for dropdowns
    data['groupers'] = model.get_groupers()
    data['reports'] = model.get_all_reports()
    
    return render_template('vreports/edit.html', **data)

@bp.route('/view', methods=['GET', 'POST'])
def view():
    id= request.form.get('id',0)

    print(f"ID:{id}")
    data = {
        'report_id': id,
    }
    # Get report
    if id==0:
        return redirect(url_for('virtual_reports.index'))


    report = model.get_report_for_view(id)
    
    
    if not report:
        return redirect(url_for('virtual_reports.index'))
    
    # Check if report is public or user has access
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    if report.get('id_public') != 1 and not is_admin:
        # Check if user has permission to view this report
        if not model.has_permission(user_id, report['id']):
            return redirect(url_for('virtual_reports.index'))
    
    
    # Set wide display if needed
    if report.get('is_wide') == 1:
        data['wide'] = True
    
    vars_data = report.get('variables', [])
    data['report'] = report
    data['columns'] = report.get('columns', [])
    
    
    # Handle variables from form
    if request.method == 'POST' and request.form.get('vars'):
        vars_form = request.form.get('vars')
        
        # Create lookup dict for better performance
        vars_by_name = {var.name: i for i, var in enumerate(vars_data)}
        
        # Process values
        for name, value in vars_form.items():
            if name in vars_by_name:
                key = vars_by_name[name]
                vars_data[key].value = value
    
    data['variables'] = vars_data
    
    # Set CSV filename
    user_id = session.get('user_id', 'unknown')
    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    data['csv_file_name'] = f"{timestamp}-{report['name']}[{user_id}].csv"
    
    
    
    return render_template('vreports/view.html', **data)

@bp.route('/run_report/<int:id>', methods=['POST'])
def run_report(id):
   
    # Execute report query
    try:
        # Run the report with variables, pagination, and user limiting
        result = model.run_report_query(
            request
        )
        
        # Return results in DataTables format
        return result
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "draw": int(request.form.get('draw', 0)),
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }), 500

@bp.route('/export_csv/<int:id>', methods=['GET', 'POST'])
def export_csv(id):
    # Get report
    report = model.get_report_for_view(id)
    
    if not report:
        return "Report not found", 404
    
    # Get variables from form or query params depending on request method
    if request.method == 'POST':
        vars_form = request.form.get('vars', {})
    else:
        vars_form = request.args.to_dict()
    
    # Get user ID for limiting if needed
    user_id = session.get('user_id') if report.get('limit_by_user') == 1 else None
    
    try:
        # Execute the query without pagination
        result = model.run_report_query(report, vars_form, user_id=user_id, for_export=True)
        rows = result['rows']
        
        if not rows:
            return "No data found", 404
        
        # Create CSV
        csv_data = StringIO()
        writer = csv.DictWriter(csv_data, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
        # Generate filename
        user_id = session.get('user_id', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M')
        filename = f"{timestamp}-{report['name']}[{user_id}].csv"
        
        # Create a response with the CSV data
        csv_output = csv_data.getvalue()
        response = Response(csv_output, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    except Exception as e:
        return str(e), 500

@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Display dashboard with report statistics"""
    # Get statistics from the model
    stats = model.get_report_stats()
    
    # Get most recently used reports
    recent_reports = model.get_recent_reports(10)
    
    # Get most popular reports
    popular_reports = model.get_popular_reports(10)
    
    return render_template('vreports/dashboard.html', 
                          stats=stats,
                          recent_reports=recent_reports,
                          popular_reports=popular_reports)

@bp.route('/delete', methods=['POST'])
def delete():
    report_id = request.values.get('id', type=int)
    if not report_id:
        flash('No report ID provided', 'danger')
        return redirect(url_for('virtual_reports.index'))
    
    try:
        results=model.delete(report_id);       

        return redirect(url_for('virtual_reports.index'))
    except Exception as e:
        return redirect(url_for('virtual_reports.index'))
