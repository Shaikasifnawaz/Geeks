"""
Interactive script to create .env file with user input.
"""

import os
from pathlib import Path


def create_env_file():
    """Create .env file interactively."""
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / '.env'
    
    print("=" * 60)
    print("NCAAFB Backend - Environment Configuration Setup")
    print("=" * 60)
    print("\nThis script will help you create the .env configuration file.")
    print("All your API keys and database credentials will be stored here.\n")
    
    # Check if .env already exists
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled. Keeping existing .env file.")
            return
    
    # Get Sportradar API Key
    print("\n--- Sportradar API Configuration ---")
    api_key = input("Enter Sportradar API Key (or press Enter for default trial key): ").strip()
    if not api_key:
        api_key = "6dP4ysShCJmktrukYUWKueZNV9A6aL8tCU89ck2L"
        print(f"Using default trial key: {api_key}")
    
    # Get Database Configuration
    print("\n--- PostgreSQL Database Configuration ---")
    print("Enter your PostgreSQL connection details:")
    
    db_host = input("Database Host [localhost]: ").strip() or "localhost"
    db_port = input("Database Port [5432]: ").strip() or "5432"
    db_name = input("Database Name [ncaafb]: ").strip() or "ncaafb"
    db_user = input("Database User [postgres]: ").strip() or "postgres"
    
    print("\n⚠️  IMPORTANT: Enter your PostgreSQL password")
    print("   (This will be stored in .env file - keep it secure!)")
    db_password = input("Database Password: ").strip()
    
    if not db_password:
        print("⚠️  WARNING: No password provided. You may need to set it manually.")
        db_password = "postgres"
    
    # Create .env content
    env_content = f"""# Sportradar API Configuration
# Get your API key from: https://sportradar.com
SPORTRADAR_API_KEY={api_key}

# PostgreSQL Database Configuration
# Update these values to match your PostgreSQL setup
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("\n" + "=" * 60)
        print("✅ .env file created successfully!")
        print("=" * 60)
        print(f"\nLocation: {env_file}")
        print("\nConfiguration saved:")
        print(f"  - API Key: {api_key[:20]}...")
        print(f"  - Database: {db_user}@{db_host}:{db_port}/{db_name}")
        print("\n⚠️  SECURITY NOTE:")
        print("   - Keep your .env file secure and never commit it to git")
        print("   - The .env file is already in .gitignore")
        print("\n✅ You can now run the pipeline: python backend/main.py")
        
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")
        return False
    
    return True


if __name__ == "__main__":
    create_env_file()

