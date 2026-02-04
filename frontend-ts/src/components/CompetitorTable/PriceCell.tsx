import React from 'react';

interface PriceCellProps {
  price: number;
  currency: string;
}

export const PriceCell: React.FC<PriceCellProps> = ({ price, currency }) => {
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);

  return (
    <td className="whitespace-nowrap px-6 py-4 text-right">
      <span className="text-sm font-medium text-gray-900">{formattedPrice}</span>
    </td>
  );
};