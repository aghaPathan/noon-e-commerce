/**
 * ProductDetail - Modal showing product details and price history chart
 */

import { useState, useEffect } from 'react';
import { SKU, PriceHistoryResponse, priceApi } from '../../services/api';
import { PriceChart } from '../charts/PriceChart';

interface ProductDetailProps {
  product: SKU;
  onClose: () => void;
  onUpdate?: () => void;
}

export function ProductDetail({ product, onClose, onUpdate }: ProductDetailProps) {
  const [priceHistory, setPriceHistory] = useState<PriceHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await priceApi.getHistory(product.id, days);
        setPriceHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load price history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [product.id, days]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div>
            <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
              {product.sku}
            </span>
            <h2 className="text-xl font-bold mt-2">
              {product.product_name || 'Unknown Product'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Product Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Brand</p>
              <p className="font-medium">{product.brand || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Category</p>
              <p className="font-medium">{product.category || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Target Price</p>
              <p className="font-medium">
                {product.target_price ? `SAR ${product.target_price}` : 'Not set'}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Notifications</p>
              <p className="font-medium">
                {product.notify_on_drop ? '✅ Enabled' : '❌ Disabled'}
              </p>
            </div>
          </div>

          {/* Price Statistics */}
          {priceHistory && priceHistory.history.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-blue-600">Current Price</p>
                <p className="text-xl font-bold text-blue-700">
                  SAR {priceHistory.current_price?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-green-600">Lowest ({days}d)</p>
                <p className="text-xl font-bold text-green-700">
                  SAR {priceHistory.min_price?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <p className="text-sm text-red-600">Highest ({days}d)</p>
                <p className="text-xl font-bold text-red-700">
                  SAR {priceHistory.max_price?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-purple-600">Average ({days}d)</p>
                <p className="text-xl font-bold text-purple-700">
                  SAR {priceHistory.avg_price?.toFixed(2) || 'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* Day selector */}
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-gray-600">Time range:</span>
            <div className="flex gap-2">
              {[7, 14, 30, 60, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-3 py-1 text-sm rounded ${
                    days === d
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          {/* Price Chart */}
          <div className="bg-white border rounded-lg p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-64 text-red-500">
                {error}
              </div>
            ) : priceHistory ? (
              <PriceChart
                history={priceHistory.history}
                title={`Price History - ${product.product_name || product.sku}`}
                height={350}
              />
            ) : null}
          </div>

          {/* Noon Link */}
          {product.url && (
            <div className="mt-6">
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800"
              >
                <span>View on Noon.com</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;
