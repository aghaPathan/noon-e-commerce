/**
 * Authenticated API Client
 * Automatically handles token refresh and authentication
 */

import { getValidAccessToken, tokenStorage } from './auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8096';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Request options type
interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  requireAuth?: boolean;
}

// Authenticated fetch wrapper
async function authFetch<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', body, headers = {}, requireAuth = true } = options;

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add auth header if required
  if (requireAuth) {
    const token = await getValidAccessToken();
    if (!token) {
      throw new ApiError(401, 'Not authenticated');
    }
    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Handle 401 - clear tokens and throw
  if (response.status === 401) {
    tokenStorage.clear();
    throw new ApiError(401, 'Session expired');
  }

  // Handle other errors
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.detail || error.message || `Request failed: ${response.status}`,
      error
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// SKU types
export interface SKU {
  id: number;
  sku: string;
  product_name: string | null;
  brand: string | null;
  category: string | null;
  url: string | null;
  image_url: string | null;
  target_price: number | null;
  notify_on_drop: boolean;
  created_at: string;
}

export interface SKUListResponse {
  items: SKU[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SKUCreateData {
  sku_code: string;
  target_price?: number;
}

export interface SKUUpdateData {
  target_price?: number;
  notify_on_drop?: boolean;
}

export interface BulkImportResponse {
  created: number;
  skipped: number;
  sku_codes: string[];
}

// SKU API
export const skuApi = {
  list: (params?: { page?: number; page_size?: number; search?: string; sort_by?: string; sort_order?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.sort_order) searchParams.set('sort_order', params.sort_order);
    
    const query = searchParams.toString();
    return authFetch<SKUListResponse>(`/api/skus${query ? `?${query}` : ''}`);
  },

  get: (id: number) => authFetch<SKU>(`/api/skus/${id}`),

  create: (data: SKUCreateData) => authFetch<SKU>('/api/skus', {
    method: 'POST',
    body: data,
  }),

  update: (id: number, data: SKUUpdateData) => authFetch<SKU>(`/api/skus/${id}`, {
    method: 'PUT',
    body: data,
  }),

  delete: (id: number) => authFetch<void>(`/api/skus/${id}`, {
    method: 'DELETE',
  }),

  bulkImport: (sku_codes: string[]) => authFetch<BulkImportResponse>('/api/skus/bulk', {
    method: 'POST',
    body: { sku_codes },
  }),
};

// Admin types
export interface AdminStats {
  total_users: number;
  total_products: number;
  total_watchlist_items: number;
  total_alerts: number;
  new_users_this_week: number;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

// Admin API
export const adminApi = {
  getStats: () => authFetch<AdminStats>('/api/admin/stats'),
  
  listUsers: (params?: { page?: number; page_size?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    
    const query = searchParams.toString();
    return authFetch<UserListResponse>(`/api/admin/users${query ? `?${query}` : ''}`);
  },

  getUser: (id: number) => authFetch<AdminUser>(`/api/admin/users/${id}`),

  updateUser: (id: number, data: { role?: string; is_active?: boolean }) => 
    authFetch<AdminUser>(`/api/admin/users/${id}`, {
      method: 'PUT',
      body: data,
    }),

  deleteUser: (id: number) => authFetch<void>(`/api/admin/users/${id}`, {
    method: 'DELETE',
  }),
};

// Price History types
export interface PricePoint {
  date: string;
  price: number;
  original_price: number | null;
  discount_pct: number | null;
  in_stock: boolean;
}

export interface PriceHistoryResponse {
  sku: string;
  product_name: string | null;
  current_price: number | null;
  min_price: number | null;
  max_price: number | null;
  avg_price: number | null;
  history: PricePoint[];
}

// Price History API
export const priceApi = {
  getHistory: (skuId: number, days: number = 30) =>
    authFetch<PriceHistoryResponse>(`/api/skus/${skuId}/price-history?days=${days}`),
};

// Alert types
export interface Alert {
  id: number;
  sku: string;
  old_price: number;
  new_price: number;
  change_pct: number;
  alert_type: string;
  read_at: string | null;
  created_at: string;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

// Alerts API
export const alertsApi = {
  list: (params?: { page?: number; page_size?: number; unread_only?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.unread_only) searchParams.set('unread_only', 'true');
    const query = searchParams.toString();
    return authFetch<AlertListResponse>(`/api/alerts${query ? `?${query}` : ''}`);
  },

  getUnreadCount: () => authFetch<{ unread_count: number }>('/api/alerts/unread-count'),

  markRead: (alertId: number) => authFetch<{ success: boolean }>(`/api/alerts/${alertId}/read`, {
    method: 'POST',
  }),

  markAllRead: () => authFetch<{ success: boolean; marked: number }>('/api/alerts/mark-all-read', {
    method: 'POST',
  }),
};

// Export fetch helper for custom endpoints
export { authFetch };
