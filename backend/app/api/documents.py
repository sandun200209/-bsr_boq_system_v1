from __future__ import annotations
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models import SourceFile, ImportJob, RateItem, User
from ..schemas import SourceFileOut, ImportJobOut
from ..services.storage_service import StorageService, get_media_type
from ..services.auth_service import get_current_user_optional, require_role, log_audit
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
    sector: str = Form("Building Works"),
    rate_system: str = Form("BSR"),
    file: UploadFile = File(...),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    # If a user is logged in, verify they are not a read-only VIEWER
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(
            status_code=403,
            detail="Viewers have read-only access and cannot upload documents.",
        )

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

    # 1. Permanently store original file (Cloud Supabase Storage or Local)
    (
        stored_path,
        orig_name,
        stored_name,
        file_size,
        sha256,
        storage_provider,
        storage_key,
        public_url,
    ) = StorageService.store_uploaded_file(
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
        sector=sector.strip() if sector else "Building Works",
        rate_system=rate_system.strip() if rate_system else "BSR",
        storage_provider=storage_provider,
        storage_key=storage_key,
        public_url=public_url,
        uploaded_by_id=current_user.id if current_user else None,
        uploaded_by_email=current_user.email if current_user else None,
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
    except OCRRequiredException:
        doc.upload_status = "COMPLETED"
        doc.import_status = "OCR_REQUIRED"
        doc.processed_at = datetime.utcnow()
        job.status = "READY_FOR_REVIEW"
        job.progress_percent = 100
        job.message = "Scanned document detected: OCR required for image-only pages."
        db.commit()

        log_audit(
            db=db,
            action="UPLOAD_DOCUMENT",
            entity_type="SOURCE_FILE",
            entity_id=str(doc.id),
            description=f"Uploaded {doc.original_filename} (OCR Required)",
            user=current_user,
        )

        return {
            "success": True,
            "document_id": doc.id,
            "job_id": job.id,
            "filename": orig_name,
            "file_size": file_size,
            "items_detected": 0,
            "valid_items": 0,
            "needs_review": 0,
            "rejected_items": 0,
            "ocr_required": True,
            "message": "Scanned PDF detected without a text layer. Marked as OCR_REQUIRED.",
        }
    except Exception as e:
        doc.upload_status = "FAILED"
        doc.import_status = "FAILED"
        job.status = "FAILED"
        job.message = f"Extraction failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

    job.progress_percent = 50
    job.message = f"Extraction completed: {len(extracted)} candidate rows detected. Saving items..."
    db.commit()

    # 5. Bulk insert extracted rate items in safe batches of 500
    valid_count = 0
    review_count = 0
    rejected_count = 0

    batch_size = 500
    batch_records = []

    for item in extracted:
        status_val = item.validation_status
        if status_val == "VALID":
            valid_count += 1
        elif status_val == "NEEDS_REVIEW":
            review_count += 1
        elif status_val == "REJECTED":
            rejected_count += 1

        rate_item = RateItem(
            source_file_id=doc.id,
            province=doc.province,
            district=doc.district,
            year=doc.year,
            revision=doc.revision,
            dataset_type=doc.dataset_type,
            vat_basis=doc.vat_basis,
            sector=doc.sector,
            rate_system=doc.rate_system,
            category_code=item.category_code,
            category_name=item.category_name,
            item_code=item.item_code,
            description=item.description,
            unit=item.unit,
            rate=item.rate,
            source_page=item.source_page,
            source_sheet=item.source_sheet,
            source_row=item.source_row,
            source_cell=item.source_cell,
            raw_text=item.raw_text,
            confidence_score=item.confidence_score,
            validation_status=item.validation_status,
            validation_notes=item.validation_notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        batch_records.append(rate_item)

        if len(batch_records) >= batch_size:
            db.add_all(batch_records)
            db.flush()
            batch_records.clear()

    if batch_records:
        db.add_all(batch_records)
        db.flush()
        batch_records.clear()

    # 6. Update SourceFile and ImportJob summary
    doc.upload_status = "COMPLETED"
    doc.import_status = "READY_FOR_REVIEW" if review_count > 0 else "COMPLETED"
    doc.processed_at = datetime.utcnow()
    doc.total_rows_detected = len(extracted)
    doc.valid_rows = valid_count
    doc.review_rows = review_count
    doc.rejected_rows = rejected_count

    job.status = "COMPLETED"
    job.progress_percent = 100
    job.message = f"Extraction complete: {valid_count} valid, {review_count} need review, {rejected_count} rejected."

    db.commit()

    # 7. Audit log
    log_audit(
        db=db,
        action="UPLOAD_DOCUMENT",
        entity_type="SOURCE_FILE",
        entity_id=str(doc.id),
        description=f"Uploaded {doc.original_filename} ({doc.sector} / {doc.rate_system}) - {len(extracted)} items extracted",
        user=current_user,
    )

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
    sector: str | None = Query(None),
    rate_system: str | None = Query(None),
    province: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List documents with optional filtering."""
    query = select(SourceFile)
    if sector:
        query = query.where(SourceFile.sector == sector)
    if rate_system:
        query = query.where(SourceFile.rate_system == rate_system)
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
    """Get single document metadata."""
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")
    return doc

@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Download source document."""
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")

    try:
        file_path = StorageService.get_file_content_or_path(
            doc.file_path, doc.storage_provider, doc.storage_key
        )
    except HTTPException:
        raise HTTPException(status_code=404, detail="Stored file could not be located on disk or cloud")

    media_type = get_media_type(doc.original_filename)
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=media_type,
    )

@router.get("/{doc_id}/view")
def view_document(
    doc_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Inline view of document (PDFs, images, text)."""
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")

    try:
        file_path = StorageService.get_file_content_or_path(
            doc.file_path, doc.storage_provider, doc.storage_key
        )
    except HTTPException:
        raise HTTPException(status_code=404, detail="Stored file could not be located on disk or cloud")

    media_type = get_media_type(doc.original_filename)
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=media_type,
    )

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """Delete a document and its associated rate items (ADMIN only)."""
    doc = db.get(SourceFile, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Source file not found")

    filename = doc.original_filename
    item_count = len(doc.rate_items)

    # Delete from storage
    StorageService.delete_stored_file(doc.file_path, doc.storage_provider, doc.storage_key)

    # Delete database record (cascading to rate_items and import_jobs)
    db.delete(doc)
    db.commit()

    log_audit(
        db=db,
        action="DELETE_DOCUMENT",
        entity_type="SOURCE_FILE",
        entity_id=str(doc_id),
        description=f"Deleted source file '{filename}' and {item_count} associated rate items",
        user=current_user,
    )

    return {
        "success": True,
        "message": f"Document '{filename}' and {item_count} rate items deleted successfully.",
    }
