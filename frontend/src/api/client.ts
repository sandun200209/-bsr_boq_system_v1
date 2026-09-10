import {
  DashboardMetrics,
  FilterOptions,
  SourceFile,
  RateItem,
  CompareResponse,
  MasterItem,
  MasterSuggestion,
} from '../types';

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...options?.headers,
    },
  });

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

export const api = {
  // Health
  getHealth: () => request<{ status: string; app: string; version: string }>('/health'),
  getDatabaseHealth: () => request<{ status: string; select_1: boolean; pg_trgm_enabled: boolean }>('/health/database'),

  // Dashboard
  getDashboard: () => request<DashboardMetrics>('/dashboard'),

  // Documents
  uploadDocument: (formData: FormData) =>
    request<{
      success: boolean;
      document_id: number;
      job_id: number;
      filename: string;
      items_detected: number;
      valid_items: number;
      needs_review: number;
      rejected_items: number;
      ocr_required: boolean;
      message: string;
    }>('/documents/upload', {
      method: 'POST',
      body: formData,
    }),

  getDocuments: (params?: { province?: string; district?: string; year?: number; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.province) q.set('province', params.province);
    if (params?.district) q.set('district', params.district);
    if (params?.year) q.set('year', params.year.toString());
    if (params?.skip !== undefined) q.set('skip', params.skip.toString());
    if (params?.limit !== undefined) q.set('limit', params.limit.toString());
    return request<SourceFile[]>(`/documents?${q.toString()}`);
  },

  getDocument: (id: number) => request<SourceFile>(`/documents/${id}`),

  // Rates
  getFilterOptions: () => request<FilterOptions>('/rates/filters'),

  searchRates: (params: {
    q?: string;
    province?: string;
    district?: string;
    year?: number;
    revision?: string;
    dataset_type?: string;
    vat_basis?: string;
    category?: string;
    status?: string;
    source_page?: number;
    sheet?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    page?: number;
    page_size?: number;
  }) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        q.set(key, val.toString());
      }
    });
    return request<{
      total: number;
      page: number;
      page_size: number;
      pages: number;
      items: RateItem[];
    }>(`/rates/search?${q.toString()}`);
  },

  getRateItem: (id: number) => request<RateItem>(`/rates/${id}`),

  // Compare
  getCompare: (params: {
    provinces?: string[];
    districts?: string[];
    years?: number[];
    revisions?: string[];
    category?: string;
    vat_basis?: string;
    q?: string;
    base_item_id?: number;
  }) => {
    const q = new URLSearchParams();
    params.provinces?.forEach((p) => q.append('provinces', p));
    params.districts?.forEach((d) => q.append('districts', d));
    params.years?.forEach((y) => q.append('years', y.toString()));
    params.revisions?.forEach((r) => q.append('revisions', r));
    if (params.category) q.set('category', params.category);
    if (params.vat_basis) q.set('vat_basis', params.vat_basis);
    if (params.q) q.set('q', params.q);
    if (params.base_item_id) q.set('base_item_id', params.base_item_id.toString());
    return request<CompareResponse>(`/compare?${q.toString()}`);
  },

  // Review Queue
  getReviewQueue: (params?: {
    source_file_id?: number;
    status?: string;
    category?: string;
    page?: number;
    page_size?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.source_file_id) q.set('source_file_id', params.source_file_id.toString());
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
  getMasterItems: (params?: { q?: string; category?: string; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.q) q.set('q', params.q);
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
};
