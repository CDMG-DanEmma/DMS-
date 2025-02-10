import os
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Optional, Union, Any
import logging
from config import JOB_FOLDER_PATTERN, FILE_TYPES, METADATA_FIELDS

logger = logging.getLogger('app.utils')

def validate_job_folder(folder_path: str) -> bool:
    """
    Validate that a folder name matches the required 1YY###-PH pattern.
    
    Args:
        folder_path (str): Path to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        folder_name = os.path.basename(folder_path)
        return bool(re.match(JOB_FOLDER_PATTERN, folder_name))
    except Exception as e:
        logger.error(f"Error validating job folder {folder_path}: {e}")
        return False

def get_file_type(file_path: str) -> str:
    """
    Determine file type from extension using predefined mapping.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Mapped file type or 'OTHER' if unknown
    """
    try:
        extension = os.path.splitext(file_path)[1].lower()
        return FILE_TYPES.get(extension, 'OTHER')
    except Exception as e:
        logger.error(f"Error getting file type for {file_path}: {e}")
        return 'OTHER'

def format_timestamp(timestamp: Union[str, datetime]) -> str:
    """
    Format a timestamp consistently for display.
    
    Args:
        timestamp (Union[str, datetime]): Timestamp to format
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return str(timestamp)

def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get the relative path from a base directory.
    
    Args:
        file_path (str): Full path to file
        base_path (str): Base directory path
        
    Returns:
        str: Relative path
    """
    try:
        return str(Path(file_path).relative_to(base_path))
    except Exception as e:
        logger.error(f"Error getting relative path for {file_path}: {e}")
        return file_path

def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate and clean metadata fields.
    
    Args:
        metadata (Dict[str, Any]): Raw metadata dictionary
        
    Returns:
        Dict[str, str]: Cleaned metadata with invalid fields removed
    """
    cleaned = {}
    try:
        for field in METADATA_FIELDS:
            value = metadata.get(field)
            if value:
                # Strip whitespace and ensure string type
                cleaned[field] = str(value).strip()
    except Exception as e:
        logger.error(f"Error validating metadata: {e}")
    return cleaned

def calculate_file_stats(file_paths: List[str]) -> Dict[str, int]:
    """
    Calculate statistics about a list of files.
    
    Args:
        file_paths (List[str]): List of file paths
        
    Returns:
        Dict[str, int]: Statistics including counts by file type
    """
    stats = {'total': len(file_paths), 'by_type': {}}
    try:
        for path in file_paths:
            file_type = get_file_type(path)
            stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
    except Exception as e:
        logger.error(f"Error calculating file statistics: {e}")
    return stats

def ensure_directory(directory: Union[str, Path]) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (Union[str, Path]): Directory path
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error ensuring directory {directory}: {e}")
        return False

def is_file_readable(file_path: str) -> bool:
    """
    Check if a file exists and is readable.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        bool: True if file is readable
    """
    try:
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception as e:
        logger.error(f"Error checking file readability for {file_path}: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """
    Remove or replace invalid characters in a filename.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    try:
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    except Exception as e:
        logger.error(f"Error sanitizing filename {filename}: {e}")
        return filename

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    try:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    except Exception as e:
        logger.error(f"Error formatting file size {size_bytes}: {e}")
        return f"{size_bytes} B"

def parse_revision(filename: str) -> Optional[str]:
    """
    Attempt to extract revision information from filename.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        Optional[str]: Extracted revision or None if not found
    """
    try:
        # Common revision patterns (e.g., "REV A", "R1", "V2.0")
        patterns = [
            r'REV\s*([A-Z0-9]+)',
            r'R(\d+)',
            r'V(\d+(\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename.upper())
            if match:
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error parsing revision from {filename}: {e}")
        return None