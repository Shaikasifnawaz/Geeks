"""
Database Populator Module.

This module handles inserting transformed data into the database.
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2 import sql
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.utils.helpers import get_project_root
except ImportError:
    from utils.helpers import get_project_root

load_dotenv()


class DatabasePopulator:
    """Handles populating the database with transformed data."""
    
    def __init__(self, db_config: Optional[dict] = None):
        """
        Initialize database populator.
        
        Args:
            db_config: Database configuration dict
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
        self.insert_statements = []
    
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
    
    def _generate_insert_statement(self, table_name: str, record: Dict[str, Any]) -> str:
        """
        Generate SQL INSERT statement for a record.
        
        Args:
            table_name: Name of the table
            record: Dictionary of column -> value
            
        Returns:
            SQL INSERT statement string
        """
        columns = list(record.keys())
        values = list(record.values())
        
        # Format values for SQL
        formatted_values = []
        for val in values:
            if val is None:
                formatted_values.append('NULL')
            elif isinstance(val, str):
                # Escape single quotes
                escaped = val.replace("'", "''")
                formatted_values.append(f"'{escaped}'")
            elif isinstance(val, bool):
                formatted_values.append('TRUE' if val else 'FALSE')
            else:
                formatted_values.append(str(val))
        
        columns_str = ', '.join(columns)
        values_str = ', '.join(formatted_values)
        
        return f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
    
    def _insert_table(self, table_name: str, records: List[Dict[str, Any]], 
                     use_upsert: bool = True) -> int:
        """
        Insert records into a table.
        
        Args:
            table_name: Name of the table
            records: List of record dictionaries
            use_upsert: If True, use ON CONFLICT UPDATE (upsert)
            
        Returns:
            Number of records inserted
        """
        if not records:
            print(f"No records to insert into {table_name}")
            return 0
        
        if not self.conn:
            if not self.connect():
                return 0
        
        try:
            cursor = self.conn.cursor()
            
            # Get column names from first record
            columns = list(records[0].keys())
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            
            if use_upsert:
                # Get primary key column (usually table_name_id or id)
                pk_column = None
                if f"{table_name[:-1]}_id" in columns:  # e.g., team_id for teams table
                    pk_column = f"{table_name[:-1]}_id"
                elif "id" in columns:
                    pk_column = "id"
                elif f"{table_name}_id" in columns:
                    pk_column = f"{table_name}_id"
                
                if pk_column:
                    # Use ON CONFLICT for primary key
                    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != pk_column])
                    query = f"""
                        INSERT INTO {table_name} ({columns_str})
                        VALUES ({placeholders})
                        ON CONFLICT ({pk_column}) DO UPDATE SET {update_clause}
                    """
                else:
                    # No primary key found, just use DO NOTHING
                    query = f"""
                        INSERT INTO {table_name} ({columns_str})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                    """
            else:
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Prepare data
            data = []
            for record in records:
                row = [record.get(col) for col in columns]
                data.append(row)
            
            # Execute batch insert
            execute_batch(cursor, query, data, page_size=100)
            
            # Also save INSERT statements to file
            for record in records:
                stmt = self._generate_insert_statement(table_name, record)
                self.insert_statements.append(stmt)
            
            self.conn.commit()
            count = len(records)
            print(f"Inserted {count} records into {table_name}")
            
            cursor.close()
            return count
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error inserting into {table_name}: {e}")
            return 0
    
    def populate_all_tables(self, transformed_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Populate all database tables with transformed data.
        
        Args:
            transformed_data: Dictionary of table_name -> list of records
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connect():
            return False
        
        print("=" * 60)
        print("Starting database population...")
        print("=" * 60)
        
        # Insert in dependency order
        insertion_order = [
            'conferences',
            'divisions',
            'venues',
            'seasons',
            'teams',
            'players',
            'coaches',
            'player_statistics',
            'rankings'
        ]
        
        total_inserted = 0
        
        for table_name in insertion_order:
            if table_name in transformed_data:
                records = transformed_data[table_name]
                count = self._insert_table(table_name, records)
                total_inserted += count
        
        # Save INSERT statements to file
        self._save_insert_statements()
        
        print("\n" + "=" * 60)
        print(f"Database population completed! Total records: {total_inserted}")
        print("=" * 60)
        
        return True
    
    def _save_insert_statements(self) -> None:
        """Save all generated INSERT statements to SQL file."""
        sql_dir = os.path.join(get_project_root(), 'backend', 'sql')
        os.makedirs(sql_dir, exist_ok=True)
        
        filepath = os.path.join(sql_dir, 'insert_statements.sql')
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("-- Generated INSERT statements for NCAAFB database\n")
                f.write(f"-- Total statements: {len(self.insert_statements)}\n\n")
                
                for stmt in self.insert_statements:
                    f.write(stmt + '\n')
            
            print(f"Saved {len(self.insert_statements)} INSERT statements to {filepath}")
        except Exception as e:
            print(f"Error saving INSERT statements: {e}")
    
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

