import uuid
import datetime
import json
from urllib.parse import quote_plus, urlparse
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app._system._core.base import BaseModel


class Connection(BaseModel):
    __depends_on__ = ['DatabaseType']  # Add this line if db_type is a FK
    __tablename__ = 'connections'

    name = Column(String, unique=True, nullable=False)
    db_type = Column(String, nullable=False)
    connection_string = Column(Text, nullable=False)
    credentials = Column(JSON, nullable=True)
    options = Column(JSON, nullable=True)


    def _parse_key_value_conn_string(self, conn_str):
        """Parse a key-value connection string into a dictionary"""
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

    def get_connection_string(self):
        """Build a complete connection string with credentials and options"""
        conn_str = self.connection_string
        # Get credentials from JSON field
        username = self.credentials.get('user') if self.credentials else None
        password = self.credentials.get('password') if self.credentials else None
        options = self.options or {}
        
        # SQLite doesn't need auth
        if self.db_type.lower() == 'sqlite':
            if options and '?' not in conn_str:
                option_str = '&'.join(f"{k}={v}" for k, v in options.items())
                return f"{conn_str}?{option_str}"
            return conn_str
        
        # All other DBs need auth
        if not username or not password:
            raise ValueError(f"Username and password required for {self.db_type} connections")
            
        # Handle URL-format connection strings
        if '://' in conn_str:
            parsed = urlparse(conn_str)
            scheme = parsed.scheme
            netloc = parsed.netloc
            path = parsed.path
            query = parsed.query
            
            # Extract host and port from netloc if present
            if '@' in netloc:
                netloc = netloc.split('@', 1)[1]
            
            # Build new connection with credentials
            new_conn = f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@{netloc}{path}"
            
            # Add options as query parameters if provided
            if options:
                if query:
                    # Merge with existing query params
                    new_conn += f"?{query}&{('&'.join(f'{k}={v}' for k, v in options.items()))}"
                else:
                    new_conn += f"?{('&'.join(f'{k}={v}' for k, v in options.items()))}"
            elif query:
                new_conn += f"?{query}"
                
            return new_conn
        
        # Handle other formats based on DB type
        db_type = self.db_type.lower()
        
        if db_type == 'postgres' or db_type == 'postgresql':
            params = self._parse_key_value_conn_string(conn_str)
            params['user'] = username
            params['password'] = password
            params.update(options)
            return ' '.join(f"{k}={v}" for k, v in params.items())
            
        elif db_type == 'mysql':
            params = self._parse_key_value_conn_string(conn_str)
            params['user'] = username
            params['passwd'] = password
            params.update(options)
            return ' '.join(f"{k}={v}" for k, v in params.items())
            
        elif db_type == 'mssql':
            params = self._parse_key_value_conn_string(conn_str)
            params['UID'] = username
            params['PWD'] = password
            params.update(options)

            conn_str=';'.join(f"{k}={v}" for k, v in params.items())
            connection_string = (
                "mssql+pyodbc:///?"
                "odbc_connect=" + conn_str
                )            

            return connection_string
            
        elif db_type == 'oracle':
            # Handle TNS names and easy connect formats
            if '/' in conn_str or '@' in conn_str:
                if '@' in conn_str:
                    conn_str = conn_str.split('@', 1)[1]
                return f"{username}/{password}@{conn_str}"
            else:
                params = self._parse_key_value_conn_string(conn_str)
                params['user'] = username
                params['password'] = password
                params.update(options)
                return ';'.join(f"{k}={v}" for k, v in params.items())
                
        elif db_type == 'mongodb':
            if '@' not in conn_str:
                params = self._parse_key_value_conn_string(conn_str)
                params['username'] = username
                params['password'] = password
                params.update(options)
                return json.dumps(params)
            
            # Else, handled by the URL case above
            
        else:
            raise ValueError(f"Unsupported database type: {db_type}")