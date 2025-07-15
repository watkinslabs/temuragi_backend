from abc import ABC, abstractmethod
from sqlalchemy import text

from app.register.database import db_registry 

from abc import ABC, abstractmethod
from sqlalchemy import text

from app.register.database import db_registry 

class ReportQueryGenerator(ABC):
    """Abstract base class for report query generation"""
    __depends_on__ = []  
    def __init__(self):
        self.db_session = db_registry._routing_session()

    @abstractmethod
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build a paginated query with filters and ordering"""
        pass
    
    @abstractmethod
    def build_count_query(self, base_query, filters=None):
        """Build a count query"""
        pass
    
    @abstractmethod
    def get_row_number_syntax(self):
        """Get the row number syntax for the database"""
        pass
    
    def process_variables(self, query, variables):
        """Replace variable placeholders in the query"""
        processed_query = query
        for name, value in variables.items():
            placeholder = f"{{{name}}}"
            processed_query = processed_query.replace(placeholder, str(value))
        return processed_query
    
    def build_filter_conditions(self, columns, column_search, global_search, report=None):
        """Build WHERE conditions from search parameters"""
        conditions = []
        
        # Get column metadata if report is provided
        column_types = {}
        if report and hasattr(report, 'columns'):
            for col in report.columns:
                if col.data_type:
                    column_types[col.name] = col.data_type.name.lower()
        
        # Column-specific search
        if column_search:
            for col_idx, search_text in column_search.items():
                if search_text and search_text.strip():
                    col_name = columns[int(col_idx)] if col_idx.isdigit() else col_idx
                    condition = self._build_column_condition(col_name, search_text.strip(), column_types.get(col_name))
                    if condition:
                        conditions.append(condition)
        
        # Global search - only on searchable columns
        if global_search and report:
            global_conditions = []
            for col in report.columns:
                # Only search on searchable text-like columns
                if col.is_searchable and col.data_type and col.data_type.name.lower() in ['string', 'text', 'varchar', 'char']:
                    condition = self._build_column_condition(col.name, global_search, col.data_type.name.lower())
                    if condition:
                        global_conditions.append(condition)
            
            if global_conditions:
                conditions.append(f"({' OR '.join(global_conditions)})")
        elif global_search and not report:
            # Fallback: if no report metadata, only search on columns that are likely text
            global_conditions = []
            for col_name in columns:
                # Skip columns that are likely not text based on common naming patterns
                if not any(pattern in col_name.lower() for pattern in ['_id', '_at', 'is_', 'has_', 'version', 'count', 'amount', 'price']):
                    global_conditions.append(f"{self._quote_identifier(col_name)} LIKE '%{self._escape_sql_string(global_search)}%'")
            
            if global_conditions:
                conditions.append(f"({' OR '.join(global_conditions)})")
        
        return conditions
    
    def _build_column_condition(self, col_name, search_value, data_type=None):
        """Build appropriate filter condition based on column data type"""
        escaped_value = self._escape_sql_string(search_value)
        quoted_col = self._quote_identifier(col_name)
        
        # Handle different data types
        if data_type:
            if data_type in ['string', 'text', 'varchar', 'char']:
                return f"{quoted_col} ILIKE '%{escaped_value}%'"
            elif data_type in ['integer', 'bigint', 'smallint', 'numeric', 'decimal', 'float', 'double']:
                # For numeric types, only filter if search value is numeric
                try:
                    float(search_value)
                    return f"{quoted_col}::text LIKE '%{escaped_value}%'"
                except ValueError:
                    return None
            elif data_type in ['boolean', 'bool']:
                # For boolean, check for true/false variations
                lower_val = search_value.lower()
                if lower_val in ['true', '1', 'yes', 'y', 't']:
                    return f"{quoted_col} = true"
                elif lower_val in ['false', '0', 'no', 'n', 'f']:
                    return f"{quoted_col} = false"
                return None
            elif data_type in ['date', 'datetime', 'timestamp']:
                # Cast to text for date/time searching
                return f"{quoted_col}::text ILIKE '%{escaped_value}%'"
            elif data_type in ['uuid', 'id']:
                # For UUIDs, exact match or cast to text
                return f"{quoted_col}::text ILIKE '%{escaped_value}%'"
            elif data_type in ['json', 'jsonb']:
                # For JSON fields, cast to text
                return f"{quoted_col}::text ILIKE '%{escaped_value}%'"
            else:
                # Unknown type, try text casting
                return f"{quoted_col}::text ILIKE '%{escaped_value}%'"
        else:
            # No type info, use LIKE
            return f"{quoted_col} LIKE '%{escaped_value}%'"
    
    def _escape_sql_string(self, value):
        """Escape SQL string to prevent injection"""
        if value is None:
            return ''
        # Escape single quotes
        return str(value).replace("'", "''").replace("%", "\\%").replace("_", "\\_")
    
    @abstractmethod
    def _quote_identifier(self, identifier):
        """Quote identifier based on database type"""
        pass


class PostgreSQLQueryGenerator(ReportQueryGenerator):
    """Query generator for PostgreSQL"""
    __depends_on__ = []  
    
    def get_row_number_syntax(self):
        return "ROW_NUMBER() OVER"
    
    def _quote_identifier(self, identifier):
        """Quote identifier for PostgreSQL"""
        return f'"{identifier}"'
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build PostgreSQL paginated query using LIMIT/OFFSET"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([self._quote_identifier(col) for col in columns])
        
        # PostgreSQL can use simpler LIMIT/OFFSET syntax
        query = f"""
        SELECT {col_list}
        FROM ({base_query}) AS base_data
        {where_clause}
        {order_by}
        LIMIT {limit} OFFSET {offset}
        """
        return query
    
    def build_count_query(self, base_query, filters=None):
        """Build PostgreSQL count query"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        return f"SELECT COUNT(*) as count FROM ({base_query}) AS counted {where_clause}"


class MSSQLQueryGenerator(ReportQueryGenerator):
    """Query generator for Microsoft SQL Server"""
    __depends_on__ = []  

    def get_row_number_syntax(self):
        return "ROW_NUMBER() OVER"
    
    def _quote_identifier(self, identifier):
        """Quote identifier for SQL Server"""
        return f'[{identifier}]'
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build MSSQL paginated query using ROW_NUMBER()"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([self._quote_identifier(col) for col in columns])
        
        query = f"""
        SELECT {col_list}
        FROM (
            SELECT ROW_NUMBER() OVER ({order_by}) AS RowNo, *
            FROM (
                SELECT *
                FROM ({base_query}) AS INTERNAL
            ) AS WRAPPEDROWS
            {where_clause}
        ) AS PAGINATED
        WHERE RowNo > {offset} AND RowNo <= {offset + limit}
        """
        return query
    
    def build_count_query(self, base_query, filters=None):
        """Build MSSQL count query"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        return f"SELECT COUNT(*) as count FROM ({base_query}) AS counted {where_clause}"


class MySQLQueryGenerator(ReportQueryGenerator):
    """Query generator for MySQL"""
    __depends_on__ = []  

    def get_row_number_syntax(self):
        # MySQL 8.0+ supports ROW_NUMBER()
        return "ROW_NUMBER() OVER"
    
    def _quote_identifier(self, identifier):
        """Quote identifier for MySQL"""
        return f'`{identifier}`'
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build MySQL paginated query using LIMIT/OFFSET"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([self._quote_identifier(col) for col in columns])
        
        query = f"""
        SELECT {col_list}
        FROM ({base_query}) AS base_data
        {where_clause}
        {order_by}
        LIMIT {limit} OFFSET {offset}
        """
        return query
    
    def build_count_query(self, base_query, filters=None):
        """Build MySQL count query"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        return f"SELECT COUNT(*) as count FROM ({base_query}) AS counted {where_clause}"

class ReportQueryExecutor:
    """Main class for executing report queries across different database types"""
    __depends_on__ = ['MSSQLQueryGenerator',
                      'PostgreSQLQueryGenerator',
                      'MySQLQueryGenerator']
    
    GENERATORS = {
        'mssql': MSSQLQueryGenerator,
        'postgresql': PostgreSQLQueryGenerator,
        'postgres': PostgreSQLQueryGenerator,
        'mysql': MySQLQueryGenerator,
    }
    
    def __init__(self, db_type='postgresql'):
        """Initialize with specific database type"""
        generator_class = self.GENERATORS.get(db_type.lower())
        if not generator_class:
            raise ValueError(f"Unsupported database type: {db_type}")
        self.generator = generator_class()
        self.db_type = db_type.lower()
        self.db_session=None
    
    def execute_report(self, report, request_data):
        """Execute a report with the given parameters"""
        # Extract parameters from request
        draw = int(request_data.get('draw', 1))
        start = int(request_data.get('start', 0))
        length = int(request_data.get('length', 10))
        
        # Handle search - support both formats
        search_value = request_data.get('search', '')
        if isinstance(search_value, dict):
            search_value = search_value.get('value', '')
        
        # Extract column ordering - support both old and new formats
        order_data = request_data.get('order', [])
        order_column_idx = None
        order_dir = 'asc'
        
        # New format: order as array
        if isinstance(order_data, list) and len(order_data) > 0:
            order_column_idx = order_data[0].get('column')
            order_dir = order_data[0].get('dir', 'asc').upper()
        else:
            # Old format: order[0][column]
            order_column_idx = request_data.get('order[0][column]')
            order_dir = request_data.get('order[0][dir]', 'asc').upper()
        
        # Get return columns if specified
        return_columns = request_data.get('return_columns', [])
        
        # Extract column information
        columns_data = {}
        column_search = {}
        
        # Support new format with columns array
        columns = request_data.get('columns', [])
        if isinstance(columns, list):
            for idx, col_data in enumerate(columns):
                if isinstance(col_data, dict):
                    columns_data[str(idx)] = col_data.get('data', col_data.get('name', ''))
                    search_val = col_data.get('search', {})
                    if isinstance(search_val, dict) and search_val.get('value'):
                        column_search[str(idx)] = search_val['value']
        else:
            # Old format: columns[0][data]
            for key in request_data:
                if key.startswith('columns[') and key.endswith('][data]'):
                    idx = key[8:key.find(']')]
                    columns_data[idx] = request_data[key]
                    
                    search_key = f'columns[{idx}][search][value]'
                    if search_key in request_data and request_data[search_key]:
                        column_search[idx] = request_data[search_key]
        
        # Extract variables
        vars_form = request_data.get('vars', {})
        if not isinstance(vars_form, dict):
            # Old format: vars[name]
            vars_form = {}
            for key in request_data:
                if key.startswith('vars['):
                    var_name = key[5:-1]
                    vars_form[var_name] = request_data[key]
        
        # Get column names from report
        column_names = [col.name for col in report.columns if col.name]
        
        # Build ORDER BY clause
        order_by = ""
        order_column = None
        
        if order_column_idx is not None:
            # Use return_columns if provided, otherwise use columns_data or column_names
            if return_columns and 0 <= int(order_column_idx) < len(return_columns):
                order_column = return_columns[int(order_column_idx)]
            elif str(order_column_idx) in columns_data:
                order_column = columns_data[str(order_column_idx)]
            elif 0 <= int(order_column_idx) < len(column_names):
                order_column = column_names[int(order_column_idx)]
        
        if not order_column:
            # No explicit order specified - find default sort column
            default_sort_column = None
            for col in report.columns:
                if col.name and hasattr(col, 'is_default_sort') and col.is_default_sort:
                    default_sort_column = col.name
                    break
            
            # Use default sort column if found, otherwise first column
            order_column = default_sort_column if default_sort_column else column_names[0] if column_names else None
            order_dir = 'ASC'  # Default direction when no order specified
        
        # Always build ORDER BY since ROW_NUMBER() requires it
        if order_column:
            if self.db_type == 'mssql':
                order_by = f"ORDER BY [{order_column}] {order_dir}"
            elif self.db_type in ('postgresql', 'postgres'):
                order_by = f'ORDER BY "{order_column}" {order_dir}'
            else:  # mysql
                order_by = f"ORDER BY `{order_column}` {order_dir}"
        
        # Process base query
        base_query = report.query.strip().rstrip(';')
        base_query = self.generator.process_variables(base_query, vars_form)
        
        # Get searchable columns from request or use report metadata
        searchable_columns = request_data.get('searchable_columns', [])
        
        # If searchable_columns provided, use only those for global search
        if searchable_columns and search_value:
            # Filter column_names to only searchable ones
            search_column_names = [col for col in column_names if col in searchable_columns]
        else:
            search_column_names = column_names
        
        # Build filter conditions - pass report for column type information
        filters = self.generator.build_filter_conditions(
            search_column_names, column_search, search_value, report
        )
        
        try:
            # Build and execute paginated query
            paginated_query = self.generator.build_paginated_query(
                base_query, column_names, filters, order_by, length, start
            )
            
            engine = db_registry.get_or_create_engine(report.connection.name)
            if engine:
                with engine.connect() as conn:
                    results = conn.execute(text(paginated_query), vars_form).fetchall()
                    
                    # Convert results to list of dicts
                    data_rows = []
                    for row in results:
                        # If return_columns specified, return only those columns in order
                        if return_columns:
                            row_data = {}
                            row_mapping = dict(row._mapping)
                            
                            # Always include PK/identity columns for row actions
                            if report and hasattr(report, 'columns'):
                                for col in report.columns:
                                    if (col.is_pk or col.is_identity) and col.name in row_mapping:
                                        # Add PK/identity columns even if not in return_columns
                                        if col.name not in return_columns:
                                            row_data[col.name] = row_mapping[col.name]
                            
                            # Add requested columns
                            for col in return_columns:
                                row_data[col] = row_mapping.get(col)
                            
                            data_rows.append(row_data)
                        else:
                            data_rows.append(dict(row._mapping))
                    
                    # Get total count
                    count_query = self.generator.build_count_query(base_query)
                    count_result = conn.execute(text(count_query), vars_form).fetchone()
                    total_rows = count_result.count if count_result else 0
                    
                    # Get filtered count
                    filtered_count = total_rows
                    if filters:
                        filtered_query = self.generator.build_count_query(base_query, filters)
                        filtered_result = conn.execute(text(filtered_query), vars_form).fetchone()
                        filtered_count = filtered_result.count if filtered_result else 0
                    
                    return {
                        "success": True,
                        "draw": draw,
                        "recordsTotal": total_rows,
                        "recordsFiltered": filtered_count,
                        "data": data_rows,
                        "headers": return_columns if return_columns else column_names
                    }
        
        except Exception as e:
            return {
                "success": False,
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": str(e)
            }
        
    def test_query(self, query, params=None):
        """Test a query and return column information"""
        try:
            # Execute query with LIMIT 1 to get column info
            if self.db_type == 'mssql':
                test_query = f"SELECT TOP 1 * FROM ({query}) AS test"
            else:
                test_query = f"SELECT * FROM ({query}) AS test LIMIT 1"
            
            result = self.db_session.execute(text(test_query), params or {}).first()
            
            columns = []
            if result:
                for column_name in result._mapping.keys():
                    columns.append({
                        'name': column_name,
                        'label': column_name,
                        'type': 'text',
                        'desc': ''
                    })
            
            return columns
        except Exception as e:
            raise Exception(f"Query test failed: {str(e)}")






