import React, { useEffect, useState } from 'react';
import { Package, Search, Download, TrendingUp, Layers, IndianRupee, ShoppingBag, ArrowUpRight } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { productApi } from '../services/productApi';
import { reportApi } from '../services/reportApi';
import { Product } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useNavigate } from 'react-router-dom';

import { useDebounce } from '../hooks/useDebounce';

export const Products: React.FC = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('total_revenue');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchProducts = async (currentPage = page, currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await productApi.list({
        page: currentPage,
        page_size: pageSize,
        search: currentSearch || undefined,
        category: category || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setProducts(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to fetch products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(page, debouncedSearch);
  }, [page, debouncedSearch, category, sortBy, sortOrder]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts(1, search);
  };

  const handleFilterDashboardByProduct = (productId: number) => {
    navigate(`/?productId=${productId}`);
  };

  // Top stats calculations from current items
  const totalUnits = products.reduce((acc, p) => acc + p.total_units_sold, 0);
  const totalProductOrders = products.reduce((acc, p) => acc + p.total_orders, 0);
  const totalCatalogRev = products.reduce((acc, p) => acc + p.total_revenue, 0);
  const topProduct = products.length > 0 ? products[0] : null;

  return (
    <div>
      <Header
        title="Product Analytics & Catalog"
        subtitle="Track total units sold, total orders, gross sales revenue, average revenue per order, and percentage contribution by SKU"
        action={
          <Button
            size="sm"
            variant="outline"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => reportApi.downloadProducts('xlsx')}
          >
            Export Products
          </Button>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Top Product KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="shadow-2xs">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Catalog SKUs</span>
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight">{formatNumber(total)}</span>
            <p className="text-[11px] text-slate-500 mt-1">Active registered products</p>
          </Card>

          <Card className="shadow-2xs">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Total Units Sold</span>
            <span className="text-2xl font-extrabold text-indigo-600 tracking-tight">{formatNumber(totalUnits)}</span>
            <p className="text-[11px] text-slate-500 mt-1">Across listed catalog items</p>
          </Card>

          <Card className="shadow-2xs">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Total Orders</span>
            <span className="text-2xl font-extrabold text-blue-600 tracking-tight">{formatNumber(totalProductOrders)}</span>
            <p className="text-[11px] text-slate-500 mt-1">From qualifying product orders</p>
          </Card>

          <Card className="shadow-2xs">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Catalog Gross Revenue</span>
            <span className="text-2xl font-extrabold text-emerald-600 tracking-tight">{formatCurrency(totalCatalogRev)}</span>
            <p className="text-[11px] text-slate-500 mt-1">From qualifying order items</p>
          </Card>

          <Card className="shadow-2xs">
            <span className="text-xs font-semibold text-slate-500 block mb-1">Top Contributing Product</span>
            <span className="text-sm font-bold text-slate-900 block truncate" title={topProduct?.product_name || 'N/A'}>
              {topProduct?.product_name || 'N/A'}
            </span>
            <p className="text-[11px] text-indigo-600 font-semibold mt-1">
              {topProduct ? `${topProduct.revenue_contribution_pct.toFixed(1)}% of total revenue` : ''}
            </p>
          </Card>
        </div>

        {/* Filters */}
        <div className="glass-card p-4 rounded-xl space-y-3 shadow-xs">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search product name or SKU..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
              />
            </div>

            <input
              type="text"
              placeholder="Category"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs min-w-[140px]"
            />

            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split('-');
                setSortBy(sb);
                setSortOrder(so);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
            >
              <option value="total_revenue-desc">Highest Revenue</option>
              <option value="total_units_sold-desc">Most Units Sold</option>
              <option value="total_orders-desc">Most Orders</option>
              <option value="avg_revenue_per_order-desc">Highest Avg Revenue / Order</option>
              <option value="product_name-asc">Product Name (A-Z)</option>
            </select>

            <Button size="sm" type="submit">
              Filter
            </Button>
          </form>
        </div>

        {/* Product Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-indigo-600" />
              Product Performance ({total})
            </h3>
            <span className="text-xs text-slate-500">Aggregated from qualifying order transactions</span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={8} />
            </div>
          ) : products.length === 0 ? (
            <EmptyState
              title="No products found"
              description="Upload an Excel file with product and order data to view product metrics."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3.5 pl-6">Product Name</th>
                    <th className="p-3.5">SKU / Code</th>
                    <th className="p-3.5">Category</th>
                    <th className="p-3.5 text-right">Unit Price</th>
                    <th className="p-3.5 text-center">Units Sold</th>
                    <th className="p-3.5 text-center">Total Orders</th>
                    <th className="p-3.5 text-right">Total Revenue</th>
                    <th className="p-3.5 text-right">Avg Rev / Order</th>
                    <th className="p-3.5 text-right">Revenue Contribution</th>
                    <th className="p-3.5 text-right pr-6">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {products.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-semibold text-slate-900 max-w-[220px] truncate">
                        {p.product_name}
                      </td>

                      <td className="p-3.5 font-mono text-slate-600">
                        {p.sku || <span className="text-slate-400">-</span>}
                      </td>

                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-medium text-[11px]">
                          {p.category || 'General'}
                        </span>
                      </td>

                      <td className="p-3.5 text-right text-slate-800 font-medium">
                        {formatCurrency(p.price)}
                      </td>

                      <td className="p-3.5 text-center font-bold text-indigo-600">
                        {formatNumber(p.total_units_sold)}
                      </td>

                      <td className="p-3.5 text-center text-slate-600">
                        {p.total_orders}
                      </td>

                      <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">
                        {formatCurrency(p.total_revenue)}
                      </td>

                      <td className="p-3.5 text-right font-semibold text-slate-800">
                        {formatCurrency(p.avg_revenue_per_order || (p.total_orders > 0 ? p.total_revenue / p.total_orders : 0))}
                      </td>

                      <td className="p-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="w-14 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-indigo-600 h-full rounded-full"
                              style={{ width: `${Math.min(p.revenue_contribution_pct, 100)}%` }}
                            />
                          </div>
                          <span className="font-bold text-slate-700 text-xs w-10">
                            {p.revenue_contribution_pct.toFixed(1)}%
                          </span>
                        </div>
                      </td>

                      <td className="p-3.5 text-right pr-6">
                        <button
                          onClick={() => handleFilterDashboardByProduct(p.id)}
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-1 rounded-md border border-indigo-200 transition-colors shadow-2xs"
                          title="Filter Business Dashboard by this Product"
                        >
                          Dashboard <ArrowUpRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <Pagination
            currentPage={page}
            totalPages={totalPages}
            totalItems={total}
            pageSize={pageSize}
            onPageChange={setPage}
          />
        </div>
      </div>
    </div>
  );
};
