from __future__ import annotations
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models import SourceFile, ImportJob, RateItem
from ..schemas import SourceFileOut, ImportJobOut
from ..services.storage_service import StorageService
from ..importers import extract_document, OCRRequiredException

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=dict)
def upload_document(
    province: str = Form(...),
    district: str = Form(...),
    year: int = Form(...),
    revision: str = Form(...),
    dataset_type: str = Form("BSR Rate Book"),
    vat_basis: str = Form("Without VAT"),
    category_hint: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate Sri Lanka province and district
    prov = province.strip()
    dist = district.strip()

    # Normalize All Provinces / National aliases
    if prov.lower() in ["all provinces", "all province", "all island", "national", "all-island"]:
        prov = "All Provinces"
    if dist.lower() in ["all districts", "all district", "all", "national", "all island"]:
        dist = "All Districts"

    if prov not in settings.SRI_LANKA_PROVINCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid province '{prov}'. Valid: {', '.join(settings.SRI_LANKA_PROVINCES.keys())}"
        )
    valid_districts = settings.SRI_LANKA_PROVINCES[prov]
    if dist not in valid_districts and dist != "All Districts":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid district '{dist}' for province '{prov}'. Valid: {', '.join(valid_districts)}"
        )

    # 1. Permanently store original file
    stored_path, orig_name, stored_name, file_size, sha256 = StorageService.store_uploaded_file(
        file=file,
        province=prov,
        district=dist,
        year=year,
        revision=revision.strip(),
    )

    ext = Path(orig_name).suffix.lower()

    # 2. Create SourceFile record
    doc = SourceFile(
        original_filename=orig_name,
        stored_filename=stored_name,
        file_path=str(stored_path),
        file_type=ext,
        file_size=file_size,
        sha256_hash=sha256,
        province=prov,
        district=dist,
        year=year,
        revision=revision.strip(),
        dataset_type=dataset_type.strip(),
        vat_basis=vat_basis.strip(),
        category_hint=category_hint.strip() if category_hint else None,
        upload_status="UPLOADED",
        import_status="PROCESSING",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Create ImportJob record
    job = ImportJob(
        source_file_id=doc.id,
        status="PROCESSING",
        progress_percent=10,
        message="Starting format extraction pipeline...",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 4. Run format-specific extraction
    try:
        extracted = extract_document(stored_path, category_hint=doc.category_hint)
    except OCRRequiredException as ocr_err:
        doc.upload_status = "COMPLETED"
        doc.import_status = "OCR_REQUIRED"
        doc.processed_at = datetime.utcnow()
        job.status = "READY_FOR_REVIEW"
        job.progress_percent = 100
        job.message = "Scanned document detected: OCR required for image-only pages."
        db.commit()
        return {
            "success": True,
            "document_id": doc.id,
            "job_id": job.id,
            "filename": orig_name,
            "items_detected": 0,
            "valid_items": 0,
            "needs_review": 0,
            "ocr_required": True,
            "message": "Scanned document detected. Digital text layer absent.",
        }
    except Exception as exc:
        doc.upload_status = "FAILED"
        doc.import_status = "FAILED"
        job.status = "FAILED"
        job.message = f"Extraction failed: {str(exc)}"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Failed to extract rates from document: {str(exc)}")

    # 5. Save rate items in transaction
    valid_count = 0
    review_count = 0
    rejected_count = 0

    rate_items_to_add: list[RateItem] = []
    for item in extracted:
        status = item.validation_status
        if status == "VALID":
            valid_count += 1
        elif status == "NEEDS_REVIEW":
            review_count += 1
        elif status == "REJECTED":
            rejected_count += 1

        item_year = item.sheet_year or doc.year
        item_rev = (item.sheet_revision or doc.revision)[:120]
        item_vat = (item.sheet_vat_basis or doc.vat_basis)[:80]
        item_dst = (item.sheet_dataset_type or doc.dataset_type)[:80]

        rate_items_to_add.append(
            RateItem(
                source_file_id=doc.id,
                province=doc.province[:80],
                district=doc.district[:80],
                year=item_year,
                revision=item_rev,
                dataset_type=item_dst,
                vat_basis=item_vat,
                category_code=item.category_code[:250] if item.category_code else None,
                category_name=item.category_name[:490] if item.category_name else None,
                item_code=item.item_code[:250] if item.item_code else None,
                description=item.description,
                unit=item.unit[:90] if item.unit else None,
                rate=item.rate,
                source_page=item.source_page,
                source_sheet=item.source_sheet[:250] if item.source_sheet else None,
                source_row=item.source_row,
                source_cell=item.source_cell[:250] if item.source_cell else None,
                raw_text=item.raw_text[:2000] if item.raw_text else None,
                confidence_score=item.confidence_score,
                validation_status=item.validation_status,
                validation_notes=item.validation_notes,
            )
        )

    # Insert in batches of 500 to stay well within Postgres parameter limits
    BATCH_SIZE = 500
    for i in range(0, len(rate_items_to_add), BATCH_SIZE):
        batch = rate_items_to_add[i : i + BATCH_SIZE]
        db.add_all(batch)
        db.flush()

    # 6. Update SourceFile and Job stats
    doc.upload_status = "COMPLETED"
    doc.import_status = "READY_FOR_REVIEW" if review_count > 0 else "COMPLETED"
    doc.processed_at = datetime.utcnow()
    doc.total_rows_detected = len(extracted)
    doc.valid_rows = valid_count
    doc.review_rows = review_count
    doc.rejected_rows = rejected_count

    job.status = "COMPLETED"
    job.progress_percent = 100
    job.message = f"Successfully parsed {len(extracted)} items ({valid_count} valid, {review_count} needs review)."

    db.commit()

    return {
        "success": True,
        "document_id": doc.id,
        "job_id": job.id,
        "filename": orig_name,
        "file_size": file_size,
        "items_detected": len(extracted),
        "valid_items": valid_count,
        "needs_review": review_count,
        "rejected_items": rejected_count,
        "ocr_required": False,
        "message": f"Successfully imported {len(extracted)} items.",
    }

@router.get("", response_model=list[SourceFileOut])
def list_documents(
    province: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(SourceFile)
    if province:
        query = query.where(SourceFile.province == province)
    if district:
        query = query.where(SourceFile.district == district)
    if year:
        query = query.where(SourceFile.year == year)
    query = query.order_by(desc(SourceFile.uploaded_at)).offset(skip).limit(limit)
    return db.scalars(query).all()

@router.get("/{doc_id}", response_model=SourceFileOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")
    return doc

@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file could not be located on disk")
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type="application/octet-stream",
    )

@router.get("/{doc_id}/view")
def view_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file could not be located on disk")
    media_type = "application/pdf" if doc.file_type == ".pdf" else "text/plain"
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=media_type,
    )
