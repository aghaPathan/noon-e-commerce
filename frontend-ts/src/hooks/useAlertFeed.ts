import { useState, useEffect, useCallback, useRef } from 'react';
import { PriceAlert, AlertFeedState } from '../types/alert.types';
import { apiClient } from '../services/api-client';

interface UseAlertFeedOptions {
  autoRefreshInterval?: number;
  maxAlerts?: number;
}

export const useAlertFeed = (options: UseAlertFeedOptions = {}) => {
  const { autoRefreshInterval, maxAlerts } = options;
  
  const [state, setState] = useState<AlertFeedState>({
    alerts: [],
    isLoading: true,
    error: null,
    lastUpdated: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const alerts = await apiClient.fetchAlerts<PriceAlert>();
      
      // Sort by timestamp (newest first)
      const sortedAlerts = [...alerts].sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      // Limit alerts if maxAlerts is specified
      const limitedAlerts = maxAlerts 
        ? sortedAlerts.slice(0, maxAlerts)
        : sortedAlerts;

      setState({
        alerts: limitedAlerts,
        isLoading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch alerts',
      }));
    }
  }, [maxAlerts]);

  const refresh = useCallback(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  useEffect(() => {
    if (autoRefreshInterval && autoRefreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchAlerts();
      }, autoRefreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [autoRefreshInterval, fetchAlerts]);

  return {
    ...state,
    refresh,
  };
};