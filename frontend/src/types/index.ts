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
  sector_systems?: Record<string, string[]>;
  category_presets?: Record<string, string[]>;
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
