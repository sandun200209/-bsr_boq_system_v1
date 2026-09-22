from __future__ import annotations
import io
import os
import copy
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import (
    Project,
    ProjectSection,
    ProjectItem,
    DuplicationRecord,
    ChangeRegisterRecord,
    ReconciliationRecord,
    Template,
    TemplateMapping,
)

DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "Matara_OT_Renovation_Consolidated_BOQ_Estimate_Rev7_Electrical_Ancillary_Deduplicated.xlsx"

def get_or_register_default_template(db: Session) -> Template:
    """
    Registers the master Excel reference workbook in the database if not present.
    """
    tpl = db.scalar(select(Template).where(Template.is_default == True))
    if tpl:
        return tpl

    tpl = Template(
        template_name="Matara OT Renovation Master Template Rev7",
        file_path=str(DEFAULT_TEMPLATE_PATH),
        description="Master engineering estimate, duplication register, and reconciliation template.",
        is_default=True,
    )
    db.add(tpl)
    db.flush()

    # Register default section mappings
    mappings = [
        ("BOQ", "Electrical BOQ - Reviewed", 5, "B", None, "C", "D", "E", "F", "G", "H", "I", "J", "O"),
        ("BOQ", "Added Renovation BOQ", 5, "A", "B", "C", "D", "E", "F", "G", None, None, None, "K"),
        ("BOQ", "MVAC BOQ & Estimate", 5, "A", "B", "C", "D", "E", "F", "G", None, None, None, "K"),
        ("BOQ", "Water Supply BOQ & Estimate", 5, "A", "B", "C", "D", "E", "F", "G", None, None, None, "K"),
        ("DUPLICATION", "Site Works - Reviewed", 5, "A", "B", "C", "D", "E", "F", "G", "H", None, None, "K"),
        ("CHANGE_REGISTER", "Consolidation Change Register", 4, "A", None, "D", None, None, None, "I", None, "H", None, None),
        ("RECONCILIATION", "Electrical Reconciliation", 4, None, None, None, None, None, None, None, None, None, None, None),
    ]

    for stype, sheet, start_r, c_item, c_bsr, c_desc, c_unit, c_qty, c_rate, c_amt, c_yr, c_src, c_adj, c_rem in mappings:
        db.add(
            TemplateMapping(
                template_id=tpl.id,
                section_type=stype,
                target_sheet=sheet,
                start_row=start_r,
                item_no_column=c_item,
                bsr_ref_column=c_bsr,
                description_column=c_desc,
                unit_column=c_unit,
                quantity_column=c_qty,
                rate_column=c_rate,
                amount_column=c_amt,
                rate_year_column=c_yr,
                rate_source_column=c_src,
                adjustment_column=c_adj,
                remarks_column=c_rem,
            )
        )

    db.commit()
    db.refresh(tpl)
    return tpl


def export_project_excel(
    project: Project,
    mode: str = "consolidated",
    target_section_id: int | None = None,
    template_path: str | None = None,
) -> io.BytesIO:
    """
    Exports project data into the Master Excel Template:
    - Mode 'consolidated' (Option A): One Excel workbook with each section as a separate worksheet.
    - Mode 'separate' (Option B): An Excel file containing strictly the selected section.
    
    Populates:
    1. Standard BOQ sections (Item, Description, Unit, Qty, Rate, Live Formulas, Rate Source Year).
    2. 'MATARA OT RENOVATION – SITE WORKS BOQ REVIEWED FOR DUPLICATION' with exact BOQ-style columns:
       Item, BSR Ref, Description, Unit, Qty, Rate, Amount, Rate Source Year, Duplicate With, Status, Remarks.
    3. 'REV 7 CONSOLIDATION CHANGE / DUPLICATION REGISTER' with exact audit columns:
       Ref, Package / Sheet, Item, Description, Original Status, REV 7 Action, Duplicate With, Rate Source, Cost Impact, Reason.
    4. Scope Reconciliation sections with approved records.
    
    Preserves all merged cells, fonts, fills, borders, widths, row heights, and print setup.
    Never modifies the original master workbook on disk.
    """
    t_path = template_path or str(DEFAULT_TEMPLATE_PATH)
    wb = openpyxl.load_workbook(t_path, data_only=False)

    thin_side = Side(style="thin", color="D9D9D9")
    data_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    num_fmt = "#,##0.00"

    # Filter sections to export
    if mode == "separate" and target_section_id:
        active_sections = [s for s in project.sections if s.id == target_section_id]
        if not active_sections:
            active_sections = project.sections[:1]
    else:
        active_sections = project.sections

    # Map sheets needed
    target_sheets_to_keep = set()
    for s in active_sections:
        if s.target_sheet and s.target_sheet in wb.sheetnames:
            target_sheets_to_keep.add(s.target_sheet)

    if not target_sheets_to_keep:
        target_sheets_to_keep.add(wb.sheetnames[0])

    # Populate each section into its target worksheet
    for section in active_sections:
        sheet_name = section.target_sheet
        if not sheet_name or sheet_name not in wb.sheetnames:
            continue

        ws = wb[sheet_name]

        # -------------------------------------------------------------
        # 1. DUPLICATION REVIEW SHEET: OT Site Works Duplication Review
        # Target: 'Site Works - Reviewed'
        # -------------------------------------------------------------
        if section.section_type == "DUPLICATION" or "site works" in section.section_name.lower():
            # Clear old rows from row 5 down
            for r in range(5, max(ws.max_row + 5, 20)):
                for c in range(1, 15):
                    if type(ws.cell(r, c)).__name__ != 'MergedCell': ws.cell(r, c).value = None

            # Headers on row 4:
            # Col A: Item, Col B: BSR Ref, Col C: Description, Col D: Unit, Col E: Qty,
            # Col F: Rate, Col G: Amount, Col H: Rate Source Year, Col I: Duplicate With,
            # Col J: Status, Col K: Remarks
            current_r = 5
            for idx, d_rec in enumerate(section.duplication_records, start=1):
                r = current_r
                qty_val = float(d_rec.qty or 0.0)
                rate_val = float(d_rec.rate or 0.0)

                # Col A: Item
                c_a = ws.cell(r, 1, d_rec.item or str(idx))
                c_a.alignment = Alignment(horizontal="center", vertical="top")

                # Col B: BSR Ref
                c_b = ws.cell(r, 2, d_rec.bsr_ref or "-")
                c_b.alignment = Alignment(horizontal="center", vertical="top")

                # Col C: Description
                c_c = ws.cell(r, 3, d_rec.description)
                c_c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                # Col D: Unit
                c_d = ws.cell(r, 4, d_rec.unit or "Item")
                c_d.alignment = Alignment(horizontal="center", vertical="top")

                # Col E: Qty
                c_e = ws.cell(r, 5, qty_val)
                c_e.number_format = num_fmt
                c_e.alignment = Alignment(horizontal="right", vertical="top")

                # Col F: Rate
                c_f = ws.cell(r, 6, rate_val)
                c_f.number_format = num_fmt
                c_f.alignment = Alignment(horizontal="right", vertical="top")

                # Col G: Amount (Live Formula =E*F)
                c_g = ws.cell(r, 7, f"=E{r}*F{r}")
                c_g.number_format = num_fmt
                c_g.alignment = Alignment(horizontal="right", vertical="top")

                # Col H: Rate Source Year
                c_h = ws.cell(r, 8, str(d_rec.rate_source_year or project.project_base_year))
                c_h.alignment = Alignment(horizontal="center", vertical="top")

                # Col I: Duplicate With
                c_i = ws.cell(r, 9, d_rec.duplicate_with or "-")
                c_i.alignment = Alignment(horizontal="left", vertical="top")

                # Col J: Status
                c_j = ws.cell(r, 10, d_rec.status or "RETAIN")
                c_j.alignment = Alignment(horizontal="center", vertical="top")

                # Col K: Remarks
                c_k = ws.cell(r, 11, d_rec.remarks or "")
                c_k.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                for col_idx in range(1, 12):
                    cell = ws.cell(r, col_idx)
                    cell.font = Font(name="Carlito", size=10, bold=False)
                    cell.border = data_border

                desc_len = len(str(d_rec.description or ""))
                ws.row_dimensions[r].height = max(24.0, min(80.0, 18.0 + (desc_len // 45) * 14.0))
                current_r += 1

            # Subtotal row
            sub_r = current_r + 1
            ws.cell(sub_r, 3, "Reviewed Subtotal").font = Font(name="Carlito", size=11, bold=True)
            c_sub = ws.cell(sub_r, 7, f"=SUM(G5:G{current_r - 1})")
            c_sub.font = Font(name="Carlito", size=11, bold=True)
            c_sub.number_format = num_fmt
            c_sub.alignment = Alignment(horizontal="right", vertical="top")

        # -------------------------------------------------------------
        # 2. CHANGE REGISTER SHEET: REV 7 Consolidation Change Register
        # Target: 'Consolidation Change Register'
        # -------------------------------------------------------------
        elif section.section_type == "CHANGE_REGISTER" or "change" in section.section_name.lower():
            # Clear old rows from row 4 down
            for r in range(4, max(ws.max_row + 5, 20)):
                for c in range(1, 12):
                    if type(ws.cell(r, c)).__name__ != 'MergedCell': ws.cell(r, c).value = None

            # Headers on row 3:
            # Col A: Ref, Col B: Package / Sheet, Col C: Item, Col D: Description,
            # Col E: Original Status, Col F: REV 7 Action, Col G: Duplicate With,
            # Col H: Rate Source, Col I: Cost Impact, Col J: Reason
            current_r = 4
            for c_rec in section.change_register_records:
                r = current_r

                # Col A: Ref
                c_a = ws.cell(r, 1, c_rec.ref_code)
                c_a.alignment = Alignment(horizontal="center", vertical="top")

                # Col B: Package / Sheet
                c_b = ws.cell(r, 2, c_rec.package_sheet)
                c_b.alignment = Alignment(horizontal="center", vertical="top")

                # Col C: Item
                c_c = ws.cell(r, 3, c_rec.item_code or "-")
                c_c.alignment = Alignment(horizontal="center", vertical="top")

                # Col D: Description
                c_d = ws.cell(r, 4, c_rec.description)
                c_d.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                # Col E: Original Status
                c_e = ws.cell(r, 5, c_rec.original_status or "-")
                c_e.alignment = Alignment(horizontal="left", vertical="top")

                # Col F: REV 7 Action
                c_f = ws.cell(r, 6, c_rec.rev7_action or "-")
                c_f.alignment = Alignment(horizontal="left", vertical="top")

                # Col G: Duplicate With
                c_g = ws.cell(r, 7, c_rec.duplicate_with or "-")
                c_g.alignment = Alignment(horizontal="left", vertical="top")

                # Col H: Rate Source
                c_h = ws.cell(r, 8, c_rec.rate_source or "-")
                c_h.alignment = Alignment(horizontal="center", vertical="top")

                # Col I: Cost Impact
                c_i = ws.cell(r, 9, float(c_rec.cost_impact or 0.0))
                c_i.number_format = num_fmt
                c_i.alignment = Alignment(horizontal="right", vertical="top")

                # Col J: Reason
                c_j = ws.cell(r, 10, c_rec.reason or "")
                c_j.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                for col_idx in range(1, 11):
                    cell = ws.cell(r, col_idx)
                    cell.font = Font(name="Carlito", size=10, bold=False)
                    cell.border = data_border

                desc_len = len(str(c_rec.description or ""))
                ws.row_dimensions[r].height = max(24.0, min(80.0, 18.0 + (desc_len // 45) * 14.0))
                current_r += 1

            # Summary impact row
            sub_r = current_r + 1
            ws.cell(sub_r, 4, "Total Net Cost Impact (LKR)").font = Font(name="Carlito", size=11, bold=True)
            c_imp = ws.cell(sub_r, 9, f"=SUM(I4:I{current_r - 1})")
            c_imp.font = Font(name="Carlito", size=11, bold=True)
            c_imp.number_format = num_fmt
            c_imp.alignment = Alignment(horizontal="right", vertical="top")

        # -------------------------------------------------------------
        # 3. RECONCILIATION SHEET
        # -------------------------------------------------------------
        elif section.section_type == "RECONCILIATION" or "reconciliation" in section.section_name.lower():
            start_r = 4
            for r in range(start_r, max(ws.max_row + 5, 20)):
                for c in range(1, 9):
                    if type(ws.cell(r, c)).__name__ != 'MergedCell': ws.cell(r, c).value = None

            approved_records = [rec for rec in section.reconciliation_records if rec.is_approved]
            for idx, r_rec in enumerate(approved_records):
                r = start_r + idx
                vals = [
                    r_rec.scope_element,
                    r_rec.source_boq or "-",
                    r_rec.other_package or "-",
                    r_rec.consolidated_treatment or "-",
                    r_rec.deduction_amount or "-",
                    r_rec.reason or "-",
                    r_rec.risk or "Low",
                    r_rec.tender_action or "-",
                ]
                for c_idx, val in enumerate(vals, start=1):
                    cell = ws.cell(r, c_idx, val)
                    cell.font = Font(name="Carlito", size=10, bold=False)
                    cell.border = data_border
                    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # -------------------------------------------------------------
        # 4. STANDARD BOQ SECTIONS (Civil, Electrical, MVAC, Water, etc.)
        # -------------------------------------------------------------
        else:
            start_row = 5
            for r in range(start_row, max(ws.max_row + 15, 30)):
                for c in range(1, 16):
                    if type(ws.cell(r, c)).__name__ != 'MergedCell': ws.cell(r, c).value = None

            current_r = start_row
            for idx, it in enumerate(section.items, start=1):
                r = current_r
                qty_val = float(it.quantity or 0.0)
                rate_val = float(it.selected_rate or 0.0)

                # Col A: Source Row / Item No
                c_a = ws.cell(r, 1, it.item_no or str(idx))
                c_a.alignment = Alignment(horizontal="center", vertical="top")

                # Col B: Item Code
                c_b = ws.cell(r, 2, it.rate_source_item_code or it.item_no or str(idx))
                c_b.alignment = Alignment(horizontal="center", vertical="top")

                # Col C: Description
                c_c = ws.cell(r, 3, it.description)
                c_c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                # Col D: Unit
                c_d = ws.cell(r, 4, it.unit)
                c_d.alignment = Alignment(horizontal="center", vertical="top")

                # Col E: Source Qty
                c_e = ws.cell(r, 5, qty_val)
                c_e.number_format = num_fmt
                c_e.alignment = Alignment(horizontal="right", vertical="top")

                # Col F: Rate (LKR)
                c_f = ws.cell(r, 6, rate_val)
                c_f.number_format = num_fmt
                c_f.alignment = Alignment(horizontal="right", vertical="top")

                # Col G: Source Amount (Formula =E*F)
                c_g = ws.cell(r, 7, f"=E{r}*F{r}")
                c_g.number_format = num_fmt
                c_g.alignment = Alignment(horizontal="right", vertical="top")

                # Col H: Duplicate Qty (default 0)
                c_h = ws.cell(r, 8, 0.0)
                c_h.number_format = num_fmt
                c_h.alignment = Alignment(horizontal="right", vertical="top")

                # Col I: Duplicate Amount (Formula =H*F)
                c_i = ws.cell(r, 9, f"=H{r}*F{r}")
                c_i.number_format = num_fmt
                c_i.alignment = Alignment(horizontal="right", vertical="top")

                # Col J: Reviewed Qty (Formula =E-H)
                c_j = ws.cell(r, 10, f"=E{r}-H{r}")
                c_j.number_format = num_fmt
                c_j.alignment = Alignment(horizontal="right", vertical="top")

                # Col K: Reviewed Amount (Formula =J*F)
                c_k = ws.cell(r, 11, f"=J{r}*F{r}")
                c_k.number_format = num_fmt
                c_k.alignment = Alignment(horizontal="right", vertical="top")

                # Col L: Overlap / Reason
                c_l = ws.cell(r, 12, it.rate_justification or "")
                c_l.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                # Col M: Action
                c_m = ws.cell(r, 13, "RETAIN")
                c_m.alignment = Alignment(horizontal="center", vertical="top")

                # Col N: Rate Source Year / Confidence
                # Shows explicit rate source year
                c_n = ws.cell(r, 14, f"BSR {it.rate_source_year}")
                c_n.alignment = Alignment(horizontal="center", vertical="top")

                # Col O: Remarks & Source Book
                rem_text = it.remarks or ""
                if it.rate_source_book:
                    rem_text = f"[{it.rate_source_book}] {rem_text}".strip()
                c_o = ws.cell(r, 15, rem_text)
                c_o.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                for col_idx in range(1, 16):
                    cell = ws.cell(r, col_idx)
                    cell.font = Font(name="Carlito", size=11, bold=False)
                    cell.border = data_border

                desc_len = len(str(it.description or ""))
                ws.row_dimensions[r].height = max(24.0, min(80.0, 18.0 + (desc_len // 45) * 14.0))
                current_r += 1

            last_data_r = max(current_r - 1, start_row)
            sum_r = last_data_r + 2

            ws.cell(sum_r, 3, f"{section.section_name} Subtotal").font = Font(name="Carlito", size=11, bold=True)
            c_tot = ws.cell(sum_r, 11, f"=SUM(K5:K{last_data_r})")
            c_tot.font = Font(name="Carlito", size=11, bold=True)
            c_tot.number_format = num_fmt
            c_tot.alignment = Alignment(horizontal="right", vertical="top")

    # If Option A (consolidated) or Option B (separate):
    # Remove all worksheets not in target_sheets_to_keep
    all_names = list(wb.sheetnames)
    for sheet_name in all_names:
        if sheet_name not in target_sheets_to_keep:
            if len(wb.sheetnames) > 1:
                wb.remove(wb[sheet_name])

    output_stream = io.BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream

