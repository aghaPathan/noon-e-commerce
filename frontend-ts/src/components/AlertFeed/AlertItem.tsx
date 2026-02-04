import React from 'react';
import { Alert } from '../../types';
import { PriceAlert } from '../../types/alert.types';
import { formatDistanceToNow } from 'date-fns';

// Union type to support both alert formats
type AlertType = Alert | PriceAlert;

// Type guard to check if alert is a PriceAlert
function isPriceAlert(alert: AlertType): alert is PriceAlert {
  return 'productName' in alert && 'oldPrice' in alert && 'newPrice' in alert;
}

interface AlertItemProps {
  alert: AlertType;
  onDismiss?: () => void;
  onClick?: (alert: AlertType) => void;
}

export const AlertItem: React.FC<AlertItemProps> = ({ alert, onDismiss, onClick }) => {
  const formatTimestamp = (date: Date | string): string => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return formatDistanceToNow(dateObj, { addSuffix: true });
  };

  const handleClick = () => {
    if (onClick) {
      onClick(alert);
    }
  };

  // Render PriceAlert format
  if (isPriceAlert(alert)) {
    const {
      productName,
      productImage,
      oldPrice,
      newPrice,
      discountPercentage,
      timestamp,
      currency = '$',
    } = alert;

    const formatPrice = (price: number): string => `${currency}${price.toFixed(2)}`;

    return (
      <div
        className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-4 border border-gray-200 cursor-pointer"
        onClick={handleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        aria-label={`Price drop alert for ${productName}`}
      >
        <div className="flex gap-4">
          {productImage && (
            <div className="flex-shrink-0">
              <img
                src={productImage}
                alt={productName}
                className="w-16 h-16 object-cover rounded-md"
                loading="lazy"
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 mb-2 truncate">
              {productName}
            </h3>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-sm text-gray-500 line-through">
                {formatPrice(oldPrice)}
              </span>
              <span className="text-lg font-bold text-green-600">
                {formatPrice(newPrice)}
              </span>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                -{discountPercentage.toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center text-xs text-gray-500">
              <time dateTime={new Date(timestamp).toISOString()}>
                {formatTimestamp(timestamp)}
              </time>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render generic Alert format
  const { title, message, severity, timestamp } = alert;

  const severityColors = {
    low: 'bg-gray-100 text-gray-800 border-gray-200',
    medium: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    high: 'bg-orange-50 text-orange-800 border-orange-200',
    critical: 'bg-red-50 text-red-800 border-red-200',
  };

  return (
    <div
      className={`rounded-lg shadow-sm p-4 border ${severityColors[severity]} ${onClick ? 'cursor-pointer hover:shadow-md' : ''}`}
      onClick={onClick ? handleClick : undefined}
      role={onClick ? 'button' : 'article'}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-sm font-semibold mb-1">{title}</h3>
          <p className="text-sm opacity-90">{message}</p>
          <div className="text-xs opacity-70 mt-2">
            {formatTimestamp(timestamp)}
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
            className="ml-2 text-gray-400 hover:text-gray-600"
            aria-label="Dismiss alert"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};
