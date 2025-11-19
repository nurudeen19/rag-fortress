"""
File Storage Service - Handles file disk I/O and cleanup.
Manages file saving, hashing, and deletion from disk.
Uses unified structure: data/files/{category}/
"""

import os
import hashlib
from pathlib import Path
from typing import Optional

from app.core import get_logger


logger = get_logger(__name__)


class FileStorage:
    """Manages file storage operations on disk with category-based subdirectories.
    
    Unified structure: data/files/{category}/
    Categories: uploaded, knowledge_base, processing, archive
    """
    
    # Valid storage categories
    CATEGORIES = {"uploaded", "knowledge_base", "processing", "archive"}
    
    def __init__(self, base_dir: Optional[str] = None, category: str = "uploaded"):
        """
        Initialize storage service.
        
        Args:
            base_dir: Base directory for files. Uses FILES_DIR env var or default to data/files.
            category: Category subdirectory (uploaded, knowledge_base, processing, archive).
        
        Raises:
            ValueError: If category is not valid.
        """
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {self.CATEGORIES}")
        
        base_path = base_dir or os.getenv("FILES_DIR", "data/files")
        self.category = category
        self.base_dir = base_path
        self.storage_dir = os.path.join(base_path, category)
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"File storage initialized: {self.storage_dir}")
    
    async def save_file(self, filename: str, content: bytes) -> str:
        """
        Save file to disk in the category subdirectory.
        
        Args:
            filename: Original filename
            content: File content as bytes
        
        Returns:
            Relative path from data/files/ (e.g., "uploaded/filename.pdf")
        """
        try:
            file_path = os.path.join(self.storage_dir, filename)
            
            # Prevent directory traversal
            real_path = Path(file_path).resolve()
            storage_dir_path = Path(self.storage_dir).resolve()
            if not str(real_path).startswith(str(storage_dir_path)):
                raise ValueError(f"Invalid file path: {filename}")
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Return relative path from base files directory
            rel_path = os.path.join(self.category, filename)
            logger.info(f"Saved file: {rel_path} ({len(content)} bytes)")
            return rel_path
        
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise
    
    async def delete_file(self, rel_file_path: str) -> bool:
        """
        Delete file from disk.
        
        Args:
            rel_file_path: Relative path from data/files/ (e.g., "uploaded/filename.pdf")
        
        Returns:
            True if deleted, False if file not found
        """
        try:
            # Construct full path
            full_path = os.path.join(self.base_dir, rel_file_path)
            path = Path(full_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {rel_file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {rel_file_path}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to delete file {rel_file_path}: {e}")
            raise
    
    async def file_exists(self, rel_file_path: str) -> bool:
        """Check if file exists.
        
        Args:
            rel_file_path: Relative path from data/files/ (e.g., "uploaded/filename.pdf")
        """
        full_path = os.path.join(self.base_dir, rel_file_path)
        return Path(full_path).exists()
    
    @staticmethod
    async def calculate_hash(file_path: str, base_dir: str = "data/files") -> str:
        """
        Calculate SHA-256 hash of file.
        
        Args:
            file_path: Relative path (e.g., "uploaded/filename.pdf") or full path
            base_dir: Base directory for resolving relative paths
        
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        try:
            # If relative path, construct full path
            if not os.path.isabs(file_path):
                full_path = os.path.join(base_dir, file_path)
            else:
                full_path = file_path
            
            with open(full_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
    
    @staticmethod
    async def get_file_size(file_path: str, base_dir: str = "data/files") -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Relative path (e.g., "uploaded/filename.pdf") or full path
            base_dir: Base directory for resolving relative paths
        """
        if not os.path.isabs(file_path):
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path
        return Path(full_path).stat().st_size
