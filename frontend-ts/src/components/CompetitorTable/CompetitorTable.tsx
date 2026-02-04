import React, { useState, useMemo } from 'react';
import type {
  CompetitorTableProps,
  ProductComparison,
  SortConfig,
  SortField,
  SortDirection,
} from '../../types/competitor.types';
import { TableHeader } from './TableHeader';
import { TableRow } from './TableRow';
import { TableSkeleton } from './TableSkeleton';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';

export const CompetitorTable: React.FC<CompetitorTableProps> = ({
  data = [],
  isLoading = false,
  error = null,
  onRefresh,
  enableSorting = true,
  showPriceDifference = true,
  showPercentage = true,
  maxCompetitorsToShow = 5,
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'productName',
    direction: 'asc',
  });

  // Sort handler
  const handleSort = (field: SortField) => {
    if (!enableSorting) return;

    setSortConfig((prev) => ({
      field,
      direction:
        prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Sorted data
  const sortedData = useMemo(() => {
    if (!data || data.length === 0) return [];

    const sorted = [...data].sort((a, b) => {
      const { field, direction } = sortConfig;
      let aValue: number | string = 0;
      let bValue: number | string = 0;

      switch (field) {
        case 'productName':
          aValue = a.productName.toLowerCase();
          bValue = b.productName.toLowerCase();
          break;
        case 'ourPrice':
          aValue = a.ourPrice;
          bValue = b.ourPrice;
          break;
        case 'lowestCompetitorPrice':
          aValue = a.lowestCompetitorPrice;
          bValue = b.lowestCompetitorPrice;
          break;
        case 'averageCompetitorPrice':
          aValue = a.averageCompetitorPrice;
          bValue = b.averageCompetitorPrice;
          break;
        case 'priceDifference':
          aValue = a.priceDifference;
          bValue = b.priceDifference;
          break;
        case 'priceDifferencePercentage':
          aValue = a.priceDifferencePercentage;
          bValue = b.priceDifferencePercentage;
          break;
        default:
          return 0;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return direction === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });

    return sorted;
  }, [data, sortConfig]);

  // Loading state
  if (isLoading) {
    return (
      <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <TableSkeleton rows={5} />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <ErrorState error={error} onRetry={onRefresh} />
      </div>
    );
  }

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <EmptyState onRefresh={onRefresh} />
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <TableHeader
            sortConfig={sortConfig}
            onSort={handleSort}
            enableSorting={enableSorting}
            showPriceDifference={showPriceDifference}
            showPercentage={showPercentage}
          />
          <tbody className="divide-y divide-gray-200 bg-white">
            {sortedData.map((product) => (
              <TableRow
                key={product.productId}
                product={product}
                showPriceDifference={showPriceDifference}
                showPercentage={showPercentage}
                maxCompetitorsToShow={maxCompetitorsToShow}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer with data info */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {sortedData.length} product
            {sortedData.length !== 1 ? 's' : ''}
          </span>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="flex items-center gap-1 text-blue-600 hover:text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-2 py-1"
              aria-label="Refresh data"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
          )}
        </div>
      </div>
    </div>
  );
};