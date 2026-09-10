from __future__ import annotations
from pathlib import Path
from .base import ExtractedItem
from .excel_importer import extract_excel
from .pdf_importer import extract_pdf, OCRRequiredException
from .docx_importer import extract_docx
from .csv_importer import extract_csv
from .text_importer import extract_text

def extract_document(
    file_path: Path,
    category_hint: str | None = None,
) -> list[ExtractedItem]:
    """
    Dispatcher directing files to their dedicated format-specific extractor.
    """
    ext = file_path.suffix.lower()

    if ext in {".xlsx", ".xlsm"}:
        return extract_excel(file_path, category_hint=category_hint)
    elif ext == ".pdf":
        return extract_pdf(file_path, category_hint=category_hint)
    elif ext == ".docx":
        return extract_docx(file_path, category_hint=category_hint)
    elif ext in {".csv", ".tsv"}:
        return extract_csv(file_path, category_hint=category_hint)
    elif ext in {".txt", ".text"}:
        return extract_text(file_path, category_hint=category_hint)
    else:
        raise ValueError(f"No extractor registered for file extension '{ext}'")

__all__ = [
    "extract_document",
    "extract_excel",
    "extract_pdf",
    "extract_docx",
    "extract_csv",
    "extract_text",
    "ExtractedItem",
    "OCRRequiredException",
]
