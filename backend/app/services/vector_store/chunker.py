"""
Document Chunker - Chunks documents using LangChain splitters.
Receives documents from DocumentLoader with enriched metadata.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from app.config.settings import settings
from app.core import get_logger


logger = get_logger(__name__)


class DocumentChunker:
    """Chunks documents from loader, returns LangChain Documents with enriched metadata."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Standard recursive text splitter (fallback for plain text)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Markdown-aware splitter preserves hierarchy
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
            ],
            strip_headers=False  # Keep headers in content for semantic matching
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
                elif file_type == "md":
                    chunks = self._chunk_markdown(file_data)
                elif file_type == "pdf":
                    chunks = self._chunk_pdf(file_data)
                elif file_type in {"doc", "docx"}:
                    chunks = self._chunk_word(file_data)
                else:
                    # Fallback to standard text chunking
                    chunks = self._chunk_text(file_data)

                all_docs.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to chunk {file_data.get('file_name')}: {e}")

        # Enrich with chunk indices and timestamps
        enriched = self._enrich_metadata(all_docs)
        
        logger.info(f"Generated {len(enriched)} chunks from {len(files)} files")
        return enriched

    def _chunk_text(self, file_data: Dict[str, Any]) -> List[Document]:
        """Chunk plain text content (txt, etc.)."""
        content = file_data.get("content")
        if not isinstance(content, str) or not content.strip():
            return []

        meta = file_data.get("meta", {})
        doc = Document(page_content=content, metadata=meta)
        return self.text_splitter.split_documents([doc])
    
    def _chunk_markdown(self, file_data: Dict[str, Any]) -> List[Document]:
        """
        Chunk markdown files preserving hierarchical structure.
        Headers are kept in content and added as metadata for semantic matching.
        """
        content = file_data.get("content")
        if not isinstance(content, str) or not content.strip():
            return []
        
        meta = file_data.get("meta", {})
        file_name = file_data.get("file_name", "unknown")
        
        try:
            # Split by markdown headers first
            md_chunks = self.markdown_splitter.split_text(content)
            
            # Further split large chunks if needed
            final_chunks: List[Document] = []
            for md_doc in md_chunks:
                # Merge header metadata with file metadata
                combined_meta = {**meta, **md_doc.metadata}
                
                # Check if chunk exceeds size limit
                if len(md_doc.page_content) > self.chunk_size:
                    # Further split while preserving metadata
                    doc = Document(page_content=md_doc.page_content, metadata=combined_meta)
                    sub_chunks = self.text_splitter.split_documents([doc])
                    
                    # Keep the header metadata on all sub-chunks
                    for chunk in sub_chunks:
                        chunk.metadata.update(combined_meta)
                    
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(Document(
                        page_content=md_doc.page_content,
                        metadata=combined_meta
                    ))
            
            logger.info(f"Markdown file {file_name}: Split into {len(final_chunks)} chunks with hierarchy preservation")
            return final_chunks
            
        except Exception as e:
            logger.warning(f"Markdown splitting failed for {file_name}, falling back to text splitter: {e}")
            doc = Document(page_content=content, metadata=meta)
            return self.text_splitter.split_documents([doc])
    
    def _chunk_pdf(self, file_data: Dict[str, Any]) -> List[Document]:
        """
        Chunk PDF content with section/heading detection.
        Detects common heading patterns and preserves document structure.
        """
        content = file_data.get("content")
        if not isinstance(content, str) or not content.strip():
            return []
        
        meta = file_data.get("meta", {})
        file_name = file_data.get("file_name", "unknown")
        
        # Detect sections using common heading patterns in PDFs
        sections = self._detect_sections(content)
        
        if sections:
            # Process each section with its heading as context
            final_chunks: List[Document] = []
            
            for section_heading, section_content in sections:
                # Add heading to metadata for semantic search
                section_meta = {**meta}
                if section_heading:
                    section_meta["section"] = section_heading
                
                # Include heading in content for better semantic matching
                full_section = f"{section_heading}\n\n{section_content}" if section_heading else section_content
                
                # Split large sections
                doc = Document(page_content=full_section, metadata=section_meta)
                chunks = self.text_splitter.split_documents([doc])
                
                # Preserve section metadata on all chunks
                for chunk in chunks:
                    chunk.metadata.update(section_meta)
                
                final_chunks.extend(chunks)
            
            logger.info(f"PDF file {file_name}: Split into {len(final_chunks)} chunks across {len(sections)} sections")
            return final_chunks
        else:
            # No clear sections detected, use standard text splitting
            logger.info(f"PDF file {file_name}: No sections detected, using standard chunking")
            doc = Document(page_content=content, metadata=meta)
            return self.text_splitter.split_documents([doc])
    
    def _chunk_word(self, file_data: Dict[str, Any]) -> List[Document]:
        """
        Chunk Word document content with heading detection.
        Similar to PDF chunking but tailored for Word document structure.
        """
        content = file_data.get("content")
        if not isinstance(content, str) or not content.strip():
            return []
        
        meta = file_data.get("meta", {})
        file_name = file_data.get("file_name", "unknown")
        
        # Detect sections in Word document
        sections = self._detect_sections(content)
        
        if sections:
            final_chunks: List[Document] = []
            
            for section_heading, section_content in sections:
                section_meta = {**meta}
                if section_heading:
                    section_meta["section"] = section_heading
                
                # Include heading in content
                full_section = f"{section_heading}\n\n{section_content}" if section_heading else section_content
                
                # Split large sections
                doc = Document(page_content=full_section, metadata=section_meta)
                chunks = self.text_splitter.split_documents([doc])
                
                # Preserve section metadata
                for chunk in chunks:
                    chunk.metadata.update(section_meta)
                
                final_chunks.extend(chunks)
            
            logger.info(f"Word file {file_name}: Split into {len(final_chunks)} chunks across {len(sections)} sections")
            return final_chunks
        else:
            logger.info(f"Word file {file_name}: No sections detected, using standard chunking")
            doc = Document(page_content=content, metadata=meta)
            return self.text_splitter.split_documents([doc])
    
    def _detect_sections(self, content: str) -> List[tuple[str, str]]:
        """
        Detect sections in unstructured text (PDFs, Word docs).
        Returns list of (heading, content) tuples.
        
        Detects patterns like:
        - ALL CAPS HEADINGS
        - Numbered headings (1. Title, 1.1 Subtitle)
        - Common section markers (Chapter, Section, Part)
        """
        if not content:
            return []
        
        lines = content.split('\n')
        sections: List[tuple[str, str]] = []
        current_heading: str = ""
        current_content: List[str] = []
        
        # Heading patterns
        all_caps_pattern = re.compile(r'^[A-Z][A-Z\s]{2,}$')  # At least 3 uppercase letters
        numbered_pattern = re.compile(r'^\d+(\.\d+)*\.?\s+[A-Z]')  # 1. Title or 1.1 Subtitle
        section_pattern = re.compile(r'^(Chapter|Section|Part|Article|Appendix)\s+\d+', re.IGNORECASE)
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this line is a heading
            is_heading = False
            
            if stripped and (
                all_caps_pattern.match(stripped) or
                numbered_pattern.match(stripped) or
                section_pattern.match(stripped)
            ):
                # Headings are typically short (not full paragraphs)
                if len(stripped) < 100:
                    is_heading = True
            
            if is_heading:
                # Save previous section
                if current_heading or current_content:
                    sections.append((current_heading, '\n'.join(current_content)))
                
                # Start new section
                current_heading = stripped
                current_content = []
            else:
                # Add to current section content
                current_content.append(line)
        
        # Add final section
        if current_heading or current_content:
            sections.append((current_heading, '\n'.join(current_content)))
        
        # Only return sections if we found meaningful headings
        # (if we only have one section with no heading, better to use standard chunking)
        if len(sections) <= 1 and not sections[0][0]:
            return []
        
        return sections

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
        
        result = self.text_splitter.split_documents(docs)
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
