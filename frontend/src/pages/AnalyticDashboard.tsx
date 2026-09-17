import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Package,
  ShoppingBag,
  IndianRupee,
  Users,
  TrendingUp,
  MapPin,
  Building,
  Mail,
  RefreshCw,
  Search,
  X
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { analyticsApi } from '../services/analyticsApi';
import { productApi } from '../services/productApi';
import {
  GeographicSummaryKPIs,
  DistrictAnalyticsItem,
  PincodeAnalyticsItem,
  PostOfficeAnalyticsItem,
  Product
} from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';

// Colors for visual hierarchy
const BLUE_COLOR = '#3b82f6';
const EMERALD_COLOR = '#10b981';

const DATE_PRESETS = [
  { label: 'All Time', value: 'all' },
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'Last 7 Days', value: 'last_7_days' },
  { label: 'Last 30 Days', value: 'last_30_days' },
  { label: 'This Month', value: 'this_month' },
  { label: 'Previous Month', value: 'last_month' },
  { label: 'Custom Range', value: 'custom' },
];

export const AnalyticDashboard: React.FC = () => {
  // Filter States: Only Date & Product
  const [datePreset, setDatePreset] = useState<string>('all');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedProductId, setSelectedProductId] = useState<number | undefined>(undefined);

  // Products dropdown list & search
  const [products, setProducts] = useState<Product[]>([]);
  const [productSearch, setProductSearch] = useState<string>('');

  // Analytics Data States
  const [summary, setSummary] = useState<GeographicSummaryKPIs | null>(null);
  const [districts, setDistricts] = useState<DistrictAnalyticsItem[]>([]);
  const [pincodes, setPincodes] = useState<PincodeAnalyticsItem[]>([]);
  const [postOffices, setPostOffices] = useState<PostOfficeAnalyticsItem[]>([]);

  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load product list on mount
  useEffect(() => {
    productApi
      .list({ page: 1, page_size: 100, sort_by: 'product_name', sort_order: 'asc' })
      .then((res) => {
        if (res && res.items) {
          setProducts(res.items);
        }
      })
      .catch((err) => console.error('Failed to load products list:', err));
  }, []);

  // Fetch all analytics data on filter change
  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        preset: datePreset,
        startDate: datePreset === 'custom' && startDate ? startDate : undefined,
        endDate: datePreset === 'custom' && endDate ? endDate : undefined,
        productId: selectedProductId,
      };

      const [summaryRes, districtsRes, pincodesRes, postOfficesRes] = await Promise.all([
        analyticsApi.getGeographicOverview(params),
        analyticsApi.getGeographicDistricts(params),
        analyticsApi.getGeographicPincodes({ ...params, limit: 15, sortBy: 'revenue' }),
        analyticsApi.getGeographicPostOffices({ ...params, limit: 15, sortBy: 'revenue' }),
      ]);

      setSummary(summaryRes);
      setDistricts(districtsRes);
      setPincodes(pincodesRes);
      setPostOffices(postOfficesRes);
    } catch (err: any) {
      console.error('Failed to load analytic dashboard:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load analytics dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [datePreset, startDate, endDate, selectedProductId]);

  // Reset all filters
  const handleResetFilters = () => {
    setDatePreset('all');
    setStartDate('');
    setEndDate('');
    setSelectedProductId(undefined);
    setProductSearch('');
  };

  // Filtered product options for dropdown
  const filteredProducts = products.filter((p) =>
    productSearch ? p.product_name.toLowerCase().includes(productSearch.toLowerCase()) : true
  );

  // Custom tooltips
  const CustomTooltip = ({ active, payload, label, unit = 'orders' }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 text-white px-3 py-2 rounded-xl shadow-lg border border-slate-800 text-xs min-w-[170px]">
          <div className="font-bold text-slate-100 border-b border-slate-800 pb-1 mb-1.5 truncate">
            {data.district || data.pincode || data.post_office || label}
          </div>
          <div className="space-y-1">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Orders:</span>
              <span className="font-bold text-white">{formatNumber(data.total_orders || 0)}</span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Revenue:</span>
              <span className="font-bold text-emerald-400">{formatCurrency(data.total_revenue || 0)}</span>
            </div>
            {data.customer_count !== undefined && (
              <div className="flex justify-between items-center text-slate-300">
                <span className="text-slate-400">Customers:</span>
                <span className="font-medium text-slate-200">{formatNumber(data.customer_count || 0)}</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const hasData = summary && (summary.total_orders > 0 || summary.total_revenue > 0);

  return (
    <div className="min-h-screen bg-slate-50/60 pb-16">
      {/* Header */}
      <Header
        title="Analytic Dashboard"
        subtitle="Visual geographic analysis of order count and revenue by District, Pincode, and Post Office"
      />

      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
        {/* 1. Global Filters (Date & Product Only) */}
        <Card className="p-4 bg-white border border-slate-200/90 shadow-2xs rounded-2xl">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            {/* Left: Date Presets & Custom Range */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                <span>Date Filter</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {DATE_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => setDatePreset(preset.value)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                      datePreset === preset.value
                        ? 'bg-indigo-600 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>

              {/* Custom Date Range Inputs */}
              {datePreset === 'custom' && (
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-hidden font-medium text-slate-700"
                  />
                  <span className="text-xs text-slate-400">to</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500 outline-hidden font-medium text-slate-700"
                  />
                </div>
              )}
            </div>

            {/* Right: Product Filter & Reset */}
            <div className="flex items-end gap-3">
              <div className="space-y-2 w-full sm:w-64">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                    <Package className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Product Filter</span>
                  </div>
                  {loading && (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-indigo-600 animate-pulse">
                      <RefreshCw className="w-3 h-3 animate-spin text-indigo-600" />
                      <span>Filtering...</span>
                    </span>
                  )}
                </div>
                <div className="relative">
                  <select
                    value={selectedProductId || ''}
                    disabled={loading}
                    onChange={(e) =>
                      setSelectedProductId(e.target.value ? Number(e.target.value) : undefined)
                    }
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-xl font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-hidden shadow-2xs disabled:bg-slate-50 disabled:text-slate-400"
                  >
                    <option value="">All Products</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.product_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {(datePreset !== 'all' || selectedProductId !== undefined) && (
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={loading}
                  onClick={handleResetFilters}
                  className="text-xs shrink-0 font-semibold"
                >
                  <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
                  Reset
                </Button>
              )}
            </div>
          </div>

          {/* Active Filtering Notification Bar */}
          {loading && summary && (
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-indigo-700 bg-indigo-50/70 px-3 py-1.5 rounded-xl border border-indigo-100/80">
              <div className="flex items-center gap-2 font-medium">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                <span>Applying filters and recalculating Order & Revenue analytics...</span>
              </div>
              <span className="text-[11px] text-indigo-500 font-semibold">Live update in progress</span>
            </div>
          )}
        </Card>

        {/* Loading Skeleton on Initial Load */}
        {loading && !summary && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 p-2 bg-indigo-50 rounded-xl">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
              <span>Loading Analytic Dashboard...</span>
            </div>
            <LoadingSkeleton rows={5} />
          </div>
        )}

        {/* Error State */}
        {error && (
          <ErrorState
            message={error}
            onRetry={loadDashboardData}
          />
        )}

        {/* Zero Data Notification Banner */}
        {!loading && !error && summary && summary.total_orders === 0 && (
          <div className="bg-amber-50/90 border border-amber-200 text-amber-900 px-4 py-3 rounded-2xl text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
            <div className="flex items-center gap-2.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0 animate-pulse" />
              <span>
                No qualifying orders found for <strong>{DATE_PRESETS.find((p) => p.value === datePreset)?.label || datePreset}</strong>.
                Select <strong>All Time</strong>, <strong>Previous Month</strong>, or <strong>Last 30 Days</strong> to analyze historical data.
              </span>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleResetFilters}
              className="text-xs shrink-0 font-semibold bg-white border border-amber-300 hover:bg-amber-100"
            >
              Reset to All Time
            </Button>
          </div>
        )}

        {/* Main Dashboard Content */}
        {summary && (
          <div className={`space-y-8 transition-opacity duration-200 ${loading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
            {/* 2. Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Total Orders */}
              <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Total Orders
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
                    <ShoppingBag className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {formatNumber(summary.total_orders)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">Qualifying orders</p>
                </div>
              </Card>

              {/* Total Revenue */}
              <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Total Revenue
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
                    <IndianRupee className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl lg:text-3xl font-extrabold text-emerald-600 tracking-tight">
                    {formatCurrency(summary.total_revenue)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">Calculated via RevenueService</p>
                </div>
              </Card>

              {/* Total Customers */}
              <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Total Customers
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {formatNumber(summary.total_customers)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">Unique associated customers</p>
                </div>
              </Card>

              {/* Average Order Value */}
              <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Average Order Value
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl lg:text-3xl font-extrabold text-violet-700 tracking-tight">
                    {formatCurrency(summary.average_order_value)}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">Total Revenue / Total Orders</p>
                </div>
              </Card>
            </div>

            {/* 3. District-wise Analytics */}
            {(() => {
              const orderDistricts = districts
                .filter((d) => Boolean(d.district && d.district.trim() && d.total_orders > 0))
                .sort((a, b) => b.total_orders - a.total_orders);

              const revenueDistricts = districts
                .filter((d) => Boolean(d.district && d.district.trim() && d.total_revenue > 0))
                .sort((a, b) => b.total_revenue - a.total_revenue);

              const totalActiveDistrictsCount = new Set([
                ...orderDistricts.map((d) => d.district),
                ...revenueDistricts.map((d) => d.district),
              ]).size;

              return (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4 text-indigo-600" />
                      <h3 className="text-base font-bold text-slate-900">District-wise Analytics</h3>
                    </div>
                    {totalActiveDistrictsCount > 0 && (
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
                        {totalActiveDistrictsCount} active {totalActiveDistrictsCount === 1 ? 'district' : 'districts'}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* District Order Count */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          District-wise Order Count
                        </h4>
                        {orderDistricts.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {orderDistricts.length} {orderDistricts.length === 1 ? 'district' : 'districts'}
                          </span>
                        )}
                      </div>
                      {orderDistricts.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <Building className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active district order data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, orderDistricts.length * 68)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={orderDistricts}
                                barCategoryGap="20%"
                                margin={{ top: 12, right: 16, left: -15, bottom: 65 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="district"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={65}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_orders"
                                  name="Orders"
                                  fill={BLUE_COLOR}
                                  maxBarSize={32}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>

                    {/* District Revenue */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          District-wise Order Revenue
                        </h4>
                        {revenueDistricts.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {revenueDistricts.length} {revenueDistricts.length === 1 ? 'district' : 'districts'}
                          </span>
                        )}
                      </div>
                      {revenueDistricts.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <Building className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active district revenue data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, revenueDistricts.length * 68)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={revenueDistricts}
                                barCategoryGap="20%"
                                margin={{ top: 12, right: 16, left: 10, bottom: 65 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="district"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={65}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_revenue"
                                  name="Revenue"
                                  fill={EMERALD_COLOR}
                                  maxBarSize={32}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>
                  </div>
                </div>
              );
            })()}

            {/* 4. Pincode-wise Analytics */}
            {(() => {
              const orderPincodes = pincodes
                .filter((p) => Boolean(p.pincode && p.pincode.trim() && p.total_orders > 0))
                .sort((a, b) => b.total_orders - a.total_orders);

              const revenuePincodes = pincodes
                .filter((p) => Boolean(p.pincode && p.pincode.trim() && p.total_revenue > 0))
                .sort((a, b) => b.total_revenue - a.total_revenue);

              const totalActivePincodesCount = new Set([
                ...orderPincodes.map((p) => p.pincode),
                ...revenuePincodes.map((p) => p.pincode),
              ]).size;

              return (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      <h3 className="text-base font-bold text-slate-900">Pincode-wise Analytics</h3>
                    </div>
                    {totalActivePincodesCount > 0 && (
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
                        {totalActivePincodesCount} active PIN {totalActivePincodesCount === 1 ? 'code' : 'codes'}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Pincode Order Count */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          Pincode-wise Order Count
                        </h4>
                        {orderPincodes.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {orderPincodes.length} PIN {orderPincodes.length === 1 ? 'code' : 'codes'}
                          </span>
                        )}
                      </div>
                      {orderPincodes.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <MapPin className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active PIN code order data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, orderPincodes.length * 62)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={orderPincodes}
                                barCategoryGap="18%"
                                margin={{ top: 12, right: 16, left: -15, bottom: 60 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="pincode"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={60}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_orders"
                                  name="Orders"
                                  fill={BLUE_COLOR}
                                  maxBarSize={38}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>

                    {/* Pincode Revenue */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          Pincode-wise Order Revenue
                        </h4>
                        {revenuePincodes.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {revenuePincodes.length} PIN {revenuePincodes.length === 1 ? 'code' : 'codes'}
                          </span>
                        )}
                      </div>
                      {revenuePincodes.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <MapPin className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active PIN code revenue data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, revenuePincodes.length * 62)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={revenuePincodes}
                                barCategoryGap="18%"
                                margin={{ top: 12, right: 16, left: 10, bottom: 60 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="pincode"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={60}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_revenue"
                                  name="Revenue"
                                  fill={EMERALD_COLOR}
                                  maxBarSize={38}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>
                  </div>
                </div>
              );
            })()}

            {/* 5. Post Office-wise Analytics */}
            {(() => {
              const orderPostOffices = postOffices
                .filter((po) => Boolean(po.post_office && po.post_office.trim() && po.total_orders > 0))
                .sort((a, b) => b.total_orders - a.total_orders);

              const revenuePostOffices = postOffices
                .filter((po) => Boolean(po.post_office && po.post_office.trim() && po.total_revenue > 0))
                .sort((a, b) => b.total_revenue - a.total_revenue);

              const totalActivePostOfficesCount = new Set([
                ...orderPostOffices.map((po) => po.post_office),
                ...revenuePostOffices.map((po) => po.post_office),
              ]).size;

              return (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-emerald-600" />
                      <h3 className="text-base font-bold text-slate-900">Post Office-wise Analytics</h3>
                    </div>
                    {totalActivePostOfficesCount > 0 && (
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
                        {totalActivePostOfficesCount} active post {totalActivePostOfficesCount === 1 ? 'office' : 'offices'}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Post Office Order Count */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          Post Office-wise Order Count
                        </h4>
                        {orderPostOffices.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {orderPostOffices.length} post {orderPostOffices.length === 1 ? 'office' : 'offices'}
                          </span>
                        )}
                      </div>
                      {orderPostOffices.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <Mail className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active post office order data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, orderPostOffices.length * 65)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={orderPostOffices}
                                barCategoryGap="18%"
                                margin={{ top: 12, right: 16, left: -15, bottom: 65 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="post_office"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={65}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_orders"
                                  name="Orders"
                                  fill={BLUE_COLOR}
                                  maxBarSize={38}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>

                    {/* Post Office Revenue */}
                    <Card className="p-5 border border-slate-200/90 shadow-2xs rounded-2xl bg-white space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                          Post Office-wise Order Revenue
                        </h4>
                        {revenuePostOffices.length > 0 && (
                          <span className="text-[11px] font-medium text-slate-400">
                            {revenuePostOffices.length} post {revenuePostOffices.length === 1 ? 'office' : 'offices'}
                          </span>
                        )}
                      </div>
                      {revenuePostOffices.length === 0 ? (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 text-xs">
                          <Mail className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                          No active post office revenue data for this selection
                        </div>
                      ) : (
                        <div className="w-full overflow-x-auto pb-2 pt-2 scrollbar-thin">
                          <div style={{ minWidth: `${Math.max(480, revenuePostOffices.length * 65)}px`, height: 320 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={revenuePostOffices}
                                barCategoryGap="18%"
                                margin={{ top: 12, right: 16, left: 10, bottom: 65 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                  dataKey="post_office"
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  interval={0}
                                  angle={-35}
                                  textAnchor="end"
                                  height={65}
                                  dx={-4}
                                  dy={4}
                                />
                                <YAxis
                                  tick={{ fontSize: 11, fill: '#64748b' }}
                                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar
                                  dataKey="total_revenue"
                                  name="Revenue"
                                  fill={EMERALD_COLOR}
                                  maxBarSize={38}
                                  radius={[4, 4, 0, 0]}
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </Card>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticDashboard;
