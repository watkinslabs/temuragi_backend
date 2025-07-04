import uuid
import time
import traceback
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy import or_,  desc, asc, func
from flask import request, g
from app.utils import jsonify


from app.register.classes import get_model
from app.register.database import db_registry

from .handler_class import  (
        MinerError,
        MinerPermissionError,
        DataBrokerError,
        BaseDataHandler
        )

class Miner:
    """
    Enhanced Data API handler with RBAC, logging, audit trails, and slim output
    Now includes data broker functionality for delegating to specialized handlers
    """
    __depends_on__ = ['MinerError', 'MinerPermissionError', 'DataBrokerError', 'RbacPermissionChecker']

    def __init__(self, app=None):
        self.app = app
        self.logger = None
        self.data_handlers = {}  # Registry for specialized data handlers
        self.db_session=db_registry._routing_session()

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the Miner with Flask app"""
        self.app = app
        self.logger = app.logger
        app.miner = self

    def register_data_handler(self, model_name, handler_class):
        """
        Register a specialized handler for a specific model
        
        Args:
            model_name: Name of the model (e.g., 'PurchaseOrder')
            handler_class: Class that will handle operations for this model
        """
        self.data_handlers[model_name] = handler_class
        if self.logger:
            self.logger.info(f"Registered data handler {handler_class.__name__} for model {model_name}")

    def broker_data(self, model_name, operation, data=None, context=None):
        """
        Broker data to a specialized handler class
        
        Args:
            model_name: Name of the model to handle
            operation: Operation to perform ('create', 'update', 'metadata', 'process', etc.)
            data: Data to process (single object or dict of objects)
            context: Additional context (user info, permissions, etc.)
            
        Returns:
            Result from the handler
        """
        start_time = time.time()
        self.logger.info(f"In Miner Data API Service processor {model_name}")

        
        # Get the handler for this model
        handler_class = self.data_handlers.get(model_name)
        if not handler_class:
            # Fall back to standard Miner processing
            return self._process_standard_operation(model_name, operation, data, context)
        
        try:
            # Initialize handler with context
            handler = handler_class(
                auth_context=context or g.auth_context,
                logger=self.logger
            )
            
            # Determine which method to call on the handler
            method_map = {
                'create': 'handle_create',
                'update': 'handle_update',
                'delete': 'handle_delete',
                'metadata': 'handle_metadata',
                'process': 'handle_process',
                'batch_create': 'handle_batch_create',
                'batch_update': 'handle_batch_update',
                'validate': 'handle_validate',
                'transform': 'handle_transform',
                'import': 'handle_import',
                'export': 'handle_export',
                'list': 'handle_list',
                'get': 'handle_get',
                'read': 'handle_read'
            }
            
            method_name = method_map.get(operation)
            if None == method_name :
                self.logger.error(f"{operation}: not supported")

            # Check hasattr explicitly
            has_attr_result = hasattr(handler, method_name)
            self.logger.debug(f"  hasattr result: {has_attr_result}")

            # The original check that's failing
            if not method_name or not hasattr(handler, method_name):
                self.logger.debug(f"FAILING: method_name={repr(method_name)}, hasattr={hasattr(handler, method_name)}")
                raise DataBrokerError(
                    f"Handler {handler_class.__name__} does not support operation '{operation}'",
                    handler_class=handler_class.__name__,
                    operation=operation
                )

            # Call the handler method
            method = getattr(handler, method_name)
            result = method(data)
            
            # Log successful operation
            response_time_ms = int((time.time() - start_time) * 1000)
            self.logger.info(
                f"Data broker: {handler_class.__name__}.{method_name} completed in {response_time_ms}ms"
            )
            
            return result
            
        except Exception as e:
            # Log error and re-raise
            self.logger.error(
                f"Data broker error: {handler_class.__name__} failed on {operation}: {str(e)}"
            )
            raise

    def broker_batch_data(self, operations):
        """
        Process multiple operations in a batch
        
        Args:
            operations: List of operation dicts, each containing:
                - model_name: Name of the model
                - operation: Operation to perform
                - data: Data for the operation
                - context: Optional context override
                
        Returns:
            List of results in the same order as operations
        """
        results = []
        errors = []
        
        for idx, op in enumerate(operations):
            try:
                result = self.broker_data(
                    model_name=op.get('model_name'),
                    operation=op.get('operation'),
                    data=op.get('data'),
                    context=op.get('context')
                )
                results.append({
                    'index': idx,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                error_detail = {
                    'index': idx,
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                errors.append(error_detail)
                results.append(error_detail)
        
        return {
            'results': results,
            'errors': errors,
            'total': len(operations),
            'successful': len(operations) - len(errors),
            'failed': len(errors)
        }

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

            token_obj = user_token_model.validate_token(auth_token)
            if not token_obj:
                raise MinerError('Invalid or expired token', 'AuthenticationError', 401)

            # Store auth context
            g.auth_context = token_obj.get_auth_context()
            audit_data.update({
                'user_id': g.auth_context.get('user_id'),
                'token_id': str(token_obj.id)
            })

            # Parse JSON payload
            if not request.is_json:
                raise MinerError('Content-Type must be application/json', 'ValidationError', 400)

            data = request.get_json()
            if not data:
                raise MinerError('Invalid JSON payload', 'ValidationError', 400)

            # Check if this is a batch operation
            if data.get('batch'):
                return self._handle_batch_endpoint(data.get('operations', []), audit_data)

            # Validate required fields
            model_name = data.get('model')
            operation = data.get('operation').lower()

            if not model_name or not operation:
                raise MinerError('model and operation are required', 'ValidationError', 400)

            # Check if we should broker to a specialized handler
            if model_name in self.data_handlers:
                # Let the broker handle permission checking internally
                result = self.broker_data(
                    model_name=model_name,
                    operation=operation,
                    data=data,
                    context=g.auth_context
                )
                return jsonify(result)

            # Standard operations continue as before
            if operation not in ['read', 'create', 'update', 'delete', 'list', 'count', 'metadata', 'form_metadata']:
                raise MinerError(f'Invalid operation: {operation}', 'ValidationError', 400)

            # Update audit data
            audit_data.update({
                'operation': operation,
                'model_name': model_name,
                'target_id': data.get('id'),
                'request_data': self._sanitize_request_data(data)
            })

            # Get model class from registry
            model_class = get_model(model_name)
            if not model_class:
                raise MinerError(f'Model {model_name} not found', 'ValidationError', 404)

            # Check RBAC permissions
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
            elif operation == 'metadata':
                result = self.handle_metadata(model_class, data, audit_data)
            elif operation == 'form_metadata':
                result = self.handle_form_metadata(model_class, data, audit_data)

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            return result

        except MinerError as e:
            return self._handle_error(e, audit_data, start_time)
        except SQLAlchemyError as e:
            return self._handle_error(MinerError('Database error', 'DatabaseError', 500, {'original_error': str(e)}), audit_data, start_time)
        except Exception as e:
            return self._handle_error(MinerError('Internal server error', 'SystemError', 500, {'original_error': str(e)}), audit_data, start_time)

    def _handle_batch_endpoint(self, operations, audit_data):
        """Handle batch operations through the endpoint"""
        result = self.broker_batch_data(operations)
        
        # Log batch operation
        self.logger.info(
            f"Batch operation - User: {audit_data.get('user_id')} - "
            f"Total: {result['total']}, Success: {result['successful']}, Failed: {result['failed']}"
        )
        
        return jsonify(result)

    def _process_standard_operation(self, model_name, operation, data, context):
        """Fallback to standard Miner processing when no handler is registered"""
        # This allows the broker to work even for models without specialized handlers
        request_data = {
            'model': model_name,
            'operation': operation
        }
        
        if data:
            if operation in ['create', 'update']:
                request_data['data'] = data
            elif operation in ['read', 'delete']:
                request_data['id'] = data.get('id') if isinstance(data, dict) else data
            else:
                request_data.update(data if isinstance(data, dict) else {})
        
        # Get model class
        model_class = get_model(model_name)
        if not model_class:
            raise MinerError(f'Model {model_name} not found', 'ValidationError', 404)
        
        # Check permissions
        permission_required = self._get_required_permission(model_class, operation, request_data)
        self._check_permission(permission_required, model_class, operation, request_data)
        
        # Execute operation
        audit_data = {}
        if operation == 'read':
            return self.handle_read(model_class, request_data, audit_data)
        elif operation == 'create':
            return self.handle_create(model_class, request_data, audit_data)
        elif operation == 'update':
            return self.handle_update(model_class, request_data, audit_data)
        elif operation == 'delete':
            return self.handle_delete(model_class, request_data, audit_data)
        elif operation == 'metadata':
            return self.handle_metadata(model_class, request_data, audit_data)
        else:
            raise MinerError(f'Operation {operation} not supported in standard processing', 'ValidationError', 400)

    def _get_required_permission(self, model_class, operation, data):
        """Determine required permission for operation"""
        table_name = model_class.__tablename__
        
        # Map operations to permission actions
        permission_map = {
            'read': 'read',
            'list': 'read', 
            'count': 'read',
            'create': 'create',
            'update': 'update', 
            'delete': 'delete'
        }
        
        action = permission_map.get(operation, operation)
        return f"api:{model_class.__name__.lower()}:{action}"

    def _check_permission(self, permission_required, model_class, operation, data):
        """Check if user has required permission using RBAC system with auto-audit"""
        
        if not g.auth_context or not g.auth_context.get('user_id'):
            raise MinerPermissionError('Authentication required', permission_required)

        # Import here to avoid circular imports
        from app.classes  import RbacPermissionChecker
        
        checker = RbacPermissionChecker()
        
        # Check permission with automatic auditing
        granted = checker.check_api_permission(
            user_id=g.auth_context['user_id'],
            permission_name=permission_required,
            model_name=model_class.__name__,
            action=operation,
            record_id=data.get('id'),
            token_id=g.auth_context.get('token_id')
        )
        
        if not granted:
            raise MinerPermissionError(f'Permission denied: {permission_required}', permission_required)
        
        return granted

    def _log_permission_denial(self, user_id, permission_name):
        """Log permission denial for security monitoring"""
        try:
            audit_log_model = get_model('ApiAuditLog')
            if audit_log_model:
                audit_log_model.log_permission_check(
                    user_id, permission_name, False, 
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
                audit_log_model.log_api_request(**audit_data)
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

    def handle_metadata(self, model_class, data, audit_data):
        """Handle metadata operations - return model structure information"""
        
        # Define fields to exclude from API
        excluded_fields = ['is_active']
        
        columns = []
        
        # Get column information from SQLAlchemy model
        for column in model_class.__table__.columns:
            # Skip excluded fields
            if column.name in excluded_fields:
                continue
                
            column_info = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'foreign_keys': [str(fk) for fk in column.foreign_keys],
                'default': str(column.default) if column.default else None,
                'unique': column.unique or False,
                'index': column.index or False,
            }
            
            # Add human-readable label (convert snake_case to Title Case)
            label = column.name.replace('_', ' ').title()
            # Special cases
            label_map = {
                'Uuid': 'UUID',
                'Id': 'ID',
                'Url': 'URL',
                'Api': 'API',
                'Ip': 'IP',
                'Json': 'JSON',
                'Xml': 'XML',
                'Html': 'HTML',
                'Css': 'CSS',
                'Sql': 'SQL',
                'Http': 'HTTP',
                'Https': 'HTTPS',
                'Ftp': 'FTP',
                'Smtp': 'SMTP',
                'Pop3': 'POP3',
                'Imap': 'IMAP',
                'Dns': 'DNS',
                'Tcp': 'TCP',
                'Udp': 'UDP',
                'Ssh': 'SSH',
                'Ssl': 'SSL',
                'Tls': 'TLS',
                'Vpn': 'VPN',
                'Vm': 'VM',
                'Os': 'OS',
                'Cpu': 'CPU',
                'Ram': 'RAM',
                'Ssd': 'SSD',
                'Hdd': 'HDD',
                'Gb': 'GB',
                'Mb': 'MB',
                'Kb': 'KB',
                'Tb': 'TB',
                'Pb': 'PB'
            }
            
            for old, new in label_map.items():
                label = label.replace(old, new)
            
            column_info['label'] = label
            
            # Determine searchability based on type
            column_type_str = str(column.type).upper()
            searchable = True
            
            # Don't search on these types
            if any(t in column_type_str for t in ['BOOLEAN', 'BINARY', 'BLOB', 'BYTEA']):
                searchable = False
            
            # Special handling for specific column names
            if column.name in ['password_hash', 'salt', 'token', 'secret']:
                searchable = False
                
            column_info['searchable'] = searchable
            
            # Add format hints for frontend
            if 'DATE' in column_type_str or 'TIME' in column_type_str:
                column_info['format'] = 'datetime'
            elif 'BOOLEAN' in column_type_str:
                column_info['format'] = 'boolean'
            elif 'INTEGER' in column_type_str or 'NUMERIC' in column_type_str or 'FLOAT' in column_type_str:
                column_info['format'] = 'number'
            elif 'UUID' in column_type_str:
                column_info['format'] = 'id'
            elif 'JSON' in column_type_str:
                column_info['format'] = 'json'
            else:
                column_info['format'] = 'text'
                
            columns.append(column_info)
        
        # Get relationships if any
        relationships = []
        for key, relationship in model_class.__mapper__.relationships.items():
            rel_info = {
                'name': key,
                'type': relationship.direction.name,  # MANYTOONE, ONETOMANY, etc.
                'target_model': relationship.mapper.class_.__name__,
                'foreign_keys': [str(fk) for fk in relationship._calculated_foreign_keys],
                'uselist': relationship.uselist,  # True for *-to-many relationships
                'back_populates': relationship.back_populates
            }
            relationships.append(rel_info)
        
        # Get any custom metadata from the model
        custom_metadata = {}
        if hasattr(model_class, '__table_args__'):
            table_args = model_class.__table_args__
            if isinstance(table_args, dict):
                custom_metadata = table_args.get('info', {})
            elif isinstance(table_args, tuple) and len(table_args) > 0:
                # Last element might be a dict with info
                if isinstance(table_args[-1], dict):
                    custom_metadata = table_args[-1].get('info', {})
        
        # Build response
        metadata = {
            'model_name': model_class.__name__,
            'table_name': model_class.__tablename__,
            'columns': columns,
            'relationships': relationships,
            'primary_keys': [col.name for col in model_class.__table__.primary_key],
            'indexes': [
                {
                    'name': idx.name,
                    'columns': [col.name for col in idx.columns],
                    'unique': idx.unique
                } for idx in model_class.__table__.indexes
            ],
            'custom': custom_metadata
        }
        
        # Add model docstring if available
        if model_class.__doc__:
            metadata['description'] = model_class.__doc__.strip()
        
        # Update audit data
        audit_data['operation_details'] = 'metadata_retrieved'
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
    
    def handle_read(self, model_class, data, audit_data):
        """Handle read operations - single record by any column"""
        # Support both old 'id' field and new flexible approach
        if 'id' in data:
            # Backward compatibility
            filter_column = 'id'
            filter_value = data['id']
        else:
            # New approach: filter by any column
            filter_column = data.get('filter_column')
            filter_value = data.get('filter_value')
        
        if not filter_column or filter_value is None:
            raise MinerError('filter_column and filter_value are required for read operation', 'ValidationError', 400)
        
        # Validate column exists
        if not hasattr(model_class, filter_column):
            raise MinerError(f'Column {filter_column} does not exist on model {model_class.__name__}', 'ValidationError', 400)
        
        # Build query
        column = getattr(model_class, filter_column)
        instance = self.db_session.query(model_class).filter(column == filter_value).first()
        
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)
        
        # Update audit data
        audit_data['records_returned'] = 1
        audit_data['filter_used'] = {filter_column: filter_value}
        
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

        # Filter out is_active - it should always use the model's default
        filtered_data = {k: v for k, v in create_data.items() if k != 'is_active'}

        # Create new instance
        instance = model_class(**filtered_data)
        self.db_session.add(instance)
        self.db_session.commit()


        pk_value = self._get_instance_pk_value(instance)
        # Update audit data
        audit_data.update({
            'target_id': str(pk_value) if pk_value is not None else None,
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
        """Handle update operations - find by any column"""
        update_data = data.get('data', {})
        
        # Support both old 'id' field and new flexible approach
        if 'id' in data:
            # Backward compatibility
            filter_column = 'id'
            filter_value = data['id']
        else:
            # New approach: filter by any column
            filter_column = data.get('filter_column')
            filter_value = data.get('filter_value')
        
        if not filter_column or filter_value is None:
            raise MinerError('filter_column and filter_value (or id) are required for update operation', 'ValidationError', 400)
        if not update_data:
            raise MinerError('data field is required for update operation', 'ValidationError', 400)
        
        # Validate column exists
        if not hasattr(model_class, filter_column):
            raise MinerError(f'Column {filter_column} does not exist on model {model_class.__name__}', 'ValidationError', 400)
        
        # Filter out is_active - it should never be updated via API
        filtered_data = {k: v for k, v in update_data.items() if k != 'is_active'}
        
        # Find record
        column = getattr(model_class, filter_column)
        instance = self.db_session.query(model_class).filter(column == filter_value).first()
        
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)
        
        # Get readonly fields for this model
        readonly_fields = getattr(model_class, '__readonly_fields__', [])
        
        # Track attempted readonly updates and successful updates
        readonly_attempts = []
        fields_updated = []
        
        # Update fields
        for field, value in filtered_data.items():
            if hasattr(instance, field):
                if field in readonly_fields:
                    readonly_attempts.append(field)
                else:
                    setattr(instance, field, value)
                    fields_updated.append(field)
        
        self.db_session.commit()
        
        # Update audit data
        audit_data['records_returned'] = 1
        audit_data['fields_updated'] = fields_updated
        audit_data['readonly_attempts'] = readonly_attempts
        audit_data['filter_used'] = {filter_column: filter_value}
        
        # Return updated object
        slim = data.get('slim', False)
        result_data = self._serialize_instance(instance, slim)
        
        response = {
            'success': True,
            'data': result_data,
            'message': f'{model_class.__name__} updated successfully'
        }
        
        # Add warning if readonly fields were attempted
        if readonly_attempts:
            response['warning'] = f'The following readonly fields were not updated: {", ".join(readonly_attempts)}'
            response['readonly_fields_attempted'] = readonly_attempts
            self.logger.warning(f"User {audit_data.get('user_id')} attempted to update readonly fields {readonly_attempts} on {model_class.__name__} {filter_column}={filter_value}")
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)
        
        return jsonify(response)
    
    def handle_delete(self, model_class, data, audit_data):
        """Handle delete operations - find by any column"""
        hard_delete = data.get('hard_delete', False)
        
        # Support both old 'id' field and new flexible approach
        if 'id' in data:
            # Backward compatibility
            filter_column = 'id'
            filter_value = data['id']
        else:
            # New approach: filter by any column
            filter_column = data.get('filter_column')
            filter_value = data.get('filter_value')
        
        if not filter_column or filter_value is None:
            raise MinerError('filter_column and filter_value (or id) are required for delete operation', 'ValidationError', 400)
        
        # Validate column exists
        if not hasattr(model_class, filter_column):
            raise MinerError(f'Column {filter_column} does not exist on model {model_class.__name__}', 'ValidationError', 400)
        
        # Find record
        column = getattr(model_class, filter_column)
        instance = self.db_session.query(model_class).filter(column == filter_value).first()
        
        if not instance:
            raise MinerError('Record not found', 'NotFoundError', 404)
        
        # Store filter info for audit
        audit_data['filter_used'] = {filter_column: filter_value}
        
        if hard_delete:
            self.db_session.delete(instance)
        else:
            # Soft delete if model supports it
            if hasattr(instance, 'soft_delete'):
                instance.soft_delete()
            else:
                self.db_session.delete(instance)
        
        self.db_session.commit()
        
        delete_type = 'permanently deleted' if hard_delete else 'deactivated'
        
        return jsonify({
            'success': True,
            'message': f'{model_class.__name__} {delete_type} successfully'
        })
    
    def handle_list(self, model_class, data, audit_data):
        """Handle list operations with pagination, filtering, sorting, and search"""
        
        # DataTables sends these parameters
        draw = data.get('draw', 1)
        start = data.get('start', 0)
        length = data.get('length', 10)
        
        # Search parameters - DataTables sends as 'search' (string) not in a dict
        search_value = data.get('search', '')
        
        # Get searchable columns from the request
        searchable_columns = data.get('searchable_columns', [])
        
        # Get columns to return
        return_columns = data.get('return_columns', [])
        
        # Extract DataTables order information
        order_data = data.get('order', [])
        columns_data = data.get('columns', [])
        
        # Determine sort column and direction
        sort_by = 'created_at'
        sort_order = 'desc'
        
        if order_data and len(order_data) > 0 and columns_data:
            order_col_index = order_data[0].get('column', 0)
            if 0 <= order_col_index < len(columns_data):
                col_name = columns_data[order_col_index].get('name')
                if col_name and hasattr(model_class, col_name):
                    sort_by = col_name
                    sort_order = 'desc' if order_data[0].get('dir') == 'desc' else 'asc'
        
        # Other parameters from your existing implementation
        filters = data.get('filters', {})
        include_inactive = data.get('include_inactive', False)
        slim = data.get('slim', False)
        
        # Start building query
        query = self.db_session.query(model_class)
        
        # Apply active filter unless explicitly including inactive
        if hasattr(model_class, 'is_active') and not include_inactive:
            query = query.filter(model_class.is_active == True)
        
        # Apply filters
        query = self._apply_filters(query, model_class, filters)
        
        # Apply search using searchable columns
        if search_value and searchable_columns:
            query = self._apply_search(query, model_class, search_value, searchable_columns)
            audit_data['search_terms'] = search_value
        
        # Get total count before filtering (for DataTables recordsTotal)
        pk_field = self._get_primary_key_field(model_class)
        pk_column = getattr(model_class, pk_field)
        total_query = self.db_session.query(func.count(pk_column))
        if hasattr(model_class, 'is_active') and not include_inactive:
            total_query = total_query.filter(model_class.is_active == True)
        records_total = total_query.scalar() or 0
        
        # Get filtered count (for DataTables recordsFiltered) - using subquery approach
        # Create a subquery from the current query without ordering
        subquery = query.order_by(None).subquery()
        records_filtered = self.db_session.query(func.count()).select_from(subquery).scalar() or 0
        
        # Apply sorting
        query = self._apply_sorting(query, model_class, sort_by, sort_order)
        
        # Apply pagination using DataTables parameters
        if length==0:
            query = query.offset(start)
        else:
            query = query.offset(start).limit(length)
        
        # Execute query
        instances = query.all()
        
        # Update audit data
        audit_data.update({
            'records_returned': len(instances),
            'total_records': records_filtered,
            'filters_applied': filters
        })
        
        # Serialize results with only requested columns
        data_list = [self._serialize_instance(instance, slim, return_columns) for instance in instances]
        
        # Return DataTables-compatible response
        response = {
            'success': True,
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data_list
        }
        
        if slim:
            response['metadata'] = self._get_model_metadata(model_class)
        
        return jsonify(response)
    
    def handle_count(self, model_class, data, audit_data):
        """Handle count operations with optional filtering"""
        filters = data.get('filters', {})
        include_inactive = data.get('include_inactive', False)

        # Get the actual primary key field name
        pk_field = self._get_primary_key_field(model_class)
        pk_attr = getattr(model_class, pk_field)

        # Start building query
        query = self.db_session.query(func.count(pk_attr))

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

    def _get_primary_key_field(self, model_class):
        """Get the primary key field name(s) for a model"""
        pk_columns = list(model_class.__table__.primary_key.columns)
        if not pk_columns:
            # Fallback to 'id' if no PK defined
            if hasattr(model_class, 'id'):
                return 'id'
            raise MinerError(f"No primary key defined for {model_class.__name__}", 'ConfigurationError', 500)
        
        # Find the attribute name that corresponds to this column
        pk_column = pk_columns[0]
        
        # Search through the model's mapper to find the attribute name
        for attr_name, attr in model_class.__mapper__.all_orm_descriptors.items():
            if hasattr(attr, 'property') and hasattr(attr.property, 'columns'):
                # Check if this attribute maps to our primary key column
                if pk_column in attr.property.columns:
                    return attr_name
        
        # If we can't find the mapping, log an error and return the column name as fallback
        if self.logger:
            self.logger.error(f"Could not find attribute name for primary key column {pk_column.name} in {model_class.__name__}")
        return pk_column.name

    def _get_instance_pk_value(self, instance):
        """Get primary key value from an instance"""
        pk_field = self._get_primary_key_field(instance.__class__)
        return getattr(instance, pk_field, None)

    def _apply_filters(self, query, model_class, filters):
        """Apply filters to query"""
        for field_name, value in filters.items():
            if not hasattr(model_class, field_name):
                continue
            
            field = getattr(model_class, field_name)
            
            # Check if this is a relationship by checking the mapper
            try:
                # Get the attribute from the mapper
                mapper_property = model_class.__mapper__.get_property(field_name)
                
                # Check if it's a RelationshipProperty
                if isinstance(mapper_property, RelationshipProperty):
                    # Handle relationship filters
                    if value:  # Only filter if value is provided
                        related_class = mapper_property.mapper.class_
                        # Join the relationship and filter on the related table's name field
                        if hasattr(related_class, 'name'):
                            query = query.join(field).filter(related_class.name == value)
                    continue
            except Exception:
                # Not a relationship, continue with normal field handling
                pass
            
            # Handle different filter types for regular fields
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
                if value is not None:  # Only apply filter if value is not None
                    query = query.filter(field == value)
        
        return query

    def _apply_search(self, query, model_class, search_term, search_fields):
        """Apply search across specified fields"""
        if not search_term:
            return query

        # Determine if search term is numeric
        is_numeric_search = False
        numeric_value = None
        try:
            numeric_value = float(search_term)
            is_numeric_search = True
        except ValueError:
            pass

        # Check if search term looks like a date/time
        is_date_time_search = self._looks_like_date_time(search_term)

        # If no search fields specified, auto-detect appropriate fields
        if not search_fields:
            search_fields = []
            for column in model_class.__table__.columns:
                column_type = str(column.type).upper()

                # Skip booleans always
                if 'BOOLEAN' in column_type:
                    continue

                # Include date/time fields only if search term looks like date/time
                if 'DATE' in column_type or 'TIME' in column_type or 'TIMESTAMP' in column_type:
                    if is_date_time_search:
                        search_fields.append(column.name)
                    continue

                # Include numeric fields only if search term is numeric
                if any(num_type in column_type for num_type in ['INTEGER', 'NUMERIC', 'FLOAT', 'DECIMAL']):
                    if is_numeric_search:
                        search_fields.append(column.name)
                    continue

                # Skip UUID fields unless search term looks like a UUID
                if 'UUID' in column_type:
                    try:
                        import uuid
                        uuid.UUID(search_term)
                        search_fields.append(column.name)
                    except ValueError:
                        pass
                    continue

                # Include text fields
                if any(text_type in column_type for text_type in ['VARCHAR', 'TEXT', 'STRING', 'CHAR']):
                    search_fields.append(column.name)
        else:
            # Filter out boolean fields from explicitly provided search_fields
            valid_search_fields = []
            for field_name in search_fields:
                if hasattr(model_class, field_name):
                    column = model_class.__table__.columns.get(field_name)
                    if column is not None:
                        column_type = str(column.type).upper()
                        
                        # Skip boolean fields
                        if 'BOOLEAN' in column_type:
                            if self.logger:
                                self.logger.debug(f"Removing boolean field {field_name} from search fields")
                            continue
                        
                        # For date/time fields, only include if search term looks like date/time
                        if 'DATE' in column_type or 'TIME' in column_type or 'TIMESTAMP' in column_type:
                            if not is_date_time_search:
                                if self.logger:
                                    self.logger.debug(f"Removing date/time field {field_name} from search - term doesn't look like date/time")
                                continue
                        
                        valid_search_fields.append(field_name)

            search_fields = valid_search_fields

        # If no valid searchable fields found, return query unchanged
        if not search_fields:
            if self.logger:
                self.logger.debug(f"No valid search fields for model {model_class.__name__}")
            return query

        # Build OR conditions for search
        search_conditions = []
        for field_name in search_fields:
            if not hasattr(model_class, field_name):
                continue

            field = getattr(model_class, field_name)
            column = model_class.__table__.columns.get(field_name)
            if column is None:
                continue

            column_type = str(column.type).upper()

            # Handle date/time fields
            if 'DATE' in column_type or 'TIME' in column_type or 'TIMESTAMP' in column_type:
                # Cast to text and use ILIKE for partial date matching
                # This allows searching for "2024" to match "2024-01-15 10:30:00"
                from sqlalchemy import cast, String
                search_conditions.append(cast(field, String).ilike(f'%{search_term}%'))

            # Handle numeric fields
            elif any(num_type in column_type for num_type in ['INTEGER', 'NUMERIC', 'FLOAT', 'DECIMAL']):
                if is_numeric_search:
                    search_conditions.append(field == numeric_value)

            # Handle UUID fields
            elif 'UUID' in column_type:
                try:
                    import uuid
                    id_value = uuid.UUID(search_term)
                    search_conditions.append(field == id_value)
                except ValueError:
                    pass

            # Handle text fields with ILIKE
            else:
                search_conditions.append(field.ilike(f'%{search_term}%'))

        # Only apply filter if we have valid conditions
        if search_conditions:
            if len(search_conditions) == 1:
                # Single condition doesn't need OR
                query = query.filter(search_conditions[0])
            else:
                # Multiple conditions need OR
                query = query.filter(or_(*search_conditions))
        else:
            if self.logger:
                self.logger.debug(f"No search conditions generated for term '{search_term}'")

        return query

    def _looks_like_date_time(self, search_term):
        """Check if search term looks like it could be a date or time"""
        if not search_term:
            return False
        
        # Common date/time patterns to check for
        date_time_indicators = [
            # Year patterns
            r'\b(19|20)\d{2}\b',  # 1900-2099
            # Date separators
            r'[-/.]',
            # Month names
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
            # Time indicators
            r'[:\s](am|pm|AM|PM)\b',
            r'\d{1,2}:\d{2}',  # HH:MM
            # ISO date patterns
            r'\d{4}-\d{1,2}',  # YYYY-MM
            r'\d{1,2}-\d{1,2}',  # MM-DD or DD-MM
            # Common date formats
            r'\d{1,2}/\d{1,2}',  # MM/DD or DD/MM
        ]
        
        import re
        search_lower = search_term.lower()
        
        for pattern in date_time_indicators:
            if re.search(pattern, search_lower):
                return True
        
        # Check if it's just a 4-digit year
        if re.match(r'^\d{4}$', search_term):
            try:
                year = int(search_term)
                if 1900 <= year <= 2100:
                    return True
            except ValueError:
                pass
        
        return False
    
    def _apply_sorting(self, query, model_class, sort_by, sort_order):
        """Apply sorting to query"""
        if not hasattr(model_class, sort_by):
            pk_field = self._get_primary_key_field(model_class)
            if pk_field and hasattr(model_class, pk_field):
                sort_by = pk_field
            else:
                # If absolutely no sortable field found, log error
                if self.logger:
                    self.logger.error(f"No sortable field found for {model_class.__name__}")
                # Still return query unchanged - let database error provide feedback
                return query


        field = getattr(model_class, sort_by)

        if sort_order.lower() == 'desc':
            query = query.order_by(desc(field))
        else:
            query = query.order_by(asc(field))

        return query

    def _serialize_instance(self, instance, slim=False, return_columns=None):
        """Convert model instance to dictionary with optional slim mode and column filtering"""
        # Define fields to always exclude from API responses
        excluded_fields = ['is_active']
        
        if slim:
            # Slim mode: only return indexed data (values as array)
            if return_columns:
                # Filter out excluded fields from return_columns
                filtered_columns = [col for col in return_columns if col not in excluded_fields]
                return [self._serialize_value(getattr(instance, col, None))
                    for col in filtered_columns]
            else:
                # Return all columns except excluded fields
                return [self._serialize_value(getattr(instance, col.name))
                    for col in instance.__class__.__table__.columns
                    if col.name not in excluded_fields]
        else:
            # Full mode: return as key-value pairs
            if hasattr(instance, 'to_dict'):
                result = instance.to_dict()
            else:
                # Basic serialization
                result = {}
                for column in instance.__class__.__table__.columns:
                    if column.name not in excluded_fields:
                        value = getattr(instance, column.name)
                        result[column.name] = self._serialize_value(value)
            
            # Remove excluded fields if they were included by to_dict
            for field in excluded_fields:
                result.pop(field, None)
            
            # Filter to only requested columns if specified
            if return_columns:
                filtered_result = {}
                for col in return_columns:
                    if col in result and col not in excluded_fields:
                        filtered_result[col] = result[col]
                # Always include id for actions
                if 'id' in result and 'id' not in filtered_result:
                    filtered_result['id'] = result['id']
                return filtered_result
            
            return result

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
        # Exclude is_active from metadata columns
        excluded_fields = ['is_active']
        columns = [col.name for col in model_class.__table__.columns if col.name not in excluded_fields]
        
        return {
            'columns': columns,
            'table_name': model_class.__tablename__,
            'model_name': model_class.__name__
        }
    
    def handle_form_metadata(self, model_class, data, audit_data):
        """
        Handle form_metadata operations - return rich metadata for form generation
        Includes field types, constraints, relationships, and smart FK detection
        """
        # Get basic metadata first
        basic_metadata = self._get_form_basic_metadata(model_class)
        
        # Enrich with relationship details
        relationships = self._get_form_relationship_metadata(model_class)
        
        # Get validation rules
        validation_rules = self._get_form_validation_rules(model_class)
        
        # Detect which fields should be shown/hidden in forms
        form_config = self._get_form_display_config(model_class)
        
        # Build complete metadata
        metadata = {
            'model': {
                'name': model_class.__name__,
                'table_name': model_class.__tablename__,
                'display_name': self._get_model_display_name(model_class),
                'description': model_class.__doc__.strip() if model_class.__doc__ else None
            },
            'fields': basic_metadata,
            'relationships': relationships,
            'validation': validation_rules,
            'form_config': form_config,
            'primary_key': [col.name for col in model_class.__table__.primary_key][0] if model_class.__table__.primary_key else 'id'
        }
        
        # Update audit data
        audit_data['operation_details'] = 'form_metadata_retrieved'
        
        try:
            return jsonify({
                'success': True,
                'metadata': metadata
            })
        except:
            return {
                'success': True,
                'metadata': metadata
            }

    def _get_form_basic_metadata(self, model_class):
        """Get basic field metadata for form generation"""
        # Define fields to exclude from forms
        excluded_fields = ['is_active']
        
        fields = {}
        
        for column in model_class.__table__.columns:
            # Skip excluded fields
            if column.name in excluded_fields:
                continue
                
            field_meta = {
                'name': column.name,
                'type': self._get_field_type(column),
                'sql_type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'unique': column.unique or False,
                'index': column.index or False,
                'default': self._serialize_default(column.default),
                'label': self._get_field_label(column.name),
                'placeholder': self._get_field_placeholder(column),
                'help_text': None,  # Can be customized per model
                'readonly': False,
                'hidden': False,
                'order': 0
            }
            
            # Add constraints
            if hasattr(column.type, 'length') and column.type.length:
                field_meta['max_length'] = column.type.length
            
            # Check for foreign keys
            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                field_meta['is_foreign_key'] = True
                field_meta['foreign_key'] = {
                    'table': fk.column.table.name,
                    'column': fk.column.name,
                    'model': self._get_model_from_table_name(fk.column.table.name)
                }
            else:
                field_meta['is_foreign_key'] = False
            
            # Auto-detect if field should be hidden
            if column.primary_key or column.name in ['created_at', 'updated_at', 'deleted_at']:
                field_meta['hidden'] = True
            
            # Auto-detect readonly fields
            if column.name in ['created_at', 'updated_at', 'created_by', 'updated_by']:
                field_meta['readonly'] = True
            
            # Special handling for common field names
            if column.name == 'password' or column.name == 'password_hash':
                field_meta['type'] = 'password'
                field_meta['hidden_on_edit'] = True
            
            if column.name == 'email':
                field_meta['type'] = 'email'
            
            if column.name == 'url' or column.name.endswith('_url'):
                field_meta['type'] = 'url'
            
            fields[column.name] = field_meta
        
        return fields

    def _get_form_relationship_metadata(self, model_class):
        """Get detailed relationship metadata for form generation"""
        relationships = {}
        
        for key, rel in model_class.__mapper__.relationships.items():
            rel_meta = {
                'name': key,
                'type': rel.direction.name,  # MANYTOONE, ONETOMANY, MANYTOMANY
                'model': rel.mapper.class_.__name__,
                'table': rel.mapper.class_.__tablename__,
                'uselist': rel.uselist,
                'back_populates': rel.back_populates,
                'cascade': rel.cascade,
                'lazy': rel.lazy,
                'display_field': self._detect_display_field(rel.mapper.class_),
                'foreign_keys': [str(fk) for fk in rel._calculated_foreign_keys],
                'is_owned': False,  # Will be determined below
                'back_reference_field': None,
                'inline_editing': False,
                'order_by': None
            }
            
            # Detect if this is an "owned" relationship (has back-reference to parent)
            related_model = rel.mapper.class_
            for col in related_model.__table__.columns:
                if col.foreign_keys:
                    for fk in col.foreign_keys:
                        if fk.column.table.name == model_class.__tablename__:
                            rel_meta['is_owned'] = True
                            rel_meta['back_reference_field'] = col.name
                            break
            
            # Determine if inline editing should be enabled
            if rel_meta['is_owned'] and rel.uselist:
                rel_meta['inline_editing'] = True
            
            # Check for ordering
            if hasattr(related_model, 'order_index'):
                rel_meta['order_by'] = 'order_index'
            elif hasattr(related_model, 'created_at'):
                rel_meta['order_by'] = 'created_at'
            
            relationships[key] = rel_meta
        
        return relationships

    def _get_form_validation_rules(self, model_class):
        """Extract validation rules from model"""
        # Define fields to exclude
        excluded_fields = ['is_active']
        
        rules = {}
        
        for column in model_class.__table__.columns:
            # Skip excluded fields
            if column.name in excluded_fields:
                continue
                
            col_rules = {}
            
            # Required fields - a field is required if it's not nullable
            # Don't mark as required if:
            # - It's a primary key (usually auto-generated)
            # - It has a server-side default (like func.now())
            # - It's an auto-timestamp field
            if not column.nullable and not column.primary_key:
                # Check if it has a server-side default
                has_server_default = False
                if column.default is not None:
                    # Check if it's a server-side function (like func.now())
                    if hasattr(column.default, 'arg') and callable(column.default.arg):
                        has_server_default = True
                    # Also check for server_default
                    if column.server_default is not None:
                        has_server_default = True
                
                # Auto-timestamp fields should not be required in forms
                auto_timestamp_fields = ['created_at', 'updated_at', 'deleted_at']
                if column.name not in auto_timestamp_fields and not has_server_default:
                    col_rules['required'] = True
            
            # Length constraints
            if hasattr(column.type, 'length') and column.type.length:
                col_rules['max_length'] = column.type.length
            
            # Numeric constraints
            if self._is_numeric_type(column.type):
                if hasattr(column.type, 'precision'):
                    col_rules['precision'] = column.type.precision
                if hasattr(column.type, 'scale'):
                    col_rules['scale'] = column.type.scale
            
            # Pattern constraints for common fields
            if column.name == 'email':
                col_rules['pattern'] = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                col_rules['pattern_message'] = 'Please enter a valid email address'
            
            if column.name == 'phone':
                col_rules['pattern'] = r'^[\d\s\-\+\(\)]+$'
                col_rules['pattern_message'] = 'Please enter a valid phone number'
            
            # Unique constraint
            if column.unique:
                col_rules['unique'] = True
            
            if col_rules:
                rules[column.name] = col_rules
        
        return rules

    def _get_form_display_config(self, model_class):
        """Get form display configuration"""
        # Define fields to exclude from forms
        excluded_fields = ['is_active']
        
        config = {
            'field_order': [],
            'fieldsets': [],
            'excluded_fields': ['deleted_at', 'password_hash', 'salt', 'is_active'],
            'readonly_fields': ['created_at', 'updated_at', 'created_by', 'updated_by'],
            'hidden_fields': ['id', 'uuid'],
            'inline_models': []
        }
        
        # Build default field order (non-hidden fields)
        for column in model_class.__table__.columns:
            if column.name not in config['excluded_fields'] and not column.primary_key:
                config['field_order'].append(column.name)
        
        # Add relationships at the end
        for key, rel in model_class.__mapper__.relationships.items():
            if rel.uselist:  # One-to-many or many-to-many
                config['inline_models'].append(key)
            else:  # Many-to-one
                config['field_order'].append(key)
        
        # Check for custom form config on model
        if hasattr(model_class, '__form_config__'):
            custom_config = model_class.__form_config__
            config.update(custom_config)
        
        return config

    def _get_field_type(self, column):
        """Map SQL types to form field types"""
        type_str = str(column.type).upper()
        
        # Special cases based on column name
        if column.name in ['password', 'password_hash']:
            return 'password'
        if column.name == 'email':
            return 'email'
        if column.name == 'url' or column.name.endswith('_url'):
            return 'url'
        
        # Map SQL types to HTML input types
        if 'BOOLEAN' in type_str:
            return 'checkbox'
        elif 'DATE' in type_str and 'TIME' not in type_str:
            return 'date'
        elif 'DATETIME' in type_str or 'TIMESTAMP' in type_str:
            return 'datetime-local'
        elif 'TIME' in type_str and 'DATE' not in type_str:
            return 'time'
        elif 'INT' in type_str or 'NUMERIC' in type_str or 'DECIMAL' in type_str or 'FLOAT' in type_str:
            return 'number'
        elif 'TEXT' in type_str:
            return 'textarea'
        elif 'JSON' in type_str:
            return 'json'
        elif 'UUID' in type_str:
            return 'hidden'  # Usually auto-generated
        else:
            return 'text'

    def _get_field_label(self, field_name):
        """Convert field name to human-readable label"""
        # Remove common suffixes
        label = field_name.replace('_id', '').replace('_at', '')
        
        # Convert snake_case to Title Case
        label = label.replace('_', ' ').title()
        
        # Special cases
        label_map = {
            'Uuid': 'UUID',
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Fk': 'FK',
            'Ip': 'IP Address',
            'Json': 'JSON',
            'Xml': 'XML',
            'Csv': 'CSV',
            'Pdf': 'PDF'
        }
        
        for old, new in label_map.items():
            label = label.replace(old, new)
        
        return label

    def _get_field_placeholder(self, column):
        """Generate appropriate placeholder text"""
        if column.name == 'email':
            return 'user@example.com'
        elif column.name == 'phone':
            return '(555) 123-4567'
        elif column.name == 'url' or column.name.endswith('_url'):
            return 'https://example.com'
        elif 'name' in column.name:
            return f'Enter {self._get_field_label(column.name).lower()}'
        else:
            return ''

    def _detect_display_field(self, model_class):
        """Auto-detect the best field to use for display in dropdowns"""
        # Priority order for display fields
        display_field_priority = [
            'display_name', 'display', 'name', 'title', 'label', 
            'description', 'email', 'username', 'code', 'slug'
        ]
        
        # Check each priority field
        for field_name in display_field_priority:
            if hasattr(model_class, field_name):
                column = model_class.__table__.columns.get(field_name)
                if column is not None and 'VARCHAR' in str(column.type).upper():
                    return field_name
        
        # Fallback: first string column that's not an ID
        for column in model_class.__table__.columns:
            if ('VARCHAR' in str(column.type).upper() or 'TEXT' in str(column.type).upper()) \
            and not column.primary_key \
            and not column.foreign_keys \
            and 'id' not in column.name.lower() \
            and 'uuid' not in column.name.lower():
                return column.name
        
        # Last resort: use ID
        return 'id'

    def _serialize_default(self, default):
        """Serialize column defaults for JSON response"""
        if default is None:
            return None
        
        if hasattr(default, 'arg'):
            # SQLAlchemy default
            if callable(default.arg):
                return 'function'
            else:
                return str(default.arg)
        
        return str(default)

    def _get_model_from_table_name(self, table_name):
        """Get model name from table name by looking it up in the registry"""
        # Import all registered models
        from app.register.classes import _model_registry

        
        # Get all models from the registry
        # Find the model with matching table name
        for model_name, model_class in _model_registry.items():
            if hasattr(model_class, '__tablename__') and model_class.__tablename__ == table_name:
                return model_class.__name__
        
        # If not found in registry, fall back to simple conversion
        # but log a warning
        if self.logger:
            self.logger.warning(f"Table '{table_name}' not found in model registry, using fallback conversion")
        
        # Fallback: try to intelligently convert table name
        # Handle common patterns like 'users' -> 'User', 'user_tokens' -> 'UserToken'
        parts = table_name.split('_')
        
        # Remove common plural suffixes from the last part
        if parts and parts[-1].endswith('ies'):
            parts[-1] = parts[-1][:-3] + 'y'  # 'categories' -> 'category'
        elif parts and parts[-1].endswith('es'):
            parts[-1] = parts[-1][:-2]  # 'addresses' -> 'address'
        elif parts and parts[-1].endswith('s'):
            parts[-1] = parts[-1][:-1]  # 'users' -> 'user'
        
        # Capitalize each part
        model_name = ''.join(part.capitalize() for part in parts)
        
        return model_name

    def _get_model_display_name(self, model_class):
        """Get human-readable display name for model"""
        if hasattr(model_class, '__display_name__'):
            return model_class.__display_name__
        
        # Convert CamelCase to Title Case
        import re
        name = model_class.__name__
        # Insert spaces before capital letters
        name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
        return name

    def _is_numeric_type(self, column_type):
        """Check if column type is numeric"""
        type_str = str(column_type).upper()
        numeric_types = ['INTEGER', 'NUMERIC', 'DECIMAL', 'FLOAT', 'REAL', 'SMALLINT', 'BIGINT']
        return any(t in type_str for t in numeric_types)
    