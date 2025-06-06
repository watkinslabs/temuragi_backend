import os
import logging
from logging.handlers import RotatingFileHandler
from tabulate import tabulate
from .config import config
from .register_db import register_models_for_cli, get_model
from app.utils.component_export import ComponentExporter


class BaseCLI:
    """
    Base CLI class with logging, database support, and consistent output
    """
    
    def __init__(self, name="cli", log_level=None, log_file=None, connect_db=True, verbose=False, show_icons=True, table_format=None):
        """
        Initialize CLI with logging and optional database connection
        
        Args:
            name: Name for this CLI instance (used in logging)
            log_level: Override config LOG_LEVEL
            log_file: Override config LOG_FILE
            connect_db: Whether to establish database connection
            verbose: Enable verbose logging (debug level)
            show_icons: Whether to show icons in output messages
            table_format: Table format for tabulate (overrides config)
        """
        self.name = name
        self.verbose = verbose
        self.show_icons = show_icons
        self.session = None
        self.exporter = None
        
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
        self._setup_logger(log_level, log_file)
        self.log_info(f"CLI instance '{self.name}' initializing")
        self.log_debug(f"Table format set to: {self.table_format}")
        
        # Setup database connection if requested
        if connect_db:
            self._setup_database()
            self.exporter = ComponentExporter(self.session, self) 
        
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
        self.logger.setLevel(log_level)
        self.logger.propagate = False
    
    def _setup_database(self):
        """Setup database connection using register_models_for_cli"""
        try:
            self.log_info("Establishing database connection")
            self.session = register_models_for_cli()
            self.log_info("Database connection established successfully")
        except Exception as e:
            self.log_error(f"Failed to establish database connection: {e}")
            raise
    
    def get_model(self, model_name):
        """Get a model from the registry with logging"""
        self.log_debug(f"Retrieving model: {model_name}")
        model = get_model(model_name)
        if model:
            self.log_debug(f"Model '{model_name}' retrieved successfully")
        else:
            self.log_warning(f"Model '{model_name}' not found in registry")
        return model
    
    def output(self, message, output_type='info'):
        """
        Unified output method with optional icons
        
        Args:
            message: Message to display
            output_type: Type of output (success, error, warning, info, debug)
        """
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
        
        if headers:
            print(tabulate(rows, headers=headers, tablefmt=format_to_use))
        else:
            print(tabulate(rows, tablefmt=format_to_use))
    
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
        self.logger.debug(message)
    
    def log_info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def log_warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def log_critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
    
    def close(self):
        """Clean up resources"""
        if self.session:
            self.log_info("Closing database session")
            self.session.close()
            self.session = None
        self.log_info(f"CLI instance '{self.name}' closed")