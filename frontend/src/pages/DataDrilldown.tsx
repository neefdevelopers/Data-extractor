import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GitFork,
  MapPin,
  Package,
  Users,
  ShoppingBag,
  ChevronRight,
  ArrowLeft,
  Search,
  IndianRupee,
  Calendar,
  Layers,
  Eye,
  ArrowUpRight,
  RotateCcw,
  CheckCircle2,
  Clock,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { Pagination } from '../components/common/Pagination';
import { CustomerProfileModal } from '../components/customer/CustomerProfileModal';
import { analyticsApi } from '../services/analyticsApi';
import { customerApi } from '../services/customerApi';
import { productApi } from '../services/productApi';
import { orderApi } from '../services/orderApi';
import { useDebounce } from '../hooks/useDebounce';
import {
  DistrictAnalyticsItem,
  PincodeAnalyticsItem,
  Customer,
  Product,
  Order
} from '../types';
import { formatCurrency, formatNumber, formatDateTime, getStatusBadgeColor, getRfmSegmentBadgeColor } from '../utils/formatters';

type DrilldownDimension = 'geographic' | 'product' | 'customer';

export const DataDrilldown: React.FC = () => {
  const navigate = useNavigate();
  const [dimension, setDimension] = useState<DrilldownDimension>('geographic');

  // Customer profile modal state
  const [modalCustomerId, setModalCustomerId] = useState<number | null>(null);

  // Common Search & Debounce
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // -------------------------------------------------------------
  // Flow 1: Geographic (District -> Pincode -> Customers -> Orders)
  // -------------------------------------------------------------
  const [geoDistrict, setGeoDistrict] = useState<string | null>(null);
  const [geoPincode, setGeoPincode] = useState<string | null>(null);
  const [geoCustomer, setGeoCustomer] = useState<Customer | null>(null);
  const [geoDistrictsList, setGeoDistrictsList] = useState<DistrictAnalyticsItem[]>([]);
  const [geoPincodesList, setGeoPincodesList] = useState<PincodeAnalyticsItem[]>([]);
  const [geoCustomersList, setGeoCustomersList] = useState<Customer[]>([]);
  const [geoOrdersList, setGeoOrdersList] = useState<Order[]>([]);

  // -------------------------------------------------------------
  // Flow 2: Product (Product -> Orders -> Customers)
  // -------------------------------------------------------------
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [productOrdersList, setProductOrdersList] = useState<Order[]>([]);
  const [productsList, setProductsList] = useState<Product[]>([]);

  // -------------------------------------------------------------
  // Flow 3: Customer (Customer -> Order History -> Order Details)
  // -------------------------------------------------------------
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerOrdersList, setCustomerOrdersList] = useState<Order[]>([]);
  const [customersList, setCustomersList] = useState<Customer[]>([]);

  // Reset drilldown when dimension changes
  const handleDimensionChange = (dim: DrilldownDimension) => {
    setDimension(dim);
    setSearch('');
    setPage(1);

    // Reset all drilldown selections
    setGeoDistrict(null);
    setGeoPincode(null);
    setGeoCustomer(null);
    setSelectedProduct(null);
    setSelectedCustomer(null);
  };

  // Reset to page 1 on search change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  // Load active data based on dimension and drill-down depth
  const loadData = async () => {
    setLoading(true);
    try {
      if (dimension === 'geographic') {
        if (geoCustomer) {
          // Level 4: Orders for Geo Customer
          const data = await customerApi.getOrders(geoCustomer.id, page, pageSize);
          setGeoOrdersList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        } else if (geoPincode) {
          // Level 3: Customers for Geo PIN
          const data = await customerApi.list({
            pincode: geoPincode,
            search: debouncedSearch || undefined,
            page,
            page_size: pageSize
          });
          setGeoCustomersList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        } else if (geoDistrict) {
          // Level 2: PIN codes for Geo District
          const data = await analyticsApi.getPincodes(geoDistrict, debouncedSearch || undefined);
          setGeoPincodesList(data);
          setTotalItems(data.length);
          setTotalPages(1);
        } else {
          // Level 1: All Districts
          const data = await analyticsApi.getDistricts(debouncedSearch || undefined);
          setGeoDistrictsList(data);
          setTotalItems(data.length);
          setTotalPages(1);
        }
      } else if (dimension === 'product') {
        if (selectedProduct) {
          // Level 2: Orders containing this product
          const data = await orderApi.list({
            product_id: selectedProduct.id,
            search: debouncedSearch || undefined,
            page,
            page_size: pageSize
          });
          setProductOrdersList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        } else {
          // Level 1: Products
          const data = await productApi.list({
            search: debouncedSearch || undefined,
            page,
            page_size: pageSize
          });
          setProductsList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        }
      } else if (dimension === 'customer') {
        if (selectedCustomer) {
          // Level 2: Customer orders
          const data = await customerApi.getOrders(selectedCustomer.id, page, pageSize);
          setCustomerOrdersList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        } else {
          // Level 1: Customers
          const data = await customerApi.list({
            search: debouncedSearch || undefined,
            page,
            page_size: pageSize
          });
          setCustomersList(data.items);
          setTotalItems(data.total);
          setTotalPages(data.total_pages);
        }
      }
    } catch (err) {
      console.error('Failed to load drill-down data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [
    dimension,
    page,
    debouncedSearch,
    geoDistrict,
    geoPincode,
    geoCustomer,
    selectedProduct,
    selectedCustomer
  ]);

  return (
    <div>
      <Header
        title="Multi-Dimensional Data Drill-Down"
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Dimension Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            onClick={() => handleDimensionChange('geographic')}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-28 ${
              dimension === 'geographic'
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-500/20'
                : 'bg-white text-slate-800 border-slate-200 hover:border-indigo-300 shadow-2xs hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <MapPin className={`w-5 h-5 ${dimension === 'geographic' ? 'text-white' : 'text-indigo-600'}`} />
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                dimension === 'geographic' ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-700'
              }`}>
                4 Levels
              </span>
            </div>
            <div>
              <div className="font-bold text-sm">Geographic Drill-down</div>
              <div className={`text-[11px] truncate ${dimension === 'geographic' ? 'text-indigo-100' : 'text-slate-500'}`}>
                District → PIN → Customers → Orders
              </div>
            </div>
          </button>

          <button
            onClick={() => handleDimensionChange('product')}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-28 ${
              dimension === 'product'
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-500/20'
                : 'bg-white text-slate-800 border-slate-200 hover:border-indigo-300 shadow-2xs hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <Package className={`w-5 h-5 ${dimension === 'product' ? 'text-white' : 'text-indigo-600'}`} />
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                dimension === 'product' ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-700'
              }`}>
                3 Levels
              </span>
            </div>
            <div>
              <div className="font-bold text-sm">Product Drill-down</div>
              <div className={`text-[11px] truncate ${dimension === 'product' ? 'text-indigo-100' : 'text-slate-500'}`}>
                Product → Orders → Customers
              </div>
            </div>
          </button>

          <button
            onClick={() => handleDimensionChange('customer')}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-28 ${
              dimension === 'customer'
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-500/20'
                : 'bg-white text-slate-800 border-slate-200 hover:border-indigo-300 shadow-2xs hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <Users className={`w-5 h-5 ${dimension === 'customer' ? 'text-white' : 'text-indigo-600'}`} />
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                dimension === 'customer' ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-700'
              }`}>
                3 Levels
              </span>
            </div>
            <div>
              <div className="font-bold text-sm">Customer Drill-down</div>
              <div className={`text-[11px] truncate ${dimension === 'customer' ? 'text-indigo-100' : 'text-slate-500'}`}>
                Customer → Order History → Details
              </div>
            </div>
          </button>
        </div>

        {/* Dynamic Breadcrumbs & Current Depth Header */}
        <div className="glass-card p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold overflow-x-auto py-1">
            {/* Geographic Breadcrumbs */}
            {dimension === 'geographic' && (
              <>
                <button
                  onClick={() => {
                    setGeoDistrict(null);
                    setGeoPincode(null);
                    setGeoCustomer(null);
                  }}
                  className={`flex items-center gap-1.5 transition-colors ${
                    !geoDistrict ? 'text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md' : 'text-slate-600 hover:text-indigo-600'
                  }`}
                >
                  <MapPin className="w-3.5 h-3.5" /> All Districts
                </button>

                {geoDistrict && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <button
                      onClick={() => {
                        setGeoPincode(null);
                        setGeoCustomer(null);
                      }}
                      className={`transition-colors ${
                        !geoPincode ? 'text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md' : 'text-slate-600 hover:text-indigo-600'
                      }`}
                    >
                      District: {geoDistrict}
                    </button>
                  </>
                )}

                {geoPincode && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <button
                      onClick={() => setGeoCustomer(null)}
                      className={`font-mono transition-colors ${
                        !geoCustomer ? 'text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md' : 'text-slate-600 hover:text-indigo-600'
                      }`}
                    >
                      PIN: {geoPincode}
                    </button>
                  </>
                )}

                {geoCustomer && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md">
                      Customer: {geoCustomer.customer_name}
                    </span>
                  </>
                )}
              </>
            )}

            {/* Product Breadcrumbs */}
            {dimension === 'product' && (
              <>
                <button
                  onClick={() => setSelectedProduct(null)}
                  className={`flex items-center gap-1.5 transition-colors ${
                    !selectedProduct ? 'text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md' : 'text-slate-600 hover:text-indigo-600'
                  }`}
                >
                  <Package className="w-3.5 h-3.5" /> All Catalog Products
                </button>

                {selectedProduct && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md truncate max-w-[280px]">
                      Product: {selectedProduct.product_name}
                    </span>
                  </>
                )}
              </>
            )}

            {/* Customer Breadcrumbs */}
            {dimension === 'customer' && (
              <>
                <button
                  onClick={() => setSelectedCustomer(null)}
                  className={`flex items-center gap-1.5 transition-colors ${
                    !selectedCustomer ? 'text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md' : 'text-slate-600 hover:text-indigo-600'
                  }`}
                >
                  <Users className="w-3.5 h-3.5" /> All Registered Customers
                </button>

                {selectedCustomer && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-indigo-600 font-bold bg-indigo-50 px-2 py-1 rounded-md">
                      Customer Profile: {selectedCustomer.customer_name}
                    </span>
                  </>
                )}
              </>
            )}
          </div>

          {/* Quick Search */}
          <div className="relative min-w-[220px]">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search current level..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* VIEW 1: Geographic Drilldown                                   */}
        {/* ------------------------------------------------------------- */}
        {dimension === 'geographic' && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            {/* Level 4: Orders for Geo Customer */}
            {geoCustomer ? (
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setGeoCustomer(null)}
                      className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                      title="Back to Customers"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <ShoppingBag className="w-4 h-4 text-indigo-600" />
                        Orders Placed by <span className="text-indigo-600 font-bold">{geoCustomer.customer_name}</span> ({totalItems})
                      </h3>
                      <p className="text-[11px] text-slate-500">
                        {geoCustomer.district} • PIN {geoCustomer.pincode} • Phone: {geoCustomer.contact_number || 'N/A'}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="xs"
                    variant="outline"
                    icon={<Eye className="w-3.5 h-3.5" />}
                    onClick={() => setModalCustomerId(geoCustomer.id)}
                  >
                    Open Customer Profile
                  </Button>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={5} /></div>
                ) : geoOrdersList.length === 0 ? (
                  <EmptyState title="No orders found for this customer" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Order ID</th>
                          <th className="p-3.5">Order Date</th>
                          <th className="p-3.5">Payment</th>
                          <th className="p-3.5">Status</th>
                          <th className="p-3.5 text-right">Subtotal</th>
                          <th className="p-3.5 text-right">Total Amount</th>
                          <th className="p-3.5 text-right pr-6">Revenue Eligible</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {geoOrdersList.map((o) => (
                          <tr key={o.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-mono font-bold text-indigo-700">#{o.order_number}</td>
                            <td className="p-3.5 text-slate-600">{formatDateTime(o.order_date)}</td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200">
                                {o.payment_mode}
                              </span>
                            </td>
                            <td className="p-3.5">
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getStatusBadgeColor(o.order_status)}`}>
                                {o.order_status}
                              </span>
                            </td>
                            <td className="p-3.5 text-right text-slate-700">{formatCurrency(o.subtotal || o.total_amount)}</td>
                            <td className="p-3.5 text-right font-bold text-slate-900 text-sm">{formatCurrency(o.total_amount)}</td>
                            <td className="p-3.5 text-right font-bold text-emerald-600 pr-6 text-sm">{formatCurrency(o.revenue_amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : geoPincode ? (
              // Level 3: Customers for Geo PIN
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setGeoPincode(null)}
                      className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                      title="Back to PIN Codes"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <Users className="w-4 h-4 text-indigo-600" />
                        Customers in PIN <span className="text-indigo-600 font-mono font-bold">{geoPincode}</span> ({totalItems})
                      </h3>
                      <p className="text-[11px] text-slate-500">District: {geoDistrict} • Click any customer to view their orders</p>
                    </div>
                  </div>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : geoCustomersList.length === 0 ? (
                  <EmptyState title="No customers found in this PIN" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Customer Name</th>
                          <th className="p-3.5">Contact</th>
                          <th className="p-3.5">Post Office / Address</th>
                          <th className="p-3.5 text-center">Orders</th>
                          <th className="p-3.5 text-right">Total Spend</th>
                          <th className="p-3.5 text-center">RFM Segment</th>
                          <th className="p-3.5 text-right pr-6">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {geoCustomersList.map((c) => (
                          <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-semibold text-slate-900">{c.customer_name}</td>
                            <td className="p-3.5 font-mono text-slate-700">{c.contact_number || '-'}</td>
                            <td className="p-3.5 text-slate-600 max-w-[240px] truncate">{c.full_address || c.post_office || '-'}</td>
                            <td className="p-3.5 text-center font-bold text-slate-800">{c.total_orders}</td>
                            <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">{formatCurrency(c.total_spend)}</td>
                            <td className="p-3.5 text-center">
                              {c.rfm_segment ? (
                                <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getRfmSegmentBadgeColor(c.rfm_segment)}`}>
                                  {c.rfm_segment}
                                </span>
                              ) : '-'}
                            </td>
                            <td className="p-3.5 text-right pr-6">
                              <button
                                onClick={() => setGeoCustomer(c)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 shadow-2xs"
                              >
                                View Orders <ChevronRight className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : geoDistrict ? (
              // Level 2: PIN codes for Geo District
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setGeoDistrict(null)}
                      className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                      title="Back to Districts"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-indigo-600" />
                        Postal PIN Codes in <span className="text-indigo-600 font-bold">{geoDistrict}</span> ({geoPincodesList.length})
                      </h3>
                      <p className="text-[11px] text-slate-500">Click any PIN code to inspect residing customers</p>
                    </div>
                  </div>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : geoPincodesList.length === 0 ? (
                  <EmptyState title="No PIN codes found in this district" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Postal PIN</th>
                          <th className="p-3.5">District</th>
                          <th className="p-3.5 text-center">Customers</th>
                          <th className="p-3.5 text-center">Total Orders</th>
                          <th className="p-3.5 text-right">Total Revenue</th>
                          <th className="p-3.5 text-right pr-6">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {geoPincodesList.map((pin) => {
                          const isUnknownPin = !pin.pincode || pin.pincode.toLowerCase().includes('unknown') || pin.pincode === '000000';
                          return (
                            <tr key={pin.pincode} className="hover:bg-slate-50 transition-colors">
                              <td className="p-3.5 pl-6 font-mono font-bold text-slate-900">
                                {isUnknownPin ? (
                                  <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded border border-amber-300 font-semibold text-xs">
                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                                    {pin.pincode || 'Unknown PIN'}
                                  </span>
                                ) : (
                                  <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-200">
                                    {pin.pincode}
                                  </span>
                                )}
                              </td>
                              <td className="p-3.5 text-slate-700 font-medium">{pin.district}</td>
                              <td className="p-3.5 text-center font-semibold text-slate-800">{formatNumber(pin.customer_count)}</td>
                              <td className="p-3.5 text-center text-slate-600">{formatNumber(pin.total_orders)}</td>
                              <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">{formatCurrency(pin.total_revenue)}</td>
                              <td className="p-3.5 text-right pr-6 space-x-2">
                                {isUnknownPin && (
                                  <button
                                    onClick={() => navigate('/unknown-locations?tab=unknown_pincode')}
                                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-md border border-amber-300 shadow-2xs"
                                    title="Open Unknown Location Data session to correct PIN codes"
                                  >
                                    <AlertTriangle className="w-3 h-3 text-amber-600" />
                                    Resolve PINs
                                  </button>
                                )}
                                <button
                                  onClick={() => setGeoPincode(pin.pincode)}
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 shadow-2xs"
                                >
                                  View Customers <ChevronRight className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              // Level 1: Districts
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-indigo-600" />
                    All Districts ({geoDistrictsList.length})
                  </h3>
                  <span className="text-xs text-slate-500">Click any district to begin hierarchical postal drill-down</span>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : geoDistrictsList.length === 0 ? (
                  <EmptyState title="No districts recorded" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">District Name</th>
                          <th className="p-3.5">State</th>
                          <th className="p-3.5 text-center">Customers</th>
                          <th className="p-3.5 text-center">Total Orders</th>
                          <th className="p-3.5 text-right">Total Revenue</th>
                          <th className="p-3.5 text-right pr-6">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {geoDistrictsList.map((d) => {
                          const isUnknownDist = !d.district || d.district.toLowerCase().includes('unknown') || d.district.toLowerCase().includes('unassigned');
                          return (
                            <tr key={d.district} className="hover:bg-slate-50 transition-colors">
                              <td className="p-3.5 pl-6 font-bold text-slate-900">
                                {isUnknownDist ? (
                                  <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded border border-amber-300 font-semibold text-xs">
                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                                    {d.district}
                                  </span>
                                ) : (
                                  d.district
                                )}
                              </td>
                              <td className="p-3.5 text-slate-600">{d.state || '-'}</td>
                              <td className="p-3.5 text-center font-semibold text-slate-800">{formatNumber(d.customer_count)}</td>
                              <td className="p-3.5 text-center text-slate-600">{formatNumber(d.total_orders)}</td>
                              <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">{formatCurrency(d.total_revenue)}</td>
                              <td className="p-3.5 text-right pr-6 space-x-2">
                                {isUnknownDist && (
                                  <button
                                    onClick={() => navigate('/unknown-locations?tab=unknown_district')}
                                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-md border border-amber-300 shadow-2xs"
                                    title="Open Unknown Location Data session to correct missing/unknown districts"
                                  >
                                    <AlertTriangle className="w-3 h-3 text-amber-600" />
                                    Resolve District
                                  </button>
                                )}
                                <button
                                  onClick={() => setGeoDistrict(d.district)}
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 shadow-2xs"
                                >
                                  Drill Down <ChevronRight className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* VIEW 2: Product Drilldown (Product -> Orders -> Customers)    */}
        {/* ------------------------------------------------------------- */}
        {dimension === 'product' && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            {selectedProduct ? (
              // Level 2: Orders for Selected Product
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setSelectedProduct(null)}
                      className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                      title="Back to Products"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <ShoppingBag className="w-4 h-4 text-indigo-600" />
                        Orders containing <span className="text-indigo-600 font-bold">{selectedProduct.product_name}</span> ({totalItems})
                      </h3>
                      <p className="text-[11px] text-slate-500">
                        SKU: {selectedProduct.sku || 'N/A'} • Unit Price: {formatCurrency(selectedProduct.price)} • Category: {selectedProduct.category || 'General'}
                      </p>
                    </div>
                  </div>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : productOrdersList.length === 0 ? (
                  <EmptyState title="No orders found for this product" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Order ID</th>
                          <th className="p-3.5">Customer</th>
                          <th className="p-3.5">Order Date</th>
                          <th className="p-3.5">Payment</th>
                          <th className="p-3.5">Status</th>
                          <th className="p-3.5 text-right">Order Amount</th>
                          <th className="p-3.5 text-right pr-6">Customer Profile</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {productOrdersList.map((o) => (
                          <tr key={o.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-mono font-bold text-indigo-700">#{o.order_number}</td>
                            <td className="p-3.5">
                              <div className="font-semibold text-slate-900">{o.customer_name || 'Customer'}</div>
                              <div className="text-[11px] text-slate-500">{o.customer_district} {o.customer_pincode ? `• ${o.customer_pincode}` : ''}</div>
                            </td>
                            <td className="p-3.5 text-slate-600">{formatDateTime(o.order_date)}</td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200">
                                {o.payment_mode}
                              </span>
                            </td>
                            <td className="p-3.5">
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getStatusBadgeColor(o.order_status)}`}>
                                {o.order_status}
                              </span>
                            </td>
                            <td className="p-3.5 text-right font-bold text-slate-900 text-sm">{formatCurrency(o.total_amount)}</td>
                            <td className="p-3.5 text-right pr-6">
                              <button
                                onClick={() => setModalCustomerId(o.customer_id)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-1 rounded-md border border-indigo-200 shadow-2xs"
                              >
                                View Customer <Eye className="w-3 h-3" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              // Level 1: Products List
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Package className="w-4 h-4 text-indigo-600" />
                    Product Catalog Performance ({totalItems})
                  </h3>
                  <span className="text-xs text-slate-500">Click any product to drill down into order and customer records</span>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : productsList.length === 0 ? (
                  <EmptyState title="No products found" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Product Name</th>
                          <th className="p-3.5">SKU / Code</th>
                          <th className="p-3.5">Category</th>
                          <th className="p-3.5 text-right">Price</th>
                          <th className="p-3.5 text-center">Units Sold</th>
                          <th className="p-3.5 text-center">Orders</th>
                          <th className="p-3.5 text-right">Total Revenue</th>
                          <th className="p-3.5 text-right pr-6">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {productsList.map((p) => (
                          <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-semibold text-slate-900 max-w-[220px] truncate">{p.product_name}</td>
                            <td className="p-3.5 font-mono text-slate-600">{p.sku || '-'}</td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] border border-slate-200">
                                {p.category || 'General'}
                              </span>
                            </td>
                            <td className="p-3.5 text-right text-slate-800 font-medium">{formatCurrency(p.price)}</td>
                            <td className="p-3.5 text-center font-bold text-indigo-600">{formatNumber(p.total_units_sold)}</td>
                            <td className="p-3.5 text-center text-slate-700">{p.total_orders}</td>
                            <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">{formatCurrency(p.total_revenue)}</td>
                            <td className="p-3.5 text-right pr-6">
                              <button
                                onClick={() => setSelectedProduct(p)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 shadow-2xs"
                              >
                                Drill Down <ChevronRight className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* VIEW 3: Customer Drilldown (Customer -> Order History)         */}
        {/* ------------------------------------------------------------- */}
        {dimension === 'customer' && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            {selectedCustomer ? (
              // Level 2: Selected Customer Order History
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setSelectedCustomer(null)}
                      className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                      title="Back to Customers"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <ShoppingBag className="w-4 h-4 text-indigo-600" />
                        Order History for <span className="text-indigo-600 font-bold">{selectedCustomer.customer_name}</span> ({totalItems})
                      </h3>
                      <p className="text-[11px] text-slate-500">
                        {selectedCustomer.district || 'N/A'} • PIN {selectedCustomer.pincode || 'N/A'} • Lifetime Spend: {formatCurrency(selectedCustomer.total_spend)}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="xs"
                    variant="outline"
                    icon={<Eye className="w-3.5 h-3.5" />}
                    onClick={() => setModalCustomerId(selectedCustomer.id)}
                  >
                    Open Full Profile
                  </Button>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : customerOrdersList.length === 0 ? (
                  <EmptyState title="No orders recorded for this customer" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Order ID</th>
                          <th className="p-3.5">Order Date</th>
                          <th className="p-3.5">Payment</th>
                          <th className="p-3.5">Status</th>
                          <th className="p-3.5 text-right">Subtotal</th>
                          <th className="p-3.5 text-right">Total Amount</th>
                          <th className="p-3.5 text-right pr-6">Revenue Amount</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {customerOrdersList.map((o) => (
                          <tr key={o.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-mono font-bold text-indigo-700">#{o.order_number}</td>
                            <td className="p-3.5 text-slate-600">{formatDateTime(o.order_date)}</td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200">
                                {o.payment_mode}
                              </span>
                            </td>
                            <td className="p-3.5">
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getStatusBadgeColor(o.order_status)}`}>
                                {o.order_status}
                              </span>
                            </td>
                            <td className="p-3.5 text-right text-slate-700">{formatCurrency(o.subtotal || o.total_amount)}</td>
                            <td className="p-3.5 text-right font-bold text-slate-900 text-sm">{formatCurrency(o.total_amount)}</td>
                            <td className="p-3.5 text-right font-bold text-emerald-600 pr-6 text-sm">{formatCurrency(o.revenue_amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              // Level 1: Customer Directory
              <div>
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Users className="w-4 h-4 text-indigo-600" />
                    Customer Directory ({totalItems})
                  </h3>
                  <span className="text-xs text-slate-500">Click any customer row or action to drill down into order timeline</span>
                </div>

                {loading ? (
                  <div className="p-6"><LoadingSkeleton rows={6} /></div>
                ) : customersList.length === 0 ? (
                  <EmptyState title="No customers found" />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="p-3.5 pl-6">Customer Name</th>
                          <th className="p-3.5">Contact</th>
                          <th className="p-3.5">District</th>
                          <th className="p-3.5">PIN</th>
                          <th className="p-3.5 text-center">Orders</th>
                          <th className="p-3.5 text-right">Total Spend</th>
                          <th className="p-3.5 text-center">RFM Segment</th>
                          <th className="p-3.5 text-right pr-6">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {customersList.map((c) => (
                          <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 pl-6 font-semibold text-slate-900">{c.customer_name}</td>
                            <td className="p-3.5 font-mono text-slate-700">{c.contact_number || '-'}</td>
                            <td className="p-3.5 text-slate-700">{c.district || '-'}</td>
                            <td className="p-3.5 font-mono text-indigo-700 font-semibold">{c.pincode || '-'}</td>
                            <td className="p-3.5 text-center font-bold text-slate-800">{c.total_orders}</td>
                            <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">{formatCurrency(c.total_spend)}</td>
                            <td className="p-3.5 text-center">
                              {c.rfm_segment ? (
                                <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getRfmSegmentBadgeColor(c.rfm_segment)}`}>
                                  {c.rfm_segment}
                                </span>
                              ) : '-'}
                            </td>
                            <td className="p-3.5 text-right pr-6">
                              <button
                                onClick={() => setSelectedCustomer(c)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 shadow-2xs"
                              >
                                Order History <ChevronRight className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Pagination */}
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={totalItems}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      </div>

      {/* Customer Profile Modal */}
      <CustomerProfileModal
        customerId={modalCustomerId}
        isOpen={Boolean(modalCustomerId)}
        onClose={() => setModalCustomerId(null)}
      />
    </div>
  );
};
