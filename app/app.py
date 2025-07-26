import os
import sys
import logging

print(f"=== PROCESS INFO ===")
print(f"PID: {os.getpid()}")
print(f"PPID: {os.getppid()}")
print(f"WERKZEUG_RUN_MAIN: {os.environ.get('WERKZEUG_RUN_MAIN')}")
print(f"Python executable: {sys.executable}")
print(f"Command line: {' '.join(sys.argv)}")
print("===================")

from flask import Flask
from .config import config 
from .register.logging import register_logger
from .register.blueprints import register_blueprints
from .register.template_hooks import register_hooks
from .register.database import register_db
from .register.classes import register_classes

from flask import Blueprint, redirect

from .config import config

bp = Blueprint('V1', __name__,)

@bp.route('/<path:path>')
def catch_all(path):
    return redirect(config['route_prefix'])

@bp.route('/')
def catch_all2():
    return redirect(config['route_prefix'])

app=None

def set_app(instance):
    """Set the global app instance"""
    global app
    app = instance

def get_app():
    """Get the global app instance"""
    if app is None:
        raise RuntimeError("app not initialized yet")
    return app

def create_app():
    print("=== CREATE APP START ===")
    
    app = Flask(__name__)
    app.extensions={}
    
    app.config.update(config)
    print("Config updated")
    
    # Register logger first
    register_logger(app)
    print("Logger registered")
    
    # Test if logging is working
    test_logger = logging.getLogger(__name__)
    test_logger.info("Test log after register_logger")
    print(f"Root logger level: {logging.root.level}")
    print(f"Root logger handlers: {logging.root.handlers}")
    
    # Now register classes with logging enabled
    print("About to register classes...")
    print(f"Scan paths: {config['scan_paths']}")
    print(f"Base dir: {getattr(config, 'base_dir', 'NOT SET')}")
    
    try:
        register_classes()
        print("Classes registered successfully")
    except Exception as e:
        print(f"ERROR registering classes: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    register_db(app)
    print("Database registered")
        
    app.register_blueprint(bp)
    print("Blueprint registered")

    # Register hooks for all scan paths
    for path in config['scan_paths']:
        print(f"Registering hooks for path: {path}")
        register_hooks(path, app)
    
    for path in config['scan_paths']:
        print(f"Registering blueprints for path: {path}")
        register_blueprints(config['route_prefix'], path, app)
    
    print("=== CREATE APP COMPLETE ===")
    return app


app = create_app()

    
if __name__ == "__main__":
    print(f"Starting app on port {config['port']}")
    app.run(debug=True, host='0.0.0.0', port=config['port'])