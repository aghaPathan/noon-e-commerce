import React from 'react';

interface EmptyStateProps {
  onRefresh?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onRefresh }) => {
  return (
    <div className="text-center py-12">
      <p className="text-gray-500 mb-4">No data available</p>
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh
        </button>
      )}
    </div>
  );
};

export default EmptyState;
