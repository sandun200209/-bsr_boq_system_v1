"""
BSR 31-Part Canonical Workflow – API Router
Endpoints for the full canonical Part selection workflow.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from ..database import get_db
from ..models import CanonicalBSRPart, ProjectPartSelection, ProjectPartItem, PartTemplateMapping
from ..services import bsr_part_service as svc
from ..services.auth_service import get_current_user
from ..schemas import (
    CanonicalBSRPartOut,
    ProjectPartItemOut,
    ProjectPartItemUpdate,
    ProjectPartSelectionOut,
    PartTemplateMappingOut,
    PartTemplateMappingUpdate,
    BSRImportBreakdownOut,
)

router = APIRouter(prefix="/bsr-parts", tags=["BSR 31-Part Workflow"])


# ---------------------------------------------------------------------------
# Canonical Parts list
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CanonicalBSRPartOut])
def list_canonical_parts(db: Session = Depends(get_db)):
    parts = (
        db.query(CanonicalBSRPart)
        .filter(CanonicalBSRPart.active == True)
        .order_by(CanonicalBSRPart.sort_order)
        .all()
    )
    return parts


# ---------------------------------------------------------------------------
# Parts Library (with year availability matrix)
# ---------------------------------------------------------------------------

@router.get("/library")
def get_parts_library(
    district: str | None = Query(None),
    province: str | None = Query(None),
    rate_system: str = Query("BSR"),
    db: Session = Depends(get_db),
):
    return svc.get_parts_library(db, district=district, province=province, rate_system=rate_system)


# ---------------------------------------------------------------------------
# Cross-Year Part Data
# ---------------------------------------------------------------------------

@router.get("/{part_id}/cross-year")
def get_part_cross_year(
    part_id: int,
    district: str | None = Query(None),
    province: str | None = Query(None),
    rate_system: str = Query("BSR"),
    vat_basis: str | None = Query(None),
    years: str | None = Query(None, description="Comma-separated years e.g. 2023,2024"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    part = db.query(CanonicalBSRPart).get(part_id)
    if not part:
        raise HTTPException(404, f"Canonical BSR Part {part_id} not found")

    year_list = None
    if years:
        try:
            year_list = [int(y.strip()) for y in years.split(",") if y.strip()]
        except ValueError:
            raise HTTPException(400, "years must be comma-separated integers")

    return svc.get_part_cross_year_data(
        db,
        part_id=part_id,
        district=district,
        province=province,
        years=year_list,
        search=search,
        vat_basis=vat_basis,
        rate_system=rate_system,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Template Mapping CRUD
# ---------------------------------------------------------------------------

@router.get("/{part_id}/template-mapping", response_model=PartTemplateMappingOut | None)
def get_template_mapping(part_id: int, db: Session = Depends(get_db)):
    mapping = (
        db.query(PartTemplateMapping)
        .filter(PartTemplateMapping.canonical_part_id == part_id)
        .first()
    )
    return mapping


@router.patch("/{part_id}/template-mapping", response_model=PartTemplateMappingOut)
def update_template_mapping(
    part_id: int,
    payload: PartTemplateMappingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "MANAGER"):
        raise HTTPException(403, "Only ADMIN or MANAGER can update template mappings")

    mapping = (
        db.query(PartTemplateMapping)
        .filter(PartTemplateMapping.canonical_part_id == part_id)
        .first()
    )
    if not mapping:
        # Create it
        part = db.query(CanonicalBSRPart).get(part_id)
        if not part:
            raise HTTPException(404, f"Part {part_id} not found")
        mapping = PartTemplateMapping(canonical_part_id=part_id, target_sheet=f"Part {part.part_no}")
        db.add(mapping)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(mapping, field, value)

    db.commit()
    db.refresh(mapping)
    return mapping


# ---------------------------------------------------------------------------
# Classify unmapped items
# ---------------------------------------------------------------------------

@router.post("/classify")
def classify_items(
    rate_system: str = Query("BSR"),
    force_remap: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "MANAGER"):
        raise HTTPException(403, "Requires ADMIN or MANAGER role")
    counts = svc.classify_all_unmapped_rate_items(db, rate_system=rate_system, force_remap=force_remap)
    return {"success": True, **counts}


# ---------------------------------------------------------------------------
# Import Breakdown
# ---------------------------------------------------------------------------

@router.get("/import-breakdown/{source_file_id}", response_model=BSRImportBreakdownOut)
def import_breakdown(source_file_id: int, db: Session = Depends(get_db)):
    try:
        return svc.get_import_breakdown(db, source_file_id=source_file_id)
    except Exception as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------------------
# Seed default template mappings
# ---------------------------------------------------------------------------

@router.post("/seed-template-mappings")
def seed_mappings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Only ADMIN can seed template mappings")
    created = svc.seed_default_part_template_mappings(db)
    return {"success": True, "created": created}


# ---------------------------------------------------------------------------
# Part Selections (Project BOQs)
# ---------------------------------------------------------------------------

@router.post("/{part_id}/selections", response_model=ProjectPartSelectionOut)
def create_selection(
    part_id: int,
    project_id: int | None = Body(None),
    name: str | None = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        sel = svc.create_part_selection(
            db,
            canonical_part_id=part_id,
            project_id=project_id,
            user_email=current_user.email,
            name=name,
        )
        return sel
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/selections/{selection_id}", response_model=ProjectPartSelectionOut)
def get_selection(selection_id: int, db: Session = Depends(get_db)):
    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise HTTPException(404, f"Selection {selection_id} not found")
    return sel


@router.get("/selections", response_model=list[ProjectPartSelectionOut])
def list_selections(
    part_id: int | None = Query(None),
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ProjectPartSelection)
    if part_id:
        q = q.filter(ProjectPartSelection.canonical_part_id == part_id)
    if project_id:
        q = q.filter(ProjectPartSelection.project_id == project_id)
    return q.order_by(ProjectPartSelection.created_at.desc()).all()


@router.delete("/selections/{selection_id}")
def delete_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise HTTPException(404, f"Selection {selection_id} not found")
    db.delete(sel)
    db.commit()
    return {"success": True, "deleted_id": selection_id}


# ---------------------------------------------------------------------------
# Add items to selection
# ---------------------------------------------------------------------------

@router.post("/selections/{selection_id}/items")
def add_items(
    selection_id: int,
    rate_item_ids: list[int] = Body(...),
    allow_duplicates: bool = Body(False),
    replace_existing_ids: list[int] | None = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        result = svc.add_items_to_part_selection(
            db,
            selection_id=selection_id,
            rate_item_ids=rate_item_ids,
            user_email=current_user.email,
            allow_duplicates=allow_duplicates,
            replace_existing_ids=replace_existing_ids,
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ---------------------------------------------------------------------------
# Edit a project item
# ---------------------------------------------------------------------------

@router.patch("/selections/items/{item_id}", response_model=ProjectPartItemOut)
def update_item(
    item_id: int,
    payload: ProjectPartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        updated = svc.update_part_item(
            db,
            item_id=item_id,
            payload=payload.model_dump(exclude_none=True),
            user_email=current_user.email,
            user_role=current_user.role,
        )
        return updated
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------------------
# Duplicate item
# ---------------------------------------------------------------------------

@router.post("/selections/items/{item_id}/duplicate", response_model=ProjectPartItemOut)
def duplicate_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return svc.duplicate_part_item(db, item_id=item_id, user_email=current_user.email)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ---------------------------------------------------------------------------
# Remove item from project (NEVER deletes BSR source)
# ---------------------------------------------------------------------------

@router.delete("/selections/items/{item_id}")
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    removed = svc.remove_part_item(db, item_id=item_id)
    if not removed:
        raise HTTPException(404, f"Item {item_id} not found")
    return {"success": True, "removed_id": item_id}


# ---------------------------------------------------------------------------
# Item edit history
# ---------------------------------------------------------------------------

@router.get("/selections/items/{item_id}/history")
def get_item_history(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "MANAGER"):
        raise HTTPException(403, "Only ADMIN or MANAGER can view edit history")
    history = svc.get_part_item_history(db, item_id=item_id)
    return [
        {
            "id": h.id,
            "project_part_item_id": h.project_part_item_id,
            "field_changed": h.field_changed,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "changed_by": h.changed_by,
            "changed_at": h.changed_at.isoformat(),
            "reason": h.reason,
        }
        for h in history
    ]


# ---------------------------------------------------------------------------
# Reorder items in selection
# ---------------------------------------------------------------------------

@router.put("/selections/{selection_id}/reorder")
def reorder_items(
    selection_id: int,
    item_orders: list[dict] = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sel = db.query(ProjectPartSelection).get(selection_id)
    if not sel:
        raise HTTPException(404, f"Selection {selection_id} not found")

    for order in item_orders:
        item = db.query(ProjectPartItem).get(order["id"])
        if item and item.project_part_selection_id == selection_id:
            item.sort_order = order["sort_order"]

    db.commit()
    return {"success": True, "message": f"Reordered {len(item_orders)} items"}


# ---------------------------------------------------------------------------
# Export Excel
# ---------------------------------------------------------------------------

@router.get("/selections/{selection_id}/export/excel")
def export_excel(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data, filename = svc.export_part_excel(db, selection_id=selection_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Export PDF
# ---------------------------------------------------------------------------

@router.get("/selections/{selection_id}/export/pdf")
def export_pdf(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data, filename = svc.export_part_pdf(db, selection_id=selection_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
