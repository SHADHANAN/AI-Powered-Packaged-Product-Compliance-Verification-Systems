import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ExtractedFieldBase(BaseModel):
    """Base schema for extracted OCR key-value field."""

    verification_id: uuid.UUID
    field_name: str = Field(..., min_length=1, max_length=100)
    field_value: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_text: Optional[str] = None


class ExtractedFieldCreate(ExtractedFieldBase):
    """Schema for persisting extracted field data."""
    pass


class ExtractedFieldRead(ExtractedFieldBase):
    """Schema for reading extracted field data."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
