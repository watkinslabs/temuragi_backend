import os
import re
import importlib
import inspect
from flask import Flask, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from .engines import Engines
from .config import config
from .utils.route_collector import collect_blueprint_routes
from .utils.logger import register_logger


def register_db(app: Flask):
    """Initialize database and register all models with global ordering"""
    # Create database engine and session
    config_engine = create_engine(app.config['DATABASE_URI'])
    app.db_session = scoped_session(sessionmaker(bind=config_engine))
    
    # Discover and import all models globally
    discover_and_import_models(app)
    
    # Create all tables
    create_all_tables(app, config_engine)
    
    # Setup session cleanup
    @app.teardown_appcontext
    def cleanup_sessions(exc=None):
        app.db_session.remove()
    
    # Make session available in request context
    @app.before_request
    def setup_request_context():
        if not hasattr(g, 'session'):
            g.session = app.db_session


def discover_and_import_models(app):
    """Discover all model files and import them in global order"""
    scan_paths = config['SYSTEM_SCAN_PATHS']
    root_pkg = __package__
    
    # Find all model files across all paths
    all_models = []
    for scan_path in scan_paths:
        models = find_models_in_path(scan_path, root_pkg, app)
        all_models.extend(models)
    
    if not all_models:
        app.logger.warning("No model files found")
        return
    
    # Sort by global order number
    all_models.sort(key=lambda x: (x['order'], x['path']))
    
    app.logger.info(f"Loading {len(all_models)} models in order:")
    for model in all_models:
        app.logger.info(f"  {model['order']:3d}: {model['display']}")
    
    # Import models with retry for dependencies
    import_models(all_models, app)


def find_models_in_path(scan_path, root_pkg, app):
    """Find all model files in a specific path"""
    base_dir = os.path.join(os.path.dirname(__file__), scan_path)
    
    if not os.path.exists(base_dir):
        app.logger.debug(f"Path not found: {scan_path}")
        return []
    
    models = []
    pkg_path = scan_path.replace(os.sep, '.')
    
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith('model.py'):
                # Get order from filename
                order = get_model_order(filename)
                
                # Build import path
                rel_path = os.path.relpath(root, base_dir)
                path_parts = [] if rel_path == '.' else rel_path.split(os.sep)
                module_name = filename[:-3]  # Remove .py
                
                import_path = '.'.join([root_pkg, pkg_path] + path_parts + [module_name])
                display_path = '/'.join([scan_path] + path_parts + [filename])
                
                models.append({
                    'order': order,
                    'filename': filename,
                    'import_path': import_path,
                    'display': display_path,
                    'path': display_path
                })
    
    return models


def get_model_order(filename):
    """Extract order number from filename prefix: 20_menu_model.py -> 20"""
    # Primary pattern: number prefix
    match = re.match(r'^(\d+)_.*model\.py$', filename)
    if match:
        return int(match.group(1))
    
    # Special case: base models
    if 'base' in filename.lower():
        return 0
    
    # Default: load last
    return 999


def import_models(models, app):
    """Import models with retry logic for dependencies"""
    remaining = models.copy()
    imported = set()
    max_retries = 3
    retry = 0
    
    while remaining and retry < max_retries:
        failed_this_round = []
        progress = False
        
        for model in remaining[:]:
            try:
                module = importlib.import_module(model['import_path'])
                imported.add(model['import_path'])
                remaining.remove(model)
                progress = True
                
                app.logger.debug(f"✓ {model['display']}")
                
                # Log table names
                tables = [obj.__tablename__ for name, obj in inspect.getmembers(module, inspect.isclass) 
                         if hasattr(obj, '__tablename__')]
                if tables:
                    app.logger.debug(f"    Tables: {', '.join(tables)}")
                
            except ImportError as e:
                failed_this_round.append((model, str(e)))
        
        if not progress:
            retry += 1
        else:
            retry = 0
    
    # Log results
    if remaining:
        app.logger.warning(f"Failed to import {len(remaining)} models:")
        for model, error in failed_this_round:
            app.logger.warning(f"  {model['display']}: {error}")
    
    app.logger.info(f"Successfully imported {len(imported)} models")


def create_all_tables(app, engine):
    """Create database tables from all loaded models"""
    try:
        # Find BaseModel
        base_paths = [
            'app._system._core.base',
            'app._system.base', 
            'app.base'
        ]
        
        BaseModel = None
        for path in base_paths:
            try:
                module = importlib.import_module(path)
                BaseModel = getattr(module, 'BaseModel', None)
                if BaseModel:
                    break
            except ImportError:
                continue
        
        if not BaseModel:
            raise ImportError("BaseModel not found")
        
        # Create all tables
        BaseModel.metadata.create_all(engine)
        app.logger.info("Database tables created successfully")
        
        # Log table info
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = current_schema()
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            app.logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
        
    except Exception as e:
        app.logger.error(f"Failed to create tables: {e}")
        raise


def preview_model_order(scan_paths=None):
    """Preview model loading order without importing - for CLI/debugging"""
    if scan_paths is None:
        scan_paths = config['SYSTEM_SCAN_PATHS']
    
    all_models = []
    root_pkg = 'app'  # Hardcoded for CLI use
    
    for scan_path in scan_paths:
        base_dir = os.path.join(os.path.dirname(__file__), scan_path)
        if not os.path.exists(base_dir):
            continue
            
        pkg_path = scan_path.replace(os.sep, '.')
        
        for root, dirs, files in os.walk(base_dir):
            for filename in files:
                if filename.endswith('model.py'):
                    order = get_model_order(filename)
                    rel_path = os.path.relpath(root, base_dir)
                    path_parts = [] if rel_path == '.' else rel_path.split(os.sep)
                    
                    display_path = '/'.join([scan_path] + path_parts + [filename])
                    
                    all_models.append({
                        'order': order,
                        'filename': filename,
                        'display': display_path,
                        'scan_path': scan_path
                    })
    
    # Sort by order
    all_models.sort(key=lambda x: (x['order'], x['display']))
    
    return all_models