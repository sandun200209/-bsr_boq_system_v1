from __future__ import annotations
from pathlib import Path
from typing import Generator
import re
import openpyxl
from .base import ExtractedItem, parse_numeric_rate, HEADER_ALIASES
from ..services.validation_service import (
    ValidationService,
    detect_category_from_code,
    clean_text,
    is_non_rate_noise,
)

def find_header_mapping(row_values: list[str], target_year: int | None = None) -> dict[str, int]:
    mapping: dict[str, int] = {}
    normalized = [clean_text(v).lower() for v in row_values]

    # Map code, description, unit
    for col_idx, text in enumerate(normalized):
        if not text:
            continue
        for key in ("code", "description", "unit"):
            if key not in mapping:
                aliases = HEADER_ALIASES[key]
                if any(alias == text or (len(alias) > 3 and alias in text) for alias in aliases):
                    mapping[key] = col_idx
                    break

    # Score rate candidate columns
    rate_candidates: list[tuple[int, int]] = []  # (score, col_idx)
    rate_aliases = HEADER_ALIASES["rate"]

    for col_idx, text in enumerate(normalized):
        if not text:
            continue
        if any(alias == text or (len(alias) > 3 and alias in text) for alias in rate_aliases):
            score = 10
            # Target year bonus
            if target_year and str(target_year) in text:
                score += 50
            elif any(str(y) in text for y in (2025, 2026)):
                score += 40

            # Keywords bonus
            if "market price" in text:
                score += 25
            elif "basic rate" in text or "rate" in text:
                score += 15

            # Heavy penalty for older years (e.g. 2022 Market Price)
            old_years = [y for y in range(2015, 2025) if y != target_year]
            if any(str(y) in text for y in old_years):
                score -= 100
            if "old" in text or "previous" in text:
                score -= 80

            rate_candidates.append((score, col_idx))

    if rate_candidates:
        rate_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_col = rate_candidates[0]
        if best_score > 0:
            mapping["rate"] = best_col

    return mapping

def extract_excel(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Extracts BSR rate items from XLSX or XLSM workbooks using openpyxl with data_only=True
    to capture calculated values while ignoring formatting ranges, totals, and notes.
    """
    items: list[ExtractedItem] = []

    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)

    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        current_category_name = category_hint
        current_category_code = None
        header_map: dict[str, int] | None = None
        existing_codes_in_sheet: set[str] = set()

        sheet_name_clean = sheet_name.strip()
        sheet_name_lower = sheet_name_clean.lower()

        # 1. Determine sheet-specific VAT basis
        sheet_vat_basis: str | None = None
        if "without vat" in sheet_name_lower or "without_vat" in sheet_name_lower or "w/o vat" in sheet_name_lower or " wv" in sheet_name_lower:
            sheet_vat_basis = "Without VAT"
        elif "with vat" in sheet_name_lower or "with_vat" in sheet_name_lower or "w/ vat" in sheet_name_lower:
            sheet_vat_basis = "With VAT"

        # 2. Determine sheet-specific Dataset Type
        sheet_dataset_type: str | None = None
        if "material" in sheet_name_lower:
            sheet_dataset_type = "Basic Material Rates"
        elif "lab" in sheet_name_lower or "labour" in sheet_name_lower:
            sheet_dataset_type = "Labour Rates"
        elif "transport" in sheet_name_lower or sheet_name_lower.startswith("bad") or sheet_name_lower.startswith("mon"):
            sheet_dataset_type = "Transport Rates"
        elif "rate book" in sheet_name_lower:
            sheet_dataset_type = "BSR Rate Book"

        # 3. Detect sheet-specific Year and Revision
        sheet_year: int | None = None
        sheet_revision: str | None = None
        m_name_year = re.search(r'\b(202[0-9])\b', sheet_name_clean)
        if m_name_year:
            sheet_year = int(m_name_year.group(1))

        rows_iter = sheet.iter_rows(values_only=True)
        row_idx = 0

        for row in rows_iter:
            row_idx += 1
            if not row or not any(row):
                continue

            str_row = [str(c) if c is not None else "" for c in row]

            # Check top banner rows for year & revision
            if row_idx <= 4:
                row_combined = " ".join(str_row)
                m_row_year = re.search(r'\b(202[0-9])\b', row_combined)
                if m_row_year and sheet_year is None:
                    sheet_year = int(m_row_year.group(1))
                if re.search(r'first\s*half|1st\s*half', row_combined, re.I) and sheet_revision is None:
                    sheet_revision = "First Half"
                elif re.search(r'second\s*half|2nd\s*half', row_combined, re.I) and sheet_revision is None:
                    sheet_revision = "Second Half"

            # Try to identify header row within the first 25 non-empty rows
            if header_map is None:
                candidate = find_header_mapping(str_row, target_year=sheet_year)
                if len(candidate) >= 3 and "rate" in candidate:
                    header_map = candidate
                    continue
                # If we haven't found headers yet, this might be a category title row
                non_empty = [c for c in str_row if c.strip()]
                if len(non_empty) == 1 and len(non_empty[0]) > 3:
                    current_category_name = non_empty[0].strip()
                continue

            # We have identified the header row, process rows
            code_col = header_map.get("code")
            desc_col = header_map.get("description")
            unit_col = header_map.get("unit")
            rate_col = header_map.get("rate")

            raw_code = str_row[code_col] if code_col is not None and code_col < len(str_row) else ""
            raw_desc = str_row[desc_col] if desc_col is not None and desc_col < len(str_row) else ""
            raw_unit = str_row[unit_col] if unit_col is not None and unit_col < len(str_row) else ""
            raw_rate = row[rate_col] if rate_col is not None and rate_col < len(row) else None

            code_clean = clean_text(raw_code)
            desc_clean = clean_text(raw_desc)
            unit_clean = clean_text(raw_unit)
            parsed_rate = parse_numeric_rate(raw_rate)

            # Filter out Excel error formulas like #N/A, #VALUE!, #REF!
            if code_clean in ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?"):
                code_clean = ""
            if desc_clean in ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?"):
                desc_clean = ""
            if unit_clean in ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?"):
                unit_clean = ""

            # If code_clean is unusually long (> 40 chars), it is almost certainly a description or section heading
            if len(code_clean) > 40:
                if not desc_clean:
                    desc_clean = code_clean
                    code_clean = ""
                elif parsed_rate is None and not unit_clean:
                    current_category_name = code_clean[:400]
                    current_category_code = None
                    continue

            code_lower = code_clean.lower()
            desc_lower = desc_clean.lower()
            unit_lower = unit_clean.lower()

            # 1. Skip repeated table headers inside the sheet
            if (
                code_lower in ("no", "no.", "code", "item", "item no", "item no.", "item code", "s/n", "sr no", "item_no")
                or desc_lower in ("description", "discription", "item description", "particulars", "details", "work description")
                or unit_lower in ("unit", "uom", "units", "unit.")
            ) and parsed_rate is None:
                continue

            # 2. Automatically ignore obvious headings, notes, and non-rate calculation text
            if is_non_rate_noise(desc_clean, code=code_clean, rate=parsed_rate, unit=unit_clean):
                if len(desc_clean) > 3 and not code_clean and parsed_rate is None and not unit_clean:
                    current_category_name = desc_clean[:400]
                    current_category_code = None
                continue

            # 3. If row has NO rate and NO code, it is not a rate item
            if parsed_rate is None and not code_clean:
                if len(desc_clean) > 3 and not unit_clean:
                    current_category_name = desc_clean[:400]
                    current_category_code = None
                continue

            # Check if this is a section / category banner row
            non_empty_cells = [c for c in str_row if c.strip()]
            if parsed_rate is None and (not unit_clean) and len(desc_clean) > 3 and len(non_empty_cells) <= 2:
                current_category_name = desc_clean[:400]
                current_category_code = None
                continue

            # Ignore totals, headers repeated on pagination, and notes
            if any(desc_lower.startswith(prefix) for prefix in ("total", "sub total", "grand total", "page", "note:", "continued")):
                continue

            # If all code, description, and rate are blank, skip
            if not code_clean and not desc_clean and parsed_rate is None:
                continue

            # Auto-detect category code from item code
            cat_code, cat_name = detect_category_from_code(code_clean, current_category_name)
            if not current_category_name and cat_name:
                current_category_name = cat_name
            if cat_code:
                current_category_code = cat_code

            # Validate
            status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                code=code_clean,
                description=desc_clean,
                unit=unit_clean,
                rate=parsed_rate,
                existing_codes=existing_codes_in_sheet,
            )

            if code_clean:
                existing_codes_in_sheet.add(code_clean)

            cell_ref = f"Row {row_idx}"
            if code_col is not None and rate_col is not None:
                cell_ref = f"{openpyxl.utils.get_column_letter(code_col+1)}{row_idx}:{openpyxl.utils.get_column_letter(rate_col+1)}{row_idx}"

            items.append(
                ExtractedItem(
                    item_code=code_clean[:200] if code_clean else None,
                    description=desc_clean or None,
                    unit=(norm_unit or unit_clean or "")[:80] or None,
                    rate=parsed_rate,
                    category_code=current_category_code[:200] if current_category_code else None,
                    category_name=current_category_name[:400] if current_category_name else None,
                    source_sheet=sheet_name[:200],
                    source_row=row_idx,
                    source_cell=cell_ref[:200],
                    raw_text=f"{raw_code} | {raw_desc} | {raw_unit} | {raw_rate}",
                    confidence_score=conf,
                    validation_status=status,
                    validation_notes=notes,
                    sheet_year=sheet_year,
                    sheet_revision=sheet_revision,
                    sheet_vat_basis=sheet_vat_basis,
                    sheet_dataset_type=sheet_dataset_type,
                )
            )

    wb.close()
    return items
