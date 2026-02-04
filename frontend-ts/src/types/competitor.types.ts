export interface CompetitorPrice {
  competitorId: string;
  competitorName: string;
  price: number;
  currency: string;
  lastUpdated: string;
  availability: 'in_stock' | 'out_of_stock' | 'limited_stock';
  url?: string;
}

export interface ProductComparison {
  productId: string;
  productName: string;
  sku: string;
  ourPrice: number;
  currency: string;
  competitorPrices: CompetitorPrice[];
  lowestCompetitorPrice: number;
  averageCompetitorPrice: number;
  priceDifference: number;
  priceDifferencePercentage: number;
  pricePosition: 'lowest' | 'competitive' | 'higher' | 'highest';
}

export interface CompetitorTableProps {
  data?: ProductComparison[];
  isLoading?: boolean;
  error?: Error | null;
  onRefresh?: () => void;
  enableSorting?: boolean;
  showPriceDifference?: boolean;
  showPercentage?: boolean;
  maxCompetitorsToShow?: number;
}

export type SortField = 
  | 'productName' 
  | 'ourPrice' 
  | 'lowestCompetitorPrice' 
  | 'averageCompetitorPrice'
  | 'priceDifference'
  | 'priceDifferencePercentage';

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}