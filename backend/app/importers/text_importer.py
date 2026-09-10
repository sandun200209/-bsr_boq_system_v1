from __future__ import annotations
import re
from pathlib import Path
from .base import ExtractedItem, parse_numeric_rate
from ..services.validation_service import (
    ValidationService,
    detect_category_from_code,
    clean_text,
    normalize_unit,
)

# Common regex patterns in plain text rate listings
TXT_LINE_PATTERN = re.compile(
    r"^\s*([A-Z0-9\-_]{2,10})\s+(.+?)\s+(m3|m2|m|cu\.m|sq\.m|nr|no|nos|kg|ton|ltr|L|hr|day|set|pair|point|item)\s+([0-9][0-9,]*(?:\.\d{1,4})?)\s*$",
    re.I
)

def extract_text(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Extracts rate items from plain text files using pattern-matching heuristics.
    """
    items: list[ExtractedItem] = []
    existing_codes: set[str] = set()

    raw_bytes = file_path.read_bytes()
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1", errors="replace")

    current_category = category_hint
    current_cat_code = None

    lines = content.splitlines()
    for row_idx, line in enumerate(lines, start=1):
        cleaned_line = clean_text(line)
        if not cleaned_line:
            continue

        # Check for category header (e.g. [EARTH WORK] or SECTION: DEMOLITION)
        if (cleaned_line.startswith("[") and cleaned_line.endswith("]")) or (cleaned_line.isupper() and len(cleaned_line) > 3 and not re.search(r"\d+\.\d+", cleaned_line)):
            current_category = cleaned_line.strip("[]: ")
            current_cat_code = None
            continue

        # Try regex match
        m = TXT_LINE_PATTERN.match(cleaned_line)
        if m:
            code_val = m.group(1).strip()
            desc_val = m.group(2).strip()
            unit_val = m.group(3).strip()
            rate_val = parse_numeric_rate(m.group(4))

            cat_code, cat_name = detect_category_from_code(code_val, current_category)
            if not current_category and cat_name:
                current_category = cat_name
            if cat_code:
                current_cat_code = cat_code

            status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                code=code_val,
                description=desc_val,
                unit=unit_val,
                rate=rate_val,
                existing_codes=existing_codes,
            )

            if code_val:
                existing_codes.add(code_val)

            items.append(
                ExtractedItem(
                    item_code=code_val,
                    description=desc_val,
                    unit=norm_unit or unit_val,
                    rate=rate_val,
                    category_code=current_cat_code,
                    category_name=current_category,
                    source_sheet="TXT",
                    source_row=row_idx,
                    source_cell=f"Line {row_idx}",
                    raw_text=cleaned_line,
                    confidence_score=conf,
                    validation_status=status,
                    validation_notes=notes,
                )
            )
            continue

        # Fallback tab-separated check
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) >= 4:
            rate_val = parse_numeric_rate(parts[-1])
            if rate_val is not None:
                code_val = parts[0]
                desc_val = parts[1]
                unit_val = parts[2]

                cat_code, cat_name = detect_category_from_code(code_val, current_category)
                status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                    code=code_val,
                    description=desc_val,
                    unit=unit_val,
                    rate=rate_val,
                    existing_codes=existing_codes,
                )
                if code_val:
                    existing_codes.add(code_val)

                items.append(
                    ExtractedItem(
                        item_code=code_val,
                        description=desc_val,
                        unit=norm_unit or unit_val,
                        rate=rate_val,
                        category_code=cat_code,
                        category_name=current_category,
                        source_sheet="TXT",
                        source_row=row_idx,
                        source_cell=f"Line {row_idx}",
                        raw_text=cleaned_line,
                        confidence_score=conf,
                        validation_status=status,
                        validation_notes=notes,
                    )
                )

    return items
