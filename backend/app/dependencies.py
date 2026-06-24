"""Common FastAPI dependencies: authentication and authorization."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class CurrentUser(BaseModel):
    """Authenticated user info extracted from JWT token."""
    user_id: int
    username: str
    role: str = "agent"
    region: Optional[str] = None
    is_active: bool = True


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Authenticate user via JWT bearer token.

    Decodes and verifies the JWT, then returns the current user info.
    Raises 401 if the token is missing, invalid, or expired.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Look up user from database
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    from app.models import Agent
    user = db.query(Agent).filter(Agent.id == user_id, Agent.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Use role from DB (source of truth), fallback to JWT claim
    role = user.role if hasattr(user, "role") and user.role else payload.get("role", "agent")

    return CurrentUser(
        user_id=user.id,
        username=user.name,
        role=role,
        region=user.region if hasattr(user, "region") else None,
        is_active=user.status == 0 if user.status is not None else True,
    )


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[CurrentUser]:
    """Like get_current_user but returns None instead of raising 401."""
    if token is None:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None


def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Require the current user to have the 'admin' role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
