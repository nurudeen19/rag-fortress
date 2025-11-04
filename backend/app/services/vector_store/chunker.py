"""
Document Chunker - Chunks documents using LangChain splitters.
Simple, focused responsibility.

Input: loader results (list of dicts with file_path, file_name, file_type, content,
       and optionally structured_fields, flatten_nested per file).

For structured data (json/csv/xlsx): can select fields (per-file) and flatten
to readable strings for better LLM context.
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
            List[Document]: All chunks across files
        """
        if not files:
            return []

        all_chunks: List[Document] = []
        for f in files:
            try:
                file_type = (f.get("file_type") or "").lower()
                if file_type in {"txt", "md", "markdown"}:
                    chunks = self._chunk_text_file(f)
                elif file_type in {"json", "csv", "xlsx", "xls"}:
                    chunks = self._chunk_structured_file(f)
                elif file_type in {"pdf", "doc", "docx", "xlsx", "xls"}:
                    # Load content/documents via appropriate loaders and split
                    chunks = self._chunk_via_loader(f)
                else:
                    # Unknown -> attempt text chunking if content present
                    chunks = self._chunk_text_file(f)

                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to chunk {f.get('file_name')}: {e}", exc_info=False)

        return all_chunks

    # --- Strategies ---
    def _chunk_text_file(self, f: Dict[str, Any]) -> List[Document]:
        content = f.get("content")
        if not isinstance(content, str) or not content.strip():
            # No inline text content → try loading via loaders (pdf/docx/xlsx might land here)
            return self._chunk_via_loader(f)

        base_meta = {
            "source": f.get("file_path"),
            "file_name": f.get("file_name"),
            "file_type": f.get("file_type"),
        }

        doc = Document(page_content=content, metadata=base_meta)
        return self.splitter.split_documents([doc])

    def _chunk_via_loader(self, f: Dict[str, Any]) -> List[Document]:
        """Load non-inline content types (pdf/docx/xlsx) with community loaders then split."""
        suffix = (f.get("file_type") or "").lower()
        path = f.get("file_path")
        if not path:
            return []

        p = Path(path)
        docs: List[Document] = []

        try:
            if suffix == "pdf":
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(p))
                docs = loader.load()
            elif suffix in {"doc", "docx"}:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(p))
                docs = loader.load()
            elif suffix in {"xlsx", "xls"}:
                # Treat spreadsheet as unstructured text for now
                from langchain_community.document_loaders import UnstructuredExcelLoader
                loader = UnstructuredExcelLoader(str(p))
                docs = loader.load()
            else:
                # Fallback: read as plain text if possible
                try:
                    text = Path(path).read_text(encoding="utf-8")
                    docs = [Document(page_content=text, metadata={
                        "source": path,
                        "file_name": f.get("file_name"),
                        "file_type": suffix,
                    })]
                except Exception:
                    logger.warning(f"Unsupported or unreadable file type: {suffix} ({path})")
                    return []
        except Exception as e:
            logger.warning(f"Loader failed for {p.name} ({suffix}): {e}")
            return []

        return self.splitter.split_documents(docs)

    def _chunk_structured_file(self, f: Dict[str, Any]) -> List[Document]:
        content = f.get("content")
        if content is None:
            # Nothing to process
            return []

        base_meta = {
            "source": f.get("file_path"),
            "file_name": f.get("file_name"),
            "file_type": f.get("file_type"),
            "is_structured": True,
        }

        records: List[Dict[str, Any]] = []

        # Normalize content to list[dict]
        if isinstance(content, list):
            # csv already a list[dict] or json list
            if content and isinstance(content[0], dict):
                records = content  # type: ignore[assignment]
            else:
                # list of primitives → wrap
                records = [{"value": v} for v in content]
        elif isinstance(content, dict):
            # single json object
            records = [content]
        else:
            # Unknown structure → stringify and treat as single record
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
                # Join list items into a readable string
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
        # key: value lines for readability and LLM friendliness
        parts = []
        for k, v in rec.items():
            parts.append(f"{k}: {self._coerce_scalar(v)}")
        return "\n".join(parts)
