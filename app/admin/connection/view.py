from flask import Blueprint, render_template, request, jsonify, url_for, current_app, g
from sqlalchemy import desc, asc, text
from sqlalchemy.exc import IntegrityError
import json
import uuid
from datetime import datetime


from .connection_model import Connection
from app.admin.database_type.database_type_model import DatabaseType


bp = Blueprint(
    'connection',
    __name__,
    url_prefix='/connection',
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
    db_types = sess.query(DatabaseType).filter_by(active=True).all()
    db_types_tuples = [(dt.name, dt.display) for dt in db_types]
    
    return render_template('connection/list.html', db_types=db_types_tuples)

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
    columns = ['name', 'db_type', 'connection_string', 'active']
    order_column = columns[order_column_idx]
    
    # Base query
    query = sess.query(Connection)
    
    # Apply column filters
    if 'columns' in params:
        for i, col_info in enumerate(params['columns']):
            if i < len(columns) and 'search' in col_info and col_info['search']['value']:
                col = columns[i]
                search_value = col_info['search']['value']
                
                if col == 'active':
                    if search_value == 'Yes':
                        query = query.filter(Connection.active == True)
                    elif search_value == 'No':
                        query = query.filter(Connection.active == False)
                else:
                    query = query.filter(getattr(Connection, col).ilike(f'%{search_value}%'))
    
    # Count total records (before filtering)
    total_records = sess.query(Connection).count()
    
    # Count filtered records
    filtered_records = query.count()
    
    # Apply sorting
    if order_dir == 'asc':
        query = query.order_by(getattr(Connection, order_column).asc())
    else:
        query = query.order_by(getattr(Connection, order_column).desc())
    
    # Apply pagination - handle the "All" option (-1)
    if length != -1:
        conns = query.offset(start).limit(length).all()
    else:
        # If length is -1 (All), don't use LIMIT
        conns = query.offset(start).all()
    
    # Format the data
    data = [{
        'uuid': str(c.uuid),
        'name': c.name,
        'db_type': c.db_type,
        'connection_string': c.connection_string,
        'credentials': c.credentials,
        'options': c.options,
        'active': 'Yes' if c.active else 'No'
    } for c in conns]
    
    # Prepare response in DataTables format
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

@bp.route('/list', methods=['GET'])
def list_ajax():
    """Get list of active connections"""
    session = g.session
    
    try:
        connections = session.query(Connection).filter_by(active=True).all()
        
        data = [{
            'uuid': str(conn.uuid),
            'name': conn.name,
            'db_type': conn.db_type
        } for conn in connections]
        
        return jsonify({
            'connections': data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting connections: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/create', methods=('POST',))
def create_ajax():
    sess = g.session
    payload = request.get_json()
    try:
        conn = Connection(
            name=payload['name'],
            db_type=payload['db_type'],
            connection_string=payload['connection_string'],
            credentials=payload.get('credentials'),
            options=payload.get('options'),
            active=payload.get('active', True)
        )
        sess.add(conn)
        sess.commit()
        return jsonify(status='ok', msg='Created'), 201
    except Exception as e:
        sess.rollback()
        return jsonify(status='error', msg=str(e)), 400

@bp.route('/update', methods=('POST',))
def update_ajax():
    session = g.session

    payload = request.get_json()
    conn = session.query(Connection).get(uuid.UUID(payload['uuid']))
    if not conn:
        return jsonify(status='error', msg='Not found'), 404
    try:
        conn.name              = payload['name']
        conn.db_type           = payload['db_type']
        conn.connection_string = payload['connection_string']
        conn.credentials       = payload.get('credentials')
        conn.options           = payload.get('options')
        conn.active            = payload.get('active', False)
        session.commit()
        return jsonify(status='ok', msg='Updated')
    except Exception as e:
        session.rollback()
        return jsonify(status='error', msg=str(e)), 400

@bp.route('/delete', methods=('POST',))
def delete_ajax():
    sess = g.session
    payload = request.get_json()
    conn = sess.query(Connection).get(uuid.UUID(payload['uuid']))
    if not conn:
        return jsonify(status='error', msg='Not found'), 404
    sess.delete(conn)
    sess.commit()
    return jsonify(status='ok', msg='Deleted')

