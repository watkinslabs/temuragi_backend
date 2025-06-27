import json
from urllib.parse import quote_plus, urlparse

from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pg_id
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app.base.model import BaseModel
from app.config import config

encryption_key = config["DB_CONN_ENC_KEY"]

class Connection(BaseModel):
    __depends_on__ = ['DatabaseType']
    __tablename__ = 'connections'

    name = Column(String, unique=True, nullable=False)
    database_type_id = Column(
        pg_id(as_uuid=True),
        ForeignKey('database_types.id'),
        nullable=False
    )
    connection_string = Column(Text, nullable=False)
    username = Column(
        EncryptedType(String, encryption_key, AesEngine, 'pkcs5'),
        nullable=True
    )
    password = Column(
        EncryptedType(String, encryption_key, AesEngine, 'pkcs5'),
        nullable=True
    )
    options = Column(JSON, nullable=True)

    database_type = relationship('DatabaseType', backref='connections')

    def get_connection_string(self):
        conn_str = self.connection_string
        username = self.username
        password = self.password
        options = self.options or {}

        db_type_name = self.database_type.name.lower()

        if db_type_name == 'sqlite':
            if options and '?' not in conn_str:
                option_str = '&'.join(f"{k}={v}" for k, v in options.items())
                return f"{conn_str}?{option_str}"
            return conn_str

        if not username or not password:
            raise ValueError(
                f"Username and password required for {self.database_type.display} connections"
            )

        if '://' in conn_str:
            parsed = urlparse(conn_str)
            scheme = parsed.scheme
            netloc = parsed.netloc
            path = parsed.path
            query = parsed.query

            if '@' in netloc:
                netloc = netloc.split('@', 1)[1]

            new_conn = (
                f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@"
                f"{netloc}{path}"
            )

            if options:
                opts = '&'.join(f"{k}={v}" for k, v in options.items())
                new_conn += f"?{query}&{opts}" if query else f"?{opts}"
            elif query:
                new_conn += f"?{query}"

            return new_conn

        def _parse_params(s):
            delim = ';' if ';' in s and '=' in s else ' '
            parts = s.split(delim)
            params = {}
            for p in parts:
                if '=' in p:
                    k, v = p.split('=', 1)
                    params[k.strip()] = v.strip()
            return params

        params = _parse_params(conn_str)
        params['user'] = username

        if db_type_name == 'mysql':
            params['passwd'] = password
        elif db_type_name in ('postgres', 'postgresql'):
            params['password'] = password
        elif db_type_name == 'mssql':
            params['UID'] = username
            params['PWD'] = password
        elif db_type_name == 'oracle':
            params['password'] = password
        elif db_type_name == 'mongodb':
            params['password'] = password

        params.update(options)

        if db_type_name in ('mysql', 'postgres', 'postgresql', 'oracle'):
            sep = ' ' if db_type_name != 'oracle' else ';'
            return sep.join(f"{k}={v}" for k, v in params.items())

        if db_type_name == 'mssql':
            odbc_str = ';'.join(f"{k}={v}" for k, v in params.items())
            return f"mssql+pyodbc:///?odbc_connect={odbc_str}"

        if db_type_name == 'mongodb':
            return json.dumps(params)

        raise ValueError(f"Unsupported database type: {self.database_type.display}")