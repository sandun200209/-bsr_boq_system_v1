export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'ADMIN' | 'MANAGER' | 'USER' | 'VIEWER';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AuditLog {
  id: number;
  user_id?: number | null;
  user_email?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  description?: string | null;
  ip_address?: string | null;
  created_at: string;
}

export interface SourceFile {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  sha256_hash: string;
  province: string;
  district: string;
  year: number;
  revision: string;
  dataset_type: string;
  vat_basis: string;
  category_hint?: string | null;
  sector: string;
  rate_system: string;
  storage_provider?: string;
  storage_key?: string | null;
  public_url?: string | null;
  uploaded_by_email?: string | null;
  upload_status: string;
  import_status: string;
  uploaded_at: string;
  processed_at?: string | null;
  total_rows_detected: number;
  valid_rows: number;
  review_rows: number;
  rejected_rows: number;
}

export interface RateItem {
  id: number;
  source_file_id: number;
  sector: string;
  rate_system: string;
  province: string;
  district: string;
  year: number;
  revision: string;
  dataset_type: string;
  vat_basis: string;
  category_code?: string | null;
  category_name?: string | null;
  item_code?: string | null;
  description?: string | null;
  unit?: string | null;
  rate?: number | null;
  master_item_id?: number | null;
  source_page?: number | null;
  source_sheet?: string | null;
  source_row?: number | null;
  source_cell?: string | null;
  raw_text?: string | null;
  confidence_score: number;
  validation_status: 'VALID' | 'NEEDS_REVIEW' | 'REJECTED' | 'APPROVED';
  validation_notes?: string | null;
  created_at: string;
  updated_at: string;
  verified_at?: string | null;
  original_filename?: string | null;
  updated_by_email?: string | null;
  cesmm_sections?: RateItemCESMM[];
}

export interface CESMMSection {
  id: number;
  section_no: string;
  section_code: string;
  name: string;
  section_name?: string;
  is_active: boolean;
  display_label?: string | null;
}

export interface RateItemCESMM {
  id: number;
  cesmm_section_id: number;
  section_no: string;
  section_code: string;
  name: string;
  section_name?: string;
  is_primary: boolean;
}

export interface FilterOptions {
  sectors: string[];
  rate_systems: string[];
  provinces: string[];
  districts: string[];
  years: number[];
  revisions: string[];
  dataset_types: string[];
  vat_bases: string[];
  categories: string[];
  sheets: string[];
  cesmm_sections?: CESMMSection[];
  sector_systems?: Record<string, string[]>;
  category_presets?: Record<string, string[]>;
  statuses?: string[];
  source_pages?: number[];
  total_matching?: number;
}

export interface CompareRow {
  id: number;
  source_file_id: number;
  sector?: string;
  rate_system?: string;
  province: string;
  district: string;
  year: number;
  revision: string;
  category_name?: string | null;
  item_code?: string | null;
  description?: string | null;
  unit?: string | null;
  rate: number;
  is_base?: boolean;
  diff_lkr: number;
  diff_percent: number;
  source_label?: string;
}

export interface CompareGroup {
  key: string;
  title: string;
  unit?: string | null;
  base_item_id?: number | null;
  min_rate: number;
  max_rate: number;
  avg_rate: number;
  spread: number;
  items: CompareRow[];
}

export interface CompareResponse {
  groups: CompareGroup[];
  total_groups: number;
  total_items_compared: number;
}

export interface RateItemSearchResponse {
  total: number;
  page: number;
  page_size: number;
  pages: number;
  items: RateItem[];
}

export interface MasterItem {
  id: number;
  master_code: string;
  canonical_description: string;
  canonical_unit: string;
  category?: string | null;
  sector?: string;
  rate_system?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  mapped_count: number;
  mapped_rates?: RateItem[];
  updated_by_email?: string | null;
}

export interface MasterSuggestion {
  rate_item: RateItem;
  suggested_master_id: number;
  master_code: string;
  canonical_description: string;
  similarity: number;
}

export interface DashboardMetrics {
  total_rate_items: number;
  approved_items: number;
  items_needing_review: number;
  source_files_count: number;
  provinces_count: number;
  districts_count: number;
  recent_uploads: SourceFile[];
  province_breakdown: { province: string; count: number }[];
  sector_breakdown?: { sector: string; count: number }[];
  rate_system_breakdown?: { rate_system: string; count: number }[];
  sector_files_breakdown?: { sector: string; count: number }[];
  latest_revisions: { province: string; district: string; year: number; revision: string; files: number }[];
}

export interface MasterBOQItem {
  id: number;
  master_boq_id: number;
  source_rate_item_id?: number | null;
  source_rate_book?: string | null;
  source_code?: string | null;
  source_category?: string | null;
  source_cesmm_section?: string | null;
  source_year?: number | null;
  source_revision?: string | null;
  source_region?: string | null;
  source_file?: string | null;
  source_page?: number | null;
  original_rate?: number | null;

  item_no?: string | null;
  description: string;
  unit: string;
  quantity: number;
  rate: number;
  amount: number;
  notes?: string | null;
  sort_order: number;
  is_custom: boolean;
  is_modified_rate?: boolean;

  created_at: string;
  updated_at: string;
}

export interface MasterBOQ {
  id: number;
  name: string;
  project_id?: number | null;
  status: string;
  contingency_rate: number;
  vat_status: string;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  items: MasterBOQItem[];
  total_items?: number;
  subtotal?: number;
  contingency_amount?: number;
  grand_total?: number;
}

export interface MasterBOQCreate {
  name?: string;
  project_id?: number | null;
  contingency_rate?: number;
  vat_status?: string;
  notes?: string | null;
}

export interface MasterBOQUpdate {
  name?: string;
  status?: string;
  contingency_rate?: number;
  vat_status?: string;
  notes?: string | null;
}

export interface MasterBOQItemCreate {
  description: string;
  unit: string;
  quantity?: number;
  rate?: number;
  item_no?: string | null;
  notes?: string | null;
  is_custom?: boolean;
}

export interface MasterBOQItemUpdate {
  item_no?: string | null;
  description?: string | null;
  unit?: string | null;
  quantity?: number | null;
  rate?: number | null;
  notes?: string | null;
  sort_order?: number | null;
}

export interface AddRatesToBOQResponse {
  added_count: number;
  existing_count: number;
  items: MasterBOQItem[];
  message: string;
}

// ─── BSR 31-Part Canonical Workflow ─────────────────────────────────────────

export interface CanonicalBSRPart {
  id: number;
  part_no: string;
  part_code: string;
  part_name: string;
  aliases?: string | null;
  description?: string | null;
  sort_order: number;
  active: boolean;
}

export interface PartLibraryItem extends CanonicalBSRPart {
  year_availability: Record<number, number>; // { 2023: 124, 2024: 86, ... }
  total_items: number;
}

export interface CrossYearRateItem {
  id: number;
  item_code?: string | null;
  description?: string | null;
  unit?: string | null;
  rate?: number | null;
  year: number;
  province: string;
  district: string;
  revision: string;
  vat_basis: string;
  source_page?: number | null;
  source_sheet?: string | null;
  source_row?: number | null;
  source_file_id: number;
  master_item_id?: number | null;
  validation_status: string;
  part_mapping_status: string;
}

export interface CrossYearPartData {
  canonical_part_id: number;
  total: number;
  page: number;
  page_size: number;
  available_years: number[];
  by_year: Record<number, CrossYearRateItem[]>;
}

export interface ProjectPartItemHistoryRecord {
  id: number;
  project_part_item_id: number;
  field_changed: string;
  old_value?: string | null;
  new_value?: string | null;
  changed_by?: string | null;
  changed_at: string;
  reason?: string | null;
}

export interface ProjectPartItem {
  id: number;
  project_part_selection_id: number;
  bsr_item_id?: number | null;
  master_item_id?: number | null;
  item_no?: string | null;
  original_code?: string | null;
  project_code?: string | null;
  original_description: string;
  project_description: string;
  original_unit: string;
  project_unit: string;
  quantity: number;
  original_rate: number;
  adjustment_percent: number;
  adopted_rate: number;
  amount: number;
  rate_source_year: string;
  rate_source_book?: string | null;
  rate_source_province?: string | null;
  rate_source_district?: string | null;
  rate_source_revision?: string | null;
  rate_source_file_id?: number | null;
  rate_source_page?: number | null;
  rate_source_sheet?: string | null;
  rate_source_row?: number | null;
  rate_justification?: string | null;
  remarks?: string | null;
  sort_order: number;
  is_modified: boolean;
  unit_warning_acknowledged: boolean;
  edited_by?: string | null;
  edited_at?: string | null;
  created_at: string;
  updated_at: string;
  history_records?: ProjectPartItemHistoryRecord[];
}

export interface ProjectPartSelection {
  id: number;
  project_id?: number | null;
  canonical_part_id: number;
  canonical_part?: CanonicalBSRPart | null;
  name: string;
  status: string;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  items: ProjectPartItem[];
  total_items?: number;
  subtotal?: number;
}

export interface DuplicateWarning {
  master_item_id?: number | null;
  existing_selection_item_id: number;
  existing_rate_year: string;
  new_rate_item_id: number;
  new_rate_year: string;
}

export interface AddItemsResult {
  added_count: number;
  duplicates_skipped: number;
  warnings: DuplicateWarning[];
}

export interface PartTemplateMappingOut {
  id: number;
  canonical_part_id: number;
  template_id?: number | null;
  target_sheet: string;
  title?: string | null;
  start_row: number;
  item_no_column?: string | null;
  bsr_ref_column?: string | null;
  description_column?: string | null;
  unit_column?: string | null;
  qty_column?: string | null;
  original_rate_column?: string | null;
  adopted_rate_column?: string | null;
  amount_column?: string | null;
  rate_year_column?: string | null;
  rate_source_column?: string | null;
  justification_column?: string | null;
  remarks_column?: string | null;
}

export interface BSRImportPartBreakdown {
  canonical_part_id?: number | null;
  part_no: string;
  part_code: string;
  part_name: string;
  item_count: number;
  valid_count: number;
  review_count: number;
}

export interface BSRImportBreakdown {
  source_file_id: number;
  file_name: string;
  total_extracted: number;
  total_valid: number;
  total_needs_review: number;
  total_unmapped: number;
  total_duplicate: number;
  parts_breakdown: BSRImportPartBreakdown[];
}
