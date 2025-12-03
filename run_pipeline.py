#!/usr/bin/env python3
"""
Script to run the complete NCAAFB data pipeline.
This script fetches data from SportsRadar API and populates the database.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the complete ETL pipeline."""
    try:
        from backend.main import run_etl_pipeline
        
        print("Starting NCAAFB Data Pipeline...")
        print("=" * 50)
        
        # Run the pipeline with all teams
        success = run_etl_pipeline(
            year=2025,
            season_type="REG",
            create_schema=True,
            max_teams=None,  # Fetch all teams
            fetch_player_profiles=False  # Skip individual player profiles for faster execution
        )
        
        if success:
            print("\nPipeline completed successfully!")
            print("Your database should now be populated with data from SportsRadar.")
            print("You can now redeploy your services on Render to see the data in your frontend.")
        else:
            print("\nPipeline failed. Check the logs above for details.")
            return 1
            
    except Exception as e:
        print(f"Error running pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())