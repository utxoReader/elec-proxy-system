"""Authentication business logic.

Handles user registration and login using the Agent table as user store.
Passwords are hashed with bcrypt; JWT tokens are issued on successful login.
"""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.agent import Agent
from app.schemas.auth import ChangePasswordRequest, Token, UpdateProfileRequest, UserProfile


def register_user(db: Session, payload, role: str = "agent") -> dict:
    """Register a new user (Agent) with bcrypt-hashed password."""
    existing = db.query(Agent).filter(
        Agent.name == payload.username,
        Agent.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    agent = Agent(
        name=payload.username,
        password_hash=get_password_hash(payload.password),
        role=role,
        type=1,  # Default to 大代理商
        status=0,  # Enabled
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "id": agent.id,
        "username": agent.name,
        "role": agent.role,
        "is_active": agent.status == 0,
    }


def authenticate_user(db: Session, payload) -> Token:
    """Verify password and issue a JWT access token with role claim."""
    agent = db.query(Agent).filter(
        Agent.name == payload.username,
        Agent.deleted_at.is_(None),
    ).first()

    if not agent or not agent.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(payload.password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if agent.status != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        subject=str(agent.id),
        role=agent.role,
        expires_delta=timedelta(hours=24),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 60 * 60,  # 24 hours in seconds
    )


def get_user_profile(db: Session, user_id: int) -> UserProfile:
    """Get the current user's profile."""
    agent = db.query(Agent).filter(
        Agent.id == user_id,
        Agent.deleted_at.is_(None),
    ).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserProfile(
        id=agent.id,
        username=agent.name,
        role=agent.role,
        agent_type=agent.type,
        status=agent.status,
        region=agent.region if hasattr(agent, "region") else None,
        is_active=agent.status == 0,
    )


def change_password(db: Session, user_id: int, payload: ChangePasswordRequest) -> dict:
    """Change the current user's password."""
    agent = db.query(Agent).filter(
        Agent.id == user_id,
        Agent.deleted_at.is_(None),
    ).first()
    if not agent or not agent.password_hash:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not verify_password(payload.old_password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )

    agent.password_hash = get_password_hash(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


def update_profile(db: Session, user_id: int, payload: UpdateProfileRequest) -> dict:
    """Update the current user's profile (remark only for now)."""
    agent = db.query(Agent).filter(
        Agent.id == user_id,
        Agent.deleted_at.is_(None),
    ).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if payload.remark is not None:
        agent.remark = payload.remark
    db.commit()

    return {
        "id": agent.id,
        "username": agent.name,
        "role": agent.role,
        "remark": agent.remark,
    }
