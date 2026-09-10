from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    province: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revision: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dataset_type: Mapped[str] = mapped_column(String(80), default="BSR Rate Book", index=True)
    vat_basis: Mapped[str] = mapped_column(String(80), default="Without VAT", index=True)
    category_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sector: Mapped[str] = mapped_column(String(100), default="Building Works", server_default="Building Works", index=True)
    rate_system: Mapped[str] = mapped_column(String(100), default="BSR", server_default="BSR", index=True)

    upload_status: Mapped[str] = mapped_column(String(40), default="UPLOADED", index=True)
    import_status: Mapped[str] = mapped_column(String(40), default="READY_FOR_REVIEW", index=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    total_rows_detected: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    review_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    rate_items: Mapped[list["RateItem"]] = relationship(
        back_populates="source_file", cascade="all, delete-orphan"
    )
    import_jobs: Mapped[list["ImportJob"]] = relationship(
        back_populates="source_file", cascade="all, delete-orphan"
    )

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_file_id: Mapped[int] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(40), default="UPLOADED", index=True
    )  # UPLOADED, PROCESSING, READY_FOR_REVIEW, COMPLETED, FAILED
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    source_file: Mapped["SourceFile"] = relationship(back_populates="import_jobs")

class MasterItem(Base):
    __tablename__ = "master_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    canonical_description: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_unit: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    sector: Mapped[str] = mapped_column(String(100), default="Building Works", server_default="Building Works", index=True)
    rate_system: Mapped[str | None] = mapped_column(String(100), default="BSR", server_default="BSR", nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    mappings: Mapped[list["RateItemMasterMapping"]] = relationship(
        back_populates="master_item", cascade="all, delete-orphan"
    )

class RateItem(Base):
    __tablename__ = "rate_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_file_id: Mapped[int] = mapped_column(
        ForeignKey("source_files.id", ondelete="CASCADE"), index=True
    )

    province: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revision: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dataset_type: Mapped[str] = mapped_column(String(80), default="BSR Rate Book", index=True)
    vat_basis: Mapped[str] = mapped_column(String(80), default="Without VAT", index=True)
    sector: Mapped[str] = mapped_column(String(100), default="Building Works", server_default="Building Works", index=True)
    rate_system: Mapped[str] = mapped_column(String(100), default="BSR", server_default="BSR", index=True)

    category_code: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category_name: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    item_code: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    rate: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    master_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("master_items.id", ondelete="SET NULL"), nullable=True, index=True
    )

    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_cell: Mapped[str | None] = mapped_column(String(255), nullable=True)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    validation_status: Mapped[str] = mapped_column(
        String(40), default="VALID", index=True
    )  # VALID, NEEDS_REVIEW, REJECTED, APPROVED
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source_file: Mapped["SourceFile"] = relationship(back_populates="rate_items")
    master_item: Mapped["MasterItem | None"] = relationship()
    master_mapping: Mapped["RateItemMasterMapping | None"] = relationship(
        back_populates="rate_item", cascade="all, delete-orphan", uselist=False
    )

class RateItemMasterMapping(Base):
    __tablename__ = "rate_item_master_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_item_id: Mapped[int] = mapped_column(
        ForeignKey("master_items.id", ondelete="CASCADE"), index=True
    )
    rate_item_id: Mapped[int] = mapped_column(
        ForeignKey("rate_items.id", ondelete="CASCADE"), unique=True, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    mapped_by: Mapped[str] = mapped_column(String(80), default="user")
    mapped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    master_item: Mapped["MasterItem"] = relationship(back_populates="mappings")
    rate_item: Mapped["RateItem"] = relationship(back_populates="master_mapping")

# Additional composite indexes for fast search and comparison queries
Index(
    "ix_rates_composite_lookup",
    RateItem.province,
    RateItem.district,
    RateItem.year,
    RateItem.revision,
    RateItem.category_name,
)
Index("ix_rates_item_code_lower", RateItem.item_code)
Index("ix_rates_status_filter", RateItem.validation_status)
Index("ix_rate_items_sector_rate_system", RateItem.sector, RateItem.rate_system)
Index("ix_rate_items_sector_prov_dist_year", RateItem.sector, RateItem.province, RateItem.district, RateItem.year)
Index("ix_rate_items_system_year_cat", RateItem.rate_system, RateItem.year, RateItem.category_name)
Index("ix_source_files_sector_rate_system", SourceFile.sector, SourceFile.rate_system)
