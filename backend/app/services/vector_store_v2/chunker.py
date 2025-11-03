"""
Document Chunker - Chunks documents using LangChain splitters.
Simple, focused responsibility.
"""

from typing import List, Optional

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
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk documents using recursive character splitting.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of chunked LangChain Document objects
        """
        if not documents:
            return []
        
        logger.info(f"Chunking {len(documents)} documents...")
        
        # Let LangChain handle the chunking
        chunks = self.splitter.split_documents(documents)
        
        logger.info(f"Generated {len(chunks)} chunks")
        return chunks
