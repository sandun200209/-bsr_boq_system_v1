from __future__ import annotations
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

class MasterMappingRequest(BaseModel):
    rate_item_id: int

class MasterSuggestionOut(BaseModel):
    rate_item: RateItemOut
    suggested_master_id: int
    master_code: str
    canonical_description: str
    similarity: float
