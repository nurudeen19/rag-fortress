"""
Message Metadata Schemas

Defines structured schemas for the Message.meta JSON field to enforce
consistency for sources, citations, and other message metadata.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DocumentSource(BaseModel):
    """Structured metadata for a document source citation."""
    
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Name of the source document")
    page: Optional[int] = Field(None, description="Page number if applicable")
    chunk_id: Optional[str] = Field(None, description="Specific chunk/section identifier")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score from retrieval")
    content_preview: Optional[str] = Field(None, max_length=500, description="Preview of cited content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123",
                "filename": "security_policy.pdf",
                "page": 5,
                "chunk_id": "chunk_10",
                "relevance_score": 0.92,
                "content_preview": "Access to classified materials requires..."
            }
        }


class MessageSources(BaseModel):
    """Container for document sources and citations."""
    
    sources: List[DocumentSource] = Field(default_factory=list, description="List of cited document sources")
    total_sources: Optional[int] = Field(None, description="Total number of sources consulted")
    retrieval_method: Optional[str] = Field(None, description="Method used for document retrieval")
    
    @field_validator('total_sources')
    @classmethod
    def validate_total_sources(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure total_sources matches actual sources count if provided."""
        if v is not None and 'sources' in info.data:
            sources_count = len(info.data['sources'])
            if v != sources_count:
                return sources_count  # Auto-correct to match actual count
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "sources": [
                    {
                        "document_id": "doc_123",
                        "filename": "policy.pdf",
                        "page": 5,
                        "relevance_score": 0.92
                    }
                ],
                "total_sources": 1,
                "retrieval_method": "semantic_search"
            }
        }


class IntentMetadata(BaseModel):
    """Metadata for intent classification results."""
    
    intent: str = Field(..., description="Detected intent type")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Classification confidence")
    template_response: Optional[bool] = Field(False, description="Whether response was from template")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "greeting",
                "confidence": 0.95,
                "template_response": True
            }
        }


class ThreatMetadata(BaseModel):
    """Metadata for security threat detection."""
    
    threat_type: str = Field(..., description="Type of detected threat")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Threat detection confidence")
    reason: Optional[str] = Field(None, description="Reason for threat classification")
    blocked: bool = Field(True, description="Whether the query was blocked")
    
    class Config:
        json_schema_extra = {
            "example": {
                "threat_type": "sql_injection",
                "confidence": 0.89,
                "reason": "Contains SQL injection patterns",
                "blocked": True
            }
        }


class AssistantMessageMetadata(BaseModel):
    """
    Complete metadata schema for assistant messages.
    
    This is the recommended structure for the Message.meta field.
    All fields are optional to maintain backward compatibility.
    """
    
    sources: Optional[MessageSources] = Field(None, description="Document sources and citations")
    intent: Optional[str] = Field(None, description="Detected intent (legacy field)")
    intent_metadata: Optional[IntentMetadata] = Field(None, description="Detailed intent classification")
    threat_metadata: Optional[ThreatMetadata] = Field(None, description="Security threat detection")
    model: Optional[str] = Field(None, description="LLM model used for generation")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed for generation")
    generation_time_ms: Optional[int] = Field(None, ge=0, description="Time taken to generate response")
    cache_hit: Optional[bool] = Field(None, description="Whether response came from cache")
    custom: Optional[Dict[str, Any]] = Field(None, description="Custom metadata fields")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sources": {
                    "sources": [
                        {
                            "document_id": "doc_123",
                            "filename": "policy.pdf",
                            "relevance_score": 0.92
                        }
                    ],
                    "total_sources": 1,
                    "retrieval_method": "semantic_search"
                },
                "intent_metadata": {
                    "intent": "document_query",
                    "confidence": 0.88
                },
                "model": "gpt-4",
                "tokens_used": 450,
                "generation_time_ms": 1250
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_legacy(cls, legacy_meta: Dict[str, Any]) -> "AssistantMessageMetadata":
        """
        Convert legacy metadata format to structured schema.
        
        Handles common legacy patterns:
        - sources: List[Dict] -> MessageSources
        - intent: str -> intent field
        - threat_type + confidence -> ThreatMetadata
        """
        metadata = cls()
        
        # Handle sources
        if "sources" in legacy_meta:
            sources_list = legacy_meta["sources"]
            if isinstance(sources_list, list):
                try:
                    doc_sources = [DocumentSource(**src) for src in sources_list]
                    metadata.sources = MessageSources(
                        sources=doc_sources,
                        total_sources=len(doc_sources)
                    )
                except Exception:
                    # Keep as custom field if parsing fails
                    metadata.custom = metadata.custom or {}
                    metadata.custom["sources_raw"] = sources_list
        
        # Handle intent
        if "intent" in legacy_meta:
            metadata.intent = legacy_meta["intent"]
            if "confidence" in legacy_meta:
                metadata.intent_metadata = IntentMetadata(
                    intent=legacy_meta["intent"],
                    confidence=legacy_meta.get("confidence"),
                    template_response=legacy_meta.get("template_response", False)
                )
        
        # Handle threat detection
        if "threat_type" in legacy_meta:
            metadata.threat_metadata = ThreatMetadata(
                threat_type=legacy_meta["threat_type"],
                confidence=legacy_meta.get("confidence", 0.0),
                reason=legacy_meta.get("reason"),
                blocked=legacy_meta.get("blocked", True)
            )
        
        # Copy other fields
        for key in ["model", "tokens_used", "generation_time_ms", "cache_hit"]:
            if key in legacy_meta:
                setattr(metadata, key, legacy_meta[key])
        
        # Store any remaining fields in custom
        handled_keys = {
            "sources", "intent", "confidence", "template_response",
            "threat_type", "reason", "blocked", "model", 
            "tokens_used", "generation_time_ms", "cache_hit"
        }
        remaining = {k: v for k, v in legacy_meta.items() if k not in handled_keys}
        if remaining:
            metadata.custom = remaining
        
        return metadata
