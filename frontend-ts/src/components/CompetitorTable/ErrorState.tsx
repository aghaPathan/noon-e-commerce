import React from 'react';

interface ErrorStateProps {
  message?: string;
  error?: Error | null;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  message, 
  error, 
  onRetry 
}) => {
  const displayMessage = message || error?.message || 'An error occurred';
  
  return (
    <div className="text-center py-12">
      <p className="text-red-500 mb-4">{displayMessage}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState;
