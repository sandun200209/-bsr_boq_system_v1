from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Any

RATE_REGEX = re.compile(r"^[\s\u00a0]*([0-9][0-9,]*(?:\.\d{1,4})?)[\s\u00a0]*$")

@dataclass
class ExtractedItem:
    item_code: str | None
    description: str | None
    unit: str | None
    rate: float | None
    category_code: str | None = None
    category_name: str | None = None
    source_page: int | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_cell: str | None = None
    raw_text: str | None = None
    confidence_score: float = 1.0
    validation_status: str = "VALID"
    validation_notes: str | None = None
    sheet_year: int | None = None
    sheet_revision: str | None = None
    sheet_vat_basis: str | None = None
    sheet_dataset_type: str | None = None
    cesmm_section_no: str | None = None
    cesmm_section_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def parse_numeric_rate(value: Any) -> float | None:
    """Safely extracts a numeric rate from strings, ints, floats, or formulas."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("\u00a0", " ").strip()
    match = RATE_REGEX.match(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None

HEADER_ALIASES = {
    "code": ("code", "item", "item no", "item no.", "item code", "item number", "item_no", "no", "no.", "sr no", "serial no", "s/n"),
    "description": ("description", "discription", "item description", "item discription", "desc", "details", "work description", "specification", "particulars", "item particulars", "description of work"),
    "unit": ("unit", "uom", "unit of measure", "unit of measurement", "units", "unit."),
    "rate": ("rate", "basic rate", "rate (lkr)", "rate lkr", "price", "unit rate", "current rate", "rate (rs.)", "amount", "approved rate"),
    "cesmm_section_no": ("cesmm_section_no", "cesmm_section", "cesmm_no", "cesmm no", "cesmm section no", "cesmm", "cesmm_sl", "cesmm section"),
    "cesmm_section_code": ("cesmm_section_code", "cesmm_code", "cesmm code", "cesmm section code"),
}
