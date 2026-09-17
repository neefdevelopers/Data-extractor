import React, { useEffect, useState } from 'react';
import {
  User,
  Phone,
  MapPin,
  Calendar,
  ShoppingBag,
  TrendingUp,
  Package,
  Clock,
  ShieldCheck,
  Tag,
  CreditCard,
  Layers,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { CopyCustomerButton } from './CopyCustomerButton';
import { CustomerDetail, Order } from '../../types';
import { customerApi } from '../../services/customerApi';
import { formatCurrency, formatDate, formatDateTime, getRfmSegmentBadgeColor, getStatusBadgeColor } from '../../utils/formatters';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

interface CustomerProfileModalProps {
  customerId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectOrder?: (orderId: number) => void;
}

export const CustomerProfileModal: React.FC<CustomerProfileModalProps> = ({
  customerId,
  isOpen,
  onClose,
  onSelectOrder,
}) => {
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'orders' | 'rfm'>('overview');

  useEffect(() => {
    if (customerId && isOpen) {
      setLoading(true);
      Promise.all([
        customerApi.getById(customerId),
        customerApi.getOrders(customerId, 1, 100),
      ])
        .then(([custData, ordersData]) => {
          setCustomer(custData);
          setOrders(ordersData.items);
        })
        .catch((err) => console.error('Failed to load customer profile:', err))
        .finally(() => setLoading(false));
    } else {
      setCustomer(null);
      setOrders([]);
    }
  }, [customerId, isOpen]);

  if (!isOpen) return null;

  const purchasedProducts = customer?.purchased_products || [];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="4xl"
      title={
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-lg border border-indigo-200 shadow-2xs">
            {customer?.customer_name ? customer.customer_name[0].toUpperCase() : 'C'}
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="font-bold text-slate-900 text-lg">{customer?.customer_name || 'Customer Profile'}</span>
              {customer?.rfm_segment && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getRfmSegmentBadgeColor(customer.rfm_segment)}`}>
                  {customer.rfm_segment}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Customer ID #{customer?.id} {customer?.normalized_contact ? `• 📞 ${customer.normalized_contact}` : ''}
            </p>
          </div>
        </div>
      }
      actionFooter={
        customer && (
          <div className="flex items-center justify-between w-full">
            <CopyCustomerButton customer={customer} size="sm" />
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold bg-white text-slate-700 hover:bg-slate-50 rounded-lg transition-colors border border-slate-300 shadow-2xs"
            >
              Close
            </button>
          </div>
        )
      }
    >
      {loading || !customer ? (
        <LoadingSkeleton rows={8} />
      ) : (
        <div className="space-y-6">
          {/* Tabs */}
          <div className="flex border-b border-slate-200 space-x-6 text-sm font-medium overflow-x-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-3 transition-colors border-b-2 whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === 'overview'
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <User className="w-4 h-4" />
              Profile & Contact
            </button>
            <button
              onClick={() => setActiveTab('products')}
              className={`pb-3 transition-colors border-b-2 whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === 'products'
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Package className="w-4 h-4" />
              Products Purchased
              <span className="bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs px-2 py-0.2 rounded-full font-bold">
                {purchasedProducts.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`pb-3 transition-colors border-b-2 whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === 'orders'
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <ShoppingBag className="w-4 h-4" />
              Order History
              <span className="bg-slate-100 text-slate-700 text-xs px-2 py-0.2 rounded-full font-bold border border-slate-200">
                {orders.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('rfm')}
              className={`pb-3 transition-colors border-b-2 whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === 'rfm'
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              RFM Analytics & Scores
            </button>
          </div>

          {/* Tab 1: Overview */}
          {activeTab === 'overview' && (
            <div className="space-y-5">
              {/* Top KPI row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1">Total Lifetime Spend</span>
                  <span className="text-xl font-bold text-emerald-600">{formatCurrency(customer.total_spend)}</span>
                </div>
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1">Total Orders</span>
                  <span className="text-xl font-bold text-indigo-600">{customer.total_orders}</span>
                </div>
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1">Average Order Value</span>
                  <span className="text-xl font-bold text-sky-600">{formatCurrency(customer.average_order_value)}</span>
                </div>
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block mb-1">RFM Score</span>
                  <span className="text-xl font-bold text-amber-600 font-mono">{customer.rfm_score || 'N/A'}</span>
                </div>
              </div>

              {/* Contact & Address info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200 space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-indigo-600" />
                    Customer Identity & Contact
                  </h4>
                  <div className="flex items-center gap-2 text-sm text-slate-800">
                    <span className="text-slate-500 w-24 shrink-0 text-xs">Full Name:</span>
                    <span className="font-semibold text-slate-900">{customer.customer_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-800">
                    <span className="text-slate-500 w-24 shrink-0 text-xs">Phone:</span>
                    <span className="font-mono text-indigo-700 font-medium">
                      {customer.contact_number || customer.normalized_contact || 'No phone recorded'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <span className="text-slate-500 w-24 shrink-0 text-xs">First Order:</span>
                    <span className="text-slate-800">{formatDate(customer.first_order_date)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <span className="text-slate-500 w-24 shrink-0 text-xs">Last Order:</span>
                    <span className="text-slate-800">{formatDate(customer.last_order_date)}</span>
                  </div>
                </div>

                <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200 space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-rose-500" />
                    Postal & Delivery Address
                  </h4>
                  <div className="flex items-start gap-2 text-sm text-slate-800">
                    <span className="text-slate-500 w-20 shrink-0 text-xs mt-0.5">Address:</span>
                    <span className="font-medium text-slate-900">{customer.full_address || 'No full street address recorded'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2.5 pt-2.5 border-t border-slate-200 text-xs">
                    <div>
                      <span className="text-slate-500 block mb-0.5">PIN Code:</span>
                      <span className="font-bold font-mono text-indigo-700 text-sm">{customer.pincode || '-'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">Post Office:</span>
                      <span className="font-medium text-slate-800">{customer.post_office || '-'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">District:</span>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-slate-800">{customer.district || '-'}</span>
                        {customer.district_resolution_source === 'PINCODE' && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600" />
                            Resolved from Pincode
                          </span>
                        )}
                      </div>
                      {customer.district_mismatch && customer.source_district && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200 mt-1" title={`Uploaded district was '${customer.source_district}'`}>
                          <AlertTriangle className="w-2.5 h-2.5 text-amber-600 shrink-0" />
                          Uploaded as {customer.source_district}
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-0.5">State:</span>
                      <span className="font-medium text-slate-800">{customer.state || '-'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Products Purchased */}
          {activeTab === 'products' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Summary of all products ordered by this customer</span>
                <span>{purchasedProducts.length} unique products</span>
              </div>

              {purchasedProducts.length === 0 ? (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                  <Package className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No product item records found for this customer.</p>
                </div>
              ) : (
                <div className="rounded-xl border border-slate-200 overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="p-3 pl-4">Product Name</th>
                        <th className="p-3">Category</th>
                        <th className="p-3 text-center">Units Purchased</th>
                        <th className="p-3 text-right">Total Spent</th>
                        <th className="p-3 text-right pr-4">Last Ordered</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {purchasedProducts.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="p-3 pl-4">
                            <div className="font-semibold text-slate-900">{p.product_name}</div>
                            {p.sku && <div className="text-[10px] text-slate-400 font-mono">SKU: {p.sku}</div>}
                          </td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] border border-slate-200">
                              {p.category || 'General'}
                            </span>
                          </td>
                          <td className="p-3 text-center">
                            <span className="font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                              {p.total_quantity}
                            </span>
                          </td>
                          <td className="p-3 text-right font-bold text-emerald-600">
                            {formatCurrency(p.total_spend)}
                          </td>
                          <td className="p-3 text-right pr-4 text-slate-500">
                            {p.last_purchased_date ? formatDate(p.last_purchased_date) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Orders */}
          {activeTab === 'orders' && (
            <div className="space-y-3">
              {orders.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-6">No orders found for this customer.</p>
              ) : (
                <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                  {orders.map((o) => (
                    <div
                      key={o.id}
                      onClick={() => onSelectOrder?.(o.id)}
                      className="bg-white hover:bg-slate-50 p-4 rounded-xl border border-slate-200 cursor-pointer transition-colors space-y-2.5 shadow-2xs"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold text-indigo-600">
                            #{o.order_number}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getStatusBadgeColor(o.order_status)}`}>
                            {o.order_status}
                          </span>
                          <span className="bg-slate-100 text-slate-700 border border-slate-200 text-xs px-2 py-0.5 rounded font-mono">
                            {o.payment_mode}
                          </span>
                        </div>
                        <span className="text-base font-bold text-emerald-600">
                          {formatCurrency(o.total_amount)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>📅 Order Date: {formatDateTime(o.order_date)}</span>
                        {o.employee_name && <span>Sales Rep: {o.employee_name}</span>}
                      </div>

                      {/* Items */}
                      {o.items && o.items.length > 0 && (
                        <div className="pt-2.5 border-t border-slate-100 text-xs space-y-1.5">
                          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                            Line Items ({o.items.length})
                          </span>
                          {o.items.map((it) => (
                            <div key={it.id} className="flex items-center justify-between text-slate-700 bg-slate-50 p-1.5 px-2.5 rounded border border-slate-200/60">
                              <span className="truncate max-w-[340px]">
                                <span className="font-bold text-indigo-600">{it.quantity}x</span> {it.product_name}
                              </span>
                              <span className="font-mono font-medium">{formatCurrency(it.item_total)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 4: RFM */}
          {activeTab === 'rfm' && (
            <div className="space-y-5">
              <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200">
                <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-600" />
                  RFM Quintile Breakdown (1 to 5 Scoring)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                  <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
                    <span className="text-xs text-slate-500 block mb-1">Recency (R)</span>
                    <span className="text-2xl font-bold text-indigo-600 block">{customer.rfm_details?.recency_days ?? '-'}</span>
                    <span className="text-xs text-slate-500">days since last purchase</span>
                    <div className="mt-2.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 py-1 rounded">
                      R Score: {customer.rfm_details?.r_score ?? customer.rfm_score?.[0] ?? '-'} / 5
                    </div>
                  </div>

                  <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
                    <span className="text-xs text-slate-500 block mb-1">Frequency (F)</span>
                    <span className="text-2xl font-bold text-sky-600 block">{customer.rfm_details?.frequency ?? customer.total_orders}</span>
                    <span className="text-xs text-slate-500">lifetime orders</span>
                    <div className="mt-2.5 text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-200 py-1 rounded">
                      F Score: {customer.rfm_details?.f_score ?? customer.rfm_score?.[1] ?? '-'} / 5
                    </div>
                  </div>

                  <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
                    <span className="text-xs text-slate-500 block mb-1">Monetary (M)</span>
                    <span className="text-2xl font-bold text-emerald-600 block">
                      {formatCurrency(customer.rfm_details?.monetary_value ?? customer.total_spend)}
                    </span>
                    <span className="text-xs text-slate-500">lifetime spend</span>
                    <div className="mt-2.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 py-1 rounded">
                      M Score: {customer.rfm_details?.m_score ?? customer.rfm_score?.[2] ?? '-'} / 5
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50/80 p-4 rounded-xl border border-slate-200 space-y-2">
                <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Behavioral Segment Classification
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed">
                  This customer is classified as <strong className="text-indigo-600">{customer.rfm_segment || 'New Customers'}</strong> with an overall composite RFM score of <strong className="text-amber-600 font-mono">{customer.rfm_score || '111'}</strong>.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
};
