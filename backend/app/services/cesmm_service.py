from __future__ import annotations
import logging
from datetime import datetime
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session, selectinload, joinedload

from ..models import CESMMSection, RateItemCESMMSection, RateItem
from ..schemas import RateItemCESMMOut

logger = logging.getLogger("bsr_rate_hub.cesmm")

# Exact 31 CESMM-SL (Sri Lanka) Work Sections
CESMM_SL_31_SECTIONS = [
    {"section_no": "01", "section_code": "A", "name": "Preliminaries"},
    {"section_no": "02", "section_code": "B", "name": "Ground investigation"},
    {"section_no": "03", "section_code": "C", "name": "Geotechnical and other specialist processes"},
    {"section_no": "04", "section_code": "D", "name": "Demolition and site clearance"},
    {"section_no": "05", "section_code": "E", "name": "Earth works"},
    {"section_no": "06", "section_code": "F", "name": "Dredging and reclamation"},
    {"section_no": "07", "section_code": "G", "name": "Landscaping and irrigation"},
    {"section_no": "08", "section_code": "H1", "name": "Concrete work - Insitu concrete"},
    {"section_no": "09", "section_code": "H2", "name": "Concrete work - Form work"},
    {"section_no": "10", "section_code": "H3", "name": "Concrete work - Reinforcement"},
    {"section_no": "11", "section_code": "H4", "name": "Concrete work - Precast concrete"},
    {"section_no": "12", "section_code": "J1", "name": "Pipe work - Pipes"},
    {"section_no": "13", "section_code": "J2", "name": "Pipe work - Fittings"},
    {"section_no": "14", "section_code": "J3", "name": "Pipe work - Valves and miscellaneous work"},
    {"section_no": "15", "section_code": "J4", "name": "Pipe work - Manholes and pipe work ancillaries"},
    {"section_no": "16", "section_code": "J5", "name": "Pipe work - Supports and protection, ancillaries to laying and excavation"},
    {"section_no": "17", "section_code": "K", "name": "Structural metalwork"},
    {"section_no": "18", "section_code": "L", "name": "Miscellaneous metalwork"},
    {"section_no": "19", "section_code": "M", "name": "Timber"},
    {"section_no": "20", "section_code": "N1", "name": "Piling work - Piling"},
    {"section_no": "21", "section_code": "N2", "name": "Piling work - Diaphragm walling"},
    {"section_no": "22", "section_code": "N3", "name": "Piling work - Underpinning"},
    {"section_no": "23", "section_code": "P", "name": "Roads and paving"},
    {"section_no": "24", "section_code": "Q", "name": "Rail track"},
    {"section_no": "25", "section_code": "R", "name": "Tunnels"},
    {"section_no": "26", "section_code": "S", "name": "Brickwork, block work and masonry"},
    {"section_no": "27", "section_code": "T", "name": "Painting"},
    {"section_no": "28", "section_code": "U", "name": "Waterproofing"},
    {"section_no": "29", "section_code": "V", "name": "Miscellaneous work"},
    {"section_no": "30", "section_code": "W", "name": "Sewer and water main renovation and ancillary works"},
    {"section_no": "31", "section_code": "X", "name": "Simple building works incidental to civil engineering works"},
]

def seed_cesmm_sections(db: Session) -> list[CESMMSection]:
    """
    Seeds the 31 standard CESMM-SL Work Sections into the database if not present.
    Also maps initial baseline items across BSR, HSR, and Water to verify acceptance criteria.
    """
    existing_sections = {s.section_no: s for s in db.scalars(select(CESMMSection)).all()}
    created = 0

    for s_data in CESMM_SL_31_SECTIONS:
        sec_no = s_data["section_no"]
        if sec_no not in existing_sections:
            sec = CESMMSection(
                section_no=sec_no,
                section_code=s_data["section_code"],
                name=s_data["name"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(sec)
            created += 1

    if created > 0:
        db.commit()
        logger.info(f"Seeded {created} CESMM-SL work sections into the database.")

    # Refresh sections map
    all_sections = {s.section_no: s for s in db.scalars(select(CESMMSection).order_by(CESMMSection.section_no)).all()}

    # Baseline seed mappings for testing & immediate usability
    seed_baseline_cesmm_mappings(db, all_sections)

    return list(all_sections.values())


def seed_baseline_cesmm_mappings(db: Session, sections_by_no: dict[str, CESMMSection]):
    """
    Ensures key benchmark records in BSR, HSR, and Water Supply have appropriate
    CESMM mappings for Scenario A (04), Scenario B (05), Scenario C (12), Scenario 3 (08).
    """
    sec_04 = sections_by_no.get("04")  # Demolition and site clearance
    sec_05 = sections_by_no.get("05")  # Earth works
    sec_08 = sections_by_no.get("08")  # Concrete work - Insitu concrete
    sec_12 = sections_by_no.get("12")  # Pipe work - Pipes
    sec_26 = sections_by_no.get("26")  # Brickwork, block work and masonry

    if not sec_04 or not sec_05:
        return

    # Check if mappings already exist
    existing_count = db.scalar(select(RateItemCESMMSection.id).limit(1))
    if existing_count:
        return  # Already seeded or customized by user

    # 1. BSR Demolisher items -> CESMM 04 (Demolition and site clearance)
    if sec_04:
        bsr_demo_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system == "BSR",
                RateItem.category_name.ilike("%demolish%"),
            )
            .limit(20)
        ).all()
        for item in bsr_demo_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_04.id, is_primary=True))

    # 2. BSR Excavator & Earthwork items -> CESMM 05 (Earth works)
    if sec_05:
        bsr_excav_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system == "BSR",
                RateItem.category_name.ilike("%excavat%"),
            )
            .limit(20)
        ).all()
        for item in bsr_excav_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_05.id, is_primary=True))

    # 3. HSR Earthwork items -> CESMM 05 (Earth works)
    if sec_05:
        hsr_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system == "HSR",
                RateItem.item_code.in_(["H-EW01", "H-EW02"]),
            )
        ).all()
        for item in hsr_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_05.id, is_primary=True))

    # 4. BSR Concreter items -> CESMM 08 (Concrete work - Insitu concrete)
    if sec_08:
        bsr_concrete_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system == "BSR",
                RateItem.category_name.ilike("%concreter%"),
            )
            .limit(20)
        ).all()
        for item in bsr_concrete_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_08.id, is_primary=True))

    # 5. Water Supply pipe items -> CESMM 12 (Pipe work - Pipes)
    if sec_12:
        water_pipe_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system.ilike("%water%"),
                RateItem.description.ilike("%pipe%"),
            )
            .limit(10)
        ).all()
        for item in water_pipe_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_12.id, is_primary=True))

    # 6. BSR Brickwork items -> CESMM 26 (Brickwork, block work and masonry)
    if sec_26:
        bsr_brick_items = db.scalars(
            select(RateItem)
            .where(
                RateItem.rate_system == "BSR",
                RateItem.category_name.ilike("%brick%"),
            )
            .limit(20)
        ).all()
        for item in bsr_brick_items:
            db.add(RateItemCESMMSection(rate_item_id=item.id, cesmm_section_id=sec_26.id, is_primary=True))

    db.commit()
    logger.info("Successfully initialized baseline CESMM-SL mappings.")


def get_all_cesmm_sections(db: Session, active_only: bool = True) -> list[CESMMSection]:
    """Returns all 31 CESMM sections ordered by section_no."""
    query = select(CESMMSection).order_by(CESMMSection.section_no)
    if active_only:
        query = query.where(CESMMSection.is_active == True)
    return list(db.scalars(query).all())


def get_item_cesmm_mappings(db: Session, rate_item_id: int) -> list[RateItemCESMMOut]:
    """Returns all assigned CESMM sections for a rate item, primary first."""
    mappings = db.scalars(
        select(RateItemCESMMSection)
        .where(RateItemCESMMSection.rate_item_id == rate_item_id)
        .options(joinedload(RateItemCESMMSection.cesmm_section))
        .order_by(RateItemCESMMSection.is_primary.desc(), RateItemCESMMSection.id.asc())
    ).all()

    results = []
    for m in mappings:
        if m.cesmm_section:
            results.append(
                RateItemCESMMOut(
                    id=m.id,
                    cesmm_section_id=m.cesmm_section_id,
                    section_no=m.cesmm_section.section_no,
                    section_code=m.cesmm_section.section_code,
                    name=m.cesmm_section.name,
                    is_primary=m.is_primary,
                )
            )
    return results


def assign_item_cesmm_sections(
    db: Session,
    rate_item_id: int,
    section_ids: list[int],
    primary_section_id: int | None = None,
) -> list[RateItemCESMMOut]:
    """
    Replaces or sets CESMM mappings for a rate item without altering original category or rate book.
    """
    # Verify rate item exists
    item = db.get(RateItem, rate_item_id)
    if not item:
        raise ValueError(f"RateItem {rate_item_id} not found")

    # Remove existing mappings
    db.execute(
        delete(RateItemCESMMSection).where(RateItemCESMMSection.rate_item_id == rate_item_id)
    )

    # Normalize entries into (sec_id, is_primary)
    parsed_entries: list[tuple[int, bool]] = []
    for entry in section_ids:
        if isinstance(entry, int):
            parsed_entries.append((entry, False))
        elif isinstance(entry, dict):
            sec_id = entry.get("cesmm_section_id") or entry.get("id")
            is_pri = bool(entry.get("is_primary", False))
            if sec_id:
                parsed_entries.append((int(sec_id), is_pri))
        elif hasattr(entry, "cesmm_section_id"):
            sec_id = getattr(entry, "cesmm_section_id")
            is_pri = bool(getattr(entry, "is_primary", False))
            if sec_id:
                parsed_entries.append((int(sec_id), is_pri))

    # If primary_section_id is given explicitly, override
    if primary_section_id is not None:
        parsed_entries = [(sid, sid == primary_section_id) for sid, _ in parsed_entries]
    elif parsed_entries and not any(is_pri for _, is_pri in parsed_entries):
        # Default the first one to primary
        first_sid, _ = parsed_entries[0]
        parsed_entries[0] = (first_sid, True)

    seen: set[int] = set()
    for sec_id, is_pri in parsed_entries:
        if sec_id in seen:
            continue
        seen.add(sec_id)
        sec = db.get(CESMMSection, sec_id)
        if not sec:
            continue
        mapping = RateItemCESMMSection(
            rate_item_id=rate_item_id,
            cesmm_section_id=sec_id,
            is_primary=is_pri,
            created_at=datetime.utcnow(),
        )
        db.add(mapping)

    db.commit()
    return get_item_cesmm_mappings(db, rate_item_id)


def remove_item_cesmm_mapping(
    db: Session,
    rate_item_id: int,
    cesmm_section_id: int,
) -> list[RateItemCESMMOut]:
    """Removes a single CESMM mapping from a rate item."""
    db.execute(
        delete(RateItemCESMMSection).where(
            and_(
                RateItemCESMMSection.rate_item_id == rate_item_id,
                RateItemCESMMSection.cesmm_section_id == cesmm_section_id,
            )
        )
    )
    db.commit()

    # If removed was primary, designate remaining first as primary
    remaining = db.scalars(
        select(RateItemCESMMSection)
        .where(RateItemCESMMSection.rate_item_id == rate_item_id)
        .order_by(RateItemCESMMSection.id.asc())
    ).all()
    if remaining and not any(r.is_primary for r in remaining):
        remaining[0].is_primary = True
        db.commit()

    return get_item_cesmm_mappings(db, rate_item_id)


def set_primary_cesmm_mapping(
    db: Session,
    rate_item_id: int,
    cesmm_section_id: int,
) -> list[RateItemCESMMOut]:
    """Designates one assigned CESMM section as primary."""
    mappings = db.scalars(
        select(RateItemCESMMSection).where(RateItemCESMMSection.rate_item_id == rate_item_id)
    ).all()
    found = False
    for m in mappings:
        if m.cesmm_section_id == cesmm_section_id:
            m.is_primary = True
            found = True
        else:
            m.is_primary = False
    if not found:
        raise ValueError(f"Mapping between RateItem {rate_item_id} and CESMMSection {cesmm_section_id} does not exist.")
    db.commit()
    return get_item_cesmm_mappings(db, rate_item_id)
