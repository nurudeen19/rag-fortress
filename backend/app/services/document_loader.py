"""
Document loader service.
Loads documents and determines appropriate processor based on file type.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from app.core.exceptions import DocumentError


class DocumentType(str, Enum):
    """Supported document types."""
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"


class Document:
    """Represents a loaded document."""
    
    def __init__(
        self,
        content: str,
        doc_type: DocumentType,
        metadata: Dict[str, Any],
        source: str
    ):
        self.content = content
        self.doc_type = doc_type
        self.metadata = metadata
        self.source = source


class DocumentLoader:
    """
    Loads documents from various file types.
    Simple, focused on just loading the content.
    """
    
    @staticmethod
    def load(file_path: str) -> Document:
        """
        Load a document from file path.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Document: Loaded document with content and metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise DocumentError(f"File not found: {file_path}")
        
        # Determine document type from extension
        extension = path.suffix.lower().lstrip('.')
        try:
            doc_type = DocumentType(extension)
        except ValueError:
            raise DocumentError(f"Unsupported file type: {extension}")
        
        # Load content based on type
        if doc_type == DocumentType.TXT:
            content = DocumentLoader._load_txt(path)
        elif doc_type == DocumentType.MARKDOWN:
            content = DocumentLoader._load_txt(path)  # Same as txt
        elif doc_type == DocumentType.PDF:
            content = DocumentLoader._load_pdf(path)
        elif doc_type == DocumentType.DOCX:
            content = DocumentLoader._load_docx(path)
        elif doc_type == DocumentType.JSON:
            content = DocumentLoader._load_json(path)
        elif doc_type == DocumentType.CSV:
            content = DocumentLoader._load_csv(path)
        elif doc_type == DocumentType.XLSX:
            content = DocumentLoader._load_xlsx(path)
        elif doc_type == DocumentType.PPTX:
            content = DocumentLoader._load_pptx(path)
        else:
            raise DocumentError(f"No loader implemented for: {doc_type}")
        
        # Basic metadata
        metadata = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_type": doc_type.value,
        }
        
        return Document(
            content=content,
            doc_type=doc_type,
            metadata=metadata,
            source=str(path)
        )
    
    @staticmethod
    def _load_txt(path: Path) -> str:
        """Load plain text file."""
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            return path.read_text(encoding='latin-1')
    
    @staticmethod
    def _load_pdf(path: Path) -> str:
        """Load PDF file."""
        try:
            from pypdf2 import PdfReader
        except ImportError:
            raise DocumentError("pypdf2 not installed. Install with: pip install pypdf2")
        
        try:
            reader = PdfReader(str(path))
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n\n".join(text)
        except Exception as e:
            raise DocumentError(f"Failed to load PDF: {e}")
    
    @staticmethod
    def _load_docx(path: Path) -> str:
        """Load DOCX file."""
        try:
            from docx import Document as DocxDocument
        except ImportError:
            raise DocumentError("python-docx not installed. Install with: pip install python-docx")
        
        try:
            doc = DocxDocument(str(path))
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n\n".join(text)
        except Exception as e:
            raise DocumentError(f"Failed to load DOCX: {e}")
    
    @staticmethod
    def _load_json(path: Path) -> str:
        """
        Load JSON file.
        Returns as formatted string for now.
        """
        import json
        try:
            data = json.loads(path.read_text())
            # Return pretty-printed JSON
            return json.dumps(data, indent=2)
        except Exception as e:
            raise DocumentError(f"Failed to load JSON: {e}")
    
    @staticmethod
    def _load_csv(path: Path) -> str:
        """
        Load CSV file.
        Returns as formatted string for now.
        """
        try:
            import csv
            rows = []
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(' | '.join(row))
            return '\n'.join(rows)
        except Exception as e:
            raise DocumentError(f"Failed to load CSV: {e}")
    
    @staticmethod
    def _load_xlsx(path: Path) -> str:
        """Load Excel file."""
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise DocumentError("openpyxl not installed. Install with: pip install openpyxl")
        
        try:
            wb = load_workbook(str(path))
            text = []
            for sheet in wb.worksheets:
                text.append(f"Sheet: {sheet.title}")
                for row in sheet.iter_rows(values_only=True):
                    text.append(' | '.join(str(cell) if cell else '' for cell in row))
            return '\n'.join(text)
        except Exception as e:
            raise DocumentError(f"Failed to load XLSX: {e}")
    
    @staticmethod
    def _load_pptx(path: Path) -> str:
        """Load PowerPoint file."""
        try:
            from pptx import Presentation
        except ImportError:
            raise DocumentError("python-pptx not installed. Install with: pip install python-pptx")
        
        try:
            prs = Presentation(str(path))
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return '\n\n'.join(text)
        except Exception as e:
            raise DocumentError(f"Failed to load PPTX: {e}")
