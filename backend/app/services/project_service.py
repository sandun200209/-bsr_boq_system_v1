from __future__ import annotations
import json
import math
from datetime import datetime
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Project,
    ProjectSection,
    ProjectItem,
    DuplicationRecord,
    ChangeRegisterRecord,
    ReconciliationRecord,
    MasterItem,
    RateItem,
    RateItemMasterMapping,
    Template,
    TemplateMapping,
)
from ..schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectSectionCreate,
    ProjectSectionUpdate,
    ProjectItemCreate,
    ProjectItemUpdate,
    DuplicationRecordCreate,
    ChangeRegisterRecordCreate,
    ReconciliationRecordCreate,
    HistoricalRateComparisonOut,
    HistoricalRateEntry,
)

def get_or_create_default_project(db: Session) -> Project:
    """
    Ensures the reference project MATARA-OT-REV7 exists with all standard sections,
    including the separate Site Works Duplication and REV 7 Change Register datasets.
    """
    proj = db.scalar(
        select(Project)
        .where(Project.project_code == "MATARA-OT-REV7")
        .options(
            selectinload(Project.sections).selectinload(ProjectSection.items),
            selectinload(Project.sections).selectinload(ProjectSection.duplication_records),
            selectinload(Project.sections).selectinload(ProjectSection.change_register_records),
            selectinload(Project.sections).selectinload(ProjectSection.reconciliation_records),
        )
    )
    if proj:
        return proj

    proj = Project(
        project_code="MATARA-OT-REV7",
        project_name="DGH Matara - Operating Theatre Renovation & Consolidation",
        project_base_year=2026,
        location="District General Hospital Matara, Southern Province",
        description="Comprehensive consolidation estimate, duplication review, and rate basis alignment.",
        status="IN_REVIEW",
        contingency_rate=0.10,
        vat_status="Excluded",
    )
    db.add(proj)
    db.flush()

    # Define standard sections
    sections_def = [
        ("SEC-DEMO", "Preparatory & Demolition Works", "BOQ", "Added Renovation BOQ", 1),
        ("SEC-CIVIL", "Civil Renovation Works", "BOQ", "Added Renovation BOQ", 2),
        ("SEC-ELEC", "Electrical BOQ - Reviewed", "BOQ", "Electrical BOQ - Reviewed", 3),
        ("SEC-MVAC", "MVAC BOQ & Estimate", "BOQ", "MVAC BOQ & Estimate", 4),
        ("SEC-WATER", "Water Supply BOQ & Estimate", "BOQ", "Water Supply BOQ & Estimate", 5),
        ("SEC-SITE-DUP", "MATARA OT RENOVATION – SITE WORKS BOQ REVIEWED FOR DUPLICATION", "DUPLICATION", "Site Works - Reviewed", 6),
        ("SEC-REV7-REG", "REV 7 CONSOLIDATION CHANGE / DUPLICATION REGISTER", "CHANGE_REGISTER", "Consolidation Change Register", 7),
        ("SEC-ELEC-REC", "Electrical Scope Reconciliation", "RECONCILIATION", "Electrical Reconciliation", 8),
    ]

    sec_map = {}
    for code, name, stype, target_sheet, s_order in sections_def:
        sec = ProjectSection(
            project_id=proj.id,
            section_code=code,
            section_name=name,
            section_type=stype,
            target_sheet=target_sheet,
            sort_order=s_order,
        )
        db.add(sec)
        db.flush()
        sec_map[code] = sec

    # Seed sample BOQ items demonstrating separate rate source year vs project base year (2026)
    demo_sec = sec_map["SEC-DEMO"]
    db.add(
        ProjectItem(
            project_section_id=demo_sec.id,
            item_no="1",
            description="Demolishing brickwork in cement stacking brick and clearing debris away",
            unit="Cube",
            quantity=8.5,
            selected_rate=3905.0,
            rate_source_year="2026",
            rate_source_book="BSR Southern 2026",
            rate_source_item_code="A001",
            adjustment=0.0,
            rate_justification="Standard 2026 Southern BSR approved rate",
            amount=8.5 * 3905.0,
            remarks="Ground floor demolition corridor",
            sort_order=1,
        )
    )
    db.add(
        ProjectItem(
            project_section_id=demo_sec.id,
            item_no="2",
            description="Demolishing cabook masonry in lime mortar stacking cabook and clearing away",
            unit="Cube",
            quantity=4.0,
            selected_rate=2570.0,
            rate_source_year="2023",  # Past year explicitly selected by user!
            rate_source_book="BSR Southern 2023",
            rate_source_item_code="A003",
            adjustment=15.0,  # 15% escalation
            rate_justification="2023 Southern rate adopted with +15% regional escalation adjustment",
            amount=4.0 * (2570.0 * 1.15),
            remarks="Adopted from 2023 schedule as 2026 code was non-delineated",
            sort_order=2,
        )
    )

    # Seed Site Works Duplication items
    site_sec = sec_map["SEC-SITE-DUP"]
    site_dup_items = [
        ("1", "A. Preliminaries", "Protection to live hospital, barricading, dust/noise control, temporary access and housekeeping", "Item", 1.0, 250000.0, 250000.0, "2026", "None", "RETAIN", "Reviewed direct hospital protection preliminaries"),
        ("2", "B. Earthwork", "Excavation for new ramp and walkway foundation including backfilling and compaction", "m3", 45.0, 1850.0, 83250.0, "2026", "Added Renovation B2", "REDUCE", "Overlapped with general contractor excavation by 15 m3"),
        ("3", "C. Landscaping", "Turfing and tree relocation around OT entrance perimeter", "m2", 120.0, 650.0, 78000.0, "2023", "Site Works Unchanged C1", "DEDUCT", "Duplicate of landscape maintenance package"),
    ]
    for idx, (item_val, bsr_ref_val, desc_val, u_val, q_val, r_val, amt_val, yr_val, dup_val, st_val, rem_val) in enumerate(site_dup_items, start=1):
        db.add(
            DuplicationRecord(
                project_section_id=site_sec.id,
                item=item_val,
                bsr_ref=bsr_ref_val,
                description=desc_val,
                unit=u_val,
                qty=q_val,
                rate=r_val,
                amount=amt_val,
                rate_source_year=yr_val,
                duplicate_with=dup_val,
                status=st_val,
                remarks=rem_val,
                sort_order=idx,
            )
        )

    # Seed REV 7 Change / Duplication Register items
    reg_sec = sec_map["SEC-REV7-REG"]
    change_items = [
        ("CR-01", "Electrical", "E-01", "40 OT light points + 40 Type 1 luminaires overlap Modular OT C6", "Source subtotal LKR 21,039,600", "Reduce electrical quantities", "Modular OT C6 quantity = 40", "BSR 2026", 1080000.0, "Modular OT package includes specialized surgical cleanroom lighting", 1),
        ("CR-02", "Site Works", "SW-03", "Excavation and backfilling perimeter drainage", "Site Works Original LKR 1,450,000", "Reduce civil drainage overlaps", "Civil Renovation D3", "BSR 2023", 220000.0, "Avoid double-counting trench excavation across civil and site works contracts", 2),
        ("CR-03", "MVAC", "M-14", "Duct insulation overlap with acoustic plenum lining", "MVAC BOQ LKR 14,890,000", "Deduct duplicate acoustic wrap", "Architectural Finishes F2", "Market Rate", 345000.0, "Specified by MEP engineer and architectural interior acoustic schedule simultaneously", 3),
    ]
    for ref_val, pkg_val, code_val, desc_val, orig_val, act_val, dup_val, src_val, cost_val, rsn_val, ord_val in change_items:
        db.add(
            ChangeRegisterRecord(
                project_section_id=reg_sec.id,
                ref_code=ref_val,
                package_sheet=pkg_val,
                item_code=code_val,
                description=desc_val,
                original_status=orig_val,
                rev7_action=act_val,
                duplicate_with=dup_val,
                rate_source=src_val,
                cost_impact=cost_val,
                reason=rsn_val,
                sort_order=ord_val,
            )
        )

    # Seed Reconciliation items
    rec_sec = sec_map["SEC-ELEC-REC"]
    rec_items = [
        ("OT cleanroom lighting points", "Electrical BOQ Item 1-2", "Modular OT package C6", "Reduced electrical quantity by 40 units", "1,080,000.00", "Avoid double-counting with specialized surgical ceiling luminaires", "Low", "Issue addendum clarifying demarcation line between general and specialist contractor", True, 1),
        ("Medical gas emergency power cabling", "Electrical BOQ Item 14", "Medical Gas Package MG-08", "Retained under electrical package only", "0.00", "Medical gas contractor only supplies manifold; primary feed belongs to electrical", "Medium", "Confirm feeder cable route with hospital electrical engineer", True, 2),
    ]
    for scope_val, src_val, oth_val, trt_val, ded_val, rsn_val, rsk_val, act_val, app_val, ord_val in rec_items:
        db.add(
            ReconciliationRecord(
                project_section_id=rec_sec.id,
                scope_element=scope_val,
                source_boq=src_val,
                other_package=oth_val,
                consolidated_treatment=trt_val,
                deduction_amount=ded_val,
                reason=rsn_val,
                risk=rsk_val,
                tender_action=act_val,
                is_approved=app_val,
                sort_order=ord_val,
            )
        )

    db.commit()
    db.refresh(proj)
    return proj


def compare_historical_rates(
    db: Session,
    master_item_id: int | None = None,
    query: str | None = None,
    base_year: int = 2026,
) -> HistoricalRateComparisonOut:
    """
    For one selected master item (or keyword), fetches all available years and rate books side-by-side.
    Allows user to explicitly select which year's rate to use.
    """
    matched_master = None
    if master_item_id:
        matched_master = db.get(MasterItem, master_item_id)

    stmt = select(RateItem).join(RateItem.source_file, isouter=True)

    if matched_master:
        # Check mapping table and master_item_id
        stmt = stmt.where(
            or_(
                RateItem.master_item_id == matched_master.id,
                RateItem.description.ilike(f"%{matched_master.canonical_description[:30]}%"),
                RateItem.item_code == matched_master.master_code,
            )
        )
    elif query and query.strip():
        q_term = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                RateItem.item_code.ilike(q_term),
                RateItem.description.ilike(q_term),
                RateItem.category_name.ilike(q_term),
            )
        )
    else:
        # Default first 30 rates with diverse years
        pass

    rate_rows = db.scalars(stmt.order_by(RateItem.year.desc(), RateItem.province).limit(100)).all()

    rates_by_year: dict[str, list[HistoricalRateEntry]] = {}
    all_entries: list[HistoricalRateEntry] = []
    rates_vals: list[float] = []

    for r in rate_rows:
        if r.rate is not None and r.rate > 0:
            rates_vals.append(r.rate)
            yr_key = str(r.year)
            entry = HistoricalRateEntry(
                year=r.year,
                province=r.province,
                district=r.district,
                book_title=r.source_file.original_filename if r.source_file else f"{r.province} BSR {r.year}",
                item_code=r.item_code or "-",
                description=r.description or "",
                unit=r.unit or "Item",
                rate=r.rate,
                rate_item_id=r.id,
            )
            if yr_key not in rates_by_year:
                rates_by_year[yr_key] = []
            rates_by_year[yr_key].append(entry)
            all_entries.append(entry)

    avg_r = sum(rates_vals) / len(rates_vals) if rates_vals else 0.0
    min_r = min(rates_vals) if rates_vals else 0.0
    max_r = max(rates_vals) if rates_vals else 0.0

    # Calculate variance from average for each entry
    for entry in all_entries:
        if avg_r > 0:
            entry.variance_pct = round(((entry.rate - avg_r) / avg_r) * 100.0, 1)

    return HistoricalRateComparisonOut(
        master_item_id=matched_master.id if matched_master else None,
        master_code=matched_master.master_code if matched_master else None,
        canonical_description=matched_master.canonical_description if matched_master else (query or "All Historical BSR Rates"),
        canonical_unit=matched_master.canonical_unit if matched_master else "Item",
        project_base_year=base_year,
        rates_by_year=rates_by_year,
        all_rates=all_entries,
        average_rate=round(avg_r, 2),
        min_rate=round(min_r, 2),
        max_rate=round(max_r, 2),
    )
