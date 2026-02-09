/**
 * User Dashboard - SKU tracking overview with price charts
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { UserMenu } from '../components/auth/UserMenu';
import { AlertBell } from '../components/alerts/AlertBell';
import { ProductDetail } from '../components/products/ProductDetail';
import { skuApi, SKU, SKUListResponse } from '../services/api';

export function Dashboard() {
  const { user } = useAuth();
  const [skus, setSkus] = useState<SKU[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [newSku, setNewSku] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<SKU | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  // Fetch SKUs
  const fetchSkus = async () => {
    try {
      setIsLoading(true);
      const response = await skuApi.list({ 
        page, 
        page_size: pageSize,
        search: search || undefined 
      });
      setSkus(response.items);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SKUs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSkus();
  }, [page]);

  // Search handler
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchSkus();
  };

  // Add SKU handler
  const handleAddSku = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSku.trim()) return;

    setIsAdding(true);
    try {
      await skuApi.create({ sku_code: newSku.trim() });
      setNewSku('');
      fetchSkus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add SKU');
    } finally {
      setIsAdding(false);
    }
  };

  // Delete SKU handler
  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Remove this SKU from tracking?')) return;
    
    try {
      await skuApi.delete(id);
      fetchSkus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete SKU');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Noon Price Tracker</h1>
          <div className="flex items-center gap-4">
            <AlertBell />
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Welcome */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900">
            Welcome, {user?.full_name || user?.email}!
          </h2>
          <p className="text-gray-600">Track price changes on your favorite Noon products.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-full">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Tracked Products</p>
                <p className="text-2xl font-bold text-gray-900">{total}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-full">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Price Drops</p>
                <p className="text-2xl font-bold text-gray-900">-</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-full">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{skus.filter(s => s.target_price).length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Add SKU Form */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-medium mb-4">Add New SKU</h3>
          <form onSubmit={handleAddSku} className="flex gap-4">
            <input
              type="text"
              value={newSku}
              onChange={(e) => setNewSku(e.target.value)}
              placeholder="Enter Noon SKU (e.g., N50910931A)"
              className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={isAdding || !newSku.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isAdding ? 'Adding...' : 'Add SKU'}
            </button>
          </form>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleSearch} className="flex gap-4">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by SKU or product name..."
              className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700"
            >
              Search
            </button>
          </form>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
            <button 
              onClick={() => setError(null)} 
              className="float-right text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}

        {/* SKU List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-medium">Your Tracked SKUs ({total})</h3>
            <p className="text-sm text-gray-500">Click a product to view price history</p>
          </div>

          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : skus.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No SKUs tracked yet. Add one above to get started!
            </div>
          ) : (
            <>
              <div className="divide-y divide-gray-200">
                {skus.map((sku) => (
                  <div 
                    key={sku.id} 
                    onClick={() => setSelectedProduct(sku)}
                    className="p-6 flex items-center justify-between hover:bg-blue-50 cursor-pointer transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                          {sku.sku}
                        </span>
                        {sku.target_price && (
                          <span className="text-sm text-green-600 bg-green-50 px-2 py-1 rounded">
                            Target: SAR {sku.target_price}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-gray-900 font-medium">
                        {sku.product_name || 'Unknown Product'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {sku.brand || 'Unknown Brand'} • {sku.category || 'Uncategorized'}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={(e) => handleDelete(sku.id, e)}
                        className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded hover:bg-red-50"
                      >
                        Remove
                      </button>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} of {total}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-sm">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <ProductDetail
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onUpdate={fetchSkus}
        />
      )}
    </div>
  );
}

export default Dashboard;
