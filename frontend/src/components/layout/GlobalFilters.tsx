import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Filter,
  X,
  Search,
  RotateCcw,
  Package,
  UserCheck,
  CreditCard,
  MapPin,
  Tag,
  ChevronDown,
  ChevronUp,
  Activity
} from 'lucide-react';
import { GlobalFilterState, Product, Employee } from '../../types';
import { productApi } from '../../services/productApi';
import { employeeApi } from '../../services/employeeApi';

interface GlobalFiltersProps {
  filters: GlobalFilterState;
  onFilterChange: (filters: GlobalFilterState) => void;
  showSearch?: boolean;
  showPaymentMode?: boolean;
  showDistrict?: boolean;
  showPincode?: boolean;
  showRfmSegment?: boolean;
  showProduct?: boolean;
  showEmployee?: boolean;
  showOrderStatus?: boolean;
}

export const GlobalFilters: React.FC<GlobalFiltersProps> = ({
  filters,
  onFilterChange,
  showSearch = true,
  showPaymentMode = true,
  showDistrict = true,
  showPincode = true,
  showRfmSegment = true,
  showProduct = true,
  showEmployee = true,
  showOrderStatus = true,
}) => {
  const [isCustomDate, setIsCustomDate] = useState(filters.preset === 'custom');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [productList, setProductList] = useState<Product[]>([]);
  const [employeeList, setEmployeeList] = useState<Employee[]>([]);

  useEffect(() => {
    if (showProduct) {
      productApi.list({ page: 1, page_size: 100, sort_by: 'product_name', sort_order: 'asc' })
        .then((res) => setProductList(res.items))
        .catch((err) => console.error('Failed to load products for filter:', err));
    }
  }, [showProduct]);

  useEffect(() => {
    if (showEmployee) {
      employeeApi.list({ page: 1, page_size: 100, sort_by: 'employee_name', sort_order: 'asc' })
        .then((res) => setEmployeeList(res.items))
        .catch((err) => console.error('Failed to load employees for filter:', err));
    }
  }, [showEmployee]);

  const handlePresetChange = (preset: string) => {
    if (preset === 'custom') {
      setIsCustomDate(true);
      onFilterChange({ ...filters, preset: 'custom' });
    } else {
      setIsCustomDate(false);
      onFilterChange({ ...filters, preset, startDate: undefined, endDate: undefined });
    }
  };

  const handleReset = () => {
    setIsCustomDate(false);
    onFilterChange({
      preset: 'all',
      startDate: undefined,
      endDate: undefined,
      employeeId: undefined,
      paymentMode: undefined,
      productId: undefined,
      district: undefined,
      pincode: undefined,
      rfmSegment: undefined,
      orderStatus: undefined,
      search: undefined,
      customerId: undefined,
    });
  };

  const activeFilterCount = [
    filters.preset !== 'all',
    Boolean(filters.startDate || filters.endDate),
    Boolean(filters.employeeId),
    Boolean(filters.paymentMode),
    Boolean(filters.productId),
    Boolean(filters.district),
    Boolean(filters.pincode),
    Boolean(filters.rfmSegment),
    Boolean(filters.orderStatus),
    Boolean(filters.search),
    Boolean(filters.customerId),
  ].filter(Boolean).length;

  return (
    <div className="glass-card p-4 rounded-xl space-y-3 mb-6 shadow-xs border border-slate-200">
      {/* Top row: Date Presets & Filter Summary */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium">
          {[
            { label: 'All Time', value: 'all' },
            { label: 'Today', value: 'today' },
            { label: 'Yesterday', value: 'yesterday' },
            { label: 'Last 7 Days', value: '7d' },
            { label: 'Last 30 Days', value: '30d' },
            { label: 'This Month', value: 'thismonth' },
            { label: 'Previous Month', value: 'prevmonth' },
            { label: 'Custom Range', value: 'custom' },
          ].map((item) => (
            <button
              key={item.value}
              onClick={() => handlePresetChange(item.value)}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filters.preset === item.value
                  ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg border transition-colors ${
              showAdvanced || activeFilterCount > 0
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700 font-semibold'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Filter className="w-3 h-3 text-indigo-600" />
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] flex items-center justify-center font-bold">
                {activeFilterCount}
              </span>
            )}
            {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {activeFilterCount > 0 && (
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 text-xs text-rose-600 hover:text-rose-700 font-medium px-2.5 py-1.5 rounded-lg bg-rose-50 border border-rose-200 transition-colors shadow-2xs"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Custom Date Range Row */}
      {isCustomDate && (
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          <span className="text-slate-600 font-medium flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-indigo-600" /> From:
          </span>
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => onFilterChange({ ...filters, startDate: e.target.value })}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
          />
          <span className="text-slate-600 font-medium flex items-center gap-1">
            To:
          </span>
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => onFilterChange({ ...filters, endDate: e.target.value })}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
          />
        </div>
      )}

      {/* Primary Row: Quick Search, Product, Payment Mode, Order Status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-100">
        {showSearch && (
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search customer, phone, order #..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange({ ...filters, search: e.target.value || undefined })}
              className="w-full bg-white border border-slate-300 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          </div>
        )}

        {showProduct && (
          <select
            value={filters.productId || ''}
            onChange={(e) =>
              onFilterChange({
                ...filters,
                productId: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs truncate"
          >
            <option value="">All Products</option>
            {productList.map((p) => (
              <option key={p.id} value={p.id}>
                {p.product_name} {p.sku ? `(${p.sku})` : ''}
              </option>
            ))}
          </select>
        )}

        {showPaymentMode && (
          <select
            value={filters.paymentMode || ''}
            onChange={(e) => onFilterChange({ ...filters, paymentMode: e.target.value || undefined })}
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs"
          >
            <option value="">All Payment Modes</option>
            <option value="COD">Cash on Delivery (COD)</option>
            <option value="PREPAID">Prepaid (Online / UPI)</option>
          </select>
        )}

        {showOrderStatus && (
          <select
            value={filters.orderStatus || ''}
            onChange={(e) => onFilterChange({ ...filters, orderStatus: e.target.value || undefined })}
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs"
          >
            <option value="">All Order Statuses</option>
            <option value="DELIVERED">Delivered</option>
            <option value="COMPLETED">Completed</option>
            <option value="PENDING">Pending</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="RETURNED">Returned</option>
            <option value="REFUNDED">Refunded</option>
          </select>
        )}
      </div>

      {/* Advanced Filter Row (Employee, District, Pincode, RFM Segment) */}
      {showAdvanced && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-slate-100 animate-in fade-in duration-200">
          {showEmployee && (
            <select
              value={filters.employeeId || ''}
              onChange={(e) =>
                onFilterChange({
                  ...filters,
                  employeeId: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs"
            >
              <option value="">All Employees</option>
              {employeeList.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_name} {emp.employee_code ? `(${emp.employee_code})` : ''}
                </option>
              ))}
            </select>
          )}

          {showDistrict && (
            <input
              type="text"
              placeholder="District (e.g. Mumbai, Pune)"
              value={filters.district || ''}
              onChange={(e) => onFilterChange({ ...filters, district: e.target.value || undefined })}
              className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          )}

          {showPincode && (
            <input
              type="text"
              placeholder="Pincode (e.g. 400001)"
              value={filters.pincode || ''}
              onChange={(e) => onFilterChange({ ...filters, pincode: e.target.value || undefined })}
              className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          )}

          {showRfmSegment && (
            <select
              value={filters.rfmSegment || ''}
              onChange={(e) => onFilterChange({ ...filters, rfmSegment: e.target.value || undefined })}
              className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 shadow-2xs"
            >
              <option value="">All RFM Segments</option>
              <option value="Champions">Champions</option>
              <option value="Loyal Customers">Loyal Customers</option>
              <option value="Potential Loyalists">Potential Loyalists</option>
              <option value="New Customers">New Customers</option>
              <option value="At Risk">At Risk</option>
              <option value="Dormant Customers">Dormant Customers</option>
              <option value="Lost Customers">Lost Customers</option>
            </select>
          )}
        </div>
      )}

      {/* Active Filter Chips / Badges */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100 text-xs">
          <span className="text-slate-400 text-[11px] font-medium mr-1">Active filters:</span>
          {filters.preset !== 'all' && (
            <span className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Period: {filters.preset}
              <X className="w-3 h-3 cursor-pointer hover:text-indigo-900" onClick={() => handlePresetChange('all')} />
            </span>
          )}
          {filters.productId && (
            <span className="inline-flex items-center gap-1 bg-sky-50 text-sky-700 border border-sky-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Product ID: {filters.productId}
              <X className="w-3 h-3 cursor-pointer hover:text-sky-900" onClick={() => onFilterChange({ ...filters, productId: undefined })} />
            </span>
          )}
          {filters.paymentMode && (
            <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Payment: {filters.paymentMode}
              <X className="w-3 h-3 cursor-pointer hover:text-amber-900" onClick={() => onFilterChange({ ...filters, paymentMode: undefined })} />
            </span>
          )}
          {filters.orderStatus && (
            <span className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 border border-violet-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Status: {filters.orderStatus}
              <X className="w-3 h-3 cursor-pointer hover:text-violet-900" onClick={() => onFilterChange({ ...filters, orderStatus: undefined })} />
            </span>
          )}
          {filters.employeeId && (
            <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Employee ID: {filters.employeeId}
              <X className="w-3 h-3 cursor-pointer hover:text-emerald-900" onClick={() => onFilterChange({ ...filters, employeeId: undefined })} />
            </span>
          )}
          {filters.district && (
            <span className="inline-flex items-center gap-1 bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              District: {filters.district}
              <X className="w-3 h-3 cursor-pointer hover:text-teal-900" onClick={() => onFilterChange({ ...filters, district: undefined })} />
            </span>
          )}
          {filters.pincode && (
            <span className="inline-flex items-center gap-1 bg-cyan-50 text-cyan-700 border border-cyan-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              PIN: {filters.pincode}
              <X className="w-3 h-3 cursor-pointer hover:text-cyan-900" onClick={() => onFilterChange({ ...filters, pincode: undefined })} />
            </span>
          )}
          {filters.rfmSegment && (
            <span className="inline-flex items-center gap-1 bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-full text-[11px] font-medium">
              RFM: {filters.rfmSegment}
              <X className="w-3 h-3 cursor-pointer hover:text-purple-900" onClick={() => onFilterChange({ ...filters, rfmSegment: undefined })} />
            </span>
          )}
          {filters.search && (
            <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded-full text-[11px] font-medium">
              Search: "{filters.search}"
              <X className="w-3 h-3 cursor-pointer hover:text-slate-900" onClick={() => onFilterChange({ ...filters, search: undefined })} />
            </span>
          )}
        </div>
      )}
    </div>
  );
};
