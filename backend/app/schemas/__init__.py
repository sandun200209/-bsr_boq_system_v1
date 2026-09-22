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
