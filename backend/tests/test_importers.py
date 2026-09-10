import pytest
import io
import tempfile
from pathlib import Path
import openpyxl

from app.importers.csv_importer import extract_csv
from app.importers.excel_importer import extract_excel
from app.importers.text_importer import extract_text
from app.importers.pdf_importer import fix_split_units
from app.services.validation_service import ValidationService, normalize_unit, detect_category_from_code
from app.services.compare_service import CompareService
from app.models import RateItem

def test_unit_normalization():
    assert normalize_unit("m3") == "m³"
    assert normalize_unit("m^3") == "m³"
    assert normalize_unit("cu.m") == "m³"
    assert normalize_unit("m2") == "m²"
    assert normalize_unit("sq.m") == "m²"
    assert normalize_unit("no") == "nr"
    assert normalize_unit("nos") == "nr"
    assert fix_split_units("m 3") == "m³"
    assert fix_split_units("m + 3") == "m³"
    assert fix_split_units("m + 2") == "m²"

def test_category_detection():
    code, name = detect_category_from_code("DM01")
    assert code == "DM"
    assert name == "Demolisher"

    code, name = detect_category_from_code("BK05c")
    assert code == "BK"
    assert name == "Brick Layer"

    code, name = detect_category_from_code("EW02")
    assert code == "EW"
    assert name == "Earth Work"

def test_validation_service():
    # Valid row
    status, conf, notes, unit = ValidationService.validate_rate_item(
        code="BK01",
        description="Brickwork in 225 mm 1:5 cement sand mortar",
        unit="m3",
        rate=30616.0,
    )
    assert status == "VALID"
    assert conf >= 0.8
    assert unit == "m³"
    assert notes is None

    # Invalid rate
    status, conf, notes, _ = ValidationService.validate_rate_item(
        code="BK01",
        description="Brickwork in 225 mm 1:5 cement sand mortar",
        unit="m3",
        rate=-50.0,
    )
    assert status == "NEEDS_REVIEW"
    assert "Zero or negative rate" in notes

    # Missing code
    status, conf, notes, _ = ValidationService.validate_rate_item(
        code=None,
        description="Brickwork",
        unit="m3",
        rate=100.0,
    )
    assert status == "NEEDS_REVIEW"
    assert "Missing item code" in notes

def test_csv_importer():
    csv_content = (
        "Code,Description,Unit,Rate\n"
        "DM01,Demolishing existing brick walls,m3,596.00\n"
        "BK01,Brickwork in 225mm 1:5 cement sand mortar,m3,30616.00\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        items = extract_csv(tmp_path)
        assert len(items) == 2
        assert items[0].item_code == "DM01"
        assert items[0].rate == 596.0
        assert items[0].unit == "m³"
        assert items[1].item_code == "BK01"
        assert items[1].rate == 30616.0
    finally:
        tmp_path.unlink(missing_ok=True)

def test_excel_importer():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rates"

    ws.append(["Item Code", "Work Description", "Unit", "Rate (LKR)"])
    ws.append(["EW01", "Excavation in ordinary soil up to 1.5m", "m3", 1250.00])
    ws.append(["CT01", "1:2:4 concrete in foundation", "m3", 24500.00])
    # Obvious noise lines that must be skipped automatically
    ws.append(["", "Overhead and Profit", "", None])
    ws.append(["", "Allow for scaffolding", "", None])
    ws.append(["Item No", "Work Description", "Unit", "Rate (LKR)"])

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        wb.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        items = extract_excel(tmp_path)
        # Only the 2 valid items should be extracted, noise must be ignored
        assert len(items) == 2
        assert items[0].item_code == "EW01"
        assert items[0].unit == "m³"
        assert items[0].rate == 1250.00
        assert items[1].item_code == "CT01"
        assert items[1].rate == 24500.00
    finally:
        tmp_path.unlink(missing_ok=True)

def test_compare_service_strict_master_items():
    from app.models import MasterItem

    # Two items with similar description but NO master item must NOT be grouped
    item1 = RateItem(
        id=1, source_file_id=1, province="Western", district="Colombo",
        year=2026, revision="First Half", item_code="A1",
        description="Brickwork 225mm mortar", unit="m³", rate=1000.0, master_item_id=None
    )
    item2 = RateItem(
        id=2, source_file_id=2, province="Central", district="Kandy",
        year=2026, revision="First Half", item_code="B1",
        description="Brickwork 225mm cement mortar", unit="m³", rate=1200.0, master_item_id=None
    )

    resp = CompareService.build_comparison([item1, item2])
    # Must produce 2 separate unmapped groups, not 1 merged group
    assert resp.total_groups == 2
    assert resp.groups[0].key.startswith("unmapped_")
    assert resp.groups[1].key.startswith("unmapped_")

    # When items share an approved MasterItem, they ARE grouped
    m = MasterItem(id=99, master_code="M-BK01", canonical_description="Brickwork 225mm", canonical_unit="m³")
    item1.master_item_id = 99
    item1.master_item = m
    item2.master_item_id = 99
    item2.master_item = m

    resp2 = CompareService.build_comparison([item1, item2])
    assert resp2.total_groups == 1
    assert resp2.groups[0].key == "master_99"
    assert len(resp2.groups[0].items) == 2

