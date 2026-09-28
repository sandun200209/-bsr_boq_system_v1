from __future__ import annotations

import io
import urllib.parse
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    MasterBOQOut,
    MasterBOQCreate,
    MasterBOQUpdate,
    MasterBOQItemOut,
    MasterBOQItemCreate,
    MasterBOQItemUpdate,
    AddRatesToBOQRequest,
    AddRatesToBOQResponse,
    BulkDeleteBOQItemsRequest,
    ReorderBOQItemsRequest,
)
from ..services.auth_service import get_current_user_optional, log_audit
from ..services import master_boq_service

router = APIRouter(prefix="/master-boqs", tags=["Master BOQ Workspace"])


@router.get("/active", response_model=MasterBOQOut)
def get_active_master_boq(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Returns the currently active Master BOQ workspace, or creates one if none exists.
    """
    return master_boq_service.get_or_create_active_boq(db, project_id=project_id)


@router.get("", response_model=list[MasterBOQOut])
def list_master_boqs(db: Session = Depends(get_db)):
    """
    Returns all Master BOQ workspaces ordered by latest update.
    """
    return master_boq_service.list_master_boqs(db)


@router.post("", response_model=MasterBOQOut)
def create_master_boq(
    payload: MasterBOQCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Creates a new Master BOQ workspace.
    """
    user_email = current_user.email if current_user else None
    boq = master_boq_service.create_master_boq(db, payload, user_email=user_email)
    if current_user:
        log_audit(db, current_user.id, "create_master_boq", "master_boqs", boq.id, {"name": boq.name})
    return boq


@router.get("/{boq_id}", response_model=MasterBOQOut)
def get_master_boq(boq_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a specific Master BOQ and its line items.
    """
    return master_boq_service.get_master_boq(db, boq_id)


@router.patch("/{boq_id}", response_model=MasterBOQOut)
def update_master_boq(
    boq_id: int,
    payload: MasterBOQUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Updates Master BOQ metadata (name, contingency rate, vat status, etc.).
    """
    boq = master_boq_service.update_master_boq(db, boq_id, payload)
    if current_user:
        log_audit(db, current_user.id, "update_master_boq", "master_boqs", boq.id, payload.model_dump(exclude_unset=True))
    return boq


@router.delete("/{boq_id}")
def delete_master_boq(
    boq_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Deletes a Master BOQ. Original RateItems in rate_items remain untouched.
    """
    master_boq_service.delete_master_boq(db, boq_id)
    if current_user:
        log_audit(db, current_user.id, "delete_master_boq", "master_boqs", boq_id, {})
    return {"success": True, "message": f"Master BOQ {boq_id} deleted"}


@router.post("/{boq_id}/items/from-rates", response_model=AddRatesToBOQResponse)
def add_rate_items_to_boq(
    boq_id: int,
    payload: AddRatesToBOQRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Exports selected RateItems from Rate Search to the Master BOQ workspace.
    Preserves source metadata and avoids unintentional duplicates.
    """
    added_items, added_count, existing_count = master_boq_service.add_rate_items_to_boq(
        db, boq_id, payload.rate_item_ids
    )
    if current_user:
        log_audit(
            db,
            current_user.id,
            "add_rate_items_to_boq",
            "master_boqs",
            boq_id,
            {"added": added_count, "existing": existing_count, "ids": payload.rate_item_ids},
        )
    return AddRatesToBOQResponse(
        added_count=added_count,
        existing_count=existing_count,
        items=added_items,
        message=f"{added_count} items added to Master BOQ ({existing_count} already existed)",
    )


@router.post("/{boq_id}/items/custom", response_model=MasterBOQItemOut)
def add_custom_item_to_boq(
    boq_id: int,
    payload: MasterBOQItemCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Adds a custom manual item directly to the Master BOQ workspace.
    """
    item = master_boq_service.add_custom_item_to_boq(db, boq_id, payload)
    if current_user:
        log_audit(db, current_user.id, "add_custom_boq_item", "master_boq_items", item.id, {"description": item.description})
    return item


@router.patch("/{boq_id}/items/{item_id}", response_model=MasterBOQItemOut)
def update_boq_item(
    boq_id: int,
    item_id: int,
    payload: MasterBOQItemUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Edits working BOQ line item values (description, unit, quantity, rate, notes).
    Strict data safety guarantee: original rate_items records are NEVER modified.
    """
    item = master_boq_service.update_boq_item(db, boq_id, item_id, payload)
    if current_user:
        log_audit(db, current_user.id, "update_boq_item", "master_boq_items", item.id, payload.model_dump(exclude_unset=True))
    return item


@router.delete("/{boq_id}/items/{item_id}")
def delete_boq_item(
    boq_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Deletes an individual item from Master BOQ. Original RateItems are NOT deleted.
    """
    master_boq_service.delete_boq_item(db, boq_id, item_id)
    if current_user:
        log_audit(db, current_user.id, "delete_boq_item", "master_boq_items", item_id, {})
    return {"success": True, "deleted_item_id": item_id}


@router.post("/{boq_id}/items/bulk-delete")
def bulk_delete_boq_items(
    boq_id: int,
    payload: BulkDeleteBOQItemsRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Deletes multiple selected items from Master BOQ.
    """
    count = master_boq_service.bulk_delete_boq_items(db, boq_id, payload.item_ids)
    if current_user:
        log_audit(db, current_user.id, "bulk_delete_boq_items", "master_boqs", boq_id, {"count": count})
    return {"success": True, "deleted_count": count}


@router.post("/{boq_id}/items/{item_id}/duplicate", response_model=MasterBOQItemOut)
def duplicate_boq_item(
    boq_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Explicitly duplicates an item in the Master BOQ workspace.
    """
    clone = master_boq_service.duplicate_boq_item(db, boq_id, item_id)
    if current_user:
        log_audit(db, current_user.id, "duplicate_boq_item", "master_boq_items", clone.id, {"original_id": item_id})
    return clone


@router.put("/{boq_id}/reorder")
def reorder_boq_items(
    boq_id: int,
    payload: ReorderBOQItemsRequest,
    db: Session = Depends(get_db),
):
    """
    Updates the sort_order of items in the Master BOQ workspace.
    """
    item_orders = [entry.model_dump() for entry in payload.item_orders]
    master_boq_service.reorder_boq_items(db, boq_id, item_orders)
    return {"success": True, "message": "Items reordered successfully"}


@router.get("/{boq_id}/export/excel")
@router.post("/{boq_id}/export/excel")
def export_master_boq_excel(boq_id: int, db: Session = Depends(get_db)):
    """
    Exports the current Master BOQ to a formatted Excel (.xlsx) file.
    Uses working rates, working quantities, and calculated amounts.
    """
    boq = master_boq_service.get_master_boq(db, boq_id)
    content = master_boq_service.export_master_boq_excel(boq)
    clean_name = "".join(c for c in boq.name if c.isalnum() or c in (" ", "-", "_")).strip() or "Master_BOQ"
    filename = f"{clean_name.replace(' ', '_')}.xlsx"
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/{boq_id}/export/pdf")
@router.post("/{boq_id}/export/pdf")
def export_master_boq_pdf(boq_id: int, db: Session = Depends(get_db)):
    """
    Exports the current Master BOQ to a formatted PDF report.
    Uses working rates, working quantities, and calculated amounts.
    """
    boq = master_boq_service.get_master_boq(db, boq_id)
    content = master_boq_service.export_master_boq_pdf(boq)
    clean_name = "".join(c for c in boq.name if c.isalnum() or c in (" ", "-", "_")).strip() or "Master_BOQ"
    filename = f"{clean_name.replace(' ', '_')}.pdf"
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
