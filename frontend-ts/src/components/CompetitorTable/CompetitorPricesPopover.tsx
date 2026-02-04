import React, { useState } from 'react';
import type { CompetitorPrice } from '../../types/competitor.types';

interface CompetitorPricesPopoverProps {
  competitors: CompetitorPrice[];
  maxToShow?: number;
  currency?: string;
}

export const CompetitorPricesPopover: React.FC<CompetitorPricesPopoverProps> = ({ 
  competitors,
  maxToShow = 5,
  currency = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const displayCompetitors = competitors.slice(0, maxToShow);
  const remaining = competitors.length - maxToShow;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-blue-600 hover:text-blue-800 text-sm underline"
      >
        {competitors.length} competitor{competitors.length !== 1 ? 's' : ''}
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 bg-white shadow-lg rounded-lg p-4 z-10 min-w-[250px] border">
          <h4 className="font-semibold mb-3 text-gray-900">Competitor Prices</h4>
          <ul className="space-y-2">
            {displayCompetitors.map((c) => (
              <li key={c.competitorId} className="flex justify-between items-center text-sm">
                <span className="text-gray-700">{c.competitorName}</span>
                <span className="font-mono text-gray-900">
                  {currency} {c.price.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
          {remaining > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              +{remaining} more competitor{remaining !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default CompetitorPricesPopover;
