"""
Document and chunk schemas for RAG system.
Standardized format used across all vector store providers.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator


class SourceType(str, Enum):
    """Supported document source types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "md"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    JSON = "json"
    XML = "xml"


class SecurityLevel(str, Enum):
    """Document security classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"


class ChunkMetadata(BaseModel):
    """
    Standardized metadata for document chunks.
    This format is used consistently across all vector store providers.
    """
    source: str = Field(..., description="Original filename or URL")
    source_type: SourceType = Field(..., description="Type of source document")
    chunk_index: int = Field(..., ge=0, description="Position of chunk in document")
    
    # Optional security and organizational metadata
    security_level: Optional[SecurityLevel] = Field(
        default=None,
        description="Security classification of the document"
    )
    organization: Optional[str] = Field(
        default=None,
        description="Organization or department owning the document"
    )
    
    # Version control
    version: Optional[str] = Field(
        default=None,
        description="Document version identifier"
    )
    
    # Temporal information
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the chunk was created/indexed"
    )
    
    # Categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )
    
    # Additional flexible metadata
    custom_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific or custom metadata fields"
    )
    
    # Document structure information
    page_number: Optional[int] = Field(
        default=None,
        description="Page number in source document (for PDFs, DOCX)"
    )
    section: Optional[str] = Field(
        default=None,
        description="Section or chapter name"
    )
    
    # Text statistics
    char_count: Optional[int] = Field(
        default=None,
        description="Number of characters in the chunk"
    )
    token_count: Optional[int] = Field(
        default=None,
        description="Estimated token count for LLM processing"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class DocumentChunk(BaseModel):
    """
    Standardized document chunk format for vector storage.
    This is the canonical format used across all vector store implementations.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the chunk (UUID4 for security)"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Text content of the chunk for embedding"
    )
    metadata: ChunkMetadata = Field(
        ...,
        description="Structured metadata about the chunk"
    )
    
    # Optional pre-computed embedding (for efficiency)
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Pre-computed embedding vector"
    )
    
    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or only whitespace")
        return v
    
    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class DocumentChunkCreate(BaseModel):
    """Schema for creating new document chunks."""
    content: str = Field(..., min_length=1)
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None


class DocumentChunkResponse(BaseModel):
    """Response schema for chunk retrieval."""
    id: str = Field(..., description="Chunk ID as string")
    content: str
    metadata: ChunkMetadata
    score: Optional[float] = Field(
        default=None,
        description="Similarity score (for search results)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SearchQuery(BaseModel):
    """Schema for vector similarity search queries."""
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")
    
    # Optional filters
    source_types: Optional[List[SourceType]] = Field(
        default=None,
        description="Filter by document types"
    )
    security_levels: Optional[List[SecurityLevel]] = Field(
        default=None,
        description="Filter by security levels"
    )
    organizations: Optional[List[str]] = Field(
        default=None,
        description="Filter by organizations"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (any match)"
    )
    min_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    
    # Date range filters
    start_date: Optional[datetime] = Field(
        default=None,
        description="Filter chunks created after this date"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Filter chunks created before this date"
    )


class SearchResponse(BaseModel):
    """Response schema for search operations."""
    query: str
    results: List[DocumentChunkResponse]
    total_results: int
    execution_time_ms: float = Field(..., description="Search execution time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class BulkInsertRequest(BaseModel):
    """Schema for bulk inserting multiple chunks."""
    chunks: List[DocumentChunkCreate] = Field(
        ...,
        min_items=1,
        description="List of chunks to insert"
    )


class BulkInsertResponse(BaseModel):
    """Response for bulk insert operations."""
    inserted_count: int
    failed_count: int = Field(default=0)
    chunk_ids: List[str]
    errors: Optional[List[Dict[str, Any]]] = Field(default=None)


class DeleteRequest(BaseModel):
    """Schema for deleting chunks."""
    chunk_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific chunk IDs to delete"
    )
    source: Optional[str] = Field(
        default=None,
        description="Delete all chunks from this source"
    )
    organization: Optional[str] = Field(
        default=None,
        description="Delete all chunks from this organization"
    )
    
    @validator('chunk_ids', 'source', 'organization')
    def validate_at_least_one(cls, v, values):
        """Ensure at least one deletion criteria is provided."""
        if not any([v, values.get('source'), values.get('organization')]):
            raise ValueError(
                "At least one deletion criteria must be provided: "
                "chunk_ids, source, or organization"
            )
        return v


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    deleted_count: int
    success: bool
    message: str
