from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, CESMMSection
from ..schemas import (
    CESMMSectionOut,
    RateItemCESMMOut,
    RateItemCESMMAssignRequest,
)
from ..services.auth_service import get_current_user_optional, require_role, log_audit
from ..services.cesmm_service import (
    get_all_cesmm_sections,
    get_item_cesmm_mappings,
    assign_item_cesmm_sections,
    remove_item_cesmm_mapping,
    set_primary_cesmm_mapping,
    seed_cesmm_sections,
)

router = APIRouter(prefix="/cesmm", tags=["CESMM-SL"])


@router.get("/sections", response_model=list[CESMMSectionOut])
def list_cesmm_sections(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Returns all 31 standard CESMM-SL Work Sections (e.g. 01 Preliminaries to 31 Simple Building Works).
    """
    sections = get_all_cesmm_sections(db, active_only=active_only)
    if not sections:
        # Seed on demand if database was just initialized
        sections = seed_cesmm_sections(db)

    results = []
    for s in sections:
        out = CESMMSectionOut.model_validate(s)
        out.display_label = f"{s.section_no} - {s.name} (Section {s.section_code})"
        results.append(out)
    return results


@router.get("/items/{rate_id}", response_model=list[RateItemCESMMOut])
def get_rate_item_cesmm(
    rate_id: int,
    db: Session = Depends(get_db),
):
    """Returns current CESMM-SL mappings for a given rate item."""
    return get_item_cesmm_mappings(db, rate_id)


@router.post("/items/{rate_id}", response_model=list[RateItemCESMMOut])
def assign_rate_item_cesmm(
    rate_id: int,
    payload: RateItemCESMMAssignRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Assigns or updates one or more CESMM-SL sections to a rate item.
    Designates one as primary. Does NOT alter the item's original Category or Rate Book.
    """
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    section_ids = [m.cesmm_section_id for m in payload.mappings]
    primary_id = next((m.cesmm_section_id for m in payload.mappings if m.is_primary), None)
    if not primary_id and section_ids:
        primary_id = section_ids[0]

    try:
        updated = assign_item_cesmm_sections(
            db=db,
            rate_item_id=rate_id,
            section_ids=section_ids,
            primary_section_id=primary_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    log_audit(
        db=db,
        action="UPDATE_CESMM_MAPPING",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Assigned CESMM sections {section_ids} (Primary: {primary_id}) to RateItem {rate_id}",
        user=current_user,
    )

    return updated


@router.delete("/items/{rate_id}/{cesmm_section_id}", response_model=list[RateItemCESMMOut])
def delete_rate_item_cesmm(
    rate_id: int,
    cesmm_section_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Removes an incorrect or obsolete CESMM section mapping from a rate item."""
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    updated = remove_item_cesmm_mapping(db, rate_id, cesmm_section_id)

    log_audit(
        db=db,
        action="DELETE_CESMM_MAPPING",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Removed CESMM section {cesmm_section_id} from RateItem {rate_id}",
        user=current_user,
    )

    return updated


@router.put("/items/{rate_id}/primary/{cesmm_section_id}", response_model=list[RateItemCESMMOut])
def set_primary_cesmm(
    rate_id: int,
    cesmm_section_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Sets a specific assigned CESMM section as primary for a rate item."""
    if current_user and current_user.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Viewers have read-only permissions.")

    try:
        updated = set_primary_cesmm_mapping(db, rate_id, cesmm_section_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_audit(
        db=db,
        action="SET_PRIMARY_CESMM",
        entity_type="RATE_ITEM",
        entity_id=str(rate_id),
        description=f"Set CESMM section {cesmm_section_id} as primary for RateItem {rate_id}",
        user=current_user,
    )

    return updated
