from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RateItem, SourceFile, User
from ..schemas import ExportRequest, ExportPdfRequest, ExportByIdsRequest
from ..services.auth_service import get_current_user_optional, log_audit
from ..services.export_service import (
    PACKAGE_REGISTRY,
    get_template_package_data,
    generate_package_excel,
    generate_package_pdf,
)

router = APIRouter(prefix="/export", tags=["Export & QS Reports"])


@router.get("/packages")
def get_export_packages():
    """
    Returns available QS packages supported by the master template,
    including sheet names, default titles, and columns.
    """
    packages = []
    for pkg_id, pkg in PACKAGE_REGISTRY.items():
        packages.append({
            "id": pkg_id,
            "name": pkg["name"],
            "boq_sheet": pkg["boq_sheet"],
            "recon_sheet": pkg["recon_sheet"],
            "default_title": pkg["default_title"],
            "default_recon_title": pkg["default_recon_title"],
            "default_note": pkg["default_note"],
            "columns": pkg["columns"],
            "recon_columns": pkg["recon_columns"],
        })
    return {"packages": packages}


@router.get("/preview/{package_key}")
def get_package_preview(package_key: str = "electrical"):
    """
    Returns the audited baseline data from the reference template for instant
    live preview in the UI before generating downloads.
    """
    try:
        data = get_template_package_data(package_key)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preview data: {str(e)}")


@router.post("/excel")
def export_excel(
    payload: ExportRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Generates and streams an Excel (.xlsx) workbook strictly matching the master
    reference template layout, sheets, formulas, and QS styling.
    """
    try:
        xlsx_bytes = generate_package_excel(
            package_key=payload.package_key,
            project_title=payload.project_title,
            source_note=payload.source_note,
            contingency_rate=payload.contingency_rate,
            items=payload.items,
            reconciliation_items=payload.reconciliation_items,
            vat_status=payload.vat_status,
        )

        pkg_name = payload.package_key.capitalize()
        filename = f"Matara_OT_Consolidated_BOQ_Estimate_{pkg_name}.xlsx"

        if current_user:
            log_audit(
                db=db,
                action="EXPORT_EXCEL",
                entity_type="PACKAGE",
                entity_id=payload.package_key,
                description=f"Exported Master QS Excel for package {pkg_name}",
                user=current_user,
            )

        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


@router.post("/pdf")
def export_pdf(
    payload: ExportPdfRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Generates and streams a professional QS engineering PDF report mirroring the Excel
    reference workbook appearance.
    Variant options: 'combined' (both sections), 'boq' (only BOQ), 'reconciliation' (only Reconciliation).
    """
    try:
        pdf_bytes = generate_package_pdf(
            package_key=payload.package_key,
            variant=payload.variant,
            project_title=payload.project_title,
            source_note=payload.source_note,
            contingency_rate=payload.contingency_rate,
            items=payload.items,
            reconciliation_items=payload.reconciliation_items,
            vat_status=payload.vat_status,
        )

        pkg_name = payload.package_key.capitalize()
        var_name = payload.variant.capitalize()
        filename = f"Matara_OT_Consolidated_{pkg_name}_{var_name}.pdf"

        if current_user:
            log_audit(
                db=db,
                action="EXPORT_PDF",
                entity_type="PACKAGE",
                entity_id=payload.package_key,
                description=f"Exported Master QS PDF ({payload.variant}) for package {pkg_name}",
                user=current_user,
            )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/from-database")
def export_from_database(
    sector: str | None = Query(None),
    rate_system: str | None = Query(None),
    source_file_id: int | None = Query(None),
    status: str | None = Query("VALID"),
    limit: int = Query(100, ge=1, le=500),
    format: str = Query("excel", enum=["excel", "pdf_combined", "pdf_boq", "pdf_recon"]),
    contingency_rate: float = Query(0.10),
    package_key: str = Query("electrical"),
    db: Session = Depends(get_db),
):
    """
    Fetches stored rate items from the database / review queue and formats them into
    the master template layout.
    """
    query = select(RateItem)
    if sector:
        query = query.where(RateItem.sector == sector)
    if rate_system:
        query = query.where(RateItem.rate_system == rate_system)
    if source_file_id:
        query = query.where(RateItem.source_file_id == source_file_id)
    if status and status.upper() != "ALL":
        query = query.where(RateItem.validation_status == status.upper())

    query = query.order_by(RateItem.id.asc()).limit(limit)
    db_items = db.scalars(query).all()

    items = []
    for idx, it in enumerate(db_items):
        items.append({
            "source_row": it.source_row or (idx + 1),
            "item_code": it.item_code or f"{idx+1}",
            "description": it.description or "Rate Item",
            "unit": it.unit or "Item",
            "source_qty": 1.0,
            "rate": it.rate or 0.0,
            "duplicate_qty": 0.0,
            "reviewed_qty": 1.0,
            "overlap_reason": it.validation_notes or "",
            "action": "RETAIN",
            "confidence": "High" if it.confidence_score >= 0.8 else "Medium",
            "remarks": f"System Status: {it.validation_status}",
        })

    if format == "excel":
        xlsx_bytes = generate_package_excel(
            package_key=package_key,
            items=items,
            contingency_rate=contingency_rate,
        )
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="BSR_Hub_Export_{package_key}.xlsx"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    else:
        var_map = {
            "pdf_combined": "combined",
            "pdf_boq": "boq",
            "pdf_recon": "reconciliation",
        }
        variant = var_map.get(format, "combined")
        pdf_bytes = generate_package_pdf(
            package_key=package_key,
            variant=variant,
            items=items,
            contingency_rate=contingency_rate,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="BSR_Hub_Export_{package_key}_{variant}.pdf"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )


@router.post("/by-ids")
def export_selected_items(
    payload: ExportByIdsRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Exports rate items explicitly selected by the user by ID into the master template.
    Maps:
      Item Code -> Item
      Description -> Description
      Unit -> Unit
      Rate -> Rate (LKR)
    Populates project review fields:
      Source Qty
      Duplicate Qty
      Reviewed Qty
      Overlap / Reason
      Action
      Confidence
      Remarks
    Calculates Source Amount, Duplicate Amount and Reviewed Amount.
    Populates the Reconciliation sheet only with approved reconciliation records.
    Generates a NEW .xlsx file or matching PDF.
    """
    if not payload.rate_item_ids:
        raise HTTPException(status_code=400, detail="No rate items were selected for export.")

    # Retrieve matching items preserving order of IDs
    items_query = select(RateItem).where(RateItem.id.in_(payload.rate_item_ids))
    db_items = {it.id: it for it in db.scalars(items_query).all()}

    mapped_items = []
    for idx, r_id in enumerate(payload.rate_item_ids):
        it = db_items.get(r_id)
        if not it:
            continue
        mapped_items.append({
            "source_row": it.source_row or (idx + 1),
            "item_code": it.item_code or f"{idx+1}",
            "description": it.description or "Rate Item",
            "unit": it.unit or "Item",
            "source_qty": 1.0,
            "rate": it.rate or 0.0,
            "duplicate_qty": 0.0,
            "reviewed_qty": None,  # Computed via =E-H
            "overlap_reason": it.validation_notes or "",
            "action": "RETAIN",
            "confidence": "High" if (it.confidence_score or 1.0) >= 0.8 else "Medium",
            "remarks": f"Selected from BSR Rate Hub (Status: {it.validation_status})",
        })

    pkg_name = payload.package_key.capitalize()

    if payload.format == "excel":
        xlsx_bytes = generate_package_excel(
            package_key=payload.package_key,
            project_title=payload.project_title,
            source_note=payload.source_note,
            contingency_rate=payload.contingency_rate,
            items=mapped_items,
            reconciliation_items=payload.reconciliation_items,
            vat_status=payload.vat_status,
        )
        filename = f"Matara_OT_Consolidated_BOQ_Estimate_{pkg_name}_Selected.xlsx"
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    else:
        var_map = {
            "pdf_combined": "combined",
            "pdf_boq": "boq",
            "pdf_recon": "reconciliation",
        }
        variant = var_map.get(payload.format, "combined")
        pdf_bytes = generate_package_pdf(
            package_key=payload.package_key,
            variant=variant,
            project_title=payload.project_title,
            source_note=payload.source_note,
            contingency_rate=payload.contingency_rate,
            items=mapped_items,
            reconciliation_items=payload.reconciliation_items,
            vat_status=payload.vat_status,
        )
        filename = f"Matara_OT_Consolidated_{pkg_name}_Selected_{variant.capitalize()}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
