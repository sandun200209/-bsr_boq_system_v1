from __future__ import annotations
from pathlib import Path
import docx
from .base import ExtractedItem, parse_numeric_rate, HEADER_ALIASES
from ..services.validation_service import (
    ValidationService,
    detect_category_from_code,
    clean_text,
)

def extract_docx(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Extracts rate items from Microsoft Word DOCX documents.
    Prioritizes structured tables and falls back to structured paragraph sequences.
    """
    items: list[ExtractedItem] = []
    existing_codes: set[str] = set()

    doc = docx.Document(file_path)
    current_category = category_hint
    current_cat_code = None

    # 1. Process Tables First
    for t_idx, table in enumerate(doc.tables, start=1):
        header_map: dict[str, int] | None = None

        for row_idx, row in enumerate(table.rows, start=1):
            cells = [clean_text(c.text) for c in row.cells]
            if not any(cells):
                continue

            # Identify header row
            if header_map is None:
                candidate: dict[str, int] = {}
                for col_idx, cell_text in enumerate(cells):
                    lower = cell_text.lower()
                    for key, aliases in HEADER_ALIASES.items():
                        if key not in candidate and any(a in lower for a in aliases):
                            candidate[key] = col_idx
                if len(candidate) >= 3 and "rate" in candidate:
                    header_map = candidate
                    continue
                # If first row is a title banner
                if len(cells) == 1 and len(cells[0]) > 3:
                    current_category = cells[0]
                continue

            # Parse data row
            code_col = header_map.get("code")
            desc_col = header_map.get("description")
            unit_col = header_map.get("unit")
            rate_col = header_map.get("rate")

            code_raw = cells[code_col] if code_col is not None and code_col < len(cells) else ""
            desc_raw = cells[desc_col] if desc_col is not None and desc_col < len(cells) else ""
            unit_raw = cells[unit_col] if unit_col is not None and unit_col < len(cells) else ""
            rate_raw = cells[rate_col] if rate_col is not None and rate_col < len(cells) else ""

            code_clean = clean_text(code_raw)
            desc_clean = clean_text(desc_raw)
            unit_clean = clean_text(unit_raw)
            parsed_rate = parse_numeric_rate(rate_raw)

            # Check if this row is a category header
            if not code_clean and parsed_rate is None and len(desc_clean) > 3:
                current_category = desc_clean
                current_cat_code = None
                continue

            if not code_clean and not desc_clean and parsed_rate is None:
                continue

            cat_code, cat_name = detect_category_from_code(code_clean, current_category)
            if not current_category and cat_name:
                current_category = cat_name
            if cat_code:
                current_cat_code = cat_code

            status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                code=code_clean,
                description=desc_clean,
                unit=unit_clean,
                rate=parsed_rate,
                existing_codes=existing_codes,
            )

            if code_clean:
                existing_codes.add(code_clean)

            items.append(
                ExtractedItem(
                    item_code=code_clean or None,
                    description=desc_clean or None,
                    unit=norm_unit or unit_clean or None,
                    rate=parsed_rate,
                    category_code=current_cat_code,
                    category_name=current_category,
                    source_sheet=f"Table {t_idx}",
                    source_row=row_idx,
                    source_cell=f"R{row_idx}C1:R{row_idx}C{len(cells)}",
                    raw_text=" | ".join(cells),
                    confidence_score=conf,
                    validation_status=status,
                    validation_notes=notes,
                )
            )

    # 2. If no tables or few items, scan paragraphs for tab-delimited text
    if not items:
        for p_idx, para in enumerate(doc.paragraphs, start=1):
            text = clean_text(para.text)
            if not text:
                continue
            parts = [clean_text(part) for part in para.text.split("\t") if clean_text(part)]
            if len(parts) >= 3:
                parsed_rate = parse_numeric_rate(parts[-1])
                if parsed_rate is not None:
                    code_val = parts[0]
                    desc_val = parts[1] if len(parts) >= 4 else parts[0]
                    unit_val = parts[2] if len(parts) >= 4 else parts[1]

                    cat_code, cat_name = detect_category_from_code(code_val, current_category)
                    status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                        code=code_val,
                        description=desc_val,
                        unit=unit_val,
                        rate=parsed_rate,
                        existing_codes=existing_codes,
                    )
                    if code_val:
                        existing_codes.add(code_val)

                    items.append(
                        ExtractedItem(
                            item_code=code_val,
                            description=desc_val,
                            unit=norm_unit or unit_val,
                            rate=parsed_rate,
                            category_code=cat_code,
                            category_name=current_category,
                            source_sheet="Paragraphs",
                            source_row=p_idx,
                            raw_text=text,
                            confidence_score=conf,
                            validation_status=status,
                            validation_notes=notes,
                        )
                    )

    return items
