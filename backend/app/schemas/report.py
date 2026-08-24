import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReportType


class ReportBase(BaseModel):
    """Base schema for exported verification report."""

    verification_id: uuid.UUID
    report_type: ReportType
    file_path: str = Field(..., max_length=1000)


class ReportCreate(ReportBase):
    """Schema for recording generated report file."""
    pass


class ReportRead(ReportBase):
    """Schema for reading report record."""

    id: uuid.UUID
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
