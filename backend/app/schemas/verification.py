import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VerificationStatus


class VerificationBase(BaseModel):
    """Base schema for verification entity."""

    product_id: Optional[uuid.UUID] = None
    inspector_id: Optional[uuid.UUID] = None
    status: VerificationStatus = Field(default=VerificationStatus.PENDING)
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    source_image_path: str = Field(..., max_length=1000)
    ocr_raw_text: Optional[str] = None


class VerificationCreate(BaseModel):
    """Schema for initializing a new verification run."""

    product_id: Optional[uuid.UUID] = None
    inspector_id: Optional[uuid.UUID] = None
    source_image_path: str = Field(..., max_length=1000)


class VerificationUpdate(BaseModel):
    """Schema for updating verification progress and scoring."""

    status: Optional[VerificationStatus] = None
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    ocr_raw_text: Optional[str] = None
    completed_at: Optional[datetime] = None


class VerificationRead(VerificationBase):
    """Schema for reading verification data."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
