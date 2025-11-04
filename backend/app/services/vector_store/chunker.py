"""
Document Chunker - Chunks documents using LangChain splitters.
Simple, focused responsibility.

Input: loader results (list of dicts with file_path, file_name, file_type, content,
       and optionally structured_fields, flatten_nested per file).

Returns: List of LangChain Document objects ready for vector storage.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentChunker:
    """
    Chunks documents using LangChain text splitters.
    Returns LangChain Document objects ready for vectorization.
    """
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Use LangChain's battle-tested splitter
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
    
    # Primary entrypoint: accept loader outputs directly
    def chunk_loaded_files(
        self,
        files: List[Dict[str, Any]],
    ) -> List[Document]:
        """
        Chunk a list of files returned from the DocumentLoader.

        Args:
            files: List of dicts with keys {file_path, file_name, file_type, content}

        Returns:
            List[Document]: All chunks across files as LangChain Documents with enriched metadata
        """
        if not files:
            return []

        all_docs: List[Document] = []
        for f in files:
            try:
                file_type = (f.get("file_type") or "").lower()
                content = f.get("content")
                
                # Skip files with no content
                if content is None:
                    logger.warning(f"Skipping {f.get('file_name')}: no content loaded")
                    continue
                
                # Route based on file type
                if file_type in {"json", "csv", "xlsx", "xls"}:
                    chunks = self._chunk_structured_file(f)
                else:
                    # Text files (txt, md, pdf, docx, etc.)
                    chunks = self._chunk_text_file(f)

                all_docs.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to chunk {f.get('file_name')}: {e}", exc_info=False)

        # Enrich metadata with chunk indices and additional fields
        enriched_docs = self._enrich_metadata(all_docs)
        
        logger.info(f"Generated {len(enriched_docs)} total chunks from {len(files)} files")
        return enriched_docs

    # --- Strategies ---
    def _chunk_text_file(self, f: Dict[str, Any]) -> List[Document]:
        """Chunk text content from any file type (txt, md, pdf, docx, etc.)."""
        content = f.get("content")
        if not isinstance(content, str) or not content.strip():
            return []

        base_meta = {
            "source": f.get("file_name"),
            "file_path": f.get("file_path"),
            "file_type": f.get("file_type"),
        }

        doc = Document(page_content=content, metadata=base_meta)
        return self.splitter.split_documents([doc])


    def _chunk_structured_file(self, f: Dict[str, Any]) -> List[Document]:
        """Chunk structured data (JSON, CSV) with optional field selection and flattening."""
        content = f.get("content")
        if content is None:
            return []

        base_meta = {
            "source": f.get("file_name"),
            "file_path": f.get("file_path"),
            "file_type": f.get("file_type"),
            "is_structured": True,
        }

        records: List[Dict[str, Any]] = []

        # Normalize content to list[dict]
        if isinstance(content, list):
            if content and isinstance(content[0], dict):
                records = content
            else:
                # list of primitives → wrap
                records = [{"value": v} for v in content]
        elif isinstance(content, dict):
            records = [content]
        else:
            records = [{"value": str(content)}]

        # Per-file options
        structured_fields: Optional[List[str]] = f.get("structured_fields")
        flatten_nested: bool = f.get("flatten_nested", True)

        # Field selection and optional flattening
        processed_strings: List[str] = []
        for idx, rec in enumerate(records):
            item = rec
            if flatten_nested:
                item = self._flatten_dict(item)

            if structured_fields:
                item = {k: item.get(k) for k in structured_fields if k in item}

            # Convert to readable string
            processed_strings.append(self._stringify_record(item))

        # Build Documents (one per record string), then split
        docs = [
            Document(
                page_content=s,
                metadata={**base_meta, "record_index": i}
            )
            for i, s in enumerate(processed_strings)
            if isinstance(s, str) and s.strip()
        ]

        return self.splitter.split_documents(docs)

    # --- Helpers ---
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
        """Recursively flatten nested dicts/lists into a single-level dict."""
        items: Dict[str, Any] = {}
        for k, v in (d or {}).items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                items[new_key] = ", ".join([self._coerce_scalar(x) for x in v])
            else:
                items[new_key] = self._coerce_scalar(v)
        return items

    def _coerce_scalar(self, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return str(v)

    def _stringify_record(self, rec: Dict[str, Any]) -> str:
        """Convert record dict to readable key: value format."""
        parts = []
        for k, v in rec.items():
            parts.append(f"{k}: {self._coerce_scalar(v)}")
        return "\n".join(parts)
    
    def _enrich_metadata(self, docs: List[Document]) -> List[Document]:
        """Enrich document metadata with chunk indices and additional fields."""
        if not docs:
            return []
        
        # Track per-source chunk indices
        per_source_index: Dict[str, int] = {}
        enriched_docs: List[Document] = []
        
        for doc in docs:
            # Get existing metadata
            meta = dict(doc.metadata or {})
            
            # Extract key fields
            file_name = meta.get("source")
            file_path = meta.get("file_path", "")
            source_type = meta.get("file_type")
            
            # Use file_path or file_name as unique key for indexing
            source_key = file_path or file_name or "unknown"
            
            # Get and increment chunk index for this source
            chunk_idx = per_source_index.get(source_key, 0)
            per_source_index[source_key] = chunk_idx + 1
            
            # Build enriched metadata
            enriched_meta: Dict[str, Any] = {
                "source": file_name or source_key,
                "source_type": source_type,
                "chunk_index": chunk_idx,
                # Placeholders/basis for future fields
                "security_level": meta.get("security_level"),
                "version": meta.get("version"),
                "timestamp": meta.get("timestamp"),
                "tags": meta.get("tags", []),
            }
            
            # Preserve any additional metadata fields
            for k, v in meta.items():
                if k not in enriched_meta and k not in {"source", "file_path"}:
                    enriched_meta[k] = v
            
            # Create new document with enriched metadata
            enriched_docs.append(
                Document(page_content=doc.page_content, metadata=enriched_meta)
            )
        
        return enriched_docs
