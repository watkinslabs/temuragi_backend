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
    
    # In your RoutingSession.get_bind method, add logging:
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
        main_session = None
        try:
            # Use a separate session to query the main database
            main_session = sessionmaker(bind=self.main_engine)()
            
            # Import here to avoid circular imports
            from app.models import Connection
            
            # List all available connections first
            all_connections = main_session.query(Connection).all()
            
            connection = main_session.query(Connection).filter_by(name=bind_key).first()
            
            if not connection:
                return None
            
            
            # Get the connection string with credentials
            connection_string = connection.get_connection_string()
            
            # Create the engine
            engine = create_engine(connection_string, pool_size=5, max_overflow=10)
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
            
            # Cache it
            self._dynamic_engines[bind_key] = engine
            self._app.logger.info(f"Created dynamic engine for bind_key: {bind_key}")
            
            return engine
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._app.logger.error(f"Failed to create engine for bind_key {bind_key}: {e}")
            return None
        finally:
            if main_session:
                main_session.close()

    def create_all_tables(self, base_model, app):
        """Create tables for all models in their respective databases"""
        
        # Verify we have metadata
        if not hasattr(base_model, 'metadata'):
            app.logger.error(f"Base model has no metadata attribute: {base_model}")
            raise AttributeError("Base model must have metadata attribute")
        
        # Just create ALL tables in the main database, regardless of bind_key
        app.logger.info("Creating all tables in main database")
        
        # Create all tables defined in the metadata
        base_model.metadata.create_all(self.main_engine, checkfirst=True)
        
        self._log_tables(self.main_engine, 'main', app)
        
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

def create_all_tables(app, engine=None):
    """Debug version of create_all_tables with extensive logging"""
    from app.base.model import Base
    from sqlalchemy import MetaData
    
    if Base and hasattr(Base, 'metadata') and Base.metadata is not None:
        try:
            # Create a new metadata instance for filtered tables
            filtered_metadata = MetaData()
            
            # Track what we're doing
            total_tables = len(Base.metadata.tables)
            filtered_count = 0
            
            # Iterate through all tables in the original metadata
            for table_name, table in Base.metadata.tables.items():
                # Find the model class for this table
                model_class = None
                for mapper in Base.registry.mappers:
                    if mapper.class_.__table__.name == table.name:
                        model_class = mapper.class_
                        break
                
                # Check if model has NO __bind_key__ or it's None
                if model_class:
                    if not hasattr(model_class, '__bind_key__') or model_class.__bind_key__ is None:
                        # Copy table to filtered metadata
                        table.tometadata(filtered_metadata)
                        filtered_count += 1
                        app.logger.debug(f"   - Including table '{table_name}' (no bind_key)")
                    else:
                        app.logger.debug(f"   - Skipping table '{table_name}' (has bind_key='{model_class.__bind_key__}')")
                else:
                    # No model class found, include it by default
                    table.tometadata(filtered_metadata)
                    filtered_count += 1
                    app.logger.debug(f"   - Including table '{table_name}' (no model class found)")
            
            app.logger.info(f"   - Filtered {filtered_count} tables from {total_tables} total")
            
            # Only create tables if we have any to create
            if filtered_count > 0:
                filtered_metadata.create_all(engine, checkfirst=True)
                app.logger.info(f"   - Created {filtered_count} tables successfully")
            else:
                app.logger.info("   - No tables to create (all models have bind_key set)")
                
        except Exception as e:
            raise
    else:
        app.logger.error("   - CANNOT CREATE TABLES: Base or metadata is invalid")