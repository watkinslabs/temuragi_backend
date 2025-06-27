#!/usr/bin/env python3
"""
Automated MSSQL table scanner and SQLAlchemy model generator
"""
from datetime import datetime
import os
import sys
import pyodbc
from pathlib import Path
import logging
import time
import re
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see more details
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sanitize_identifier(name: str, prefix_for_numeric: str = '_', is_table_name: bool = False) -> str:
    """
    Sanitize table/column names to be valid Python identifiers
    
    Args:
        name: The original table or column name
        prefix_for_numeric: Prefix to add if name starts with number
        is_table_name: True if sanitizing a table name (for PascalCase conversion)
    
    Returns:
        Sanitized name safe for use as Python identifier
    """
    # Python reserved keywords
    reserved_words = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield', 'type', 'match', 'case'
    }
    
    # First, handle empty names
    if not name:
        return prefix_for_numeric + 'unnamed'
    
    # Replace all special characters with underscores
    # This includes: brackets, spaces, hyphens, parentheses, dollar signs, 
    # periods, forward/back slashes, at signs, hash, percent, ampersand, 
    # asterisk, plus, equals, pipes, colons, semicolons, quotes, etc.
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Replace multiple consecutive underscores with single underscore
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    
    # Handle empty result after sanitization
    if not safe_name:
        safe_name = prefix_for_numeric + 'unnamed'
    
    # Handle names that start with numbers
    if safe_name[0].isdigit():
        safe_name = prefix_for_numeric + safe_name
    
    # Handle reserved words
    if safe_name.lower() in reserved_words:
        safe_name = safe_name + '_'
    
    # For table names, convert to PascalCase
    if is_table_name:
        # Split by underscores and capitalize each part
        parts = safe_name.split('_')
        safe_name = ''.join(word.capitalize() for word in parts if word)
        
        # Re-check if it starts with number after PascalCase conversion
        if safe_name and safe_name[0].isdigit():
            safe_name = prefix_for_numeric + safe_name
            
        # Re-check reserved words for PascalCase
        if safe_name in reserved_words:
            safe_name = safe_name + '_'
    
    return safe_name


def main():
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate SQLAlchemy models from MSSQL database')
    parser.add_argument('-d', '--database', nargs='+', help='Database name(s) to process', required=True)
    parser.add_argument('-t', '--table', help='Specific table name to process (optional)')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-c', '--connection', help='Connection string (DSN=TEST_DNS;UID=USER;PWD=PASSWORD)')
    parser.add_argument('-p', '--prefix', default='_', help='Prefix for tables/columns starting with numbers (default: _)')
    parser.add_argument('-b', '--bind-key',  help='Virtual Database Connection to bind tables to (default: dev)',default='dev')
    
    args = parser.parse_args()
    
    # Strip schema prefix from table name if provided
    table_name = args.table
    
    if table_name and '.' in table_name:
        parts = table_name.split('.')
        table_name = parts[-1]  # Get just the table name
    
    # Determine output mode
    if args.output and args.output.endswith('.py'):
        # Single file output mode
        output_dir = None
        output_file = args.output
    else:
        # Directory mode
        output_dir = args.output or 'app/user/databases/'
        output_file = None
    
    # Create generator
    if output_dir:
        generator = mssql_model_generator(args.connection, output_dir, numeric_table_prefix=args.prefix,bind_key=args.bind_key)
    else:
        generator = mssql_model_generator(args.connection, '.', numeric_table_prefix=args.prefix,bind_key=args.bind_key)
    
    logger.info(f"Database(s): {args.database}")
    if table_name:
        logger.info(f"Specific table: {table_name}")
    if output_file:
        logger.info(f"Output file: {output_file}")
    else:
        logger.info(f"Output directory: {generator.output_dir}")
    
    try:
        # Connect to database
        generator.connect()
        
        # If specific table is requested, process just that table
        if table_name:
            # Process just the one table
            database_name = args.database[0]  # Use first database
            
            logger.info(f"Processing table {table_name} in database {database_name}")
            
            # Switch to the database
            generator.switch_database(database_name)
            
            # Get DDL for specific table
            ddl = generator.get_table_ddl(table_name)
            
            # Generate model programmatically
            model_code = generator.generate_model_programmatically(table_name, ddl, database_name)
            
            # Save model
            if output_file:
                # Save to specific file
                with open(output_file, 'w') as f:
                    f.write(model_code)
                logger.info(f"Saved model to {output_file}")
            else:
                # Save to directory structure
                generator.save_model(database_name, "dbo", table_name, model_code)
        else:
            # Process all tables in database(s)
            generator.process_database(args.database)
        
    finally:
        # Always disconnect
        generator.disconnect()

class mssql_model_generator:
    def __init__(self, connection_string: str, output_dir: str = "generated_models",numeric_table_prefix='_',bind_key='dev'):
        self.connection_string = connection_string
        self.output_dir = Path(output_dir)
        self.connection = None
        self.numeric_table_prefix = numeric_table_prefix
        self.bind_key=bind_key
        self.header="""import re
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Time, Date, Text, 
    func, ForeignKey, Index, UniqueConstraint, Numeric, Float, 
    LargeBinary, Table, MetaData
)
from sqlalchemy.orm import relationship, validates, backref


from app.base.model import Base

"""
        
    def connect(self):
        """Establish connection to MSSQL database"""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            logger.info("Connected to MSSQL database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")
            
    def get_database_name(self) -> str:
        """Extract database name from current connection"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        cursor.close()
        return db_name
        
    def get_tables(self) -> List[str]:
        """Get all user tables from dbo schema"""
        cursor = self.connection.cursor()
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME NOT LIKE 'sys%'
        AND TABLE_NAME NOT LIKE 'MS%'
        AND TABLE_NAME NOT LIKE '#%'
        ORDER BY TABLE_NAME
        """
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        logger.info(f"Found {len(tables)} tables in dbo schema")
        return tables
        
    def test_indexes(self, table_name: str):
        """Test method to debug index fetching"""
        cursor = self.connection.cursor()
        
        # Try a simple index query
        test_query = """
        SELECT 
            i.name AS index_name,
            i.is_unique,
            i.type_desc
        FROM sys.indexes i
        WHERE i.object_id = OBJECT_ID(?)
        AND i.is_primary_key = 0
        AND i.type > 0
        """
        
        try:
            cursor.execute(test_query, f'dbo.{table_name}')
            results = cursor.fetchall()
            logger.info(f"Index query results for {table_name}: {results}")
        except Exception as e:
            logger.error(f"Error in index query: {e}")
            
        cursor.close()
        
    def get_table_ddl(self, table_name: str) -> str:
        """Generate DDL for a specific table - simplified for SQL Server 2008 R2 compatibility"""
        cursor = self.connection.cursor()
        
        # Get column information including IDENTITY check
        column_query = """
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            CASE 
                WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES'
                ELSE 'NO'
            END AS IS_PRIMARY_KEY,
            COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME, 'IsIdentity') AS IS_IDENTITY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = 'dbo' 
        AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
        """
        
        try:
            cursor.execute(column_query, table_name)
            columns = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching columns for {table_name}: {e}")
            raise
        
        # Build DDL
        ddl = f"CREATE TABLE [dbo].[{table_name}] (\n"
        column_defs = []
        primary_keys = []
        
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            max_length = col[2]
            precision = col[3]
            scale = col[4]
            is_nullable = col[5]
            default = col[6]
            is_pk = col[7]
            is_identity = col[8]  # New field
            
            # Build column definition
            col_def = f"    [{col_name}] {data_type}"
            
            # Add size/precision info
            if data_type in ['varchar', 'char', 'nvarchar', 'nchar']:
                if max_length == -1:
                    col_def += "(MAX)"
                elif max_length:
                    col_def += f"({max_length})"
            elif data_type in ['decimal', 'numeric']:
                if precision and scale is not None:
                    col_def += f"({precision},{scale})"
            elif data_type == 'float' and precision:
                col_def += f"({precision})"
            
            # Add IDENTITY if applicable
            if is_identity == 1:
                col_def += " IDENTITY(1,1)"
            
            # Add NOT NULL
            if is_nullable == 'NO':
                col_def += " NOT NULL"
                
            # Add DEFAULT
            if default and is_identity != 1:  # Don't add DEFAULT for IDENTITY columns
                col_def += f" DEFAULT {default}"
                
            column_defs.append(col_def)
            
            # Track primary keys
            if is_pk == 'YES':
                primary_keys.append(col_name)
        
        ddl += ",\n".join(column_defs)
        
        # Add primary key constraint if exists
        if primary_keys:
            pk_constraint = f",\n    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({', '.join([f'[{pk}]' for pk in primary_keys])})"
            ddl += pk_constraint
            
        ddl += "\n)"
        
        # Rest of the method remains the same...
        # Try to get constraints and indexes - but don't fail if it doesn't work
        try:
            # Get unique constraints - simple query
            unique_query = """
            SELECT 
                tc.CONSTRAINT_NAME,
                kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND tc.TABLE_CATALOG = kcu.TABLE_CATALOG
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            WHERE tc.TABLE_CATALOG = DB_NAME()
            AND tc.TABLE_SCHEMA = 'dbo' 
            AND tc.TABLE_NAME = ?
            AND tc.CONSTRAINT_TYPE = 'UNIQUE'
            ORDER BY tc.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
            """
            
            cursor.execute(unique_query, table_name)
            unique_rows = cursor.fetchall()
            
            # Group unique constraints manually
            unique_constraints = {}
            for row in unique_rows:
                constraint_name = row[0]
                column_name = row[1]
                if constraint_name not in unique_constraints:
                    unique_constraints[constraint_name] = []
                unique_constraints[constraint_name].append(column_name)
            
            # Add metadata about unique constraints
            if unique_constraints:
                ddl += "\n-- UNIQUE CONSTRAINTS:\n"
                for constraint_name, columns in unique_constraints.items():
                    ddl += f"-- {constraint_name}: {','.join(columns)}\n"
                    
        except Exception as e:
            logger.warning(f"Could not fetch constraints for {table_name}: {e}")
            
        # Try to get indexes
        try:
            # Get current database name
            db_query = "SELECT DB_NAME()"
            cursor.execute(db_query)
            current_db = cursor.fetchone()[0]
            
            # Get indexes - using fully qualified name
            index_query = """
            SELECT 
                i.name AS INDEX_NAME,
                i.is_unique,
                c.name AS COLUMN_NAME
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID(?)
            AND i.is_primary_key = 0
            AND i.type > 0
            ORDER BY i.name, ic.key_ordinal
            """
            
            # Use fully qualified name: database.schema.table
            full_table_name = f'{current_db}.dbo.{table_name}'
            cursor.execute(index_query, full_table_name)
            index_rows = cursor.fetchall()
            
            # Group indexes manually
            indexes = {}
            for row in index_rows:
                index_name = row[0]
                is_unique = row[1]
                column_name = row[2]
                if index_name not in indexes:
                    indexes[index_name] = {'is_unique': is_unique, 'columns': []}
                indexes[index_name]['columns'].append(column_name)
            
            # Add metadata about indexes
            if indexes:
                ddl += "\n-- INDEXES:\n"
                for index_name, index_info in indexes.items():
                    unique_str = "UNIQUE " if index_info['is_unique'] else ""
                    ddl += f"-- {index_name}: {unique_str}{','.join(index_info['columns'])}\n"
            else:
                logger.debug(f"No indexes found for {full_table_name}")
                    
        except Exception as e:
            logger.warning(f"Could not fetch indexes for {table_name}: {e}")
        
        cursor.close()
        return ddl

    def save_model(self, database_name: str, schema_name: str, table_name: str, model_code: str, status: str = 'GOOD'):
        """Save generated model to appropriate directory structure
        
        Args:
            database_name: Database name
            schema_name: Schema name (usually 'dbo')
            table_name: Table name
            model_code: Generated model code
            status: 'GOOD', 'PATCH', or 'BAD'
        """
        # Create directory structure based on status
        if status == 'GOOD':
            dir_path = self.output_dir / database_name / schema_name
        elif status == 'PATCH':
            dir_path = self.output_dir / database_name / "PATCH"
        else:  # BAD
            dir_path = self.output_dir / database_name / "BAD"
            
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Sanitize the filename
        safe_filename = sanitize_identifier(table_name, self.numeric_table_prefix, is_table_name=False)
        
        # Save model file
        file_path = dir_path / f"{safe_filename}_model.py"
        with open(file_path, 'w') as f:
            f.write(model_code)
            
        logger.info(f"Saved model to {file_path} (status: {status})")   
    def switch_database(self, database_name: str):
        """Switch to a different database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"USE [{database_name}]")
            cursor.close()
            logger.info(f"Switched to database: {database_name}")
        except Exception as e:
            logger.error(f"Failed to switch to database {database_name}: {e}")
            raise
            
    def process_database(self, database_list: List[str] = None):
        """Process database(s) and generate all models"""
        if database_list:
            # Process each database in the list
            for database_name in database_list:
                try:
                    logger.info(f"Processing database: {database_name}")
                    
                    # Switch to the database
                    self.switch_database(database_name)
                    
                    # Get all tables
                    tables = self.get_tables()
                    
                    # Track statistics
                    good_count = 0
                    patch_count = 0
                    bad_count = 0
                    
                    for table in tables:
                        try:
                            logger.info(f"Processing table: {database_name}.dbo.{table}")
                            
                            # Get DDL
                            ddl = self.get_table_ddl(table)
                            logger.debug(f"DDL for {table}:\n{ddl}")
                            
                            # Generate model programmatically
                            model_code, status = self.generate_model_programmatically(table, ddl, database_name)
                            
                            # Save model based on status
                            self.save_model(database_name, "dbo", table, model_code, status)
                            
                            # Update statistics
                            if status == 'GOOD':
                                good_count += 1
                            elif status == 'PATCH':
                                patch_count += 1
                            else:
                                bad_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing table {table}: {e}")
                            continue
                            
                    logger.info(f"Completed processing database {database_name}")
                    logger.info(f"Results: GOOD={good_count}, PATCH={patch_count}, BAD={bad_count}")
                        
                except Exception as e:
                    logger.error(f"Error processing database {database_name}: {e}")
                    continue
                    
    def _build_column_definition(self, col: dict, is_primary_key: bool) -> str:
        """Build SQLAlchemy column definition from column info"""
        
        # Map SQL Server types to SQLAlchemy types
        type_mapping = {
            'bit': 'Boolean',
            'int': 'Integer',
            'bigint': 'Integer',
            'smallint': 'Integer',
            'tinyint': 'Integer',
            'float': 'Float',
            'real': 'Float',
            'money': 'Numeric(precision=19, scale=4)',
            'smallmoney': 'Numeric(precision=10, scale=4)',
            'text': 'Text',
            'ntext': 'Text',
            'image': 'LargeBinary',
            'datetime': 'DateTime',
            'datetime2': 'DateTime',
            'smalldatetime': 'DateTime',
            'date': 'Date',
            'time': 'Time',
            'uniqueidentifier': 'String(length=36)',
            'timestamp': 'LargeBinary(length=8)',
            'rowversion': 'LargeBinary(length=8)',
            'xml': 'Text',
            'sql_variant': 'Text'
        }
        
        # Handle parameterized types
        col_type = col['type']
        type_params = col['params']
        
        if col_type in ['varchar', 'char', 'nvarchar', 'nchar']:
            if type_params == 'MAX':
                sqlalchemy_type = 'Text'
            elif type_params:
                sqlalchemy_type = f'String(length={type_params})'
            else:
                sqlalchemy_type = 'String'
                
        elif col_type in ['decimal', 'numeric']:
            if type_params:
                # Parse precision and scale
                parts = type_params.split(',')
                if len(parts) == 2:
                    precision = parts[0].strip()
                    scale = parts[1].strip()
                    sqlalchemy_type = f'Numeric(precision={precision}, scale={scale})'
                else:
                    sqlalchemy_type = f'Numeric(precision={parts[0].strip()})'
            else:
                sqlalchemy_type = 'Numeric'
                
        elif col_type in ['binary', 'varbinary']:
            if type_params == 'MAX':
                sqlalchemy_type = 'LargeBinary'
            elif type_params:
                sqlalchemy_type = f'LargeBinary(length={type_params})'
            else:
                sqlalchemy_type = 'LargeBinary'
                
        else:
            # Use mapping or default to String
            sqlalchemy_type = type_mapping.get(col_type, 'String')
        
        # Build column arguments
        col_args = [sqlalchemy_type]
        
        # Add primary key
        if is_primary_key:
            col_args.append('primary_key=True')
        
        # Add nullable (only if False)
        if not col['nullable']:
            col_args.append('nullable=False')
        
        # Note: We skip server_default as per requirements
        
        return f"Column({', '.join(col_args)})"
    
    def generate_model_programmatically(self, table_name: str, ddl: str, database_name: str) -> Tuple[str, str]:
        """Generate SQLAlchemy model programmatically from DDL
        
        Returns:
            Tuple of (model_code, status) where status is 'GOOD', 'PATCH', or 'BAD'
        """

         # Create class name as Database_Schema_TableName
        # Sanitize each part separately then combine
        safe_db = sanitize_identifier(database_name, self.numeric_table_prefix, is_table_name=False)
        safe_table = sanitize_identifier(table_name, self.numeric_table_prefix, is_table_name=False)
        
        # Combine with underscores and ensure first letter is uppercase
        class_name = f"{safe_db}_dbo_{safe_table}"
        
        # Rest of the function remains the same...
        # Parse DDL to extract columns
        columns = []
        primary_keys = []
        status = 'GOOD'  # Default status
        
        # DEBUG: Show column extraction
        print("\nDEBUG: Extracting columns...")
        
        # Extract column definitions from DDL line by line
        lines = ddl.split('\n')
        in_table_def = False
        
        for line in lines:
            line = line.strip()
            
            # Start of table definition
            if 'CREATE TABLE' in line:
                in_table_def = True
                continue
                
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
                
            # Stop at end of table or constraints
            if in_table_def and (line.startswith(')') or 'CONSTRAINT' in line.upper()):
                break
                
            # Parse column definition
            if in_table_def and line.startswith('['):
                try:
                    # Pattern for columns with nested brackets like [BKGL_CURRENT[  1]]
                    nested_match = re.match(r'^\[([^\]]+\[[^\]]+\])\]\s+(\w+)', line)
                    # Pattern for simple columns like [MDS_RECNUM]
                    simple_match = re.match(r'^\[([^\]]+)\]\s+(\w+)', line)
                    
                    if nested_match:
                        col_name = nested_match.group(1)
                        data_type = nested_match.group(2).lower()
                        # Get the rest of the line after the data type
                        rest_start = nested_match.end()
                    elif simple_match:
                        col_name = simple_match.group(1)
                        data_type = simple_match.group(2).lower()
                        # Get the rest of the line after the data type
                        rest_start = simple_match.end()
                    else:
                        print(f"DEBUG: Could not parse column name from: {line}")
                        continue
                    
                    # Extract the rest of the line for type params and modifiers
                    rest_of_line = line[rest_start:].strip()
                    
                    # Parse type parameters and modifiers
                    type_params = None
                    nullable = True
                    
                    # Check for type parameters like (10) or (19,4)
                    if rest_of_line.startswith('('):
                        param_match = re.match(r'^\(([^)]+)\)', rest_of_line)
                        if param_match:
                            type_params = param_match.group(1)
                            rest_of_line = rest_of_line[param_match.end():].strip()
                    
                    # Check for NOT NULL
                    if 'NOT NULL' in rest_of_line:
                        nullable = False
                    
                    print(f"DEBUG: Found column: {col_name} {data_type}({type_params}) nullable={nullable}")
                    
                    columns.append({
                        'name': col_name,
                        'type': data_type,
                        'params': type_params,
                        'nullable': nullable,
                        'default': None
                    })
                        
                except Exception as e:
                    print(f"DEBUG: Error parsing line '{line}': {e}")
        
        print(f"\nDEBUG: Total columns found: {len(columns)}")
        
        # Extract primary key columns
        pk_pattern = r'CONSTRAINT\s+\[?[^\]]+\]?\s+PRIMARY KEY\s*\(([^)]+)\)'
        pk_match = re.search(pk_pattern, ddl, re.IGNORECASE)
        if pk_match:
            pk_cols = pk_match.group(1)
            primary_keys = [col.strip().strip('[]') for col in pk_cols.split(',')]
            print(f"DEBUG: Found PRIMARY KEY constraint with columns: {primary_keys}")
        else:
            print("DEBUG: No PRIMARY KEY constraint found - checking for IDENTITY columns")
            # Look for IDENTITY columns in the DDL
            identity_pattern = r'\[([^\]]+)\]\s+\w+(?:\([^)]+\))?\s+IDENTITY(?:\([^)]+\))?'
            identity_match = re.search(identity_pattern, ddl)
            if identity_match:
                identity_col = identity_match.group(1)
                primary_keys = [identity_col]
                status = 'PATCH'  # Mark as patched
                print(f"DEBUG: Found IDENTITY column '{identity_col}' - using as primary key (PATCH)")
            else:
                print("DEBUG: No IDENTITY column found either - marking as BAD")
                status = 'BAD'
        
        # Extract unique constraints from comments
        unique_constraints = []
        unique_pattern = r'-- (\w+): ([\w,\s]+)'
        unique_section = False
        for line in ddl.split('\n'):
            if '-- UNIQUE CONSTRAINTS:' in line:
                unique_section = True
                continue
            elif '-- INDEXES:' in line:
                unique_section = False
            elif unique_section and line.startswith('--'):
                match = re.match(unique_pattern, line)
                if match:
                    constraint_name = match.group(1)
                    columns_str = match.group(2)
                    constraint_cols = [col.strip() for col in columns_str.split(',')]
                    unique_constraints.append({
                        'name': constraint_name,
                        'columns': constraint_cols
                    })
        
        # Extract indexes from comments
        indexes = []
        index_pattern = r'-- (\w+): (UNIQUE\s+)?([\w,\s]+)'
        index_section = False
        for line in ddl.split('\n'):
            if '-- INDEXES:' in line:
                index_section = True
                continue
            elif index_section and line.startswith('--'):
                match = re.match(index_pattern, line)
                if match:
                    index_name = match.group(1)
                    is_unique = match.group(2) is not None
                    columns_str = match.group(3)
                    index_cols = [col.strip() for col in columns_str.split(',')]
                    indexes.append({
                        'name': index_name,
                        'columns': index_cols,
                        'unique': is_unique
                    })
        
        # Build the model code
        model_lines = []
        
        # Add imports
        model_lines.append(self.header)
        # Get generation time
        generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add status comment if not GOOD
        if status != 'GOOD':
            model_lines.append(f"# STATUS: {status}")
            if status == 'PATCH':
                model_lines.append("# WARNING: No explicit PRIMARY KEY found - using IDENTITY column as primary key")
            elif status == 'BAD':
                model_lines.append("# WARNING: No primary key or IDENTITY column found")
            model_lines.append("")
        
        # Start class definition
        model_lines.append(f"class {class_name}(Base):")
        model_lines.append(f"    __tablename__ = '{table_name}'")
        model_lines.append(f"    __bind_key__ = '{self.bind_key}'")
        model_lines.append("    __depends_on__ = []")
        model_lines.append("    __version__ = '1.0.0'")
        model_lines.append(f"    __generated__ = '{generation_time}'")
        
        # Build __table_args__
        table_args_items = []
        
        # Add unique constraints
        for uc in unique_constraints:
            cols_str = ', '.join([f"'{col}'" for col in uc['columns']])
            table_args_items.append(f"        UniqueConstraint({cols_str}, name='{uc['name']}')")
        
        # Add indexes
        for idx in indexes:
            cols_str = ', '.join([f"'{col}'" for col in idx['columns']])
            table_args_items.append(f"        Index('{idx['name']}', {cols_str})")
        
        # Add schema
        if table_args_items:
            model_lines.append("    __table_args__ = (")
            model_lines.extend([item + "," for item in table_args_items])
            model_lines.append(f"        {{'schema': '{database_name}.dbo'}}")
            model_lines.append("    )")
        else:
            model_lines.append(f"    __table_args__ = {{'schema': '{database_name}.dbo'}}")
        
        model_lines.append("")  # Empty line before columns
        
        # Create a mapping to track sanitized names for primary keys
        sanitized_pk_names = {}
        for pk in primary_keys:
            sanitized_pk_names[pk] = sanitize_identifier(pk, self.numeric_table_prefix, is_table_name=False)
        
        # Add columns
        for col in columns:
            # Sanitize column name
            safe_col_name = sanitize_identifier(col['name'], self.numeric_table_prefix, is_table_name=False)
            
            col_def = self._build_column_definition(col, col['name'] in primary_keys)
            
            # If we renamed the column, we need to specify the actual DB column name
            if safe_col_name != col['name']:
                # Add the key parameter to map to the actual column name
                if col_def.endswith(')'):
                    # Insert key parameter before the closing paren
                    col_def = col_def[:-1] + f", key='{col['name']}')"
                else:
                    # No closing paren (like for simple Column(Integer))
                    col_def += f", key='{col['name']}')"
            
            model_lines.append(f"    {safe_col_name} = {col_def}")
        
        # Add __repr__ method
        model_lines.append("")
        model_lines.append("    def __repr__(self):")
        if primary_keys:
            # Use original primary key names in the display
            pk_parts = []
            for pk in primary_keys:
                safe_pk = sanitized_pk_names.get(pk, sanitize_identifier(pk, self.numeric_table_prefix, is_table_name=False))
                pk_parts.append(f"{pk}={{self.{safe_pk}}}")
            pk_str = ', '.join(pk_parts)
            # Use original table name in repr for readability
            model_lines.append(f'        return f"<{class_name}({pk_str})>"')
        else:
            model_lines.append(f'        return f"<{class_name}()>"')
        
        return '\n'.join(model_lines), status
    

if __name__ == "__main__":
    main()