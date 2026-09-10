from __future__ import annotations
import re
from typing import Any

# Standard Sri Lankan BSR Category Prefixes
CATEGORY_PREFIX_MAP: dict[str, str] = {
    "DM": "Demolisher",
    "EW": "Earth Work",
    "BK": "Brick Layer",
    "CT": "Concreter",
    "FW": "Form Work",
    "RF": "Steel Rates",
    "RR": "R R Masonry",
    "CB": "Cement Block Work",
    "PA": "Pavior",
    "PL": "Plasterer",
    "TN": "Tinker",
    "RO": "Roofer",
    "CP": "Carpenter & Joiner",
    "IR": "Iron Monger",
    "BF": "Brass Founder",
    "PT": "Painter",
    "PB": "Plumber",
    "MA": "Maintenance",
    "TG": "Tempered Glass",
    "GL": "Glazier",
    "CL": "Cladding Work",
    "GW": "General Work",
    "AL": "Maintenance Aluminum",
    "ALN": "Natural Anodized Aluminum",
    "ALB": "Bronze Anodized Aluminum",
    "ALP": "Powder Coated Aluminum",
    "EL": "Electrical",
    "DR": "Drainage",
    "RD": "Road Work",
    "WF": "Water Supply & Fittings",
}

# Unit mappings for Sri Lankan BSR
UNIT_MAP: dict[str, str] = {
    "m3": "m³", "m^3": "m³", "m³": "m³", "cu.m": "m³", "cum": "m³", "cu m": "m³", "m 3": "m³", "m+3": "m³",
    "m2": "m²", "m^2": "m²", "m²": "m²", "sq.m": "m²", "sqm": "m²", "sq m": "m²", "m 2": "m²", "m+2": "m²",
    "m": "m", "lin.m": "m", "lm": "m", "m.hr": "m.hr", "mhr": "m.hr",
    "nr": "nr", "no": "nr", "nos": "nr", "no.": "nr", "nos.": "nr", "number": "nr", "numbers": "nr", "item": "item",
    "each": "nr", "ea": "nr",
    "kg": "kg", "kg.hr": "kg.hr", "t": "ton", "ton": "ton", "tonne": "ton", "m.ton": "ton",
    "ltr": "L", "l": "L", "liter": "L", "litres": "L", "lit": "L",
    "hr": "hr", "hour": "hr", "hours": "hr",
    "day": "day", "days": "day", "day(8 hrs.)": "day", "day(8 hrs)": "day", "day(8hrs)": "day", "day (8 hrs.)": "day",
    "set": "set", "sets": "set", "pair": "pair", "pairs": "pair", "point": "point", "points": "point", "sq": "sq",
    "cube": "Cube", "cubes": "Cube",
    "sqr": "Sqr", "square": "Sqr", "squares": "Sqr",
    "l.ft": "L.ft", "lft": "L.ft", "lin.ft": "L.ft", "l.f": "L.ft", "lin.ft.": "L.ft",
    "sq.ft": "Sq.ft", "sqft": "Sq.ft", "sq.f": "Sq.ft", "sq.ft.": "Sq.ft",
    "cu.ft": "Cu.ft", "cuft": "Cu.ft", "cu.f": "Cu.ft", "cu.ft.": "Cu.ft",
    "p.s": "P.S", "ps": "P.S", "p.s.": "P.S", "provisional sum": "P.S",
    "month": "month", "wk": "week", "week": "week", "km": "km",
    "bag": "bag", "bags": "bag", "roll": "roll", "rolls": "roll",
    "drum": "drum", "can": "can", "tube": "tube", "pkt": "pkt", "packet": "pkt", "bundle": "bundle",
}

KNOWN_UNITS: set[str] = {
    "m³", "m²", "m", "m.hr", "nr", "item", "kg", "kg.hr", "ton", "L", "hr", "day",
    "set", "pair", "point", "sq", "Cube", "Sqr", "L.ft", "Sq.ft", "Cu.ft", "P.S",
    "month", "week", "km", "bag", "roll", "drum", "can", "tube", "pkt", "bundle"
}

# Regex for typical Sri Lankan BSR codes: e.g. "BK01", "D-15", "1104", "204", "101", "A.1", "123/A"
CODE_PATTERN = re.compile(r"^(?:[A-Za-z0-9]+(?:[\.\-\/][A-Za-z0-9]+)*|\d+)$")

NOISE_LINE_PATTERNS = [
    re.compile(r'^\s*(overhead\s*(?:and|&)\s*profit|o\s*&\s*p)\b', re.I),
    re.compile(r'^\s*allow\s+for\b', re.I),
    re.compile(r'^\s*data\s+for\b', re.I),
    re.compile(r'^\s*(sub[\s-]?total|grand\s*total|total\s*(?:cost|amount|price|value)?)\s*$', re.I),
    re.compile(r'^\s*(page\s*\d+(\s*of\s*\d+)?)\s*$', re.I),
    re.compile(r'^\s*(note|notes|n\.b\.)\s*[:\-]', re.I),
    re.compile(r'^\s*(continued\s*(?:on\s*next\s*page)?|carried\s*forward|brought\s*forward|b\/f|c\/f)\b', re.I),
    re.compile(r'^\s*(prepared\s*by|checked\s*by|approved\s*by|chief\s*engineer|executive\s*engineer)\b', re.I),
    re.compile(r'^\s*(contractor(?:[\']?s)?\s*profit)\b', re.I),
]

def is_non_rate_noise(
    description: str | None,
    code: str | None = None,
    rate: float | None = None,
    unit: str | None = None,
) -> bool:
    """
    Identifies obvious headings, footers, notes, repeated headers, or estimation sub-lines
    that should be completely skipped rather than sent to the Review Queue.
    """
    clean_desc = clean_text(description).lower() if description else ""
    clean_c = clean_text(code).lower() if code else ""

    # Blank row
    if not clean_desc and not clean_c and rate is None:
        return True

    # Repeated table headers (e.g. Item No | Description | Unit | Rate)
    header_words = {"item", "item no", "item no.", "code", "no", "no.", "description", "discription", "unit", "rate", "basic rate", "particulars", "details"}
    if rate is None:
        if clean_c in header_words or clean_desc in header_words:
            return True
        if clean_desc in ("description", "discription", "item particulars", "work description", "item description"):
            return True

    # If row has no rate AND no code: it is calculation text, notes, or section heading, NOT a rate item
    if rate is None and not clean_c:
        return True

    # Check non-rate calculation patterns (overhead & profit, allow for scaffolding, data for, etc.)
    if rate is None or rate <= 0:
        for pat in NOISE_LINE_PATTERNS:
            if pat.search(clean_desc):
                return True

    return False

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u00a0", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()

def normalize_unit(unit_str: str | None) -> str | None:
    if not unit_str:
        return None
    cleaned = clean_text(unit_str).lower().replace(" ", "").replace("+", "")
    if cleaned in UNIT_MAP:
        return UNIT_MAP[cleaned]
    # Check with original spaces preserved
    base_clean = clean_text(unit_str).lower()
    if base_clean in UNIT_MAP:
        return UNIT_MAP[base_clean]
    return clean_text(unit_str)

def detect_category_from_code(code: str | None, category_hint: str | None = None) -> tuple[str | None, str | None]:
    """Returns (category_code, category_name)"""
    if not code:
        return None, category_hint
    code_upper = code.strip().upper()
    # Try 3-letter, 2-letter, or prefix match
    for length in (3, 2):
        prefix = code_upper[:length]
        if prefix in CATEGORY_PREFIX_MAP:
            return prefix, CATEGORY_PREFIX_MAP[prefix]
    # Check dash like A-01, B-04
    if "-" in code_upper:
        prefix = code_upper.split("-")[0]
        if prefix in CATEGORY_PREFIX_MAP:
            return prefix, CATEGORY_PREFIX_MAP[prefix]
        return prefix, category_hint or f"Section {prefix}"
    return None, category_hint

def generate_comparison_key(description: str | None, unit: str | None) -> str:
    """Creates a normalized semantic key for cross-comparison."""
    if not description:
        return ""
    text = description.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if len(t) > 1 and t not in {"in", "and", "the", "for", "with", "to", "of", "a", "an", "at", "as", "by"}]
    tokens.sort()
    u = (unit or "").lower()
    return f"{'-'.join(tokens[:8])}_{u}"

class ValidationService:
    @staticmethod
    def validate_rate_item(
        code: str | None,
        description: str | None,
        unit: str | None,
        rate: float | None,
        existing_codes: set[str] | None = None,
    ) -> tuple[str, float, str | None, str | None]:
        """
        Validates an extracted rate item.
        
        Returns:
            (validation_status, confidence_score, validation_notes, normalized_unit)
        """
        issues: list[str] = []
        confidence = 1.0

        # Check rate
        if rate is None:
            issues.append("Missing rate value")
            confidence -= 0.35
        elif rate <= 0:
            issues.append("Zero or negative rate")
            confidence -= 0.4
        elif rate < 0.01:
            issues.append("Suspiciously low rate (< 0.01)")
            confidence -= 0.2
        elif rate > 50_000_000:
            issues.append("Suspiciously high rate (> 50,000,000)")
            confidence -= 0.2

        # Check code
        clean_code = clean_text(code) if code else None
        if not clean_code:
            issues.append("Missing item code")
            confidence -= 0.25
        elif not CODE_PATTERN.match(clean_code):
            issues.append("Unconventional code format")
            confidence -= 0.05

        # Check duplicate code within local sheet dataset
        if clean_code and existing_codes and clean_code in existing_codes:
            issues.append(f"Duplicate code '{clean_code}' in sheet")
            confidence -= 0.1

        # Check description
        clean_desc = clean_text(description) if description else None
        if not clean_desc or len(clean_desc) < 3:
            issues.append("Missing or very short description")
            confidence -= 0.35

        # Check unit
        norm_unit = normalize_unit(unit)
        if not norm_unit:
            issues.append("Missing unit")
            confidence -= 0.15
        elif norm_unit not in KNOWN_UNITS:
            issues.append(f"Unrecognized unit: '{norm_unit}'")
            confidence -= 0.05

        confidence = max(0.0, min(1.0, round(confidence, 2)))

        # A rate item is VALID if:
        # - Has a positive valid rate (0 < rate <= 50,000,000)
        # - Has an item code
        # - Has a valid description
        # Genuinely ambiguous items (missing rate or code or extreme values) go to NEEDS_REVIEW
        if rate is not None and 0 < rate <= 50_000_000 and clean_code and clean_desc and len(clean_desc) >= 3:
            status = "VALID"
            notes = "; ".join(issues) if issues else None
        elif issues:
            status = "NEEDS_REVIEW"
            notes = "; ".join(issues)
        else:
            status = "VALID"
            notes = None

        return status, confidence, notes, norm_unit
