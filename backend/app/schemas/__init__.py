from __future__ import annotations
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, computed_field

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

# ----------------- CESMM-SL Work Sections -----------------
class CESMMSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_no: str
    section_code: str
    name: str
    is_active: bool
    display_label: str | None = None

    @computed_field
    def section_name(self) -> str:
        return self.name

class RateItemCESMMOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cesmm_section_id: int
    section_no: str
    section_code: str
    name: str
    is_primary: bool

    @computed_field
    def section_name(self) -> str:
        return self.name

class CESMMAssignEntry(BaseModel):
    cesmm_section_id: int
    is_primary: bool = False

class RateItemCESMMAssignRequest(BaseModel):
    mappings: list[CESMMAssignEntry] = []

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
    cesmm_sections: list[RateItemCESMMOut] = []

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
    cesmm_sections: list[CESMMSectionOut] = []
    sector_systems: dict[str, list[str]] = {}
    category_presets: dict[str, list[str]] = {}
    statuses: list[str] = []
    source_pages: list[int] = []
    total_matching: int = 0

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


# ----------------- Master BOQ Working Workspace -----------------

class MasterBOQItemBase(BaseModel):
    item_no: str | None = None
    description: str
    unit: str
    quantity: float = 0.0
    rate: float = 0.0
    notes: str | None = None
    sort_order: int = 0
    is_custom: bool = False

class MasterBOQItemCreate(BaseModel):
    description: str
    unit: str
    quantity: float = 0.0
    rate: float = 0.0
    item_no: str | None = None
    notes: str | None = None
    is_custom: bool = True

class MasterBOQItemUpdate(BaseModel):
    item_no: str | None = None
    description: str | None = None
    unit: str | None = None
    quantity: float | None = None
    rate: float | None = None
    notes: str | None = None
    sort_order: int | None = None

class MasterBOQItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    master_boq_id: int
    source_rate_item_id: int | None = None
    source_rate_book: str | None = None
    source_code: str | None = None
    source_category: str | None = None
    source_cesmm_section: str | None = None
    source_year: int | None = None
    source_revision: str | None = None
    source_region: str | None = None
    source_file: str | None = None
    source_page: int | None = None
    original_rate: float | None = None

    item_no: str | None = None
    description: str
    unit: str
    quantity: float = 0.0
    rate: float = 0.0
    amount: float = 0.0
    notes: str | None = None
    sort_order: int = 0
    is_custom: bool = False

    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_modified_rate(self) -> bool:
        if self.original_rate is not None and not self.is_custom:
            return round(self.rate, 2) != round(self.original_rate, 2)
        return False

class MasterBOQBase(BaseModel):
    name: str = "Master BOQ Working Workspace"
    project_id: int | None = None
    status: str = "ACTIVE"
    contingency_rate: float = 0.10
    vat_status: str = "Excluded"
    notes: str | None = None

class MasterBOQCreate(BaseModel):
    name: str = "Master BOQ Working Workspace"
    project_id: int | None = None
    contingency_rate: float = 0.10
    vat_status: str = "Excluded"
    notes: str | None = None

class MasterBOQUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    contingency_rate: float | None = None
    vat_status: str | None = None
    notes: str | None = None

class MasterBOQOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    project_id: int | None = None
    status: str
    contingency_rate: float
    vat_status: str
    notes: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    items: list[MasterBOQItemOut] = []

    @computed_field
    def total_items(self) -> int:
        return len(self.items)

    @computed_field
    def subtotal(self) -> float:
        return round(sum(it.amount for it in self.items), 2)

    @computed_field
    def contingency_amount(self) -> float:
        return round(self.subtotal * self.contingency_rate, 2)

    @computed_field
    def grand_total(self) -> float:
        return round(self.subtotal + self.contingency_amount, 2)

class AddRatesToBOQRequest(BaseModel):
    rate_item_ids: list[int]

class AddRatesToBOQResponse(BaseModel):
    added_count: int
    existing_count: int
    items: list[MasterBOQItemOut]
    message: str

class BulkDeleteBOQItemsRequest(BaseModel):
    item_ids: list[int]

class ReorderItemEntry(BaseModel):
    id: int
    sort_order: int

class ReorderBOQItemsRequest(BaseModel):
    item_orders: list[ReorderItemEntry]


# ----------------- 31-Part Canonical BSR Workflow Schemas -----------------

class CanonicalBSRPartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_no: str
    part_code: str
    part_name: str
    aliases: str | None = None
    description: str | None = None
    sort_order: int = 0
    active: bool = True
    created_at: datetime
    updated_at: datetime

class CanonicalBSRPartUpdate(BaseModel):
    part_name: str | None = None
    part_code: str | None = None
    aliases: str | None = None
    description: str | None = None
    sort_order: int | None = None
    active: bool | None = None

class PartYearAvailability(BaseModel):
    year: int
    count: int

class PartLibraryItemOut(BaseModel):
    id: int
    part_no: str
    part_code: str
    part_name: str
    description: str | None = None
    sort_order: int = 0
    active: bool = True
    total_items: int = 0
    years_available: list[int] = []
    year_counts: dict[str, int] = {}

class CrossYearRateItemOut(BaseModel):
    id: int
    canonical_part_id: int | None = None
    item_code: str | None = None
    description: str
    unit: str
    rate: float
    year: int
    revision: str
    province: str
    district: str
    vat_basis: str
    source_file_id: int | None = None
    source_file_name: str | None = None
    source_page: int | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    validation_status: str = "VALID"
    part_mapping_status: str = "MAPPED"
    master_item_id: int | None = None
    master_code: str | None = None
    canonical_description: str | None = None
    canonical_unit: str | None = None
    is_master_approved: bool = False
    similarity_suggestion: str | None = None
    similarity_score: float | None = None

class CrossYearPartGroupOut(BaseModel):
    part: CanonicalBSRPartOut
    available_years: list[int] = []
    items_by_year: dict[str, list[CrossYearRateItemOut]] = {}
    master_grouped_items: list[dict[str, Any]] = []
    total_items: int = 0

class AddPartItemEntry(BaseModel):
    rate_item_id: int
    quantity: float = 1.0
    adjustment_percent: float = 0.0
    adopted_rate: float | None = None
    rate_justification: str | None = None
    remarks: str | None = None

class AddItemsToPartSelectionRequest(BaseModel):
    items: list[AddPartItemEntry]
    replace_existing_master_ids: list[int] = []
    allow_duplicates: bool = False

class DuplicateItemWarningDetail(BaseModel):
    master_item_id: int | None = None
    item_code: str | None = None
    existing_item_id: int
    existing_year: str
    existing_rate: float
    new_rate_item_id: int
    new_year: str
    new_rate: float
    description: str

class DuplicateItemWarningResponse(BaseModel):
    has_duplicates: bool
    warnings: list[DuplicateItemWarningDetail] = []
    message: str | None = None

class ProjectPartItemHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_part_item_id: int
    field_changed: str
    old_value: str | None = None
    new_value: str | None = None
    changed_by: str | None = None
    changed_at: datetime
    reason: str | None = None

class ProjectPartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_part_selection_id: int
    bsr_item_id: int | None = None
    master_item_id: int | None = None
    item_no: str | None = None
    original_code: str | None = None
    project_code: str | None = None
    original_description: str
    project_description: str
    original_unit: str
    project_unit: str
    quantity: float = 0.0
    original_rate: float = 0.0
    adjustment_percent: float = 0.0
    adopted_rate: float = 0.0
    amount: float = 0.0
    rate_source_year: str
    rate_source_book: str | None = None
    rate_source_province: str | None = None
    rate_source_district: str | None = None
    rate_source_revision: str | None = None
    rate_source_file_id: int | None = None
    rate_source_page: int | None = None
    rate_source_sheet: str | None = None
    rate_source_row: int | None = None
    rate_justification: str | None = None
    remarks: str | None = None
    sort_order: int = 0
    is_modified: bool = False
    unit_warning_acknowledged: bool = False
    edited_by: str | None = None
    edited_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    history_records: list[ProjectPartItemHistoryOut] = []

class ProjectPartItemUpdate(BaseModel):
    item_no: str | None = None
    project_description: str | None = None
    project_unit: str | None = None
    quantity: float | None = None
    adjustment_percent: float | None = None
    adopted_rate: float | None = None
    rate_justification: str | None = None
    remarks: str | None = None
    sort_order: int | None = None
    unit_warning_acknowledged: bool | None = None
    # Optional permission fields (manager/admin)
    project_code: str | None = None
    rate_source_year: str | None = None
    rate_source_book: str | None = None

class ProjectPartSelectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None = None
    canonical_part_id: int
    canonical_part: CanonicalBSRPartOut | None = None
    name: str
    status: str
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[ProjectPartItemOut] = []

    @computed_field
    def total_items(self) -> int:
        return len(self.items)

    @computed_field
    def subtotal(self) -> float:
        return round(sum(it.amount for it in self.items), 2)

class PartTemplateMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_part_id: int
    template_id: int | None = None
    target_sheet: str
    title: str | None = None
    start_row: int = 5
    item_no_column: str | None = "A"
    bsr_ref_column: str | None = "B"
    description_column: str | None = "C"
    unit_column: str | None = "D"
    qty_column: str | None = "E"
    original_rate_column: str | None = "F"
    adopted_rate_column: str | None = "G"
    amount_column: str | None = "H"
    rate_year_column: str | None = "I"
    rate_source_column: str | None = "J"
    justification_column: str | None = "K"
    remarks_column: str | None = "L"
    column_mapping_json: str | None = None

class PartTemplateMappingUpdate(BaseModel):
    template_id: int | None = None
    target_sheet: str | None = None
    title: str | None = None
    start_row: int | None = None
    item_no_column: str | None = None
    bsr_ref_column: str | None = None
    description_column: str | None = None
    unit_column: str | None = None
    qty_column: str | None = None
    original_rate_column: str | None = None
    adopted_rate_column: str | None = None
    amount_column: str | None = None
    rate_year_column: str | None = None
    rate_source_column: str | None = None
    justification_column: str | None = None
    remarks_column: str | None = None
    column_mapping_json: str | None = None

class BSRImportPartBreakdownEntry(BaseModel):
    canonical_part_id: int | None = None
    part_no: str
    part_code: str
    part_name: str
    item_count: int
    valid_count: int
    review_count: int

class BSRImportBreakdownOut(BaseModel):
    source_file_id: int
    file_name: str
    total_extracted: int
    total_valid: int
    total_needs_review: int
    total_unmapped: int
    total_duplicate: int
    parts_breakdown: list[BSRImportPartBreakdownEntry] = []


