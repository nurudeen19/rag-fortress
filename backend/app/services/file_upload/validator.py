"""
File Validator Service - Validates file types, sizes, and extensions.
Handles MIME type checking and extension-based fallback validation.
"""

from typing import Tuple, Dict, Set

from app.core import get_logger


logger = get_logger(__name__)


# Supported file types with their MIME types and extensions
SUPPORTED_FORMATS: Dict[str, Set[str]] = {
    "json": {
        "mimes": {"application/json"},
        "extensions": {"json"}
    },
    "csv": {
        "mimes": {"text/csv", "application/csv"},
        "extensions": {"csv"}
    },
    "xlsx": {
        "mimes": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "extensions": {"xlsx"}
    },
    "xls": {
        "mimes": {"application/vnd.ms-excel", "application/x-ms-excel"},
        "extensions": {"xls"}
    },
    "pdf": {
        "mimes": {"application/pdf"},
        "extensions": {"pdf"}
    },
    "docx": {
        "mimes": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "extensions": {"docx"}
    },
    "doc": {
        "mimes": {"application/msword", "application/x-msword"},
        "extensions": {"doc"}
    },
    "txt": {
        "mimes": {"text/plain"},
        "extensions": {"txt"}
    },
    "md": {
        "mimes": {"text/markdown", "text/x-markdown", "application/x-markdown", "text/plain"},
        "extensions": {"md"}
    }
}


class FileValidator:
    """Validates uploaded files."""
    
    # Constants
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    @staticmethod
    def get_extension_from_filename(filename: str) -> str:
        """Extract file extension from filename."""
        if not filename or "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()
    
    @staticmethod
    def is_extension_supported(filename: str) -> Tuple[bool, str]:
        """
        Check if file extension is supported.
        
        Returns:
            Tuple[bool, str] - (is_supported, file_type)
        """
        ext = FileValidator.get_extension_from_filename(filename)
        if not ext:
            return False, ""
        
        for file_type, config in SUPPORTED_FORMATS.items():
            if ext in config["extensions"]:
                return True, file_type
        
        return False, ""
    
    @staticmethod
    def is_mime_type_supported(mime_type: str) -> Tuple[bool, str]:
        """
        Check if MIME type is supported.
        
        Returns:
            Tuple[bool, str] - (is_supported, file_type)
        """
        mime_type = mime_type.lower() if mime_type else ""
        
        for file_type, config in SUPPORTED_FORMATS.items():
            if mime_type in config["mimes"]:
                return True, file_type
        
        return False, ""
    
    @staticmethod
    def validate_file(
        filename: str,
        file_size: int,
        mime_type: str = ""
    ) -> Tuple[bool, str, str]:
        """
        Validate file comprehensively.
        
        Returns:
            Tuple[bool, str, str] - (is_valid, error_message, file_type)
        """
        # Check filename
        if not filename:
            return False, "File name is required", ""
        
        # Check file size
        if file_size == 0:
            return False, "File is empty", ""
        
        if file_size > FileValidator.MAX_FILE_SIZE:
            return False, f"File exceeds {FileValidator.MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit", ""
        
        # Try MIME type first (primary validation)
        is_mime_valid, file_type = FileValidator.is_mime_type_supported(mime_type)
        if is_mime_valid:
            return True, "", file_type
        
        # Fallback to extension-based validation
        is_ext_valid, file_type = FileValidator.is_extension_supported(filename)
        if is_ext_valid:
            logger.debug(f"File {filename} validated by extension (MIME: {mime_type})")
            return True, "", file_type
        
        # Both validations failed
        supported_exts = ", ".join(
            ext for config in SUPPORTED_FORMATS.values() for ext in config["extensions"]
        )
        return False, f"File type not supported. Allowed: {supported_exts}", ""
    
    @staticmethod
    def get_supported_extensions() -> list:
        """Get list of all supported extensions."""
        extensions = []
        for config in SUPPORTED_FORMATS.values():
            extensions.extend(config["extensions"])
        return sorted(list(set(extensions)))
    
    @staticmethod
    def get_supported_mime_types() -> Dict[str, Set[str]]:
        """Get dict of file types and their MIME types."""
        return {
            file_type: config["mimes"]
            for file_type, config in SUPPORTED_FORMATS.items()
        }
