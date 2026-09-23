from __future__ import annotations
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, desc, asc, text
from sqlalchemy.orm import Session, selectinload, joinedload

from ..config import settings
from ..database import get_db
from ..models import RateItem, SourceFile, CESMMSection, RateItemCESMMSection
from ..schemas import RateItemOut, RateItemSearchResponse, FilterOptionsResponse, CESMMSectionOut, RateItemCESMMOut
from ..services.cesmm_service import get_all_cesmm_sections, seed_cesmm_sections

router = APIRouter(prefix="/rates", tags=["Rates"])

@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)):
    """Returns available distinct filter values across all stored rate items."""
    sectors_db = db.scalars(
        select(RateItem.sector).distinct().where(RateItem.sector.isnot(None)).order_by(RateItem.sector)
    ).all()
    rate_systems_db = db.scalars(
        select(RateItem.rate_system).distinct().where(RateItem.rate_system.isnot(None)).order_by(RateItem.rate_system)
    ).all()
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

    # Fetch 31 standard CESMM sections
    cesmm_sections_db = get_all_cesmm_sections(db, active_only=True)
    if not cesmm_sections_db:
        cesmm_sections_db = seed_cesmm_sections(db)

    cesmm_out = [
        CESMMSectionOut(
            id=s.id,
            section_no=s.section_no,
            section_code=s.section_code,
            name=s.name,
            is_active=s.is_active,
            display_label=f"{s.section_no} - {s.name} (Section {s.section_code})",
        )
        for s in cesmm_sections_db
    ]

    # Merge with supported defaults so user can select empty sectors too
    all_sectors = list(dict.fromkeys(list(sectors_db) + settings.SUPPORTED_SECTORS))
    all_systems = list(dict.fromkeys(list(rate_systems_db) + settings.SUPPORTED_RATE_SYSTEMS))

    return FilterOptionsResponse(
        sectors=all_sectors,
        rate_systems=all_systems,
        provinces=list(provinces),
        districts=list(districts),
        years=list(years),
        revisions=list(revisions),
        dataset_types=list(dataset_types),
        vat_bases=list(vat_bases),
        categories=list(categories),
        sheets=list(sheets),
        cesmm_sections=cesmm_out,
        sector_systems=settings.SECTOR_RATE_SYSTEM_MAP,
        category_presets=settings.SECTOR_CATEGORY_PRESETS,
    )

@router.get("/search", response_model=RateItemSearchResponse)
def search_rates(
    q: str | None = Query(None, description="Keywords, item code, description or partial search"),
    sector: str | None = Query(None),
    rate_system: str | None = Query(None),
    cesmm_section_id: int | None = Query(None, description="Filter by CESMM section ID"),
    cesmm_section_no: str | None = Query(None, description="Filter by CESMM section number e.g. 04 or 4"),
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
    if sector:
        query = query.where(RateItem.sector == sector)
    if rate_system and rate_system.strip():
        rs_clean = rate_system.strip()
        if rs_clean.lower() in ("water", "water supply", "water supply rates"):
            query = query.where(RateItem.rate_system.ilike("%water%"))
        elif rs_clean.lower() == "bsr":
            query = query.where(RateItem.rate_system == "BSR")
        elif rs_clean.lower() == "hsr":
            query = query.where(RateItem.rate_system == "HSR")
        else:
            query = query.where(RateItem.rate_system == rs_clean)
    if cesmm_section_id is not None:
        query = query.where(
            RateItem.cesmm_mappings.any(
                RateItemCESMMSection.cesmm_section_id == cesmm_section_id
            )
        )
    elif cesmm_section_no and cesmm_section_no.strip():
        clean_sec_no = cesmm_section_no.strip().zfill(2)
        query = query.where(
            RateItem.cesmm_mappings.any(
                RateItemCESMMSection.cesmm_section.has(
                    CESMMSection.section_no == clean_sec_no
                )
            )
        )
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

    # Eager load CESMM mappings and source_file
    query = query.options(
        selectinload(RateItem.cesmm_mappings).joinedload(RateItemCESMMSection.cesmm_section)
    )

    items = db.scalars(query).all()
    pages = math.ceil(total / page_size) if total > 0 else 1

    result_items: list[RateItemOut] = []
    for it in items:
        item_out = RateItemOut.model_validate(it)
        item_out.original_filename = it.source_file.original_filename if it.source_file else None
        item_out.cesmm_sections = [
            RateItemCESMMOut(
                id=m.id,
                cesmm_section_id=m.cesmm_section_id,
                section_no=m.cesmm_section.section_no,
                section_code=m.cesmm_section.section_code,
                name=m.cesmm_section.name,
                is_primary=m.is_primary,
            )
            for m in sorted(it.cesmm_mappings, key=lambda x: (not x.is_primary, x.id))
            if m.cesmm_section
        ]
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
    item = db.scalar(
        select(RateItem)
        .where(RateItem.id == rate_id)
        .options(selectinload(RateItem.cesmm_mappings).joinedload(RateItemCESMMSection.cesmm_section))
    )
    if not item:
        raise HTTPException(status_code=404, detail="Rate item not found")
    out = RateItemOut.model_validate(item)
    out.original_filename = item.source_file.original_filename if item.source_file else None
    out.cesmm_sections = [
        RateItemCESMMOut(
            id=m.id,
            cesmm_section_id=m.cesmm_section_id,
            section_no=m.cesmm_section.section_no,
            section_code=m.cesmm_section.section_code,
            name=m.cesmm_section.name,
            is_primary=m.is_primary,
        )
        for m in sorted(item.cesmm_mappings, key=lambda x: (not x.is_primary, x.id))
        if m.cesmm_section
    ]
    return out
