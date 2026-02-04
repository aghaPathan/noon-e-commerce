import React from 'react';

type PricePosition = 'lowest' | 'competitive' | 'higher' | 'highest' | 'middle';

interface PricePositionBadgeProps {
  position: PricePosition;
}

export const PricePositionBadge: React.FC<PricePositionBadgeProps> = ({ position }) => {
  const colors: Record<PricePosition, string> = {
    lowest: 'bg-green-100 text-green-800',
    competitive: 'bg-blue-100 text-blue-800',
    middle: 'bg-gray-100 text-gray-800',
    higher: 'bg-yellow-100 text-yellow-800',
    highest: 'bg-red-100 text-red-800',
  };
  
  const labels: Record<PricePosition, string> = {
    lowest: 'Lowest',
    competitive: 'Competitive',
    middle: 'Middle',
    higher: 'Higher',
    highest: 'Highest',
  };
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[position]}`}>
      {labels[position]}
    </span>
  );
};

export default PricePositionBadge;
