from flask import Blueprint, request, jsonify, g
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest, Unauthorized
import uuid
import time
import traceback
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_, desc, asc, func, text
from sqlalchemy.orm import Query
from datetime import datetime, timezone
import re
import logging

from app.register.database import get_model


class MinerError(Exception):
    """Custom exception for Miner operations"""
    def __init__(self, message, error_type="MinerError", status_code=400, details=None):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class MinerPermissionError(MinerError):
    """Permission denied error"""
    def __init__(self, message, permission_required=None):
        super().__init__(message, "PermissionError", 403, {'permission_required': permission_required})


class Miner:
    """
    Enhanced Data API handler with RBAC, logging, audit trails, and slim output
    """

    def __init__(self, app=None):
        self.app = app
        self.logger = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the Miner with Flask app"""
        self.app = app
        self.logger = app.logger
        app.miner = self

        # Register blueprint
        bp = Blueprint('miner', __name__, url_prefix='/api')
        bp.add_url_rule('/data', 'data_endpoint', self.data_endpoint, methods=['POST'])
        app.register_blueprint(bp)

    def data_endpoint(self):
        """Single POST endpoint for all model operations with full RBAC and logging"""
        start_time = time.time()
        audit_data = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'request_method': request.method,
            'endpoint': request.endpoint or '/api/data'
        }
        
        try:
            # Validate CSRF token
            validate_csrf(request.headers.get('X-CSRFToken'))

            # Authenticate via token
            auth_token = request.headers.get('Authorization')
            if not auth_token:
                raise MinerError('Authorization token required', 'AuthenticationError', 401)

            # Remove 'Bearer ' prefix if present
            if auth_token.startswith('Bearer '):
                auth_token = auth_token[7:]

            # Validate token
            user_token_model = get_model('UserToken')
            if not user_token_model:
                raise MinerError('Authentication system unavailable', 'SystemError', 500)

            token_obj = user_token_model.validate_token(g.session, auth_token)
            if not token_obj:
                raise MinerError('Invalid or expired token', 'AuthenticationError', 401)

            # Store auth context
            g.auth_context = token_obj.get_auth_context()
            audit_data.update({
                'user_uuid': g.auth_context.get('user_uuid'),
                'token_uuid': str(token_obj.uuid)
            })

            # Parse JSON payload
            if not request.is_json:
                raise MinerError('Content-Type must be application/json', 'ValidationError', 400)

            data = request.get_json()
            if not data:
                raise MinerError('Invalid JSON payload', 'ValidationError', 400)

            # Validate required fields
            model_name = data.get('model')
            operation = data.get('operation')

            if not model_name or not operation:
                raise MinerError('model and operation are required', 'ValidationError', 400)

            if operation not in ['read', 'create', 'update', 'delete', 'list', 'count']:
                raise MinerError(f'Invalid operation: {operation}', 'ValidationError', 400)

            # Update audit data
            audit_data.update({
                'operation': operation,
                'model_name': model_name,
                'target_uuid': data.get('uuid'),
                'request_data': self._sanitize_request_data(data)
            })

            # Get model class from registry
            model_class = get_model(model_name)
            if not model_class:
                raise MinerError(f'Model {model_name} not found', 'ValidationError', 404)

            # Check RBAC permissions (this will automatically audit the permission check)
            permission_required = self._get_required_permission(model_class, operation, data)
            self._check_permission(permission_required, model_class, operation, data)

            # Execute operation
            if operation == 'read':
                result = self.handle_read(model_class, data, audit_data)
            elif operation == 'create':
                result = self.handle_create(model_class, data, audit_data)
            elif operation == 'update':
                result = self.handle_update(model_class, data, audit_data)
            elif operation == 'delete':
                result = self.handle_delete(model_class, data, audit_data)
            elif operation == 'list':
                result = self.handle_list(model_class, data, audit_data)
            elif operation == 'count':
                result = self.handle_count(model_class, data, audit_data)

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log successful operation (simplified since RBAC already audited permission)
            self.logger.info(f"API {operation} {model_name} - User: {audit_data.get('user_uuid')} - Time: {response_time_ms}ms")

            return result

        except BadRequest:
            return self._handle_error(MinerError('Invalid CSRF token', 'CSRFError', 403), audit_data, start_time)
        except MinerError as e:
            return self._handle_error(e, audit_data, start_time)
        except SQLAlchemyError as e:
            return self._handle_error(MinerError('Database error', 'DatabaseError', 500, {'original_error': str(e)}), audit_data, start_time)
        except Exception as e:
            return self._handle_error(MinerError('Internal server error', 'SystemError', 500, {'original_error': str(e)}), audit_data, start_time)

    def _get_required_permission(self, model_class, operation, data):
        """Determine required permission for operation"""
        table_name = model_class.__tablename__
        
        # Map operations to permission actions
        permission_map = {
            'read': 'read',
            'list': 'read', 
            'count': 'read',
            'create': 'write',
            'update': 'write', 
            'delete': 'delete'
        }
        
        action = permission_map.get(operation, operation)
        return f"{table_name}:{action}"

    def _check_permission(self, permission_required, model_class, operation, data):
        """Check if user has required permission using RBAC system with auto-audit"""
        
        if not g.auth_context or not g.auth_context.get('user_uuid'):
            raise MinerPermissionError('Authentication required', permission_required)

        # Import here to avoid circular imports
        from app._system.rbac.rbac_permission_checker import RbacPermissionChecker
        
        checker = RbacPermissionChecker(g.session)
        
        # Check permission with automatic auditing
        granted = checker.check_api_permission(
            user_uuid=g.auth_context['user_uuid'],
            permission_name=permission_required,
            model_name=model_class.__name__,
            action=operation,
            record_id=data.get('uuid'),
            token_uuid=g.auth_context.get('token_uuid')
        )
        
        if not granted:
            raise MinerPermissionError(f'Permission denied: {permission_required}', permission_required)
        
        return granted

    def _log_permission_denial(self, user_uuid, permission_name):
        """Log permission denial for security monitoring"""
        try:
            audit_log_model = get_model('ApiAuditLog')
            if audit_log_model:
                audit_log_model.log_permission_check(
                    g.session, user_uuid, permission_name, False, 
                    f'Access denied for permission: {permission_name}'
                )
        except Exception as e:
            self.logger.warning(f"Failed to log permission denial: {e}")

    def _handle_error(self, error, audit_data, start_time):
        """Handle and log errors consistently"""
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log error details
        self.logger.error(f"API Error - {error.error_type}: {error.message} - Details: {error.details}")
        
        # Log full traceback for system errors
        if error.status_code >= 500:
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            'success': False,
            'error': error.message,
            'error_type': error.error_type,
            'details': error.details if self.app.debug else {}
        }), error.status_code

    def _log_audit(self, audit_data):
        """Log audit trail"""
        try:
            audit_log_model = get_model('ApiAuditLog')
            if audit_log_model:
                audit_log_model.log_api_request(g.session, **audit_data)
        except Exception as e:
            self.logger.warning(f"Audit logging failed: {e}")

    def _sanitize_request_data(self, data):
        """Remove sensitive data from request before logging"""
        if not data:
            return None
            
        sanitized = data.copy()
        sensitive_fields = ['password', 'token', 'secret', 'key', 'csrf']
        
        def remove_sensitive(obj):
            if isinstance(obj, dict):
                return {
                    k: '[REDACTED]' if any(sens in k.lower() for sens in sensitive_fields) 
                    else remove_sensitive(v) 
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [remove_sensitive(item) for item in obj]
            else:
                return obj
        
        return remove_sensitive(sanitized)

    def handle_read(self, model_class, data, audit_data):
        """Handle read operations - single record only"""
        record_uuid = data.get('uuid')
        if not record_uuid:
            raise MinerError('uuid is required for read operation', 'ValidationError', 400)

        # Find single record
        instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)

        # Update audit data
        audit_data['records_returned'] = 1

        # Check for slim output
        slim = data.get('slim', False)
        result_data = self._serialize_instance(instance, slim)

        response = {'success': True, 'data': result_data}
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)

        return jsonify(response)

    def handle_create(self, model_class, data, audit_data):
        """Handle create operations"""
        create_data = data.get('data', {})
        if not create_data:
            raise MinerError('data field is required for create operation', 'ValidationError', 400)

        # Create new instance
        instance = model_class(**create_data)
        g.session.add(instance)
        g.session.commit()

        # Update audit data
        audit_data.update({
            'target_uuid': str(instance.uuid),
            'records_returned': 1
        })

        # Return created object
        slim = data.get('slim', False)
        result_data = self._serialize_instance(instance, slim)

        response = {
            'success': True,
            'data': result_data,
            'message': f'{model_class.__name__} created successfully'
        }
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)

        return jsonify(response), 201

    def handle_update(self, model_class, data, audit_data):
        """Handle update operations"""
        record_uuid = data.get('uuid')
        update_data = data.get('data', {})

        if not record_uuid:
            raise MinerError('uuid is required for update operation', 'ValidationError', 400)
        if not update_data:
            raise MinerError('data field is required for update operation', 'ValidationError', 400)

        # Find record
        instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)

        # Update fields
        for field, value in update_data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        g.session.commit()

        # Update audit data
        audit_data['records_returned'] = 1

        # Return updated object
        slim = data.get('slim', False)
        result_data = self._serialize_instance(instance, slim)

        response = {
            'success': True,
            'data': result_data,
            'message': f'{model_class.__name__} updated successfully'
        }
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)

        return jsonify(response)

    def handle_delete(self, model_class, data, audit_data):
        """Handle delete operations"""
        record_uuid = data.get('uuid')
        hard_delete = data.get('hard_delete', False)

        if not record_uuid:
            raise MinerError('uuid is required for delete operation', 'ValidationError', 400)

        # Find record
        instance = g.session.query(model_class).filter(model_class.uuid == record_uuid).first()
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)

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

    def handle_list(self, model_class, data, audit_data):
        """Handle list operations with pagination, filtering, sorting, and search"""
        # Extract parameters
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 20), 100)  # Cap at 100 for safety
        sort_by = data.get('sort_by', 'created_at')
        sort_order = data.get('sort_order', 'desc')
        filters = data.get('filters', {})
        search = data.get('search', '')
        search_fields = data.get('search_fields', [])
        include_inactive = data.get('include_inactive', False)
        slim = data.get('slim', False)

        # Start building query
        query = g.session.query(model_class)

        # Apply active filter unless explicitly including inactive
        if hasattr(model_class, 'is_active') and not include_inactive:
            query = query.filter(model_class.is_active == True)

        # Apply filters
        query = self._apply_filters(query, model_class, filters)

        # Apply search
        if search and search_fields:
            query = self._apply_search(query, model_class, search, search_fields)
            audit_data['search_terms'] = search

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        query = self._apply_sorting(query, model_class, sort_by, sort_order)

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Execute query
        instances = query.all()

        # Update audit data
        audit_data.update({
            'records_returned': len(instances),
            'total_records': total_count,
            'filters_applied': filters
        })

        # Serialize results
        data_list = [self._serialize_instance(instance, slim) for instance in instances]

        # Calculate pagination metadata
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        response = {
            'success': True,
            'data': data_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'filters_applied': filters,
            'search_applied': search if search else None,
            'sort': {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)

        return jsonify(response)

    def handle_count(self, model_class, data, audit_data):
        """Handle count operations with optional filtering"""
        filters = data.get('filters', {})
        include_inactive = data.get('include_inactive', False)

        # Start building query
        query = g.session.query(func.count(model_class.uuid))

        # Apply active filter unless explicitly including inactive
        if hasattr(model_class, 'is_active') and not include_inactive:
            query = query.filter(model_class.is_active == True)

        # Apply filters
        query = self._apply_filters(query, model_class, filters)

        # Execute count query
        count = query.scalar()

        # Update audit data
        audit_data.update({
            'records_returned': count,
            'filters_applied': filters
        })

        return jsonify({
            'success': True,
            'count': count,
            'filters_applied': filters
        })

    def _apply_filters(self, query, model_class, filters):
        """Apply filters to query"""
        for field_name, value in filters.items():
            if not hasattr(model_class, field_name):
                continue

            field = getattr(model_class, field_name)

            # Handle different filter types
            if isinstance(value, dict):
                # Complex filter: {"operator": "gt", "value": 10}
                operator = value.get('operator', 'eq')
                filter_value = value.get('value')

                if operator == 'eq':
                    query = query.filter(field == filter_value)
                elif operator == 'ne':
                    query = query.filter(field != filter_value)
                elif operator == 'gt':
                    query = query.filter(field > filter_value)
                elif operator == 'gte':
                    query = query.filter(field >= filter_value)
                elif operator == 'lt':
                    query = query.filter(field < filter_value)
                elif operator == 'lte':
                    query = query.filter(field <= filter_value)
                elif operator == 'like':
                    query = query.filter(field.like(f'%{filter_value}%'))
                elif operator == 'ilike':
                    query = query.filter(field.ilike(f'%{filter_value}%'))
                elif operator == 'in':
                    if isinstance(filter_value, list):
                        query = query.filter(field.in_(filter_value))
                elif operator == 'not_in':
                    if isinstance(filter_value, list):
                        query = query.filter(~field.in_(filter_value))
                elif operator == 'is_null':
                    if filter_value:
                        query = query.filter(field.is_(None))
                    else:
                        query = query.filter(field.isnot(None))
            else:
                # Simple equality filter
                query = query.filter(field == value)

        return query

    def _apply_search(self, query, model_class, search_term, search_fields):
        """Apply search across specified fields"""
        if not search_term or not search_fields:
            return query

        # Build OR conditions for search across multiple fields
        search_conditions = []
        for field_name in search_fields:
            if hasattr(model_class, field_name):
                field = getattr(model_class, field_name)
                # Use ilike for case-insensitive search
                search_conditions.append(field.ilike(f'%{search_term}%'))

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        return query

    def _apply_sorting(self, query, model_class, sort_by, sort_order):
        """Apply sorting to query"""
        if not hasattr(model_class, sort_by):
            # Fallback to created_at if sort field doesn't exist
            if hasattr(model_class, 'created_at'):
                sort_by = 'created_at'
            else:
                # No sorting if no valid field
                return query

        field = getattr(model_class, sort_by)

        if sort_order.lower() == 'desc':
            query = query.order_by(desc(field))
        else:
            query = query.order_by(asc(field))

        return query

    def _serialize_instance(self, instance, slim=False):
        """Convert model instance to dictionary with optional slim mode"""
        if slim:
            # Slim mode: only return indexed data (values as array)
            return [self._serialize_value(getattr(instance, col.name)) 
                   for col in instance.__class__.__table__.columns]
        else:
            # Full mode: return as key-value pairs
            if hasattr(instance, 'to_dict'):
                return instance.to_dict()
            else:
                # Basic serialization
                result_data = {}
                for column in instance.__class__.__table__.columns:
                    value = getattr(instance, column.name)
                    result_data[column.name] = self._serialize_value(value)
                return result_data

    def _serialize_value(self, value):
        """Serialize individual values"""
        if isinstance(value, uuid.UUID):
            return str(value)
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
        else:
            return value

    def _get_model_metadata(self, model_class):
        """Get model metadata for slim responses"""
        return {
            'columns': [col.name for col in model_class.__table__.columns],
            'table_name': model_class.__tablename__,
            'model_name': model_class.__name__
        }