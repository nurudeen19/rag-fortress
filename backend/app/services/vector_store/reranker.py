"""
Reranker service for improving retrieval quality.
Uses LangChain wrappers for provider-agnostic reranking.
"""

from typing import List, Tuple, Optional
from langchain_core.documents import Document

from app.core.reranker_factory import get_reranker
from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)


class RerankerService:
    """
    Service for reranking documents using configured reranker provider.
    
    Improves retrieval quality by reranking documents based on semantic
    similarity to the query using the configured reranker (HuggingFace, Cohere, or Jina).
    """
    
    def __init__(self):
        """Initialize reranker service."""
        self._reranker = None
        self._provider = None
    
    def _get_reranker(self):
        """Lazy load the reranker from factory."""
        if self._reranker is None:
            self._reranker = get_reranker()
            if self._reranker:
                self._provider = settings.reranker_settings.RERANKER_PROVIDER.lower()
        return self._reranker
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3
    ) -> Tuple[List[Document], List[float]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: The search query
            documents: Documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Tuple of (reranked_documents, scores) limited to top_k
        """
        if not documents:
            logger.warning("No documents provided for reranking")
            return [], []
        
        # Get reranker from factory
        reranker = self._get_reranker()
        
        # If reranker is disabled, return original documents
        if reranker is None:
            logger.debug("Reranker is disabled, returning original documents")
            return documents[:top_k], [0.0] * min(top_k, len(documents))
        
        try:
            # Provider-specific reranking
            if self._provider == "huggingface":
                return self._rerank_huggingface(reranker, query, documents, top_k)
            elif self._provider == "cohere":
                return self._rerank_cohere(reranker, query, documents, top_k)
            elif self._provider == "jina":
                return self._rerank_jina(reranker, query, documents, top_k)
            else:
                logger.error(f"Unknown reranker provider: {self._provider}")
                return documents[:top_k], [0.0] * min(top_k, len(documents))
        
        except Exception as e:
            logger.error(f"Error during reranking: {e}", exc_info=True)
            # Fallback: return original documents without reranking
            return documents[:top_k], [0.0] * min(top_k, len(documents))
    
    def _rerank_huggingface(self, model, query: str, documents: List[Document], top_k: int) -> Tuple[List[Document], List[float]]:
        """Rerank using HuggingFace CrossEncoder."""
        # Prepare query-document pairs
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Get relevance scores
        scores = model.predict(pairs)
        
        # Sort documents by score (descending)
        doc_score_pairs = list(zip(documents, scores))
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Take top_k results
        top_results = doc_score_pairs[:top_k]
        
        reranked_docs = [doc for doc, _ in top_results]
        reranked_scores = [float(score) for _, score in top_results]
        
        return reranked_docs, reranked_scores
    
    def _rerank_cohere(self, compressor, query: str, documents: List[Document], top_k: int) -> Tuple[List[Document], List[float]]:
        """Rerank using LangChain CohereRerank wrapper."""
        try:
            # CohereRerank is a document compressor that needs invoke() call
            # It returns reranked documents with relevance_score in metadata
            reranked_docs = compressor.compress_documents(documents, query)
            
            # Extract scores from metadata (CohereRerank adds relevance_score)
            reranked_scores = []
            for doc in reranked_docs:
                score = doc.metadata.get("relevance_score", 0.0)
                reranked_scores.append(float(score))
            
            # Limit to top_k
            return reranked_docs[:top_k], reranked_scores[:top_k]
        
        except Exception as e:
            logger.error(f"Error in Cohere reranking: {e}")
            raise
    
    def _rerank_jina(self, compressor, query: str, documents: List[Document], top_k: int) -> Tuple[List[Document], List[float]]:
        """Rerank using LangChain JinaRerank wrapper."""
        try:
            # JinaRerank is a document compressor that needs compress_documents() call
            # It returns reranked documents with relevance_score in metadata
            reranked_docs = compressor.compress_documents(documents, query)
            
            # Extract scores from metadata (JinaRerank adds relevance_score)
            reranked_scores = []
            for doc in reranked_docs:
                score = doc.metadata.get("relevance_score", 0.0)
                reranked_scores.append(float(score))
            
            # Limit to top_k
            return reranked_docs[:top_k], reranked_scores[:top_k]
        
        except Exception as e:
            logger.error(f"Error in Jina reranking: {e}")
            raise

# Singleton instance
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """
    Get reranker service instance.
    Creates singleton instance on first call.
    
    Returns:
        RerankerService: Reranker service instance
    """
    global _reranker_service
    
    if _reranker_service is None:
        _reranker_service = RerankerService()
    
    return _reranker_service
