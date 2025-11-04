"""
Document Loader - Loads documents from pending directory.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import csv

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentLoader:
    """Loads documents from pending directory."""
    
    def __init__(self, pending_dir: Optional[str] = None):
        self.pending_dir = Path(pending_dir or settings.PENDING_DIR)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_pending(
        self,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Load documents from pending directory.
        
        Args:
            recursive: Search subdirectories
            file_types: Filter by file extensions (e.g., ['pdf', 'txt'])
            
        Returns:
            List of dictionaries with 'file_path', 'file_type', and 'content' keys
        """
        logger.info(f"Loading documents from {self.pending_dir}")
        
        # Find files
        pattern = "**/*" if recursive else "*"
        all_files = list(self.pending_dir.glob(pattern))
        
        # Filter files
        all_files = [f for f in all_files if f.is_file() and f.name.lower() != 'readme.md']
        
        # Filter by file type if specified
        if file_types:
            file_types_lower = [ft.lower().lstrip('.') for ft in file_types]
            all_files = [
                f for f in all_files 
                if f.suffix.lower().lstrip('.') in file_types_lower
            ]
        
        logger.info(f"Found {len(all_files)} files to load")
        
        # Load file contents
        documents = []
        for file_path in all_files:
            try:
                doc = self._load_file(file_path)
                documents.append(doc)
                logger.info(f"✓ Loaded: {file_path.name} ({doc['file_type']})")
            except Exception as e:
                logger.error(f"✗ Failed to load {file_path.name}: {e}")
        
        logger.info(f"Successfully loaded {len(documents)} documents")
        return documents
    
    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load file content based on type."""
        file_type = file_path.suffix.lower().lstrip('.')
        
        doc = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_type': file_type,
            'content': None
        }
        
        # Text-based files
        if file_type in ['txt', 'md', 'markdown']:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc['content'] = f.read()
        
        # JSON files
        elif file_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                doc['content'] = json.load(f)
        
        # CSV files
        elif file_type == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                doc['content'] = list(reader)
        
        # PDF files
        elif file_type == 'pdf':
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(file_path))
                docs = loader.load()
                # Combine all pages into single content
                doc['content'] = "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load PDF {file_path.name}: {e}")
                doc['content'] = None
        
        # Word documents
        elif file_type in ['doc', 'docx']:
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(file_path))
                docs = loader.load()
                doc['content'] = "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load DOCX {file_path.name}: {e}")
                doc['content'] = None
        
        # Excel files
        elif file_type in ['xlsx', 'xls']:
            try:
                from langchain_community.document_loaders import UnstructuredExcelLoader
                loader = UnstructuredExcelLoader(str(file_path))
                docs = loader.load()
                doc['content'] = "\n\n".join([d.page_content for d in docs])
            except Exception as e:
                logger.error(f"Failed to load Excel {file_path.name}: {e}")
                doc['content'] = None
        
        # Unknown file types
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            doc['content'] = None
        
        return doc
