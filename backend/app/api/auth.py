from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserLogin, TokenResponse, UserOut, ChangePasswordRequest
from ..services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    log_audit,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate user with email or username and return JWT token."""
    identifier = login_data.username_or_email.strip().lower()

    # Find user by email or username
    query = select(User).where(
        or_(
            User.email.ilike(identifier),
            User.username.ilike(identifier),
        )
    )
    user = db.scalars(query).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        log_audit(
            db=db,
            action="LOGIN_FAILED",
            entity_type="USER",
            description=f"Failed login attempt for identifier: {identifier}",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact an administrator.",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    log_audit(
        db=db,
        action="LOGIN",
        entity_type="USER",
        entity_id=str(user.id),
        description=f"User {user.email} logged in successfully ({user.role})",
        user=user,
        ip_address=request.client.host if request.client else None,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Record logout event."""
    log_audit(
        db=db,
        action="LOGOUT",
        entity_type="USER",
        entity_id=str(current_user.id),
        description=f"User {current_user.email} logged out",
        user=current_user,
    )
    return {"success": True, "message": "Logged out successfully"}

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow authenticated user to change their password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long.",
        )

    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()

    log_audit(
        db=db,
        action="CHANGE_PASSWORD",
        entity_type="USER",
        entity_id=str(current_user.id),
        description="Password updated successfully",
        user=current_user,
    )

    return {"success": True, "message": "Password changed successfully"}
