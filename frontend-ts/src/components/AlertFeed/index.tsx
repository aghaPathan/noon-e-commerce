import React from 'react';
import { Alert } from '../../types';
import { PriceAlert } from '../../types/alert.types';
import { AlertItem } from './AlertItem';
import { EmptyState } from './EmptyState';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';

// Support both Alert and PriceAlert types
type AlertType = Alert | PriceAlert;

interface AlertFeedProps {
  alerts: AlertType[];
  onDismiss?: (alertId: string) => void;
  maxHeight?: string;
  isLoading?: boolean;
  error?: string | null;
}

export const AlertFeed: React.FC<AlertFeedProps> = ({
  alerts,
  onDismiss,
  maxHeight = '400px',
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (alerts.length === 0) {
    return <EmptyState />;
  }

  return (
    <div style={{ maxHeight, overflowY: 'auto' }} className="space-y-3">
      {alerts.map((alert) => (
        <AlertItem
          key={alert.id}
          alert={alert}
          onDismiss={onDismiss ? () => onDismiss(alert.id) : undefined}
        />
      ))}
    </div>
  );
};

export default AlertFeed;
