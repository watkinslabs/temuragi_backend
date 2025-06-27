import os
import importlib
import inspect
from collections import defaultdict, deque
from flask import Flask, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.orm.session import Session as SessionType
from sqlalchemy.exc import SQLAlchemyError

from app.config import config


class RoutingSession(Session):
    """Custom session that routes queries to the correct engine based on model's __bind_key__"""
    
    def __init__(self, bind=None, **options):
        # Extract our custom parameters
        self._db_registry = options.pop('db_registry', None)
        self._default_bind = options.pop('default_bind', bind)
        
        # Pass the bind to parent class
        super().__init__(bind=self._default_bind, **options)
    
    def get_bind(self, mapper=None, clause=None):
        """Return the engine for the given model based on its __bind_key__"""
        if mapper is not None:
            model_class = mapper.class_
            bind_key = getattr(model_class, '__bind_key__', None)
            
            if bind_key:
                # Get or create engine for this bind key
                engine = self._db_registry.get_or_create_engine(bind_key)
                if engine:
                    return engine
        
        return self._default_bind


class DynamicDatabaseRegistry:
    """Registry for dynamically created database engines based on stored connections"""
    
    def __init__(self):
        self.main_engine = None
        self._dynamic_engines = {}  # Cache for dynamically created engines
        self._routing_session = None
        self._app = None
    
    def init_app(self, app: Flask):
        """Initialize the main database connection"""
        self._app = app
        
        # Main/default database
        main_uri = app.config.get('DATABASE_URI')
        if not main_uri:
            raise ValueError("DATABASE_URI not configured")
        
        self.main_engine = create_engine(main_uri, pool_size=5, max_overflow=10)
        app.logger.info(f"Initialized main database engine")
        
        # Create the routing session factory
        session_factory = sessionmaker(
            class_=RoutingSession,
            bind=self.main_engine,
            db_registry=self,
            default_bind=self.main_engine
        )
        
        self._routing_session = scoped_session(session_factory)
        
        return self._routing_session
    
    def get_or_create_engine(self, bind_key):
        """Get or create an engine for the given bind key"""
        if not bind_key:
            return self.main_engine
        
        # Check cache first
        if bind_key in self._dynamic_engines:
            return self._dynamic_engines[bind_key]
        
        # Look up connection from database
        try:
            # Use a separate session to query the main database
            main_session = sessionmaker(bind=self.main_engine)()
            
            # Import here to avoid circular imports
            from app.models.connection import Connection
            
            connection = main_session.query(Connection).filter_by(name=bind_key).first()
            main_session.close()
            
            if not connection:
                self._app.logger.warning(f"No connection found for bind_key: {bind_key}")
                return None
            
            # Get the connection string with credentials
            connection_string = connection.get_connection_string()
            
            # Create the engine
            engine = create_engine(connection_string, pool_size=5, max_overflow=10)
            
            # Cache it
            self._dynamic_engines[bind_key] = engine
            
            self._app.logger.info(f"Created dynamic engine for bind_key: {bind_key}")
            
            return engine
            
        except Exception as e:
            self._app.logger.error(f"Failed to create engine for bind_key {bind_key}: {e}")
            return None
    
    def create_all_tables(self, base_model, app):
        """Create tables for all models in their respective databases"""
        
        # Group models by their bind key
        models_by_bind = defaultdict(list)
        
        from .classes import _class_registry
        
        for name, model_class in _class_registry.items():
            if (hasattr(model_class, '__tablename__') and
                hasattr(model_class, '__name__') and
                name == model_class.__name__):
                
                bind_key = getattr(model_class, '__bind_key__', None)
                models_by_bind[bind_key].append(model_class)
        
        # First, create tables for models without bind_key (main database)
        if None in models_by_bind:
            main_models = models_by_bind[None]
            app.logger.info(f"Creating {len(main_models)} tables in main database")
            
            tables_to_create = [model.__table__ for model in main_models]
            base_model.metadata.create_all(self.main_engine, tables=tables_to_create, checkfirst=True)
            
            self._log_tables(self.main_engine, 'main', app)
        
        # Then create tables for models with bind_key (dynamic databases)
        for bind_key, models in models_by_bind.items():
            if bind_key is not None:  # Skip None, we handled it above
                engine = self.get_or_create_engine(bind_key)
                if engine:
                    app.logger.info(f"Creating {len(models)} tables for bind_key '{bind_key}'")
                    
                    tables_to_create = [model.__table__ for model in models]
                    base_model.metadata.create_all(engine, tables=tables_to_create, checkfirst=True)
                    
                    self._log_tables(engine, bind_key, app)
                else:
                    app.logger.warning(f"Skipping table creation for bind_key '{bind_key}' - no engine available")
    
    def _log_tables(self, engine, db_name, app):
        """Log tables in a database"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                app.logger.info(f"Database '{db_name}' has {len(tables)} tables: {', '.join(tables)}")
        except Exception as e:
            app.logger.error(f"Failed to list tables for '{db_name}': {e}")


# Global registry instance
db_registry = DynamicDatabaseRegistry()


def register_db(app: Flask):
    """Initialize database and register all models with dynamic multi-database support"""
    
    # Initialize the main database connection
    app.db_session = db_registry.init_app(app)
    
    # Setup session cleanup
    @app.teardown_appcontext
    def cleanup_sessions(exc=None):
        app.db_session.remove()
        
        # Also clean up any dynamic sessions if needed
        for engine in db_registry._dynamic_engines.values():
            engine.dispose()
    
    # Make session available in request context
    @app.before_request
    def setup_request_context():
        if not hasattr(g, 'session'):
            g.session = app.db_session
        
        # Also make the registry available for direct access if needed
        g.db_registry = db_registry


def create_all_tables(app, engine=None):
    """Create database tables from all loaded models"""
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
        
        app.logger.info("Creating database tables for all configured databases...")
        
        from .classes import _class_registry, get_model
        app.get_model = get_model
        
        # Use the registry to create tables in all databases
        db_registry.create_all_tables(BaseModel, app)
        
        app.logger.info("All database tables created successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to create tables: {e}")
        raise


# Utility functions for manual engine management if needed
def get_engine_for_bind_key(bind_key=None):
    """Get engine for a specific bind key"""
    return db_registry.get_or_create_engine(bind_key)


def refresh_dynamic_engine(bind_key):
    """Force refresh a dynamic engine (useful if connection details changed)"""
    if bind_key in db_registry._dynamic_engines:
        old_engine = db_registry._dynamic_engines[bind_key]
        old_engine.dispose()
        del db_registry._dynamic_engines[bind_key]
    
    return db_registry.get_or_create_engine(bind_key)