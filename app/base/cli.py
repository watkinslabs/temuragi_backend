import os
import logging
import traceback
from logging.handlers import RotatingFileHandler
from tabulate import tabulate

from app.config import config
from app.register.classes import register_classes, get_class, get_model


# Track if registration has been done for this process
_cli_registry_initialized = False
_cli_db_initialized = False

class AppBase:
    session=None
    logger=None

    def __init__(self):
        pass
    

class BaseCLI:
    """
    Base CLI class with logging, database support, and class registry
    """

    def __init__(self, name="cli", log_level=None, log_file=None, connect_db=True, verbose=False, show_icons=True, table_format=None, console_logging=False):
        """
        Initialize CLI with logging, database, and class registry

        Args:
            name: Name for this CLI instance (used in logging)
            log_level: Override config LOG_LEVEL
            log_file: Override config LOG_FILE
            connect_db: Whether to establish database connection
            verbose: Enable verbose logging (debug level)
            show_icons: Whether to show icons in output messages
            table_format: Table format for tabulate (overrides config)
            console_logging: Also log to console (useful for debugging)
        """
        self.name = name
        self.verbose = verbose
        self.show_icons = show_icons
        self.console_logging = console_logging
        self.session = None
        self.initialization_errors = []
        self.app=AppBase()

        # Configure table format from config or parameter
        self.table_format = table_format or config.get('CLI_TABLE_FORMAT', 'simple')

        # Icon mapping for output types
        self._icons = {
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ',
            'debug': '🔍'
        } if show_icons else {}

        # Setup logging first
        try:
            self._setup_logger(log_level, log_file)
            self.log_info(f"CLI instance '{self.name}' initializing")
            self.log_debug(f"Table format set to: {self.table_format}")
            self.log_debug(f"Verbose mode: {self.verbose}")
            self.log_debug(f"Console logging: {self.console_logging}")
        except Exception as e:
            self.initialization_errors.append(f"Logger setup failed: {e}")
            print(f"ERROR: Failed to setup logger: {e}")

        if name != "tmcli":  # Don't setup for the master CLI itself


            try:
                self._setup_class_registry()
            except Exception as e:
                self.initialization_errors.append(f"Class registry setup failed: {e}")
                self.log_warning(f"Class registry setup failed: {e}")
                if not self.console_logging:
                    print(f"WARNING: Class registry setup failed: {e}")

            try:
                self._setup_database()
                if self.session:
                    self.log_info("Database connection established successfully")
            except Exception as e:
                self.initialization_errors.append(f"Database setup failed: {e}")
                self.log_critical(f"Database setup failed: {e}")
                self._log_full_traceback("Database setup error", e)
                if not self.console_logging:
                    print(f"CRITICAL: Database setup failed: {e}")
                raise
        if self.initialization_errors:
            self.log_warning(f"CLI initialized with {len(self.initialization_errors)} errors")
            for error in self.initialization_errors:
                self.log_error(f"Initialization error: {error}")
        else:
            self.log_info(f"CLI instance '{self.name}' initialized successfully")

    def _setup_logger(self, log_level=None, log_file=None):
        """Setup logger with same parameters as register_logger"""
        # Use provided values or fall back to config
        if self.verbose:
            log_level = logging.DEBUG
        else:
            log_level = log_level or config.get('LOG_LEVEL', logging.INFO)

        log_file = log_file or config.get('LOG_FILE', f'logs/{self.name}_cli.log')
        max_bytes = 10485760
        backup_count = 5

        # Configure logging format (same as register_logger)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )

        # Configure file handler with rotation
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else '.'
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)

        # Create and configure logger
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

        # Log the logger configuration
        self.logger.info(f"Logger configured - Level: {logging.getLevelName(log_level)}, File: {log_file}")
        if self.console_logging:
            self.logger.info("Console logging enabled")

    def _setup_class_registry(self):
        """Setup class registry for CLI usage - only register once per process"""
        global _cli_registry_initialized

        try:
            if not _cli_registry_initialized:
                self.log_info("Registering classes for CLI usage (first time)")
                # Call register_classes to trigger the autoloader
                register_classes()
                _cli_registry_initialized = True
                
            # Get the registry after it's been populated
            self.log_info(f"Class registry loadedclasses")
                
        except Exception as e:
            self.log_error(f"Failed to setup class registry: {e}")
            raise

    def _setup_database(self):
        """Setup database connection - models are already loaded by autoloader"""
        global _cli_db_initialized

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            # Create engine and session
            engine = create_engine(config['DATABASE_URI'])
            session_factory = sessionmaker(bind=engine)
            self.session = session_factory()
            self.app.session=self.session
            self.log_info("Database session created successfully")
            
            # Verify models are available (they should be loaded by autoloader)
            from app.models import get_model
            test_model = get_model('User')  # or any model you know should exist
            if test_model:
                self.log_debug(f"Models are available - test model 'User' found: {test_model}")
            else:
                self.log_warning("Models may not be properly loaded by autoloader")
                
        except Exception as e:
            self.log_error(f"Failed to establish database connection: {e}")
            raise
        
    def _mask_database_uri(self, uri):
        """Mask sensitive parts of database URI for logging"""
        if not uri or uri == 'NOT_SET':
            return uri

        try:
            # Simple masking - replace password with ***
            if '://' in uri and '@' in uri:
                parts = uri.split('://')
                if len(parts) == 2:
                    protocol = parts[0]
                    rest = parts[1]
                    if '@' in rest:
                        auth_host = rest.split('@')
                        if len(auth_host) == 2:
                            auth = auth_host[0]
                            host = auth_host[1]
                            if ':' in auth:
                                user = auth.split(':')[0]
                                return f"{protocol}://{user}:***@{host}"
            return uri
        except:
            return "URI_MASKED"

    def _log_full_traceback(self, context, exception):
        """Log full traceback for debugging"""
        self.log_error(f"{context}: {exception}")
        if self.verbose:
            tb_str = traceback.format_exc()
            self.log_debug(f"Full traceback for {context}:\n{tb_str}")

    def get_model(self, model_name):
        """Get a model from the registry with logging"""
        self.log_debug(f"Retrieving model: {model_name}")

        try:
            model = get_model(model_name)
            if model:
                self.log_debug(f"Model '{model_name}' retrieved successfully: {model.__name__}")
                self.log_debug(f"Model table: {getattr(model, '__tablename__', 'NO_TABLE')}")
            else:
                self.log_warning(f"Model '{model_name}' not found in registry")
                # Log available models for debugging
                try:
                    from app.register.database import list_models
                    available = list_models()
                    self.log_debug(f"Available models: {available[:10] if available else 'None'}...")
                except:
                    pass
            return model
        except Exception as e:
            self.log_error(f"Error retrieving model '{model_name}': {e}")
            self._log_full_traceback("Model retrieval error", e)
            return None

    def get_class(self, class_name):
        """Get a class from the registry with logging"""
        self.log_debug(f"Retrieving class: {class_name}")

        try:
            cls = get_class(class_name)
            if cls:
                self.log_debug(f"Class '{class_name}' retrieved successfully: {cls.__name__}")
                self.log_debug(f"Class module: {getattr(cls, '__module__', 'NO_MODULE')}")
            else:
                self.log_warning(f"Class '{class_name}' not found in registry")
                # Log available classes for debugging
                try:
                    from app.register.classes import list_classes
                    available = list_classes()
                    self.log_debug(f"Available classes: {available[:10] if available else 'None'}...")
                except:
                    pass
            return cls
        except Exception as e:
            self.log_error(f"Error retrieving class '{class_name}': {e}")
            self._log_full_traceback("Class retrieval error", e)
            return None

    def execute_with_logging(self, operation_name, func, *args, **kwargs):
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
        """Get current timestamp for duration calculations"""
        import time
        return time.time()

    def validate_session(self):
        """Validate database session is working"""
        if not self.session:
            self.log_error("No database session available")
            return False

        try:
            self.session.execute("SELECT 1")
            self.log_debug("Session validation successful")
            return True
        except Exception as e:
            self.log_error(f"Session validation failed: {e}")
            return False

    def output(self, message, output_type='info'):
        """
        Unified output method with optional icons

        Args:
            message: Message to display
            output_type: Type of output (success, error, warning, info, debug)
        """
        # Always log the output message
        if output_type == 'error':
            self.log_error(f"OUTPUT: {message}")
        elif output_type == 'warning':
            self.log_warning(f"OUTPUT: {message}")
        elif output_type == 'debug':
            self.log_debug(f"OUTPUT: {message}")
        else:
            self.log_info(f"OUTPUT: {message}")

        # Display to user
        icon = self._icons.get(output_type, '')
        if icon:
            print(f"{icon} {message}")
        else:
            print(message)

    def output_table(self, rows, headers=None, table_format=None):
        """
        Output formatted table using configured format

        Args:
            rows: List of row data
            headers: Optional column headers
            table_format: Override default table format
        """
        format_to_use = table_format or self.table_format
        self.log_debug(f"Outputting table with format: {format_to_use}")
        self.log_debug(f"Table rows: {len(rows) if rows else 0}")

        try:
            if headers:
                table_output = tabulate(rows, headers=headers, tablefmt=format_to_use)
                print(table_output)
                self.log_debug(f"Table output with headers: {headers}")
            else:
                table_output = tabulate(rows, tablefmt=format_to_use)
                print(table_output)
                self.log_debug("Table output without headers")
        except Exception as e:
            self.log_error(f"Failed to output table: {e}")
            self.output_error(f"Table display failed: {e}")

    def output_success(self, message):
        """Output success message"""
        self.output(message, 'success')

    def output_error(self, message):
        """Output error message"""
        self.output(message, 'error')

    def output_warning(self, message):
        """Output warning message"""
        self.output(message, 'warning')

    def output_info(self, message):
        """Output info message"""
        self.output(message, 'info')

    def output_debug(self, message):
        """Output debug message (only if verbose)"""
        if self.verbose:
            self.output(message, 'debug')

    def log_debug(self, message):
        """Log debug message"""
        if hasattr(self, 'logger'):
            self.logger.debug(message)

    def log_info(self, message):
        """Log info message"""
        if hasattr(self, 'logger'):
            self.logger.info(message)

    def log_warning(self, message):
        """Log warning message"""
        if hasattr(self, 'logger'):
            self.logger.warning(message)

    def log_error(self, message):
        """Log error message"""
        if hasattr(self, 'logger'):
            self.logger.error(message)

    def log_critical(self, message):
        """Log critical message"""
        if hasattr(self, 'logger'):
            self.logger.critical(message)

    def log_operation_start(self, operation, details=None):
        """Log the start of an operation"""
        msg = f"=== STARTING: {operation} ==="
        if details:
            msg += f" ({details})"
        self.log_info(msg)

    def log_operation_end(self, operation, success=True, details=None):
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

        if self.session:
            try:
                self.log_info("Closing database session")
                self.session.close()
                self.session = None
                self.log_info("Database session closed successfully")
            except Exception as e:
                self.log_error(f"Error closing database session: {e}")

        if self.initialization_errors:
            self.log_warning(f"CLI closed with {len(self.initialization_errors)} initialization errors")

        self.log_info(f"CLI instance '{self.name}' closed")