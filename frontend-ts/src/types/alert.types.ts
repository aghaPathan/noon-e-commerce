export interface PriceAlert {
  id: string;
  productId: string;
  productName: string;
  productUrl?: string;
  productImage?: string;
  oldPrice: number;
  newPrice: number;
  discountPercentage: number;
  timestamp: Date | string;
  currency?: string;
}

export interface AlertFeedProps {
  autoRefreshInterval?: number; // in milliseconds
  maxAlerts?: number;
  enableVirtualization?: boolean;
  onAlertClick?: (alert: PriceAlert) => void;
}

export interface AlertFeedState {
  alerts: PriceAlert[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}