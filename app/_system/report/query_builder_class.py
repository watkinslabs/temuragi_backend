import re
import json
from abc import ABC, abstractmethod
from sqlalchemy import text
from flask import session


class ReportQueryGenerator(ABC):
    """Abstract base class for report query generation"""
    __depends_on__ = []  


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
    
    def build_filter_conditions(self, columns, column_search, global_search):
        """Build WHERE conditions from search parameters"""
        conditions = []
        
        # Column-specific search
        if column_search:
            for col_idx, search_text in column_search.items():
                if search_text and search_text.strip():
                    col_name = columns[int(col_idx)] if col_idx.isdigit() else col_idx
                    conditions.append(f"{col_name} LIKE '%{search_text.strip()}%'")
        
        # Global search
        if global_search:
            global_conditions = []
            for col_name in columns:
                global_conditions.append(f"{col_name} LIKE '%{global_search}%'")
            if global_conditions:
                conditions.append(f"({' OR '.join(global_conditions)})")
        
        return conditions


class MSSQLQueryGenerator(ReportQueryGenerator):
    """Query generator for Microsoft SQL Server"""
    __depends_on__ = []  

    def get_row_number_syntax(self):
        return "ROW_NUMBER() OVER"
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build MSSQL paginated query using ROW_NUMBER()"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([f"[{col}]" for col in columns])
        
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


class PostgreSQLQueryGenerator(ReportQueryGenerator):
    """Query generator for PostgreSQL"""
    __depends_on__ = []  
    
    def get_row_number_syntax(self):
        return "ROW_NUMBER() OVER"
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build PostgreSQL paginated query using LIMIT/OFFSET"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([f'"{col}"' for col in columns])
        
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


class MySQLQueryGenerator(ReportQueryGenerator):
    """Query generator for MySQL"""
    __depends_on__ = []  

    def get_row_number_syntax(self):
        # MySQL 8.0+ supports ROW_NUMBER()
        return "ROW_NUMBER() OVER"
    
    def build_paginated_query(self, base_query, columns, filters, order_by, limit, offset):
        """Build MySQL paginated query using LIMIT/OFFSET"""
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        col_list = ', '.join([f"`{col}`" for col in columns])
        
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
        'mysql': MySQLQueryGenerator,
    }
    
    def __init__(self, db_type='postgresql'):
        """Initialize with specific database type"""
        generator_class = self.GENERATORS.get(db_type.lower())
        if not generator_class:
            raise ValueError(f"Unsupported database type: {db_type}")
        self.generator = generator_class()
        self.db_type = db_type.lower()
    
    def execute_report(self, db_session, report, request_data):
        """Execute a report with the given parameters"""
        # Extract parameters from request
        draw = int(request_data.get('draw', 1))
        start = int(request_data.get('start', 0))
        length = int(request_data.get('length', 10))
        search_value = request_data.get('search[value]', '')
        
        # Extract column ordering
        order_column_idx = request_data.get('order[0][column]')
        order_dir = request_data.get('order[0][dir]', 'asc').upper()
        
        # Extract column information
        columns_data = {}
        column_search = {}
        
        for key in request_data:
            if key.startswith('columns[') and key.endswith('][data]'):
                idx = key[8:key.find(']')]
                columns_data[idx] = request_data[key]
                
                search_key = f'columns[{idx}][search][value]'
                if search_key in request_data and request_data[search_key]:
                    column_search[idx] = request_data[search_key]
        
        # Extract variables
        vars_form = {}
        for key in request_data:
            if key.startswith('vars['):
                var_name = key[5:-1]
                vars_form[var_name] = request_data[key]
        
        # Get column names from report
        column_names = [col.get('name') for col in report.columns if col.get('name')]
        
        # Build ORDER BY clause
        order_by = ""
        if order_column_idx is not None and column_names:
            order_column = columns_data.get(order_column_idx, column_names[0])
            if self.db_type == 'mssql':
                order_by = f"ORDER BY [{order_column}] {order_dir}"
            elif self.db_type == 'postgresql':
                order_by = f'ORDER BY "{order_column}" {order_dir}'
            else:  # mysql
                order_by = f"ORDER BY `{order_column}` {order_dir}"
        
        # Process base query
        base_query = report.query.strip().rstrip(';')
        base_query = self.generator.process_variables(base_query, vars_form)
        
        # Build filter conditions
        filters = self.generator.build_filter_conditions(
            column_names, column_search, search_value
        )
        
        try:
            # Build and execute paginated query
            paginated_query = self.generator.build_paginated_query(
                base_query, column_names, filters, order_by, length, start
            )
            
            results = db_session.execute(text(paginated_query), vars_form).fetchall()
            
            # Convert results to list of dicts
            data_rows = []
            for row in results:
                data_rows.append(dict(row._mapping))
            
            # Get total count
            count_query = self.generator.build_count_query(base_query)
            count_result = db_session.execute(text(count_query), vars_form).fetchone()
            total_rows = count_result.count if count_result else 0
            
            # Get filtered count
            filtered_count = total_rows
            if filters:
                filtered_query = self.generator.build_count_query(base_query, filters)
                filtered_result = db_session.execute(text(filtered_query), vars_form).fetchone()
                filtered_count = filtered_result.count if filtered_result else 0
            
            return {
                "draw": draw,
                "recordsTotal": total_rows,
                "recordsFiltered": filtered_count,
                "data": data_rows,
                "headers": column_names
            }
            
        except Exception as e:
            return {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": str(e)
            }
    
    def test_query(self, db_session, query, params=None):
        """Test a query and return column information"""
        try:
            # Execute query with LIMIT 1 to get column info
            if self.db_type == 'mssql':
                test_query = f"SELECT TOP 1 * FROM ({query}) AS test"
            else:
                test_query = f"SELECT * FROM ({query}) AS test LIMIT 1"
            
            result = db_session.execute(text(test_query), params or {}).first()
            
            columns = []
            if result:
                for column_name in result._mapping.keys():
                    columns.append({
                        'name': column_name,
                        'display': column_name,
                        'type': 'text',
                        'desc': ''
                    })
            
            return columns
        except Exception as e:
            raise Exception(f"Query test failed: {str(e)}")

