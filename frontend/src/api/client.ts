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

  getFilterOptions: () => request<FilterOptions>('/rates/filters'),

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
};
