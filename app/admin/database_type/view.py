from flask import Blueprint, render_template, request, jsonify, url_for, current_app, g
from sqlalchemy import desc, asc, text
from sqlalchemy.exc import IntegrityError
import json
import uuid
from datetime import datetime
#from . import engine, Session


from app.admin.connection.connection_model import Connection
from .database_type_model import DatabaseType

bp = Blueprint(
    'database_type',
    __name__,
    url_prefix='/database_type',
    template_folder='tpl',
    static_folder='static'
)

@bp.before_app_request
def bind_session():
    if not hasattr(g, 'session'):
        g.session = current_app.db_session

@bp.teardown_request
def close_session(exc):
    sess = g.pop('session', None)
    if sess:
        sess.close()


@bp.route('/', methods=('GET',))
def home():
    sess = g.session
    return render_template('database_type/list.html')

@bp.route('/data', methods=('POST',))
def data_ajax():
    sess = g.session
    
    # Get DataTables parameters from POST data
    params = request.get_json()
    draw = int(params.get('draw', 1))
    start = int(params.get('start', 0))
    length = int(params.get('length', 10))
    
    # Get sorting parameters
    order_column_idx = 0  # Default to name column
    order_dir = 'asc'
    
    if 'order' in params and params['order']:
        order_column_idx = int(params['order'][0]['column'])
        order_dir = params['order'][0]['dir']
    
    # Column mapping (index to column name)
    columns = ['name', 'display', 'active']
    order_column = columns[order_column_idx]
    
    # Base query
    query = sess.query(DatabaseType)
    
    # Apply column filters
    if 'columns' in params:
        for i, col_info in enumerate(params['columns']):
            if i < len(columns) and 'search' in col_info and col_info['search']['value']:
                col = columns[i]
                search_value = col_info['search']['value']
                
                if col == 'active':
                    if search_value == 'Yes':
                        query = query.filter(DatabaseType.active == True)
                    elif search_value == 'No':
                        query = query.filter(DatabaseType.active == False)
                else:
                    query = query.filter(getattr(DatabaseType, col).ilike(f'%{search_value}%'))
    
    # Count total records (before filtering)
    total_records = sess.query(DatabaseType).count()
    
    # Count filtered records
    filtered_records = query.count()
    
    # Apply sorting
    if order_dir == 'asc':
        query = query.order_by(getattr(DatabaseType, order_column).asc())
    else:
        query = query.order_by(getattr(DatabaseType, order_column).desc())
    
    # Apply pagination - handle the "All" option (-1)
    if length != -1:
        db_types = query.offset(start).limit(length).all()
    else:
        # If length is -1 (All), don't use LIMIT
        db_types = query.offset(start).all()
    
    # Format the data
    data = [{
        'uuid': str(dt.uuid),
        'name': dt.name,
        'display': dt.display,
        'active': 'Yes' if dt.active else 'No'
    } for dt in db_types]
    
    # Prepare response in DataTables format
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@bp.route('/create', methods=('POST',))
def create_ajax():
    sess = g.session
    payload = request.get_json()
    try:
        db_type = DatabaseType(
            name=payload['name'],
            display=payload['display'],
            active=payload.get('active', True)
        )
        sess.add(db_type)
        sess.commit()
        return jsonify(status='ok', msg='Created'), 201
    except Exception as e:
        sess.rollback()
        return jsonify(status='error', msg=str(e)), 400

@bp.route('/update', methods=('POST',))
def update_ajax():
    sess = g.session
    payload = request.get_json()
    db_type = sess.query(DatabaseType).get(uuid.UUID(payload['uuid']))
    if not db_type:
        return jsonify(status='error', msg='Not found'), 404
    try:
        db_type.name = payload['name']
        db_type.display = payload['display']
        db_type.active = payload.get('active', False)
        sess.commit()
        return jsonify(status='ok', msg='Updated')
    except Exception as e:
        sess.rollback()
        return jsonify(status='error', msg=str(e)), 400

@bp.route('/delete', methods=('POST',))
def delete_ajax():
    sess = g.session
    payload = request.get_json()
    db_type = sess.query(DatabaseType).get(uuid.UUID(payload['uuid']))
    if not db_type:
        return jsonify(status='error', msg='Not found'), 404
    
    # Check if this type is being used by any connections
    conn_count = sess.query(Connection).filter_by(db_type=db_type.name).count()
    if conn_count > 0:
        # If in use, just deactivate
        try:
            db_type.active = False
            sess.commit()
            return jsonify(status='ok', msg='Type in use by connections. Deactivated instead.'), 200
        except Exception as e:
            sess.rollback()
            return jsonify(status='error', msg=str(e)), 400
    else:
        # If not in use, actually delete it
        try:
            sess.delete(db_type)
            sess.commit()
            return jsonify(status='ok', msg='Deleted'), 200
        except Exception as e:
            sess.rollback()
            return jsonify(status='error', msg=str(e)), 400

 