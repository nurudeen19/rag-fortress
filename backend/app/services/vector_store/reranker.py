"""
Reranker service for improving retrieval quality.
Uses cross-encoder models to rerank documents based on query relevance.
"""

from typing import List, Tuple, Optional
from langchain_core.documents import Document

from app.core import get_logger

logger = get_logger(__name__)


class RerankerService:
    """
    Service for reranking documents using cross-encoder models.
    
    Improves retrieval quality by reranking documents based on semantic
    similarity to the query using a cross-encoder model.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker service.
        
        Args:
            model_name: HuggingFace cross-encoder model name
        """
        self.model_name = model_name
        self._model = None
    
    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except ImportError:
                logger.error(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to load cross-encoder model: {e}")
                raise
    
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
        
        # Lazy load model
        self._load_model()
        
        try:
            # Prepare query-document pairs
            pairs = [[query, doc.page_content] for doc in documents]
            
            # Get relevance scores
            scores = self._model.predict(pairs)
            
            # Sort documents by score (descending)
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Take top_k results
            top_results = doc_score_pairs[:top_k]
            
            reranked_docs = [doc for doc, _ in top_results]
            reranked_scores = [float(score) for _, score in top_results]
            
            # logger.info(
            #     f"Reranked {len(documents)} documents, returning top {len(reranked_docs)} "
            #     f"(scores: {[f'{s:.3f}' for s in reranked_scores]})"
            # )
            
            return reranked_docs, reranked_scores
        
        except Exception as e:
            logger.error(f"Error during reranking: {e}", exc_info=True)
            # Fallback: return original documents without reranking
            return documents[:top_k], [0.0] * min(top_k, len(documents))


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
        logger.info("✓ Reranker service initialized")
    
    return _reranker_service
