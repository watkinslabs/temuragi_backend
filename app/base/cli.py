#!/usr/bin/env python3
"""
Hybrid Base CLI with pluggable backend support
Supports both local (direct database) and remote (API) operations
"""

import os
import logging
import traceback
import json
import yaml
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from logging.handlers import RotatingFileHandler
from tabulate import tabulate
from datetime import datetime
from urllib.parse import urljoin

from app.register.database import db_registry

# Optional imports for token storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class BackendError(Exception):
    """Base exception for backend operations"""
    pass


class AuthenticationError(BackendError):
    """Authentication failed"""
    pass

class AppBase:
    logger=None

    def __init__(self):
        pass

 
    def teardown_appcontext(self, f):
        """Register a function to be called at the end of each request context."""
        pass

class Backend(ABC):
    """Abstract base class for CLI backends"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the backend connection"""
        pass
    
    @abstractmethod
    def authenticate(self, **kwargs) -> bool:
        """Authenticate with the backend"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        pass
    
    @abstractmethod
    def get_model(self, model_name: str) -> Any:
        """Get a model class/reference"""
        pass
    
    @abstractmethod
    def get_class(self, class_name: str) -> Any:
        """Get a class reference"""
        pass
    
    @abstractmethod
    def execute_operation(self, model: str, operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a CRUD operation"""
        pass
    
    @abstractmethod
    def close(self):
        """Clean up resources"""
        pass
    
    def _log(self, message: str, level: str = 'info'):
        """Log a message if logger is available"""
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)


class RemoteBackend(Backend):
    """Remote API backend implementation"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        super().__init__(config, logger)
        self.base_url = config.get('base_url', 'https://ahoy2.perfrad.com').rstrip('/')
        self.api_token = None
        self.refresh_token = None
        self.user_id = None
        self.csrf_token = None
        self.session = requests.Session()
        
        # API endpoints configuration
        self.endpoints = {
            'login_page': config.get('login_url', '/v2/auth/login'),
            'auth': config.get('auth_url', '/v2/api/auth/'),
            'data': config.get('api_url', '/v2/api/data'),
            'validate': config.get('validate_url', '/v2/api/validate'),
            'refresh': config.get('refresh_url', '/v2/api/auth/refresh'),
            'logout': config.get('logout_url', '/v2/api/auth/logout')
        }
        
        # Token storage configuration
        storage_dir = config.get('token_storage_dir', '~/.config/tmcli')
        self.token_dir = Path(storage_dir).expanduser()
        self.token_file = self.token_dir / config.get('token_filename', 'tokens.json')
        
        # Request timeout configuration
        self.timeout = config.get('request_timeout', 5)
        
        # Load stored tokens on init
        self._load_stored_tokens()
    
    def initialize(self) -> bool:
        """Initialize remote backend"""
        try:
            # Check if we have a base URL
            if not self.base_url or self.base_url == 'https://ahoy2.perfrad.com':
                # Default URL is fine, just check if it's accessible
                pass
            
            # Test connection to base URL
            response = self.session.get(self.base_url, timeout=self.timeout)
            self._initialized = response.status_code < 500
            self._log(f"Remote backend initialized: {self.base_url}", 'info')
            return self._initialized
        except requests.exceptions.ConnectionError:
            self._log(f"Cannot connect to API at {self.base_url}. Is the server running?", 'error')
            return False
        except requests.exceptions.Timeout:
            self._log(f"Connection timeout to {self.base_url}", 'error')
            return False
        except Exception as e:
            self._log(f"Failed to initialize remote backend: {e}", 'error')
            return False
    
    def _validate_token(self) -> bool:
        """Validate the current API token"""
        if not self.api_token:
            return False
        
        try:
            # Make a simple API call to validate token
            validate_url = urljoin(self.base_url, self.endpoints['validate'])
            headers = self._build_headers()
            
            response = self.session.get(validate_url, headers=headers, timeout=self.timeout)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _validate_or_refresh_token(self) -> bool:
        """Validate current token or refresh if needed"""
        # First try to validate existing token
        if self._validate_token():
            return True
        
        # If validation failed, try to refresh
        if self.refresh_token:
            return self._refresh_access_token()
        
        return False
    
    def _refresh_access_token(self) -> bool:
        """Use refresh token to get new access token"""
        if not self.refresh_token:
            return False
        
        try:
            self._log("Refreshing access token...", 'info')
            
            # Get fresh CSRF token
            csrf_token = self._get_csrf_token()
            if csrf_token:
                self.csrf_token = csrf_token
            
            refresh_url = urljoin(self.base_url, self.endpoints['refresh'])
            headers = self._build_headers(include_auth=False)
            
            response = self.session.post(refresh_url, headers=headers, json={
                'refresh_token': self.refresh_token
            })
            
            if response.status_code != 200:
                self._log(f"Token refresh failed: {response.status_code}", 'warning')
                return False
            
            data = response.json()
            if not data.get('success'):
                self._log(f"Token refresh failed: {data.get('message', 'Unknown error')}", 'warning')
                return False
            
            # Update tokens
            self.api_token = data.get('api_token')
            new_refresh = data.get('refresh_token')
            if new_refresh:
                self.refresh_token = new_refresh
            
            if not self.api_token:
                return False
            
            # Store updated tokens
            self._store_tokens()
            self._log("Access token refreshed successfully", 'info')
            return True
            
        except Exception as e:
            self._log(f"Token refresh error: {e}", 'error')
            return False
    
    def _clear_tokens(self):
        """Clear all stored tokens"""
        self.api_token = None
        self.refresh_token = None
        self.user_id = None
        self.csrf_token = None
        
        # Clear from file
        if self.token_file.exists():
            self.token_file.unlink()
        
        # Clear from keyring
        if KEYRING_AVAILABLE:
            try:
                for key in ['api_token', 'refresh_token', 'user_id', 'csrf_token']:
                    keyring.delete_password('tmcli', key)
            except Exception:
                pass
    
    def authenticate(self, username: str = None, password: str = None, **kwargs) -> bool:
        """Authenticate with the API"""
        # If already authenticated with valid token, return True
        if self.is_authenticated() and self._validate_token():
            return True
        
        # If no credentials provided, try to use stored tokens
        if not username and self._load_stored_tokens():
            # Try to validate/refresh the stored tokens
            if self._validate_or_refresh_token():
                return True
            # If refresh failed, clear invalid tokens
            self._clear_tokens()
        
        if not username or not password:
            raise AuthenticationError("Username and password required")
        
        try:
            # Get CSRF token
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                self._log("Failed to get CSRF token", 'warning')
            
            self.csrf_token = csrf_token
            
            # Authenticate
            auth_url = urljoin(self.base_url, self.endpoints['auth'])
            headers = self._build_headers(include_auth=False)
            
            response = self.session.post(auth_url, headers=headers, json={
                'username': username,
                'password': password,
                'remember': True
            })
            
            if response.status_code != 200:
                raise AuthenticationError(f"Login failed: {response.status_code}")
            
            data = response.json()
            if not data.get('success'):
                raise AuthenticationError(data.get('message', 'Unknown error'))
            
            self.api_token = data.get('api_token')
            self.refresh_token = data.get('refresh_token')
            self.user_id = data.get('user_id')
            
            if not self.api_token:
                raise AuthenticationError("No API token in response")
            
            # Store tokens
            self._store_tokens()
            self._log(f"Authenticated successfully as user {self.user_id}", 'info')
            return True
            
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Authentication error: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication"""
        return bool(self.api_token)
    
    def get_model(self, model_name: str) -> Dict[str, Any]:
        """Get model metadata from API"""
        try:
            result = self.execute_operation(model_name, 'metadata')
            if result.get('success'):
                return result.get('metadata', {})
            return None
        except Exception as e:
            self._log(f"Failed to get model {model_name}: {e}", 'error')
            return None
    
    def get_class(self, class_name: str) -> Dict[str, Any]:
        """Get class metadata from API"""
        # In remote context, classes and models are treated similarly
        return self.get_model(class_name)
    
    def execute_operation(self, model: str, operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute an API operation"""
        if not self.is_authenticated():
            raise AuthenticationError("Not authenticated")
        
        # Validate token before making request
        if not self._validate_or_refresh_token():
            raise AuthenticationError("Token validation failed")
        
        url = urljoin(self.base_url, self.endpoints['data'])
        
        payload = {
            'model': model,
            'operation': operation
        }
        
        if data:
            if operation in ['create', 'update']:
                payload['data'] = data
            elif operation in ['read', 'delete']:
                payload['id'] = data.get('id')
            elif operation == 'process':
                payload['data'] = data
            else:
                payload.update(data)
        
        headers = self._build_headers()
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            
            # Handle CSRF token errors
            if response.status_code == 403 or (response.status_code == 400 and 'csrf' in response.text.lower()):
                self._log("CSRF token error, refreshing...", 'info')
                self.csrf_token = self._get_csrf_token()
                if self.csrf_token:
                    self._store_tokens()
                    headers = self._build_headers()
                    response = self.session.post(url, json=payload, headers=headers)
            
            # Handle token expiration
            if response.status_code == 401:
                self._log("Token expired, attempting refresh...", 'info')
                if self._refresh_access_token():
                    # Retry with new token
                    headers = self._build_headers()
                    response = self.session.post(url, json=payload, headers=headers)
                else:
                    raise AuthenticationError("Token refresh failed")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise BackendError(f"API request failed: {e}")
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
    
    def logout(self):
        """Logout and clear all tokens"""
        try:
            # Try to invalidate token on server
            if self.api_token:
                logout_url = urljoin(self.base_url, self.endpoints['logout'])
                headers = self._build_headers()
                
                try:
                    self.session.post(logout_url, headers=headers, timeout=self.timeout)
                except Exception:
                    pass  # Continue with local cleanup even if server logout fails
            
            # Clear all tokens
            self._clear_tokens()
            self._log("Logged out successfully", 'info')
            
        except Exception as e:
            self._log(f"Logout error: {e}", 'error')
            # Still clear tokens locally
            self._clear_tokens()
    
    def _get_csrf_token(self) -> Optional[str]:
        """Get CSRF token from login page"""
        try:
            login_page_url = urljoin(self.base_url, self.endpoints['login_page'])
            response = self.session.get(login_page_url)
            
            if response.status_code != 200:
                return None
            
            import re
            csrf_match = re.search(r'<meta\s+(?:content="([^"]+)"\s+name="csrf-token"|name="csrf-token"\s+content="([^"]+)")', response.text)
            
            if csrf_match:
                return csrf_match.group(1) or csrf_match.group(2)
            
            return None
        except Exception:
            return None
    
    def _build_headers(self, include_auth: bool = True, content_type: str = 'application/json') -> Dict[str, str]:
        """Build standard headers for API requests
        
        Args:
            include_auth: Whether to include Authorization header
            content_type: Content-Type header value
            
        Returns:
            Dict of headers
        """
        headers = {
            'Content-Type': content_type
        }
        
        # Add authorization if requested and available
        if include_auth and self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        # Add CSRF token if available
        if self.csrf_token:
            headers['X-CSRF-Token'] = self.csrf_token
        
        # Add user ID for tracking and personalization
        if self.user_id:
            headers['X-User-ID'] = str(self.user_id)
        
        return headers
    
    def _store_tokens(self):
        """Store authentication tokens"""
        self.token_dir.mkdir(parents=True, exist_ok=True)
        
        tokens = {
            'api_token': self.api_token,
            'refresh_token': self.refresh_token,
            'user_id': self.user_id,
            'csrf_token': self.csrf_token
        }
        
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f)
        
        os.chmod(self.token_file, 0o600)
        
        # Also try keyring if available
        if KEYRING_AVAILABLE:
            try:
                for key, value in tokens.items():
                    if value:
                        keyring.set_password('tmcli', key, value)
            except Exception:
                pass
    
    def _load_stored_tokens(self) -> bool:
        """Load stored authentication tokens"""
        # Try keyring first
        if KEYRING_AVAILABLE:
            try:
                self.api_token = keyring.get_password('tmcli', 'api_token')
                self.refresh_token = keyring.get_password('tmcli', 'refresh_token')
                self.user_id = keyring.get_password('tmcli', 'user_id')
                self.csrf_token = keyring.get_password('tmcli', 'csrf_token')
                if self.api_token:
                    return True
            except Exception:
                pass
        
        # Try file storage
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    self.api_token = tokens.get('api_token')
                    self.refresh_token = tokens.get('refresh_token')
                    self.user_id = tokens.get('user_id')
                    self.csrf_token = tokens.get('csrf_token')
                    return bool(self.api_token)
            except Exception:
                pass
        
        return False


class LocalBackend(Backend):
    """Local database backend implementation"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        super().__init__(config, logger)
        self.session = None
        self.db_registry = None
        self.class_registry = {}
        self.model_registry = {}
    
    def initialize(self) -> bool:
        """Initialize local backend with database and registries"""
        try:
            # Import local dependencies
            from app.config import config as app_config
            from app.register.classes import register_classes, get_class
            from app.register.database import db_registry, register_db
            
            # Set up class registry
            self._log("Registering classes for local backend", 'info')
            register_classes()
            
            # Store registry references
            self.db_registry = db_registry
            self._get_class_func = get_class
            
            # Set up database
            if self.config.get('connect_db', True):
                self._setup_database()
            
            self._initialized = True
            self._log("Local backend initialized successfully", 'info')
            return True
            
        except Exception as e:
            self._log(f"Failed to initialize local backend: {e}", 'error')
            return False
    
    def authenticate(self, **kwargs) -> bool:
        """Local backend doesn't require authentication"""
        return True
    
    def is_authenticated(self) -> bool:
        """Local backend is always authenticated"""
        return True
    
    def get_model(self, model_name: str) -> Any:
        """Get a model from the local registry"""
        try:
            from app.models import get_model
            model = get_model(model_name)
            if model:
                self._log(f"Retrieved model {model_name}", 'debug')
            else:
                self._log(f"Model {model_name} not found", 'warning')
            return model
        except Exception as e:
            self._log(f"Error getting model {model_name}: {e}", 'error')
            return None
    
    def get_class(self, class_name: str) -> Any:
        """Get a class from the local registry"""
        try:
            if hasattr(self, '_get_class_func'):
                cls = self._get_class_func(class_name)
                if cls:
                    self._log(f"Retrieved class {class_name}", 'debug')
                else:
                    self._log(f"Class {class_name} not found", 'warning')
                return cls
        except Exception as e:
            self._log(f"Error getting class {class_name}: {e}", 'error')
            return None
    
    def execute_operation(self, model: str, operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a local database operation"""
        if not self.session:
            raise BackendError("No database session available")
        
        try:
            model_class = self.get_model(model)
            if not model_class:
                return {'success': False, 'error': f'Model {model} not found'}
            
            # Map operations to local methods
            if operation == 'create':
                return self._create_record(model_class, data)
            elif operation == 'read':
                return self._read_record(model_class, data)
            elif operation == 'update':
                return self._update_record(model_class, data)
            elif operation == 'delete':
                return self._delete_record(model_class, data)
            elif operation == 'list':
                return self._list_records(model_class, data)
            elif operation == 'count':
                return self._count_records(model_class, data)
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
                
        except Exception as e:
            self._log(f"Operation {operation} on {model} failed: {e}", 'error')
            return {'success': False, 'error': str(e)}
    
    def close(self):
        """Close database session"""
        if self.session:
            try:
                self.session.close()
                self._log("Database session closed", 'info')
            except Exception as e:
                self._log(f"Error closing session: {e}", 'error')
    
    def _setup_database(self):
        """Set up database connection"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from app.config import config
            
            engine = create_engine(config['database_uri'])
            session_factory = sessionmaker(bind=engine)
            self.session = session_factory()
            self._log("Database session created", 'info')
            
        except Exception as e:
            raise BackendError(f"Failed to setup database: {e}")
    
    def _create_record(self, model_class, data: Dict) -> Dict[str, Any]:
        """Create a new record"""
        try:
            instance = model_class(**data)
            self.session.add(instance)
            self.session.commit()
            return {
                'success': True,
                'id': getattr(instance, 'id', None),
                'data': self._serialize_model(instance)
            }
        except Exception as e:
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _read_record(self, model_class, data: Dict) -> Dict[str, Any]:
        """Read a record by ID"""
        try:
            record_id = data.get('id')
            if not record_id:
                return {'success': False, 'error': 'ID required'}
            
            instance = self.session.query(model_class).get(record_id)
            if not instance:
                return {'success': False, 'error': 'Record not found'}
            
            return {
                'success': True,
                'data': self._serialize_model(instance)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _update_record(self, model_class, data: Dict) -> Dict[str, Any]:
        """Update a record"""
        try:
            record_id = data.pop('id', None)
            if not record_id:
                return {'success': False, 'error': 'ID required'}
            
            instance = self.session.query(model_class).get(record_id)
            if not instance:
                return {'success': False, 'error': 'Record not found'}
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.commit()
            return {
                'success': True,
                'data': self._serialize_model(instance)
            }
        except Exception as e:
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _delete_record(self, model_class, data: Dict) -> Dict[str, Any]:
        """Delete a record"""
        try:
            record_id = data.get('id')
            if not record_id:
                return {'success': False, 'error': 'ID required'}
            
            instance = self.session.query(model_class).get(record_id)
            if not instance:
                return {'success': False, 'error': 'Record not found'}
            
            self.session.delete(instance)
            self.session.commit()
            return {'success': True, 'message': 'Record deleted'}
        except Exception as e:
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _list_records(self, model_class, data: Dict) -> Dict[str, Any]:
        """List records with optional filters"""
        try:
            query = self.session.query(model_class)
            
            # Apply filters
            filters = data.get('filters', {})
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.filter(getattr(model_class, field) == value)
            
            # Apply pagination
            limit = data.get('limit', 10)
            offset = data.get('offset', 0)
            
            total = query.count()
            records = query.limit(limit).offset(offset).all()
            
            return {
                'success': True,
                'data': [self._serialize_model(r) for r in records],
                'recordsTotal': total,
                'recordsFiltered': len(records)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _count_records(self, model_class, data: Dict) -> Dict[str, Any]:
        """Count records with optional filters"""
        try:
            query = self.session.query(model_class)
            
            # Apply filters
            filters = data.get('filters', {})
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.filter(getattr(model_class, field) == value)
            
            count = query.count()
            return {'success': True, 'count': count}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _serialize_model(self, instance) -> Dict[str, Any]:
        """Serialize a model instance to dict"""
        # Simple serialization - can be enhanced
        result = {}
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


class BaseCLI:
    """
    Hybrid Base CLI class with pluggable backend support
    Supports both local (database) and remote (API) operations
    """
    
    def __init__(self, name="cli", backend_type="auto", config=None, 
                 log_level=None, log_file=None, verbose=False, 
                 show_icons=True, table_format=None, console_logging=False,
                 **backend_kwargs):
        """
        Initialize CLI with specified backend
        
        Args:
            name: Name for this CLI instance
            backend_type: Backend type ('remote', 'local', 'auto')
            config: Configuration dict
            log_level: Override log level
            log_file: Override log file
            verbose: Enable verbose logging
            show_icons: Show icons in output
            table_format: Table format for output
            console_logging: Also log to console
            **backend_kwargs: Additional backend-specific arguments
        """
        
        self.name = name
        self.verbose = verbose
        self.show_icons = show_icons
        self.console_logging = console_logging
        self.backend = None
        self.initialization_errors = []
        self.app=AppBase()
                
        db_registry.init_app(self.app)
        # Load configuration
        self.config = self._load_config(config)
        self.app = AppBase()

        db_registry.init_app(self.app)
        
        # Set up icons
        self._icons = {
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ',
            'debug': '🔍'
        } if show_icons else {}
        
        # Set up logging
        self._setup_logger(log_level, log_file)
        
        # Configure table format
        self.table_format = table_format or self.config.get('CLI_TABLE_FORMAT', 'simple')
        
        # Initialize backend
        self._initialize_backend(backend_type, backend_kwargs)
    
    def _load_config(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Load configuration from various sources"""
        final_config = {}
        
        # Try to load from app.config
        try:
            from app.config import config as app_config
            final_config.update(app_config)
        except ImportError:
            pass
        
        # Try to load from YAML file
        config_path = Path.home() / '.config' / 'tmcli' / 'config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f) or {}
                    final_config.update(yaml_config)
            except Exception:
                pass
        
        # Override with provided config
        if config:
            final_config.update(config)
        
        return final_config
    
    def _setup_logger(self, log_level=None, log_file=None):
        """Set up logger"""
        if self.verbose:
            log_level = logging.DEBUG
        else:
            log_level = log_level or self.config.get('LOG_LEVEL', logging.INFO)
        
        log_file = log_file or self.config.get('LOG_FILE', f'logs/{self.name}_cli.log')
        max_bytes = 10485760
        backup_count = 5
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # Set up file handler
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else '.'
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Create logger
        self.logger = logging.getLogger(f'cli_{self.name}')
        self.logger.handlers.clear()
        self.logger.addHandler(file_handler)
        
        # Add console handler if requested
        if self.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            self.logger.addHandler(console_handler)
        
        self.logger.setLevel(log_level)
        self.logger.propagate = False
        
        self.logger.info(f"Logger configured - Level: {logging.getLevelName(log_level)}, File: {log_file}")
    
    def _initialize_backend(self, backend_type: str, backend_kwargs: Dict):
        """Initialize the appropriate backend"""
        self.log_info(f"Initializing {backend_type} backend")
        
        if backend_type == "auto":
            # Try remote first, fall back to local
            backend_type = self._determine_backend_type()
        
        try:
            if backend_type == "remote":
                self.backend = RemoteBackend(self.config, self.logger)
            elif backend_type == "local":
                self.backend = LocalBackend(self.config, self.logger)
            else:
                raise ValueError(f"Unknown backend type: {backend_type}")
            
            # Initialize the backend
            if self.backend.initialize():
                self.log_info(f"{backend_type.capitalize()} backend initialized successfully")
            else:
                error_msg = f"Failed to initialize {backend_type} backend"
                self.log_warning(error_msg)
                
                # For remote backend, provide helpful message
                if backend_type == "remote":
                    self.log_info("Please check:")
                    self.log_info("  1. Run 'tmcli configure' to set the API URL")
                    self.log_info("  2. Ensure the API server is running")
                    self.log_info("  3. Check network connectivity")
                
                # Don't raise for master CLI commands that don't need backend
                if self.name != "tmcli":
                    raise BackendError(error_msg)
                
        except Exception as e:
            self.initialization_errors.append(f"Backend initialization failed: {e}")
            self.log_error(f"Backend initialization failed: {e}")
            
            # Re-raise for non-master CLIs
            if self.name != "tmcli":
                raise
    
    def _determine_backend_type(self) -> str:
        """Determine which backend to use based on configuration and availability"""
        # Check if we have API configuration
        if self.config.get('base_url'):
            try:
                # Try to connect to API
                import requests
                response = requests.get(self.config['base_url'], timeout=2)
                if response.status_code < 500:
                    return "remote"
            except Exception:
                pass
        
        # Fall back to local
        return "local"
    
    # Authentication methods
    def authenticate(self, username: str = None, password: str = None, **kwargs) -> bool:
        """Authenticate with the backend"""
        try:
            return self.backend.authenticate(username=username, password=password, **kwargs)
        except Exception as e:
            self.log_error(f"Authentication failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self.backend.is_authenticated()
    
    def logout(self) -> bool:
        """Logout from the backend (primarily for remote backends)"""
        try:
            if hasattr(self.backend, 'logout'):
                self.backend.logout()
                self.log_info("Logged out successfully")
                return True
            else:
                self.log_debug("Logout not applicable for this backend")
                return True
        except Exception as e:
            self.log_error(f"Logout failed: {e}")
            return False
    
    # Model/Class access methods
    def get_model(self, model_name: str) -> Any:
        """Get a model from the backend"""
        self.log_debug(f"Retrieving model: {model_name}")
        try:
            model = self.backend.get_model(model_name)
            if model:
                self.log_debug(f"Model '{model_name}' retrieved successfully")
            else:
                self.log_warning(f"Model '{model_name}' not found")
            return model
        except Exception as e:
            self.log_error(f"Error retrieving model '{model_name}': {e}")
            return None
    
    def get_class(self, class_name: str) -> Any:
        """Get a class from the backend"""
        self.log_debug(f"Retrieving class: {class_name}")
        try:
            cls = self.backend.get_class(class_name)
            if cls:
                self.log_debug(f"Class '{class_name}' retrieved successfully")
            else:
                self.log_warning(f"Class '{class_name}' not found")
            return cls
        except Exception as e:
            self.log_error(f"Error retrieving class '{class_name}': {e}")
            return None
    
    # CRUD operations
    def create_record(self, model: str, data: Dict) -> Dict[str, Any]:
        """Create a new record"""
        return self.execute_operation(model, 'create', data)
    
    def read_record(self, model: str, record_id: Union[int, str]) -> Dict[str, Any]:
        """Read a record by ID"""
        return self.execute_operation(model, 'read', {'id': record_id})
    
    def update_record(self, model: str, record_id: Union[int, str], data: Dict) -> Dict[str, Any]:
        """Update a record"""
        data['id'] = record_id
        return self.execute_operation(model, 'update', data)
    
    def delete_record(self, model: str, record_id: Union[int, str]) -> Dict[str, Any]:
        """Delete a record"""
        return self.execute_operation(model, 'delete', {'id': record_id})
    
    def list_records(self, model: str, filters: Dict = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List records with optional filters"""
        data = {
            'filters': filters or {},
            'limit': limit,
            'offset': offset
        }
        return self.execute_operation(model, 'list', data)
    
    def count_records(self, model: str, filters: Dict = None) -> Dict[str, Any]:
        """Count records with optional filters"""
        data = {'filters': filters or {}}
        return self.execute_operation(model, 'count', data)
    
    def execute_operation(self, model: str, operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a backend operation"""
        self.log_info(f"Executing operation: {operation} on {model}")
        try:
            result = self.backend.execute_operation(model, operation, data)
            if result.get('success'):
                self.log_info(f"Operation '{operation}' on '{model}' completed successfully")
            else:
                self.log_error(f"Operation '{operation}' on '{model}' failed: {result.get('error')}")
            return result
        except Exception as e:
            self.log_error(f"Operation '{operation}' on '{model}' failed with exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_with_logging(self, operation_name: str, func, *args, **kwargs):
        """Execute a function with comprehensive logging"""
        self.log_info(f"Starting operation: {operation_name}")
        start_time = self._get_timestamp()
        
        try:
            if args:
                self.log_debug(f"Operation args: {args}")
            if kwargs:
                self.log_debug(f"Operation kwargs: {kwargs}")
            
            result = func(*args, **kwargs)
            
            end_time = self._get_timestamp()
            duration = end_time - start_time
            self.log_info(f"Operation '{operation_name}' completed successfully in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = self._get_timestamp()
            duration = end_time - start_time
            self.log_error(f"Operation '{operation_name}' failed after {duration:.2f}s: {e}")
            self._log_full_traceback(f"Operation {operation_name} error", e)
            raise
    
    def _get_timestamp(self):
        """Get current timestamp"""
        import time
        return time.time()
    
    def _log_full_traceback(self, context: str, exception: Exception):
        """Log full traceback for debugging"""
        self.log_error(f"{context}: {exception}")
        if self.verbose:
            tb_str = traceback.format_exc()
            self.log_debug(f"Full traceback for {context}:\n{tb_str}")
    
    # Output methods
    def output(self, message: str, output_type: str = 'info'):
        """Unified output method with optional icons"""
        # Log the output
        log_method = getattr(self, f'log_{output_type}', self.log_info)
        log_method(f"OUTPUT: {message}")
        
        # Display to user
        icon = self._icons.get(output_type, '')
        if icon:
            print(f"{icon} {message}")
        else:
            print(message)
    
    def output_table(self, rows: List, headers: List[str] = None, table_format: str = None):
        """Output formatted table"""
        format_to_use = table_format or self.table_format
        self.log_debug(f"Outputting table with format: {format_to_use}")
        self.log_debug(f"Table rows: {len(rows) if rows else 0}")
        
        try:
            if headers:
                table_output = tabulate(rows, headers=headers, tablefmt=format_to_use)
            else:
                table_output = tabulate(rows, tablefmt=format_to_use)
            print(table_output)
        except Exception as e:
            self.log_error(f"Failed to output table: {e}")
            self.output_error(f"Table display failed: {e}")
    
    def output_success(self, message: str):
        """Output success message"""
        self.output(message, 'success')
    
    def output_error(self, message: str):
        """Output error message"""
        self.output(message, 'error')
    
    def output_warning(self, message: str):
        """Output warning message"""
        self.output(message, 'warning')
    
    def output_info(self, message: str):
        """Output info message"""
        self.output(message, 'info')
    
    def output_debug(self, message: str):
        """Output debug message (only if verbose)"""
        if self.verbose:
            self.output(message, 'debug')
    
    # Logging methods
    def log_debug(self, message: str):
        """Log debug message"""
        if hasattr(self, 'logger'):
            self.logger.debug(message)
    
    def log_info(self, message: str):
        """Log info message"""
        if hasattr(self, 'logger'):
            self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        if hasattr(self, 'logger'):
            self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message"""
        if hasattr(self, 'logger'):
            self.logger.error(message)
    
    def log_critical(self, message: str):
        """Log critical message"""
        if hasattr(self, 'logger'):
            self.logger.critical(message)
    
    def log_operation_start(self, operation: str, details: str = None):
        """Log the start of an operation"""
        msg = f"=== STARTING: {operation} ==="
        if details:
            msg += f" ({details})"
        self.log_info(msg)
    
    def log_operation_end(self, operation: str, success: bool = True, details: str = None):
        """Log the end of an operation"""
        status = "SUCCESS" if success else "FAILED"
        msg = f"=== {status}: {operation} ==="
        if details:
            msg += f" ({details})"
        if success:
            self.log_info(msg)
        else:
            self.log_error(msg)
    
    def close(self):
        """Clean up resources"""
        self.log_info("Closing CLI instance")
        
        if self.backend:
            try:
                self.backend.close()
                self.log_info("Backend closed successfully")
            except Exception as e:
                self.log_error(f"Error closing backend: {e}")
        
        if self.initialization_errors:
            self.log_warning(f"CLI closed with {len(self.initialization_errors)} initialization errors")
        
        self.log_info(f"CLI instance '{self.name}' closed")


# Backward compatibility - maintain session property for local backend
@property
def session(self):
    """Get database session (for backward compatibility with local backend)"""
    if isinstance(self.backend, LocalBackend):
        return self.backend.session
    return None

# Add session property to BaseCLI
BaseCLI.session = session