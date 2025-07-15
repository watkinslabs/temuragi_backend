import os
import sys

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

from flask import Blueprint, redirect, request

from .config import config

bp = Blueprint('V1', __name__,)

@bp.route('/<path:path>')
def catch_all(path):
    return redirect(f'/v2/')

@bp.route('/')
def catch_all2():
    return redirect(f'/v2/')

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
    
    app = Flask(__name__)
    app.extensions={}
    
    app.config.update(config)
    register_logger(app)
    
    # registeres the scan paths internally
    register_classes()

    register_db(app)
    
        
    app.register_blueprint(bp)


    # Register hooks for all scan paths
    for path in config.scan_paths:
        register_hooks(path, app)
    
    for path in config.scan_paths:
        register_blueprints(config.route_prefix,path, app)
    
  


    return app

    
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=config.port)