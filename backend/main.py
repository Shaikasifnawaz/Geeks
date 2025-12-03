"""
Main ETL Pipeline Orchestrator for NCAAFB Data Pipeline.

This is the main entry point that orchestrates the entire ETL process:
1. Fetch data from APIs
2. Transform and normalize data
3. Create database schema
4. Populate database
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.api_fetcher import APIFetcher
    from backend.data_transformer_uuid import DataTransformer
    from backend.schema_creator import SchemaCreator
    from backend.db_populator import DatabasePopulator
except ImportError:
    from api_fetcher import APIFetcher
    try:
        from data_transformer_uuid import DataTransformer
    except ImportError:
        from data_transformer import DataTransformer
    from schema_creator import SchemaCreator
    from db_populator import DatabasePopulator


def run_etl_pipeline(year: int = 2025, season_type: str = "REG", 
                    create_schema: bool = True, max_teams: int = 10,
                    fetch_player_profiles: bool = False) -> bool:
    """
    Run the complete ETL pipeline.
    
    Args:
        year: Season year
        season_type: Season type (REG, PST, etc.)
        create_schema: Whether to create database schema (set False if schema exists)
        max_teams: Maximum number of teams to fetch rosters for (None = all)
        fetch_player_profiles: Whether to fetch individual player profiles
        
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    print("\n" + "=" * 60)
    print("NCAAFB Data Pipeline - ETL Process")
    print("=" * 60 + "\n")
    
    try:
        # Step 1: Fetch data from APIs
        print("\n[STEP 1/4] Fetching data from Sportradar APIs...")
        print("-" * 60)
        fetcher = APIFetcher()
        all_api_data = fetcher.fetch_all_data(
            year=year, 
            season_type=season_type,
            max_teams=max_teams,
            fetch_player_profiles=fetch_player_profiles
        )
        
        if not all_api_data:
            print("ERROR: Failed to fetch API data")
            return False
        
        # Step 2: Transform and normalize data
        print("\n[STEP 2/4] Transforming and normalizing data...")
        print("-" * 60)
        transformer = DataTransformer()
        transformed_data = transformer.transform_all_data(
            all_api_data, 
            year=year, 
            season_type=season_type
        )
        
        if not transformed_data:
            print("ERROR: Failed to transform data")
            return False
        
        # Step 3: Create database schema
        if create_schema:
            print("\n[STEP 3/4] Creating database schema...")
            print("-" * 60)
            schema_creator = SchemaCreator()
            
            # Create database if it doesn't exist
            db_name = os.getenv('DB_NAME', 'ncaafb')
            schema_creator.create_database(db_name)
            
            # Create schema
            if not schema_creator.create_schema():
                print("ERROR: Failed to create database schema")
                return False
            
            schema_creator.close()
        else:
            print("\n[STEP 3/4] Skipping schema creation (using existing schema)...")
        
        # Step 4: Populate database
        print("\n[STEP 4/4] Populating database...")
        print("-" * 60)
        populator = DatabasePopulator()
        
        if not populator.populate_all_tables(transformed_data):
            print("ERROR: Failed to populate database")
            return False
        
        populator.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("ETL PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSummary:")
        for table_name, records in transformed_data.items():
            print(f"  - {table_name}: {len(records)} records")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Pipeline failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NCAAFB Data Pipeline ETL')
    parser.add_argument('--year', type=int, default=2025, 
                       help='Season year (default: 2025)')
    parser.add_argument('--season-type', type=str, default='REG',
                       help='Season type: REG, PST, etc. (default: REG)')
    parser.add_argument('--skip-schema', action='store_true',
                       help='Skip schema creation (use existing schema)')
    parser.add_argument('--max-teams', type=int, default=10,
                       help='Maximum number of teams to fetch (default: 10, use 0 for all)')
    parser.add_argument('--fetch-profiles', action='store_true',
                       help='Fetch individual player profiles (slower)')
    
    args = parser.parse_args()
    
    max_teams = None if args.max_teams == 0 else args.max_teams
    
    success = run_etl_pipeline(
        year=args.year,
        season_type=args.season_type,
        create_schema=not args.skip_schema,
        max_teams=max_teams,
        fetch_player_profiles=args.fetch_profiles
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

