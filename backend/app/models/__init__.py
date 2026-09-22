from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="USER", server_default="USER", index=True)  # ADMIN, MANAGER, USER, VIEWER
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, UPLOAD, APPROVE, REJECT
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)  # RATE_ITEM, SOURCE_FILE, MASTER_ITEM, USER, SYSTEM
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

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

    # Cloud Storage & Upload Metadata
    storage_provider: Mapped[str] = mapped_column(String(50), default="local", server_default="local")  # local, supabase
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    public_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

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
    updated_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    updated_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

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


# ---------------------------------------------------------------------------
# Project-Based Estimating, Rate Comparison & Master Template Export Models
# ---------------------------------------------------------------------------

class BSRBook(Base):
    __tablename__ = "bsr_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), default="Building Works", index=True)
    rate_system: Mapped[str] = mapped_column(String(100), default="BSR", index=True)
    province: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revision: Mapped[str] = mapped_column(String(120), default="Original")
    effective_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_file_id: Mapped[int | None] = mapped_column(ForeignKey("source_files.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_file: Mapped["SourceFile | None"] = relationship()
    items: Mapped[list["BSRItem"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class BSRItem(Base):
    __tablename__ = "bsr_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("bsr_books.id", ondelete="SET NULL"), nullable=True, index=True)
    rate_item_id: Mapped[int | None] = mapped_column(ForeignKey("rate_items.id", ondelete="CASCADE"), nullable=True, index=True)
    item_code: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[float] = mapped_column(Float, default=0.0)
    category_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    book: Mapped["BSRBook | None"] = relationship(back_populates="items")
    rate_item: Mapped["RateItem | None"] = relationship()


class ItemMatch(Base):
    __tablename__ = "item_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_item_id: Mapped[int] = mapped_column(ForeignKey("master_items.id", ondelete="CASCADE"), index=True)
    bsr_item_id: Mapped[int | None] = mapped_column(ForeignKey("rate_items.id", ondelete="CASCADE"), nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    match_type: Mapped[str] = mapped_column(String(50), default="MANUAL")  # EXACT, SEMANTIC, MANUAL, HISTORICAL
    match_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    master_item: Mapped["MasterItem"] = relationship()
    bsr_item: Mapped["RateItem | None"] = relationship()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # IMPORTANT RULE: Project Base Year is distinct from each Item's Rate Source Year
    project_base_year: Mapped[int] = mapped_column(Integer, default=2026, index=True)
    location: Mapped[str] = mapped_column(String(255), default="Matara, Sri Lanka")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", index=True)  # DRAFT, IN_REVIEW, APPROVED, COMPLETED
    contingency_rate: Mapped[float] = mapped_column(Float, default=0.10)
    vat_status: Mapped[str] = mapped_column(String(50), default="Excluded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections: Mapped[list["ProjectSection"]] = relationship(back_populates="project", cascade="all, delete-orphan", order_by="ProjectSection.sort_order")


class ProjectSection(Base):
    __tablename__ = "project_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    section_code: Mapped[str] = mapped_column(String(100), index=True)
    section_name: Mapped[str] = mapped_column(String(255), nullable=False)
    section_type: Mapped[str] = mapped_column(String(50), default="BOQ", index=True)  # BOQ, RECONCILIATION, DUPLICATION, CHANGE_REGISTER
    target_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    template_mapping_id: Mapped[int | None] = mapped_column(ForeignKey("template_mappings.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="sections")
    items: Mapped[list["ProjectItem"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="ProjectItem.sort_order")
    duplication_records: Mapped[list["DuplicationRecord"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="DuplicationRecord.sort_order")
    change_register_records: Mapped[list["ChangeRegisterRecord"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="ChangeRegisterRecord.sort_order")
    reconciliation_records: Mapped[list["ReconciliationRecord"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="ReconciliationRecord.sort_order")
    template_mapping: Mapped["TemplateMapping | None"] = relationship()


class ProjectItem(Base):
    __tablename__ = "project_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_section_id: Mapped[int] = mapped_column(ForeignKey("project_sections.id", ondelete="CASCADE"), index=True)
    master_item_id: Mapped[int | None] = mapped_column(ForeignKey("master_items.id", ondelete="SET NULL"), nullable=True, index=True)
    bsr_item_id: Mapped[int | None] = mapped_column(ForeignKey("rate_items.id", ondelete="SET NULL"), nullable=True, index=True)

    item_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    selected_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # IMPORTANT: Rate Source Year is distinct from Project Base Year
    rate_source_year: Mapped[str] = mapped_column(String(50), default="2026", index=True)
    rate_source_book: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rate_source_item_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    adjustment: Mapped[float] = mapped_column(Float, default=0.0)
    rate_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    section: Mapped["ProjectSection"] = relationship(back_populates="items")
    master_item: Mapped["MasterItem | None"] = relationship()
    bsr_item: Mapped["RateItem | None"] = relationship()


class DuplicationRecord(Base):
    """
    Independent dataset for 'MATARA OT RENOVATION – SITE WORKS BOQ REVIEWED FOR DUPLICATION'
    """
    __tablename__ = "duplication_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_section_id: Mapped[int] = mapped_column(ForeignKey("project_sections.id", ondelete="CASCADE"), index=True)
    item: Mapped[str] = mapped_column(String(100), default="1")
    bsr_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(100), default="Item")
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    rate: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    rate_source_year: Mapped[str] = mapped_column(String(50), default="2026")
    duplicate_with: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="RETAIN")  # RETAIN, DEDUCT, REDUCE, TRANSFER, REVIEW
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    section: Mapped["ProjectSection"] = relationship(back_populates="duplication_records")


class ChangeRegisterRecord(Base):
    """
    Independent dataset for 'REV 7 CONSOLIDATION CHANGE / DUPLICATION REGISTER'
    """
    __tablename__ = "change_register_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_section_id: Mapped[int] = mapped_column(ForeignKey("project_sections.id", ondelete="CASCADE"), index=True)
    ref_code: Mapped[str] = mapped_column(String(50), default="CR-01")
    package_sheet: Mapped[str] = mapped_column(String(150), default="Electrical")
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    original_status: Mapped[str | None] = mapped_column(String(150), nullable=True)
    rev7_action: Mapped[str | None] = mapped_column(String(150), nullable=True)
    duplicate_with: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rate_source: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cost_impact: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    section: Mapped["ProjectSection"] = relationship(back_populates="change_register_records")


class ReconciliationRecord(Base):
    """
    Multi-package scope reconciliation and adjustment entries
    """
    __tablename__ = "reconciliation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_section_id: Mapped[int] = mapped_column(ForeignKey("project_sections.id", ondelete="CASCADE"), index=True)
    scope_element: Mapped[str] = mapped_column(String(255), nullable=False)
    source_boq: Mapped[str | None] = mapped_column(String(255), nullable=True)
    other_package: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consolidated_treatment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deduction_amount: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tender_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    section: Mapped["ProjectSection"] = relationship(back_populates="reconciliation_records")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mappings: Mapped[list["TemplateMapping"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class TemplateMapping(Base):
    __tablename__ = "template_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"), index=True)
    section_type: Mapped[str] = mapped_column(String(50), default="BOQ", index=True)  # BOQ, DUPLICATION, CHANGE_REGISTER, RECONCILIATION
    target_sheet: Mapped[str] = mapped_column(String(255), nullable=False)
    start_row: Mapped[int] = mapped_column(Integer, default=5)

    item_no_column: Mapped[str | None] = mapped_column(String(10), default="B")
    bsr_ref_column: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description_column: Mapped[str | None] = mapped_column(String(10), default="C")
    unit_column: Mapped[str | None] = mapped_column(String(10), default="D")
    quantity_column: Mapped[str | None] = mapped_column(String(10), default="E")
    rate_column: Mapped[str | None] = mapped_column(String(10), default="F")
    amount_column: Mapped[str | None] = mapped_column(String(10), default="G")
    rate_year_column: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rate_source_column: Mapped[str | None] = mapped_column(String(10), nullable=True)
    adjustment_column: Mapped[str | None] = mapped_column(String(10), nullable=True)
    remarks_column: Mapped[str | None] = mapped_column(String(10), default="O")
    custom_column_mapping: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON for arbitrary columns
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    template: Mapped["Template"] = relationship(back_populates="mappings")

