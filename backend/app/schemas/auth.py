from pydantic import BaseModel, Field

# Standard RFC-compliant lightweight email pattern matching user schema
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class LoginRequest(BaseModel):
    """Schema for user authentication request."""

    email: str = Field(..., pattern=EMAIL_REGEX, description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class TokenResponse(BaseModel):
    """Schema for returning JWT access token upon successful authentication."""

    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token authorization type")
