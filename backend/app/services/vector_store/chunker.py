"""
Document Chunker - Chunks documents using LangChain splitters.
Receives documents from DocumentLoader with enriched metadata.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentChunker:
    """Chunks documents from loader, returns LangChain Documents with enriched metadata."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        logger.info(
            f"Chunker initialized: chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def chunk_loaded_files(self, files: List[Dict[str, Any]]) -> List[Document]:
        """
        Process files from DocumentLoader.
        
        Args:
            files: List from loader with keys: file_id, file_name, file_type, content, meta
        
        Returns:
            List[Document]: Chunked documents with enriched metadata
        """
        if not files:
            return []

        all_docs: List[Document] = []
        for file_data in files:
            try:
                file_type = (file_data.get("file_type") or "").lower()
                content = file_data.get("content")
                
                if content is None:
                    logger.warning(f"Skipping {file_data.get('file_name')}: no content")
                    continue
                
                # Route by file type
                if file_type in {"json", "csv", "xlsx", "xls"}:
                    chunks = self._chunk_structured(file_data)
                else:
                    chunks = self._chunk_text(file_data)

                all_docs.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to chunk {file_data.get('file_name')}: {e}")

        # Enrich with chunk indices and timestamps
        enriched = self._enrich_metadata(all_docs)
        
        logger.info(f"Generated {len(enriched)} chunks from {len(files)} files")
        return enriched

    def _chunk_text(self, file_data: Dict[str, Any]) -> List[Document]:
        """Chunk text content (txt, md, pdf, docx, etc.)."""
        content = file_data.get("content")
        if not isinstance(content, str) or not content.strip():
            return []

        meta = file_data.get("meta", {})
        doc = Document(page_content=content, metadata=meta)
        return self.splitter.split_documents([doc])

    def _chunk_structured(self, file_data: Dict[str, Any]) -> List[Document]:
        """
        Chunk structured data (JSON, CSV, Excel).
        Uses field_selection if present, else flattens data.
        """
        content = file_data.get("content")
        file_name = file_data.get("file_name", "unknown")
        
        if content is None:
            return []

        meta = file_data.get("meta", {})
        records: List[Dict[str, Any]] = []

        # Normalize to list of dicts
        if isinstance(content, list):
            if not content:
                return []
            # Check if first item is a dict (CSV/JSON data)
            if isinstance(content[0], dict):
                records = content
            else:
                # List of primitives
                records = [{"value": v} for v in content]
        elif isinstance(content, dict):
            records = [content]
        else:
            records = [{"value": str(content)}]

        # Get field selection from loader (if specified)
        field_selection = file_data.get("field_selection")

        # Process records
        doc_strings: List[str] = []
        for rec in records:
            # Flatten nested structures
            item = self._flatten_dict(rec)
            
            # Apply field selection if present
            if field_selection:
                item = {k: item.get(k) for k in field_selection if k in item}
            
            # Convert to string
            doc_str = self._stringify_record(item)
            if doc_str and doc_str.strip():
                doc_strings.append(doc_str)

        logger.info(f"File {file_name}: Generated {len(doc_strings)} doc strings from {len(records)} records")

        # Create documents and split
        docs = [
            Document(page_content=s, metadata=meta)
            for s in doc_strings
            if isinstance(s, str) and s.strip()
        ]
        
        result = self.splitter.split_documents(docs)
        logger.info(f"File {file_name}: Chunked into {len(result)} final chunks")
        
        return result

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Recursively flatten nested dicts/lists."""
        items: Dict[str, Any] = {}
        for k, v in (d or {}).items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                items[new_key] = ", ".join(str(x) for x in v)
            else:
                items[new_key] = v
        return items

    def _stringify_record(self, rec: Dict[str, Any]) -> str:
        """Convert record dict to key: value format."""
        return "\n".join(f"{k}: {v}" for k, v in rec.items() if v is not None)

    def _enrich_metadata(self, docs: List[Document]) -> List[Document]:
        """Add chunk index and timestamp to metadata."""
        if not docs:
            return []
        
        per_source_index: Dict[str, int] = {}
        enriched: List[Document] = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for doc in docs:
            meta = dict(doc.metadata or {})
            
            # Track chunk index per source
            file_id = meta.get("file_id", "unknown")
            chunk_idx = per_source_index.get(file_id, 0)
            per_source_index[file_id] = chunk_idx + 1
            
            # Add chunk index and timestamp
            meta["chunk_index"] = chunk_idx
            meta["chunk_timestamp"] = timestamp
            
            enriched.append(Document(page_content=doc.page_content, metadata=meta))
        
        return enriched
