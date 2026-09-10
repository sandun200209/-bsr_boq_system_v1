from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RateItem, SourceFile
from ..schemas import RateItemOut, RateItemUpdate, ReviewBulkActionRequest
from ..services.validation_service import normalize_unit, detect_category_from_code

router = APIRouter(prefix="/review", tags=["Review Queue"])

@router.get("", response_model=dict)
def get_review_queue(
    source_file_id: int | None = Query(None),
    status: str | None = Query("NEEDS_REVIEW", description="VALID, NEEDS_REVIEW, REJECTED, APPROVED, or ALL"),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(RateItem).join(SourceFile, RateItem.source_file_id == SourceFile.id)

    if source_file_id:
        query = query.where(RateItem.source_file_id == source_file_id)
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
def update_review_item(rate_id: int, payload: RateItemUpdate, db: Session = Depends(get_db)):
    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    if payload.item_code is not None:
        item.item_code = payload.item_code.strip() or None
        cat_code, cat_name = detect_category_from_code(item.item_code, item.category_name)
        if cat_code:
            item.category_code = cat_code
        if not item.category_name and cat_name:
            item.category_name = cat_name

    if payload.description is not None:
        item.description = payload.description.strip() or None

    if payload.unit is not None:
        item.unit = normalize_unit(payload.unit) or payload.unit.strip()

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

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/{rate_id}/approve", response_model=RateItemOut)
def approve_review_item(rate_id: int, db: Session = Depends(get_db)):
    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    item.validation_status = "APPROVED"
    item.verified_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/{rate_id}/reject", response_model=RateItemOut)
def reject_review_item(rate_id: int, db: Session = Depends(get_db)):
    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    item.validation_status = "REJECTED"
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out

@router.post("/bulk-action", response_model=dict)
def bulk_review_action(payload: ReviewBulkActionRequest, db: Session = Depends(get_db)):
    if not payload.item_ids:
        return {"updated": 0, "message": "No item IDs provided"}

    target_status = "APPROVED" if payload.action.upper() == "APPROVE" else "REJECTED"
    now = datetime.utcnow()

    stmt = (
        update(RateItem)
        .where(RateItem.id.in_(payload.item_ids))
        .values(
            validation_status=target_status,
            verified_at=now if target_status == "APPROVED" else None,
            updated_at=now,
        )
    )
    result = db.execute(stmt)
    db.commit()

    return {
        "updated": result.rowcount,
        "action": target_status,
        "message": f"Successfully updated {result.rowcount} items to {target_status}."
    }

@router.post("/document/{doc_id}/approve-valid", response_model=dict)
def approve_valid_document_items(doc_id: int, db: Session = Depends(get_db)):
    """Approves all VALID items for a given uploaded document in one click."""
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    now = datetime.utcnow()
    stmt = (
        update(RateItem)
        .where(RateItem.source_file_id == doc_id, RateItem.validation_status == "VALID")
        .values(validation_status="APPROVED", verified_at=now, updated_at=now)
    )
    result = db.execute(stmt)
    db.commit()

    return {
        "document_id": doc_id,
        "approved_count": result.rowcount,
        "message": f"Approved {result.rowcount} valid items."
    }
