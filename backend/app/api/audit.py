from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, AuditLog
from ..schemas import AuditLogOut
from ..services.auth_service import require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs (Admin)"])

@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    user_email: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """Retrieve audit trail logs (ADMIN only)."""
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if user_email:
        query = query.where(AuditLog.user_email.ilike(f"%{user_email.strip()}%"))

    query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    return db.scalars(query).all()
