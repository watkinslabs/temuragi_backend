from flask import Blueprint, request, jsonify, g, session
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest, Unauthorized
import uuid
from sqlalchemy.exc import SQLAlchemyError

from app.register.database import get_model


class Miner:
    """Data API handler for model CRUD operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the Miner with Flask app"""
        self.app = app
        app.miner = self
        
        # Register blueprint
        bp = Blueprint('miner', __name__, url_prefix='/api')
        bp.add_url_rule('/data', 'data_endpoint', self.data_endpoint, methods=['POST'])
        app.register_blueprint(bp)
    
    def data_endpoint(self):
        """Single POST endpoint for all model operations"""
        try:
            # Validate CSRF token
            validate_csrf(request.headers.get('X-CSRFToken'))
            
            # Authenticate via token
            auth_token = request.headers.get('Authorization')
            if not auth_token:
                return jsonify({'error': 'Authorization token required'}), 401
            
            # Remove 'Bearer ' prefix if present
            if auth_token.startswith('Bearer '):
                auth_token = auth_token[7:]
            
            # Validate token
            user_token_model = get_model('UserToken')
            if not user_token_model:
                return jsonify({'error': 'Authentication system unavailable'}), 500
                
            token_obj = user_token_model.validate_token(g.session, auth_token)
            if not token_obj:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Store auth context for permission checking
            g.auth_context = token_obj.get_auth_context()
            
            # Parse JSON payload
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON payload'}), 400
            
            # Validate required fields
            model_name = data.get('model')
            operation = data.get('operation')
            
            if not model_name or not operation:
                return jsonify({'error': 'model and operation are required'}), 400
            
            if operation not in ['read', 'create', 'update', 'delete']:
                return jsonify({'error': 'Invalid operation'}), 400
            
            # Get model class from registry
            model_class = get_model(model_name)
            if not model_class:
                return jsonify({'error': f'Model {model_name} not found'}), 404
            
            # Execute operation
            if operation == 'read':
                return self.handle_read(model_class, data)
            elif operation == 'create':
                return self.handle_create(model_class, data)
            elif operation == 'update':
                return self.handle_update(model_class, data)
            elif operation == 'delete':
                return self.handle_delete(model_class, data)
                
        except BadRequest:
            return jsonify({'error': 'Invalid CSRF token'}), 403
        except Exception as e:
            self.app.logger.error(f"Miner API error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def handle_read(self, model_class, data):
        """Handle read operations - single record only"""
        try:
            record_uuid = data.get('uuid')
            
            if not record_uuid:
                return jsonify({'error': 'uuid is required for read operation'}), 400
            
            # Find single record
            instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
            if not instance:
                return jsonify({'error': 'Record not found'}), 404
            
            # Convert to dictionary
            if hasattr(instance, 'to_dict'):
                result_data = instance.to_dict()
            else:
                # Basic serialization
                result_data = {}
                for column in model_class.__table__.columns:
                    value = getattr(instance, column.name)
                    if isinstance(value, uuid.UUID):
                        value = str(value)
                    elif hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    result_data[column.name] = value
            
            return jsonify({
                'success': True,
                'data': result_data
            })
            
        except SQLAlchemyError as e:
            g.session.rollback()
            self.app.logger.error(f"Database error in read: {e}")
            return jsonify({'error': 'Database error'}), 500
    
    def handle_create(self, model_class, data):
        """Handle create operations"""
        try:
            create_data = data.get('data', {})
            if not create_data:
                return jsonify({'error': 'data field is required for create operation'}), 400
            
            # Create new instance
            instance = model_class(**create_data)
            g.session.add(instance)
            g.session.commit()
            
            # Return created object
            if hasattr(instance, 'to_dict'):
                result_data = instance.to_dict()
            else:
                result_data = {'uuid': str(instance.uuid)}
            
            return jsonify({
                'success': True,
                'data': result_data,
                'message': f'{model_class.__name__} created successfully'
            }), 201
            
        except SQLAlchemyError as e:
            g.session.rollback()
            self.app.logger.error(f"Database error in create: {e}")
            return jsonify({'error': 'Database error'}), 500
    
    def handle_update(self, model_class, data):
        """Handle update operations"""
        try:
            record_uuid = data.get('uuid')
            update_data = data.get('data', {})
            
            if not record_uuid:
                return jsonify({'error': 'uuid is required for update operation'}), 400
            
            if not update_data:
                return jsonify({'error': 'data field is required for update operation'}), 400
            
            # Find record
            instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
            if not instance:
                return jsonify({'error': 'Record not found'}), 404
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            g.session.commit()
            
            # Return updated object
            if hasattr(instance, 'to_dict'):
                result_data = instance.to_dict()
            else:
                result_data = {'uuid': str(instance.uuid)}
            
            return jsonify({
                'success': True,
                'data': result_data,
                'message': f'{model_class.__name__} updated successfully'
            })
            
        except SQLAlchemyError as e:
            g.session.rollback()
            self.app.logger.error(f"Database error in update: {e}")
            return jsonify({'error': 'Database error'}), 500
    
    def handle_delete(self, model_class, data):
        """Handle delete operations"""
        try:
            record_uuid = data.get('uuid')
            hard_delete = data.get('hard_delete', False)
            
            if not record_uuid:
                return jsonify({'error': 'uuid is required for delete operation'}), 400
            
            # Find record
            instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
            if not instance:
                return jsonify({'error': 'Record not found'}), 404
            
            if hard_delete:
                g.session.delete(instance)
            else:
                # Soft delete if model supports it
                if hasattr(instance, 'soft_delete'):
                    instance.soft_delete()
                else:
                    g.session.delete(instance)
            
            g.session.commit()
            
            delete_type = 'permanently deleted' if hard_delete else 'deactivated'
            
            return jsonify({
                'success': True,
                'message': f'{model_class.__name__} {delete_type} successfully'
            })
            
        except SQLAlchemyError as e:
            g.session.rollback()
            self.app.logger.error(f"Database error in delete: {e}")
            return jsonify({'error': 'Database error'}), 500

  