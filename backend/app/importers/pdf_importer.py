from __future__ import annotations
import re
from pathlib import Path
from typing import Any
import fitz  # PyMuPDF
import pdfplumber
from .base import ExtractedItem, parse_numeric_rate
from ..services.validation_service import (
    ValidationService,
    detect_category_from_code,
    clean_text,
    normalize_unit,
    CODE_PATTERN,
    is_non_rate_noise,
)

# Pattern for codes at line start
LINE_CODE_RE = re.compile(r"^\s*([A-Z]{1,6}-?\d{1,4}[A-Za-z]?|\d{2,5})\b")

# Regex to match isolated rate at end of row or line
END_RATE_RE = re.compile(r"([0-9][0-9,]*(?:\.\d{1,2})?)\s*$")

# Regex to detect unit followed by rate: e.g. "m3 596.00" or "m³ 1,250.00" or "nr 450.00"
UNIT_THEN_RATE_RE = re.compile(
    r"\b(m3|m2|m|nr|no|nos|kg|ton|ltr|l|hr|day|set|pair|point|item|sq|cu\.m|sq\.m)\s+([0-9][0-9,]*(?:\.\d{1,2})?)\s*$",
    re.I
)

def fix_split_units(text: str) -> str:
    """
    Normalizes multi-line and split units like:
    'm \n 3' -> 'm³'
    'm \n 2' -> 'm²'
    'm + 3' -> 'm³'
    'm + 2' -> 'm²'
    """
    # Fix m followed by 3 or 2
    t = re.sub(r"\bm\s*[\+\^]?\s*3\b", "m³", text, flags=re.I)
    t = re.sub(r"\bm\s*[\+\^]?\s*2\b", "m²", t, flags=re.I)
    t = re.sub(r"\bcu\.?\s*m\b", "m³", t, flags=re.I)
    t = re.sub(r"\bsq\.?\s*m\b", "m²", t, flags=re.I)
    return t

class OCRRequiredException(Exception):
    """Raised when PDF contains no readable text layer (scanned document)."""
    pass

def check_pdf_has_usable_text(doc: fitz.Document) -> bool:
    """Checks if the document has a usable digital text layer across sample pages."""
    sample_pages = min(len(doc), 5)
    total_chars = 0
    for page_num in range(sample_pages):
        page_text = doc[page_num].get_text()
        total_chars += len(page_text.strip())
    # If 5 pages yield fewer than 60 total characters, it's a scanned PDF
    return total_chars >= 60

def extract_pdf_tables_pdfplumber(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Attempts table extraction using pdfplumber's table detection heuristics.
    Detects dynamic column layouts and handles 'Deleted'/'Omitted' items accurately.
    """
    items: list[ExtractedItem] = []
    existing_codes: set[str] = set()

    with pdfplumber.open(file_path) as pdf:
        current_category = category_hint
        current_cat_code = None

        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table:
                    continue

                code_col = 0
                desc_col = 1
                unit_col = 2
                rate_col = 3
                has_rate_header = False

                for row in table:
                    if not row or not any(row):
                        continue

                    cells = [clean_text(c) if c is not None else "" for c in row]
                    if not any(cells):
                        continue

                    row_joined = " ".join(cells).lower()

                    # Detect rate table header row
                    if ("description" in row_joined or "item" in row_joined) and ("rate" in row_joined or "price" in row_joined or "amount" in row_joined or "cost" in row_joined):
                        has_rate_header = True
                        for ci, c in enumerate(cells):
                            cl = c.lower()
                            if "code" in cl or cl in ("no", "no.", "item no", "item code"):
                                code_col = ci
                            elif "desc" in cl:
                                desc_col = ci
                            elif "unit" in cl:
                                unit_col = ci
                            elif "rate" in cl or "price" in cl or "amount" in cl or "cost" in cl:
                                rate_col = ci
                        continue

                    # Filter out other repeated headers
                    if "description" in row_joined and ("unit" in row_joined or "code" in row_joined):
                        continue

                    # Check for category header row
                    non_empty = [c for c in cells if c]
                    if len(non_empty) == 1 and len(non_empty[0]) > 3:
                        val = non_empty[0]
                        if not re.search(r"\d{3,}", val):
                            current_category = val
                            current_cat_code = None
                        continue

                    # Skip non-rate tables (e.g. timber tables, percentage lifts)
                    if not has_rate_header and len(cells) != 4:
                        continue

                    if len(cells) <= max(code_col, desc_col, rate_col):
                        continue

                    code_val = cells[code_col] if code_col < len(cells) else ""
                    desc_val = cells[desc_col] if desc_col < len(cells) else ""
                    unit_val = cells[unit_col] if unit_col < len(cells) else ""
                    rate_raw = cells[rate_col] if rate_col < len(cells) else ""

                    if not code_val and not desc_val and not rate_raw:
                        continue

                    # Check for category banner line in table
                    if not code_val and desc_val and not rate_raw and not unit_val:
                        if len(desc_val) > 3 and not re.search(r"\d{3,}", desc_val):
                            current_category = desc_val
                            current_cat_code = None
                        continue

                    # Fix split units
                    if unit_val:
                        unit_val = fix_split_units(unit_val)
                    if desc_val:
                        desc_val = fix_split_units(desc_val)

                    rate_val = parse_numeric_rate(rate_raw)

                    if is_non_rate_noise(desc_val, code=code_val, rate=rate_val, unit=unit_val):
                        if len(desc_val or "") > 3 and not code_val and rate_val is None and not unit_val:
                            current_category = desc_val
                        continue

                    # Skip non-code rows that have no rate (e.g. notes or timber classifications)
                    if code_val and not CODE_PATTERN.match(code_val) and rate_val is None:
                        continue
                    if not code_val and rate_val is None:
                        continue

                    is_deleted = any(d in rate_raw.lower() for d in ("delete", "omit", "cancelled", "n/a"))
                    if is_deleted:
                        rate_val = None

                    cat_code, cat_name = detect_category_from_code(code_val, current_category)
                    if not current_category and cat_name:
                        current_category = cat_name
                    if cat_code:
                        current_cat_code = cat_code

                    if is_deleted:
                        status = "NEEDS_REVIEW"
                        conf = 0.85
                        notes = f"Item marked as '{rate_raw}' in source document"
                        norm_unit = normalize_unit(unit_val) if unit_val else None
                    else:
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
                            item_code=code_val or None,
                            description=desc_val or None,
                            unit=norm_unit or unit_val or None,
                            rate=rate_val,
                            category_code=current_cat_code,
                            category_name=current_category,
                            source_page=page_idx,
                            source_row=len(items) + 1,
                            raw_text=" | ".join(filter(None, [code_val, desc_val, unit_val, rate_raw])),
                            confidence_score=conf,
                            validation_status=status,
                            validation_notes=notes,
                        )
                    )

    return items

def extract_pdf_native_text(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    High-performance native PyMuPDF stream parser.
    Reconstructs multi-line descriptions and disconnected units/rates.
    """
    items: list[ExtractedItem] = []
    existing_codes: set[str] = set()

    doc = fitz.open(file_path)
    if not check_pdf_has_usable_text(doc):
        doc.close()
        raise OCRRequiredException("Scanned PDF detected: No digital text layer found.")

    current_category = category_hint
    current_cat_code = None

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if not text:
            continue

        raw_lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]
        
        # State machine to accumulate multi-line items
        accum_code: str | None = None
        accum_desc_parts: list[str] = []
        accum_unit: str | None = None
        accum_rate: float | None = None

        def flush_item():
            nonlocal accum_code, accum_desc_parts, accum_unit, accum_rate, current_category, current_cat_code
            if not accum_desc_parts and not accum_code and accum_rate is None:
                return

            full_desc = " ".join(accum_desc_parts)
            full_desc = fix_split_units(full_desc)

            if is_non_rate_noise(full_desc, code=accum_code, rate=accum_rate, unit=accum_unit):
                if len(full_desc) > 3 and not accum_code and accum_rate is None and not accum_unit:
                    current_category = full_desc
                accum_code = None
                accum_desc_parts = []
                accum_unit = None
                accum_rate = None
                return

            # Check if there is an embedded unit in the description end or accum_unit
            if not accum_unit:
                unit_match = re.search(r"\b(m³|m²|m|nr|no|nos|kg|ton|ltr|L|hr|day|set|pair|point|item)\b", full_desc, re.I)
                if unit_match:
                    accum_unit = unit_match.group(1)

            cat_code, cat_name = detect_category_from_code(accum_code, current_category)
            if not current_category and cat_name:
                current_category = cat_name
            if cat_code:
                current_cat_code = cat_code

            status, conf, notes, norm_unit = ValidationService.validate_rate_item(
                code=accum_code,
                description=full_desc,
                unit=accum_unit,
                rate=accum_rate,
                existing_codes=existing_codes,
            )

            if accum_code:
                existing_codes.add(accum_code)

            items.append(
                ExtractedItem(
                    item_code=accum_code,
                    description=full_desc or None,
                    unit=norm_unit or accum_unit,
                    rate=accum_rate,
                    category_code=current_cat_code,
                    category_name=current_category,
                    source_page=page_num + 1,
                    source_row=len(items) + 1,
                    raw_text=f"{accum_code or ''} {full_desc} {accum_unit or ''} {accum_rate or ''}".strip(),
                    confidence_score=conf,
                    validation_status=status,
                    validation_notes=notes,
                )
            )

            accum_code = None
            accum_desc_parts = []
            accum_unit = None
            accum_rate = None

        for line in raw_lines:
            # Skip page headers / footers
            lower = line.lower()
            if any(lower.startswith(skip) for skip in ("page ", "building schedule", "schedule of rates", "provisional sum", "continued")):
                continue

            # Check for isolated unit line (e.g. 'm', '3')
            if line in ("3", "2") and accum_desc_parts and accum_desc_parts[-1] == "m":
                accum_desc_parts.pop()
                accum_unit = "m³" if line == "3" else "m²"
                continue
            if line.lower() in ("m3", "m2", "nr", "kg", "ltr", "item"):
                accum_unit = normalize_unit(line)
                continue

            # Check if line contains a standard rate at the very end
            rate_match = END_RATE_RE.search(line)
            unit_rate_match = UNIT_THEN_RATE_RE.search(line)

            # Check if line starts with a valid BSR code (e.g., DM01, BK05c, CT01, A-01)
            code_match = LINE_CODE_RE.match(line)
            if code_match:
                # If we were already accumulating an item that has rate or description, flush it
                if accum_rate is not None or len(accum_desc_parts) >= 2:
                    flush_item()

                matched_code = code_match.group(1)
                accum_code = matched_code
                rest_of_line = line[len(code_match.group(0)):].strip()

                rate_match_rest = END_RATE_RE.search(rest_of_line) if rest_of_line else None
                unit_rate_match_rest = UNIT_THEN_RATE_RE.search(rest_of_line) if rest_of_line else None

                if unit_rate_match_rest:
                    accum_unit = normalize_unit(unit_rate_match_rest.group(1))
                    accum_rate = parse_numeric_rate(unit_rate_match_rest.group(2))
                    rest_desc = rest_of_line[:unit_rate_match_rest.start()].strip()
                    if rest_desc:
                        accum_desc_parts.append(rest_desc)
                elif rate_match_rest:
                    accum_rate = parse_numeric_rate(rate_match_rest.group(1))
                    rest_desc = rest_of_line[:rate_match_rest.start()].strip()
                    if rest_desc:
                        accum_desc_parts.append(rest_desc)
                else:
                    if rest_of_line:
                        accum_desc_parts.append(rest_of_line)
                continue

            # If not code line, check if it's the rate/unit line closing previous item
            if unit_rate_match:
                accum_unit = normalize_unit(unit_rate_match.group(1))
                accum_rate = parse_numeric_rate(unit_rate_match.group(2))
                prefix_desc = line[:unit_rate_match.start()].strip()
                if prefix_desc:
                    accum_desc_parts.append(prefix_desc)
                flush_item()
                continue
            elif rate_match and (accum_code or accum_desc_parts):
                accum_rate = parse_numeric_rate(rate_match.group(1))
                prefix_desc = line[:rate_match.start()].strip()
                if prefix_desc:
                    accum_desc_parts.append(prefix_desc)
                flush_item()
                continue

            # Check for section / category heading (all-caps or "Section...")
            if line.isupper() and len(line) > 3 and not rate_match:
                if accum_code or accum_desc_parts:
                    flush_item()
                current_category = line
                current_cat_code = None
                continue

            # Otherwise, it's an ongoing multi-line description
            accum_desc_parts.append(line)

        # Flush any remaining item on page end
        flush_item()

    doc.close()
    return items

def extract_pdf(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Main PDF extraction pipeline:
    1. First tries pdfplumber table extraction (standard for BSR rate books with grid lines).
    2. If table extraction yields >= 5 items, returns table items directly.
    3. If table extraction yields < 5 items, falls back to PyMuPDF native text stream parser.
    4. If scanned (no text layer), raises OCRRequiredException.
    """
    doc = fitz.open(file_path)
    has_text = check_pdf_has_usable_text(doc)
    doc.close()
    if not has_text:
        raise OCRRequiredException("Scanned PDF detected: No digital text layer found.")

    # 1. Structured table extraction first (most accurate for grid-based BSR documents)
    try:
        table_items = extract_pdf_tables_pdfplumber(file_path, category_hint=category_hint)
        if len(table_items) >= 5:
            return table_items
    except Exception:
        pass

    # 2. Fallback to native text stream parser for unstructured/plain-text PDFs
    try:
        items = extract_pdf_native_text(file_path, category_hint=category_hint)
        if items:
            return items
    except OCRRequiredException:
        raise
    except Exception:
        pass

    return table_items if "table_items" in locals() and table_items else []
