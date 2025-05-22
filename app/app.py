import os
import importlib
import inspect
from flask import Flask, g , session 
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from .engines import Engines
from .config import config 
from .utils.route_collector import collect_blueprint_routes
from .utils.logger import register_logger


from ._system.connection.connection_manager import setup_connection_manager


def register_db(app: Flask):
    config_engine = create_engine(app.config['DATABASE_URI'])
    app.db_session  = scoped_session(sessionmaker(bind=config_engine))
    
    register_models('_system', app)

    @app.teardown_appcontext
    def cleanup_sessions(exc=None):
        app.db_session.remove()

def register_models(path, app):
    """Recursively discover and register SQLAlchemy models ending with 'model.py'"""
    base_dir = os.path.join(os.path.dirname(__file__), path)
    os.makedirs(base_dir, exist_ok=True)
    
    # Determine root package from this module's package context
    root_pkg = __package__  # e.g. 'ahoy2'
    
    # Convert path to package notation
    pkg_root = path.replace(os.sep, '.')
    
    # Track imported models to prevent duplicates
    imported_models = set()
    
    for dirpath, dirnames, filenames in os.walk(base_dir):
        # Filter for files ending with 'model.py'
        model_files = [f for f in filenames if f.endswith('model.py')]
        
        for model_file in model_files:
            # Compute relative path from base_dir
            rel = os.path.relpath(dirpath, base_dir)
            parts = [] if rel == '.' else rel.split(os.sep)
            
            # Build full import path
            module_name = model_file[:-3]  # Remove .py extension
            import_path = '.'.join(filter(None, [root_pkg, pkg_root] + parts + [module_name]))
            
            if import_path in imported_models:
                continue
                
            try:
                # Import the model module
                importlib.import_module(import_path)
                imported_models.add(import_path)
                app.logger.info(f"Registered model: {import_path}")
            except ImportError as e:
                app.logger.warning(f"Could not import model at {import_path}: {e}")        

def register_blueprints(prefix ,path, app):
    """Recursively discover and register blueprints from view.py only, skip "templates" and "static" dirs,
    abort if unexpected files present in categorization dirs. Once a module is found (view.py present), do not recurse further.

    Module dirs are identified by view.py (they may contain any files).
    Categorization dirs (used only for grouping) must contain only subdirectories and __init__.py."""
    base_dir = os.path.join(os.path.dirname(__file__), path)
    os.makedirs(base_dir, exist_ok=True)

    # Determine root package from this module's package context
    root_pkg = __package__  

    # Convert path to package notation, e.g. 'modules/sub' -> 'modules.sub'
    pkg_root = path.replace(os.sep, '.')

    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        dirnames[:] = [d for d in dirnames ]

        if 'view.py' in filenames:
            # Compute subpackage path relative to base_dir
            rel = os.path.relpath(dirpath, base_dir)
            parts = [] if rel == '.' else rel.split(os.sep)
            # Build full import path without relying on __main__
            import_path = '.'.join(filter(None, [root_pkg, pkg_root] + parts + ['view']))
            try:
                view_module = importlib.import_module(import_path)
                bp = getattr(view_module, 'bp', None)
                if bp:
                    
                    full_prefix = bp.url_prefix if getattr(view_module, 'no_prefix', False) else f"{prefix}{bp.url_prefix}"
                    app.register_blueprint(bp, url_prefix=full_prefix)
                    app.logger.info(f"Registered blueprint: {bp.name} with URL prefix: {full_prefix}")
            except ImportError as e:
                app.logger.warning(f"Could not import view at {import_path}... {e}")

            dirnames[:] = []
            continue

        if '__init__.py' in filenames:
            extras = [f for f in filenames if f != '__init__.py']
            if extras:
                raise RuntimeError(f"Unexpected files {extras} in grouping directory {dirpath}")
            continue

        # continue recursion for non-package, non-module dirs
        

def register_hooks(path, app):
    """Recursively discover and register hooks from hook.py only, skip "templates" and "static" dirs.
    Classify a directory as a module if it contains any files besides __init__.py; modules may contain any files.
    For module dirs: if hook.py exists, import and register its register_* functions, then stop recursion.
    Categorization dirs (only __init__.py or empty) are recursed into without error."""

    base_dir = os.path.join(os.path.dirname(__file__), path)
    os.makedirs(base_dir, exist_ok=True)

    root_pkg = __package__
    pkg_root = path.replace(os.sep, '.')

    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=True):
        # Skip unwanted dirs
        dirnames[:] = [d for d in dirnames]

        # Determine if this is a module: any files besides __init__.py
        module_files = [f for f in filenames if f != '__init__.py']
        if module_files:
            # This is a module directory
            rel = os.path.relpath(dirpath, base_dir)
            parts = [] if rel == '.' else rel.split(os.sep)
            hook_path = os.path.join(dirpath, 'hook.py')
            if 'hook.py' in filenames:
                import_path = '.'.join(filter(None, [root_pkg, pkg_root] + parts + ['hook']))
                try:
                    hook_module = importlib.import_module(import_path)
                    for name, func in inspect.getmembers(hook_module, inspect.isfunction):
                        if name.startswith('register_'):
                            try:
                                func(app)
                                app.logger.info(f"Registered hook {name} from {import_path}")
                            except Exception as exc:
                                app.logger.error(f"Error in {name} from {import_path}: {exc}")
                except ImportError as e:
                    app.logger.warning(f"Could not import hook at {import_path}... {e}")

            # Stop recursion into module directories
            dirnames[:] = []
        # else: categorization dir -> continue recursion



def create_app():
    app = Flask(__name__)

    app.config.update(config)
    register_logger(app)
    register_db(app)
    # http error pages, theme
    register_blueprints(app.config.get('ROUTE_PREFIX', ''),"_system",app)
    # management side of system
    register_blueprints(app.config.get('ADMIN_ROUTE_PREFIX', ''),"admin",app)
    # ops side
    register_blueprints(app.config.get('ROUTE_PREFIX', '')      , "_user",app)

    register_hooks("_system",app)
    register_hooks("admin",app)
    register_hooks("_user",app)

    collect_blueprint_routes(app)

    return app

app = create_app()
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)