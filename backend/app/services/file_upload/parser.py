"""
Structured Data Parser - Extracts fields from JSON, CSV, and Excel files.
Handles field detection for field_selection in document uploads.
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core import get_logger


logger = get_logger(__name__)


class StructuredDataParser:
    """Parses structured data files to extract fields."""
    
    @staticmethod
    def parse_json(file_path: str) -> List[str]:
        """
        Extract field names from JSON file.
        Supports both array of objects and single object.
        
        Returns:
            List of unique field names
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            fields = set()
            
            if isinstance(data, list):
                # Array of objects
                for item in data:
                    if isinstance(item, dict):
                        fields.update(item.keys())
            elif isinstance(data, dict):
                # Single object
                fields.update(data.keys())
            
            return sorted(list(fields))
        
        except Exception as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_csv(file_path: str, max_rows: int = 100) -> List[str]:
        """
        Extract field names (column headers) from CSV file.
        
        Args:
            file_path: Path to CSV file
            max_rows: Max rows to read for dialect detection
        
        Returns:
            List of column names
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect CSV dialect
                sample = f.read(min(max_rows * 100, 8192))
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                f.seek(0)
                
                reader = csv.reader(f, dialect)
                headers = next(reader)
                
                return [h.strip() for h in headers if h.strip()]
        
        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {e}")
            raise
    
    @staticmethod
    def parse_excel(file_path: str) -> List[str]:
        """
        Extract field names from Excel file.
        Uses first row as headers, first sheet.
        
        Returns:
            List of column names
        """
        try:
            import openpyxl
            
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet = workbook.active
            
            headers = []
            for cell in sheet[1]:
                value = cell.value
                if value:
                    headers.append(str(value).strip())
            
            workbook.close()
            return headers
        
        except ImportError:
            logger.error("openpyxl not installed. Cannot parse Excel files.")
            raise
        except Exception as e:
            logger.error(f"Failed to parse Excel file {file_path}: {e}")
            raise
    
    @staticmethod
    def extract_fields(
        file_path: str,
        file_type: str
    ) -> List[str]:
        """
        Extract fields from structured data file.
        
        Args:
            file_path: Relative path (e.g., "uploaded/file.csv") or full path
            file_type: Type of file (json, csv, excel)
        
        Returns:
            List of field names
        """
        # Resolve path
        if not os.path.isabs(file_path):
            base_dir = os.getenv("FILES_DIR", "data/files")
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path
        
        path = Path(full_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        
        if file_type == "json":
            fields = StructuredDataParser.parse_json(full_path)
        elif file_type == "csv":
            fields = StructuredDataParser.parse_csv(full_path)
        elif file_type in ("xlsx", "xls"):
            fields = StructuredDataParser.parse_excel(full_path)
        else:
            raise ValueError(f"Unsupported file type for parsing: {file_type}")
        
        logger.info(f"Extracted {len(fields)} fields from {path.name} ({file_type})")
        return fields
    
    @staticmethod
    def validate_field_selection(
        fields: List[str],
        selected_fields: Optional[List[str]]
    ) -> List[str]:
        """
        Validate that selected fields exist in file.
        Returns only valid selected fields.
        
        Args:
            fields: Available fields in file
            selected_fields: Fields user wants to extract
        
        Returns:
            List of valid selected fields
        """
        if not selected_fields:
            return []
        
        valid_fields = [f for f in selected_fields if f in fields]
        invalid_fields = [f for f in selected_fields if f not in fields]
        
        if invalid_fields:
            logger.warning(f"Invalid field selection: {invalid_fields}")
        
        return valid_fields
