"""
Common response schemas shared across all endpoints.
"""

from pydantic import BaseModel
from typing import Optional, Any


class MessageResponse(BaseModel):
    """Standard message response."""
    status: str
    message: str
    data: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Operation completed successfully",
                "data": None
            }
        }
