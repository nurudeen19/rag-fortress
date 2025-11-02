"""
Document chunking service.
Chunks documents based on type and configuration.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.services.document_loader import Document, DocumentType
from app.config.settings import get_settings


@dataclass
class Chunk:
    """Simple chunk representation."""
    content: str
    metadata: Dict[str, Any]
    chunk_index: int


class DocumentChunker:
    """
    Chunks documents intelligently based on their type.
    
    - Text-based (TXT, MD, PDF, DOCX): Use character-based chunking with overlap
    - Structured (JSON, CSV, XLSX): Field-based chunking
    """
    
    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.chunking.chunk_size
        self.chunk_overlap = settings.chunking.chunk_overlap
    
    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Chunk a document based on its type.
        
        Args:
            document: Loaded document
            
        Returns:
            List[Chunk]: List of chunks
        """
        # Route to appropriate chunking strategy
        if document.doc_type in [DocumentType.TXT, DocumentType.MARKDOWN, 
                                  DocumentType.PDF, DocumentType.DOCX, DocumentType.PPTX]:
            return self._chunk_text(document)
        
        elif document.doc_type == DocumentType.JSON:
            return self._chunk_json(document)
        
        elif document.doc_type == DocumentType.CSV:
            return self._chunk_csv(document)
        
        elif document.doc_type == DocumentType.XLSX:
            return self._chunk_xlsx(document)
        
        else:
            # Fallback to text chunking
            return self._chunk_text(document)
    
    def _chunk_text(self, document: Document) -> List[Chunk]:
        """
        Chunk text-based documents using character-based splitting with overlap.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunks
        """
        text = document.content
        chunks = []
        
        # Simple character-based chunking
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence end
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                last_space = chunk_text.rfind(' ')
                
                # Use the best boundary we can find
                boundary = max(last_period, last_newline, last_space)
                if boundary > self.chunk_size // 2:  # Don't break too early
                    end = start + boundary + 1
                    chunk_text = text[start:end]
            
            if chunk_text.strip():  # Only add non-empty chunks
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": chunk_index,
                        "chunk_type": "text",
                        "start_char": start,
                        "end_char": end,
                    },
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _chunk_json(self, document: Document) -> List[Chunk]:
        """
        Chunk JSON documents by fields/objects.
        Each object or significant field becomes a chunk.
        """
        try:
            data = json.loads(document.content)
        except json.JSONDecodeError:
            # Fallback to text chunking if JSON is invalid
            return self._chunk_text(document)
        
        chunks = []
        chunk_index = 0
        
        def process_value(value: Any, path: str = "") -> None:
            nonlocal chunk_index
            
            if isinstance(value, dict):
                # Each dict object is a chunk
                chunks.append(Chunk(
                    content=json.dumps(value, indent=2),
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": chunk_index,
                        "chunk_type": "json_object",
                        "json_path": path,
                    },
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            elif isinstance(value, list):
                # Process list items
                for i, item in enumerate(value):
                    process_value(item, f"{path}[{i}]")
            
            else:
                # Primitive value - combine with path as context
                chunks.append(Chunk(
                    content=f"{path}: {value}",
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": chunk_index,
                        "chunk_type": "json_field",
                        "json_path": path,
                    },
                    chunk_index=chunk_index
                ))
                chunk_index += 1
        
        if isinstance(data, dict):
            for key, value in data.items():
                process_value(value, key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                process_value(item, f"[{i}]")
        else:
            process_value(data, "root")
        
        return chunks
    
    def _chunk_csv(self, document: Document) -> List[Chunk]:
        """
        Chunk CSV documents by rows.
        Each row (with header context) becomes a chunk.
        """
        lines = document.content.split('\n')
        if not lines:
            return []
        
        chunks = []
        header = lines[0] if lines else ""
        
        for i, line in enumerate(lines[1:], start=1):  # Skip header
            if line.strip():
                chunks.append(Chunk(
                    content=f"{header}\n{line}",
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": i - 1,
                        "chunk_type": "csv_row",
                        "row_number": i,
                    },
                    chunk_index=i - 1
                ))
        
        return chunks
    
    def _chunk_xlsx(self, document: Document) -> List[Chunk]:
        """
        Chunk Excel documents by sheets and rows.
        """
        lines = document.content.split('\n')
        chunks = []
        chunk_index = 0
        current_sheet = None
        sheet_header = None
        
        for line in lines:
            if line.startswith('Sheet:'):
                current_sheet = line.replace('Sheet:', '').strip()
                sheet_header = None  # Reset header for new sheet
            elif line.strip():
                if sheet_header is None:
                    sheet_header = line  # First row after sheet name is header
                else:
                    chunks.append(Chunk(
                        content=f"Sheet: {current_sheet}\n{sheet_header}\n{line}",
                        metadata={
                            **document.metadata,
                            "source": document.source,
                            "chunk_index": chunk_index,
                            "chunk_type": "xlsx_row",
                            "sheet_name": current_sheet,
                        },
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
        
        return chunks
