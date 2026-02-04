/**
 * Shared TypeScript types for the application
 */

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertCategory = 'price' | 'product' | 'marketing' | 'review';

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  category: AlertCategory;
  timestamp: string;
  competitorId?: string;
  competitorName?: string;
  actionUrl?: string;
  metadata?: Record<string, unknown>;
}

export interface Competitor {
  id: string;
  name: string;
  domain: string;
  status: 'active' | 'inactive' | 'monitoring';
  marketShare: number;
  lastUpdated: string;
  metrics?: {
    revenue?: number;
    customerCount?: number;
    growthRate?: number;
    avgRating?: number;
  };
  tags?: string[];
}

export interface ApiClientConfig {
  baseUrl: string;
  bearerToken: string;
  timeout?: number;
}

// Aliases for backwards compatibility
export type CompetitorData = Competitor;

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}