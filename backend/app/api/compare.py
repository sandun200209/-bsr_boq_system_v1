from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import RateItem, MasterItem
from ..schemas import CompareResponse
from ..services.compare_service import CompareService

router = APIRouter(prefix="/compare", tags=["Compare"])

@router.get("", response_model=CompareResponse)
def compare_rates(
    provinces: list[str] = Query(None),
    districts: list[str] = Query(None),
    years: list[int] = Query(None),
    revisions: list[str] = Query(None),
    category: str | None = Query(None),
    vat_basis: str | None = Query(None),
    q: str | None = Query(None, description="Keyword or item code search"),
    master_item_id: int | None = Query(None, description="Filter specifically by approved Master Item ID"),
    base_item_id: int | None = Query(None, description="Specific item ID to use as calculation baseline"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = (
        select(RateItem)
        .options(
            joinedload(RateItem.source_file),
            joinedload(RateItem.master_item),
        )
        .where(
            RateItem.validation_status.in_(["VALID", "APPROVED"]),
            RateItem.rate.isnot(None),
            RateItem.rate > 0,
        )
    )

    if master_item_id:
        query = query.where(RateItem.master_item_id == master_item_id)

    if provinces:
        query = query.where(RateItem.province.in_(provinces))
    if districts:
        query = query.where(RateItem.district.in_(districts))
    if years:
        query = query.where(RateItem.year.in_(years))
    if revisions:
        query = query.where(RateItem.revision.in_(revisions))
    if category:
        query = query.where(
            or_(
                RateItem.category_name == category,
                RateItem.category_code == category,
            )
        )
    if vat_basis:
        query = query.where(RateItem.vat_basis == vat_basis)

    if q and q.strip():
        search_terms = q.strip().split()
        for term in search_terms:
            t = f"%{term}%"
            query = query.where(
                or_(
                    RateItem.item_code.ilike(t),
                    RateItem.description.ilike(t),
                    RateItem.category_name.ilike(t),
                    RateItem.category_code.ilike(t),
                )
            )

    query = query.order_by(RateItem.item_code, desc(RateItem.year)).limit(limit)
    items = db.scalars(query).all()

    return CompareService.build_comparison(items=items, base_item_id=base_item_id)
