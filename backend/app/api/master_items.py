from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import MasterItem, RateItemMasterMapping, RateItem
from ..schemas import (
    MasterItemOut,
    MasterItemCreate,
    MasterItemUpdate,
    MasterMappingRequest,
    MasterSuggestionOut,
    RateItemOut,
)

router = APIRouter(prefix="/master-items", tags=["Master Items"])

@router.get("", response_model=list[MasterItemOut])
def list_master_items(
    q: str | None = Query(None),
    category: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(MasterItem)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                MasterItem.master_code.ilike(term),
                MasterItem.canonical_description.ilike(term),
            )
        )
    if category:
        query = query.where(MasterItem.category == category)

    query = query.order_by(MasterItem.master_code).offset(skip).limit(limit)
    items = db.scalars(query).all()

    result: list[MasterItemOut] = []
    for item in items:
        out = MasterItemOut.model_validate(item)
        out.mapped_count = len(item.mappings)
        result.append(out)
    return result

@router.post("", response_model=MasterItemOut)
def create_master_item(payload: MasterItemCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(MasterItem).where(MasterItem.master_code == payload.master_code.strip()))
    if existing:
        raise HTTPException(status_code=400, detail=f"Master item code '{payload.master_code}' already exists.")

    item = MasterItem(
        master_code=payload.master_code.strip(),
        canonical_description=payload.canonical_description.strip(),
        canonical_unit=payload.canonical_unit.strip(),
        category=payload.category.strip() if payload.category else None,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MasterItemOut.model_validate(item)

@router.get("/{item_id}", response_model=MasterItemOut)
def get_master_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(MasterItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    out = MasterItemOut.model_validate(item)
    out.mapped_count = len(item.mappings)
    mapped_rates = []
    for mapping in item.mappings:
        if mapping.rate_item:
            r_out = RateItemOut.model_validate(mapping.rate_item)
            r_out.original_filename = mapping.rate_item.source_file.original_filename if mapping.rate_item.source_file else None
            mapped_rates.append(r_out)
    out.mapped_rates = mapped_rates
    return out

@router.put("/{item_id}", response_model=MasterItemOut)
def update_master_item(item_id: int, payload: MasterItemUpdate, db: Session = Depends(get_db)):
    item = db.get(MasterItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    if payload.master_code is not None:
        item.master_code = payload.master_code.strip()
    if payload.canonical_description is not None:
        item.canonical_description = payload.canonical_description.strip()
    if payload.canonical_unit is not None:
        item.canonical_unit = payload.canonical_unit.strip()
    if payload.category is not None:
        item.category = payload.category.strip() or None
    if payload.notes is not None:
        item.notes = payload.notes.strip() or None

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return MasterItemOut.model_validate(item)

@router.delete("/{item_id}")
def delete_master_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(MasterItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Master item not found")

    # Unlink mapped rate items
    db.execute(
        select(RateItem).where(RateItem.master_item_id == item_id)
    )
    for rate_item in db.scalars(select(RateItem).where(RateItem.master_item_id == item_id)).all():
        rate_item.master_item_id = None

    db.delete(item)
    db.commit()
    return {"success": True, "message": "Master item deleted successfully"}

@router.post("/{item_id}/map", response_model=dict)
def map_rate_to_master(item_id: int, payload: MasterMappingRequest, db: Session = Depends(get_db)):
    master = db.get(MasterItem, item_id)
    if not master:
        raise HTTPException(status_code=404, detail="Master item not found")

    rate_item = db.get(RateItem, payload.rate_item_id)
    if not rate_item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    # Remove existing mapping if any
    existing_mapping = db.scalar(
        select(RateItemMasterMapping).where(RateItemMasterMapping.rate_item_id == rate_item.id)
    )
    if existing_mapping:
        db.delete(existing_mapping)

    mapping = RateItemMasterMapping(
        master_item_id=master.id,
        rate_item_id=rate_item.id,
        confidence=1.0,
        mapped_by="user",
        mapped_at=datetime.utcnow(),
    )
    rate_item.master_item_id = master.id
    db.add(mapping)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully mapped '{rate_item.item_code}' to Master '{master.master_code}'.",
        "master_id": master.id,
        "rate_item_id": rate_item.id,
    }

@router.post("/unmap/{rate_item_id}", response_model=dict)
def unmap_rate_from_master(rate_item_id: int, db: Session = Depends(get_db)):
    rate_item = db.get(RateItem, rate_item_id)
    if not rate_item:
        raise HTTPException(status_code=404, detail="Rate item not found")

    existing_mapping = db.scalar(
        select(RateItemMasterMapping).where(RateItemMasterMapping.rate_item_id == rate_item_id)
    )
    if existing_mapping:
        db.delete(existing_mapping)

    rate_item.master_item_id = None
    db.commit()

    return {"success": True, "message": f"Unmapped rate item {rate_item_id}."}

@router.get("/suggestions/unmapped", response_model=list[MasterSuggestionOut])
def get_mapping_suggestions(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """
    Finds unmapped rate items that have keyword similarity to existing Master Items.
    Never auto-merges; returns candidates for user review and approval.
    """
    master_items = db.scalars(select(MasterItem)).all()
    if not master_items:
        return []

    unmapped_rates = db.scalars(
        select(RateItem)
        .where(RateItem.master_item_id.is_(None), RateItem.description.isnot(None))
        .limit(100)
    ).all()

    suggestions: list[MasterSuggestionOut] = []
    for rate in unmapped_rates:
        if not rate.description:
            continue
        rate_words = set(rate.description.lower().split())

        best_master: MasterItem | None = None
        best_sim = 0.0

        for master in master_items:
            master_words = set(master.canonical_description.lower().split())
            if not master_words:
                continue
            common = rate_words.intersection(master_words)
            sim = len(common) / len(master_words)
            if sim > best_sim and sim >= 0.4:
                best_sim = sim
                best_master = master

        if best_master and best_sim >= 0.4:
            r_out = RateItemOut.model_validate(rate)
            r_out.original_filename = rate.source_file.original_filename if rate.source_file else None
            suggestions.append(
                MasterSuggestionOut(
                    rate_item=r_out,
                    suggested_master_id=best_master.id,
                    master_code=best_master.master_code,
                    canonical_description=best_master.canonical_description,
                    similarity=round(best_sim, 2),
                )
            )
            if len(suggestions) >= limit:
                break

    return suggestions
