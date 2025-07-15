import os
import logging
from logging.handlers import RotatingFileHandler

loger=None

def register_logger(app):
    """
    Initialize and configure application logger
    
    Args:
        app: Flask app instance
    """
    log_level = app.config['log_level']
    log_file = app.config['log_file']
    max_bytes = 10485760
    backup_count = 5

    
    # Add process identifier to log file
    if os.environ.get('WERKZEUG_RUN_MAIN'):
        # Reloader process (main app)
        log_file = log_file.replace('.log', '_app.log')
    else:
        # Main process
        log_file = log_file.replace('.log', '_main.log')
    
    # Rest of setup with modified log_file...

    # Configure logging format
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
    
    # Clear existing handlers and set up new configuration
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # Ensure propagation to root logger is disabled to avoid duplicate logs
    app.logger.propagate = False
    
    app.logger.info(f"Flask application '{app.name}' initialized with logger")