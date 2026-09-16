import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  ShoppingBag,
  Users,
  Package,
  CreditCard,
  Truck,
  IndianRupee,
  Calendar,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { GlobalFilters } from '../components/layout/GlobalFilters';
import { Card } from '../components/common/Card';
import { RevenueTrendChart } from '../components/charts/RevenueTrendChart';
import { PaymentModeChart } from '../components/charts/PaymentModeChart';
import { GeoDistributionChart } from '../components/charts/GeoDistributionChart';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorState } from '../components/common/ErrorState';
import { analyticsApi } from '../services/analyticsApi';
import { BusinessDashboardKPIs, DistrictAnalyticsItem, GlobalFilterState } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useNavigate, useSearchParams } from 'react-router-dom';

export const BusinessDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialProductId = searchParams.get('productId') ? Number(searchParams.get('productId')) : undefined;

  const [filters, setFilters] = useState<GlobalFilterState>({
    preset: 'all',
    productId: initialProductId,
  });
  const [kpis, setKpis] = useState<BusinessDashboardKPIs | null>(null);
  const [districts, setDistricts] = useState<DistrictAnalyticsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiData, districtData] = await Promise.all([
        analyticsApi.getDashboardKPIs(filters),
        analyticsApi.getDistricts(),
      ]);
      setKpis(kpiData);
      setDistricts(districtData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  return (
    <div>
      <Header
        title="Executive Business Analytics"
        subtitle="Real-time revenue performance, order volume, and customer lifetime KPIs"
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Global Filters Bar */}
        <GlobalFilters filters={filters} onFilterChange={setFilters} />

        {/* Quick Payment Mode Filter Pills */}
        <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Quick Payment Mode Filter:</span>
            <div className="flex items-center gap-1.5">
              {[
                { label: 'All Payment Modes', value: undefined },
                { label: 'COD Only', value: 'COD' },
                { label: 'Prepaid Only', value: 'PREPAID' },
              ].map((m) => (
                <button
                  key={m.label}
                  onClick={() => setFilters({ ...filters, paymentMode: m.value })}
                  className={`px-3 py-1 rounded-lg transition-all font-medium ${
                    filters.paymentMode === m.value
                      ? 'bg-indigo-600 text-white font-semibold shadow-2xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {filters.paymentMode && (
            <span className="text-xs text-indigo-600 font-semibold bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-200">
              Filtered: {filters.paymentMode}
            </span>
          )}
        </div>

        {error ? (
          <ErrorState message={error} onRetry={loadData} />
        ) : loading && !kpis ? (
          <LoadingSkeleton rows={6} />
        ) : kpis ? (
          <>
            {/* Top KPI Cards Grid (5-column executive metric row) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Total Revenue */}
              <Card className="relative overflow-hidden border-indigo-200 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Total Revenue</span>
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <IndianRupee className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                    {formatCurrency(kpis.total_revenue)}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
                    Qualifying orders only
                  </p>
                </div>
              </Card>

              {/* Total Orders */}
              <Card className="relative overflow-hidden shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Total Orders</span>
                  <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                    <ShoppingBag className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                    {formatNumber(kpis.total_orders)}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Fulfilled transactions
                  </p>
                </div>
              </Card>

              {/* Average Order Value (AOV) */}
              <Card className="relative overflow-hidden shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Avg Order Value (AOV)</span>
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-emerald-600 tracking-tight">
                    {formatCurrency(kpis.average_order_value)}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Revenue per order
                  </p>
                </div>
              </Card>

              {/* COD Revenue */}
              <Card className="relative overflow-hidden shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">COD Revenue</span>
                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                    <Truck className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-amber-600 tracking-tight">
                    {formatCurrency(kpis.cod_revenue)}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    {kpis.cod_orders} orders ({kpis.total_orders > 0 ? ((kpis.cod_orders / kpis.total_orders) * 100).toFixed(1) : 0}%)
                  </p>
                </div>
              </Card>

              {/* Prepaid Revenue */}
              <Card className="relative overflow-hidden shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Prepaid Revenue</span>
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                    <CreditCard className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-blue-600 tracking-tight">
                    {formatCurrency(kpis.prepaid_revenue)}
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1">
                    {kpis.prepaid_orders} orders ({kpis.total_orders > 0 ? ((kpis.prepaid_orders / kpis.total_orders) * 100).toFixed(1) : 0}%)
                  </p>
                </div>
              </Card>
            </div>

            {/* Middle Section: Date-wise Revenue Trend & COD vs Prepaid Split */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Date-wise Trend (2 columns) */}
              <Card
                className="lg:col-span-2"
                title="Date-wise Revenue & Order Trend"
                subtitle="Historical trajectory of daily revenue (₹), order counts, and daily AOV"
              >
                <RevenueTrendChart data={kpis.revenue_trend} />
              </Card>

              {/* Payment Mode Donut (1 column) */}
              <Card
                title="COD vs Prepaid Comparison"
                subtitle="Payment mode distribution and AOV comparison"
              >
                <PaymentModeChart data={kpis.payment_breakdown} metricType="revenue" />
              </Card>
            </div>

            {/* COD vs Prepaid Detailed Comparative Matrix Table */}
            <div className="glass-card rounded-xl overflow-hidden shadow-xs">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-indigo-600" />
                  COD vs Prepaid Performance Matrix
                </h3>
                <span className="text-xs text-slate-500">Comparative revenue, order share, and average basket sizes</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="p-3.5 pl-6">Payment Mode</th>
                      <th className="p-3.5 text-right">Total Revenue</th>
                      <th className="p-3.5 text-center">Revenue Share %</th>
                      <th className="p-3.5 text-center">Total Orders</th>
                      <th className="p-3.5 text-center">Order Share %</th>
                      <th className="p-3.5 text-right pr-6">Average Order Value (AOV)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    <tr className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-semibold text-amber-700 flex items-center gap-2">
                        <Truck className="w-3.5 h-3.5 text-amber-600" /> Cash on Delivery (COD)
                      </td>
                      <td className="p-3.5 text-right font-bold text-amber-600">
                        {formatCurrency(kpis.cod_revenue)}
                      </td>
                      <td className="p-3.5 text-center font-medium text-slate-700">
                        {kpis.total_revenue > 0 ? ((kpis.cod_revenue / kpis.total_revenue) * 100).toFixed(1) : 0}%
                      </td>
                      <td className="p-3.5 text-center font-bold text-slate-800">
                        {formatNumber(kpis.cod_orders)}
                      </td>
                      <td className="p-3.5 text-center font-medium text-slate-700">
                        {kpis.total_orders > 0 ? ((kpis.cod_orders / kpis.total_orders) * 100).toFixed(1) : 0}%
                      </td>
                      <td className="p-3.5 text-right pr-6 font-bold text-slate-800">
                        {formatCurrency(kpis.cod_aov || (kpis.cod_orders > 0 ? kpis.cod_revenue / kpis.cod_orders : 0))}
                      </td>
                    </tr>

                    <tr className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-semibold text-blue-700 flex items-center gap-2">
                        <CreditCard className="w-3.5 h-3.5 text-blue-600" /> Prepaid (Online / UPI)
                      </td>
                      <td className="p-3.5 text-right font-bold text-blue-600">
                        {formatCurrency(kpis.prepaid_revenue)}
                      </td>
                      <td className="p-3.5 text-center font-medium text-slate-700">
                        {kpis.total_revenue > 0 ? ((kpis.prepaid_revenue / kpis.total_revenue) * 100).toFixed(1) : 0}%
                      </td>
                      <td className="p-3.5 text-center font-bold text-slate-800">
                        {formatNumber(kpis.prepaid_orders)}
                      </td>
                      <td className="p-3.5 text-center font-medium text-slate-700">
                        {kpis.total_orders > 0 ? ((kpis.prepaid_orders / kpis.total_orders) * 100).toFixed(1) : 0}%
                      </td>
                      <td className="p-3.5 text-right pr-6 font-bold text-slate-800">
                        {formatCurrency(kpis.prepaid_aov || (kpis.prepaid_orders > 0 ? kpis.prepaid_revenue / kpis.prepaid_orders : 0))}
                      </td>
                    </tr>

                    <tr className="bg-slate-50/90 font-semibold text-slate-900 border-t border-slate-200">
                      <td className="p-3.5 pl-6">Combined Total</td>
                      <td className="p-3.5 text-right text-indigo-600 font-extrabold text-sm">
                        {formatCurrency(kpis.total_revenue)}
                      </td>
                      <td className="p-3.5 text-center">100.0%</td>
                      <td className="p-3.5 text-center font-extrabold">
                        {formatNumber(kpis.total_orders)}
                      </td>
                      <td className="p-3.5 text-center">100.0%</td>
                      <td className="p-3.5 text-right pr-6 text-emerald-600 font-extrabold">
                        {formatCurrency(kpis.average_order_value)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Bottom Section: Top Districts and Quick Navigation */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Geographic Revenue Bar */}
              <Card
                className="lg:col-span-2"
                title="Top Performing Geographic Districts"
                subtitle="Highest revenue districts in India with active customer base"
                action={
                  <button
                    onClick={() => navigate('/geography')}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold flex items-center gap-1"
                  >
                    View All <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                }
              >
                <GeoDistributionChart districts={districts} limit={6} />
              </Card>

              {/* Quick Summary Card */}
              <Card title="Platform Directory Summary" subtitle="Audited database records">
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-2.5">
                      <Users className="w-4 h-4 text-indigo-600" />
                      <span className="text-xs text-slate-700 font-medium">Customer Records</span>
                    </div>
                    <span className="text-sm font-bold text-slate-900">{kpis.total_customers.toLocaleString('en-IN')}</span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-2.5">
                      <Package className="w-4 h-4 text-sky-600" />
                      <span className="text-xs text-slate-700 font-medium">Product Catalog SKUs</span>
                    </div>
                    <span className="text-sm font-bold text-slate-900">{kpis.total_products.toLocaleString('en-IN')}</span>
                  </div>

                  <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-xl space-y-1">
                    <span className="text-xs font-bold text-indigo-900 block">Centralized Revenue Rules</span>
                    <p className="text-[11px] text-indigo-700/80 leading-relaxed">
                      Delivered/Completed orders qualify for revenue. Cancelled orders are excluded per RevenueService settings.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
