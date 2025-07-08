from flask import Blueprint, request, jsonify, Response, current_app
#from app.auth import require_auth, get_current_user, require_build_token
from app.register.database import db_registry
from sqlalchemy import func
import json
import hashlib

from app.models import ComponentBundle, RouteMapping

bp = Blueprint('components', __name__, url_prefix="/api")


# Add error handler for 403s
@bp.errorhandler(403)
def handle_403(e):
    current_app.logger.error(f"403 Forbidden error in components blueprint: {str(e)}")
    return jsonify({'error': 'Forbidden', 'message': str(e)}), 403

# Add a test endpoint to verify the blueprint is working
@bp.route('/components/test', methods=['GET'])
def test_endpoint():
    current_app.logger.info("Test endpoint hit successfully")
    return jsonify({'status': 'ok', 'message': 'Components blueprint is working'})

@bp.route('/components/sync', methods=['POST'])
def sync_component():
    """Sync a component from build process"""
    
    # Try to get data from different sources
    data = None
    
    # First try JSON
    if request.is_json:
        data = request.get_json()
        current_app.logger.info("Data received as JSON")
    # Try form data
    elif request.form:
        data = request.form.to_dict()
        current_app.logger.info("Data received as form data")
    # Try raw data
    elif request.data:
        try:
            # Attempt to parse as JSON even without proper content-type
            import json
            data = json.loads(request.data)
        except:
            return jsonify({'error': 'Could not parse request data'}), 400
    
    if data is None:
        return jsonify({'error': 'No data received'}), 400
        
    db_session = db_registry._routing_session()

    # Validate required fields
    required = ['name', 'source_code', 'compiled_code']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    component_name = data['name']

    try:
        # Find existing component
        component = db_session.query(ComponentBundle).filter(
            ComponentBundle.name == component_name
        ).first()

        if component:
            # Check if source changed
            new_source_hash = hashlib.sha256(data['source_code'].encode()).hexdigest()
            source_unchanged = component.source_hash == new_source_hash
            
            if source_unchanged:
                # Source unchanged, but still update routes if they changed
                
                # Update routes even if source unchanged
                if data.get('routes'):
                    old_routes = component.routes or []
                    new_routes = data.get('routes', [])
                    if set(old_routes) != set(new_routes):
                        component.routes = new_routes
                        db_session.commit()
                        update_route_mappings(component, new_routes)
                        
                        return jsonify({
                            'id': str(component.id),
                            'name': component.name,
                            'version': component.version,
                            'build_number': component.build_number,
                            'status': 'routes_updated'
                        })
                
                return jsonify({
                    'id': str(component.id),
                    'name': component.name,
                    'version': component.version,
                    'build_number': component.build_number,
                    'status': 'unchanged'
                })

            # Store old values before updating
            old_version = component.version
            old_build = component.build_number

            component.source_code = data['source_code']
            component.compiled_code = data['compiled_code']
            component.build_number += 1
            component.build_timestamp = func.now()

            # Update version if provided
            if data.get('version'):
                component.version = data['version']
                
        else:
            # Create new component
            version = data.get('version', '1.0.0')
            component = ComponentBundle(
                name=component_name,
                source_code=data['source_code'],
                compiled_code=data['compiled_code'],
                version=version
            )
            db_session.add(component)

        # Update metadata
        metadata_updated = []
        if data.get('description'):
            component.description = data['description']
            metadata_updated.append('description')
        if data.get('props_schema'):
            component.props_schema = data['props_schema']
            metadata_updated.append('props_schema')
        if data.get('default_props'):
            component.default_props = data['default_props']
            metadata_updated.append('default_props')
        if data.get('dependencies'):
            component.dependencies = data['dependencies']
            metadata_updated.append('dependencies')
        if 'routes' in data:  # Check if routes key exists, even if empty
            component.routes = data['routes']
            metadata_updated.append('routes')
            

        db_session.commit()

        # Update route mappings if provided
        if 'routes' in data:  # Always update route mappings if routes are provided
            update_route_mappings(component, data['routes'])

        status = 'updated' if component else 'created'
        
        return jsonify({
            'id': str(component.id),
            'name': component.name,
            'version': component.version,
            'build_number': component.build_number,
            'status': status
        })
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db_session.close()


def update_route_mappings(component, routes):
    """Update route mappings for a component"""
    db_session = db_registry._routing_session()
    
    try:
        # Get existing mappings
        existing_mappings = {rm.path: rm for rm in component.route_mappings}

        routes_activated = 0
        routes_created = 0
        routes_deactivated = 0

        for route_path in routes:
            if route_path in existing_mappings:
                # Update existing
                mapping = existing_mappings[route_path]
                if not mapping.is_active:
                    mapping.is_active = True
                    routes_activated += 1
            else:
                # Create new mapping
                mapping = RouteMapping(
                    path=route_path,
                    name=f"{component.name} - {route_path}",
                    component_id=component.id,
                    is_active=True
                )
                db_session.add(mapping)
                routes_created += 1

        # Deactivate removed routes
        for path, mapping in existing_mappings.items():
            if path not in routes and mapping.is_active:
                mapping.is_active = False
                routes_deactivated += 1

        db_session.commit()
        
        
    except Exception as e:
        db_session.rollback()
        raise
    finally:
        db_session.close()


@bp.route('/components/<component_name>/bundle.js', methods=['GET'])
def get_component_bundle(component_name):
    """Serve component bundle"""
    version = request.args.get('v', 'latest')
    
    db_session = db_registry._routing_session()

    try:
        query = db_session.query(ComponentBundle).filter(
            ComponentBundle.name == component_name,
            ComponentBundle.is_active == True
        )

        if version != 'latest':
            query = query.filter(ComponentBundle.version == version)
        else:
            query = query.order_by(ComponentBundle.build_timestamp.desc())

        component = query.first()

        if not component:
            return jsonify({'error': 'Component not found'}), 404


        # Wrap the component to register it properly
        wrapped_code = f"""
(function() {{
    // Ensure window.Components exists
    window.Components = window.Components || {{}};

    // Component code - webpack UMD format will create window['components/{component.name}']
    {component.compiled_code}

    // Register the component from the UMD global
    if (window['components/{component.name}']) {{
        window.Components['{component.name}'] = window['components/{component.name}'];
    }} else {{
        console.error('Component {component.name} not found after loading bundle');
    }}
}})();
"""

        # Return JavaScript bundle with proper headers
        response = Response(wrapped_code, mimetype='application/javascript')
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        response.headers['ETag'] = f'"{component.source_hash}"'

        return response
        
    except Exception as e:
        current_app.logger.error(f"Failed to serve bundle for component '{component_name}': {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db_session.close()


@bp.route('/routes/resolve', methods=['POST'])
def resolve_route():
    """Resolve a route to its component"""
    data = request.get_json()
    path = data.get('path', '')
    path=path.replace("/",'')
    print (path)
    
    db_session = db_registry._routing_session()

    try:
        # Find matching route
        route_mappings = db_session.query(RouteMapping).join(
            ComponentBundle
        ).filter(
            RouteMapping.is_active == True,
            ComponentBundle.is_active == True
        ).all()

        for mapping in route_mappings:
            matches, params = mapping.matches(path)
            
            if matches:
                
                # Check permissions
                """
                user = get_current_user()
                if mapping.requires_auth and not user:
                    return jsonify({'error': 'Authentication required'}), 401

                if user and mapping.requires_auth:
                    if mapping.required_permissions and not user.has_permissions(mapping.required_permissions):
                        return jsonify({'error': 'Access denied'}), 403
                    if mapping.required_roles and not user.has_roles(mapping.required_roles):
                        return jsonify({'error': 'Access denied'}), 403
                """
                response = mapping.to_response()
                response['params'] = params
                
                return jsonify(response)

        return jsonify({'sucess': 'Page not found'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Route resolution failed for path '{path}': {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db_session.close()


@bp.route('/components', methods=['GET'])
def list_components():
    """List all components"""
    db_session = db_registry._routing_session()

    try:
        components = db_session.query(ComponentBundle).filter(
            ComponentBundle.is_active == True
        ).order_by(ComponentBundle.name).all()


        component_list = []
        for c in components:
            routes = c.routes or [rm.path for rm in c.route_mappings if rm.is_active]
            component_list.append({
                'id': str(c.id),
                'name': c.name,
                'version': c.version,
                'description': c.description,
                'routes': routes,
                'build_timestamp': c.build_timestamp.isoformat() if c.build_timestamp else None,
                'build_number': c.build_number
            })

        return jsonify({'components': component_list})
        
    except Exception as e:
        current_app.logger.error(f"Failed to list components: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db_session.close()


@bp.route('/components/export', methods=['GET'])
def export_components():
    """Export all active components for build process"""
    db_session = db_registry._routing_session()

    try:
        components = db_session.query(ComponentBundle).filter(
            ComponentBundle.is_active == True
        ).all()


        export_data = []
        for c in components:
            routes = c.routes or []
            export_data.append({
                'name': c.name,
                'version': c.version,
                'component_code': c.source_code,  # For build-components.js
                'description': c.description,
                'props_schema': c.props_schema,
                'default_props': c.default_props,
                'routes': routes
            })

        return jsonify(export_data)
        
    except Exception as e:
        current_app.logger.error(f"Failed to export components: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db_session.close()