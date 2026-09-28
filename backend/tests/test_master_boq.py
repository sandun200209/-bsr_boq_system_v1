from __future__ import annotations

import io
import openpyxl
import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import MasterBOQ, MasterBOQItem, RateItem
from app.schemas import (
    MasterBOQCreate,
    MasterBOQItemCreate,
    MasterBOQItemUpdate,
)
from app.services import master_boq_service


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def sample_rate_items(db_session):
    """
    Ensures at least 3 RateItems exist for testing.
    If database already has items (e.g. from BSR/HSR seeds), retrieves 3 of them.
    Otherwise creates 3 mock items.
    """
    existing = list(db_session.scalars(select(RateItem).limit(3)).all())
    if len(existing) >= 3:
        return existing

    # Create dummy rate items for testing if fewer than 3 exist
    items = []
    codes = ["DM01", "EW01", "BK01"]
    descs = [
        "Demolish brick masonry in cement mortar",
        "Excavation in ordinary soil depth up to 1.5m",
        "Brick work 225mm thick in 1:5 cement sand mortar",
    ]
    rates = [500.0, 750.0, 1850.0]

    for i in range(3):
        item = RateItem(
            item_code=codes[i],
            description=descs[i],
            unit="m3" if i != 0 else "m2",
            rate=rates[i],
            rate_system="BSR",
            year=2025,
            revision="Rev 1",
            province="Southern",
            district="Matara",
            source_page=12 + i,
            status="APPROVED",
        )
        db_session.add(item)
        items.append(item)

    db_session.commit()
    for item in items:
        db_session.refresh(item)
    return items


class TestMasterBOQWorkspace:

    def test_create_and_retrieve_master_boq(self, db_session):
        """Test creating an independent Master BOQ workspace and retrieving it."""
        payload = MasterBOQCreate(
            name="Matara Hospital Extension Master BOQ",
            contingency_rate=0.10,
            vat_status="Excluded",
            notes="Tender estimate workspace",
        )
        boq = master_boq_service.create_master_boq(db_session, payload, user_email="qs@example.com")
        assert boq.id is not None
        assert boq.name == "Matara Hospital Extension Master BOQ"
        assert boq.contingency_rate == 0.10
        assert boq.vat_status == "Excluded"
        assert boq.status == "ACTIVE"

        fetched = master_boq_service.get_master_boq(db_session, boq.id)
        assert fetched.id == boq.id
        assert fetched.name == boq.name

    def test_add_rates_to_boq_and_metadata_preservation(self, db_session, sample_rate_items):
        """
        Test adding rate items from Rate Search to the Master BOQ.
        Verifies all provenance metadata (book, code, province/district, page, original rate) are preserved.
        """
        boq = master_boq_service.get_or_create_active_boq(db_session)
        rate_ids = [item.id for item in sample_rate_items]

        added_items, added_count, existing_count = master_boq_service.add_rate_items_to_boq(
            db_session, boq.id, rate_ids
        )

        assert added_count >= 1
        assert len(added_items) == added_count

        # Check first added item preserves source metadata
        first = added_items[0]
        original_source = next(it for it in sample_rate_items if it.id == first.source_rate_item_id)
        assert first.source_code == original_source.item_code
        assert first.original_rate == original_source.rate
        assert first.rate == original_source.rate
        assert first.description == original_source.description
        assert first.unit == original_source.unit

    def test_duplicate_prevention_on_export(self, db_session, sample_rate_items):
        """
        Test that re-exporting already present items avoids accidental duplicate creation.
        """
        boq = master_boq_service.get_or_create_active_boq(db_session)
        rate_ids = [sample_rate_items[0].id]

        # First add (may already exist or add)
        master_boq_service.add_rate_items_to_boq(db_session, boq.id, rate_ids)

        # Second add of the exact same ID
        _, added_count, existing_count = master_boq_service.add_rate_items_to_boq(
            db_session, boq.id, rate_ids
        )
        assert added_count == 0
        assert existing_count == 1

    def test_edit_boq_item_recalculation(self, db_session):
        """
        Test editing quantity and working rate of a BOQ line item.
        Verifies automatic recalculation of amount = quantity * rate.
        """
        boq = master_boq_service.get_or_create_active_boq(db_session)
        assert len(boq.items) > 0
        target_item = boq.items[0]

        # Edit quantity = 15.0 and rate = 650.0
        update_payload = MasterBOQItemUpdate(
            quantity=15.0,
            rate=650.0,
            notes="Adjusted working rate based on market survey",
        )
        updated = master_boq_service.update_boq_item(db_session, boq.id, target_item.id, update_payload)

        assert updated.quantity == 15.0
        assert updated.rate == 650.0
        assert updated.amount == round(15.0 * 650.0, 2)
        assert updated.notes == "Adjusted working rate based on market survey"

    def test_data_safety_original_rate_item_untouched(self, db_session, sample_rate_items):
        """
        CRITICAL DATA SAFETY TEST:
        Verifies that modifying a MasterBOQItem's description, rate, unit, and quantity
        does NOT modify the underlying RateItem in `rate_items`.
        """
        target_rate_item = sample_rate_items[1]
        orig_id = target_rate_item.id
        orig_code = target_rate_item.item_code
        orig_desc = target_rate_item.description
        orig_unit = target_rate_item.unit
        orig_rate = target_rate_item.rate

        # Find or add target_rate_item in active BOQ
        boq = master_boq_service.get_or_create_active_boq(db_session)
        boq_item = next((it for it in boq.items if it.source_rate_item_id == orig_id), None)
        if not boq_item:
            added, _, _ = master_boq_service.add_rate_items_to_boq(db_session, boq.id, [orig_id])
            boq_item = added[0]

        # Mutate the BOQ item completely
        boq_update = MasterBOQItemUpdate(
            description="COMPLETELY DIFFERENT CUSTOM PROJECT DESCRIPTION 999",
            unit="sq.ft",
            quantity=999.0,
            rate=12345.67,
            notes="Modified exclusively in BOQ",
        )
        master_boq_service.update_boq_item(db_session, boq.id, boq_item.id, boq_update)

        # Refresh and inspect the original RateItem from database
        db_session.expire_all()
        refetched_rate_item = db_session.get(RateItem, orig_id)

        assert refetched_rate_item is not None
        assert refetched_rate_item.item_code == orig_code
        assert refetched_rate_item.description == orig_desc
        assert refetched_rate_item.unit == orig_unit
        assert refetched_rate_item.rate == orig_rate
        # Confirm isolation
        assert refetched_rate_item.description != "COMPLETELY DIFFERENT CUSTOM PROJECT DESCRIPTION 999"
        assert refetched_rate_item.rate != 12345.67

    def test_delete_boq_item_data_safety(self, db_session, sample_rate_items):
        """
        Test that deleting an item from the Master BOQ removes it from master_boq_items
        while keeping the original RateItem intact.
        """
        target_rate_item = sample_rate_items[2]
        orig_id = target_rate_item.id

        boq = master_boq_service.get_or_create_active_boq(db_session)
        boq_item = next((it for it in boq.items if it.source_rate_item_id == orig_id), None)
        if not boq_item:
            added, _, _ = master_boq_service.add_rate_items_to_boq(db_session, boq.id, [orig_id])
            boq_item = added[0]

        boq_item_id = boq_item.id

        # Delete from Master BOQ
        deleted = master_boq_service.delete_boq_item(db_session, boq.id, boq_item_id)
        assert deleted is True

        # Verify gone from MasterBOQItem
        assert db_session.get(MasterBOQItem, boq_item_id) is None

        # Verify RateItem is STILL INTACT
        rate_item = db_session.get(RateItem, orig_id)
        assert rate_item is not None
        assert rate_item.id == orig_id

    def test_custom_item_creation(self, db_session):
        """Test adding a custom item directly to the Master BOQ workspace."""
        boq = master_boq_service.get_or_create_active_boq(db_session)
        payload = MasterBOQItemCreate(
            item_no="PS-01",
            description="Provisional sum for testing soil stabilization",
            unit="Item",
            quantity=1.0,
            rate=50000.0,
            notes="Provisional sum",
            is_custom=True,
        )
        custom_item = master_boq_service.add_custom_item_to_boq(db_session, boq.id, payload)

        assert custom_item.id is not None
        assert custom_item.is_custom is True
        assert custom_item.item_no == "PS-01"
        assert custom_item.amount == 50000.0
        assert custom_item.source_rate_item_id is None
        assert custom_item.source_rate_book == "Custom"

    def test_duplicate_boq_item(self, db_session):
        """Test explicitly duplicating a line item within the BOQ."""
        boq = master_boq_service.get_or_create_active_boq(db_session)
        assert len(boq.items) > 0
        original = boq.items[0]

        cloned = master_boq_service.duplicate_boq_item(db_session, boq.id, original.id)
        assert cloned.id != original.id
        assert cloned.description == original.description
        assert cloned.rate == original.rate
        assert cloned.quantity == original.quantity
        assert cloned.amount == original.amount
        assert "(Copy)" in (cloned.item_no or "")

    def test_reorder_boq_items(self, db_session):
        """Test updating the sort orders of BOQ line items."""
        boq = master_boq_service.get_or_create_active_boq(db_session)
        items = boq.items[:2]
        if len(items) >= 2:
            reorder_payload = [
                {"id": items[0].id, "sort_order": 99},
                {"id": items[1].id, "sort_order": 1},
            ]
            master_boq_service.reorder_boq_items(db_session, boq.id, reorder_payload)

            db_session.refresh(items[0])
            db_session.refresh(items[1])
            assert items[0].sort_order == 99
            assert items[1].sort_order == 1

    def test_excel_and_pdf_export(self, db_session):
        """Test exporting Master BOQ to Excel (.xlsx) and PDF."""
        boq = master_boq_service.get_or_create_active_boq(db_session)

        # 1. Excel Export
        excel_bytes = master_boq_service.export_master_boq_excel(boq)
        assert len(excel_bytes) > 1000

        # Verify Excel can be opened with openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
        assert "Master BOQ" in wb.sheetnames
        ws = wb["Master BOQ"]
        assert ws["A1"].value == boq.name.upper()
        assert ws["A4"].value == "Item #"

        # 2. PDF Export
        pdf_bytes = master_boq_service.export_master_boq_pdf(boq)
        assert len(pdf_bytes) > 500
        assert pdf_bytes.startswith(b"%PDF-")
