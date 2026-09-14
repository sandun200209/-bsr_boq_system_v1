from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RateItem, SourceFile, User
from ..schemas import RateItemOut, RateItemUpdate, ReviewBulkActionRequest
from ..services.validation_service import normalize_unit, detect_category_from_code
from ..services.auth_service import get_current_user_optional, log_audit

router = APIRouter(prefix="/review", tags=["Review Queue"])

@router.get("", response_model=dict)
def get_review_queue(
    source_file_id: int | None = Query(None),
    sector: str | None = Query(None),
    rate_system: str | None = Query(None),
    status: str | None = Query("NEEDS_REVIEW", description="VALID, NEEDS_REVIEW, REJECTED, APPROVED, or ALL"),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(RateItem).join(SourceFile, RateItem.source_file_id == SourceFile.id)

    if source_file_id:
        query = query.where(RateItem.source_file_id == source_file_id)
    if sector:
        query = query.where(RateItem.sector == sector)
    if rate_system:
        query = query.where(RateItem.rate_system == rate_system)
    if status and status.upper() != "ALL":
        query = query.where(RateItem.validation_status == status.upper())
    if category:
        query = query.where(RateItem.category_name == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    query = query.order_by(RateItem.confidence_score.asc(), desc(RateItem.created_at)).offset(offset).limit(page_size)
    items = db.scalars(query).all()

    result_items: list[RateItemOut] = []
    for it in items:
        item_out = RateItemOut.model_validate(it)
        item_out.original_filename = it.source_file.original_filename if it.source_file else None
        result_items.append(item_out)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result_items,
    }

@router.patch("/{rate_id}", response_model=RateItemOut)
def update_review_item(
    rate_id: int,
    payload: RateItemUpdate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    if payload.item_code is not None:
        item.item_code = payload.item_code.strip()
    if payload.description is not None:
        item.description = payload.description.strip()
    if payload.unit is not None:
        norm_unit, _ = normalize_unit(payload.unit)
        item.unit = norm_unit
    if payload.rate is not None:
        item.rate = payload.rate
    if payload.category_name is not None:
        item.category_name = payload.category_name.strip()
    if payload.validation_status is not None:
        item.validation_status = payload.validation_status.upper()
        if item.validation_status == "APPROVED":
            item.verified_at = datetime.utcnow()
    if payload.validation_notes is not None:
        item.validation_notes = payload.validation_notes

    if current_user:
        item.updated_by_email = current_user.email

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action="UPDATE_RATE_ITEM",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Updated item {item.item_code}: status={item.validation_status}, rate={item.rate}",
        user=current_user,
    )

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/{rate_id}/approve", response_model=RateItemOut)
def approve_review_item(
    rate_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    item.validation_status = "APPROVED"
    item.verified_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    if current_user:
        item.updated_by_email = current_user.email

    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action="APPROVE_RATE_ITEM",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Approved item {item.item_code}",
        user=current_user,
    )

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/{rate_id}/reject", response_model=RateItemOut)
def reject_review_item(
    rate_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    item.validation_status = "REJECTED"
    item.updated_at = datetime.utcnow()
    if current_user:
        item.updated_by_email = current_user.email

    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action="REJECT_RATE_ITEM",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Rejected item {item.item_code}",
        user=current_user,
    )

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/bulk-action", response_model=dict)
def bulk_review_action(
    payload: ReviewBulkActionRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    if not payload.item_ids:
        return {"updated": 0, "message": "No item IDs provided"}

    target_status = "APPROVED" if payload.action.upper() == "APPROVE" else "REJECTED"
    now = datetime.utcnow()

    values_dict = {
        "validation_status": target_status,
        "verified_at": now if target_status == "APPROVED" else None,
        "updated_at": now,
    }
    if current_user:
        values_dict["updated_by_email"] = current_user.email

    stmt = (
        update(RateItem)
        .where(RateItem.id.in_(payload.item_ids))
        .values(**values_dict)
    )
    result = db.execute(stmt)
    db.commit()

    log_audit(
        db=db,
        action=f"BULK_{target_status}",
        entity_type="RATE_ITEM",
        description=f"Bulk {target_status} applied to {result.rowcount} items",
        user=current_user,
    )

    return {
        "updated": result.rowcount,
        "action": target_status,
        "message": f"Successfully updated {result.rowcount} items to {target_status}."
    }

@router.post("/document/{doc_id}/approve-valid", response_model=dict)
def approve_valid_document_items(
    doc_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Approves all VALID items for a given uploaded document in one click."""
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    now = datetime.utcnow()
    values_dict = {"validation_status": "APPROVED", "verified_at": now, "updated_at": now}
    if current_user:
        values_dict["updated_by_email"] = current_user.email

    stmt = (
        update(RateItem)
        .where(RateItem.source_file_id == doc_id, RateItem.validation_status == "VALID")
        .values(**values_dict)
    )
    result = db.execute(stmt)
    db.commit()

    log_audit(
        db=db,
        action="APPROVE_DOCUMENT_VALID",
        entity_type="SOURCE_FILE",
        entity_id=str(doc_id),
        description=f"Approved {result.rowcount} valid items for document {doc.original_filename}",
        user=current_user,
    )

    return {
        "document_id": doc_id,
        "approved_count": result.rowcount,
        "message": f"Approved {result.rowcount} valid items."
    }
