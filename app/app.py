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


def create_app():
    
    app = Flask(__name__)
      
    app.config.update(config)
    register_logger(app)
    
    # registeres the scan paths internally
    register_db(app)
    
    register_classes(app)

        

    # Register hooks for all scan paths
    for path in config['SYSTEM_SCAN_PATHS']:
        register_hooks(path, app)
    
    for path in config['SYSTEM_SCAN_PATHS']:
        register_blueprints(config['ROUTE_PREFIX'],path, app)
    

    return app

    
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5050)