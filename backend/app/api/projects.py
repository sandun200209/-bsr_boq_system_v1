from __future__ import annotations
import urllib.parse
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import (
    Project,
    ProjectSection,
    ProjectItem,
    DuplicationRecord,
    ChangeRegisterRecord,
    ReconciliationRecord,
    Template,
    TemplateMapping,
    User,
)
from ..schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectSectionCreate,
    ProjectSectionUpdate,
    ProjectSectionOut,
    ProjectItemCreate,
    ProjectItemUpdate,
    ProjectItemOut,
    DuplicationRecordCreate,
    DuplicationRecordOut,
    ChangeRegisterRecordCreate,
    ChangeRegisterRecordOut,
    ReconciliationRecordCreate,
    ReconciliationRecordOut,
    HistoricalRateComparisonOut,
    TemplateOut,
    TemplateMappingOut,
    ProjectExportRequest,
)
from ..services.auth_service import get_current_user_optional, log_audit
from ..services.project_service import (
    get_or_create_default_project,
    compare_historical_rates,
)
from ..services.template_manager_service import (
    get_or_register_default_template,
    export_project_excel,
)

router = APIRouter(prefix="/projects", tags=["Projects & Estimating"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """
    Returns all projects. Ensures default project exists.
    """
    get_or_create_default_project(db)
    stmt = (
        select(Project)
        .options(
            selectinload(Project.sections).selectinload(ProjectSection.items),
            selectinload(Project.sections).selectinload(ProjectSection.duplication_records),
            selectinload(Project.sections).selectinload(ProjectSection.change_register_records),
            selectinload(Project.sections).selectinload(ProjectSection.reconciliation_records),
        )
        .order_by(Project.created_at.desc())
    )
    projects = db.scalars(stmt).all()

    result = []
    for p in projects:
        p_out = ProjectOut.model_validate(p)
        total_est = 0.0
        for s in p_out.sections:
            sec_tot = sum(it.amount for it in s.items) + sum(d.amount for d in s.duplication_records)
            s.total_amount = sec_tot
            s.items_count = len(s.items) + len(s.duplication_records) + len(s.change_register_records) + len(s.reconciliation_records)
            total_est += sec_tot
        p_out.total_estimate = round(total_est * (1.0 + p.contingency_rate), 2)
        result.append(p_out)
    return result


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Project).where(Project.project_code == payload.project_code.strip()))
    if existing:
        raise HTTPException(status_code=400, detail=f"Project code '{payload.project_code}' already exists.")

    project = Project(
        project_code=payload.project_code.strip(),
        project_name=payload.project_name.strip(),
        project_base_year=payload.project_base_year,
        location=payload.location.strip(),
        description=payload.description.strip() if payload.description else None,
        contingency_rate=payload.contingency_rate,
        vat_status=payload.vat_status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    if current_user:
        log_audit(db, current_user, "CREATE", "PROJECT", str(project.id), f"Created project {project.project_code}")

    return ProjectOut.model_validate(project)


@router.get("/rates/historical-comparison", response_model=HistoricalRateComparisonOut)
def get_historical_rate_comparison(
    master_item_id: int | None = Query(None),
    query: str | None = Query(None),
    base_year: int = Query(2026),
    db: Session = Depends(get_db),
):
    """
    Returns side-by-side historical rates across all available years and rate books.
    """
    return compare_historical_rates(db, master_item_id=master_item_id, query=query, base_year=base_year)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.sections).selectinload(ProjectSection.items),
            selectinload(Project.sections).selectinload(ProjectSection.duplication_records),
            selectinload(Project.sections).selectinload(ProjectSection.change_register_records),
            selectinload(Project.sections).selectinload(ProjectSection.reconciliation_records),
        )
    )
    project = db.scalar(stmt)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    p_out = ProjectOut.model_validate(project)
    total_est = 0.0
    for s in p_out.sections:
        sec_tot = sum(it.amount for it in s.items) + sum(d.amount for d in s.duplication_records)
        s.total_amount = sec_tot
        s.items_count = len(s.items) + len(s.duplication_records) + len(s.change_register_records) + len(s.reconciliation_records)
        total_est += sec_tot
    p_out.total_estimate = round(total_est * (1.0 + project.contingency_rate), 2)
    return p_out


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if payload.project_name is not None:
        project.project_name = payload.project_name.strip()
    if payload.project_base_year is not None:
        project.project_base_year = payload.project_base_year
    if payload.location is not None:
        project.location = payload.location.strip()
    if payload.description is not None:
        project.description = payload.description.strip()
    if payload.status is not None:
        project.status = payload.status.strip()
    if payload.contingency_rate is not None:
        project.contingency_rate = payload.contingency_rate
    if payload.vat_status is not None:
        project.vat_status = payload.vat_status

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.post("/{project_id}/sections", response_model=ProjectSectionOut)
def add_project_section(
    project_id: int,
    payload: ProjectSectionCreate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    sec = ProjectSection(
        project_id=project_id,
        section_code=payload.section_code.strip(),
        section_name=payload.section_name.strip(),
        section_type=payload.section_type.strip(),
        target_sheet=payload.target_sheet.strip() if payload.target_sheet else None,
        sort_order=payload.sort_order,
    )
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return ProjectSectionOut.model_validate(sec)


@router.post("/sections/{section_id}/items", response_model=ProjectItemOut)
def add_project_item(
    section_id: int,
    payload: ProjectItemCreate,
    db: Session = Depends(get_db),
):
    section = db.get(ProjectSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")

    # Calculate amount with adjustment if not given
    rate_val = float(payload.selected_rate or 0.0)
    qty_val = float(payload.quantity or 0.0)
    adj_val = float(payload.adjustment or 0.0)
    computed_amt = payload.amount if payload.amount is not None else round(qty_val * (rate_val + adj_val), 2)

    item = ProjectItem(
        project_section_id=section_id,
        master_item_id=payload.master_item_id,
        bsr_item_id=payload.bsr_item_id,
        item_no=payload.item_no,
        description=payload.description.strip(),
        unit=payload.unit.strip(),
        quantity=qty_val,
        selected_rate=rate_val,
        rate_source_year=str(payload.rate_source_year),  # Strictly separated
        rate_source_book=payload.rate_source_book,
        rate_source_item_code=payload.rate_source_item_code,
        adjustment=adj_val,
        rate_justification=payload.rate_justification,
        amount=computed_amt,
        remarks=payload.remarks,
        sort_order=payload.sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ProjectItemOut.model_validate(item)


@router.put("/items/{item_id}", response_model=ProjectItemOut)
def update_project_item(
    item_id: int,
    payload: ProjectItemUpdate,
    db: Session = Depends(get_db),
):
    item = db.get(ProjectItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Project item not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, val)

    # Recalculate amount if rate or quantity or adjustment changed
    if payload.amount is None:
        item.amount = round(float(item.quantity) * (float(item.selected_rate) + float(item.adjustment)), 2)

    db.commit()
    db.refresh(item)
    return ProjectItemOut.model_validate(item)


@router.delete("/items/{item_id}")
def delete_project_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(ProjectItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Project item not found.")
    db.delete(item)
    db.commit()
    return {"status": "ok", "message": "Project item deleted."}


@router.post("/sections/{section_id}/duplication-records", response_model=DuplicationRecordOut)
def add_duplication_record(
    section_id: int,
    payload: DuplicationRecordCreate,
    db: Session = Depends(get_db),
):
    section = db.get(ProjectSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")

    qty_val = float(payload.qty or 0.0)
    rate_val = float(payload.rate or 0.0)
    amt_val = payload.amount if payload.amount is not None else round(qty_val * rate_val, 2)

    d_rec = DuplicationRecord(
        project_section_id=section_id,
        item=payload.item,
        bsr_ref=payload.bsr_ref,
        description=payload.description.strip(),
        unit=payload.unit.strip(),
        qty=qty_val,
        rate=rate_val,
        amount=amt_val,
        rate_source_year=str(payload.rate_source_year),
        duplicate_with=payload.duplicate_with,
        status=payload.status,
        remarks=payload.remarks,
        sort_order=payload.sort_order,
    )
    db.add(d_rec)
    db.commit()
    db.refresh(d_rec)
    return DuplicationRecordOut.model_validate(d_rec)


@router.post("/sections/{section_id}/change-register-records", response_model=ChangeRegisterRecordOut)
def add_change_register_record(
    section_id: int,
    payload: ChangeRegisterRecordCreate,
    db: Session = Depends(get_db),
):
    section = db.get(ProjectSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")

    c_rec = ChangeRegisterRecord(
        project_section_id=section_id,
        ref_code=payload.ref_code.strip(),
        package_sheet=payload.package_sheet.strip(),
        item_code=payload.item_code,
        description=payload.description.strip(),
        original_status=payload.original_status,
        rev7_action=payload.rev7_action,
        duplicate_with=payload.duplicate_with,
        rate_source=payload.rate_source,
        cost_impact=float(payload.cost_impact or 0.0),
        reason=payload.reason,
        sort_order=payload.sort_order,
    )
    db.add(c_rec)
    db.commit()
    db.refresh(c_rec)
    return ChangeRegisterRecordOut.model_validate(c_rec)


@router.post("/sections/{section_id}/reconciliation-records", response_model=ReconciliationRecordOut)
def add_reconciliation_record(
    section_id: int,
    payload: ReconciliationRecordCreate,
    db: Session = Depends(get_db),
):
    section = db.get(ProjectSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")

    r_rec = ReconciliationRecord(
        project_section_id=section_id,
        scope_element=payload.scope_element.strip(),
        source_boq=payload.source_boq,
        other_package=payload.other_package,
        consolidated_treatment=payload.consolidated_treatment,
        deduction_amount=payload.deduction_amount,
        reason=payload.reason,
        risk=payload.risk,
        tender_action=payload.tender_action,
        is_approved=payload.is_approved,
        sort_order=payload.sort_order,
    )
    db.add(r_rec)
    db.commit()
    db.refresh(r_rec)
    return ReconciliationRecordOut.model_validate(r_rec)


@router.post("/{project_id}/export/excel")
def export_project(
    project_id: int,
    payload: ProjectExportRequest,
    db: Session = Depends(get_db),
):
    """
    Exports project data to Excel:
    - Mode 'consolidated' (Option A): One Excel workbook with each section as a separate worksheet.
    - Mode 'separate' (Option B): Separate Excel file for the selected section.
    """
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.sections).selectinload(ProjectSection.items),
            selectinload(Project.sections).selectinload(ProjectSection.duplication_records),
            selectinload(Project.sections).selectinload(ProjectSection.change_register_records),
            selectinload(Project.sections).selectinload(ProjectSection.reconciliation_records),
        )
    )
    project = db.scalar(stmt)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    tpl = get_or_register_default_template(db)
    excel_stream = export_project_excel(
        project=project,
        mode=payload.mode,
        target_section_id=payload.target_section_id,
        template_path=tpl.file_path,
    )

    if payload.mode == "separate" and payload.target_section_id:
        target_sec = next((s for s in project.sections if s.id == payload.target_section_id), None)
        raw_name = target_sec.section_name if target_sec else "Section"
        sec_slug = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in raw_name)[:30]
        filename = f"{project.project_code}_{sec_slug}.xlsx"
    else:
        filename = f"{project.project_code}_Consolidated_Master_BOQ.xlsx"

    ascii_filename = "".join(c if ord(c) < 128 else "_" for c in filename)
    safe_filename = urllib.parse.quote(filename)
    headers = {
        "Content-Disposition": f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{safe_filename}',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/system/templates", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    get_or_register_default_template(db)
    stmt = select(Template).options(selectinload(Template.mappings)).order_by(Template.created_at)
    templates = db.scalars(stmt).all()
    return [TemplateOut.model_validate(t) for t in templates]
