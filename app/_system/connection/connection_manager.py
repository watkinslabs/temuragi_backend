import uuid
import logging
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, create_engine, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from contextlib import contextmanager
from typing import Dict, Optional, Any
from urllib.parse import quote_plus, urlparse
import json
from ..report.connection_model import Connection

from urllib.parse import quote_plus, urlparse
import json

def parse_key_value_conn_string(conn_str):
    """Parse a key-value connection string into a dictionary

    Handles different formats like:
    - space-separated: "key1=value1 key2=value2"
    - semicolon-separated: "key1=value1;key2=value2"
    """
    params = {}

    if ';' in conn_str and '=' in conn_str:
        # Handle semicolon-separated
        pairs = conn_str.split(';')
    else:
        # Handle space-separated
        pairs = conn_str.split()

    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key.strip()] = value.strip()

    return params


class DBManager:
    __depends_on__=[]
    
    def __init__(self, session_factory: scoped_session):
        """
        session_factory: a SQLAlchemy scoped_session or sessionmaker
        bound to your configuration DB (where Connection records live).
        """
        self.session_factory = session_factory
        self.engines: Dict[str, Any] = {}
        self.sessionmakers: Dict[str, Any] = {}
        
        # Setup logger
        self.logger = logging.getLogger('db_manager')
        self.logger.info("DBManager initialized")
        self.logger.debug(f"Session factory type: {type(session_factory).__name__}")
        
        # Check if we received a session instance or factory
        self._is_session_instance = hasattr(session_factory, 'query')
        if self._is_session_instance:
            self.logger.warning("Received session instance instead of factory - will use it directly")

    def _get_session(self):
        """Get a session, handling both factory and instance cases"""
        if self._is_session_instance:
            # If we have a session instance, return it directly
            return self.session_factory
        else:
            # If we have a factory, create a new session
            return self.session_factory()

    def _mask_connection_string(self, conn_str):
        """Mask sensitive parts of connection string for logging"""
        if not conn_str:
            return "None"
        
        try:
            # URL format connection strings
            if '://' in conn_str and '@' in conn_str:
                parsed = urlparse(conn_str)
                if parsed.password:
                    # Replace password with asterisks
                    masked = conn_str.replace(f":{parsed.password}@", ":***@")
                    return masked
                return conn_str
            
            # Key-value format
            elif '=' in conn_str:
                params = parse_key_value_conn_string(conn_str)
                # Mask password-related fields
                for key in ['password', 'pwd', 'pass']:
                    if key in params:
                        params[key] = '***'
                # Reconstruct
                if ';' in conn_str:
                    return ';'.join([f"{k}={v}" for k, v in params.items()])
                else:
                    return ' '.join([f"{k}={v}" for k, v in params.items()])
            
            return conn_str
        except Exception as e:
            self.logger.warning(f"Failed to mask connection string: {e}")
            return "MASKED"
        
    def get_engine(self, connection_id: uuid.UUID) -> Any:
        """Get or create an Engine for the given Connection.id."""
        key = str(connection_id)
        
        # Check cache first
        if key in self.engines:
            self.logger.debug(f"Engine cache hit for connection_id: {key}")
            return self.engines[key]
        
        self.logger.info(f"Engine cache miss for connection_id: {key}, creating new engine")
        
        # Get a session (handles both factory and instance cases)
        if self._is_session_instance:
            sess = self.session_factory
            should_close = False  # Don't close if using shared instance
        else:
            sess = self.session_factory()
            should_close = True  # Close if we created it
        try:
            self.logger.debug(f"Querying for connection with UUID: {connection_id}")
            conn_record = (
                sess.query(Connection)
                    .filter_by(id=connection_id, is_active=True)
                    .first()
            )
            
            if not conn_record:
                self.logger.error(f"Active connection with ID {connection_id} not found")
                raise ValueError(f"Active connection with ID {connection_id} not found")
            
            self.logger.info(f"Found connection: {conn_record.name} (type: {conn_record.database_type.name})")
            
            conn_str = conn_record.get_connection_string()
            masked_conn_str = self._mask_connection_string(conn_str)
            self.logger.debug(f"Connection string: {masked_conn_str}")
            
            engine_opts = {}
            if conn_record.options:
                engine_opts = conn_record.options.get('engine_options', {})
                if engine_opts:
                    self.logger.debug(f"Engine options: {engine_opts}")
            
            self.logger.info(f"Creating SQLAlchemy engine for connection: {conn_record.name}")
            engine = create_engine(conn_str, **engine_opts)
            
            # Log engine dialect for debugging
            self.logger.debug(f"Engine dialect: {engine.dialect.name}")
            
            # Cache the engine
            self.engines[key] = engine
            self.logger.info(f"Engine created and cached for connection: {conn_record.name} ({key})")
            self.logger.debug(f"Total cached engines: {len(self.engines)}")
            
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to create engine for connection_id {connection_id}: {e}")
            raise
        finally:
            if should_close:
                sess.close()

    def get_session_maker(self, connection_id: uuid.UUID) -> sessionmaker:
        """Get or create a sessionmaker bound to the engine for connection_id."""
        key = str(connection_id)
        
        if key not in self.sessionmakers:
            self.logger.info(f"Creating new sessionmaker for connection_id: {key}")
            engine = self.get_engine(connection_id)
            self.sessionmakers[key] = sessionmaker(bind=engine)
            self.logger.debug(f"Sessionmaker created and cached. Total cached: {len(self.sessionmakers)}")
        else:
            self.logger.debug(f"Sessionmaker cache hit for connection_id: {key}")
            
        return self.sessionmakers[key]

    @contextmanager
    def session_scope(self, connection_id: uuid.UUID):
        """Provide a transactional scope for operations on the target DB."""
        self.logger.debug(f"Starting session scope for connection_id: {connection_id}")
        
        SessionLocal = self.get_session_maker(connection_id)
        session = SessionLocal()
        self.logger.debug(f"Session created for connection_id: {connection_id}")
        
        try:
            yield session
            session.commit()
            self.logger.debug(f"Session committed successfully for connection_id: {connection_id}")
        except Exception as e:
            self.logger.error(f"Session error for connection_id {connection_id}: {e}")
            session.rollback()
            self.logger.warning(f"Session rolled back for connection_id: {connection_id}")
            raise
        finally:
            session.close()
            self.logger.debug(f"Session closed for connection_id: {connection_id}")

    def get_main_connection_id(self) -> uuid.UUID:
        """Find the main UUID in Flask current_app or fallback to first is_active."""
        try:
            from flask import current_app
            
            main_id = current_app.config.get('MAIN_DB_CONNECTION_ID')
            if main_id:
                self.logger.info(f"Main connection ID from config: {main_id}")
                return uuid.UUID(main_id)
            else:
                self.logger.debug("No MAIN_DB_CONNECTION_ID in Flask config")
        except ImportError:
            self.logger.debug("Flask not available, skipping config check")
        except RuntimeError:
            self.logger.debug("No Flask application context, skipping config check")
        
        # Fallback to first active connection
        self.logger.warning("Falling back to first active connection as main")
        
        if self._is_session_instance:
            sess = self.session_factory
            should_close = False
        else:
            sess = self.session_factory()
            should_close = True
            
        try:
            first_conn = sess.query(Connection).filter_by(is_active=True).first()
            
            if not first_conn:
                self.logger.error("No active connections found in database")
                raise ValueError("No is_active connections found")
                
            self.logger.info(f"Using first active connection as main: {first_conn.name} ({first_conn.id})")
            return first_conn.id
        finally:
            if should_close:
                sess.close()

    def get_main_connection_engine(self) -> Any:
        """Get engine for the main connection"""
        self.logger.debug("Getting main connection engine")
        main_id = self.get_main_connection_id()
        return self.get_engine(main_id)

    @contextmanager
    def main_session_scope(self):
        """Transactional scope for the "main" connection."""
        self.logger.debug("Starting main session scope")
        main_id = self.get_main_connection_id()
        with self.session_scope(main_id) as session:
            yield session

    def invalidate_cache(self, connection_id: Optional[uuid.UUID] = None) -> None:
        """Clear cached engines and sessionmakers (all or one)."""
        if connection_id:
            key = str(connection_id)
            self.logger.info(f"Invalidating cache for connection_id: {key}")
            
            engine_removed = self.engines.pop(key, None)
            sessionmaker_removed = self.sessionmakers.pop(key, None)
            
            if engine_removed:
                self.logger.debug(f"Engine removed from cache for: {key}")
            if sessionmaker_removed:
                self.logger.debug(f"Sessionmaker removed from cache for: {key}")
                
            if not engine_removed and not sessionmaker_removed:
                self.logger.debug(f"No cached items found for connection_id: {key}")
        else:
            self.logger.warning("Invalidating all connection caches")
            engine_count = len(self.engines)
            sessionmaker_count = len(self.sessionmakers)
            
            self.engines.clear()
            self.sessionmakers.clear()
            
            self.logger.info(f"Cleared {engine_count} engines and {sessionmaker_count} sessionmakers from cache")

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        stats = {
            'cached_engines': len(self.engines),
            'cached_sessionmakers': len(self.sessionmakers),
            'engine_ids': list(self.engines.keys()),
            'sessionmaker_ids': list(self.sessionmakers.keys())
        }
        self.logger.debug(f"Cache stats: {stats}")
        return stats


def setup_connection_manager(session_factory: scoped_session) -> DBManager:
    """Factory helper—pass in your Flask app.Session."""
    logger = logging.getLogger('db_manager')
    logger.info("Setting up connection manager")
    return DBManager(session_factory)