import React, { useState } from 'react';
import type { ProductComparison } from '../../types/competitor.types';
import { PriceCell } from './PriceCell';
import { PriceDifferenceCell } from './PriceDifferenceCell';
import { PricePositionBadge } from './PricePositionBadge';
import { CompetitorPricesPopover } from './CompetitorPricesPopover';

interface TableRowProps {
  product: ProductComparison;
  showPriceDifference: boolean;
  showPercentage: boolean;
  maxCompetitorsToShow: number;
}

export const TableRow: React.FC<TableRowProps> = ({
  product,
  showPriceDifference,
  showPercentage,
  maxCompetitorsToShow,
}) => {
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="whitespace-nowrap px-6 py-4">
        <div className="flex flex-col">
          <div className="text-sm font-medium text-gray-900">
            {product.productName}
          </div>
          <div className="text-xs text-gray-500">SKU: {product.sku}</div>
        </div>
      </td>

      <PriceCell price={product.ourPrice} currency={product.currency} />
      
      <PriceCell
        price={product.lowestCompetitorPrice}
        currency={product.currency}
      />
      
      <PriceCell
        price={product.averageCompetitorPrice}
        currency={product.currency}
      />

      {showPriceDifference && (
        <PriceDifferenceCell
          difference={product.priceDifference}
          currency={product.currency}
        />
      )}

      {showPercentage && (
        <PriceDifferenceCell
          difference={product.priceDifferencePercentage}
          isPercentage
        />
      )}

      <td className="whitespace-nowrap px-6 py-4">
        <PricePositionBadge position={product.pricePosition} />
      </td>

      <td className="whitespace-nowrap px-6 py-4">
        <CompetitorPricesPopover
          competitors={product.competitorPrices}
          maxToShow={maxCompetitorsToShow}
          currency={product.currency}
        />
      </td>
    </tr>
  );
};