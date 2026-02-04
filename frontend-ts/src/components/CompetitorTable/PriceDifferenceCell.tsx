import React from 'react';

interface PriceDifferenceCellProps {
  difference: number;
  percentage?: number;
  currency?: string;
  isPercentage?: boolean;
}

export const PriceDifferenceCell: React.FC<PriceDifferenceCellProps> = ({ 
  difference, 
  percentage,
  currency,
  isPercentage = false 
}) => {
  const isPositive = difference > 0;
  const color = isPositive ? 'text-red-500' : difference < 0 ? 'text-green-500' : 'text-gray-500';
  
  if (isPercentage) {
    return (
      <td className={`whitespace-nowrap px-6 py-4 text-right text-sm ${color}`}>
        {isPositive ? '+' : ''}{difference.toFixed(1)}%
      </td>
    );
  }

  return (
    <td className={`whitespace-nowrap px-6 py-4 text-right text-sm ${color}`}>
      {isPositive ? '+' : ''}{currency || ''}{Math.abs(difference).toFixed(2)}
      {percentage !== undefined && ` (${percentage.toFixed(1)}%)`}
    </td>
  );
};

export default PriceDifferenceCell;
