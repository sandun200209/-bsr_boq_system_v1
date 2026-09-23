import pytest
from sqlalchemy import select, func
from fastapi.testclient import TestClient

import tempfile
from pathlib import Path

from app.main import app
from app.database import SessionLocal
from app.models import (
    RateItem,
    CESMMSection,
    RateItemCESMMSection,
)
from app.services.cesmm_service import (
    seed_cesmm_sections,
    seed_baseline_cesmm_mappings,
    assign_item_cesmm_sections,
    remove_item_cesmm_mapping,
    set_primary_cesmm_mapping,
)
from app.importers.csv_importer import extract_csv


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestCESMMSLClassification:

    def test_01_exactly_31_cesmm_sections_seeded(self, db_session):
        """Rule: Ensure exactly 31 standard CESMM-SL sections (01 to 31) are present."""
        seed_cesmm_sections(db_session)
        sections = db_session.query(CESMMSection).order_by(CESMMSection.section_no).all()
        assert len(sections) == 31, f"Expected 31 CESMM sections, found {len(sections)}"

        section_nos = [s.section_no for s in sections]
        expected_nos = [f"{i:02d}" for i in range(1, 32)]
        assert section_nos == expected_nos

        # Verify key sections
        sec_04 = next(s for s in sections if s.section_no == "04")
        assert sec_04.section_code == "D"
        assert "Demolition" in sec_04.name

        sec_05 = next(s for s in sections if s.section_no == "05")
        assert sec_05.section_code == "E"
        assert "Earth" in sec_05.name

        sec_12 = next(s for s in sections if s.section_no == "12")
        assert sec_12.section_code == "J1"
        assert "Pipe" in sec_12.name

    def test_02_scenario_a_bsr_cesmm04_demolition(self, client):
        """
        Acceptance Scenario A:
        Rate Book = BSR, CESMM = 04 (Demolition and Site Clearance), Category = A-Demolisher
        -> only BSR demolition items.
        """
        response = client.get(
            "/api/rates/search",
            params={
                "rate_system": "BSR",
                "cesmm_section_no": "04",
                "page_size": 25,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["rate_system"] == "BSR"
            # Verify CESMM mapping includes 04
            cesmm_nos = [m["section_no"] for m in item.get("cesmm_sections", [])]
            assert "04" in cesmm_nos

    def test_03_scenario_b_cross_ratebook_cesmm05_earthworks(self, client):
        """
        Acceptance Scenario B:
        Rate Book = All Rate Books, CESMM = 05 (Earthworks)
        -> returns earthwork items across both BSR and HSR books.
        """
        response = client.get(
            "/api/rates/search",
            params={
                "cesmm_section_no": "05",
                "page_size": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

        rate_systems_found = {item["rate_system"] for item in data["items"]}
        # Both BSR and HSR records should be mapped under Earthworks (CESMM 05)
        assert "BSR" in rate_systems_found
        assert "HSR" in rate_systems_found

        for item in data["items"]:
            cesmm_nos = [m["section_no"] for m in item.get("cesmm_sections", [])]
            assert "05" in cesmm_nos

    def test_04_scenario_c_water_cesmm12_pipework(self, client):
        """
        Acceptance Scenario C:
        Rate Book = Water, CESMM = 12 (Pipework - Pipes)
        -> returns relevant Water pipe records.
        """
        response = client.get(
            "/api/rates/search",
            params={
                "rate_system": "Water",
                "cesmm_section_no": "12",
                "page_size": 25,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert "Water" in (item.get("rate_system") or "") or "Water" in (item.get("sector") or "")
            cesmm_nos = [m["section_no"] for m in item.get("cesmm_sections", [])]
            assert "12" in cesmm_nos

    def test_05_scenario_d_cesmm_all_legacy_unmapped_items(self, client, db_session):
        """
        Acceptance Scenario D:
        CESMM = All (no cesmm_section_no param)
        -> legacy unmapped items continue to appear normally.
        Total items in database must not decrease.
        """
        response = client.get(
            "/api/rates/search",
            params={"page_size": 25},
        )
        assert response.status_code == 200
        data = response.json()
        total_api = data["total"]

        total_db = db_session.query(func.count(RateItem.id)).scalar()
        assert total_api == total_db
        assert total_db >= 5000

        # Unmapped items exist and are included
        unmapped_items = [it for it in data["items"] if len(it.get("cesmm_sections", [])) == 0]
        assert len(unmapped_items) > 0, "Unmapped items should appear when CESMM Section = All"

    def test_06_no_duplicate_rows_on_multiple_mappings(self, client, db_session):
        """
        Duplicate Prevention Rule:
        An item classified under multiple CESMM sections must NOT produce duplicate rows
        in rate search queries.
        """
        # Find or pick an item
        item = db_session.query(RateItem).first()
        assert item is not None

        sec01 = db_session.query(CESMMSection).filter_by(section_no="01").first()
        sec02 = db_session.query(CESMMSection).filter_by(section_no="02").first()

        # Assign both sec01 and sec02 to this item
        assign_item_cesmm_sections(
            db_session,
            item.id,
            [
                {"cesmm_section_id": sec01.id, "is_primary": True},
                {"cesmm_section_id": sec02.id, "is_primary": False},
            ],
        )

        # Search for section 01
        res = client.get(
            "/api/rates/search",
            params={"cesmm_section_no": "01", "page_size": 100},
        )
        assert res.status_code == 200
        items = res.json()["items"]
        item_ids = [it["id"] for it in items]
        assert item_ids.count(item.id) == 1, "Item must not appear multiple times in search results"

    def test_07_primary_mapping_management(self, db_session):
        """
        Primary Flag Rule:
        Only one section should be marked primary when requested, and setting primary
        must properly update flags.
        """
        item = db_session.query(RateItem).filter_by(item_code="A004").first()
        if not item:
            item = db_session.query(RateItem).first()

        sec04 = db_session.query(CESMMSection).filter_by(section_no="04").first()
        sec08 = db_session.query(CESMMSection).filter_by(section_no="08").first()

        # Assign both with sec04 as primary
        assign_item_cesmm_sections(
            db_session,
            item.id,
            [
                {"cesmm_section_id": sec04.id, "is_primary": True},
                {"cesmm_section_id": sec08.id, "is_primary": False},
            ],
        )

        mappings = db_session.query(RateItemCESMMSection).filter_by(rate_item_id=item.id).all()
        primary_map = next(m for m in mappings if m.cesmm_section_id == sec04.id)
        assert primary_map.is_primary is True

        # Switch primary to sec08
        set_primary_cesmm_mapping(db_session, item.id, sec08.id)

        db_session.expire_all()
        mappings = db_session.query(RateItemCESMMSection).filter_by(rate_item_id=item.id).all()
        sec08_map = next(m for m in mappings if m.cesmm_section_id == sec08.id)
        sec04_map = next(m for m in mappings if m.cesmm_section_id == sec04.id)

        assert sec08_map.is_primary is True
        assert sec04_map.is_primary is False

    def test_08_remove_mapping(self, db_session):
        """Verify removing a CESMM mapping cleanly deletes only the specified link."""
        item = db_session.query(RateItem).first()
        sec02 = db_session.query(CESMMSection).filter_by(section_no="02").first()

        # Ensure sec02 is assigned
        assign_item_cesmm_sections(
            db_session,
            item.id,
            [{"cesmm_section_id": sec02.id, "is_primary": False}],
        )
        assert db_session.query(RateItemCESMMSection).filter_by(
            rate_item_id=item.id, cesmm_section_id=sec02.id
        ).first() is not None

        # Remove sec02 mapping
        remove_item_cesmm_mapping(db_session, item.id, sec02.id)

        assert db_session.query(RateItemCESMMSection).filter_by(
            rate_item_id=item.id, cesmm_section_id=sec02.id
        ).first() is None

    def test_09_filter_options_endpoint_includes_cesmm(self, client):
        """Verify /api/rates/filters returns all 31 CESMM sections."""
        res = client.get("/api/rates/filters")
        assert res.status_code == 200
        data = res.json()
        assert "cesmm_sections" in data
        assert len(data["cesmm_sections"]) == 31
        first = data["cesmm_sections"][0]
        assert "section_no" in first
        assert "section_code" in first
        assert "name" in first

    def test_10_csv_importer_extracts_cesmm_columns(self):
        """Verify importer parses optional CESMM Section No and Code headers."""
        csv_content = (
            "Item Code,Description,Unit,Rate,Rate System,CESMM Section No,CESMM Section Code\n"
            "TEST-01,Demolish brick wall,m3,1500.00,BSR,04,D\n"
            "TEST-02,Excavate trench,m3,850.00,HSR,05,E\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tf:
            tf.write(csv_content)
            temp_path = Path(tf.name)

        try:
            items = extract_csv(temp_path)
            assert len(items) == 2

            item1 = items[0]
            assert item1.item_code == "TEST-01"
            assert item1.cesmm_section_no == "04"
            assert item1.cesmm_section_code == "D"

            item2 = items[1]
            assert item2.item_code == "TEST-02"
            assert item2.cesmm_section_no == "05"
            assert item2.cesmm_section_code == "E"
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_11_cascading_filters_flow(self, client):
        """
        Strict Cascading Filter Flow Rule:
        1. Rate Book first.
        2. Year depends on Rate Book.
        3. Province depends on Year.
        4. District depends on Province.
        5. CESMM section depends on District + prior selections.
        6. Category depends on CESMM Section + prior selections.
        7. Revision depends on Category.
        8. VAT basis depends on Revision.
        9. Status and matching records cascade cleanly.
        """
        # Step 1: Base options
        res_base = client.get("/api/rates/filters")
        assert res_base.status_code == 200
        data_base = res_base.json()
        assert "BSR" in data_base["rate_systems"]
        assert "HSR" in data_base["rate_systems"]

        # Step 2: Rate Book = BSR -> Years
        res_bsr = client.get("/api/rates/filters", params={"rate_system": "BSR"})
        assert res_bsr.status_code == 200
        assert 2023 in res_bsr.json()["years"]

        # Step 3: BSR + Year 2023 -> Provinces
        res_prov = client.get("/api/rates/filters", params={"rate_system": "BSR", "year": 2023})
        assert res_prov.status_code == 200
        assert "All Provinces" in res_prov.json()["provinces"]

        # Step 4: + Province 'All Provinces' -> Districts
        res_dist = client.get(
            "/api/rates/filters",
            params={"rate_system": "BSR", "year": 2023, "province": "All Provinces"},
        )
        assert res_dist.status_code == 200
        assert "National / All Island" in res_dist.json()["districts"]

        # Step 5: + District 'National / All Island' -> CESMM Sections
        res_cesmm = client.get(
            "/api/rates/filters",
            params={
                "rate_system": "BSR",
                "year": 2023,
                "province": "All Provinces",
                "district": "National / All Island",
            },
        )
        assert res_cesmm.status_code == 200
        sec_nos = [s["section_no"] for s in res_cesmm.json()["cesmm_sections"]]
        assert "05" in sec_nos  # Earth works

        # Step 6: + CESMM Section '05' -> Categories
        res_cat = client.get(
            "/api/rates/filters",
            params={
                "rate_system": "BSR",
                "year": 2023,
                "province": "All Provinces",
                "district": "National / All Island",
                "cesmm_section_no": "05",
            },
        )
        assert res_cat.status_code == 200
        cats = res_cat.json()["categories"]
        assert "B-EXCAVATOR" in cats

        # Step 7: + Category 'B-EXCAVATOR' -> Revisions
        res_rev = client.get(
            "/api/rates/filters",
            params={
                "rate_system": "BSR",
                "year": 2023,
                "province": "All Provinces",
                "district": "National / All Island",
                "cesmm_section_no": "05",
                "category": "B-EXCAVATOR",
            },
        )
        assert res_rev.status_code == 200
        assert "Original" in res_rev.json()["revisions"]

        # Step 8: + Revision 'Original' -> VAT basis & Total matching
        res_vat = client.get(
            "/api/rates/filters",
            params={
                "rate_system": "BSR",
                "year": 2023,
                "province": "All Provinces",
                "district": "National / All Island",
                "cesmm_section_no": "05",
                "category": "B-EXCAVATOR",
                "revision": "Original",
            },
        )
        assert res_vat.status_code == 200
        assert "Not Applicable" in res_vat.json()["vat_bases"]
        assert res_vat.json()["total_matching"] == 15

        # Test alias route /filter-options
        res_alias = client.get("/api/rates/filter-options", params={"rate_system": "BSR"})
        assert res_alias.status_code == 200
        assert res_alias.json()["years"] == res_bsr.json()["years"]

