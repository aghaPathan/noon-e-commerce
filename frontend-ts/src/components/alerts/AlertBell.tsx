/**
 * AlertBell - Notification bell with unread count badge
 */

import { useState, useEffect, useRef } from 'react';
import { alertsApi, Alert, AlertListResponse } from '../../services/api';

interface AlertBellProps {
  onOpenPanel?: () => void;
}

export function AlertBell({ onOpenPanel }: AlertBellProps) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Fetch unread count on mount
  useEffect(() => {
    const fetchCount = async () => {
      try {
        const data = await alertsApi.getUnreadCount();
        setUnreadCount(data.unread_count);
      } catch (err) {
        console.error('Failed to fetch unread count:', err);
      }
    };
    fetchCount();
    // Refresh every 60s
    const interval = setInterval(fetchCount, 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch alerts when dropdown opens
  useEffect(() => {
    if (isOpen) {
      const fetchAlerts = async () => {
        setIsLoading(true);
        try {
          const data = await alertsApi.list({ page_size: 10, unread_only: false });
          setAlerts(data.items);
          setUnreadCount(data.unread_count);
        } catch (err) {
          console.error('Failed to fetch alerts:', err);
        } finally {
          setIsLoading(false);
        }
      };
      fetchAlerts();
    }
  }, [isOpen]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await alertsApi.markAllRead();
      setUnreadCount(0);
      setAlerts(alerts.map(a => ({ ...a, read_at: new Date().toISOString() })));
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const handleMarkRead = async (alertId: number) => {
    try {
      await alertsApi.markRead(alertId);
      setAlerts(alerts.map(a => 
        a.id === alertId ? { ...a, read_at: new Date().toISOString() } : a
      ));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl z-50 border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b flex justify-between items-center">
            <h3 className="font-medium text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications yet
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    onClick={() => !alert.read_at && handleMarkRead(alert.id)}
                    className={`p-4 hover:bg-gray-50 cursor-pointer ${
                      !alert.read_at ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-full ${
                        alert.change_pct < 0 ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {alert.change_pct < 0 ? (
                          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">
                          {alert.alert_type === 'price_drop' ? 'Price Drop' : 'Price Increase'}
                        </p>
                        <p className="text-sm text-gray-600 truncate">
                          {alert.sku}
                        </p>
                        <p className="text-sm">
                          <span className="text-gray-500">AED {alert.old_price.toFixed(2)}</span>
                          <span className="mx-1">→</span>
                          <span className={alert.change_pct < 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                            AED {alert.new_price.toFixed(2)} ({alert.change_pct > 0 ? '+' : ''}{alert.change_pct}%)
                          </span>
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(alert.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {!alert.read_at && (
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {alerts.length > 0 && (
            <div className="px-4 py-3 bg-gray-50 border-t text-center">
              <button
                onClick={() => {
                  setIsOpen(false);
                  onOpenPanel?.();
                }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AlertBell;
