"""Utility functions for EasyPdfForYou."""

import os
import hashlib
from pathlib import Path
from typing import Union


def get_file_hash(filepath: Union[str, Path], algorithm: str = "md5") -> str:
    """Calculate hash of a file.
    
    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm (md5, sha1, sha256).
        
    Returns:
        Hex digest of the file hash.
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if not.
    
    Args:
        path: Directory path.
        
    Returns:
        Path object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_filename(filename: str) -> str:
    """Get a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Safe filename.
    """
    # Characters not allowed in Windows filenames
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200 - len(ext)] + ext
    
    return filename or "unnamed"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"