from __future__ import annotations
import csv
import io
from pathlib import Path
from .base import ExtractedItem, parse_numeric_rate, HEADER_ALIASES
from ..services.validation_service import (
    ValidationService,
    detect_category_from_code,
    clean_text,
    is_non_rate_noise,
)

def detect_delimiter(sample: str, default: str = ",") -> str:
    """Detects delimiter from common CSV/TSV separators."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except Exception:
        # Fallback heuristic: count frequencies
        counts = {d: sample.count(d) for d in ("\t", ",", ";", "|")}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else default

def extract_csv(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Extracts rate items from CSV or TSV files with automatic delimiter and header detection.
    """
    items: list[ExtractedItem] = []
    existing_codes: set[str] = set()

    # Read sample to detect encoding & delimiter
    raw_bytes = file_path.read_bytes()
    encoding = "utf-8"
    try:
        sample_text = raw_bytes[:8192].decode("utf-8")
    except UnicodeDecodeError:
        encoding = "latin-1"
        sample_text = raw_bytes[:8192].decode("latin-1")

    delimiter = detect_delimiter(sample_text, default="\t" if file_path.suffix.lower() == ".tsv" else ",")

    current_category = category_hint
    current_cat_code = None
    header_map: dict[str, int] | None = None

    with file_path.open("r", encoding=encoding, errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row_idx, row in enumerate(reader, start=1):
            if not row or not any(row):
                continue

            cleaned_row = [clean_text(c) for c in row]

            # Detect header
            if header_map is None:
                candidate: dict[str, int] = {}
                for col_idx, cell_text in enumerate(cleaned_row):
                    lower = cell_text.lower()
                    for key, aliases in HEADER_ALIASES.items():
                        if key not in candidate and any(a in lower for a in aliases):
                            candidate[key] = col_idx
                if len(candidate) >= 3 and "rate" in candidate:
                    header_map = candidate
                    continue
                # If first row is a title banner
                if len(cleaned_row) == 1 and len(cleaned_row[0]) > 3:
                    current_category = cleaned_row[0]
                continue

            code_col = header_map.get("code")
            desc_col = header_map.get("description")
            unit_col = header_map.get("unit")
            rate_col = header_map.get("rate")
            cesmm_no_col = header_map.get("cesmm_section_no")
            cesmm_code_col = header_map.get("cesmm_section_code")

            raw_code = cleaned_row[code_col] if code_col is not None and code_col < len(cleaned_row) else ""
            raw_desc = cleaned_row[desc_col] if desc_col is not None and desc_col < len(cleaned_row) else ""
            raw_unit = cleaned_row[unit_col] if unit_col is not None and unit_col < len(cleaned_row) else ""
            raw_rate = cleaned_row[rate_col] if rate_col is not None and rate_col < len(cleaned_row) else ""
            raw_cesmm_no = cleaned_row[cesmm_no_col] if cesmm_no_col is not None and cesmm_no_col < len(cleaned_row) else ""
            raw_cesmm_code = cleaned_row[cesmm_code_col] if cesmm_code_col is not None and cesmm_code_col < len(cleaned_row) else ""

            code_clean = clean_text(raw_code)
            desc_clean = clean_text(raw_desc)
            unit_clean = clean_text(raw_unit)
            cesmm_no_clean = clean_text(raw_cesmm_no) or None
            cesmm_code_clean = clean_text(raw_cesmm_code) or None
            parsed_rate = parse_numeric_rate(raw_rate)

            # Check for non-rate noise
            if is_non_rate_noise(desc_clean, code=code_clean, rate=parsed_rate, unit=unit_clean):
                if len(desc_clean) > 3 and not code_clean and parsed_rate is None:
                    current_category = desc_clean
                continue

            # Check for category header row
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
                    source_sheet="CSV",
                    source_row=row_idx,
                    source_cell=f"R{row_idx}",
                    raw_text=delimiter.join(cleaned_row),
                    confidence_score=conf,
                    validation_status=status,
                    validation_notes=notes,
                    cesmm_section_no=cesmm_no_clean,
                    cesmm_section_code=cesmm_code_clean,
                )
            )

    return items
