import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import create_engine, text as sql_text
from sqlalchemy.engine import Engine, Connection, Result



class QueryMetadataError(Exception):
    """Custom exception for query metadata extraction errors."""
    __depends_on__=[]

        


class QueryMetadataExtractor:
    """
    Extracts column metadata from SQL queries without fetching data.
    Supports multiple database types with appropriate fallback mechanisms.
    """
    __depends_on__ = []

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Database-specific limit syntax mappings
        self.limit_syntax = {
            'postgresql': self._limit_syntax_standard,
            'mysql': self._limit_syntax_standard,
            'sqlite': self._limit_syntax_standard,
            'mssql': self._limit_syntax_mssql,
            'sqlserver': self._limit_syntax_mssql,
            'oracle': self._limit_syntax_oracle,
            'db2': self._limit_syntax_oracle,  # Same as Oracle
        }
        
        # Python to SQL type mappings per database
        self.type_mappings = {
            'postgresql': {
                'int': 'INTEGER',
                'float': 'DOUBLE PRECISION',
                'Decimal': 'NUMERIC',
                'str': 'VARCHAR',
                'bool': 'BOOLEAN',
                'datetime': 'TIMESTAMP',
                'date': 'DATE',
                'time': 'TIME',
                'bytes': 'BYTEA',
                'NoneType': 'NULL'
            },
            'mysql': {
                'int': 'INT',
                'float': 'DOUBLE',
                'Decimal': 'DECIMAL',
                'str': 'VARCHAR',
                'bool': 'TINYINT',
                'datetime': 'DATETIME',
                'date': 'DATE',
                'time': 'TIME',
                'bytes': 'BLOB',
                'NoneType': 'NULL'
            },
            'mssql': {
                'int': 'INT',
                'float': 'FLOAT',
                'Decimal': 'DECIMAL',
                'str': 'NVARCHAR',
                'bool': 'BIT',
                'datetime': 'DATETIME2',
                'date': 'DATE',
                'time': 'TIME',
                'bytes': 'VARBINARY',
                'NoneType': 'NULL'
            }
        }
    
    def extract_metadata(self, query: str, connection_string: str, 
                        db_type: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Main entry point for extracting query metadata.
        
        Args:
            query: SQL query to analyze
            connection_string: Database connection string
            db_type: Database type (postgresql, mysql, mssql, etc.)
            params: Query parameters if any
            
        Returns:
            List of column metadata dictionaries
        """
        self.logger.info(f"Extracting metadata for query on {db_type}")
        
        try:
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                # Try primary method: LIMIT 0 approach
                metadata = self._try_limit_zero_method(conn, query, db_type, params)
                
                if metadata:
                    return metadata
                
                # Fallback: Execute and fetch one row
                return self._try_fetch_one_method(conn, query, db_type, params)
                
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            raise QueryMetadataError(f"Failed to extract query metadata: {e}")
    
    def _try_limit_zero_method(self, conn: Connection, query: str, 
                              db_type: str, params: Optional[Dict]) -> Optional[List[Dict[str, Any]]]:
        """
        Try to extract metadata using LIMIT 0 or equivalent.
        """
        try:
            limited_query = self._apply_zero_limit(query, db_type)
            self.logger.debug(f"Attempting LIMIT 0 method with query: {limited_query[:100]}...")
            
            result = conn.execute(sql_text(limited_query), params or {})
            columns = self._extract_column_info(result)
            
            self.logger.info(f"Successfully extracted {len(columns)} columns using LIMIT 0 method")
            return columns
            
        except Exception as e:
            self.logger.warning(f"LIMIT 0 method failed: {e}")
            return None
    
    def _try_fetch_one_method(self, conn: Connection, query: str, 
                             db_type: str, params: Optional[Dict]) -> List[Dict[str, Any]]:
        """
        Fallback method: Execute query and fetch one row.
        """
        try:
            self.logger.debug("Attempting fetch one row method")
            
            result = conn.execute(sql_text(query), params or {})
            columns = self._extract_column_info(result)
            
            # Try to fetch one row for type enhancement
            try:
                row = result.fetchone()
                if row:
                    columns = self._enhance_with_row_data(columns, row, db_type)
            except:
                pass  # No rows is fine
            
            self.logger.info(f"Successfully extracted {len(columns)} columns using fetch one method")
            return columns
            
        except Exception as e:
            self.logger.error(f"Fetch one method failed: {e}")
            raise QueryMetadataError(f"Both metadata extraction methods failed: {e}")
    
    def _apply_zero_limit(self, query: str, db_type: str) -> str:
        """
        Apply database-specific syntax to limit query to 0 rows.
        """
        # Clean query
        query = query.rstrip().rstrip(';')
        
        # Get appropriate limit function
        limit_func = self.limit_syntax.get(db_type, self._limit_syntax_standard)
        return limit_func(query)
    
    def _limit_syntax_standard(self, query: str) -> str:
        """Standard LIMIT 0 syntax (PostgreSQL, MySQL, SQLite)"""
        return f"{query} LIMIT 0"
    
    def _limit_syntax_mssql(self, query: str) -> str:
        """SQL Server TOP 0 syntax"""
        query_upper = query.upper()
        
        # Check if query already has TOP
        if ' TOP ' in query_upper:
            # Replace existing TOP with TOP 0
            return re.sub(r'\bTOP\s+\d+\b', 'TOP 0', query, flags=re.IGNORECASE)
        else:
            # Insert TOP 0 after SELECT
            return re.sub(r'\bSELECT\b', 'SELECT TOP 0', query, count=1, flags=re.IGNORECASE)
    
    def _limit_syntax_oracle(self, query: str) -> str:
        """Oracle/DB2 FETCH FIRST syntax"""
        return f"{query} FETCH FIRST 0 ROWS ONLY"
    
    def _extract_column_info(self, result: Result) -> List[Dict[str, Any]]:
        """
        Extract column information from query result.
        """
        columns = []
        
        # Get cursor description
        cursor_description = None
        if hasattr(result, 'cursor') and hasattr(result.cursor, 'description'):
            cursor_description = result.cursor.description
        elif hasattr(result, '_cursor_description'):
            cursor_description = result._cursor_description()
        
        if not cursor_description:
            return columns
        
        for i, col_info in enumerate(cursor_description):
            # Standard cursor description format:
            # (name, type_code, display_size, internal_size, precision, scale, nullable)
            column = {
                'index': i,
                'name': col_info[0],
                'type_code': col_info[1] if len(col_info) > 1 else None,
                'display_size': col_info[2] if len(col_info) > 2 else None,
                'internal_size': col_info[3] if len(col_info) > 3 else None,
                'precision': col_info[4] if len(col_info) > 4 else None,
                'scale': col_info[5] if len(col_info) > 5 else None,
                'nullable': col_info[6] if len(col_info) > 6 else None,
                'python_type': None,
                'sql_type': None,
                'suggested_type': 'string'  # Default
            }
            
            columns.append(column)
        
        return columns
    
    def _enhance_with_row_data(self, columns: List[Dict[str, Any]], 
                              row: Any, db_type: str) -> List[Dict[str, Any]]:
        """
        Enhance column metadata using actual row data.
        """
        if not row or not columns:
            return columns
        
        # Convert row to accessible format
        row_data = self._row_to_list(row, len(columns))
        
        # Get type mapping for this database
        type_map = self.type_mappings.get(db_type, self.type_mappings['postgresql'])
        
        # Enhance each column
        for i, column in enumerate(columns):
            if i < len(row_data):
                value = row_data[i]
                python_type = type(value).__name__
                
                column['python_type'] = python_type
                column['sql_type'] = type_map.get(python_type, 'VARCHAR')
                column['suggested_type'] = self._suggest_generic_type(python_type, value)
        
        return columns
    
    def _row_to_list(self, row: Any, expected_length: int) -> List[Any]:
        """
        Convert various row formats to a list.
        """
        try:
            # Try different row formats
            if hasattr(row, '_mapping'):
                # SQLAlchemy Row with mapping
                return list(row._mapping.values())
            elif hasattr(row, '__iter__') and not isinstance(row, str):
                # Iterable (tuple, list)
                return list(row)
            elif hasattr(row, 'values'):
                # Dict-like
                return list(row.values())
            else:
                # Fallback
                return [row] * expected_length
        except:
            return []
    
    def _suggest_generic_type(self, python_type: str, value: Any) -> str:
        """
        Suggest a generic data type name based on Python type and value.
        These should map to common type names in your system.
        """
        if python_type == 'int':
            return 'integer'
        elif python_type == 'float':
            return 'float'
        elif python_type == 'Decimal':
            return 'decimal'
        elif python_type == 'bool':
            return 'boolean'
        elif python_type == 'datetime':
            return 'datetime'
        elif python_type == 'date':
            return 'date'
        elif python_type == 'time':
            return 'time'
        elif python_type == 'bytes':
            return 'binary'
        elif python_type == 'str':
            # Analyze string value
            if value is not None:
                if len(str(value)) > 255:
                    return 'text'
                elif self._looks_like_json(value):
                    return 'json'
                elif self._looks_like_id(value):
                    return 'id'
            return 'string'
        else:
            return 'string'  # Default
    
    def _looks_like_json(self, value: str) -> bool:
        """Check if string value looks like JSON."""
        if not isinstance(value, str):
            return False
        value = value.strip()
        return (value.startswith('{') and value.endswith('}')) or \
               (value.startswith('[') and value.endswith(']'))
    
    def _looks_like_id(self, value: str) -> bool:
        """Check if string value looks like UUID."""
        if not isinstance(value, str):
            return False
        id_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(id_pattern.match(value))
    
    def analyze_query_compatibility(self, query: str, db_type: str) -> Dict[str, Any]:
        """
        Analyze if a query is compatible with metadata extraction.
        """
        analysis = {
            'is_select': False,
            'has_limit': False,
            'has_offset': False,
            'is_complex': False,
            'warnings': []
        }
        
        query_upper = query.upper().strip()
        
        # Check if SELECT query
        analysis['is_select'] = query_upper.startswith('SELECT')
        
        if not analysis['is_select']:
            analysis['warnings'].append("Query is not a SELECT statement")
            return analysis
        
        # Check for existing LIMIT/TOP
        if db_type in ['postgresql', 'mysql', 'sqlite']:
            analysis['has_limit'] = ' LIMIT ' in query_upper
        elif db_type in ['mssql', 'sqlserver']:
            analysis['has_limit'] = ' TOP ' in query_upper
        elif db_type in ['oracle', 'db2']:
            analysis['has_limit'] = ' FETCH FIRST ' in query_upper
        
        # Check for OFFSET
        analysis['has_offset'] = ' OFFSET ' in query_upper
        
        # Check complexity
        complex_indicators = ['UNION', 'INTERSECT', 'EXCEPT', 'WITH']
        analysis['is_complex'] = any(indicator in query_upper for indicator in complex_indicators)
        
        if analysis['is_complex']:
            analysis['warnings'].append("Query contains complex operations that may affect metadata extraction")
        
        return analysis

