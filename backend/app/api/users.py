from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserCreate, UserUpdate
from ..services.auth_service import (
    get_password_hash,
    require_role,
    log_audit,
)

router = APIRouter(prefix="/users", tags=["Users (Admin)"])

VALID_ROLES = {"ADMIN", "MANAGER", "USER", "VIEWER"}

@router.get("", response_model=list[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """List all user accounts (ADMIN only)."""
    query = select(User).order_by(desc(User.created_at)).offset(skip).limit(limit)
    return db.scalars(query).all()

@router.post("", response_model=UserOut)
def create_user(
    data: UserCreate,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """Create a new user account (ADMIN only)."""
    email = data.email.strip().lower()
    username = data.username.strip().lower()
    role = data.role.upper()

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Valid: {', '.join(sorted(VALID_ROLES))}",
        )

    # Check email or username duplicate
    existing = db.scalars(
        select(User).where((User.email == email) | (User.username == username))
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with that email or username already exists.",
        )

    if len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long.",
        )

    new_user = User(
        email=email,
        username=username,
        full_name=data.full_name.strip(),
        hashed_password=get_password_hash(data.password),
        role=role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(
        db=db,
        action="USER_CREATED",
        entity_type="USER",
        entity_id=str(new_user.id),
        description=f"Created user {new_user.email} with role {new_user.role}",
        user=current_user,
    )

    return new_user

@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """Update user role, status, or details (ADMIN only)."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if data.full_name is not None:
        target.full_name = data.full_name.strip()

    if data.role is not None:
        role = data.role.upper()
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role '{role}'. Valid: {', '.join(sorted(VALID_ROLES))}",
            )
        target.role = role

    if data.is_active is not None:
        # Prevent admin deactivating own account
        if target.id == current_user.id and not data.is_active:
            raise HTTPException(
                status_code=400,
                detail="You cannot deactivate your own administrative account.",
            )
        target.is_active = data.is_active

    if data.password:
        if len(data.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long.",
            )
        target.hashed_password = get_password_hash(data.password)

    db.commit()
    db.refresh(target)

    log_audit(
        db=db,
        action="USER_UPDATED",
        entity_type="USER",
        entity_id=str(target.id),
        description=f"Updated user {target.email} (role: {target.role}, active: {target.is_active})",
        user=current_user,
    )

    return target

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """Deactivate or remove user (ADMIN only)."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own administrative account.",
        )

    target.is_active = False
    db.commit()

    log_audit(
        db=db,
        action="USER_DEACTIVATED",
        entity_type="USER",
        entity_id=str(target.id),
        description=f"Deactivated user {target.email}",
        user=current_user,
    )

    return {"success": True, "message": f"User {target.email} has been deactivated."}
