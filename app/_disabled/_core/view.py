from flask import Blueprint, render_template, request, jsonify, url_for, current_app, g
from sqlalchemy import desc, asc, text
from sqlalchemy.exc import IntegrityError
import json
import uuid
from datetime import datetime
#from . import engine, Session


from .connection_model import Connection
from .crud_defs_model import CrudDef
from .data_types_model import DataType
from .variable_types_model import VariableType


bp = Blueprint(
    'core',
    __name__,
    url_prefix='/core',
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


@bp.route('/connections/', methods=('GET',))
def list_connections():
    sess = g.session
    db_types = sess.query(DatabaseType).filter_by(active=True).all()
    db_types_tuples = [(dt.name, dt.display) for dt in db_types]

    return render_template('core/connections_list.html', db_types=db_types_tuples)

@bp.route('/connections/data', methods=('POST',))
def connections_data():
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

@bp.route('/connection/db_types', methods=('GET',))
def db_types_data():
    sess = g.session
    types = sess.query(DatabaseType).filter_by(active=True).all()
    data = [{
        'uuid': str(t.uuid),
        'name': t.name,
        'display': t.display
    } for t in types]
    return jsonify(data=data)

@bp.route('/connections/list', methods=['GET'])
def connection_list_ajax():
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


@bp.route('/crud_def/run_query', methods=['POST'])
def run_query_ajax():
    """Run a query to detect columns"""
    session = g.session
    try:
        data = request.get_json()
        query = data['query']
        params = data.get('params', {})
        connection_uuid = data.get('connection_uuid')
            
        # Validate the query - ensure it's a SELECT query
        if not query.strip().lower().startswith('select'):
            return jsonify({'success': False, 'message': 'Only SELECT queries are supported for column detection'}), 400
            
        # Get connection
        if connection_uuid:
            connection = session.query(Connection).filter_by(uuid=uuid.UUID(connection_uuid)).first()

            if not connection:
                return jsonify({'success': False, 'message': 'Connection not found'}), 404
        else:
            return jsonify({'success': False, 'message': 'No active connection found'}), 404

        conn_str = connection.get_connection_string()

        # Create engine for the connection
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.exc import SQLAlchemyError
        
        try:
            engine = create_engine(conn_str)
            detect_query = text(query)

            # Execute query with parameters
            conn = engine.connect()
            result = conn.execute(detect_query, params)
            
            # Get column information
            columns = []
            
            # Load data types for mapping
            data_types=session.query(DataType).filter_by(active=True).order_by(DataType.display).all()
            
            # Create a mapping of SQL/Python types to our data types
            sql_type_map = {}
            python_type_map = {}
            
            # Default mapping if we don't find specific matches
            default_type = data_types[0].name if data_types else 'text'
            
            # Build type mappings from our data_types
            for dt in data_types:
                dt_name = dt.name.lower()
                
                # Map common text types
                if any(text_type in dt_name for text_type in ['text', 'string', 'char', 'varchar']):
                    sql_type_map.update({
                        'text': dt.name,
                        'varchar': dt.name,
                        'char': dt.name,
                        'character': dt.name,
                        'str': dt.name
                    })
                    python_type_map['str'] = dt.name
                
                # Map common numeric types
                elif any(num_type in dt_name for num_type in ['number', 'int', 'float', 'numeric', 'decimal']):
                    sql_type_map.update({
                        'int': dt.name,
                        'integer': dt.name,
                        'bigint': dt.name,
                        'smallint': dt.name,
                        'numeric': dt.name,
                        'decimal': dt.name,
                        'float': dt.name,
                        'double': dt.name,
                        'real': dt.name
                    })
                    python_type_map.update({
                        'int': dt.name,
                        'float': dt.name,
                        'complex': dt.name
                    })
                
                # Map date types
                elif 'date' in dt_name and 'datetime' not in dt_name:
                    sql_type_map['date'] = dt.name
                    python_type_map['date'] = dt.name
                
                # Map datetime types
                elif any(dt_type in dt_name for dt_type in ['datetime', 'timestamp']):
                    sql_type_map.update({
                        'datetime': dt.name,
                        'timestamp': dt.name,
                        'timestamptz': dt.name
                    })
                    python_type_map['datetime'] = dt.name
                
                # Map boolean types
                elif any(bool_type in dt_name for bool_type in ['bool', 'boolean']):
                    sql_type_map.update({
                        'boolean': dt.name,
                        'bool': dt.name
                    })
                    python_type_map['bool'] = dt.name
                
                # Map link types
                elif 'link' in dt_name:
                    sql_type_map['link'] = dt.name
            
            # Check if we have a row
            # Check if we have a row
            if result.rowcount > 0:
                # Get result metadata
                cols = result.keys()
                
                # Get first row for type detection
                row = result.fetchone()
                
                for i, col_name in enumerate(cols):
                    # Default type
                    col_type = default_type
                    
                    # Try to determine type from the value
                    if row:
                        value = row[i]
                        if value is not None:
                            # Map Python types to our data types
                            python_type = type(value).__name__
                            if python_type in python_type_map:
                                col_type = python_type_map[python_type]
                            # Special cases
                            elif isinstance(value, (int, float)):
                                col_type = python_type_map.get('float' if isinstance(value, float) else 'int', default_type)
                            elif isinstance(value, bool):
                                col_type = python_type_map.get('bool', default_type)
                            elif isinstance(value, datetime.datetime):
                                col_type = python_type_map.get('datetime', default_type)
                            elif isinstance(value, datetime.date):
                                col_type = python_type_map.get('date', default_type)
                            else:
                                col_type = python_type_map.get('str', default_type)
                    
                    # Format column display name
                    display_name = col_name.replace('_', ' ').title()
                    
                    # Add to columns list
                    columns.append({
                        'name': col_name,
                        'display': display_name,
                        'type': col_type,
                        'desc': '',
                        'order': i  # Add order field based on position in query result
                    })
            else:
                # If no rows, try to get column information from cursor description
                for i, col in enumerate(result.cursor.description):
                    col_name = col[0]
                    col_type_str = str(col[1]).lower()  # SQL type as string
                    
                    # Default type
                    col_type = default_type
                    
                    # Try to map the SQL type to one of our data types
                    for sql_type, mapped_type in sql_type_map.items():
                        if sql_type.lower() in col_type_str:
                            col_type = mapped_type
                            break
                    
                    # Format column display name
                    display_name = col_name.replace('_', ' ').title()
                    
                    # Add to columns list
                    columns.append({
                        'name': col_name,
                        'display': display_name,
                        'type': col_type,
                        'desc': '',
                        'order': i  # Add order field based on position in query result
                    })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'columns': columns
            })
            
        except SQLAlchemyError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error running query: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/connection/create', methods=('POST',))
def connection_create_ajax():
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

@bp.route('/connection/update', methods=('POST',))
def connection_update_ajax():
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

@bp.route('/connection/delete', methods=('POST',))
def connection_delete_ajax():
    sess = g.session
    payload = request.get_json()
    conn = sess.query(Connection).get(uuid.UUID(payload['uuid']))
    if not conn:
        return jsonify(status='error', msg='Not found'), 404
    sess.delete(conn)
    sess.commit()
    return jsonify(status='ok', msg='Deleted')



@bp.route('/types', methods=('GET',))
def list_db_types():
    sess = g.session
    return render_template('core/types_list.html')

@bp.route('/types/data', methods=('POST',))
def db_types_data_ajax():
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

@bp.route('/types/create', methods=('POST',))
def db_type_create_ajax():
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

@bp.route('/types/update', methods=('POST',))
def db_type_update_ajax():
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
@bp.route('/types/delete', methods=('POST',))
def db_type_delete_ajax():
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



@bp.route('/crud_defs')
def crud_defs():
    """Render the CRUD definitions list page"""
    return render_template('core/crud_defs_list.html')

@bp.route('/crud_defs/data', methods=['POST'])
def crud_defs_data_ajax():
    """Get CRUD definitions data for DataTables"""
    session = g.session

    try:
        # Parse DataTables request parameters
        data = request.get_json()
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        search = data.get('search', {}).get('value', '')
        order_column_idx = data.get('order', [{}])[0].get('column', 0)
        order_dir = data.get('order', [{}])[0].get('dir', 'asc')
        
        # Column search values
        columns = data.get('columns', [])
        column_search = {}
        for i, col in enumerate(columns):
            if 'search' in col and col['search']['value']:
                column_search[i] = col['search']['value']
        
        # Base query
        query = session.query(CrudDef)
        
        # Global search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                CrudDef.name.ilike(search_term) | 
                CrudDef.display.ilike(search_term) |
                CrudDef.description.ilike(search_term)
            )
        
        # Column specific search
        if 0 in column_search:
            query = query.filter(CrudDef.name.ilike(f"%{column_search[0]}%"))
        if 1 in column_search:
            query = query.filter(CrudDef.display.ilike(f"%{column_search[1]}%"))
        if 2 in column_search:
            query = query.filter(CrudDef.description.ilike(f"%{column_search[2]}%"))
        if 3 in column_search:
            is_active = column_search[3] == 'Yes'
            query = query.filter(CrudDef.active == is_active)
        
        # Order
        if order_column_idx == 0:
            query = query.order_by(asc(CrudDef.name) if order_dir == 'asc' else desc(CrudDef.name))
        elif order_column_idx == 1:
            query = query.order_by(asc(CrudDef.display) if order_dir == 'asc' else desc(CrudDef.display))
        elif order_column_idx == 2:
            query = query.order_by(asc(CrudDef.description) if order_dir == 'asc' else desc(CrudDef.description))
        elif order_column_idx == 3:
            query = query.order_by(asc(CrudDef.active) if order_dir == 'asc' else desc(CrudDef.active))
        
        # Total records count
        total_records = query.count()
        
        # Apply pagination
        if length != -1:
            query = query.offset(start).limit(length)
        
        # Get the records
        records = query.all()
        
        # Format the data for DataTables
        data = []
        for crud_def in records:
            data.append({
                'uuid': str(crud_def.uuid),
                'name': crud_def.name,
                'display': crud_def.display,
                'description': crud_def.description or '',
                'active': 'Yes' if crud_def.active else 'No',
                'query_select': crud_def.query_select,
                'query_insert': crud_def.query_insert,
                'query_update': crud_def.query_update,
                'query_delete': crud_def.query_delete,
                'columns': crud_def.columns,
                'variables': crud_def.variables,
                'options': crud_def.options
            })
        
        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
    finally:
        session.close()

@bp.route('/crud_def/create', methods=['POST'])
def crud_def_create_ajax():
    """Create a new CRUD definition"""
    session = g.session
    try:
        data = request.get_json()
        
        # Create new CRUD definition
        crud_def = CrudDef(
            name=data['name'],
            display=data['display'],
            description=data.get('description'),
            query_select=data['query_select'],
            query_insert=data['query_insert'],
            query_update=data['query_update'],
            query_delete=data['query_delete'],
            columns=data.get('columns'),
            variables=data.get('variables'),
            options=data.get('options'),
            active=data.get('active', True)
        )
        
        session.add(crud_def)
        session.commit()
        
        return jsonify({'success': True})
    except IntegrityError:
        session.rollback()
        return jsonify({'success': False, 'msg': 'A CRUD definition with this name already exists'}), 400
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 400
    finally:
        session.close()

@bp.route('/crud_def/update', methods=['POST'])
def crud_def_update_ajax():
    """Update an existing CRUD definition"""
    session = g.session
    try:
        data = request.get_json()
        
        # Get the existing CRUD definition
        crud_def = session.query(CrudDef).filter_by(uuid=uuid.UUID(data['uuid'])).first()
        if not crud_def:
            return jsonify({'success': False, 'msg': 'CRUD definition not found'}), 404
        
        # Update fields
        crud_def.name = data['name']
        crud_def.display = data['display']
        crud_def.connection_uuid = data['connection_uuid']
        crud_def.description = data.get('description')
        crud_def.query_select = data['query_select']
        crud_def.query_insert = data['query_insert']
        crud_def.query_update = data['query_update']
        crud_def.query_delete = data['query_delete']
        crud_def.columns = data.get('columns')
        crud_def.variables = data.get('variables')
        crud_def.options = data.get('options')
        crud_def.active = data.get('active', True)
        crud_def.updated_at = datetime.utcnow()
        
        session.commit()
        
        return jsonify({'success': True})
    except IntegrityError:
        session.rollback()
        return jsonify({'success': False, 'msg': 'A CRUD definition with this name already exists'}), 400
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 400
    finally:
        session.close()

@bp.route('/crud_def/delete', methods=['POST'])
def crud_def_delete_ajax():
    """Delete a CRUD definition"""
    session = g.session
    try:
        data = request.get_json()
        
        # Get the CRUD definition
        crud_def = session.query(CrudDef).filter_by(uuid=uuid.UUID(data['uuid'])).first()
        if not crud_def:
            return jsonify({'success': False, 'msg': 'CRUD definition not found'}), 404
        
        # Delete the CRUD definition
        session.delete(crud_def)
        session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 400
    finally:
        session.close()

@bp.route('/crud_def/toggle', methods=['POST'])
def crud_def_toggle_ajax():
    """Toggle the active status of a CRUD definition"""
    session = g.session
    try:
        data = request.get_json()
        
        # Get the CRUD definition
        crud_def = session.query(CrudDef).filter_by(uuid=uuid.UUID(data['uuid'])).first()
        if not crud_def:
            return jsonify({'success': False, 'msg': 'CRUD definition not found'}), 404
        
        # Toggle active status
        crud_def.active = data.get('active', not crud_def.active)
        crud_def.updated_at = datetime.utcnow()
        
        session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 400
    finally:
        session.close()            



@bp.route('/crud_def/edit', methods=['POST'])
def crud_def_edit():
    """Render the CRUD definition edit page"""
    session = g.session
    
    try:

        data_types = session.query(DataType).filter_by(active=True).order_by(DataType.display).all()
        variable_types = session.query(VariableType).filter_by(active=True).order_by(VariableType.display).all()
    
        # If accessed via GET with no data, redirect to list
        if request.method == 'GET' and not request.args.get('uuid'):
            return redirect(url_for('core.crud_defs'))
        
        # Get the UUID from POST or GET
        uuid_str = None
        if request.method == 'POST':
            uuid_str = request.form.get('uuid')
        else:  # GET
            uuid_str = request.args.get('uuid')
        
        if not uuid_str:
            return redirect(url_for('core.crud_defs'))
            
        # Get the CRUD definition
        crud_def = session.query(CrudDef).filter_by(uuid=uuid.UUID(uuid_str)).first()
        if not crud_def:
            return render_template('error.html', error='CRUD definition not found'), 404
        
        # Format JSON for template
        crud_def.columns_json = json.dumps(crud_def.columns, indent=2) if crud_def.columns else '{}'
        crud_def.variables_json = json.dumps(crud_def.variables, indent=2) if crud_def.variables else '{}'
        crud_def.options_json = json.dumps(crud_def.options, indent=2) if crud_def.options else '{}'

        connections = session.query(Connection).filter_by(active=True).all()
        
        return render_template('core/crud_def_edit.html', crud_def=crud_def, connections=connections,data_types=data_types,variable_types=variable_types)
    except Exception as e:
        current_app.logger.error(f"Error rendering CRUD definition edit page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@bp.route('/crud_def/new_default', methods=['POST'])
def crud_def_new_default_ajax():
    """Create a new default CRUD definition and return its UUID"""
    session = g.session
    try:
        # Get connection UUID from request
        data = request.get_json()
        connection_uuid = data.get('connection_uuid')
        
        # Create a new default CRUD definition
        new_uuid = uuid.uuid4()
     # Get CRUD operation flags (default to True if not provided)
        is_read = data.get('is_read', True)
        is_create = data.get('is_create', False)
        is_update = data.get('is_update', False)
        is_delete = data.get('is_delete', False)
        
        # Create a new default CRUD definition
        new_uuid = uuid.uuid4()
        
        # Define default options with CRUD operation flags
        default_options = {
            "results_limit": 0,
            "is_datatable": True,
            "is_read": is_read,
            "is_create": is_create,
            "is_update": is_update,
            "is_delete": is_delete,
            "datatable": {
                "is_live": False,
                "is_searchable": False, 
                "is_filterable": True,
                "is_exportable": False,
                "export_formats": "csv,xlsx"
            }
        }
        
        # Create the CRUD definition - connection_uuid can be None
        crud_def = CrudDef(
            uuid=new_uuid,
            name=f"new_crud_{new_uuid.hex[:8]}",
            display="New CRUD Definition",
            description="",
            query_select="",
            query_insert="",
            query_update="",
            query_delete="",
            connection_uuid= None,
            columns={},
            variables={},
            options=default_options,
            active=True
        )
        
        session.add(crud_def)
        session.commit()
        
        return jsonify({
            'success': True, 
            'uuid': str(crud_def.uuid),
            'name': crud_def.name
        })
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error creating CRUD definition: {str(e)}")
        return jsonify({'success': False, 'msg': str(e)}), 400
    finally:
        session.close()        