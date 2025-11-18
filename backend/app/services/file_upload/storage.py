"""
File Storage Service - Handles file disk I/O and cleanup.
Manages file saving, hashing, and deletion from disk.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional

from app.core import get_logger


logger = get_logger(__name__)


class FileStorage:
    """Manages file storage operations on disk."""
    
    def __init__(self, upload_dir: Optional[str] = None):
        """
        Initialize storage service.
        
        Args:
            upload_dir: Directory for file uploads. Uses UPLOAD_DIR env var or default.
        """
        self.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "data/uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"File storage initialized at: {self.upload_dir}")
    
    async def save_file(self, filename: str, content: bytes) -> str:
        """
        Save file to disk.
        
        Args:
            filename: Original filename
            content: File content as bytes
        
        Returns:
            Full path to saved file
        """
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            # Prevent directory traversal
            real_path = Path(file_path).resolve()
            upload_dir_path = Path(self.upload_dir).resolve()
            if not str(real_path).startswith(str(upload_dir_path)):
                raise ValueError(f"Invalid file path: {filename}")
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Saved file to: {file_path} ({len(content)} bytes)")
            return file_path
        
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk.
        
        Args:
            file_path: Full path to file
        
        Returns:
            True if deleted, False if file not found
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()
    
    @staticmethod
    async def calculate_hash(file_path: str) -> str:
        """
        Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
    
    @staticmethod
    async def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        return Path(file_path).stat().st_size
