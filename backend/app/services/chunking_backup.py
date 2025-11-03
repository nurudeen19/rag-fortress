"""
Document chunking service.
Chunks documents and returns LangChain Documents.
"""

import json
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document as LangChainDocument

from app.services.document_loader import Document, DocumentType
from app.config.settings import get_settings


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
    
    def chunk_document(
        self, 
        document: Document,
        fields_to_keep: Optional[List[str]] = None,
        json_flatten: bool = True
    ) -> List[LangChainDocument]:
        """
        Chunk a document based on its type.
        Returns LangChain Document objects ready for vector store ingestion.
        
        Args:
            document: Loaded document
            fields_to_keep: For structured data (JSON, CSV, XLSX), list of fields/columns to keep.
                           If None, keeps all fields.
                           Examples:
                           - JSON: ["name", "company", "address.city"]
                           - CSV/XLSX: ["Name", "Email", "Department"]
            json_flatten: For JSON documents, whether to flatten nested objects.
                         Default: True
            
        Returns:
            List[LangChainDocument]: List of LangChain Document chunks
            
        Example:
            # Filter JSON fields
            chunks = chunker.chunk_document(
                json_doc, 
                fields_to_keep=["name", "company", "city"]
            )
            
            # Ready to pass to vector store
            vector_store.add_documents(chunks)
        """
        # Route to appropriate chunking strategy
        if document.doc_type in [DocumentType.TXT, DocumentType.MARKDOWN, 
                                  DocumentType.PDF, DocumentType.DOCX, DocumentType.PPTX]:
            return self._chunk_text(document)
        
        elif document.doc_type == DocumentType.JSON:
            return self._chunk_json(document, fields_to_keep, json_flatten)
        
        elif document.doc_type == DocumentType.CSV:
            return self._chunk_csv(document, fields_to_keep)
        
        elif document.doc_type == DocumentType.XLSX:
            return self._chunk_xlsx(document, fields_to_keep)
        
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
                chunks.append(LangChainDocument(page_content=
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
    
    def _chunk_json(
        self, 
        document: Document, 
        fields_to_keep: Optional[List[str]] = None,
        flatten: bool = True
    ) -> List[Chunk]:
        """
        Chunk JSON documents with optional field filtering and flattening.
        
        Args:
            document: JSON document to chunk
            fields_to_keep: List of fields to keep (e.g., ["name", "company", "city"]).
                           If None, keeps all fields.
            flatten: If True, flattens nested objects into key-value pairs.
                    If False, keeps original JSON structure.
        
        Returns:
            List of chunks with filtered and/or flattened content
        
        Examples:
            # Filter and flatten
            Input: {"name": "John", "age": 30, "address": {"city": "SF", "zip": "94102"}}
            fields_to_keep: ["name", "address.city"]
            Output: "name: John\naddress.city: SF"
            
            # Keep all, flatten
            Input: {"name": "John", "address": {"city": "SF"}}
            fields_to_keep: None
            Output: "name: John\naddress.city: SF"
        """
        try:
            data = json.loads(document.content)
        except json.JSONDecodeError:
            # Fallback to text chunking if JSON is invalid
            return self._chunk_text(document)
        
        chunks = []
        chunk_index = 0
        
        # Handle list of objects (common in JSON files)
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    flattened = self._flatten_json_object(item, fields_to_keep, flatten)
                    if flattened:  # Only add non-empty chunks
                        chunks.append(LangChainDocument(page_content=
                            content=flattened,
                            metadata={
                                **document.metadata,
                                "source": document.source,
                                "chunk_index": chunk_index,
                                "chunk_type": "json_object",
                                "array_index": i,
                            },
                            chunk_index=chunk_index
                        ))
                        chunk_index += 1
                else:
                    # Primitive in array
                    chunks.append(LangChainDocument(page_content=
                        content=str(item),
                        metadata={
                            **document.metadata,
                            "source": document.source,
                            "chunk_index": chunk_index,
                            "chunk_type": "json_primitive",
                            "array_index": i,
                        },
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
        
        # Handle single object
        elif isinstance(data, dict):
            flattened = self._flatten_json_object(data, fields_to_keep, flatten)
            if flattened:
                chunks.append(LangChainDocument(page_content=
                    content=flattened,
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": chunk_index,
                        "chunk_type": "json_object",
                    },
                    chunk_index=chunk_index
                ))
        
        # Handle primitive value
        else:
            chunks.append(LangChainDocument(page_content=
                content=str(data),
                metadata={
                    **document.metadata,
                    "source": document.source,
                    "chunk_index": 0,
                    "chunk_type": "json_primitive",
                },
                chunk_index=0
            ))
        
        return chunks if chunks else self._chunk_text(document)
    
    def _flatten_json_object(
        self, 
        obj: Dict[str, Any], 
        fields_to_keep: Optional[List[str]] = None,
        flatten: bool = True,
        parent_key: str = ""
    ) -> str:
        """
        Flatten a JSON object into key-value pairs with optional field filtering.
        
        Args:
            obj: Dictionary to flatten
            fields_to_keep: List of field paths to keep (e.g., ["name", "address.city"])
            flatten: Whether to flatten nested objects
            parent_key: Current parent key for nested objects
        
        Returns:
            Flattened string representation
        """
        items = []
        
        for key, value in obj.items():
            # Build full key path
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            # Check if we should keep this field
            if fields_to_keep is not None:
                # Check exact match or prefix match (for nested fields)
                should_keep = any(
                    full_key == field or 
                    full_key.startswith(field + ".") or
                    field.startswith(full_key + ".")
                    for field in fields_to_keep
                )
                if not should_keep:
                    continue
            
            # Process the value
            if isinstance(value, dict) and flatten:
                # Recursively flatten nested objects
                nested = self._flatten_json_object(value, fields_to_keep, flatten, full_key)
                if nested:
                    items.append(nested)
            elif isinstance(value, list):
                # Handle arrays
                if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                    # Array of primitives - join them
                    items.append(f"{full_key}: {', '.join(map(str, value))}")
                else:
                    # Array of objects - flatten each
                    for i, item in enumerate(value):
                        if isinstance(item, dict) and flatten:
                            nested = self._flatten_json_object(item, fields_to_keep, flatten, f"{full_key}[{i}]")
                            if nested:
                                items.append(nested)
                        else:
                            items.append(f"{full_key}[{i}]: {item}")
            elif isinstance(value, dict):
                # Keep original JSON structure if not flattening
                items.append(f"{full_key}: {json.dumps(value)}")
            else:
                # Primitive value
                items.append(f"{full_key}: {value}")
        
        return "\n".join(items)
    
    
    def _chunk_csv(
        self, 
        document: Document, 
        fields_to_keep: Optional[List[str]] = None
    ) -> List[Chunk]:
        """
        Chunk CSV documents by rows with optional column filtering.
        Each row (with header context) becomes a chunk.
        
        Args:
            document: CSV document
            fields_to_keep: List of column names to keep (case-sensitive).
                           If None, keeps all columns.
                           Example: ["Name", "Email", "Department"]
        
        Returns:
            List of chunks with filtered columns
        """
        lines = document.content.split('\n')
        if not lines:
            return []
        
        chunks = []
        header_line = lines[0] if lines else ""
        
        # Parse header to get column names
        header_columns = [col.strip() for col in header_line.split('|')]
        header_columns = [col for col in header_columns if col]  # Remove empty
        
        # Determine which columns to keep
        if fields_to_keep is not None:
            # Find indices of columns to keep
            indices_to_keep = []
            filtered_headers = []
            
            for i, col in enumerate(header_columns):
                if col in fields_to_keep:
                    indices_to_keep.append(i)
                    filtered_headers.append(col)
            
            if not indices_to_keep:
                # No matching columns found, return empty
                return []
            
            filtered_header = ' | '.join(filtered_headers)
        else:
            # Keep all columns
            indices_to_keep = list(range(len(header_columns)))
            filtered_header = header_line
        
        # Process rows
        for i, line in enumerate(lines[1:], start=1):  # Skip header
            if line.strip():
                # Parse row
                row_values = [val.strip() for val in line.split('|')]
                row_values = [val for val in row_values if val]  # Remove empty
                
                # Filter columns
                if fields_to_keep is not None:
                    filtered_values = [
                        row_values[idx] for idx in indices_to_keep 
                        if idx < len(row_values)
                    ]
                    filtered_row = ' | '.join(filtered_values)
                else:
                    filtered_row = line
                
                # Create chunk with filtered content
                chunks.append(LangChainDocument(page_content=
                    content=f"{filtered_header}\n{filtered_row}",
                    metadata={
                        **document.metadata,
                        "source": document.source,
                        "chunk_index": i - 1,
                        "chunk_type": "csv_row",
                        "row_number": i,
                        "columns_kept": filtered_headers if fields_to_keep else header_columns,
                    },
                    chunk_index=i - 1
                ))
        
        return chunks
    
    
    def _chunk_xlsx(
        self, 
        document: Document, 
        fields_to_keep: Optional[List[str]] = None
    ) -> List[Chunk]:
        """
        Chunk Excel documents by sheets and rows with optional column filtering.
        
        Args:
            document: XLSX document
            fields_to_keep: List of column names to keep (case-sensitive).
                           If None, keeps all columns.
                           Example: ["Name", "Email", "Department"]
        
        Returns:
            List of chunks with filtered columns
        """
        lines = document.content.split('\n')
        chunks = []
        chunk_index = 0
        current_sheet = None
        sheet_header = None
        header_columns = []
        indices_to_keep = []
        filtered_headers = []
        
        for line in lines:
            if line.startswith('Sheet:'):
                # New sheet
                current_sheet = line.replace('Sheet:', '').strip()
                sheet_header = None  # Reset header for new sheet
                header_columns = []
                indices_to_keep = []
                filtered_headers = []
                
            elif line.strip():
                if sheet_header is None:
                    # This is the header row
                    sheet_header = line
                    header_columns = [col.strip() for col in line.split('|')]
                    header_columns = [col for col in header_columns if col]
                    
                    # Determine which columns to keep
                    if fields_to_keep is not None:
                        for i, col in enumerate(header_columns):
                            if col in fields_to_keep:
                                indices_to_keep.append(i)
                                filtered_headers.append(col)
                        
                        if not indices_to_keep:
                            # No matching columns in this sheet, skip to next sheet
                            continue
                    else:
                        # Keep all columns
                        indices_to_keep = list(range(len(header_columns)))
                        filtered_headers = header_columns
                        
                else:
                    # Data row
                    row_values = [val.strip() for val in line.split('|')]
                    row_values = [val for val in row_values if val]
                    
                    # Filter columns
                    if fields_to_keep is not None and indices_to_keep:
                        filtered_values = [
                            row_values[idx] for idx in indices_to_keep 
                            if idx < len(row_values)
                        ]
                        filtered_row = ' | '.join(filtered_values)
                        filtered_header = ' | '.join(filtered_headers)
                    else:
                        filtered_row = line
                        filtered_header = sheet_header
                    
                    # Create chunk
                    chunks.append(LangChainDocument(page_content=
                        content=f"Sheet: {current_sheet}\n{filtered_header}\n{filtered_row}",
                        metadata={
                            **document.metadata,
                            "source": document.source,
                            "chunk_index": chunk_index,
                            "chunk_type": "xlsx_row",
                            "sheet_name": current_sheet,
                            "columns_kept": filtered_headers if fields_to_keep else header_columns,
                        },
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
        
        return chunks
