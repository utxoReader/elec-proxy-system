"""Authentication router."""

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.schemas.auth import (
    ChangePasswordRequest,
    Token,
    UpdateProfileRequest,
    UserProfile,
    UserLogin,
)
from app.schemas.common import ApiResponse
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Register a new user account."""
    try:
        result = auth_service.register_user(db, payload)
        return ApiResponse(message="User registered", data=result)
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            error=e.detail,
        )


@router.post("/login")
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> ApiResponse[Token]:
    """Authenticate and receive a JWT access token."""
    try:
        token = auth_service.authenticate_user(db, payload)
        return ApiResponse(message="Login successful", data=token)
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            error=e.detail,
        )


@router.get("/me")
def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UserProfile]:
    """Get current user profile."""
    profile = auth_service.get_user_profile(db, current_user.user_id)
    return ApiResponse(message="OK", data=profile)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Change the current user's password."""
    try:
        result = auth_service.change_password(db, current_user.user_id, payload)
        return ApiResponse(message="Password changed", data=result)
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            error=e.detail,
        )


@router.get("/profile")
def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UserProfile]:
    """Get current user profile (alias for /me)."""
    profile = auth_service.get_user_profile(db, current_user.user_id)
    return ApiResponse(message="OK", data=profile)


@router.put("/profile")
def update_profile(
    payload: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Update current user profile."""
    try:
        result = auth_service.update_profile(db, current_user.user_id, payload)
        return ApiResponse(message="Profile updated", data=result)
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            error=e.detail,
        )


@router.post("/logout")
def logout(
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Logout (stateless — client discards token)."""
    return ApiResponse(message="Logged out", data={"username": current_user.username})
