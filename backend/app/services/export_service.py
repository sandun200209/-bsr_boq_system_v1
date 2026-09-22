"""
BSR Rate Hub - Master Template Export Engine
Reproduces the exact workbook structure, sheet separation, column order, title layout,
notes layout, wrapping, number formats, and engineering/QS appearance of the reference workbook:
Matara_OT_Renovation_Consolidated_BOQ_Estimate_Rev7_Electrical_Ancillary_Deduplicated.xlsx
"""

from __future__ import annotations

import io
import os
import copy
from typing import Any
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
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas

# Path to the pristine master reference template
TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates",
    "Matara_OT_Renovation_Consolidated_BOQ_Estimate_Rev7_Electrical_Ancillary_Deduplicated.xlsx",
)

# Supported QS Packages with their template sheets and standard configurations
PACKAGE_REGISTRY = {
    "electrical": {
        "id": "electrical",
        "name": "Electrical",
        "boq_sheet": "Electrical BOQ - Reviewed",
        "recon_sheet": "Electrical Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – ELECTRICAL BOQ REVIEWED FOR CONSOLIDATION",
        "default_recon_title": "ELECTRICAL / MODULAR OT / MVAC – SCOPE RECONCILIATION",
        "default_note": (
            "Source: uploaded legacy Excel electrical BOQ (subtotal LKR 21,039,600). "
            "Quantities have been reviewed against the Modular OT and MVAC packages. "
            "Only clearly identifiable overlaps are deducted; upstream UPS distribution "
            "and general electrical infrastructure are retained."
        ),
        "columns": [
            "Source Row", "Item", "Description", "Unit", "Source Qty", "Rate (LKR)",
            "Source Amount", "Duplicate Qty", "Duplicate Amount", "Reviewed Qty",
            "Reviewed Amount", "Overlap / Reason", "Action", "Confidence", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Source Electrical BOQ", "Other Package", "Consolidated Treatment",
            "Deduction / Adjustment", "Reason", "Risk", "Tender Action"
        ],
    },
    "water_supply": {
        "id": "water_supply",
        "name": "Water Supply",
        "boq_sheet": "Water Supply BOQ & Estimate",
        "recon_sheet": "Water Supply Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – WATER SUPPLY SYSTEM BOQ & ENGINEER'S ESTIMATE",
        "default_recon_title": "WATER SUPPLY / MODULAR OT / RENOVATION / MVAC – SCOPE RECONCILIATION",
        "default_note": (
            "Preliminary estimate for external and internal water-supply infrastructure serving "
            "the renovated operating-theatre complex."
        ),
        "columns": [
            "Item", "Section", "BOQ Description", "Unit", "Qty", "Rate (LKR)",
            "Amount (LKR)", "Rate Basis", "Drawing / Source", "Duplication Check", "Status", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Existing Package / Source", "Treatment in Water-Supply BOQ",
            "Reason", "Boundary / Interface", "Duplication Risk", "Current Allowance", "Action Before Tender"
        ],
    },
    "wastewater": {
        "id": "wastewater",
        "name": "Wastewater & Sewer",
        "boq_sheet": "Wastewater & Sewer BOQ",
        "recon_sheet": "Wastewater Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – WASTEWATER & SEWERAGE SYSTEM BOQ & ENGINEER'S ESTIMATE",
        "default_recon_title": "WASTEWATER / SEWERAGE – SCOPE RECONCILIATION WITH OTHER MATARA PACKAGES",
        "default_note": (
            "Preliminary estimate for sanitary wastewater/soil and sewerage works serving "
            "the renovated operating-theatre complex."
        ),
        "columns": [
            "Item", "Section", "BOQ Description", "Unit", "Qty", "Rate (LKR)",
            "Amount (LKR)", "Rate Basis", "Drawing / Source", "Duplication Check", "Status", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Existing Package / Source", "Treatment in Wastewater BOQ",
            "Reason", "Boundary / Interface", "Duplication Risk", "Current Allowance", "Action Before Tender"
        ],
    },
    "rainwater": {
        "id": "rainwater",
        "name": "Rainwater Disposal",
        "boq_sheet": "Rainwater Disposal BOQ",
        "recon_sheet": "Rainwater Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – RAINWATER DISPOSAL SYSTEM BOQ & ENGINEER'S ESTIMATE",
        "default_recon_title": "RAINWATER DISPOSAL – SCOPE RECONCILIATION WITH MATARA BOQ PACKAGES",
        "default_note": (
            "Special design emphasis: courtyard rainwater is to be collected positively and diverted in a fully "
            "closed, maintainable pipe system across/over the first-floor slab through the building."
        ),
        "columns": [
            "Item", "Section", "BOQ Description", "Unit", "Qty", "Rate (LKR)",
            "Amount (LKR)", "Rate Basis", "Drawing / Source", "Duplication Check", "Status", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Existing Package / Source", "Treatment in Rainwater BOQ",
            "Reason", "Boundary / Interface", "Duplication Risk", "Current Allowance", "Action Before Tender"
        ],
    },
    "mvac": {
        "id": "mvac",
        "name": "MVAC",
        "boq_sheet": "MVAC BOQ & Estimate",
        "recon_sheet": "MVAC Scope Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – MVAC BOQ & ENGINEER'S ESTIMATE",
        "default_recon_title": "MVAC / MODULAR OPERATING THEATRE – SCOPE RECONCILIATION",
        "default_note": (
            "Prepared from uploaded MVAC drawings. OT-specific LAF/AHU/exhaust/ductwork/room-control "
            "scope already included in the Modular OT package is excluded to avoid duplication."
        ),
        "columns": [
            "Item", "Section", "BOQ Description", "Unit", "Qty", "Rate (LKR)",
            "Amount (LKR)", "Rate Basis", "Drawing / Source", "Duplication Check", "Status", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Modular OT Existing BOQ", "MVAC Drawing", "Treatment in this MVAC BOQ",
            "Reason", "Connection / Boundary", "Risk", "Action"
        ],
    },
    "medical_gas": {
        "id": "medical_gas",
        "name": "Medical Gas",
        "boq_sheet": "Medical Gas BOQ & Estimate",
        "recon_sheet": "Medical Gas Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – MEDICAL GAS SYSTEM BOQ & ENGINEER'S ESTIMATE",
        "default_recon_title": "MEDICAL GAS / MODULAR OT / GENERAL RENOVATION – SCOPE RECONCILIATION",
        "default_note": (
            "Preliminary estimate for the renovated OT complex. OT pendants and the 8 modular-theatre "
            "medical-gas terminal boxes are excluded from this BOQ to prevent duplication."
        ),
        "columns": [
            "Item", "Section", "BOQ Description", "Unit", "Qty", "Rate (LKR)",
            "Amount (LKR)", "Rate Basis", "Source / Basis", "Duplication Check", "Status", "Remarks"
        ],
        "recon_columns": [
            "Scope Element", "Existing Package / Source", "Treatment in Medical-Gas BOQ",
            "Reason", "Boundary / Interface", "Duplication Risk", "Current Allowance", "Action Before Tender"
        ],
    },
    "all": {
        "id": "all",
        "name": "Consolidated Master Package (All Sheets)",
        "boq_sheet": "Electrical BOQ - Reviewed",
        "recon_sheet": "Electrical Reconciliation",
        "default_title": "DISTRICT GENERAL HOSPITAL MATARA – CONSOLIDATED RENOVATION ESTIMATE",
        "default_recon_title": "SCOPE RECONCILIATION & DUPLICATION REGISTER",
        "default_note": "Consolidated multi-package engineering estimate and duplication audit.",
        "columns": [],
        "recon_columns": [],
    }
}


def get_template_package_data(package_key: str = "electrical") -> dict[str, Any]:
    """
    Extracts the audited baseline items and reconciliation matrix directly from the reference template.
    Allows UI preview and populating export data.
    """
    pkg = PACKAGE_REGISTRY.get(package_key.lower(), PACKAGE_REGISTRY["electrical"])
    wb = openpyxl.load_workbook(TEMPLATE_PATH, data_only=True)

    boq_sheet_name = pkg["boq_sheet"]
    recon_sheet_name = pkg["recon_sheet"]

    ws_boq = wb[boq_sheet_name]
    ws_recon = wb[recon_sheet_name]

    # Extract BOQ items
    boq_items = []
    if package_key.lower() == "electrical":
        for r in range(5, ws_boq.max_row + 1):
            desc = ws_boq.cell(r, 3).value
            if not desc or str(desc).strip() in ["Source BOQ subtotal", "Identified duplicate deductions", "Reviewed direct electrical subtotal", "Design-development contingency", "Contingency Amount", "Engineer’s Estimate excl. VAT", "Engineer's Estimate excl. VAT", "VAT"]:
                continue
            boq_items.append({
                "source_row": ws_boq.cell(r, 1).value,
                "item": ws_boq.cell(r, 2).value,
                "description": desc,
                "unit": ws_boq.cell(r, 4).value,
                "source_qty": float(ws_boq.cell(r, 5).value or 0.0),
                "rate": float(ws_boq.cell(r, 6).value or 0.0),
                "source_amount": float(ws_boq.cell(r, 7).value or 0.0),
                "duplicate_qty": float(ws_boq.cell(r, 8).value or 0.0),
                "duplicate_amount": float(ws_boq.cell(r, 9).value or 0.0),
                "reviewed_qty": float(ws_boq.cell(r, 10).value or 0.0),
                "reviewed_amount": float(ws_boq.cell(r, 11).value or 0.0),
                "overlap_reason": ws_boq.cell(r, 12).value or "",
                "action": ws_boq.cell(r, 13).value or "RETAIN",
                "confidence": ws_boq.cell(r, 14).value or "High",
                "remarks": ws_boq.cell(r, 15).value or "",
            })
    else:
        # Generic package reader
        for r in range(5, ws_boq.max_row + 1):
            item_val = ws_boq.cell(r, 1).value
            desc_val = ws_boq.cell(r, 3).value
            if not desc_val or "subtotal" in str(desc_val).lower() or "estimate" in str(desc_val).lower():
                continue
            boq_items.append({
                "item": item_val,
                "section": ws_boq.cell(r, 2).value or "",
                "description": desc_val,
                "unit": ws_boq.cell(r, 4).value or "",
                "source_qty": float(ws_boq.cell(r, 5).value or 0.0),
                "rate": float(ws_boq.cell(r, 6).value or 0.0),
                "source_amount": float(ws_boq.cell(r, 7).value or 0.0),
                "rate_basis": ws_boq.cell(r, 8).value or "",
                "drawing_source": ws_boq.cell(r, 9).value if ws_boq.max_column >= 9 else "",
                "duplication_check": ws_boq.cell(r, 10).value if ws_boq.max_column >= 10 else "",
                "action": "RETAIN",
                "confidence": "High",
                "remarks": ws_boq.cell(r, 12).value if ws_boq.max_column >= 12 else "",
            })

    # Extract Reconciliation items
    recon_items = []
    for r in range(4, ws_recon.max_row + 1):
        scope_el = ws_recon.cell(r, 1).value
        if scope_el:
            row_vals = [ws_recon.cell(r, c).value or "" for c in range(1, len(pkg["recon_columns"]) + 1)]
            recon_items.append(row_vals)

    return {
        "package": pkg,
        "project_title": ws_boq.cell(1, 1).value or pkg["default_title"],
        "source_note": ws_boq.cell(2, 1).value or pkg["default_note"],
        "recon_title": ws_recon.cell(1, 1).value or pkg["default_recon_title"],
        "boq_items": boq_items,
        "recon_items": recon_items,
    }


def generate_package_excel(
    package_key: str = "electrical",
    project_title: str | None = None,
    source_note: str | None = None,
    contingency_rate: float = 0.10,
    items: list[dict] | None = None,
    reconciliation_items: list[list | dict] | None = None,
    vat_status: str = "Excluded",
) -> bytes:
    """
    Generates a master-compliant .xlsx workbook matching the exact structure and QS styling
    of the reference template.
    1. Loads a clean copy of the master template via openpyxl.
    2. Keeps only the requested package worksheets (e.g. BOQ Reviewed + Reconciliation).
    3. Updates project title (row 1 merged) and explanatory note (row 2 merged).
    4. If custom/reviewed items are supplied, populates data rows with formulas and styling.
    5. Preserves all merged cells, row heights, column widths, fills, fonts, borders,
       number formats, and formulas.
    6. Returns the resulting workbook as bytes.
    """
    pkg_id = package_key.lower()
    pkg = PACKAGE_REGISTRY.get(pkg_id, PACKAGE_REGISTRY["electrical"])

    # Load clean master template without altering the source file
    wb = openpyxl.load_workbook(TEMPLATE_PATH, data_only=False)

    if pkg_id != "all":
        # Keep only the target package worksheets
        target_sheets = [pkg["boq_sheet"], pkg["recon_sheet"]]
        sheets_to_remove = [s for s in wb.sheetnames if s not in target_sheets]
        for s in sheets_to_remove:
            wb.remove(wb[s])

    ws_boq = wb[pkg["boq_sheet"]]
    ws_recon = wb[pkg["recon_sheet"]]

    # 1. Update Project Title & Explanatory Note on BOQ Sheet
    final_title = project_title.strip() if project_title else pkg["default_title"]
    final_note = source_note.strip() if source_note else pkg["default_note"]

    ws_boq.cell(1, 1).value = final_title
    if ws_boq.cell(2, 1):
        ws_boq.cell(2, 1).value = final_note

    # Update Recon Title
    ws_recon.cell(1, 1).value = pkg["default_recon_title"]

    # 2. If custom items or reviewed rates are supplied, populate data rows
    if items is not None and len(items) > 0:
        _populate_boq_items(ws_boq, items, contingency_rate, vat_status, pkg_id)

    # 3. If approved reconciliation rows are supplied, populate reconciliation sheet
    if reconciliation_items is not None:
        _populate_recon_items(ws_recon, reconciliation_items, pkg)

    # Save to memory buffer
    out_buf = io.BytesIO()
    wb.save(out_buf)
    return out_buf.getvalue()


def _populate_boq_items(
    ws: openpyxl.worksheet.worksheet.Worksheet,
    items: list[dict],
    contingency_rate: float,
    vat_status: str,
    pkg_id: str,
):
    """
    Populates BOQ line items with exact styling, number formatting, formula evaluation,
    and QS summary totals.
    """
    header_row = 4
    start_row = 5

    # Determine maximum existing rows to clear
    max_r = ws.max_row
    # Clear existing data rows and old summary rows
    for r in range(start_row, max_r + 15):
        for c in range(1, 16):
            cell = ws.cell(r, c)
            cell.value = None

    # Thin border definition
    thin_side = Side(style="thin", color="D9D9D9")
    data_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    num_fmt = "#,##0.00"

    current_r = start_row
    for i, it in enumerate(items):
        r = current_r
        # Formatting values
        src_qty = float(it.get("source_qty", 1.0) or 0.0)
        rate = float(it.get("rate", 0.0) or 0.0)
        dup_qty = float(it.get("duplicate_qty", 0.0) or 0.0)

        # Approved reviewed qty override or formula
        approved_rev_qty = it.get("reviewed_qty")

        # Col A: Source Row
        c_a = ws.cell(r, 1, it.get("source_row", i + 1))
        c_a.alignment = Alignment(horizontal="center", vertical="top")

        # Col B: Item
        c_b = ws.cell(r, 2, it.get("item_code") or it.get("item", f"{i+1}"))
        c_b.alignment = Alignment(horizontal="center", vertical="top")

        # Col C: Description
        c_c = ws.cell(r, 3, it.get("description", ""))
        c_c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Col D: Unit
        c_d = ws.cell(r, 4, it.get("unit", "Item"))
        c_d.alignment = Alignment(horizontal="center", vertical="top")

        # Col E: Source Qty
        c_e = ws.cell(r, 5, src_qty)
        c_e.number_format = num_fmt
        c_e.alignment = Alignment(horizontal="right", vertical="top")

        # Col F: Rate (LKR)
        c_f = ws.cell(r, 6, rate)
        c_f.number_format = num_fmt
        c_f.alignment = Alignment(horizontal="right", vertical="top")

        # Col G: Source Amount (Formula =E*F)
        c_g = ws.cell(r, 7, f"=E{r}*F{r}")
        c_g.number_format = num_fmt
        c_g.alignment = Alignment(horizontal="right", vertical="top")

        # Col H: Duplicate Qty
        c_h = ws.cell(r, 8, dup_qty)
        c_h.number_format = num_fmt
        c_h.alignment = Alignment(horizontal="right", vertical="top")

        # Col I: Duplicate Amount (Formula =H*F)
        c_i = ws.cell(r, 9, f"=H{r}*F{r}")
        c_i.number_format = num_fmt
        c_i.alignment = Alignment(horizontal="right", vertical="top")

        # Col J: Reviewed Qty (Preserve approved manual qty or formula =E-H)
        if approved_rev_qty is not None and not str(approved_rev_qty).startswith("="):
            c_j = ws.cell(r, 10, float(approved_rev_qty))
        else:
            c_j = ws.cell(r, 10, f"=E{r}-H{r}")
        c_j.number_format = num_fmt
        c_j.alignment = Alignment(horizontal="right", vertical="top")

        # Col K: Reviewed Amount (Formula =J*F)
        c_k = ws.cell(r, 11, f"=J{r}*F{r}")
        c_k.number_format = num_fmt
        c_k.alignment = Alignment(horizontal="right", vertical="top")

        # Col L: Overlap / Reason
        c_l = ws.cell(r, 12, it.get("overlap_reason") or it.get("validation_notes") or "")
        c_l.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Col M: Action
        act = it.get("action") or ("REDUCE" if dup_qty > 0 else "RETAIN")
        c_m = ws.cell(r, 13, act)
        c_m.alignment = Alignment(horizontal="center", vertical="top")

        # Col N: Confidence
        conf = it.get("confidence") or "High"
        c_n = ws.cell(r, 14, conf)
        c_n.alignment = Alignment(horizontal="center", vertical="top")

        # Col O: Remarks
        c_o = ws.cell(r, 15, it.get("remarks") or "")
        c_o.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Apply fonts and borders to all 15 cells
        for col_idx in range(1, 16):
            cell = ws.cell(r, col_idx)
            cell.font = Font(name="Carlito", size=11, bold=False)
            cell.border = data_border

        # Sensible row height for narrative wrapping
        desc_len = len(str(it.get("description", "")))
        ws.row_dimensions[r].height = max(24.0, min(80.0, 18.0 + (desc_len // 45) * 14.0))

        current_r += 1

    last_data_r = current_r - 1

    # Write QS Summary Block at the bottom
    sum_r = last_data_r + 2

    summary_labels = [
        ("Source BOQ subtotal", f"=SUM(G5:G{last_data_r})", True),
        ("Identified duplicate deductions", f"=SUM(I5:I{last_data_r})", False),
        ("Reviewed direct electrical subtotal", f"=SUM(K5:K{last_data_r})", True),
        ("Design-development contingency", contingency_rate, False),
        ("Contingency Amount", f"=K{sum_r+2}*K{sum_r+3}", False),
        ("Engineer's Estimate excl. VAT", f"=K{sum_r+2}+K{sum_r+4}", True),
        ("VAT", vat_status, False),
    ]

    for idx, (label, val, is_bold) in enumerate(summary_labels):
        r = sum_r + idx
        c_lbl = ws.cell(r, 6, label)
        c_lbl.font = Font(name="Carlito", size=11, bold=is_bold)
        c_lbl.alignment = Alignment(horizontal="right", vertical="center")

        c_val = ws.cell(r, 11, val)
        c_val.font = Font(name="Carlito", size=11, bold=is_bold)
        c_val.alignment = Alignment(horizontal="right", vertical="center")

        if label == "Design-development contingency":
            c_val.number_format = "0.0%"
        elif label == "VAT":
            c_val.alignment = Alignment(horizontal="center", vertical="center")
        else:
            c_val.number_format = num_fmt


def _populate_recon_items(
    ws: openpyxl.worksheet.worksheet.Worksheet,
    recon_items: list[list | dict],
    pkg: dict,
):
    """
    Populates reconciliation items into the dedicated scope reconciliation sheet.
    """
    start_r = 4
    max_r = ws.max_row
    for r in range(start_r, max_r + 10):
        for c in range(1, 9):
            ws.cell(r, c).value = None

    thin_side = Side(style="thin", color="D9D9D9")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    for i, row_data in enumerate(recon_items):
        r = start_r + i
        if isinstance(row_data, dict):
            vals = [
                row_data.get("scope_element", ""),
                row_data.get("source_boq", ""),
                row_data.get("other_package", ""),
                row_data.get("consolidated_treatment", ""),
                row_data.get("deduction", ""),
                row_data.get("reason", ""),
                row_data.get("risk", ""),
                row_data.get("tender_action", ""),
            ]
        else:
            vals = list(row_data)

        for col_idx, val in enumerate(vals[:8], start=1):
            cell = ws.cell(r, col_idx, val)
            cell.font = Font(name="Carlito", size=10, bold=False)
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border = border

        ws.row_dimensions[r].height = 42.0


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for exact total page count ('Page X of Y') and professional running footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header thin line
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(20, 575, 822, 575)

        # Header title
        self.drawString(20, 580, "BSR Rate Hub – Sri Lanka BOQ Data System | Master QS Engineering Export")

        # Running footer line
        self.line(20, 25, 822, 25)

        # Footer notes & page number
        self.drawString(20, 15, "Confidential – Hospital Infrastructure Consolidation & Deduplication Audit")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(822, 15, page_str)
        self.restoreState()


def generate_package_pdf(
    package_key: str = "electrical",
    variant: str = "combined",  # 'combined', 'boq', or 'reconciliation'
    project_title: str | None = None,
    source_note: str | None = None,
    contingency_rate: float = 0.10,
    items: list[dict] | None = None,
    reconciliation_items: list[list | dict] | None = None,
    vat_status: str = "Excluded",
) -> bytes:
    """
    Generates a high-fidelity PDF report reproducing the exact appearance of the
    Excel reference workbook:
    - Landscape A4 layout
    - Dark teal header banner (#1F4E78) with white bold text
    - Light blue explanatory note box (#D9EAF7)
    - Blue table header (#5B9BD5) with white bold text
    - Alternating row shading, thin borders, wrapped text, and currency formatting
    - Executive summary total box with deductions and contingency
    - Dedicated Reconciliation Section on separate page
    """
    # Load baseline data if custom items not provided
    base_data = get_template_package_data(package_key)
    pkg = base_data["package"]

    final_title = project_title.strip() if project_title else base_data["project_title"]
    final_note = source_note.strip() if source_note else base_data["source_note"]
    final_recon_title = base_data["recon_title"]

    boq_data = items if items is not None and len(items) > 0 else base_data["boq_items"]
    recon_data = reconciliation_items if reconciliation_items is not None else base_data["recon_items"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=30,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.white,
        alignment=1,  # Center
    )

    note_style = ParagraphStyle(
        "SourceNote",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=1,  # Center
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#0F172A"),
    )

    cell_right = ParagraphStyle(
        "TableCellRight",
        parent=cell_style,
        alignment=2,  # Right
    )

    cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=cell_style,
        alignment=1,  # Center
    )

    story = []

    # =========================================================================
    # SECTION 1: BOQ REVIEWED
    # =========================================================================
    if variant in ["combined", "boq"]:
        # Merged Dark Teal Title Banner
        title_table = Table(
            [[Paragraph(final_title.upper(), title_style)]],
            colWidths=[802],
        )
        title_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(title_table)
        story.append(Spacer(1, 4))

        # Explanatory Note Box
        note_table = Table(
            [[Paragraph(f"<b>Audit Basis:</b> {final_note}", note_style)]],
            colWidths=[802],
        )
        note_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D9EAF7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B9D5ED")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(note_table)
        story.append(Spacer(1, 6))

        # Build BOQ Data Table
        col_widths = [22, 40, 145, 24, 38, 52, 60, 36, 52, 38, 60, 95, 46, 36, 58]

        headers = [
            Paragraph("Row", th_style),
            Paragraph("Item", th_style),
            Paragraph("Description", th_style),
            Paragraph("Unit", th_style),
            Paragraph("Src Qty", th_style),
            Paragraph("Rate (LKR)", th_style),
            Paragraph("Src Amount", th_style),
            Paragraph("Dup Qty", th_style),
            Paragraph("Dup Amount", th_style),
            Paragraph("Rev Qty", th_style),
            Paragraph("Rev Amount", th_style),
            Paragraph("Overlap / Reason", th_style),
            Paragraph("Action", th_style),
            Paragraph("Conf.", th_style),
            Paragraph("Remarks", th_style),
        ]

        table_rows = [headers]

        total_src_amount = 0.0
        total_dup_amount = 0.0
        total_rev_amount = 0.0

        for i, it in enumerate(boq_data):
            src_qty = float(it.get("source_qty", 1.0) or 0.0)
            rate = float(it.get("rate", 0.0) or 0.0)
            dup_qty = float(it.get("duplicate_qty", 0.0) or 0.0)

            src_amt = src_qty * rate
            dup_amt = dup_qty * rate

            app_rev = it.get("reviewed_qty")
            rev_qty = float(app_rev) if app_rev is not None else max(0.0, src_qty - dup_qty)
            rev_amt = rev_qty * rate

            total_src_amount += src_amt
            total_dup_amount += dup_amt
            total_rev_amount += rev_amt

            act = it.get("action") or ("REDUCE" if dup_qty > 0 else "RETAIN")
            conf = it.get("confidence") or "High"

            row_cells = [
                Paragraph(str(it.get("source_row", i + 1)), cell_center),
                Paragraph(str(it.get("item_code") or it.get("item", f"{i+1}")), cell_center),
                Paragraph(str(it.get("description", "")), cell_style),
                Paragraph(str(it.get("unit", "Item")), cell_center),
                Paragraph(f"{src_qty:,.2f}", cell_right),
                Paragraph(f"{rate:,.2f}", cell_right),
                Paragraph(f"{src_amt:,.2f}", cell_right),
                Paragraph(f"{dup_qty:,.2f}", cell_right),
                Paragraph(f"{dup_amt:,.2f}", cell_right),
                Paragraph(f"{rev_qty:,.2f}", cell_right),
                Paragraph(f"{rev_amt:,.2f}", cell_right),
                Paragraph(str(it.get("overlap_reason") or it.get("validation_notes") or "-"), cell_style),
                Paragraph(f"<b>{act}</b>", cell_center),
                Paragraph(conf, cell_center),
                Paragraph(str(it.get("remarks", "")), cell_style),
            ]
            table_rows.append(row_cells)

        boq_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        boq_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B9BD5")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(boq_table)
        story.append(Spacer(1, 10))

        # Executive Summary Totals Box
        contingency_amt = total_rev_amount * contingency_rate
        est_excl_vat = total_rev_amount + contingency_amt

        summary_data = [
            [
                Paragraph("<b>Source BOQ Subtotal:</b>", cell_style),
                Paragraph(f"<b>LKR {total_src_amount:,.2f}</b>", cell_right),
            ],
            [
                Paragraph("<b>Identified Duplicate Deductions:</b>", cell_style),
                Paragraph(f"<font color='#B91C1C'><b>- LKR {total_dup_amount:,.2f}</b></font>", cell_right),
            ],
            [
                Paragraph("<b>Reviewed Direct Electrical Subtotal:</b>", cell_style),
                Paragraph(f"<b>LKR {total_rev_amount:,.2f}</b>", cell_right),
            ],
            [
                Paragraph(f"<b>Design-development Contingency ({contingency_rate*100:.1f}%):</b>", cell_style),
                Paragraph(f"<b>LKR {contingency_amt:,.2f}</b>", cell_right),
            ],
            [
                Paragraph("<b>Engineer's Estimate excl. VAT:</b>", cell_style),
                Paragraph(f"<font color='#1E3A8A' size='8'><b>LKR {est_excl_vat:,.2f}</b></font>", cell_right),
            ],
            [
                Paragraph("<b>VAT Basis:</b>", cell_style),
                Paragraph(f"<b>{vat_status}</b>", cell_right),
            ],
        ]

        summary_table = Table(summary_data, colWidths=[200, 130])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1F4E78")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        # Align summary box to the right side
        wrapper = Table([[Table([[""]], colWidths=[472]), summary_table]], colWidths=[472, 330])
        wrapper.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(KeepTogether([wrapper]))

    # =========================================================================
    # SECTION 2: RECONCILIATION SHEET
    # =========================================================================
    if variant in ["combined", "reconciliation"]:
        if variant == "combined":
            story.append(PageBreak())

        # Dark Teal Banner for Reconciliation
        recon_title_table = Table(
            [[Paragraph(final_recon_title.upper(), title_style)]],
            colWidths=[802],
        )
        recon_title_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1F4E78")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(recon_title_table)
        story.append(Spacer(1, 8))

        recon_headers = [
            Paragraph(col, th_style) for col in pkg["recon_columns"]
        ]

        recon_widths = [105, 105, 115, 105, 85, 95, 52, 140]

        recon_rows = [recon_headers]
        for row in recon_data:
            if isinstance(row, dict):
                r_vals = [
                    row.get("scope_element", ""),
                    row.get("source_boq", ""),
                    row.get("other_package", ""),
                    row.get("consolidated_treatment", ""),
                    row.get("deduction", ""),
                    row.get("reason", ""),
                    row.get("risk", ""),
                    row.get("tender_action", ""),
                ]
            else:
                r_vals = list(row)

            cell_row = []
            for col_i, val in enumerate(r_vals[:8]):
                align = cell_center if col_i == 6 else cell_style
                cell_row.append(Paragraph(str(val or "-"), align))
            recon_rows.append(cell_row)

        recon_table = Table(recon_rows, colWidths=recon_widths, repeatRows=1)
        recon_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B9BD5")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(recon_table)

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()
