import {
  DashboardMetrics,
  FilterOptions,
  SourceFile,
  RateItem,
  CompareResponse,
  MasterItem,
  MasterSuggestion,
  User,
  AuthResponse,
  AuditLog,
  RateItemSearchResponse,
  CESMMSection,
  RateItemCESMM,
  MasterBOQ,
  MasterBOQItem,
  MasterBOQCreate,
  MasterBOQUpdate,
  MasterBOQItemCreate,
  MasterBOQItemUpdate,
  AddRatesToBOQResponse,
  CanonicalBSRPart,
  PartLibraryItem,
  CrossYearPartData,
  ProjectPartItem,
  ProjectPartSelection,
  AddItemsResult,
  ProjectPartItemHistoryRecord,
  BSRImportBreakdown,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export function getAuthToken(): string | null {
  return localStorage.getItem('bsr_token');
}

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('bsr_token', token);
  } else {
    localStorage.removeItem('bsr_token');
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options?.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // If unauthorized, clear invalid token
    // (AuthContext handles redirect to login)
    window.dispatchEvent(new CustomEvent('bsr_auth_unauthorized'));
  }

  if (!res.ok) {
    let errorDetail = 'API request failed';
    try {
      const data = await res.json();
      errorDetail = data.detail || data.message || errorDetail;
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

async function downloadFile(path: string, body: any, defaultFilename: string): Promise<void> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let errorDetail = 'File download failed';
    try {
      const data = await res.json();
      errorDetail = data.detail || data.message || errorDetail;
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  const disposition = res.headers.get('Content-Disposition');
  let filename = defaultFilename;
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) filename = match[1];
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export const api = {
  // Authentication
  login: (username_or_email: string, password: string) =>
    request<AuthResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username_or_email, password }),
    }),

  getMe: () => request<User>('/auth/me'),

  logout: () =>
    request<{ success: boolean; message: string }>('/auth/logout', {
      method: 'POST',
    }),

  changePassword: (current_password: string, new_password: string) =>
    request<{ success: boolean; message: string }>('/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password, new_password }),
    }),

  // User Management (ADMIN)
  getUsers: (skip = 0, limit = 50) =>
    request<User[]>(`/users?skip=${skip}&limit=${limit}`),

  createUser: (data: { email: string; username: string; password: string; full_name: string; role: string }) =>
    request<User>('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateUser: (id: number, data: { full_name?: string; role?: string; is_active?: boolean; password?: string }) =>
    request<User>(`/users/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteUser: (id: number) =>
    request<{ success: boolean; message: string }>(`/users/${id}`, {
      method: 'DELETE',
    }),

  // Audit Logs (ADMIN)
  getAuditLogs: (params?: { action?: string; entity_type?: string; user_email?: string; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.action) q.set('action', params.action);
    if (params?.entity_type) q.set('entity_type', params.entity_type);
    if (params?.user_email) q.set('user_email', params.user_email);
    if (params?.skip !== undefined) q.set('skip', params.skip.toString());
    if (params?.limit !== undefined) q.set('limit', params.limit.toString());
    return request<AuditLog[]>(`/audit-logs?${q.toString()}`);
  },

  // Health
  getHealth: () => request<{ status: string; app: string; version: string }>('/health'),
  getDatabaseHealth: () => request<{ status: string; select_1: boolean; pg_trgm_enabled: boolean }>('/health/database'),

  // Dashboard
  getDashboard: () => request<DashboardMetrics>('/dashboard'),

  // Documents
  uploadDocument: (formData: FormData) => {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        let err = 'Upload failed';
        try {
          const d = await res.json();
          err = d.detail || err;
        } catch {
          err = await res.text();
        }
        throw new Error(err);
      }
      return res.json();
    });
  },

  getDocuments: (params?: {
    sector?: string;
    rate_system?: string;
    province?: string;
    district?: string;
    year?: number;
    skip?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.sector) q.set('sector', params.sector);
    if (params?.rate_system) q.set('rate_system', params.rate_system);
    if (params?.province) q.set('province', params.province);
    if (params?.district) q.set('district', params.district);
    if (params?.year) q.set('year', params.year.toString());
    if (params?.skip !== undefined) q.set('skip', params.skip.toString());
    if (params?.limit !== undefined) q.set('limit', params.limit.toString());
    return request<SourceFile[]>(`/documents?${q.toString()}`);
  },

  getDocument: (id: number) => request<SourceFile>(`/documents/${id}`),

  deleteDocument: (id: number) =>
    request<{ success: boolean; message: string }>(`/documents/${id}`, {
      method: 'DELETE',
    }),

  getDocumentDownloadUrl: (id: number) => `${API_BASE}/documents/${id}/download`,
  getDocumentViewUrl: (id: number) => `${API_BASE}/documents/${id}/view`,

  // Rates
  searchRates: (params: {
    q?: string;
    sector?: string;
    rate_system?: string;
    cesmm_section_id?: number;
    cesmm_section_no?: string;
    province?: string;
    district?: string;
    year?: number;
    revision?: string;
    category?: string;
    dataset_type?: string;
    vat_basis?: string;
    status?: string;
    source_page?: number;
    sheet?: string;
    min_rate?: number;
    max_rate?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    page?: number;
    page_size?: number;
    skip?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params.q) q.set('q', params.q);
    if (params.sector) q.set('sector', params.sector);
    if (params.rate_system) q.set('rate_system', params.rate_system);
    if (params.cesmm_section_id !== undefined) q.set('cesmm_section_id', params.cesmm_section_id.toString());
    if (params.cesmm_section_no) q.set('cesmm_section_no', params.cesmm_section_no);
    if (params.province) q.set('province', params.province);
    if (params.district) q.set('district', params.district);
    if (params.year) q.set('year', params.year.toString());
    if (params.revision) q.set('revision', params.revision);
    if (params.category) q.set('category', params.category);
    if (params.dataset_type) q.set('dataset_type', params.dataset_type);
    if (params.vat_basis) q.set('vat_basis', params.vat_basis);
    if (params.status) q.set('status', params.status);
    if (params.source_page !== undefined) q.set('source_page', params.source_page.toString());
    if (params.sheet) q.set('sheet', params.sheet);
    if (params.min_rate !== undefined) q.set('min_rate', params.min_rate.toString());
    if (params.max_rate !== undefined) q.set('max_rate', params.max_rate.toString());
    if (params.sort_by) q.set('sort_by', params.sort_by);
    if (params.sort_order) q.set('sort_order', params.sort_order);
    if (params.page !== undefined) q.set('page', params.page.toString());
    if (params.page_size !== undefined) q.set('page_size', params.page_size.toString());
    if (params.skip !== undefined) q.set('skip', params.skip.toString());
    if (params.limit !== undefined) q.set('limit', params.limit.toString());
    return request<RateItemSearchResponse>(
      `/rates/search?${q.toString()}`
    );
  },

  getFilterOptions: (params?: {
    rate_system?: string;
    cesmm_section_no?: string;
    cesmm_section_id?: number;
    category?: string;
    province?: string;
    district?: string;
    year?: number;
    revision?: string;
    vat_basis?: string;
    sheet?: string;
    status?: string;
    sector?: string;
  }) => {
    const q = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          q.append(k, String(v));
        }
      });
    }
    const queryStr = q.toString();
    return request<FilterOptions>(queryStr ? `/rates/filters?${queryStr}` : '/rates/filters');
  },

  // CESMM-SL (31 Work Sections Classification)
  getCesmmSections: (activeOnly = true) =>
    request<CESMMSection[]>(`/cesmm/sections?active_only=${activeOnly}`),

  getItemCesmmMappings: (rateId: number) =>
    request<RateItemCESMM[]>(`/cesmm/items/${rateId}`),

  assignItemCesmmMappings: (rateId: number, mappings: { cesmm_section_id: number; is_primary?: boolean }[]) =>
    request<RateItemCESMM[]>(`/cesmm/items/${rateId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mappings }),
    }),

  removeItemCesmmMapping: (rateId: number, cesmmSectionId: number) =>
    request<RateItemCESMM[]>(`/cesmm/items/${rateId}/${cesmmSectionId}`, {
      method: 'DELETE',
    }),

  setPrimaryCesmmMapping: (rateId: number, cesmmSectionId: number) =>
    request<RateItemCESMM[]>(`/cesmm/items/${rateId}/primary/${cesmmSectionId}`, {
      method: 'PUT',
    }),

  // Compare
  getCompare: (params: {
    q?: string;
    sector?: string;
    rate_system?: string;
    provinces?: string[];
    years?: number[];
    categories?: string[];
    category?: string;
    base_item_id?: number;
    base_province?: string;
    base_year?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params.q) q.set('q', params.q);
    if (params.sector) q.set('sector', params.sector);
    if (params.rate_system) q.set('rate_system', params.rate_system);
    if (params.provinces) params.provinces.forEach((p) => q.append('provinces', p));
    if (params.years) params.years.forEach((y) => q.append('years', y.toString()));
    if (params.categories) params.categories.forEach((c) => q.append('categories', c));
    if (params.category) q.set('category', params.category);
    if (params.base_item_id !== undefined) q.set('base_item_id', params.base_item_id.toString());
    if (params.base_province) q.set('base_province', params.base_province);
    if (params.base_year) q.set('base_year', params.base_year.toString());
    if (params.limit) q.set('limit', params.limit.toString());
    return request<CompareResponse>(`/compare?${q.toString()}`);
  },

  // Review Queue
  getReviewQueue: (params?: {
    source_file_id?: number;
    sector?: string;
    rate_system?: string;
    status?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.source_file_id) q.set('source_file_id', params.source_file_id.toString());
    if (params?.sector) q.set('sector', params.sector);
    if (params?.rate_system) q.set('rate_system', params.rate_system);
    if (params?.status) q.set('status', params.status);
    if (params?.category) q.set('category', params.category);
    if (params?.page) q.set('page', params.page.toString());
    if (params?.page_size) q.set('page_size', params.page_size.toString());
    return request<{ total: number; page: number; page_size: number; items: RateItem[] }>(
      `/review?${q.toString()}`
    );
  },

  updateReviewItem: (id: number, data: Partial<RateItem>) =>
    request<RateItem>(`/review/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  approveReviewItem: (id: number) =>
    request<RateItem>(`/review/${id}/approve`, { method: 'POST' }),

  rejectReviewItem: (id: number) =>
    request<RateItem>(`/review/${id}/reject`, { method: 'POST' }),

  bulkReviewAction: (itemIds: number[], action: 'APPROVE' | 'REJECT') =>
    request<{ updated: number; action: string; message: string }>('/review/bulk-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: itemIds, action }),
    }),

  approveValidDocumentItems: (docId: number) =>
    request<{ document_id: number; approved_count: number; message: string }>(
      `/review/document/${docId}/approve-valid`,
      { method: 'POST' }
    ),

  // Master Items
  getMasterItems: (params?: { q?: string; sector?: string; rate_system?: string; category?: string; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.q) q.set('q', params.q);
    if (params?.sector) q.set('sector', params.sector);
    if (params?.rate_system) q.set('rate_system', params.rate_system);
    if (params?.category) q.set('category', params.category);
    if (params?.skip !== undefined) q.set('skip', params.skip.toString());
    if (params?.limit !== undefined) q.set('limit', params.limit.toString());
    return request<MasterItem[]>(`/master-items?${q.toString()}`);
  },

  getMasterItem: (id: number) => request<MasterItem>(`/master-items/${id}`),

  createMasterItem: (data: {
    master_code: string;
    canonical_description: string;
    canonical_unit: string;
    category?: string;
    sector?: string;
    rate_system?: string;
    notes?: string;
  }) =>
    request<MasterItem>('/master-items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateMasterItem: (id: number, data: Partial<MasterItem>) =>
    request<MasterItem>(`/master-items/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteMasterItem: (id: number) =>
    request<{ success: boolean; message: string }>(`/master-items/${id}`, { method: 'DELETE' }),

  mapRateToMaster: (masterId: number, rateItemId: number) =>
    request<{ success: boolean; message: string }>(`/master-items/${masterId}/map`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rate_item_id: rateItemId }),
    }),

  unmapRateFromMaster: (rateItemId: number) =>
    request<{ success: boolean; message: string }>(`/master-items/unmap/${rateItemId}`, {
      method: 'POST',
    }),

  getMasterSuggestions: (limit?: number) =>
    request<MasterSuggestion[]>(`/master-items/suggestions/unmapped?limit=${limit || 20}`),

  // Master Template QS Export
  getExportPackages: () =>
    request<{ packages: any[] }>('/export/packages'),

  getExportPreview: (packageKey: string) =>
    request<any>(`/export/preview/${packageKey}`),

  downloadExportExcel: (options: {
    package_key: string;
    project_title?: string;
    source_note?: string;
    contingency_rate?: number;
    items?: any[];
    reconciliation_items?: any[];
    vat_status?: string;
  }) =>
    downloadFile(
      '/export/excel',
      options,
      `Matara_OT_Consolidated_BOQ_${options.package_key}.xlsx`
    ),

  downloadExportPdf: (options: {
    package_key: string;
    variant?: 'combined' | 'boq' | 'reconciliation';
    project_title?: string;
    source_note?: string;
    contingency_rate?: number;
    items?: any[];
    reconciliation_items?: any[];
    vat_status?: string;
  }) =>
    downloadFile(
      '/export/pdf',
      options,
      `Matara_OT_Consolidated_${options.package_key}_${options.variant || 'combined'}.pdf`
    ),

  // Project Estimating & Template Export Engine
  getProjects: () => request<any[]>('/projects'),

  getProject: (id: number) => request<any>(`/projects/${id}`),

  createProject: (data: any) =>
    request<any>('/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateProject: (id: number, data: any) =>
    request<any>(`/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  addProjectSection: (projectId: number, data: any) =>
    request<any>(`/projects/${projectId}/sections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  addProjectItem: (sectionId: number, data: any) =>
    request<any>(`/projects/sections/${sectionId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateProjectItem: (itemId: number, data: any) =>
    request<any>(`/projects/items/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteProjectItem: (itemId: number) =>
    request<any>(`/projects/items/${itemId}`, { method: 'DELETE' }),

  addDuplicationRecord: (sectionId: number, data: any) =>
    request<any>(`/projects/sections/${sectionId}/duplication-records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  addChangeRegisterRecord: (sectionId: number, data: any) =>
    request<any>(`/projects/sections/${sectionId}/change-register-records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getHistoricalRateComparison: (params: { master_item_id?: number; query?: string; base_year?: number }) => {
    const q = new URLSearchParams();
    if (params.master_item_id) q.append('master_item_id', String(params.master_item_id));
    if (params.query) q.append('query', params.query);
    if (params.base_year) q.append('base_year', String(params.base_year));
    return request<any>(`/projects/rates/historical-comparison?${q.toString()}`);
  },

  downloadProjectExcel: (projectId: number, mode: 'consolidated' | 'separate', targetSectionId?: number) =>
    downloadFile(
      `/projects/${projectId}/export/excel`,
      { mode, target_section_id: targetSectionId },
      `Project_${projectId}_${mode}.xlsx`
    ),

  getSystemTemplates: () => request<any[]>('/projects/system/templates'),

  // Master BOQ Working Workspace
  getActiveMasterBOQ: (projectId?: number) =>
    request<MasterBOQ>(`/master-boqs/active${projectId ? `?project_id=${projectId}` : ''}`),

  listMasterBOQs: () => request<MasterBOQ[]>('/master-boqs'),

  createMasterBOQ: (data: MasterBOQCreate) =>
    request<MasterBOQ>('/master-boqs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getMasterBOQ: (id: number) => request<MasterBOQ>(`/master-boqs/${id}`),

  updateMasterBOQ: (id: number, data: MasterBOQUpdate) =>
    request<MasterBOQ>(`/master-boqs/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteMasterBOQ: (id: number) =>
    request<{ success: boolean; message: string }>(`/master-boqs/${id}`, { method: 'DELETE' }),

  addRatesToMasterBOQ: (boqId: number, rateItemIds: number[]) =>
    request<AddRatesToBOQResponse>(`/master-boqs/${boqId}/items/from-rates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rate_item_ids: rateItemIds }),
    }),

  addCustomItemToMasterBOQ: (boqId: number, data: MasterBOQItemCreate) =>
    request<MasterBOQItem>(`/master-boqs/${boqId}/items/custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  updateMasterBOQItem: (boqId: number, itemId: number, data: MasterBOQItemUpdate) =>
    request<MasterBOQItem>(`/master-boqs/${boqId}/items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  deleteMasterBOQItem: (boqId: number, itemId: number) =>
    request<{ success: boolean; deleted_item_id: number }>(`/master-boqs/${boqId}/items/${itemId}`, {
      method: 'DELETE',
    }),

  bulkDeleteMasterBOQItems: (boqId: number, itemIds: number[]) =>
    request<{ success: boolean; deleted_count: number }>(`/master-boqs/${boqId}/items/bulk-delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_ids: itemIds }),
    }),

  duplicateMasterBOQItem: (boqId: number, itemId: number) =>
    request<MasterBOQItem>(`/master-boqs/${boqId}/items/${itemId}/duplicate`, {
      method: 'POST',
    }),

  reorderMasterBOQItems: (boqId: number, itemOrders: { id: number; sort_order: number }[]) =>
    request<{ success: boolean; message: string }>(`/master-boqs/${boqId}/reorder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_orders: itemOrders }),
    }),

  downloadMasterBOQExcel: (boqId: number, filename?: string) =>
    downloadFile(`/master-boqs/${boqId}/export/excel`, {}, filename || `Master_BOQ_${boqId}.xlsx`),

  downloadMasterBOQPdf: (boqId: number, filename?: string) =>
    downloadFile(`/master-boqs/${boqId}/export/pdf`, {}, filename || `Master_BOQ_${boqId}.pdf`),

  // ── BSR 31-Part Canonical Workflow ──────────────────────────────────────

  listCanonicalParts: () =>
    request<CanonicalBSRPart[]>('/bsr-parts'),

  getPartsLibrary: (params?: { district?: string; province?: string; rate_system?: string }) => {
    const qs = new URLSearchParams();
    if (params?.district) qs.set('district', params.district);
    if (params?.province) qs.set('province', params.province);
    if (params?.rate_system) qs.set('rate_system', params.rate_system);
    return request<PartLibraryItem[]>(`/bsr-parts/library?${qs}`);
  },

  getPartCrossYear: (
    partId: number,
    params?: {
      district?: string;
      province?: string;
      rate_system?: string;
      vat_basis?: string;
      years?: number[];
      search?: string;
      page?: number;
      page_size?: number;
    },
  ) => {
    const qs = new URLSearchParams();
    if (params?.district) qs.set('district', params.district);
    if (params?.province) qs.set('province', params.province);
    if (params?.rate_system) qs.set('rate_system', params.rate_system);
    if (params?.vat_basis) qs.set('vat_basis', params.vat_basis);
    if (params?.years?.length) qs.set('years', params.years.join(','));
    if (params?.search) qs.set('search', params.search);
    if (params?.page) qs.set('page', String(params.page));
    if (params?.page_size) qs.set('page_size', String(params.page_size));
    return request<CrossYearPartData>(`/bsr-parts/${partId}/cross-year?${qs}`);
  },

  getImportBreakdown: (sourceFileId: number) =>
    request<BSRImportBreakdown>(`/bsr-parts/import-breakdown/${sourceFileId}`),

  classifyItems: (rateSystem = 'BSR', forceRemap = false) =>
    request<{ success: boolean; mapped: number; needs_review: number; unchanged: number }>(
      `/bsr-parts/classify?rate_system=${rateSystem}&force_remap=${forceRemap}`,
      { method: 'POST' },
    ),

  seedTemplateMappings: () =>
    request<{ success: boolean; created: number }>('/bsr-parts/seed-template-mappings', {
      method: 'POST',
    }),

  createPartSelection: (partId: number, data?: { project_id?: number; name?: string }) =>
    request<ProjectPartSelection>(`/bsr-parts/${partId}/selections`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    }),

  listPartSelections: (params?: { part_id?: number; project_id?: number }) => {
    const qs = new URLSearchParams();
    if (params?.part_id) qs.set('part_id', String(params.part_id));
    if (params?.project_id) qs.set('project_id', String(params.project_id));
    return request<ProjectPartSelection[]>(`/bsr-parts/selections?${qs}`);
  },

  getPartSelection: (selectionId: number) =>
    request<ProjectPartSelection>(`/bsr-parts/selections/${selectionId}`),

  deletePartSelection: (selectionId: number) =>
    request<{ success: boolean; deleted_id: number }>(`/bsr-parts/selections/${selectionId}`, {
      method: 'DELETE',
    }),

  addItemsToSelection: (
    selectionId: number,
    rateItemIds: number[],
    allowDuplicates = false,
    replaceExistingIds?: number[],
  ) =>
    request<AddItemsResult>(`/bsr-parts/selections/${selectionId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rate_item_ids: rateItemIds,
        allow_duplicates: allowDuplicates,
        replace_existing_ids: replaceExistingIds,
      }),
    }),

  updatePartItem: (itemId: number, data: Partial<ProjectPartItem>) =>
    request<ProjectPartItem>(`/bsr-parts/selections/items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  duplicatePartItem: (itemId: number) =>
    request<ProjectPartItem>(`/bsr-parts/selections/items/${itemId}/duplicate`, {
      method: 'POST',
    }),

  removePartItem: (itemId: number) =>
    request<{ success: boolean; removed_id: number }>(
      `/bsr-parts/selections/items/${itemId}`,
      { method: 'DELETE' },
    ),

  getPartItemHistory: (itemId: number) =>
    request<ProjectPartItemHistoryRecord[]>(`/bsr-parts/selections/items/${itemId}/history`),

  reorderPartItems: (selectionId: number, itemOrders: { id: number; sort_order: number }[]) =>
    request<{ success: boolean; message: string }>(`/bsr-parts/selections/${selectionId}/reorder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itemOrders),
    }),

  downloadPartExcel: (selectionId: number, filename?: string) =>
    downloadFile(
      `/bsr-parts/selections/${selectionId}/export/excel`,
      {},
      filename || `BSR_Part_Selection_${selectionId}.xlsx`,
    ),

  downloadPartPdf: (selectionId: number, filename?: string) =>
    downloadFile(
      `/bsr-parts/selections/${selectionId}/export/pdf`,
      {},
      filename || `BSR_Part_Selection_${selectionId}.pdf`,
    ),
};
