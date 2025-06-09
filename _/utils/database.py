import pyodbc
from flask import g, current_app
from contextlib import contextmanager
from app.utils.dot_dict import DotDict
import re
import logging

def register_db(app):
    db = Database(app.logger,conn_str=app.config['CONNECTION_STRING'])
    app.db = db
    app.teardown_appcontext(db.close_connection)
        

class Database:
    """Database connection and query class for Flask applications"""

    def __init__(self, logger, conn_str=None, pool_size=5):
        """Initialize database with connection string and pool size"""
        self.conn_str = conn_str
        self.pool_size = pool_size
        self.pool = []  # Connection pool
        self.named_param_regex = re.compile(r':(\w+)')
        self.logger=logger
        self.logger.info(f"Database initialized")
        self.logger.debug(f"Connection pool size: {self.pool_size}")


    def get_connection(self):
        """Get a database connection from the pool or create a new one"""
        if 'db_conn' not in g:
            self.logger.debug("Creating new database connection")
            try:
                g.db_conn = pyodbc.connect(self.conn_str)
                self.logger.debug("Database connection established")
            except Exception as e:
                self.logger.error(f"Failed to establish database connection: {str(e)}")
                raise
        return g.db_conn

    def close_connection(self, exception=None):
        """Close database connection at the end of a request"""
        conn = g.pop('db_conn', None)
        if conn is not None:
            try:
                conn.close()
                self.logger.debug("Database connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing database connection: {str(e)}")

    def _process_query_params(self, query, params):
        """Process query to handle both ? and :param_name formats
        
        Returns:
            tuple: (modified_query, ordered_params)
        """
        import copy
        
        # If params is None or not a dict, use as-is with ? placeholders
        if params is None or not isinstance(params, dict):
            return query, copy.deepcopy(params)
            
        # Find all named parameters in the query
        named_params = self.named_param_regex.findall(query)
        
        if not named_params:
            # No named parameters found, use as-is
            return query, copy.deepcopy(params)
            
        # Replace named parameters with ? and build ordered parameter list
        ordered_params = []
        self.logger.debug(f"Processing named parameters: {named_params}")
        
        # Create a safe copy of each parameter to avoid modifying the original
        for param_name in named_params:
            if param_name not in params:
                error_msg = f"Named parameter :{param_name} not found in params dictionary"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Get the value and make a deep copy
            param_value = copy.deepcopy(params[param_name])
            ordered_params.append(param_value)
            
        # Replace :param_name with ? in the query
        modified_query = self.named_param_regex.sub('?', query)
        
        return modified_query, ordered_params

    @contextmanager
    def get_cursor(self, commit=False):
        """Context manager for cursor to ensure proper cleanup"""
        conn = self.get_connection()
        cursor = conn.cursor()
        self.logger.debug("Database cursor created")
        try:
            yield cursor
            if commit:
                conn.commit()
                self.logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error, transaction rolled back: {str(e)}")
            raise e
        finally:
            cursor.close()
            self.logger.debug("Database cursor closed")

    def execute(self, query, params=None, commit=True):
        """Execute a query that modifies data (INSERT, UPDATE, DELETE)"""
        self.logger.debug(f"Executing query: {query}")
        query, calc_params = self._process_query_params(query, params)

        # --------------------------------------------------------------------
        # ——— INSERT THESE LINES ———
        if calc_params:
            # inline each ? with repr(val)
            formatted = query
            for val in calc_params:
                formatted = formatted.replace('?', repr(val), 1)
            self.logger.debug(f"Executing query: {formatted}")
        else:
            self.logger.debug(f"Executing query: {query}")
        # ————————————————————————————————————————————————————————————————
                
        with self.get_cursor(commit=commit) as cursor:
            try:
                if params:
                    cursor.execute(query, calc_params)
                else:
                    cursor.execute(query)
                rowcount = cursor.rowcount
                #self.logger.info(f"Query executed successfully. Rows affected: {rowcount}")
                return rowcount
            except Exception as e:
                self.logger.error(f"Query execution failed: {str(e)}")
                raise

    def executemany(self, query, params_list, commit=True):
        """Execute multiple similar queries in batch"""
        # Note: For executemany, we assume params_list contains lists/tuples, not dicts
        # Named parameters aren't typically used with executemany
        self.logger.debug(f"Executing batch query: {query}")
        self.logger.debug(f"Batch size: {len(params_list)}")
        with self.get_cursor(commit=commit) as cursor:
            try:
                cursor.executemany(query, params_list)
                rowcount = cursor.rowcount
                self.logger.info(f"Batch query executed successfully. Rows affected: {rowcount}")
                return rowcount
            except Exception as e:
                self.logger.error(f"Batch query execution failed: {str(e)}")
                raise

    def fetch(self, query, params=None):
        """Fetch a single row result as a dot-accessible object"""
        self.logger.debug(f"Fetching single row: {query}")
        query, calc_params = self._process_query_params(query, params)
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(query, calc_params)
                else:
                    cursor.execute(query)
                
                # Get the result
                row = cursor.fetchone()
                
                # Return None if no results
                if not row:
                    self.logger.debug("No results found")
                    return None
                    
                # Convert row to dictionary then to dot-accessible object
                columns = [column[0] for column in cursor.description]
                #self.logger.debug("Single row fetched successfully")
                return DotDict(dict(zip(columns, row)))
            except Exception as e:
                self.logger.error(f"Error fetching all rows: {repr(e)}")
                self.logger.error(f"query: {str(query)}")
                if params:
                    self.logger.error(f"params: {' '.join(f'{k}={v}' for k, v in params.items())}")
                else:
                    self.logger.error("NO params")
                raise

    def fetch_all(self, query, params=None):
        """Fetch all results as list of dot-accessible objects"""
        self.logger.debug(f"Fetching all rows: {query}")
        query, calc_params = self._process_query_params(query, params)
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(query, calc_params)
                else:
                    cursor.execute(query)
                
                # Get column names from cursor description
                columns = [column[0] for column in cursor.description]
                
                # Convert rows to dot-accessible objects
                result = []
                for row in cursor.fetchall():
                    result.append(DotDict(dict(zip(columns, row))))
                
                #self.logger.debug(f"Fetched {len(result)} rows")
                return result
            except Exception as e:
                self.logger.error(f"Error fetching all rows: {str(e)}")
                self.logger.error(f"query: {repr(query)}")
                if params:
                    self.logger.error(f"params: {' '.join(f'{k}={v}' for k, v in params.items())}")
                else:
                    self.logger.error("NO params")
                raise
            
            
    def select(self, table, columns="*", where=None, params=None, order_by=None, limit=None):
        """Convenient method to build and execute a SELECT query"""
        query = f"SELECT {columns} FROM {table}"
        
        if where:
            query += f" WHERE {where}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
        
        self.logger.debug(f"Built SELECT query: {query}")
        query, calc_params = self._process_query_params(query, params)
        return self.fetch_all(query, calc_params)

    def insert(self, table, data, commit=True):
        """Insert a row into the table"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.logger.debug(f"Built INSERT query for table {table}")
        
        with self.get_cursor(commit=commit) as cursor:
            try:
                cursor.execute(query, list(data.values()))
                last_id = cursor.lastrowid
                self.logger.info(f"Row inserted into {table}. Last ID: {last_id}")
                return last_id
            except Exception as e:
                self.logger.error(f"Error inserting into {table}: {str(e)}")
                raise
    
    def update(self, table, data, where, params=None, commit=True):
        """Update rows in the table"""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        self.logger.debug(f"Built UPDATE query for table {table}")
        
        # Process the where clause for named parameters
        where_query, where_params = self._process_query_params(where, params)
        full_query = f"UPDATE {table} SET {set_clause} WHERE {where_query}"
        
        # Combine data values with where clause params
        all_params = list(data.values())
        if where_params:
            if isinstance(where_params, list):
                all_params.extend(where_params)
            else:
                all_params.append(where_params)
        
        try:
            rows_affected = self.execute(full_query, all_params, commit)
            self.logger.info(f"Updated {rows_affected} rows in table {table}")
            return rows_affected
        except Exception as e:
            self.logger.error(f"Error updating table {table}: {str(e)}")
            raise
    
    def delete(self, table, where, params=None, commit=True):
        """Delete rows from the table"""
        query = f"DELETE FROM {table} WHERE {where}"
        self.logger.debug(f"Built DELETE query for table {table}")
        
        query, calc_params = self._process_query_params(query, params)
        try:
            rows_affected = self.execute(query, calc_params, commit)
            self.logger.info(f"Deleted {rows_affected} rows from table {table}")
            return rows_affected
        except Exception as e:
            self.logger.error(f"Error deleting from table {table}: {str(e)}")
            raise
        
    def call_proc(self, proc_name, params=None):
        """Call a stored procedure"""
        self.logger.debug(f"Calling stored procedure: {proc_name}")
        # For stored procedures, we'll stick with positional parameters
        with self.get_cursor() as cursor:
            try:
                if params:
                    cursor.execute(f"{{CALL {proc_name}({','.join(['?'] * len(params))})}}",
                                params)
                else:
                    cursor.execute(f"{{CALL {proc_name}}}")
                
                # Try to fetch results if available
                try:
                    columns = [column[0] for column in cursor.description]
                    result = []
                    for row in cursor.fetchall():
                        result.append(dict(zip(columns, row)))
                    self.logger.debug(f"Stored procedure returned {len(result)} rows")
                    return result
                except:
                    self.logger.debug("Stored procedure executed successfully with no results")
                    return None
            except Exception as e:
                self.logger.error(f"Error calling stored procedure {proc_name}: {str(e)}")
                raise
