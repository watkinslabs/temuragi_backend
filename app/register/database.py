import threading
from flask import Flask, g
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from contextlib import contextmanager

from app.config import config


class RoutingSession(Session):
    """Custom session that routes queries to the correct engine based on model's __bind_key__"""

    def __init__(self, bind=None, **options):
        self._db_registry = options.pop('db_registry', None)
        self._default_bind = options.pop('default_bind', bind)
        super().__init__(bind=self._default_bind, **options)

    def get_bind(self, mapper=None, clause=None):
        """Return the engine for the given model based on its __bind_key__"""
        if mapper is not None:
            model_class = mapper.class_
            bind_key = getattr(model_class, '__bind_key__', None)

            if bind_key:
                engine = self._db_registry.get_or_create_engine(bind_key)
                if engine:
                    return engine

        return self._default_bind


class DynamicDatabaseRegistry:
    """Registry for dynamically created database engines based on stored connections"""

    def __init__(self):
        self.main_engine = None
        self._dynamic_engines = {}
        self._routing_session = None
        self._app = None
        self._lock = threading.RLock()  # Use RLock for reentrant locking

    def init_app(self, app: Flask):
        """Initialize the main database connection"""
        self._app = app

        main_uri = config.database.uri
        if not main_uri:
            raise ValueError("DATABASE_URI not configured")

        # Create main engine
        self.main_engine = create_engine(
            main_uri,
            pool_size=20,
            max_overflow=0,  # No overflow connections
            pool_pre_ping=True,
            pool_recycle=3600,
            isolation_level='READ COMMITTED'  # Prevent lock issues
        )

        # Create session factory WITHOUT routing first
        base_factory = sessionmaker(
            bind=self.main_engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        # Then wrap with routing
        def routing_factory():
            return RoutingSession(
                bind=self.main_engine,
                db_registry=self,
                default_bind=self.main_engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )

        # Create scoped session with proper thread locals
        self._routing_session = scoped_session(
            routing_factory,
            scopefunc=lambda: threading.current_thread().ident
        )

        return self._routing_session

    def get_session(self, bind_key=None):
        """Get a session for a specific database - returns session directly"""
        engine = self.get_or_create_engine(bind_key) if bind_key else self.main_engine
        if not engine:
            raise ValueError(f"No engine available for bind_key: {bind_key}")

        # Create a new session factory for this specific engine
        SessionLocal = sessionmaker(
            bind=engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        return SessionLocal()

    @contextmanager
    def session_scope(self, bind_key=None):
        """Get a session for a specific database using context manager"""
        session = self.get_session(bind_key)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create_engine(self, bind_key):
        """Get or create an engine for the given bind key"""
        if not bind_key:
            return self.main_engine

        # Check cache without lock first
        if bind_key in self._dynamic_engines:
            return self._dynamic_engines[bind_key]

        # Create engine with lock
        with self._lock:
            # Double-check
            if bind_key in self._dynamic_engines:
                return self._dynamic_engines[bind_key]

            try:
                # Query connection info using isolated session
                with self.session_scope() as session:
                    from app.models import Connection

                    connection = session.query(Connection).filter_by(name=bind_key).first()
                    if not connection:
                        self._app.logger.error(f"No connection found for bind_key: {bind_key}")
                        return None

                    connection_string = connection.get_connection_string()
                print(connection_string)
                # Create engine with appropriate settings
                engine_config = {
                    'pool_size': 10,
                    'max_overflow': 0,
                    'pool_pre_ping': True,
                    'pool_recycle': 3600,
                    'isolation_level': 'READ COMMITTED'
                }

                # Add database-specific settings
                if 'mssql' in connection_string.lower():
                    # For MSSQL, ensure proper connection string format
                    if 'TrustServerCertificate' not in connection_string:
                        connection_string += '&TrustServerCertificate=yes' if '?' in connection_string else '?TrustServerCertificate=yes'

                engine = create_engine(connection_string, **engine_config)

                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    conn.commit()

                # Cache it
                self._dynamic_engines[bind_key] = engine
                self._app.logger.info(f"Created engine for bind_key: {bind_key}")

                return engine

            except Exception as e:
                self._app.logger.error(f"Failed to create engine for {bind_key}: {e}")
                import traceback
                traceback.print_exc()
                return None

    def create_all_tables(self, base_model, app):
        """Create tables in main database only"""
        if not hasattr(base_model, 'metadata'):
            raise AttributeError("Base model must have metadata attribute")

        base_model.metadata.create_all(self.main_engine, checkfirst=True)


# Global registry
db_registry = DynamicDatabaseRegistry()


def register_db(app: Flask):
    """Initialize database with proper cleanup"""

    # Initialize the registry
    app.db_session = db_registry.init_app(app)

    # Add helper for context-managed sessions
    app.get_db_session = db_registry.session_scope

    @app.teardown_appcontext
    def cleanup(exc=None):
        """Clean up sessions after each request"""
        try:
            app.db_session.remove()
        except:
            pass  # Ignore cleanup errors


def get_engine_for_bind_key(bind_key=None):
    """Get engine for a specific bind key"""
    return db_registry.get_or_create_engine(bind_key)


def refresh_dynamic_engine(bind_key):
    """Force refresh a dynamic engine"""
    with db_registry._lock:
        if bind_key in db_registry._dynamic_engines:
            old_engine = db_registry._dynamic_engines[bind_key]
            old_engine.dispose()
            del db_registry._dynamic_engines[bind_key]

    return db_registry.get_or_create_engine(bind_key)


def create_all_tables(app, engine=None):
    """Create tables in main database"""
    from app.base.model import Base

    if Base and hasattr(Base, 'metadata'):
        # Only create tables without bind_key in main database
        from sqlalchemy import MetaData

        filtered_metadata = MetaData()

        for table_name, table in Base.metadata.tables.items():
            model_class = None

            # Find model for this table
            for mapper in Base.registry.mappers:
                if hasattr(mapper.class_, '__table__') and mapper.class_.__table__.name == table.name:
                    model_class = mapper.class_
                    break

            # Only include tables without bind_key
            if not model_class or not getattr(model_class, '__bind_key__', None):
                table.tometadata(filtered_metadata)

        filtered_metadata.create_all(engine or db_registry.main_engine, checkfirst=True)