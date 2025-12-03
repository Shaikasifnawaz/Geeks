"""
Utility helper functions for the NCAAFB data pipeline.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from a file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary containing JSON data or None if file doesn't exist
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return None


def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path where to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def safe_get(data: Dict[str, Any], *keys, default=None):
    """
    Safely get nested dictionary values.
    
    Args:
        data: Dictionary to search
        *keys: Keys to traverse (e.g., 'key1', 'key2', 'key3')
        default: Default value if key path doesn't exist
        
    Returns:
        Value at the key path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current if current is not None else default


def normalize_string(value: Any) -> Optional[str]:
    """
    Normalize string values, handling None and empty strings.
    
    Args:
        value: Value to normalize
        
    Returns:
        Normalized string or None
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() if value.strip() else None
    return str(value).strip() if str(value).strip() else None


def normalize_int(value: Any) -> Optional[int]:
    """
    Normalize integer values, handling None and invalid values.
    
    Args:
        value: Value to normalize
        
    Returns:
        Integer or None
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_float(value: Any) -> Optional[float]:
    """
    Normalize float values, handling None and invalid values.
    
    Args:
        value: Value to normalize
        
    Returns:
        Float or None
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def normalize_date(value: Any) -> Optional[str]:
    """
    Normalize date values to ISO format string.
    
    Args:
        value: Date value (string, datetime, etc.)
        
    Returns:
        ISO format date string or None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip() if value.strip() else None
    return None


def get_project_root() -> str:
    """
    Get the project root directory (where backend folder is located).
    
    Returns:
        Path to project root
    """
    current_file = os.path.abspath(__file__)
    # Go up from utils/helpers.py -> utils/ -> backend/ -> project root
    backend_dir = os.path.dirname(os.path.dirname(current_file))
    # If we're already at project root level, return it
    if os.path.basename(backend_dir) == 'backend':
        return os.path.dirname(backend_dir)
    return backend_dir


def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to directory
    """
    os.makedirs(directory, exist_ok=True)


def normalize_uuid(value: Any) -> Optional[str]:
    """
    Normalize UUID values, handling None and invalid values.
    
    Args:
        value: Value to normalize (can be string UUID or None)
        
    Returns:
        UUID string or None
    """
    if value is None:
        return None
    if isinstance(value, str):
        # Try to validate it's a valid UUID format
        try:
            uuid.UUID(value)
            return value
        except (ValueError, AttributeError):
            return None
    return None


def convert_height_to_inches(height_str: Any) -> Optional[int]:
    """
    Convert height string to inches (INTEGER).
    
    Handles formats like:
    - "75" (already inches)
    - "6-3" (feet-inches)
    - "6'3\"" (feet-inches with quotes)
    
    Args:
        height_str: Height string or integer
        
    Returns:
        Height in inches as integer or None
    """
    if height_str is None:
        return None
    
    if isinstance(height_str, int):
        return height_str
    
    if isinstance(height_str, str):
        height_str = height_str.strip()
        
        # If it's just a number, assume inches
        if height_str.isdigit():
            return int(height_str)
        
        # Try to parse feet-inches format (e.g., "6-3", "6'3\"")
        if '-' in height_str:
            parts = height_str.split('-')
            if len(parts) == 2:
                try:
                    feet = int(parts[0].strip())
                    inches = int(parts[1].strip())
                    return (feet * 12) + inches
                except ValueError:
                    return None
        
        # Try format with quotes (e.g., "6'3\"")
        if "'" in height_str or '"' in height_str:
            import re
            match = re.match(r"(\d+)['\"](\d+)", height_str)
            if match:
                try:
                    feet = int(match.group(1))
                    inches = int(match.group(2))
                    return (feet * 12) + inches
                except ValueError:
                    return None
    
    return None

