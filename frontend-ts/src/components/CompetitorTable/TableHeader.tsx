import React from 'react';
import type { SortConfig, SortField } from '../../types/competitor.types';
import { SortIcon } from './SortIcon';

interface TableHeaderProps {
  sortConfig: SortConfig;
  onSort: (field: SortField) => void;
  enableSorting: boolean;
  showPriceDifference: boolean;
  showPercentage: boolean;
}

export const TableHeader: React.FC<TableHeaderProps> = ({
  sortConfig,
  onSort,
  enableSorting,
  showPriceDifference,
  showPercentage,
}) => {
  const headerClass =
    'px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700 bg-gray-50';
  const sortableClass = enableSorting
    ? 'cursor-pointer hover:bg-gray-100 select-none'
    : '';

  const renderHeaderCell = (
    label: string,
    field: SortField,
    align: 'left' | 'right' = 'left'
  ) => (
    <th
      scope="col"
      className={`${headerClass} ${sortableClass} ${
        align === 'right' ? 'text-right' : ''
      }`}
      onClick={() => enableSorting && onSort(field)}
      role={enableSorting ? 'button' : undefined}
      tabIndex={enableSorting ? 0 : undefined}
      onKeyDown={(e) => {
        if (enableSorting && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onSort(field);
        }
      }}
      aria-sort={
        sortConfig.field === field
          ? sortConfig.direction === 'asc'
            ? 'ascending'
            : 'descending'
          : 'none'
      }
    >
      <div className={`flex items-center gap-2 ${align === 'right' ? 'justify-end' : ''}`}>
        {label}
        {enableSorting && (
          <SortIcon
            isActive={sortConfig.field === field}
            direction={sortConfig.direction}
          />
        )}
      </div>
    </th>
  );

  return (
    <thead>
      <tr>
        {renderHeaderCell('Product', 'productName')}
        {renderHeaderCell('Our Price', 'ourPrice', 'right')}
        {renderHeaderCell('Lowest Competitor', 'lowestCompetitorPrice', 'right')}
        {renderHeaderCell('Avg. Competitor', 'averageCompetitorPrice', 'right')}
        {showPriceDifference &&
          renderHeaderCell('Difference', 'priceDifference', 'right')}
        {showPercentage &&
          renderHeaderCell('% Diff', 'priceDifferencePercentage', 'right')}
        <th scope="col" className={headerClass}>
          Position
        </th>
        <th scope="col" className={headerClass}>
          Competitors
        </th>
      </tr>
    </thead>
  );
};