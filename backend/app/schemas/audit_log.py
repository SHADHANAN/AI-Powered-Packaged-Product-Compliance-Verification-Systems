import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogBase(BaseModel):
    """Base schema for audit log entries."""

    verification_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: AuditAction
    status: str = "SUCCESS"
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    pass


class AuditLogRead(AuditLogBase):
    """Schema for reading audit log entry."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
