"""
Setup script to create .env file from template.
"""

import os
import shutil
from pathlib import Path


def setup_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    backend_dir = Path(__file__).parent.parent
    env_example = backend_dir / '.env.example'
    env_file = backend_dir / '.env'
    
    if env_file.exists():
        print(".env file already exists. Skipping creation.")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"Created .env file from .env.example")
        print(f"Please edit {env_file} with your configuration.")
    else:
        # Create basic .env file
        env_content = """# Sportradar API Configuration
SPORTRADAR_API_KEY=6dP4ysShCJmktrukYUWKueZNV9A6aL8tCU89ck2L

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ncaafb
DB_USER=postgres
DB_PASSWORD=postgres
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created .env file with default values.")
        print(f"Please edit {env_file} with your configuration.")


if __name__ == "__main__":
    setup_env_file()

