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

def _apply_rate_filters(
    query,
    sector: str | None = None,
    rate_system: str | None = None,
    cesmm_section_no: str | None = None,
    cesmm_section_id: int | None = None,
    category: str | None = None,
    province: str | None = None,
    district: str | None = None,
    year: int | None = None,
    revision: str | None = None,
    dataset_type: str | None = None,
    vat_basis: str | None = None,
    sheet: str | None = None,
    status: str | None = None,
    source_page: int | None = None,
):
    """Context-aware filter helper applying exact cascading constraints."""
    if sector and sector.strip():
        query = query.where(RateItem.sector == sector.strip())
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
    if category and category.strip():
        cat = category.strip()
        query = query.where(
            or_(
                RateItem.category_name == cat,
                RateItem.category_code == cat,
            )
        )
    if province and province.strip():
        query = query.where(RateItem.province == province.strip())
    if district and district.strip():
        query = query.where(RateItem.district == district.strip())
    if year is not None:
        query = query.where(RateItem.year == year)
    if revision and revision.strip():
        query = query.where(RateItem.revision == revision.strip())
    if dataset_type and dataset_type.strip():
        query = query.where(RateItem.dataset_type == dataset_type.strip())
    if vat_basis and vat_basis.strip():
        query = query.where(RateItem.vat_basis == vat_basis.strip())
    if sheet and sheet.strip():
        query = query.where(RateItem.source_sheet == sheet.strip())
    if status and status.strip() and status.upper() != "ALL":
        query = query.where(RateItem.validation_status == status.strip().upper())
    if source_page is not None:
        query = query.where(RateItem.source_page == source_page)
    return query

@router.get("/filters", response_model=FilterOptionsResponse)
@router.get("/filter-options", response_model=FilterOptionsResponse)
def get_filter_options(
    sector: str | None = Query(None),
    rate_system: str | None = Query(None),
    cesmm_section_no: str | None = Query(None),
    cesmm_section_id: int | None = Query(None),
    category: str | None = Query(None),
    province: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    revision: str | None = Query(None),
    dataset_type: str | None = Query(None),
    vat_basis: str | None = Query(None),
    sheet: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Returns available distinct filter values across stored rate items, dynamically cascading."""
    # 1. Rate systems (Step 1) - Always all available rate books
    rate_systems_db = db.scalars(
        select(RateItem.rate_system).distinct().where(RateItem.rate_system.isnot(None)).order_by(RateItem.rate_system)
    ).all()
    all_systems = list(dict.fromkeys(list(rate_systems_db) + settings.SUPPORTED_RATE_SYSTEMS))

    sectors_db = db.scalars(
        select(RateItem.sector).distinct().where(RateItem.sector.isnot(None)).order_by(RateItem.sector)
    ).all()
    all_sectors = list(dict.fromkeys(list(sectors_db) + settings.SUPPORTED_SECTORS))

    # 2. CESMM Sections (Step 2) - Only sections with mapped items for selected rate_system
    if rate_system and rate_system.strip():
        cesmm_q = (
            select(CESMMSection)
            .join(RateItemCESMMSection, RateItemCESMMSection.cesmm_section_id == CESMMSection.id)
            .join(RateItem, RateItem.id == RateItemCESMMSection.rate_item_id)
            .where(CESMMSection.is_active == True)
        )
        cesmm_q = _apply_rate_filters(cesmm_q, rate_system=rate_system, sector=sector)
        cesmm_sections_db = db.scalars(cesmm_q.distinct().order_by(CESMMSection.section_no)).all()
    else:
        # Full master list if no rate system selected
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

    # 3. Category / Trade (Step 3) - Depends on Rate Book + CESMM Section
    cat_q = select(RateItem.category_name).distinct().where(RateItem.category_name.isnot(None))
    cat_q = _apply_rate_filters(
        cat_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
    )
    categories = db.scalars(cat_q.order_by(RateItem.category_name)).all()

    # 4. Province (Step 4) - Depends on previous (Rate Book, CESMM, Category)
    prov_q = select(RateItem.province).distinct().where(RateItem.province.isnot(None))
    prov_q = _apply_rate_filters(
        prov_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
    )
    provinces = db.scalars(prov_q.order_by(RateItem.province)).all()

    # 5. District (Step 5) - Depends on previous + Province
    dist_q = select(RateItem.district).distinct().where(RateItem.district.isnot(None))
    dist_q = _apply_rate_filters(
        dist_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
    )
    districts = db.scalars(dist_q.order_by(RateItem.district)).all()

    # 6. Year (Step 6) - Depends on previous + District
    year_q = select(RateItem.year).distinct().where(RateItem.year.isnot(None))
    year_q = _apply_rate_filters(
        year_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
    )
    years = db.scalars(year_q.order_by(desc(RateItem.year))).all()

    # 7. Revision (Step 7) - Depends on previous + Year
    rev_q = select(RateItem.revision).distinct().where(RateItem.revision.isnot(None))
    rev_q = _apply_rate_filters(
        rev_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
    )
    revisions = db.scalars(rev_q.order_by(RateItem.revision)).all()

    # 8. VAT (Step 8) - Depends on previous + Revision
    vat_q = select(RateItem.vat_basis).distinct().where(RateItem.vat_basis.isnot(None))
    vat_q = _apply_rate_filters(
        vat_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
    )
    vat_bases = db.scalars(vat_q.order_by(RateItem.vat_basis)).all()

    # 9. Sheet (Step 9) - Depends on previous + VAT
    sheet_q = select(RateItem.source_sheet).distinct().where(RateItem.source_sheet.isnot(None))
    sheet_q = _apply_rate_filters(
        sheet_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
        vat_basis=vat_basis,
    )
    sheets = db.scalars(sheet_q.order_by(RateItem.source_sheet)).all()

    # 10. Status (Step 10) - Depends on previous + Sheet
    status_q = select(RateItem.validation_status).distinct().where(RateItem.validation_status.isnot(None))
    status_q = _apply_rate_filters(
        status_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
        vat_basis=vat_basis,
        sheet=sheet,
    )
    statuses = db.scalars(status_q.order_by(RateItem.validation_status)).all()

    # 11. Source Pages (Step 11) - Distinct source pages available
    page_q = select(RateItem.source_page).distinct().where(RateItem.source_page.isnot(None))
    page_q = _apply_rate_filters(
        page_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
        vat_basis=vat_basis,
        sheet=sheet,
        status=status,
    )
    source_pages = db.scalars(page_q.order_by(RateItem.source_page)).all()

    # Total matching records with current filter combination
    count_q = select(func.count(RateItem.id))
    count_q = _apply_rate_filters(
        count_q,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
        vat_basis=vat_basis,
        sheet=sheet,
        status=status,
    )
    total_matching = db.scalar(count_q) or 0

    dataset_types = db.scalars(
        select(RateItem.dataset_type).distinct().where(RateItem.dataset_type.isnot(None)).order_by(RateItem.dataset_type)
    ).all()

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
        statuses=list(statuses),
        source_pages=list(source_pages),
        total_matching=total_matching,
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

    # Filtering via centralized cascading helper
    query = _apply_rate_filters(
        query,
        sector=sector,
        rate_system=rate_system,
        cesmm_section_no=cesmm_section_no,
        cesmm_section_id=cesmm_section_id,
        category=category,
        province=province,
        district=district,
        year=year,
        revision=revision,
        dataset_type=dataset_type,
        vat_basis=vat_basis,
        sheet=sheet,
        status=status,
        source_page=source_page,
    )

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
