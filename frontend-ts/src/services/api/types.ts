// API Types and Interfaces

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
}

export interface RequestConfig extends RequestInit {
  timeout?: number;
  retry?: boolean;
  retryAttempts?: number;
  retryDelay?: number;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
}

// Competitor Types
export interface Competitor {
  id: string;
  name: string;
  domain: string;
  industry: string;
  status: 'active' | 'inactive' | 'pending';
  lastScraped?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CompetitorListParams {
  page?: number;
  limit?: number;
  status?: string;
  industry?: string;
  search?: string;
}

export interface CompetitorListResponse {
  competitors: Competitor[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Price Comparison Types
export interface PriceData {
  id: string;
  competitorId: string;
  competitorName: string;
  productName: string;
  productSku?: string;
  price: number;
  currency: string;
  availability: 'in_stock' | 'out_of_stock' | 'pre_order' | 'discontinued';
  url: string;
  scrapedAt: string;
  metadata?: Record<string, unknown>;
}

export interface PriceComparisonParams {
  competitorIds?: string[];
  productName?: string;
  productSku?: string;
  minPrice?: number;
  maxPrice?: number;
  availability?: string;
  startDate?: string;
  endDate?: string;
  page?: number;
  limit?: number;
}

export interface PriceComparisonResponse {
  prices: PriceData[];
  summary: {
    averagePrice: number;
    minPrice: number;
    maxPrice: number;
    totalProducts: number;
  };
  total: number;
  page: number;
  limit: number;
}

// Alert Types
export interface Alert {
  id: string;
  type: 'price_drop' | 'price_increase' | 'availability_change' | 'new_competitor';
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  competitorId?: string;
  competitorName?: string;
  productName?: string;
  oldValue?: string | number;
  newValue?: string | number;
  isRead: boolean;
  createdAt: string;
  metadata?: Record<string, unknown>;
}

export interface AlertListParams {
  page?: number;
  limit?: number;
  type?: string;
  severity?: string;
  isRead?: boolean;
  competitorId?: string;
  startDate?: string;
  endDate?: string;
}

export interface AlertListResponse {
  alerts: Alert[];
  unreadCount: number;
  total: number;
  page: number;
  limit: number;
}

export interface AlertUpdatePayload {
  isRead?: boolean;
}

// Auth Types
export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
}

export interface RequestInterceptor {
  onRequest?: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
  onRequestError?: (error: Error) => void | Promise<void>;
}

export interface ResponseInterceptor {
  onResponse?: <T>(response: ApiResponse<T>) => ApiResponse<T> | Promise<ApiResponse<T>>;
  onResponseError?: (error: ApiError) => void | Promise<void>;
}