"""
File utility functions for handling document files.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from ..config import settings


def validate_file(file_path: str) -> bool:
    """
    Validate if a file can be processed.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is valid
    """
    if not os.path.exists(file_path):
        return False
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_path} ({file_size} bytes)")
        return False
    
    # Check file extension
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {file_path}")
        return False
    
    return True


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    
    return {
        "filename": path_obj.name,
        "file_path": str(path_obj.absolute()),
        "file_size": path_obj.stat().st_size,
        "file_extension": path_obj.suffix.lower(),
        "file_hash": file_hash,
        "created_time": path_obj.stat().st_ctime,
        "modified_time": path_obj.stat().st_mtime,
        "is_readable": os.access(file_path, os.R_OK),
        "is_writable": os.access(file_path, os.W_OK)
    }


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        File hash string
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified age.
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of files cleaned
    """
    import time
    
    cleaned_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to clean up {file_path}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Failed to clean up directory {directory}: {str(e)}")
    
    return cleaned_count


def create_temp_file(original_path: str, suffix: str = "") -> str:
    """
    Create a temporary copy of a file.
    
    Args:
        original_path: Path to original file
        suffix: Optional suffix for temp file
        
    Returns:
        Path to temporary file
    """
    import tempfile
    
    temp_dir = Path(settings.UPLOAD_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    original_name = Path(original_path).name
    temp_name = f"temp_{original_name}{suffix}"
    temp_path = temp_dir / temp_name
    
    shutil.copy2(original_path, temp_path)
    
    return str(temp_path)


def move_file_to_processed(source_path: str, filename: str) -> str:
    """
    Move a file to the processed directory.
    
    Args:
        source_path: Source file path
        filename: Target filename
        
    Returns:
        Path to moved file
    """
    processed_dir = Path(settings.PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = processed_dir / filename
    
    # Handle filename conflicts
    counter = 1
    original_name = target_path.stem
    original_suffix = target_path.suffix
    
    while target_path.exists():
        target_path = processed_dir / f"{original_name}_{counter}{original_suffix}"
        counter += 1
    
    shutil.move(source_path, target_path)
    
    return str(target_path)


def get_supported_formats() -> list:
    """Get list of supported file formats."""
    return settings.ALLOWED_EXTENSIONS


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}" 