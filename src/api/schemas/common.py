from __future__ import annotations

from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Exception class name, e.g. ValidationError")
    message: str
    details: dict = Field(default_factory=dict)
    request_id: str | None = None