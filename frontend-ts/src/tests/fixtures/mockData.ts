import { Competitor, Alert, ApiResponse } from '../../types';

export const mockCompetitorData: Competitor[] = [
  {
    id: '1',
    name: 'Competitor A',
    domain: 'competitor-a.com',
    status: 'active',
    marketShare: 25.5,
    lastUpdated: '2024-01-15T10:00:00Z',
    metrics: {
      revenue: 1500000,
      customerCount: 5000,
      growthRate: 15.5,
      avgRating: 4.2,
    },
    tags: ['enterprise', 'saas'],
  },
  {
    id: '2',
    name: 'Competitor B',
    domain: 'competitor-b.com',
    status: 'active',
    marketShare: 18.3,
    lastUpdated: '2024-01-14T15:30:00Z',
    metrics: {
      revenue: 800000,
      customerCount: 3000,
      growthRate: 12.0,
      avgRating: 4.5,
    },
    tags: ['smb', 'freemium'],
  },
  {
    id: '3',
    name: 'Competitor C',
    domain: 'competitor-c.com',
    status: 'monitoring',
    marketShare: 15.2,
    lastUpdated: '2024-01-13T08:45:00Z',
    metrics: {
      revenue: 600000,
      customerCount: 2000,
      growthRate: 8.5,
      avgRating: 3.9,
    },
    tags: ['startup', 'ai'],
  },
];

export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    title: 'Competitor A Price Drop',
    message: 'Competitor A reduced their pro plan pricing by 10%',
    severity: 'high',
    category: 'price',
    timestamp: '2024-01-15T10:00:00Z',
    competitorId: '1',
    competitorName: 'Competitor A',
    actionUrl: '/competitors/1',
    metadata: { priceChange: -10 },
  },
  {
    id: 'alert-2',
    title: 'New Feature Launch',
    message: 'Competitor C launched a new AI-powered feature',
    severity: 'medium',
    category: 'product',
    timestamp: '2024-01-14T14:30:00Z',
    competitorId: '3',
    competitorName: 'Competitor C',
    actionUrl: '/competitors/3',
  },
  {
    id: 'alert-3',
    title: 'Market Share Update',
    message: 'Competitor B gained 2% market share',
    severity: 'low',
    category: 'marketing',
    timestamp: '2024-01-13T09:15:00Z',
    competitorId: '2',
    competitorName: 'Competitor B',
  },
];

export const mockApiResponse = <T>(data: T): ApiResponse<T> => ({
  data,
  status: 200,
  message: 'Success',
});

export const mockApiError = (message: string, code = 500): ApiResponse<null> => ({
  data: null,
  status: code,
  message,
});
