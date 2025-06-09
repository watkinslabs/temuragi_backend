import uuid
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from contextlib import contextmanager
from typing import Dict, Optional, Any
from urllib.parse import quote_plus, urlparse
import json
from .connection_model import Connection 

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
    def __init__(self, session_factory: scoped_session):
        """
        session_factory: a SQLAlchemy scoped_session or sessionmaker
        bound to your configuration DB (where Connection records live).
        """
        self.session_factory = session_factory
        self.engines: Dict[str, Any] = {}
        self.sessionmakers: Dict[str, Any] = {}

    def get_engine(self, connection_id: uuid.UUID) -> Any:
        """Get or create an Engine for the given Connection.uuid."""
        key = str(connection_id)
        if key in self.engines:
            return self.engines[key]

        # open a fresh session to load the Connection row
        sess = self.session_factory()
        conn_record = (
            sess.query(Connection)
                .filter_by(uuid=connection_id, active=True)
                .first()
        )
        sess.close()

        if not conn_record:
            raise ValueError(f"Active connection with ID {connection_id} not found")

        conn_str = conn_record.get_connection_string()
        engine_opts = {}
        if conn_record.options:
            engine_opts = conn_record.options.get('engine_options', {})

        engine = create_engine(conn_str, **engine_opts)
        self.engines[key] = engine
        return engine

    def get_session_maker(self, connection_id: uuid.UUID) -> sessionmaker:
        """Get or create a sessionmaker bound to the engine for connection_id."""
        key = str(connection_id)
        if key not in self.sessionmakers:
            engine = self.get_engine(connection_id)
            self.sessionmakers[key] = sessionmaker(bind=engine)
        return self.sessionmakers[key]

    @contextmanager
    def session_scope(self, connection_id: uuid.UUID):
        """Provide a transactional scope for operations on the target DB."""
        SessionLocal = self.get_session_maker(connection_id)
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_main_connection_id(self) -> uuid.UUID:
        """Find the main UUID in Flask current_app or fallback to first active."""
        from flask import current_app

        main_id = current_app.config.get('MAIN_DB_CONNECTION_ID')
        if main_id:
            return uuid.UUID(main_id)

        sess = self.session_factory()
        first_conn = sess.query(Connection).filter_by(active=True).first()
        sess.close()
        if not first_conn:
            raise ValueError("No active connections found")
        return first_conn.uuid

    def get_main_connection_engine(self) -> Any:
        return self.get_engine(self.get_main_connection_id())

    @contextmanager
    def main_session_scope(self):
        """Transactional scope for the “main” connection."""
        with self.session_scope(self.get_main_connection_id()) as session:
            yield session

    def invalidate_cache(self, connection_id: Optional[uuid.UUID] = None) -> None:
        """Clear cached engines and sessionmakers (all or one)."""
        if connection_id:
            key = str(connection_id)
            self.engines.pop(key, None)
            self.sessionmakers.pop(key, None)
        else:
            self.engines.clear()
            self.sessionmakers.clear()


def setup_connection_manager(session_factory: scoped_session) -> DBManager:
    """Factory helper—pass in your Flask app.Session."""
    return DBManager(session_factory)
