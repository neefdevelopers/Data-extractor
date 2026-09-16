import React, { useEffect, useState } from 'react';
import {
  ShoppingBag,
  Search,
  Download,
  Eye,
  Calendar,
  IndianRupee,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Button } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { CustomerProfileModal } from '../components/customer/CustomerProfileModal';
import { orderApi } from '../services/orderApi';
import { reportApi } from '../services/reportApi';
import { Order } from '../types';
import { formatCurrency, formatDateTime, getStatusBadgeColor } from '../utils/formatters';
import { useDebounce } from '../hooks/useDebounce';

export const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [paymentMode, setPaymentMode] = useState('');
  const [orderStatus, setOrderStatus] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Expanded order rows for items
  const [expandedOrders, setExpandedOrders] = useState<Record<number, boolean>>({});

  // Customer modal
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);

  const fetchOrders = async (currentPage = page, currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await orderApi.list({
        page: currentPage,
        page_size: pageSize,
        search: currentSearch || undefined,
        payment_mode: paymentMode || undefined,
        order_status: orderStatus || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      setOrders(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders(page, debouncedSearch);
  }, [page, debouncedSearch, paymentMode, orderStatus, startDate, endDate]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const toggleExpand = (orderId: number) => {
    setExpandedOrders((prev) => ({ ...prev, [orderId]: !prev[orderId] }));
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchOrders(1, search);
  };

  return (
    <div>
      <Header
        title="Orders Management"
        subtitle="Track fulfilled, COD, prepaid, and returned orders with multi-item breakdowns"
        action={
          <Button
            size="sm"
            variant="outline"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => reportApi.downloadOrders('xlsx', paymentMode, orderStatus, startDate, endDate)}
          >
            Export Orders
          </Button>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Filters */}
        <div className="glass-card p-4 rounded-xl space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[220px]">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search by Order ID, customer, PIN..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
            </div>

            <select
              value={paymentMode}
              onChange={(e) => {
                setPaymentMode(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
            >
              <option value="">All Payment Modes</option>
              <option value="COD">Cash on Delivery (COD)</option>
              <option value="PREPAID">Prepaid</option>
            </select>

            <select
              value={orderStatus}
              onChange={(e) => {
                setOrderStatus(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
            >
              <option value="">All Statuses</option>
              <option value="DELIVERED">DELIVERED</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="CANCELLED">CANCELLED</option>
              <option value="RETURNED">RETURNED</option>
              <option value="PENDING">PENDING</option>
            </select>

            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
              <span>Date:</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setPage(1);
                }}
                className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
              <span>to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setPage(1);
                }}
                className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
            </div>

            <Button size="sm" type="submit">
              Apply
            </Button>
          </form>
        </div>

        {/* Orders Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-indigo-600" />
              Order Transactions ({total.toLocaleString('en-IN')})
            </h3>
            <span className="text-xs text-slate-500">Expand rows to view individual items</span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={8} />
            </div>
          ) : orders.length === 0 ? (
            <EmptyState
              title="No orders found"
              description="Upload an Excel file with order data to see order transactions."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3.5 pl-6 w-8"></th>
                    <th className="p-3.5">Order ID</th>
                    <th className="p-3.5">Customer</th>
                    <th className="p-3.5">Order Date</th>
                    <th className="p-3.5">Payment</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 text-right">Total Amount</th>
                    <th className="p-3.5 text-right">Revenue Eligible</th>
                    <th className="p-3.5 pr-6">Sales Rep</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {orders.map((o) => {
                    const isExpanded = Boolean(expandedOrders[o.id]);
                    return (
                      <React.Fragment key={o.id}>
                        <tr
                          onClick={() => toggleExpand(o.id)}
                          className="hover:bg-slate-50 cursor-pointer transition-colors"
                        >
                          <td className="p-3.5 pl-6 text-slate-400">
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-indigo-600" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-slate-400" />
                            )}
                          </td>

                          <td className="p-3.5 font-mono font-bold text-indigo-700">
                            #{o.order_number}
                          </td>

                          <td
                            className="p-3.5 text-slate-800 hover:text-indigo-600 cursor-pointer"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedCustomerId(o.customer_id);
                            }}
                          >
                            <div className="font-semibold text-slate-900">{o.customer_name || 'Customer'}</div>
                            <div className="text-[11px] text-slate-500">
                              {o.customer_district} {o.customer_pincode ? `• ${o.customer_pincode}` : ''}
                            </div>
                          </td>

                          <td className="p-3.5 text-slate-600">
                            {formatDateTime(o.order_date)}
                          </td>

                          <td className="p-3.5">
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200">
                              {o.payment_mode}
                            </span>
                          </td>

                          <td className="p-3.5">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getStatusBadgeColor(
                                o.order_status
                              )}`}
                            >
                              {o.order_status}
                            </span>
                          </td>

                          <td className="p-3.5 text-right font-bold text-slate-900 text-sm">
                            {formatCurrency(o.total_amount)}
                          </td>

                          <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">
                            {formatCurrency(o.revenue_amount)}
                          </td>

                          <td className="p-3.5 pr-6 text-slate-600">
                            {o.employee_name || 'Unassigned'}
                          </td>
                        </tr>

                        {/* Expanded Items Sub-row */}
                        {isExpanded && (
                          <tr className="bg-slate-50/80">
                            <td colSpan={9} className="p-4 pl-14">
                              <div className="space-y-2">
                                <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                                  Order Items ({o.items?.length || 0})
                                </div>
                                {o.items && o.items.length > 0 ? (
                                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                    {o.items.map((it) => (
                                      <div
                                        key={it.id}
                                        className="bg-white p-2.5 rounded-lg border border-slate-200 flex items-center justify-between text-xs shadow-2xs"
                                      >
                                        <div>
                                          <span className="font-semibold text-slate-800 block truncate max-w-[200px]">
                                            {it.product_name}
                                          </span>
                                          <span className="text-slate-500 text-[11px]">
                                            Qty: {it.quantity} × {formatCurrency(it.unit_price)}
                                          </span>
                                        </div>
                                        <span className="font-bold text-slate-900">
                                          {formatCurrency(it.item_total)}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="text-xs text-slate-500">No individual line items recorded.</p>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
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

      <CustomerProfileModal
        customerId={selectedCustomerId}
        isOpen={Boolean(selectedCustomerId)}
        onClose={() => setSelectedCustomerId(null)}
      />
    </div>
  );
};
