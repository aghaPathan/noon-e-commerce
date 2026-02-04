import React from 'react';

export const LoadingState: React.FC = () => {
  return (
    <div className="space-y-4" role="status" aria-label="Loading alerts">
      {[...Array(3)].map((_, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 animate-pulse"
        >
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-16 h-16 bg-gray-200 rounded-md"></div>
            </div>
            <div className="flex-1 space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="flex gap-2">
                <div className="h-5 bg-gray-200 rounded w-20"></div>
                <div className="h-5 bg-gray-200 rounded w-20"></div>
                <div className="h-5 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="h-3 bg-gray-200 rounded w-32"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};