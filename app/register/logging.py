# app/register/logging.py
import logging
import sys
import json
from datetime import datetime

class k8s_json_formatter(logging.Formatter):
    """Custom JSON formatter for Kubernetes environments"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add any extra fields
        if hasattr(record, 'event'):
            log_obj['event'] = record.event
            
        # Add all extra fields that were passed
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'thread', 'threadName', 'getMessage', 'event']:
                log_obj[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


class development_formatter(logging.Formatter):
    """Human-readable formatter for development"""
    
    def format(self, record):
        # Base format
        base_format = super().format(record)
        
        # Add extra fields if they exist
        extras = []
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'thread', 'threadName', 'getMessage']:
                extras.append(f"{key}={value}")
        
        if extras:
            return f"{base_format} | {' '.join(extras)}"
        return base_format


def register_logger(app):
    """Configure logging for the application"""
    
    # Determine environment
    is_production = app.config.get('ENV', 'development').lower() == 'production'
    log_level = app.config.get('LOG_LEVEL', 'INFO' if is_production else 'DEBUG')
    
    # Clear ALL handlers to prevent any file logging
    logging.root.handlers = []
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True
    
    # Create ONLY stdout handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on environment
    if is_production or app.config.get('JSON_LOGS', False):
        # Use JSON formatter for production/k8s
        handler.setFormatter(k8s_json_formatter())
    else:
        # Use human-readable formatter for development
        formatter = development_formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.setLevel(getattr(logging, log_level))
    logging.root.addHandler(handler)
    
    # Configure Flask's logger to use our setup
    app.logger.handlers = []
    app.logger.propagate = True
    
    # Disable Flask/Werkzeug file logging
    logging.getLogger('werkzeug').handlers = []
    logging.getLogger('werkzeug').propagate = True
    
    # Ensure no file handlers anywhere
    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logging.root.removeHandler(handler)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info("Logging configured", extra={
        "event": "logging_configured",
        "environment": "production" if is_production else "development",
        "log_level": log_level,
        "json_logs": is_production or app.config.get('JSON_LOGS', False),
        "handlers": [type(h).__name__ for h in logging.root.handlers]
    })