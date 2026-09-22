from __future__ import annotations
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# ----------------- Source Files -----------------
class SourceFileBase(BaseModel):
    province: str
    district: str
    year: int
    revision: str
    dataset_type: str = "BSR Rate Book"
    vat_basis: str = "Without VAT"
    category_hint: str | None = None
    sector: str = "Building Works"
    rate_system: str = "BSR"

class SourceFileOut(SourceFileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_type: str
    file_size: int
    sha256_hash: str
    upload_status: str
    import_status: str
    uploaded_at: datetime
    processed_at: datetime | None
    total_rows_detected: int
    valid_rows: int
    review_rows: int
    rejected_rows: int
    storage_provider: str = "local"
    storage_key: str | None = None
    public_url: str | None = None
    uploaded_by_email: str | None = None

class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_file_id: int
    status: str
    progress_percent: int
    message: str | None
    created_at: datetime
    updated_at: datetime

# ----------------- Rate Items -----------------
class RateItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_file_id: int
    province: str
    district: str
    year: int
    revision: str
    dataset_type: str
    vat_basis: str
    category_code: str | None
    category_name: str | None
    item_code: str | None
    description: str | None
    unit: str | None
    rate: float | None
    master_item_id: int | None
    source_page: int | None
    source_sheet: str | None
    source_row: int | None
    source_cell: str | None
    raw_text: str | None
    confidence_score: float
    validation_status: str
    validation_notes: str | None
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None
    original_filename: str | None = None
    sector: str = "Building Works"
    rate_system: str = "BSR"
    updated_by_email: str | None = None

class RateItemUpdate(BaseModel):
    item_code: str | None = None
    description: str | None = None
    unit: str | None = None
    rate: float | None = None
    category_code: str | None = None
    category_name: str | None = None
    sector: str | None = None
    rate_system: str | None = None
    validation_status: str | None = None
    validation_notes: str | None = None

class RateItemSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[RateItemOut]

class FilterOptionsResponse(BaseModel):
    sectors: list[str] = []
    rate_systems: list[str] = []
    provinces: list[str]
    districts: list[str]
    years: list[int]
    revisions: list[str]
    dataset_types: list[str]
    vat_bases: list[str]
    categories: list[str]
    sheets: list[str] = []
    sector_systems: dict[str, list[str]] = {}
    category_presets: dict[str, list[str]] = {}

# ----------------- Review Queue -----------------
class ReviewBulkActionRequest(BaseModel):
    item_ids: list[int]
    action: str  # "APPROVE" or "REJECT"

# ----------------- Rate Comparison -----------------
class CompareRowOut(BaseModel):
    id: int
    source_file_id: int
    sector: str = "Building Works"
    rate_system: str = "BSR"
    province: str
    district: str
    year: int
    revision: str
    category_name: str | None
    item_code: str | None
    description: str | None
    unit: str | None
    rate: float
    is_base: bool = False
    diff_lkr: float = 0.0
    diff_percent: float = 0.0
    source_label: str

class CompareGroupOut(BaseModel):
    key: str
    title: str
    unit: str | None
    base_item_id: int | None
    min_rate: float
    max_rate: float
    avg_rate: float
    spread: float
    items: list[CompareRowOut]

class CompareResponse(BaseModel):
    groups: list[CompareGroupOut]
    total_groups: int
    total_items_compared: int

# ----------------- Master Items -----------------
class MasterItemBase(BaseModel):
    master_code: str
    canonical_description: str
    canonical_unit: str
    category: str | None = None
    sector: str = "Building Works"
    rate_system: str | None = "BSR"
    notes: str | None = None

class MasterItemCreate(MasterItemBase):
    pass

class MasterItemUpdate(BaseModel):
    master_code: str | None = None
    canonical_description: str | None = None
    canonical_unit: str | None = None
    category: str | None = None
    sector: str | None = None
    rate_system: str | None = None
    notes: str | None = None

class MasterItemOut(MasterItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    mapped_count: int = 0
    mapped_rates: list[RateItemOut] = []
    updated_by_email: str | None = None

class MasterMappingRequest(BaseModel):
    rate_item_id: int

class MasterSuggestionOut(BaseModel):
    rate_item: RateItemOut
    suggested_master_id: int
    master_code: str
    canonical_description: str
    similarity: float

# ----------------- Authentication & Users -----------------
class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    role: str  # ADMIN, MANAGER, USER, VIEWER
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    role: str = "USER"

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# ----------------- Audit Logs -----------------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_email: str | None
    action: str
    entity_type: str
    entity_id: str | None
    description: str | None
    ip_address: str | None
    created_at: datetime

# ----------------- Master Template Export -----------------
class ExportRequest(BaseModel):
    package_key: str = "electrical"
    project_title: str | None = None
    source_note: str | None = None
    contingency_rate: float = 0.10
    items: list[dict] | None = None
    reconciliation_items: list[Any] | None = None
    vat_status: str = "Excluded"

class ExportPdfRequest(ExportRequest):
    variant: str = "combined"  # 'combined', 'boq', or 'reconciliation'

class ExportByIdsRequest(BaseModel):
    rate_item_ids: list[int]
    package_key: str = "electrical"
    project_title: str | None = None
    source_note: str | None = None
    contingency_rate: float = 0.10
    reconciliation_items: list[Any] | None = None
    vat_status: str = "Excluded"
    format: str = "excel"  # 'excel', 'pdf_combined', 'pdf_boq', 'pdf_recon'


# ----------------- Project Estimating & Sections Schemas -----------------
class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    project_base_year: int = 2026
    location: str = "Matara, Sri Lanka"
    description: str | None = None
    contingency_rate: float = 0.10
    vat_status: str = "Excluded"

class ProjectUpdate(BaseModel):
    project_name: str | None = None
    project_base_year: int | None = None
    location: str | None = None
    description: str | None = None
    status: str | None = None
    contingency_rate: float | None = None
    vat_status: str | None = None

class ProjectSectionCreate(BaseModel):
    section_code: str
    section_name: str
    section_type: str = "BOQ"  # BOQ, DUPLICATION, CHANGE_REGISTER, RECONCILIATION
    target_sheet: str | None = None
    sort_order: int = 0

class ProjectSectionUpdate(BaseModel):
    section_name: str | None = None
    section_type: str | None = None
    target_sheet: str | None = None
    sort_order: int | None = None

class ProjectItemCreate(BaseModel):
    master_item_id: int | None = None
    bsr_item_id: int | None = None
    item_no: str | None = None
    description: str
    unit: str
    quantity: float = 1.0
    selected_rate: float = 0.0
    # IMPORTANT: rate_source_year must be recorded separately from project base year
    rate_source_year: str = "2026"
    rate_source_book: str | None = None
    rate_source_item_code: str | None = None
    adjustment: float = 0.0
    rate_justification: str | None = None
    amount: float | None = None
    remarks: str | None = None
    sort_order: int = 0

class ProjectItemUpdate(BaseModel):
    item_no: str | None = None
    description: str | None = None
    unit: str | None = None
    quantity: float | None = None
    selected_rate: float | None = None
    rate_source_year: str | None = None
    rate_source_book: str | None = None
    rate_source_item_code: str | None = None
    adjustment: float | None = None
    rate_justification: str | None = None
    amount: float | None = None
    remarks: str | None = None
    sort_order: int | None = None

class ProjectItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_section_id: int
    master_item_id: int | None = None
    bsr_item_id: int | None = None
    item_no: str | None = None
    description: str
    unit: str
    quantity: float
    selected_rate: float
    rate_source_year: str
    rate_source_book: str | None = None
    rate_source_item_code: str | None = None
    adjustment: float = 0.0
    rate_justification: str | None = None
    amount: float
    remarks: str | None = None
    sort_order: int

class DuplicationRecordCreate(BaseModel):
    item: str = "1"
    bsr_ref: str | None = None
    description: str
    unit: str = "Item"
    qty: float = 1.0
    rate: float = 0.0
    amount: float | None = None
    rate_source_year: str = "2026"
    duplicate_with: str | None = None
    status: str = "RETAIN"
    remarks: str | None = None
    sort_order: int = 0

class DuplicationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_section_id: int
    item: str
    bsr_ref: str | None
    description: str
    unit: str
    qty: float
    rate: float
    amount: float
    rate_source_year: str
    duplicate_with: str | None
    status: str
    remarks: str | None
    sort_order: int

class ChangeRegisterRecordCreate(BaseModel):
    ref_code: str = "CR-01"
    package_sheet: str = "Electrical"
    item_code: str | None = None
    description: str
    original_status: str | None = None
    rev7_action: str | None = None
    duplicate_with: str | None = None
    rate_source: str | None = None
    cost_impact: float = 0.0
    reason: str | None = None
    sort_order: int = 0

class ChangeRegisterRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_section_id: int
    ref_code: str
    package_sheet: str
    item_code: str | None
    description: str
    original_status: str | None
    rev7_action: str | None
    duplicate_with: str | None
    rate_source: str | None
    cost_impact: float
    reason: str | None
    sort_order: int

class ReconciliationRecordCreate(BaseModel):
    scope_element: str
    source_boq: str | None = None
    other_package: str | None = None
    consolidated_treatment: str | None = None
    deduction_amount: str | None = None
    reason: str | None = None
    risk: str | None = None
    tender_action: str | None = None
    is_approved: bool = True
    sort_order: int = 0

class ReconciliationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_section_id: int
    scope_element: str
    source_boq: str | None
    other_package: str | None
    consolidated_treatment: str | None
    deduction_amount: str | None
    reason: str | None
    risk: str | None
    tender_action: str | None
    is_approved: bool
    sort_order: int

class ProjectSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    section_code: str
    section_name: str
    section_type: str
    target_sheet: str | None
    sort_order: int
    items_count: int = 0
    total_amount: float = 0.0
    items: list[ProjectItemOut] = []
    duplication_records: list[DuplicationRecordOut] = []
    change_register_records: list[ChangeRegisterRecordOut] = []
    reconciliation_records: list[ReconciliationRecordOut] = []

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_code: str
    project_name: str
    project_base_year: int
    location: str
    description: str | None
    status: str
    contingency_rate: float
    vat_status: str
    created_at: datetime
    updated_at: datetime
    sections: list[ProjectSectionOut] = []
    total_estimate: float = 0.0

class HistoricalRateEntry(BaseModel):
    year: int | str
    province: str
    district: str
    book_title: str
    item_code: str
    description: str
    unit: str
    rate: float
    rate_item_id: int
    variance_pct: float | None = None

class HistoricalRateComparisonOut(BaseModel):
    master_item_id: int | None = None
    master_code: str | None = None
    canonical_description: str | None = None
    canonical_unit: str | None = None
    project_base_year: int = 2026
    rates_by_year: dict[str, list[HistoricalRateEntry]] = {}
    all_rates: list[HistoricalRateEntry] = []
    average_rate: float = 0.0
    min_rate: float = 0.0
    max_rate: float = 0.0

class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_name: str
    file_path: str
    description: str | None
    is_default: bool
    mappings: list[Any] = []

class TemplateMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    section_type: str
    target_sheet: str
    start_row: int
    item_no_column: str | None
    bsr_ref_column: str | None
    description_column: str | None
    unit_column: str | None
    quantity_column: str | None
    rate_column: str | None
    amount_column: str | None
    rate_year_column: str | None
    rate_source_column: str | None
    adjustment_column: str | None
    remarks_column: str | None

class ProjectExportRequest(BaseModel):
    mode: str = "consolidated"  # 'consolidated' (Option A: all sections in 1 file) or 'separate' (Option B: single section file)
    section_ids: list[int] | None = None
    target_section_id: int | None = None  # for single section export
    template_id: int | None = None
    format: str = "excel"  # 'excel' or 'pdf'

