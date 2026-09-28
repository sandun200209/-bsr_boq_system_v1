from __future__ import annotations

import io
from datetime import datetime
from typing import Any
from fastapi import HTTPException
from sqlalchemy import select, func, delete, desc
from sqlalchemy.orm import Session, selectinload, joinedload

from ..models import MasterBOQ, MasterBOQItem, RateItem, RateItemCESMMSection, CESMMSection
from ..schemas import (
    MasterBOQCreate,
    MasterBOQUpdate,
    MasterBOQItemCreate,
    MasterBOQItemUpdate,
)

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    KeepTogether,
)


def get_or_create_active_boq(db: Session, project_id: int | None = None) -> MasterBOQ:
    """
    Returns the currently active Master BOQ workspace, or creates a default one if none exists.
    """
    query = (
        select(MasterBOQ)
        .options(
            selectinload(MasterBOQ.items).joinedload(MasterBOQItem.source_rate_item)
        )
        .order_by(MasterBOQ.updated_at.desc())
    )
    if project_id:
        query = query.where(MasterBOQ.project_id == project_id)

    boq = db.scalars(query).first()
    if not boq:
        boq = MasterBOQ(
            name="Master BOQ Working Workspace",
            project_id=project_id,
            status="ACTIVE",
            contingency_rate=0.10,
            vat_status="Excluded",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(boq)
        db.commit()
        db.refresh(boq)

    return boq


def list_master_boqs(db: Session) -> list[MasterBOQ]:
    """Returns all Master BOQ workspaces ordered by last updated."""
    return list(
        db.scalars(
            select(MasterBOQ)
            .options(selectinload(MasterBOQ.items))
            .order_by(MasterBOQ.updated_at.desc())
        ).all()
    )


def create_master_boq(db: Session, payload: MasterBOQCreate, user_email: str | None = None) -> MasterBOQ:
    """Creates a new Master BOQ workspace."""
    boq = MasterBOQ(
        name=payload.name or "Untitled Master BOQ",
        project_id=payload.project_id,
        status="ACTIVE",
        contingency_rate=payload.contingency_rate if payload.contingency_rate is not None else 0.10,
        vat_status=payload.vat_status or "Excluded",
        notes=payload.notes,
        created_by=user_email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(boq)
    db.commit()
    db.refresh(boq)
    return boq


def get_master_boq(db: Session, boq_id: int) -> MasterBOQ:
    """Retrieves a specific Master BOQ with all its line items."""
    boq = db.scalar(
        select(MasterBOQ)
        .where(MasterBOQ.id == boq_id)
        .options(
            selectinload(MasterBOQ.items).joinedload(MasterBOQItem.source_rate_item)
        )
    )
    if not boq:
        raise HTTPException(status_code=404, detail=f"Master BOQ {boq_id} not found")
    return boq


def update_master_boq(db: Session, boq_id: int, payload: MasterBOQUpdate) -> MasterBOQ:
    """Updates high-level parameters of a Master BOQ."""
    boq = get_master_boq(db, boq_id)
    if payload.name is not None:
        boq.name = payload.name.strip()
    if payload.status is not None:
        boq.status = payload.status.strip()
    if payload.contingency_rate is not None:
        boq.contingency_rate = max(0.0, payload.contingency_rate)
    if payload.vat_status is not None:
        boq.vat_status = payload.vat_status.strip()
    if payload.notes is not None:
        boq.notes = payload.notes

    boq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(boq)
    return boq


def delete_master_boq(db: Session, boq_id: int) -> bool:
    """Deletes a Master BOQ and its line items. RateItem records remain completely untouched."""
    boq = get_master_boq(db, boq_id)
    db.delete(boq)
    db.commit()
    return True


def add_rate_items_to_boq(
    db: Session, boq_id: int, rate_item_ids: list[int]
) -> tuple[list[MasterBOQItem], int, int]:
    """
    Takes selected rate items by ID and appends them to the active Master BOQ.
    Preserves all source metadata.
    Detects duplicate items: items already in the active BOQ are skipped to avoid
    accidental silent re-duplication.
    Returns (newly_added_items, added_count, existing_count).
    """
    boq = get_master_boq(db, boq_id)

    # Existing rate item IDs in this BOQ
    existing_source_ids = {
        it.source_rate_item_id
        for it in boq.items
        if it.source_rate_item_id is not None
    }

    # Fetch rate items preserving ID order
    rate_items = db.scalars(
        select(RateItem)
        .where(RateItem.id.in_(rate_item_ids))
        .options(
            selectinload(RateItem.cesmm_mappings).joinedload(RateItemCESMMSection.cesmm_section),
            joinedload(RateItem.source_file),
        )
    ).all()
    rate_items_by_id = {it.id: it for it in rate_items}

    # Determine next sort_order
    max_order = max([it.sort_order for it in boq.items], default=0)

    added_items: list[MasterBOQItem] = []
    added_count = 0
    existing_count = 0

    for r_id in rate_item_ids:
        if r_id in existing_source_ids:
            existing_count += 1
            continue

        it = rate_items_by_id.get(r_id)
        if not it:
            continue

        # Resolve primary CESMM section label
        cesmm_label = None
        if it.cesmm_mappings:
            primary_map = next((m for m in it.cesmm_mappings if m.is_primary), it.cesmm_mappings[0])
            if primary_map and primary_map.cesmm_section:
                sec = primary_map.cesmm_section
                cesmm_label = f"{sec.section_no} - {sec.name} ({sec.section_code})"

        # Default values per specification:
        # description = current rate item description
        # unit = current rate item unit
        # rate = current rate
        # quantity = 0.0 initially (or blank)
        # amount = quantity * rate
        base_rate = it.rate or 0.0
        init_qty = 0.0
        max_order += 1

        source_reg = f"{it.province} / {it.district}" if (it.province and it.district) else (it.province or it.district or "")
        src_file = it.source_file.original_filename if it.source_file else None

        boq_item = MasterBOQItem(
            master_boq_id=boq.id,
            source_rate_item_id=it.id,
            source_rate_book=it.rate_system,
            source_code=it.item_code,
            source_category=it.category_name,
            source_cesmm_section=cesmm_label,
            source_year=it.year,
            source_revision=it.revision,
            source_region=source_reg,
            source_file=src_file,
            source_page=it.source_page,
            original_rate=base_rate,
            item_no=it.item_code or str(len(boq.items) + added_count + 1),
            description=it.description or "Rate Item",
            unit=it.unit or "Item",
            quantity=init_qty,
            rate=base_rate,
            amount=round(init_qty * base_rate, 2),
            notes=None,
            sort_order=max_order,
            is_custom=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(boq_item)
        added_items.append(boq_item)
        added_count += 1
        existing_source_ids.add(it.id)

    boq.updated_at = datetime.utcnow()
    db.commit()

    for it in added_items:
        db.refresh(it)

    return added_items, added_count, existing_count


def add_custom_item_to_boq(
    db: Session, boq_id: int, payload: MasterBOQItemCreate
) -> MasterBOQItem:
    """Adds a custom item (not from BSR/HSR) to the Master BOQ."""
    boq = get_master_boq(db, boq_id)
    max_order = max([it.sort_order for it in boq.items], default=0) + 1

    qty = max(0.0, payload.quantity)
    rate = max(0.0, payload.rate)
    amount = round(qty * rate, 2)

    item = MasterBOQItem(
        master_boq_id=boq.id,
        source_rate_item_id=None,
        source_rate_book="Custom",
        source_code=payload.item_no or "CUSTOM",
        source_category="Custom Scope",
        source_cesmm_section="31 - Simple building works incidental to civil engineering works (X)",
        source_year=datetime.utcnow().year,
        source_revision="Custom",
        source_region=None,
        source_file=None,
        source_page=None,
        original_rate=rate,
        item_no=payload.item_no or str(max_order),
        description=payload.description.strip(),
        unit=payload.unit.strip(),
        quantity=qty,
        rate=rate,
        amount=amount,
        notes=payload.notes,
        sort_order=max_order,
        is_custom=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    boq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


def update_boq_item(
    db: Session, boq_id: int, item_id: int, payload: MasterBOQItemUpdate
) -> MasterBOQItem:
    """
    Edits working BOQ values (description, unit, quantity, rate, notes, item_no).
    IMPORTANT: original RateItem records are NEVER mutated.
    """
    item = db.scalar(
        select(MasterBOQItem).where(
            MasterBOQItem.id == item_id,
            MasterBOQItem.master_boq_id == boq_id,
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"BOQ Item {item_id} not found in BOQ {boq_id}")

    if payload.item_no is not None:
        item.item_no = payload.item_no.strip()
    if payload.description is not None:
        item.description = payload.description.strip()
    if payload.unit is not None:
        item.unit = payload.unit.strip()
    if payload.quantity is not None:
        item.quantity = max(0.0, payload.quantity)
    if payload.rate is not None:
        item.rate = max(0.0, payload.rate)
    if payload.notes is not None:
        item.notes = payload.notes
    if payload.sort_order is not None:
        item.sort_order = payload.sort_order

    # Recalculate amount safely
    item.amount = round(item.quantity * item.rate, 2)
    item.updated_at = datetime.utcnow()

    # Touch parent BOQ timestamp
    item.master_boq.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    return item


def delete_boq_item(db: Session, boq_id: int, item_id: int) -> bool:
    """Removes an item from Master BOQ. Original RateItem is NOT affected."""
    item = db.scalar(
        select(MasterBOQItem).where(
            MasterBOQItem.id == item_id,
            MasterBOQItem.master_boq_id == boq_id,
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"BOQ Item {item_id} not found in BOQ {boq_id}")

    db.delete(item)
    db.commit()
    return True


def bulk_delete_boq_items(db: Session, boq_id: int, item_ids: list[int]) -> int:
    """Deletes multiple items from Master BOQ."""
    if not item_ids:
        return 0
    stmt = delete(MasterBOQItem).where(
        MasterBOQItem.master_boq_id == boq_id,
        MasterBOQItem.id.in_(item_ids),
    )
    res = db.execute(stmt)
    db.commit()
    return res.rowcount or 0


def duplicate_boq_item(db: Session, boq_id: int, item_id: int) -> MasterBOQItem:
    """Creates an explicit duplicate of a BOQ item."""
    original = db.scalar(
        select(MasterBOQItem).where(
            MasterBOQItem.id == item_id,
            MasterBOQItem.master_boq_id == boq_id,
        )
    )
    if not original:
        raise HTTPException(status_code=404, detail=f"BOQ Item {item_id} not found")

    boq = get_master_boq(db, boq_id)
    max_order = max([it.sort_order for it in boq.items], default=0) + 1

    clone = MasterBOQItem(
        master_boq_id=boq.id,
        source_rate_item_id=original.source_rate_item_id,
        source_rate_book=original.source_rate_book,
        source_code=original.source_code,
        source_category=original.source_category,
        source_cesmm_section=original.source_cesmm_section,
        source_year=original.source_year,
        source_revision=original.source_revision,
        source_region=original.source_region,
        source_file=original.source_file,
        source_page=original.source_page,
        original_rate=original.original_rate,
        item_no=f"{original.item_no or ''} (Copy)".strip(),
        description=original.description,
        unit=original.unit,
        quantity=original.quantity,
        rate=original.rate,
        amount=original.amount,
        notes=original.notes,
        sort_order=max_order,
        is_custom=original.is_custom,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(clone)
    boq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(clone)
    return clone


def reorder_boq_items(db: Session, boq_id: int, item_orders: list[dict]) -> None:
    """Updates sort_order for items in the Master BOQ."""
    for entry in item_orders:
        item_id = entry.get("id")
        order = entry.get("sort_order")
        if item_id is not None and order is not None:
            item = db.get(MasterBOQItem, item_id)
            if item and item.master_boq_id == boq_id:
                item.sort_order = order

    boq = get_master_boq(db, boq_id)
    boq.updated_at = datetime.utcnow()
    db.commit()


# ---------------------------------------------------------------------------
# Excel and PDF Exporters for Master BOQ
# ---------------------------------------------------------------------------

def export_master_boq_excel(boq: MasterBOQ) -> bytes:
    """
    Generates a beautifully styled professional QS Master BOQ Excel spreadsheet (.xlsx).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master BOQ"
    ws.views.sheetView[0].showGridLines = True

    # Styling definitions
    navy_dark = "1B365D"
    blue_header = "2B4C7E"
    border_color = "D1D5DB"

    title_font = Font(name="Calibri", size=15, bold=True, color=navy_dark)
    sub_font = Font(name="Calibri", size=10, italic=True, color="555555")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    cell_font = Font(name="Calibri", size=10)
    bold_cell_font = Font(name="Calibri", size=10, bold=True)
    summary_font = Font(name="Calibri", size=11, bold=True, color="111827")

    header_fill = PatternFill(start_color=blue_header, end_color=blue_header, fill_type="solid")
    summary_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    grand_total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color=border_color),
        right=Side(style="thin", color=border_color),
        top=Side(style="thin", color=border_color),
        bottom=Side(style="thin", color=border_color),
    )

    double_bottom_border = Border(
        left=Side(style="thin", color=border_color),
        right=Side(style="thin", color=border_color),
        top=Side(style="thin", color=border_color),
        bottom=Side(style="double", color="1B365D"),
    )

    # 1. Title Block
    ws.merge_cells("A1:J1")
    ws["A1"] = boq.name.upper()
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:J2")
    ws["A2"] = f"Generated by Sri Lanka Schedule of Rates Hub | Status: {boq.status} | Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    ws["A2"].font = sub_font
    ws["A2"].alignment = Alignment(vertical="center")
    ws.row_dimensions[2].height = 18

    # 2. Table Headers (Row 4)
    headers = [
        "Item #",
        "Source Code",
        "Description",
        "CESMM Section",
        "Unit",
        "Quantity",
        "Rate (LKR)",
        "Amount (LKR)",
        "Source Reference",
        "Notes",
    ]

    ws.row_dimensions[4].height = 25
    for col_idx, h_text in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=h_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal="center" if col_idx in [1, 2, 5] else ("right" if col_idx in [6, 7, 8] else "left"),
            vertical="center",
            wrap_text=True,
        )
        cell.border = thin_border

    # 3. Data Rows
    current_row = 5
    for it in boq.items:
        ws.row_dimensions[current_row].height = 20
        # Source reference text
        src_ref = ""
        if it.source_rate_book:
            src_ref = f"{it.source_rate_book} {it.source_year or ''}"
            if it.source_region:
                src_ref += f" / {it.source_region}"
            if it.source_page:
                src_ref += f" / P.{it.source_page}"
        elif it.is_custom:
            src_ref = "Custom Item"

        ws.cell(row=current_row, column=1, value=it.item_no or "").alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=2, value=it.source_code or "").alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=current_row, column=3, value=it.description).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=current_row, column=4, value=it.source_cesmm_section or "").alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=5, value=it.unit).alignment = Alignment(horizontal="center", vertical="center")

        # Numeric cells
        c_qty = ws.cell(row=current_row, column=6, value=float(it.quantity))
        c_qty.number_format = "#,##0.00"
        c_qty.alignment = Alignment(horizontal="right", vertical="center")

        c_rate = ws.cell(row=current_row, column=7, value=float(it.rate))
        c_rate.number_format = "#,##0.00"
        c_rate.alignment = Alignment(horizontal="right", vertical="center")

        c_amt = ws.cell(row=current_row, column=8, value=float(it.amount))
        c_amt.number_format = "#,##0.00"
        c_amt.alignment = Alignment(horizontal="right", vertical="center")

        ws.cell(row=current_row, column=9, value=src_ref).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=current_row, column=10, value=it.notes or "").alignment = Alignment(horizontal="left", vertical="center")

        for c in range(1, 11):
            cell = ws.cell(row=current_row, column=c)
            cell.font = cell_font
            cell.border = thin_border

        current_row += 1

    # 4. Totals Block
    if boq.items:
        # Subtotal
        ws.row_dimensions[current_row].height = 22
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
        lbl_sub = ws.cell(row=current_row, column=1, value="SUBTOTAL (DIRECT ESTIMATE)")
        lbl_sub.font = bold_cell_font
        lbl_sub.alignment = Alignment(horizontal="right", vertical="center")

        c_sub = ws.cell(row=current_row, column=8, value=f"=SUM(H5:H{current_row-1})")
        c_sub.font = bold_cell_font
        c_sub.number_format = "#,##0.00"
        c_sub.alignment = Alignment(horizontal="right", vertical="center")

        for col in range(1, 11):
            ws.cell(row=current_row, column=col).border = thin_border
            ws.cell(row=current_row, column=col).fill = summary_fill

        subtotal_row = current_row
        current_row += 1

        # Contingency
        contingency_pct = boq.contingency_rate * 100
        ws.row_dimensions[current_row].height = 20
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
        lbl_cont = ws.cell(row=current_row, column=1, value=f"CONTINGENCY ({contingency_pct:.1f}%)")
        lbl_cont.font = bold_cell_font
        lbl_cont.alignment = Alignment(horizontal="right", vertical="center")

        c_cont = ws.cell(row=current_row, column=8, value=f"=H{subtotal_row}*{boq.contingency_rate}")
        c_cont.font = bold_cell_font
        c_cont.number_format = "#,##0.00"
        c_cont.alignment = Alignment(horizontal="right", vertical="center")

        for col in range(1, 11):
            ws.cell(row=current_row, column=col).border = thin_border
            ws.cell(row=current_row, column=col).fill = summary_fill

        cont_row = current_row
        current_row += 1

        # Grand Total / Engineer's Estimate
        ws.row_dimensions[current_row].height = 24
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
        lbl_tot = ws.cell(row=current_row, column=1, value="ENGINEER'S ESTIMATE (EXCL. VAT)")
        lbl_tot.font = summary_font
        lbl_tot.alignment = Alignment(horizontal="right", vertical="center")

        c_tot = ws.cell(row=current_row, column=8, value=f"=H{subtotal_row}+H{cont_row}")
        c_tot.font = summary_font
        c_tot.number_format = "#,##0.00"
        c_tot.alignment = Alignment(horizontal="right", vertical="center")

        for col in range(1, 11):
            ws.cell(row=current_row, column=col).border = double_bottom_border
            ws.cell(row=current_row, column=col).fill = grand_total_fill

    # Auto-adjust column widths
    col_widths = {
        1: 10,  # Item #
        2: 14,  # Source Code
        3: 45,  # Description
        4: 28,  # CESMM Section
        5: 10,  # Unit
        6: 12,  # Quantity
        7: 15,  # Rate
        8: 18,  # Amount
        9: 28,  # Source Reference
        10: 25, # Notes
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_master_boq_pdf(boq: MasterBOQ) -> bytes:
    """
    Generates an executive-ready Master BOQ report in landscape A4 PDF format.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "BoqTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1B365D"),
        spaceAfter=3,
    )
    meta_style = ParagraphStyle(
        "BoqMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    cell_style = ParagraphStyle(
        "BoqCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111827"),
    )
    bold_cell_style = ParagraphStyle(
        "BoqBoldCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111827"),
    )
    header_style = ParagraphStyle(
        "BoqHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    elements: list[Any] = []

    # Title & Metadata
    elements.append(Paragraph(boq.name.upper(), title_style))
    meta_text = (
        f"Status: <b>{boq.status}</b> | "
        f"Total Items: <b>{len(boq.items)}</b> | "
        f"VAT Basis: <b>{boq.vat_status}</b> | "
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    elements.append(Paragraph(meta_text, meta_style))

    # Table Header
    headers = [
        Paragraph("<b>Item #</b>", header_style),
        Paragraph("<b>Code</b>", header_style),
        Paragraph("<b>Description</b>", header_style),
        Paragraph("<b>CESMM</b>", header_style),
        Paragraph("<b>Unit</b>", header_style),
        Paragraph("<b>Qty</b>", header_style),
        Paragraph("<b>Rate (LKR)</b>", header_style),
        Paragraph("<b>Amount (LKR)</b>", header_style),
        Paragraph("<b>Source</b>", header_style),
    ]

    table_data = [headers]

    subtotal = sum(it.amount for it in boq.items)

    for it in boq.items:
        src_ref = ""
        if it.source_rate_book:
            src_ref = f"{it.source_rate_book} {it.source_year or ''}"
            if it.source_region:
                src_ref += f" ({it.source_region})"
        elif it.is_custom:
            src_ref = "Custom"

        row = [
            Paragraph(it.item_no or "", cell_style),
            Paragraph(it.source_code or "", cell_style),
            Paragraph(it.description, cell_style),
            Paragraph(it.source_cesmm_section or "-", cell_style),
            Paragraph(it.unit, cell_style),
            Paragraph(f"{it.quantity:,.2f}", cell_style),
            Paragraph(f"{it.rate:,.2f}", cell_style),
            Paragraph(f"{it.amount:,.2f}", bold_cell_style),
            Paragraph(src_ref, cell_style),
        ]
        table_data.append(row)

    # Totals rows
    contingency = subtotal * boq.contingency_rate
    grand_total = subtotal + contingency

    table_data.append([
        "", "", Paragraph("<b>SUBTOTAL (DIRECT ESTIMATE)</b>", bold_cell_style),
        "", "", "", "", Paragraph(f"<b>LKR {subtotal:,.2f}</b>", bold_cell_style), ""
    ])
    table_data.append([
        "", "", Paragraph(f"<b>CONTINGENCY ({boq.contingency_rate*100:.1f}%)</b>", bold_cell_style),
        "", "", "", "", Paragraph(f"<b>LKR {contingency:,.2f}</b>", bold_cell_style), ""
    ])
    table_data.append([
        "", "", Paragraph("<b>ENGINEER'S ESTIMATE (EXCL. VAT)</b>", bold_cell_style),
        "", "", "", "", Paragraph(f"<b>LKR {grand_total:,.2f}</b>", bold_cell_style), ""
    ])

    col_widths = [45, 55, 230, 110, 45, 50, 65, 80, 110]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B4C7E")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -4), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, colors.HexColor("#F8FAFC")]),
        # Totals formatting
        ("BACKGROUND", (0, -3), (-1, -1), colors.HexColor("#F1F5F9")),
        ("LINEABOVE", (0, -3), (-1, -3), 1, colors.HexColor("#94A3B8")),
        ("LINEBELOW", (0, -1), (-1, -1), 1.5, colors.HexColor("#1B365D")),
    ]
    t.setStyle(TableStyle(t_style))
    elements.append(t)

    doc.build(elements)
    return buffer.getvalue()
