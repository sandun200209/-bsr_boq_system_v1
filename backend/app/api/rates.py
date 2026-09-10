from __future__ import annotations
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, desc, asc, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RateItem, SourceFile
from ..schemas import RateItemOut, RateItemSearchResponse, FilterOptionsResponse

router = APIRouter(prefix="/rates", tags=["Rates"])

@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)):
    """Returns available distinct filter values across all stored rate items."""
    provinces = db.scalars(
        select(RateItem.province).distinct().where(RateItem.province.isnot(None)).order_by(RateItem.province)
    ).all()
    districts = db.scalars(
        select(RateItem.district).distinct().where(RateItem.district.isnot(None)).order_by(RateItem.district)
    ).all()
    years = db.scalars(
        select(RateItem.year).distinct().where(RateItem.year.isnot(None)).order_by(desc(RateItem.year))
    ).all()
    revisions = db.scalars(
        select(RateItem.revision).distinct().where(RateItem.revision.isnot(None)).order_by(RateItem.revision)
    ).all()
    dataset_types = db.scalars(
        select(RateItem.dataset_type).distinct().where(RateItem.dataset_type.isnot(None)).order_by(RateItem.dataset_type)
    ).all()
    vat_bases = db.scalars(
        select(RateItem.vat_basis).distinct().where(RateItem.vat_basis.isnot(None)).order_by(RateItem.vat_basis)
    ).all()
    categories = db.scalars(
        select(RateItem.category_name).distinct().where(RateItem.category_name.isnot(None)).order_by(RateItem.category_name)
    ).all()
    sheets = db.scalars(
        select(RateItem.source_sheet).distinct().where(RateItem.source_sheet.isnot(None)).order_by(RateItem.source_sheet)
    ).all()

    return FilterOptionsResponse(
        provinces=list(provinces),
        districts=list(districts),
        years=list(years),
        revisions=list(revisions),
        dataset_types=list(dataset_types),
        vat_bases=list(vat_bases),
        categories=list(categories),
        sheets=list(sheets),
    )

@router.get("/search", response_model=RateItemSearchResponse)
def search_rates(
    q: str | None = Query(None, description="Keywords, item code, description or partial search"),
    province: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    revision: str | None = Query(None),
    dataset_type: str | None = Query(None),
    vat_basis: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None, description="VALID, NEEDS_REVIEW, REJECTED, APPROVED or ALL"),
    source_page: int | None = Query(None, description="Specific page number in document"),
    sheet: str | None = Query(None, description="Specific Excel sheet name"),
    sort_by: str = Query("id", enum=["id", "item_code", "description", "rate", "created_at", "year", "source_page"]),
    sort_order: str = Query("asc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(RateItem).join(SourceFile, RateItem.source_file_id == SourceFile.id)

    # Filtering
    if province:
        query = query.where(RateItem.province == province)
    if district:
        query = query.where(RateItem.district == district)
    if year:
        query = query.where(RateItem.year == year)
    if revision:
        query = query.where(RateItem.revision == revision)
    if dataset_type:
        query = query.where(RateItem.dataset_type == dataset_type)
    if vat_basis:
        query = query.where(RateItem.vat_basis == vat_basis)
    if category:
        query = query.where(
            or_(
                RateItem.category_name == category,
                RateItem.category_code == category,
            )
        )
    if status and status.upper() != "ALL":
        query = query.where(RateItem.validation_status == status.upper())
    if source_page:
        query = query.where(RateItem.source_page == source_page)
    if sheet:
        query = query.where(RateItem.source_sheet == sheet)

    # Text & Trigram search
    if q and q.strip():
        search_term = q.strip()
        terms = search_term.split()
        
        # Build search conditions using ILIKE and PostgreSQL trigram similarity if possible
        search_clauses = []
        for term in terms:
            t = f"%{term}%"
            search_clauses.append(
                or_(
                    RateItem.item_code.ilike(t),
                    RateItem.description.ilike(t),
                    RateItem.category_name.ilike(t),
                    RateItem.unit.ilike(t),
                )
            )
        query = query.where(*search_clauses)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    # Sorting
    sort_col = getattr(RateItem, sort_by, RateItem.created_at)
    order_func = asc if sort_order.lower() == "asc" else desc
    query = query.order_by(order_func(sort_col))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    items = db.scalars(query).all()
    pages = math.ceil(total / page_size) if total > 0 else 1

    result_items: list[RateItemOut] = []
    for it in items:
        item_out = RateItemOut.model_validate(it)
        item_out.original_filename = it.source_file.original_filename if it.source_file else None
        result_items.append(item_out)

    return RateItemSearchResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        items=result_items,
    )

@router.get("/{rate_id}", response_model=RateItemOut)
def get_rate_item(rate_id: int, db: Session = Depends(get_db)):
    item = db.get(RateItem, rate_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")
    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    return out
