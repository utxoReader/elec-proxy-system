"""Authentication related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """User login / registration request payload."""

    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str | None = None
    exp: int | None = None
    role: str | None = None


class UserProfile(BaseModel):
    """Current user profile response."""

    id: int
    username: str
    role: str
    agent_type: int | None = None
    status: int | None = None
    region: str | None = None
    is_active: bool = True


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    old_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    """Update profile request."""

    remark: str | None = Field(None, max_length=500)
