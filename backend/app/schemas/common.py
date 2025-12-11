"""
Common response schemas shared across all endpoints.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class MessageResponse(BaseModel):
    """Standard message response."""
    status: str
    message: str
    data: Optional[Any] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "message": "Operation completed successfully",
                "data": None
            }
        }
    )
