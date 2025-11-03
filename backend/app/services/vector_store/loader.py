"""
Document Loader - Loads documents from pending directory.
Simple, focused responsibility.
"""

from typing import List, Optional
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredExcelLoader,
)

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentLoader:
    """
    Loads documents from pending directory.
    Returns LangChain Document objects.
    """
    
    def __init__(self, pending_dir: Optional[str] = None):
        self.pending_dir = Path(pending_dir or settings.PENDING_DIR)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_pending(
        self,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[Document]:
        """
        Load all documents from pending directory.
        
        Args:
            recursive: Search subdirectories
            file_types: Filter by file extensions (e.g., ['pdf', 'txt'])
            
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"Loading documents from {self.pending_dir}")
        
        # Find files
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        all_files = list(self.pending_dir.glob(pattern))
        
        # Filter by file type if specified
        if file_types:
            file_types_lower = [ft.lower().lstrip('.') for ft in file_types]
            all_files = [
                f for f in all_files 
                if f.is_file() and f.suffix.lower().lstrip('.') in file_types_lower
            ]
        else:
            all_files = [f for f in all_files if f.is_file()]
        
        logger.info(f"Found {len(all_files)} files to load")
        
        # Load documents
        documents = []
        for file_path in all_files:
            try:
                docs = self._load_file(file_path)
                documents.extend(docs)
                logger.info(f"✓ Loaded: {file_path.name}")
            except Exception as e:
                logger.error(f"✗ Failed to load {file_path.name}: {e}")
        
        logger.info(f"Successfully loaded {len(documents)} documents")
        return documents
    
    def _load_file(self, file_path: Path) -> List[Document]:
        """Load a single file using appropriate LangChain loader."""
        suffix = file_path.suffix.lower()
        
        # Text files
        if suffix in ['.txt', '.md', '.markdown']:
            if suffix in ['.md', '.markdown']:
                # Prefer Markdown-aware loader; fallback to plain text if dependency missing
                try:
                    loader = UnstructuredMarkdownLoader(str(file_path))
                    return loader.load()
                except Exception as e:
                    logger.warning(f"Markdown loader unavailable ({e}); falling back to TextLoader")
                    loader = TextLoader(str(file_path))
                    return loader.load()
            else:
                loader = TextLoader(str(file_path))
                return loader.load()
        
        # PDF
        elif suffix == '.pdf':
            loader = PyPDFLoader(str(file_path))
            return loader.load()
        
        # Word documents
        elif suffix in ['.docx', '.doc']:
            loader = Docx2txtLoader(str(file_path))
            return loader.load()
        
        # CSV
        elif suffix == '.csv':
            loader = CSVLoader(str(file_path))
            return loader.load()
        
        # JSON
        elif suffix == '.json':
            loader = JSONLoader(
                file_path=str(file_path),
                jq_schema='.',
                text_content=False
            )
            return loader.load()
        
        # Excel
        elif suffix in ['.xlsx', '.xls']:
            loader = UnstructuredExcelLoader(str(file_path))
            return loader.load()
        
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            return []
