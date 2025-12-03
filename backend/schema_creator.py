"""
Database Schema Creator Module.

This module handles creating the database schema and tables.
"""

import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class SchemaCreator:
    """Handles database schema creation."""
    
    def __init__(self, db_config: Optional[dict] = None):
        """
        Initialize schema creator.
        
        Args:
            db_config: Database configuration dict with keys:
                host, port, database, user, password
                If None, reads from environment variables
        """
        if db_config:
            self.db_config = db_config
        else:
            # Load from .env file in backend directory
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
            
            password = os.getenv('DB_PASSWORD')
            if not password:
                print("⚠️  WARNING: DB_PASSWORD not found in .env file!")
                print("   Please run: python backend/scripts/create_env.py")
                password = input("Enter PostgreSQL password (or press Enter to use 'postgres'): ").strip() or 'postgres'
            
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'ncaafb'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': password
            }
        
        self.conn = None
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print(f"Connected to database: {self.db_config['database']}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def create_database(self, db_name: str) -> bool:
        """
        Create database if it doesn't exist.
        
        Args:
            db_name: Name of database to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to postgres database to create new database
            temp_config = self.db_config.copy()
            temp_config['database'] = 'postgres'
            temp_conn = psycopg2.connect(**temp_config)
            temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = temp_conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                ))
                print(f"Database '{db_name}' created successfully")
            else:
                print(f"Database '{db_name}' already exists")
            
            cursor.close()
            temp_conn.close()
            return True
        except psycopg2.Error as e:
            print(f"Error creating database: {e}")
            return False
    
    def execute_sql_file(self, filepath: str) -> bool:
        """
        Execute SQL commands from a file.
        
        Args:
            filepath: Path to SQL file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            if not self.connect():
                return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            cursor = self.conn.cursor()
            cursor.execute(sql_script)
            cursor.close()
            
            print(f"Successfully executed SQL file: {filepath}")
            return True
        except Exception as e:
            print(f"Error executing SQL file {filepath}: {e}")
            return False
    
    def create_schema(self) -> bool:
        """
        Create the database schema by executing schema.sql.
        
        Returns:
            True if successful, False otherwise
        """
        schema_file = os.path.join(
            os.path.dirname(__file__),
            'sql',
            'schema.sql'
        )
        
        if not os.path.exists(schema_file):
            print(f"Schema file not found: {schema_file}")
            return False
        
        return self.execute_sql_file(schema_file)
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

