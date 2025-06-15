import os
import importlib
import inspect
from collections import defaultdict, deque
from flask import Flask, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config import config

# Global model registry
_model_registry = {}


class Engines:
    """Holds your engines.  One for config DB, and lazily-created ones for each target DSN."""
    def __init__(self, config_uri):
        # single engine to your Postgres "config server"
        self.config_engine = create_engine(config_uri, pool_size=5, max_overflow=10)
        # session factory for config DB
        self.ConfigSession = sessionmaker(bind=self.config_engine)
        # cache for per-page engines
        self._target_engines = {}

    def get_config_session(self):
        return self.ConfigSession()

    def get_target_engine(self, dsn, **opts):
        # reuse an engine per-DSN (keyed by the full DSN string)
        if dsn not in self._target_engines:
            self._target_engines[dsn] = create_engine(dsn, **opts)
        return self._target_engines[dsn]
    

def get_model(name):
    """Get a model class by name from the registry"""
    return _model_registry.get(name)


def list_models():
    """List all registered model names"""
    return list(_model_registry.keys())


def get_all_models():
    """Get dictionary of all registered models"""
    return _model_registry.copy()


def register_models_for_cli():
    """Register models for CLI usage without full Flask app"""
    # Create engine
    engine = create_engine(config['DATABASE_URI'])

    
    # Discover and import models (populates _model_registry)
    discover_and_import(None,"_model.py")
    
    # Return session for CLI use
    session_factory = sessionmaker(bind=engine)
    return session_factory()



def register_db(app: Flask):
    """Initialize database and register all models with dependency-aware ordering"""

    # Clear registry for fresh start
    global _model_registry
    print(f"Model registry size before clear: {len(_model_registry)}")
    _model_registry.clear()

    # Create database engine and session
    config_engine = create_engine(app.config['DATABASE_URI'])
    app.db_session = scoped_session(sessionmaker(bind=config_engine))

    # Discover and import all models with dependency resolution
    discover_and_import(app,"_model.py")

    # Create all tables BEFORE creating permissions
    create_all_tables(app, config_engine)

    # NOW create API permissions after tables exist
    create_api_permissions_for_all_models(app)

    # Setup session cleanup
    @app.teardown_appcontext
    def cleanup_sessions(exc=None):
        app.db_session.remove()

    # Make session available in request context
    @app.before_request
    def setup_request_context():
        if not hasattr(g, 'session'):
            g.session = app.db_session

    # Make model registry available on app
    app.models = _model_registry
    app.get_model = get_model

    import app.models as models_module
    for name, model in _model_registry.items():
        if not name.islower():
            setattr(models_module, name, model)
            if name not in models_module.__all__:
                models_module.__all__.append(name)    

def create_api_permissions_for_all_models(app):
    """Create API permissions for all registered models after tables exist"""
    if app:
        app.logger.info("Creating API permissions for all models...")
    
    created_total = 0
    
    # Get unique model classes (avoid duplicates from table name aliases)
    model_classes = []
    seen_tables = set()
    
    for name, model_class in _model_registry.items():
        if (hasattr(model_class, '__tablename__') and
            hasattr(model_class, '__name__') and
            name == model_class.__name__ and  # Only actual class names
            model_class.__tablename__ not in seen_tables):
            model_classes.append(model_class)
            seen_tables.add(model_class.__tablename__)
    
    for model_class in model_classes:
        try:
            created_count = create_model_api_permissions(model_class, app)
            created_total += created_count
        except Exception as e:
            if app:
                app.logger.warning(f"Failed to create permissions for {model_class.__tablename__}: {e}")
    
    if app:
        app.logger.info(f"Created {created_total} total API permissions")

def create_model_api_permissions(model_class, app=None):
    """Auto-create API permissions for a model"""
    try:
        # Get Permission model from registry
        permission_model = get_model('Permission')
        if not permission_model:
            if app:
                app.logger.debug("Permission model not available for auto-permission creation")
            return 0

        # Get session - use app.db_session if available, otherwise create one
        if app and hasattr(app, 'db_session'):
            session = app.db_session()
        else:
            # Fallback for CLI usage
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(config['DATABASE_URI'])
            session_factory = sessionmaker(bind=engine)
            session = session_factory()

        table_name = model_class.__tablename__
        model_name = model_class.__name__
        api_actions = ['read', 'write', 'update', 'delete']

        created_count = 0
        for action in api_actions:
            permission_name = f"{table_name}:{action}"
            
            # Check if permission already exists
            existing = permission_model.find_by_name(session, permission_name)
            if not existing:
                success, result = permission_model.create_permission(
                    session, 
                    service="api",
                    action=action,
                    resource=model_name,
                    description=f"API {action} access for {model_name}"
                )
                if success:
                    created_count += 1
                    if app:
                        app.logger.debug(f"Created permission: {permission_name}")

        if created_count > 0 and app:
            app.logger.debug(f"Created {created_count} API permissions for {table_name}")

        # Close session if we created it
        if not (app and hasattr(app, 'db_session')):
            session.close()

        return created_count

    except Exception as e:
        if app:
            app.logger.warning(f"Failed to create API permissions for {model_class.__tablename__}: {e}")
        else:
            print(f"Warning: Failed to create API permissions for {model_class.__tablename__}: {e}")
        return 0

def create_all_tables(app, engine):
    """Create database tables from all loaded models using existing dependency resolution"""
    try:
        # Find BaseModel
        base_paths = [
            'app.base.model',
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

        app.logger.info("Creating database tables using existing dependency resolution...")

        # Check if we have models in registry
        if not _model_registry:
            app.logger.warning("No models in registry, using simple create_all")
            BaseModel.metadata.create_all(engine, checkfirst=True)
            return

        # The models are already imported in the correct dependency order
        # SQLAlchemy's create_all() handles FK dependencies, but we can still 
        # respect the model dependency order if needed
        
        # Get model classes in the order they were registered (which follows dependencies)
        model_classes = []
        seen_tables = set()
        
        for name, model_class in _model_registry.items():
            if (hasattr(model_class, '__tablename__') and
                hasattr(model_class, '__name__') and
                name == model_class.__name__ and  # Only actual class names
                model_class.__tablename__ not in seen_tables):
                model_classes.append(model_class)
                seen_tables.add(model_class.__tablename__)

        app.logger.info(f"Found {len(model_classes)} model classes")

        # Create all tables - SQLAlchemy handles the actual dependency order
        BaseModel.metadata.create_all(engine, checkfirst=True)

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


def discover_and_import(app=None,file_pattern="_model.py"):
    """Discover all class files and import them with dependency resolution"""
    from app.scanner import ModuleScanner
    from app.resolver import ClassDependencyResolver
    
    # Create scanner for _class.py files
    scanner = ModuleScanner(
        base_paths=config['SYSTEM_SCAN_PATHS'],
        file_suffix=file_pattern,
        logger=app.logger if app else None
    )
    
    # Scan for all class modules
    all_modules = scanner.scan()
    
    if not all_modules:
        if app:
            app.logger.warning("No Model files found")
        return
    
    if app:
        app.logger.info(f"Discovered {len(all_modules)} Model class files")
    
    # Create resolver
    resolver = ClassDependencyResolver(logger=app.logger if app else None)
    
    # Define callback to register classes as they're processed
    def register_callback(class_name, class_obj, module, info):
        _model_registry[class_name] = class_obj
        if app:
            app.logger.info(f"  ✓ {class_name} from {info['display']}")
    
    try:
        # Resolve and register in dependency order
        resolver.resolve_class_dependencies(all_modules, callback=register_callback)
        
        if app:
            app.logger.info(f"Registered {len(_model_registry)} Model classes in registry")
            
    except Exception as e:
        if app:
            app.logger.error(f"Failed to resolve Model class dependencies: {e}")
        raise    