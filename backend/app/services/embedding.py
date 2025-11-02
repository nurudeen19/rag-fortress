"""
Embedding service.
Generates embeddings using configured provider.
"""

from typing import List
from abc import ABC, abstractmethod

from app.config.settings import get_settings
from app.core.exceptions import ConfigurationError


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass


class HuggingFaceEmbedding(EmbeddingProvider):
    """HuggingFace embedding provider."""
    
    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ConfigurationError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model = SentenceTransformer(model_name)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ConfigurationError(
                "openai not installed. Install with: pip install openai"
            )
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        response = await self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]


class CohereEmbedding(EmbeddingProvider):
    """Cohere embedding provider."""
    
    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        try:
            import cohere
        except ImportError:
            raise ConfigurationError(
                "cohere not installed. Install with: pip install cohere"
            )
        
        self.client = cohere.AsyncClient(api_key=api_key)
        self.model = model
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        response = await self.client.embed(
            texts=[text],
            model=self.model,
            input_type="search_document"
        )
        return response.embeddings[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document"
        )
        return response.embeddings


def get_embedding_provider() -> EmbeddingProvider:
    """
    Get embedding provider based on configuration.
    
    Returns:
        EmbeddingProvider: Configured embedding provider
    """
    settings = get_settings()
    provider = settings.embedding.provider.lower()
    
    if provider == "huggingface":
        return HuggingFaceEmbedding(
            model_name=settings.embedding.model_name
        )
    
    elif provider == "openai":
        if not settings.llm.openai_api_key:
            raise ConfigurationError("OpenAI API key not configured")
        return OpenAIEmbedding(
            api_key=settings.llm.openai_api_key,
            model=settings.embedding.model_name
        )
    
    elif provider == "cohere":
        if not settings.llm.cohere_api_key:
            raise ConfigurationError("Cohere API key not configured")
        return CohereEmbedding(
            api_key=settings.llm.cohere_api_key,
            model=settings.embedding.model_name
        )
    
    else:
        raise ConfigurationError(f"Unsupported embedding provider: {provider}")
