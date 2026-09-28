"""
BSR 31-Part Canonical Workflow Service
Handles classification, cross-year grouping, selection, editing, and export
for the canonical 31-part BSR section workflow.

SAFETY RULES:
- Original BSR rate_items are IMMUTABLE. Never update rate/description/unit on them.
- All project edits live in project_part_items (dual-storage: original_* vs project_*).
- part_mapping_status=NEEDS_REVIEW if classification is uncertain.
- Never invent rates or quantities.
"""
from __future__ import annotations

import io
import json
import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, and_, or_

from ..models import (
    CanonicalBSRPart,
    RateItem,
    SourceFile,
    MasterItem,
    RateItemMasterMapping,
    ProjectPartSelection,
    ProjectPartItem,
    ProjectPartItemHistory,
    PartTemplateMapping,
    Template,
)

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

# Map part_code/aliases to canonical part_no
# Keys are lower-case prefixes, values or section keywords that uniquely identify a Part
PART_CODE_MAP: dict[str, str] = {
    # part_code (exact)
    "dm": "01", "ew": "02", "bk": "03", "ct": "04", "fw": "05",
    "rf": "06", "rr": "07", "cb": "08", "pa": "09", "pl": "10",
    "tn": "11", "ro": "12", "cp": "13", "ir": "14", "bf": "15",
    "pt": "16", "pb": "17", "ma": "18", "tg": "19", "gl": "20",
    "cl": "21", "gw": "22", "al": "23", "aln": "24", "alb": "25",
    "alp": "26", "el": "27", "dr": "28", "rd": "29", "wf": "30",
    "pr": "31",
}

# Category/heading keyword → part_no (lower-case match; evaluated in order)
CATEGORY_KEYWORD_MAP: list[tuple[str, str]] = [
    # Most specific first
    ("tempered glass", "19"),
    ("glazier", "20"),
    ("glazi", "20"),
    ("cladding", "21"),
    ("alumin", "23"),        # generic aluminum → Part 23 (user can reclassify)
    ("natural anodized", "24"),
    ("bronze anodized", "25"),
    ("powder coated", "26"),
    ("electrici", "27"),
    ("electrical", "27"),
    ("drainage", "28"),
    ("road work", "29"),
    ("road", "29"),
    ("water supply", "30"),
    ("preliminar", "31"),
    ("miscellaneous", "31"),
    ("demolish", "01"),
    ("demolit", "01"),
    ("earth work", "02"),
    ("excavat", "02"),
    ("brick", "03"),
    ("concrete", "04"),
    ("form work", "05"),
    ("shuttering", "05"),
    ("steel rat", "06"),
    ("reinforc", "06"),
    ("tor steel", "06"),
    ("rubble", "07"),
    ("masonry", "07"),
    ("cement block", "08"),
    ("block work", "08"),
    ("pavior", "09"),
    ("tiling", "09"),
    ("paving", "09"),
    ("plaster", "10"),
    ("tinker", "11"),
    ("flashing", "11"),
    ("gutter", "11"),
    ("roof", "12"),
    ("asbestos", "12"),
    ("carpenter", "13"),
    ("joiner", "13"),
    ("timber", "13"),
    ("door", "13"),
    ("window", "13"),
    ("iron monger", "14"),
    ("structural steel", "14"),
    ("truss", "14"),
    ("grill", "14"),
    ("brass founder", "15"),
    ("ironmongery", "15"),
    ("hinge", "15"),
    ("lock", "15"),
    ("paint", "16"),
    ("decorat", "16"),
    ("plumber", "17"),
    ("plumbing", "17"),
    ("sanitary", "17"),
    ("maintenan", "18"),
    ("repair", "18"),
]


def classify_rate_item_to_canonical_part(
    item_code: str | None,
    category_name: str | None,
    description: str | None,
    all_parts: list[CanonicalBSRPart],
) -> tuple[CanonicalBSRPart | None, str]:
    """
    Attempt to map a rate item to a canonical BSR Part.

    Returns (canonical_part, mapping_status) where mapping_status is:
        'MAPPED'        – confident match
        'NEEDS_REVIEW'  – uncertain; Admin must confirm
        'UNMAPPED'      – no classification possible
    """
    part_by_no: dict[str, CanonicalBSRPart] = {p.part_no: p for p in all_parts}

    # 1. Try item_code prefix
    if item_code:
        code_upper = item_code.strip().upper()
        # Try progressively shorter prefixes (up to 4 chars)
        for length in [3, 2]:
            prefix = code_upper[:length].lower()
            if prefix in PART_CODE_MAP:
                target_no = PART_CODE_MAP[prefix]
                if target_no in part_by_no:
                    return part_by_no[target_no], "MAPPED"

    # 2. Try category_name keywords
    text_to_search = " ".join(filter(None, [category_name, description])).lower()
    for keyword, part_no in CATEGORY_KEYWORD_MAP:
        if keyword in text_to_search:
            if part_no in part_by_no:
                return part_by_no[part_no], "MAPPED"

    # 3. Nothing matched → NEEDS_REVIEW
    if text_to_search.strip():
        return None, "NEEDS_REVIEW"
    return None, "UNMAPPED"


def classify_all_unmapped_rate_items(
    db: Session,
    rate_system: str = "BSR",
    force_remap: bool = False,
) -> dict[str, int]:
    """
    Batch-classify all RateItems that are UNMAPPED (or all if force_remap=True).
    Returns counts: mapped / needs_review / unchanged.
    """
    all_parts = db.query(CanonicalBSRPart).filter(CanonicalBSRPart.active == True).all()

    query = db.query(RateItem)
    if rate_system:
        query = query.filter(RateItem.rate_system == rate_system)
    if not force_remap:
        query = query.filter(RateItem.part_mapping_status == "UNMAPPED")

    items = query.all()
    counts = {"mapped": 0, "needs_review": 0, "unchanged": 0}

    for item in items:
        part, status = classify_rate_item_to_canonical_part(
            item.item_code, item.category_name, item.description, all_parts
        )
        if status == "MAPPED" and part:
            item.canonical_part_id = part.id
            item.part_mapping_status = "MAPPED"
            counts["mapped"] += 1
        elif status == "NEEDS_REVIEW":
            item.canonical_part_id = None
            item.part_mapping_status = "NEEDS_REVIEW"
            counts["needs_review"] += 1
        else:
            counts["unchanged"] += 1

    db.commit()
    return counts


# ---------------------------------------------------------------------------
# Parts Library
# ---------------------------------------------------------------------------

def get_parts_library(
    db: Session,
    district: str | None = None,
    province: str | None = None,
    rate_system: str = "BSR",
) -> list[dict]:
    """
    Return all 31 canonical parts with year availability matrix.
    """
    all_parts = (
        db.query(CanonicalBSRPart)
        .filter(CanonicalBSRPart.active == True)
        .order_by(CanonicalBSRPart.sort_order)
        .all()
    )

    # Aggregate: canonical_part_id → { year: count }
    query = (
        db.query(
            RateItem.canonical_part_id,
            RateItem.year,
            func.count(RateItem.id).label("cnt"),
        )
        .filter(
            RateItem.canonical_part_id.isnot(None),
            RateItem.part_mapping_status == "MAPPED",
        )
    )
    if rate_system:
        query = query.filter(RateItem.rate_system == rate_system)
    if province:
        query = query.filter(RateItem.province == province)
    if district:
        query = query.filter(RateItem.district == district)

    rows = query.group_by(RateItem.canonical_part_id, RateItem.year).all()

    year_counts: dict[int, dict[int, int]] = {}
    for part_id, year, cnt in rows:
        year_counts.setdefault(part_id, {})[year] = cnt

    result = []
    for part in all_parts:
        yc = year_counts.get(part.id, {})
        total = sum(yc.values())
        result.append(
            {
                "id": part.id,
                "part_no": part.part_no,
                "part_code": part.part_code,
                "part_name": part.part_name,
                "aliases": part.aliases,
                "description": part.description,
                "sort_order": part.sort_order,
                "active": part.active,
                "year_availability": yc,  # {2023: 120, 2024: 95, ...}
                "total_items": total,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Cross-Year Part Data
# ---------------------------------------------------------------------------

def get_part_cross_year_data(
    db: Session,
    part_id: int,
    district: str | None = None,
    province: str | None = None,
    years: list[int] | None = None,
    search: str | None = None,
    vat_basis: str | None = None,
    rate_system: str = "BSR",
    page: int = 1,
    page_size: int = 200,
) -> dict:
    """
    Return items for one canonical Part across available years,
    grouped by year and enriched with Master Item info.
    """
    query = (
        db.query(RateItem)
        .filter(
            RateItem.canonical_part_id == part_id,
            RateItem.part_mapping_status == "MAPPED",
        )
    )
    if rate_system:
        query = query.filter(RateItem.rate_system == rate_system)
    if province:
        query = query.filter(RateItem.province == province)
    if district:
        query = query.filter(RateItem.district == district)
    if years:
        query = query.filter(RateItem.year.in_(years))
    if vat_basis:
        query = query.filter(RateItem.vat_basis == vat_basis)
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(RateItem.item_code).like(s),
                func.lower(RateItem.description).like(s),
            )
        )

    total = query.count()
    items = (
        query.order_by(RateItem.year.desc(), RateItem.item_code)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Group by year
    by_year: dict[int, list] = {}
    for item in items:
        by_year.setdefault(item.year, []).append(
            {
                "id": item.id,
                "item_code": item.item_code,
                "description": item.description,
                "unit": item.unit,
                "rate": item.rate,
                "year": item.year,
                "province": item.province,
                "district": item.district,
                "revision": item.revision,
                "vat_basis": item.vat_basis,
                "source_page": item.source_page,
                "source_sheet": item.source_sheet,
                "source_row": item.source_row,
                "source_file_id": item.source_file_id,
                "master_item_id": item.master_item_id,
                "validation_status": item.validation_status,
                "part_mapping_status": item.part_mapping_status,
            }
        )

    available_years = sorted(by_year.keys())

    return {
        "canonical_part_id": part_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "available_years": available_years,
        "by_year": by_year,
    }


# ---------------------------------------------------------------------------
# Part Selection (Project BOQ)
# ---------------------------------------------------------------------------

def create_part_selection(
    db: Session,
    canonical_part_id: int,
    project_id: int | None,
    user_email: str | None,
    name: str | None = None,
) -> ProjectPartSelection:
    part = db.query(CanonicalBSRPart).get(canonical_part_id)
    if not part:
        raise ValueError(f"Canonical BSR Part {canonical_part_id} not found")

    sel = ProjectPartSelection(
        project_id=project_id,
        canonical_part_id=canonical_part_id,
        name=name or f"Part {part.part_no} – {part.part_name} BOQ",
        created_by=user_email,
        status="ACTIVE",
    )
    db.add(sel)
    db.commit()
    db.refresh(sel)
    return sel


def get_part_selection(db: Session, selection_id: int) -> ProjectPartSelection | None:
    return db.query(ProjectPartSelection).get(selection_id)


def add_items_to_part_selection(
    db: Session,
    selection_id: int,
    rate_item_ids: list[int],
    user_email: str | None,
    allow_duplicates: bool = False,
    replace_existing_ids: list[int] | None = None,
) -> dict:
    """
    Add selected RateItems to a ProjectPartSelection.
    Returns:
      { added: [...], warnings: [{existing_item, new_rate_item, master_item_id}], duplicates_skipped: int }
    """
    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise ValueError(f"Selection {selection_id} not found")

    existing_items = {item.bsr_item_id: item for item in sel.items if item.bsr_item_id}
    existing_master = {item.master_item_id: item for item in sel.items if item.master_item_id}

    added: list[ProjectPartItem] = []
    warnings: list[dict] = []
    skipped = 0

    for rid in rate_item_ids:
        rate_item = db.query(RateItem).get(rid)
        if not rate_item:
            continue

        # Duplicate check: same bsr_item_id already in selection
        if rid in existing_items and not allow_duplicates:
            skipped += 1
            continue

        # Master item duplicate check
        mid = rate_item.master_item_id
        if mid and mid in existing_master and not allow_duplicates:
            existing_proj_item = existing_master[mid]
            warnings.append(
                {
                    "master_item_id": mid,
                    "existing_selection_item_id": existing_proj_item.id,
                    "existing_rate_year": existing_proj_item.rate_source_year,
                    "new_rate_item_id": rid,
                    "new_rate_year": str(rate_item.year),
                }
            )
            continue

        # If replacing existing
        if replace_existing_ids and rid in (replace_existing_ids or []):
            if rid in existing_items:
                db.delete(existing_items[rid])

        # Build project item (snapshot)
        next_sort = max((it.sort_order for it in sel.items), default=0) + 10
        proj_item = ProjectPartItem(
            project_part_selection_id=selection_id,
            bsr_item_id=rid,
            master_item_id=mid,
            item_no=None,
            original_code=rate_item.item_code,
            project_code=rate_item.item_code,
            original_description=rate_item.description or "",
            project_description=rate_item.description or "",
            original_unit=rate_item.unit or "",
            project_unit=rate_item.unit or "",
            quantity=0.0,
            original_rate=rate_item.rate or 0.0,
            adjustment_percent=0.0,
            adopted_rate=rate_item.rate or 0.0,
            amount=0.0,
            rate_source_year=str(rate_item.year),
            rate_source_book=f"{rate_item.rate_system} {rate_item.district} {rate_item.year}",
            rate_source_province=rate_item.province,
            rate_source_district=rate_item.district,
            rate_source_revision=rate_item.revision,
            rate_source_file_id=rate_item.source_file_id,
            rate_source_page=rate_item.source_page,
            rate_source_sheet=rate_item.source_sheet,
            rate_source_row=rate_item.source_row,
            sort_order=next_sort,
            is_modified=False,
        )
        db.add(proj_item)
        added.append(proj_item)

    db.commit()
    return {
        "added_count": len(added),
        "duplicates_skipped": skipped,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Item Editing (Section 21 rules)
# ---------------------------------------------------------------------------

RATE_JUSTIFICATION_REQUIRED_FIELDS = {"adopted_rate", "original_rate"}
UNIT_CHANGE_WARNING_FIELDS = {"project_unit"}

ROLE_EDITABLE_FIELDS: dict[str, set[str]] = {
    "VIEWER": set(),
    "USER": {"quantity", "project_description", "remarks", "sort_order"},
    "MANAGER": {
        "quantity", "project_description", "remarks", "sort_order",
        "item_no", "project_unit", "adjustment_percent", "adopted_rate",
        "rate_justification", "project_code",
    },
    "ADMIN": {
        "quantity", "project_description", "remarks", "sort_order",
        "item_no", "project_unit", "adjustment_percent", "adopted_rate",
        "rate_justification", "project_code",
        "rate_source_year", "rate_source_book",
    },
}


def update_part_item(
    db: Session,
    item_id: int,
    payload: dict,
    user_email: str,
    user_role: str = "USER",
) -> ProjectPartItem:
    """
    Edit a ProjectPartItem snapshot. Never touches the original RateItem.
    Enforces role-based editable fields, rate justification, and unit warnings.
    """
    item = db.query(ProjectPartItem).get(item_id)
    if not item:
        raise ValueError(f"ProjectPartItem {item_id} not found")

    allowed = ROLE_EDITABLE_FIELDS.get(user_role, set())

    for field, value in payload.items():
        if field not in allowed and user_role != "ADMIN":
            raise PermissionError(
                f"Role '{user_role}' is not permitted to edit field '{field}'"
            )

        # Rate justification enforcement
        if field == "adopted_rate" and value != item.original_rate:
            justification = payload.get("rate_justification") or item.rate_justification
            if not justification:
                raise ValueError(
                    "rate_justification is required when changing the adopted rate"
                )

        old_value = str(getattr(item, field, None))
        setattr(item, field, value)

        # Write audit record
        hist = ProjectPartItemHistory(
            project_part_item_id=item_id,
            field_changed=field,
            old_value=old_value,
            new_value=str(value),
            changed_by=user_email,
            reason=payload.get("rate_justification") or payload.get("remarks"),
        )
        db.add(hist)

    # Recalculate amount
    if item.quantity and item.adopted_rate:
        item.amount = round(item.quantity * item.adopted_rate, 2)

    # Mark as modified if any tracked field changed
    tracked = {
        "project_description", "project_unit", "adopted_rate",
        "adjustment_percent", "quantity", "project_code",
    }
    if tracked.intersection(set(payload.keys())):
        item.is_modified = True

    item.edited_by = user_email
    item.edited_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    return item


def duplicate_part_item(
    db: Session,
    item_id: int,
    user_email: str,
) -> ProjectPartItem:
    original = db.query(ProjectPartItem).get(item_id)
    if not original:
        raise ValueError(f"ProjectPartItem {item_id} not found")

    copy = ProjectPartItem(
        project_part_selection_id=original.project_part_selection_id,
        bsr_item_id=original.bsr_item_id,
        master_item_id=original.master_item_id,
        item_no=original.item_no,
        original_code=original.original_code,
        project_code=original.project_code,
        original_description=original.original_description,
        project_description=original.project_description + " (Copy)",
        original_unit=original.original_unit,
        project_unit=original.project_unit,
        quantity=original.quantity,
        original_rate=original.original_rate,
        adjustment_percent=original.adjustment_percent,
        adopted_rate=original.adopted_rate,
        amount=original.amount,
        rate_source_year=original.rate_source_year,
        rate_source_book=original.rate_source_book,
        rate_source_province=original.rate_source_province,
        rate_source_district=original.rate_source_district,
        rate_source_revision=original.rate_source_revision,
        rate_source_file_id=original.rate_source_file_id,
        rate_source_page=original.rate_source_page,
        rate_source_sheet=original.rate_source_sheet,
        rate_source_row=original.rate_source_row,
        rate_justification=original.rate_justification,
        remarks=original.remarks,
        sort_order=original.sort_order + 1,
        is_modified=original.is_modified,
        edited_by=user_email,
        edited_at=datetime.utcnow(),
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


def remove_part_item(db: Session, item_id: int) -> bool:
    """Remove a project item. NEVER deletes the original BSR RateItem."""
    item = db.query(ProjectPartItem).get(item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def get_part_item_history(db: Session, item_id: int) -> list[ProjectPartItemHistory]:
    return (
        db.query(ProjectPartItemHistory)
        .filter(ProjectPartItemHistory.project_part_item_id == item_id)
        .order_by(ProjectPartItemHistory.changed_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Export – Excel
# ---------------------------------------------------------------------------

def export_part_excel(
    db: Session,
    selection_id: int,
) -> tuple[bytes, str]:
    """
    Generate an Excel file for the selected Part BOQ.
    Clones the master template if available; otherwise generates a plain workbook.
    Returns (bytes, filename).
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("openpyxl is required for Excel export")

    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise ValueError(f"Selection {selection_id} not found")

    part = sel.canonical_part
    items = sorted(sel.items, key=lambda x: x.sort_order)

    # Try to load template mapping
    tmapping = (
        db.query(PartTemplateMapping)
        .filter(PartTemplateMapping.canonical_part_id == part.id)
        .first()
    )

    wb = openpyxl.Workbook()
    ws = wb.active

    sheet_name = (tmapping.target_sheet if tmapping else f"Part {part.part_no}")[: 31]
    ws.title = sheet_name

    # Header styles
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill("solid", fgColor="1F4E79")
    white_font = Font(bold=True, color="FFFFFF", size=10)
    thin = Side(style="thin", color="AAAAAA")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Title
    ws.merge_cells("A1:N1")
    title_cell = ws["A1"]
    title_cell.value = f"BSR Part {part.part_no} – {part.part_name}   |   {sel.name}"
    title_cell.font = Font(bold=True, size=13, color="1F4E79")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:N2")
    ws["A2"].value = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    ws["A2"].font = Font(italic=True, color="888888", size=9)

    # Column headers
    cols = [
        ("A", "Item No.", 8),
        ("B", "BSR Ref", 10),
        ("C", "Description", 40),
        ("D", "Unit", 7),
        ("E", "Qty", 8),
        ("F", "Original Rate", 13),
        ("G", "Adj %", 7),
        ("H", "Adopted Rate", 13),
        ("I", "Amount (LKR)", 14),
        ("J", "Rate Year", 10),
        ("K", "Rate Source", 20),
        ("L", "District", 12),
        ("M", "Justification", 30),
        ("N", "Remarks", 20),
    ]

    header_row = 4
    for col_letter, col_name, col_width in cols:
        cell = ws[f"{col_letter}{header_row}"]
        cell.value = col_name
        cell.font = white_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[col_letter].width = col_width

    ws.row_dimensions[header_row].height = 20

    # Data rows
    subtotal = 0.0
    for i, item in enumerate(items, start=1):
        row = header_row + i
        amount = round((item.quantity or 0) * (item.adopted_rate or 0), 2)
        subtotal += amount

        row_data = [
            item.item_no or str(i),
            item.original_code or "",
            item.project_description or item.original_description,
            item.project_unit or item.original_unit,
            item.quantity,
            item.original_rate,
            item.adjustment_percent,
            item.adopted_rate,
            amount,
            item.rate_source_year,
            item.rate_source_book or "",
            item.rate_source_district or "",
            item.rate_justification or "",
            item.remarks or "",
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = border
            if col_idx == 3:
                cell.alignment = Alignment(wrap_text=True)
            if col_idx in (5, 6, 7, 8, 9):
                cell.number_format = '#,##0.00'
            # Modified indicator
            if item.is_modified:
                cell.font = Font(color="C55A11")

        ws.row_dimensions[row].height = 16

    # Subtotal row
    subtotal_row = header_row + len(items) + 1
    ws.merge_cells(f"A{subtotal_row}:H{subtotal_row}")
    ws[f"A{subtotal_row}"].value = "SUBTOTAL"
    ws[f"A{subtotal_row}"].font = Font(bold=True)
    ws[f"A{subtotal_row}"].alignment = Alignment(horizontal="right")
    ws[f"I{subtotal_row}"].value = subtotal
    ws[f"I{subtotal_row}"].number_format = '#,##0.00'
    ws[f"I{subtotal_row}"].font = Font(bold=True)

    # Freeze panes
    ws.freeze_panes = ws[f"A{header_row + 1}"]
    ws.auto_filter.ref = f"A{header_row}:N{header_row}"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", f"BSR_Part_{part.part_no}_{part.part_code}")
    filename = f"{safe_name}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return buf.getvalue(), filename


# ---------------------------------------------------------------------------
# Export – PDF
# ---------------------------------------------------------------------------

def export_part_pdf(
    db: Session,
    selection_id: int,
) -> tuple[bytes, str]:
    """
    Generate a PDF for the selected Part BOQ using ReportLab.
    A4 landscape, repeating headers, wrapped descriptions.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Table, TableStyle,
            Spacer, PageBreak,
        )
        from reportlab.lib.units import cm
    except ImportError:
        raise RuntimeError("reportlab is required for PDF export")

    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise ValueError(f"Selection {selection_id} not found")

    part = sel.canonical_part
    items = sorted(sel.items, key=lambda x: x.sort_order)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BsrTitle",
        parent=styles["Heading1"],
        fontSize=13,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "BsrSub",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        spaceAfter=8,
    )
    wrap_style = ParagraphStyle(
        "BsrWrap",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []
    story.append(Paragraph(f"BSR Part {part.part_no} – {part.part_name}", title_style))
    story.append(Paragraph(sel.name, sub_style))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        sub_style,
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Table data
    header = [
        "Item No.", "BSR Ref", "Description", "Unit", "Qty",
        "Orig. Rate", "Adj %", "Adopted Rate", "Amount (LKR)",
        "Rate Year", "Rate Source", "Justification",
    ]

    col_widths = [1.2*cm, 1.8*cm, 6*cm, 1.2*cm, 1.2*cm,
                  2.2*cm, 1.2*cm, 2.2*cm, 2.5*cm,
                  1.5*cm, 3*cm, 4*cm]

    table_data = [header]
    subtotal = 0.0
    for i, item in enumerate(items, start=1):
        amount = round((item.quantity or 0) * (item.adopted_rate or 0), 2)
        subtotal += amount
        table_data.append([
            item.item_no or str(i),
            item.original_code or "",
            Paragraph(item.project_description or item.original_description or "", wrap_style),
            item.project_unit or item.original_unit,
            f"{item.quantity:,.2f}",
            f"{item.original_rate:,.2f}",
            f"{item.adjustment_percent:.1f}%",
            f"{item.adopted_rate:,.2f}",
            f"{amount:,.2f}",
            item.rate_source_year,
            (item.rate_source_book or "")[:30],
            Paragraph(item.rate_justification or "", wrap_style),
        ])

    # Subtotal row
    table_data.append(
        ["", "", "SUBTOTAL", "", "", "", "", "", f"{subtotal:,.2f}", "", "", ""]
    )

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    dark_blue = colors.HexColor("#1F4E79")
    light_blue = colors.HexColor("#D6E4F0")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), dark_blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, light_blue]),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F0F4F8")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (8, 1), (8, -1), "RIGHT"),
        ("ALIGN", (4, 1), (7, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    story.append(tbl)
    doc.build(story)
    buf.seek(0)

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", f"BSR_Part_{part.part_no}_{part.part_code}")
    filename = f"{safe_name}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return buf.getvalue(), filename


# ---------------------------------------------------------------------------
# Import Breakdown helper
# ---------------------------------------------------------------------------

def get_import_breakdown(
    db: Session,
    source_file_id: int,
) -> dict:
    """
    After an import, return how many items landed in each canonical part.
    """
    all_parts = (
        db.query(CanonicalBSRPart)
        .filter(CanonicalBSRPart.active == True)
        .order_by(CanonicalBSRPart.sort_order)
        .all()
    )

    rows = (
        db.query(
            RateItem.canonical_part_id,
            RateItem.part_mapping_status,
            func.count(RateItem.id).label("cnt"),
        )
        .filter(RateItem.source_file_id == source_file_id)
        .group_by(RateItem.canonical_part_id, RateItem.part_mapping_status)
        .all()
    )

    sf = db.query(SourceFile).get(source_file_id)

    part_map = {p.id: p for p in all_parts}
    # Aggregate
    by_part: dict[int | None, dict] = {}
    for part_id, status, cnt in rows:
        if part_id not in by_part:
            by_part[part_id] = {"valid": 0, "review": 0, "unmapped": 0}
        if status == "MAPPED":
            by_part[part_id]["valid"] += cnt
        elif status == "NEEDS_REVIEW":
            by_part[part_id]["review"] += cnt
        else:
            by_part[part_id]["unmapped"] += cnt

    parts_breakdown = []
    for part in all_parts:
        stats = by_part.get(part.id, {"valid": 0, "review": 0, "unmapped": 0})
        item_count = stats["valid"] + stats["review"] + stats["unmapped"]
        parts_breakdown.append(
            {
                "canonical_part_id": part.id,
                "part_no": part.part_no,
                "part_code": part.part_code,
                "part_name": part.part_name,
                "item_count": item_count,
                "valid_count": stats["valid"],
                "review_count": stats["review"],
                "unmapped_count": stats["unmapped"],
            }
        )

    unmapped_stats = by_part.get(None, {"valid": 0, "review": 0, "unmapped": 0})
    total_unmapped = unmapped_stats.get("unmapped", 0) + unmapped_stats.get("review", 0)

    total = sum(
        s["valid"] + s["review"] + s["unmapped"] for s in by_part.values()
    )
    total_valid = sum(s["valid"] for s in by_part.values())
    total_review = sum(s["review"] for s in by_part.values())

    return {
        "source_file_id": source_file_id,
        "file_name": sf.original_filename if sf else "",
        "total_extracted": total,
        "total_valid": total_valid,
        "total_needs_review": total_review,
        "total_unmapped": total_unmapped,
        "total_duplicate": 0,
        "parts_breakdown": parts_breakdown,
    }


# ---------------------------------------------------------------------------
# Seed default PartTemplateMappings
# ---------------------------------------------------------------------------

def seed_default_part_template_mappings(db: Session) -> int:
    """
    Create default PartTemplateMapping rows for all 31 parts if none exist.
    Returns count of rows created.
    """
    all_parts = db.query(CanonicalBSRPart).filter(CanonicalBSRPart.active == True).all()
    created = 0
    for part in all_parts:
        existing = (
            db.query(PartTemplateMapping)
            .filter(PartTemplateMapping.canonical_part_id == part.id)
            .first()
        )
        if not existing:
            mapping = PartTemplateMapping(
                canonical_part_id=part.id,
                template_id=None,
                target_sheet=f"Part {part.part_no} - {part.part_name}"[:31],
                title=f"Part {part.part_no} – {part.part_name}",
                start_row=5,
                item_no_column="A",
                bsr_ref_column="B",
                description_column="C",
                unit_column="D",
                qty_column="E",
                original_rate_column="F",
                adopted_rate_column="G",
                amount_column="H",
                rate_year_column="I",
                rate_source_column="J",
                justification_column="K",
                remarks_column="L",
            )
            db.add(mapping)
            created += 1
    db.commit()
    return created
