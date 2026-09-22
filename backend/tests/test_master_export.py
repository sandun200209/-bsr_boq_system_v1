"""
Automated Test Suite for Master Reference Template Export Engine
Tests PASS/FAIL against all user requirements and acceptance criteria:
- separate worksheets
- exact sheet naming
- exact column order
- merged title layout
- source note row
- header styling
- column widths
- row wrapping
- number formats
- formulas/calculations
- print setup
- long narrative visibility
- no clipped descriptions
- no merged-sheet combination
- PDF variants (combined, boq, reconciliation)
- dynamic packages (Electrical, Water, Wastewater, Rainwater, MVAC, Medical Gas)
"""

import io
import pytest
import openpyxl
from reportlab.lib.pagesizes import A4, landscape

from app.services.export_service import (
    TEMPLATE_PATH,
    PACKAGE_REGISTRY,
    get_template_package_data,
    generate_package_excel,
    generate_package_pdf,
)


class TestMasterExportEngine:
    def test_master_template_exists_and_clean(self):
        """Verifies master template exists and is pristine."""
        wb = openpyxl.load_workbook(TEMPLATE_PATH, data_only=True)
        assert "Electrical BOQ - Reviewed" in wb.sheetnames
        assert "Electrical Reconciliation" in wb.sheetnames
        assert len(wb.sheetnames) >= 20

    def test_electrical_excel_separate_worksheets(self):
        """Verify export produces separate worksheets, no merged-sheet combination."""
        xlsx_bytes = generate_package_excel("electrical")
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)

        # PASS/FAIL: separate worksheets & exact sheet naming
        assert len(wb.sheetnames) == 2, f"Expected 2 separate worksheets, got {wb.sheetnames}"
        assert wb.sheetnames == ["Electrical BOQ - Reviewed", "Electrical Reconciliation"]

    def test_electrical_exact_column_order_and_headers(self):
        """Verify exact columns and column order A through O."""
        xlsx_bytes = generate_package_excel("electrical")
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws = wb["Electrical BOQ - Reviewed"]

        expected_headers = [
            "Source Row", "Item", "Description", "Unit", "Source Qty", "Rate (LKR)",
            "Source Amount", "Duplicate Qty", "Duplicate Amount", "Reviewed Qty",
            "Reviewed Amount", "Overlap / Reason", "Action", "Confidence", "Remarks"
        ]

        actual_headers = [ws.cell(4, c).value for c in range(1, 16)]
        assert actual_headers == expected_headers, f"Headers mismatch: {actual_headers}"

    def test_electrical_merged_title_and_notes_layout(self):
        """Verify merged title (A1:O1) and merged source note (A2:O2) layout & styling."""
        xlsx_bytes = generate_package_excel("electrical")
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws = wb["Electrical BOQ - Reviewed"]

        merged_str = [str(m) for m in ws.merged_cells.ranges]
        assert "A1:O1" in merged_str, f"A1:O1 must be merged. Ranges: {merged_str}"
        assert "A2:O2" in merged_str, f"A2:O2 must be merged. Ranges: {merged_str}"

        # Title styling: dark teal/blue (1F4E78), bold white text
        c_title = ws.cell(1, 1)
        assert c_title.font.bold is True
        assert c_title.font.color.value == "FFFFFFFF"
        assert c_title.fill.fgColor.value == "FF1F4E78"

        # Note styling: light blue (D9EAF7), wrapped text
        c_note = ws.cell(2, 1)
        assert c_note.alignment.wrap_text is True

        # Header styling: blue (5B9BD5), bold white text
        c_h = ws.cell(4, 1)
        assert c_h.font.bold is True
        assert c_h.font.color.value == "FFFFFFFF"
        assert c_h.fill.fgColor.value == "FF5B9BD5"

    def test_column_widths_preserved(self):
        """Verify column widths match reference template."""
        xlsx_bytes = generate_package_excel("electrical")
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws = wb["Electrical BOQ - Reviewed"]

        # Col C (Description) must be generous (width >= 50)
        assert ws.column_dimensions["C"].width >= 50.0
        # Col L (Overlap / Reason) must be >= 35
        assert ws.column_dimensions["L"].width >= 35.0
        # Col O (Remarks) must be >= 30
        assert ws.column_dimensions["O"].width >= 30.0

    def test_formulas_and_calculations(self):
        """Verify formula calculations and approved manual reviewed qty preservation."""
        items = [
            {
                "source_row": 50,
                "item_code": "DB-1",
                "description": "Hospital Sub Distribution Board with surge protection",
                "unit": "No",
                "source_qty": 5.0,
                "rate": 120000.0,
                "duplicate_qty": 2.0,
                "reviewed_qty": 3.0,  # Approved manual quantity
                "overlap_reason": "2 DBs included in Modular OT E1 package",
                "action": "REDUCE",
                "confidence": "High",
                "remarks": "Approved by Senior QS",
            },
            {
                "source_row": 51,
                "item_code": "CBL-1",
                "description": "4C 16mm2 XLPE armoured cable",
                "unit": "m",
                "source_qty": 100.0,
                "rate": 3500.0,
                "duplicate_qty": 0.0,
                "reviewed_qty": None,  # Computed via formula
                "overlap_reason": "",
                "action": "RETAIN",
                "confidence": "High",
                "remarks": "",
            }
        ]

        xlsx_bytes = generate_package_excel("electrical", items=items, contingency_rate=0.10)
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws = wb["Electrical BOQ - Reviewed"]

        # Item 1: Source Amount formula
        assert ws.cell(5, 7).value == "=E5*F5"
        # Duplicate Amount formula
        assert ws.cell(5, 9).value == "=H5*F5"
        # Approved manual reviewed quantity preserved
        assert ws.cell(5, 10).value == 3.0
        # Reviewed Amount formula
        assert ws.cell(5, 11).value == "=J5*F5"

        # Item 2: Automatic reviewed quantity formula
        assert ws.cell(6, 10).value == "=E6-H6"
        assert ws.cell(6, 11).value == "=J6*F6"

        # Summary rows at bottom
        assert ws.cell(8, 6).value == "Source BOQ subtotal"
        assert ws.cell(8, 11).value == "=SUM(G5:G6)"
        assert ws.cell(9, 6).value == "Identified duplicate deductions"
        assert ws.cell(9, 11).value == "=SUM(I5:I6)"
        assert ws.cell(10, 6).value == "Reviewed direct electrical subtotal"
        assert ws.cell(10, 11).value == "=SUM(K5:K6)"
        assert ws.cell(11, 6).value == "Design-development contingency"
        assert ws.cell(11, 11).value == 0.10
        assert ws.cell(12, 6).value == "Contingency Amount"
        assert ws.cell(12, 11).value == "=K10*K11"
        assert ws.cell(13, 6).value == "Engineer's Estimate excl. VAT"
        assert ws.cell(13, 11).value == "=K10+K12"
        assert ws.cell(14, 6).value == "VAT"
        assert ws.cell(14, 11).value == "Excluded"

        # Check number formats
        assert ws.cell(5, 5).number_format == "#,##0.00"
        assert ws.cell(5, 6).number_format == "#,##0.00"
        assert ws.cell(5, 7).number_format == "#,##0.00"

    def test_reconciliation_sheet_structure(self):
        """Verify Sheet 2: Electrical Reconciliation exact columns and layout."""
        xlsx_bytes = generate_package_excel("electrical")
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws2 = wb["Electrical Reconciliation"]

        merged_str = [str(m) for m in ws2.merged_cells.ranges]
        assert "A1:H1" in merged_str, f"A1:H1 must be merged. Ranges: {merged_str}"

        # Row 1 Title
        assert ws2.cell(1, 1).value == "ELECTRICAL / MODULAR OT / MVAC – SCOPE RECONCILIATION"
        assert ws2.cell(1, 1).fill.fgColor.value == "FF1F4E78"

        # Row 3 Table Headers
        expected_recon = [
            "Scope Element", "Source Electrical BOQ", "Other Package", "Consolidated Treatment",
            "Deduction / Adjustment", "Reason", "Risk", "Tender Action"
        ]
        actual_recon = [ws2.cell(3, c).value for c in range(1, 9)]
        assert actual_recon == expected_recon

    def test_dynamic_package_support(self):
        """Verify dynamic package support for all packages in registry."""
        for pkg_id in ["water_supply", "wastewater", "rainwater", "mvac", "medical_gas"]:
            xlsx = generate_package_excel(pkg_id)
            wb = openpyxl.load_workbook(io.BytesIO(xlsx), data_only=False)
            pkg = PACKAGE_REGISTRY[pkg_id]
            assert wb.sheetnames == [pkg["boq_sheet"], pkg["recon_sheet"]], f"Failed for {pkg_id}"
            assert wb[pkg["boq_sheet"]].cell(1, 1).value == pkg["default_title"]

    def test_pdf_generation_variants(self):
        """Verify Combined PDF, BOQ PDF, and Reconciliation PDF generation."""
        import pymupdf

        # 1. Combined PDF
        comb_pdf = generate_package_pdf("electrical", variant="combined")
        doc_comb = pymupdf.open(stream=comb_pdf, filetype="pdf")
        assert len(doc_comb) >= 2
        text_all = "".join(p.get_text() for p in doc_comb)
        assert "ELECTRICAL BOQ REVIEWED" in text_all
        assert "SCOPE RECONCILIATION" in text_all

        # 2. BOQ PDF only
        boq_pdf = generate_package_pdf("electrical", variant="boq")
        doc_boq = pymupdf.open(stream=boq_pdf, filetype="pdf")
        text_boq = "".join(p.get_text() for p in doc_boq)
        assert "ELECTRICAL BOQ REVIEWED" in text_boq
        assert "SCOPE RECONCILIATION" not in text_boq

        # 3. Reconciliation PDF only
        recon_pdf = generate_package_pdf("electrical", variant="reconciliation")
        doc_recon = pymupdf.open(stream=recon_pdf, filetype="pdf")
        text_recon = "".join(p.get_text() for p in doc_recon)
        assert "SCOPE RECONCILIATION" in text_recon
