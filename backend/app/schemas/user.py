import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole

# Standard RFC-compliant lightweight email pattern
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    """Base schema for user data."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    email: str = Field(..., pattern=EMAIL_REGEX, description="Unique email address")
    role: UserRole = Field(default=UserRole.INSPECTOR, description="Assigned user role")
    is_active: bool = Field(default=True, description="Account active status")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=6, description="Plaintext password for registration/creation")


class UserUpdate(BaseModel):
    """Schema for updating user details."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, pattern=EMAIL_REGEX)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserRead(UserBase):
    """Schema for reading user details from database."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
