"""
Test script to verify database and API connections.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import psycopg2
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


def test_database_connection():
    """Test PostgreSQL database connection."""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    # Load .env file
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Please run: python backend/scripts/create_env.py")
        return False
    
    load_dotenv(env_path)
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': 'postgres',  # Connect to postgres DB first
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    if not db_config['password']:
        print("❌ DB_PASSWORD not found in .env file!")
        return False
    
    try:
        print(f"Connecting to {db_config['user']}@{db_config['host']}:{db_config['port']}...")
        conn = psycopg2.connect(**db_config)
        conn.close()
        print("✅ Database connection successful!")
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if PostgreSQL is running")
        print("  2. Verify credentials in backend/.env")
        print("  3. Check if PostgreSQL is listening on port", db_config['port'])
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_api_connection():
    """Test Sportradar API connection."""
    print("\n" + "=" * 60)
    print("Testing API Connection")
    print("=" * 60)
    
    # Load .env file
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    load_dotenv(env_path)
    
    api_key = os.getenv('SPORTRADAR_API_KEY')
    if not api_key:
        print("⚠️  SPORTRADAR_API_KEY not found, using default trial key")
        api_key = '6dP4ysShCJmktrukYUWKueZNV9A6aL8tCU89ck2L'
    
    url = "https://api.sportradar.com/ncaafb/trial/v7/en/league/teams.json"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key
    }
    
    try:
        print(f"Testing API connection to Sportradar...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API connection successful!")
            data = response.json()
            if 'teams' in data:
                print(f"   Found {len(data['teams'])} teams")
            return True
        elif response.status_code == 401:
            print("❌ API authentication failed - Invalid API key")
            return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
        print("   Check your internet connection")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 60)
    print("NCAAFB Backend - Connection Test")
    print("=" * 60)
    
    db_ok = test_database_connection()
    api_ok = test_api_connection()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"API:      {'✅ OK' if api_ok else '❌ FAILED'}")
    
    if db_ok and api_ok:
        print("\n✅ All tests passed! You can run the pipeline:")
        print("   python backend/main.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    print()


if __name__ == "__main__":
    main()

