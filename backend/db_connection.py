"""
Database Connection Utility for LLM Agent.

This module provides a reusable database connection class that follows
the same pattern as SchemaCreator and DatabasePopulator.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List, Any, Tuple
from dotenv import load_dotenv


class DatabaseConnection:
    """Handles database connections for the LLM agent."""
    
    def __init__(self, db_config: Optional[dict] = None):
        """
        Initialize database connection.
        
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
                password = 'postgres'  # Default fallback
            
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
            print(f"Connected to database: {self.db_config['database']}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters for parameterized queries
            
        Returns:
            Tuple of (success: bool, results: List[Dict], error: Optional[str])
        """
        if not self.conn:
            if not self.connect():
                return False, [], "Failed to connect to database"
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            # Convert RealDictRow to regular dict
            results = [dict(row) for row in results]
            cursor.close()
            return True, results, None
        except psycopg2.Error as e:
            error_msg = str(e)
            print(f"Database query error: {error_msg}")
            try:
                # Rollback the transaction to clear the error state
                self.conn.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {rollback_error}")
                # If rollback fails, try to reconnect
                try:
                    self.close()
                    self.connect()
                except Exception as reconnect_error:
                    print(f"Error during reconnect: {reconnect_error}")
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            try:
                # Rollback the transaction to clear the error state
                self.conn.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {rollback_error}")
                # If rollback fails, try to reconnect
                try:
                    self.close()
                    self.connect()
                except Exception as reconnect_error:
                    print(f"Error during reconnect: {reconnect_error}")
            return False, [], error_msg
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get database schema information for LLM context.
        
        Returns:
            Dictionary containing schema information
        """
        if not self.conn:
            if not self.connect():
                return {}
        
        schema_info = {
            'tables': {}
        }
        
        try:
            cursor = self.conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get columns for each table
            for table in tables:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = []
                for col in cursor.fetchall():
                    columns.append({
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'default': col[3]
                    })
                
                # Get foreign keys
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = %s
                """, (table,))
                
                foreign_keys = []
                for fk in cursor.fetchall():
                    foreign_keys.append({
                        'column': fk[0],
                        'references_table': fk[1],
                        'references_column': fk[2]
                    })
                
                schema_info['tables'][table] = {
                    'columns': columns,
                    'foreign_keys': foreign_keys
                }
            
            cursor.close()
            return schema_info
            
        except psycopg2.Error as e:
            print(f"Error getting schema info: {e}")
            return {}
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

