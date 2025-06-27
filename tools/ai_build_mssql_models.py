#!/usr/bin/env python3
"""
Automated MSSQL table scanner and SQLAlchemy model generator using Claude API
"""

import os
import sys
import pyodbc
import anthropic
from pathlib import Path
import logging
import time
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see more details
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class mssql_model_generator:
    def __init__(self, connection_string: str, claude_api_key: str, output_dir: str = "generated_models"):
        self.connection_string = connection_string
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
        self.output_dir = Path(output_dir)
        self.connection = None
        
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
        
        # Get column information - basic query for compatibility
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
            END AS IS_PRIMARY_KEY
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
            
            # Add NOT NULL
            if is_nullable == 'NO':
                col_def += " NOT NULL"
                
            # Add DEFAULT
            if default:
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
        
    def generate_model_with_claude(self, table_name: str, ddl: str, database_name: str) -> str:
        """Use Claude API to generate SQLAlchemy model from DDL"""
        prompt = f"""Generate a SQLAlchemy model CLASS ONLY for the following MSSQL table.

Requirements:
- DO NOT include any import statements
- Use snake_case for all variable names
- The model class name should be the table name in PascalCase
- Class should inherit from Base
- Include __tablename__ = '{table_name}' (just the table name)
- Include __depends_on__ = [] attribute (empty list)
- Include __table_args__ BEFORE column definitions
- Use Column() for all fields
- Mark primary key columns with primary_key=True
- Add a __repr__ method that shows the primary key value(s) at the END
- For columns with DEFAULT values, DO NOT include server_default in the model
- SKIP any computed columns mentioned in comments

CRITICAL ORDER - The class MUST be structured in this exact order:
1. class ClassName(Base):
2.     __tablename__ = 'table_name'
3.     __depends_on__ = []
4.     __table_args__ = (...) # BEFORE columns!
5.     # Column definitions
6.     id = Column(...)
7.     name = Column(...)
8.     # __repr__ method at the end

CRITICAL: You MUST include __table_args__ with:
1. A 'schema' parameter set to '{database_name}.dbo'
2. Any UNIQUE CONSTRAINTS listed in the DDL comments
3. Any INDEXES listed in the DDL comments

Example format:
class MyTable(Base):
    __tablename__ = 'my_table'
    __depends_on__ = []
    __table_args__ = (
        UniqueConstraint('email', name='UQ_email'),
        Index('IX_name', 'name'),
        Index('IX_name_email', 'name', 'email'),
        {{'schema': '{database_name}.dbo'}}
    )
    
    id = Column(Integer, primary_key=True)
    name = Column(String(length=50), nullable=False)
    email = Column(String(length=100))
    
    def __repr__(self):
        return f"<MyTable(id={{self.id}})>"

If there are no constraints or indexes, still include the schema:
    __table_args__ = {{'schema': '{database_name}.dbo'}}

CRITICAL Type Mappings (USE EXACTLY THESE):
- bit -> Boolean
- int -> Integer
- bigint -> Integer  
- smallint -> Integer
- tinyint -> Integer
- decimal(p,s) -> Numeric(precision=p, scale=s)
- numeric(p,s) -> Numeric(precision=p, scale=s)
- money -> Numeric(precision=19, scale=4)
- smallmoney -> Numeric(precision=10, scale=4)
- float -> Float
- real -> Float
- varchar(n) -> String(length=n)
- char(n) -> String(length=n)
- nvarchar(n) -> String(length=n)
- nchar(n) -> String(length=n)
- varchar(MAX) -> Text
- nvarchar(MAX) -> Text
- text -> Text
- ntext -> Text
- binary(n) -> LargeBinary(length=n)
- varbinary(n) -> LargeBinary(length=n)
- varbinary(MAX) -> LargeBinary
- image -> LargeBinary
- datetime -> DateTime
- datetime2 -> DateTime
- smalldatetime -> DateTime
- date -> Date
- time -> Time
- uniqueidentifier -> String(length=36)
- timestamp -> LargeBinary(length=8)
- rowversion -> LargeBinary(length=8)
- xml -> Text
- sql_variant -> Text

IMPORTANT Rules:
- __tablename__ is ONLY the table name
- __table_args__ MUST come BEFORE column definitions
- __table_args__ MUST include {{'schema': '{database_name}.dbo'}}
- Always check for UNIQUE CONSTRAINTS and INDEXES in the DDL comments
- For nullable=False columns, always include nullable=False
- For nullable=True columns, omit the nullable parameter

Database: {database_name}
Schema: dbo
Table DDL:
{ddl}

Generate ONLY the class definition, no imports, no explanations."""

        try:
            haiku="claude-3-5-haiku-20241022"
            opus3="claude-3-opus-20240229"
            opus4="claude-opus-4-20250514"
            sonnet37="claude-3-7-sonnet-20250219"
            response = self.claude_client.messages.create(
                model=opus4,
                max_tokens=8000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            model_class = response.content[0].text
            
            # Prepend the standard header with ALL required types
            header = """import re
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Time, Date, Text, 
    func, ForeignKey, Index, UniqueConstraint, Numeric, Float, 
    LargeBinary, Table, MetaData
)
from sqlalchemy.orm import relationship, validates, backref


from app.base.model import Base

"""
            
            full_model = header + model_class
            
            return full_model
            
        except Exception as e:
            logger.error(f"Claude API error for table {table_name}: {e}")
            raise
            
    def save_model(self, database_name: str, schema_name: str, table_name: str, model_code: str):
        """Save generated model to appropriate directory structure"""
        # Create directory structure
        dir_path = self.output_dir / database_name / schema_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Save model file
        file_path = dir_path / f"{table_name}_model.py"
        with open(file_path, 'w') as f:
            f.write(model_code)
            
        logger.info(f"Saved model to {file_path}")
        
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
                    
                    for table in tables:
                        try:
                            logger.info(f"Processing table: {database_name}.dbo.{table}")
                            
                            # Get DDL
                            ddl = self.get_table_ddl(table)
                            logger.debug(f"DDL for {table}:\n{ddl}")
                            
                            # Generate model with Claude
                            model_code = self.generate_model_with_claude(table, ddl, database_name)
                            
                            # Save model
                            self.save_model(database_name, "dbo", table, model_code)
                            
                            # Rate limiting - be nice to Claude API
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error processing table {table}: {e}")
                            continue
                            
                    logger.info(f"Completed processing database {database_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing database {database_name}: {e}")
                    continue
        else:
            # Process current database only
            current_db = self.get_database_name()
            logger.info(f"Processing current database: {current_db}")
            
            # Get all tables
            tables = self.get_tables()
            
            for table in tables:
                try:
                    logger.info(f"Processing table: {table}")
                    
                    # Get DDL
                    ddl = self.get_table_ddl(table)
                    logger.debug(f"DDL for {table}:\n{ddl}")
                    
                    # Generate model with Claude
                    model_code = self.generate_model_with_claude(table, ddl, current_db)
                    
                    # Save model
                    self.save_model(current_db, "dbo", table, model_code)
                    
                    # Rate limiting - be nice to Claude API
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing table {table}: {e}")
                    continue
                    
            logger.info(f"Completed processing database {current_db}")


def main():
    output_dir="app/_system/pr/"
    
    database_list = ['PartsTrader']
    
    # Create generator
    generator = mssql_model_generator(connection_string, claude_api_key, output_dir)
    
    logger.info(f"Output directory: {generator.output_dir}")
    
    try:
        # Connect to database
        generator.connect()
        
        # Process database(s)
        generator.process_database(database_list)
        
    finally:
        # Always disconnect
        generator.disconnect()


if __name__ == "__main__":
    main()