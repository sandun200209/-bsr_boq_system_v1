from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Callable
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import User, AuditLog

logger = logging.getLogger("bsr_rate_hub.auth")

# OAuth2 scheme - tokenUrl points to login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt(10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None

def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """Optional user resolver (for endpoints that permit public reads but track auth)."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        user = db.get(User, int(user_id))
        if user and user.is_active:
            return user
    except Exception:
        pass
    return None

def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Enforce valid authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.get(User, int(user_id))
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    return user

def require_role(allowed_roles: list[str]) -> Callable:
    """Dependency factory enforcing role-based permissions."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}. Your role is '{current_user.role}'."
            )
        return current_user
    return role_checker

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    description: str | None = None,
    user: User | None = None,
    ip_address: str | None = None,
):
    """Record an audit trail event."""
    try:
        audit = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else "system",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            description=description,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        logger.warning(f"Could not record audit log: {e}")
        db.rollback()
