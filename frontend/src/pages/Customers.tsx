import React, { useEffect, useState } from 'react';
import {
  Users,
  Search,
  Filter,
  Eye,
  FileSpreadsheet,
  Download,
  IndianRupee,
  ShoppingBag,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  RotateCcw,
  Sparkles,
  Layers,
  MapPin,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { CustomerProfileModal } from '../components/customer/CustomerProfileModal';
import { CopyCustomerButton } from '../components/customer/CopyCustomerButton';
import { customerApi } from '../services/customerApi';
import { reportApi } from '../services/reportApi';
import { Customer } from '../types';
import { formatCurrency, formatDate, getRfmSegmentBadgeColor } from '../utils/formatters';

const RFM_SEGMENTS = [
  'Champions',
  'Loyal Customers',
  'Potential Loyalists',
  'New Customers',
  'At Risk',
  'Dormant Customers',
  'Lost Customers',
];

import { useDebounce } from '../hooks/useDebounce';

export const Customers: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [district, setDistrict] = useState('');
  const [postOffice, setPostOffice] = useState('');
  const [pincode, setPincode] = useState('');
  const [rfmSegment, setRfmSegment] = useState('');
  const [minOrders, setMinOrders] = useState<string>('');
  const [maxOrders, setMaxOrders] = useState<string>('');
  const [minSpend, setMinSpend] = useState<string>('');
  const [maxSpend, setMaxSpend] = useState<string>('');
  const [sortBy, setSortBy] = useState('total_spend');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Selected customer for modal
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);

  const fetchCustomers = async (currentPage = page, currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await customerApi.list({
        page: currentPage,
        page_size: pageSize,
        search: currentSearch || undefined,
        district: district || undefined,
        post_office: postOffice || undefined,
        pincode: pincode || undefined,
        rfm_segment: rfmSegment || undefined,
        min_orders: minOrders ? parseInt(minOrders, 10) : undefined,
        max_orders: maxOrders ? parseInt(maxOrders, 10) : undefined,
        min_spend: minSpend ? parseFloat(minSpend) : undefined,
        max_spend: maxSpend ? parseFloat(maxSpend) : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setCustomers(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to fetch customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers(page, debouncedSearch);
  }, [page, debouncedSearch, district, postOffice, pincode, rfmSegment, minOrders, maxOrders, minSpend, maxSpend, sortBy, sortOrder]);

  // Reset to page 1 whenever debounced search query changes
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers(1, search);
  };

  const handleResetFilters = () => {
    setSearch('');
    setDistrict('');
    setPostOffice('');
    setPincode('');
    setRfmSegment('');
    setMinOrders('');
    setMaxOrders('');
    setMinSpend('');
    setMaxSpend('');
    setSortBy('total_spend');
    setSortOrder('desc');
    setPage(1);
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder(field === 'total_spend' || field === 'total_orders' || field === 'created_at' ? 'desc' : 'asc');
    }
    setPage(1);
  };

  const renderSortIcon = (field: string) => {
    if (sortBy !== field) {
      return <ArrowUpDown className="w-3 h-3 text-slate-500 opacity-60 inline-block ml-1" />;
    }
    return sortOrder === 'asc' ? (
      <ArrowUp className="w-3 h-3 text-indigo-400 inline-block ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 text-indigo-400 inline-block ml-1" />
    );
  };

  const handleExport = (format: 'xlsx' | 'csv') => {
    reportApi.downloadCustomers({
      format,
      search: search || undefined,
      district: district || undefined,
      post_office: postOffice || undefined,
      pincode: pincode || undefined,
      rfm_segment: rfmSegment || undefined,
      min_orders: minOrders ? parseInt(minOrders, 10) : undefined,
      max_orders: maxOrders ? parseInt(maxOrders, 10) : undefined,
      min_spend: minSpend ? parseFloat(minSpend) : undefined,
      max_spend: maxSpend ? parseFloat(maxSpend) : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    });
  };

  const hasActiveFilters = Boolean(
    search || district || postOffice || pincode || rfmSegment || minOrders || maxOrders || minSpend || maxSpend
  );

  return (
    <div>
      <Header
        title="Customer-wise Analytics Dashboard"
        action={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              icon={<Download className="w-3.5 h-3.5 text-emerald-400" />}
              onClick={() => handleExport('xlsx')}
            >
              Export Excel
            </Button>
            <Button
              size="sm"
              variant="outline"
              icon={<FileSpreadsheet className="w-3.5 h-3.5 text-indigo-400" />}
              onClick={() => handleExport('csv')}
            >
              Export CSV
            </Button>
          </div>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Quick Segment Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <button
            onClick={() => {
              setRfmSegment('');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all whitespace-nowrap border ${
              rfmSegment === ''
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50 shadow-2xs'
            }`}
          >
            All Segments ({total.toLocaleString('en-IN')})
          </button>
          {RFM_SEGMENTS.map((seg) => (
            <button
              key={seg}
              onClick={() => {
                setRfmSegment(rfmSegment === seg ? '' : seg);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all whitespace-nowrap border ${
                rfmSegment === seg
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50 shadow-2xs'
              }`}
            >
              {seg}
            </button>
          ))}
        </div>

        {/* Search and Filters Card */}
        <div className="glass-card p-4 rounded-xl space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search by customer name, mobile phone, district, PIN..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
              />
            </div>

            <input
              type="text"
              placeholder="District"
              value={district}
              onChange={(e) => {
                setDistrict(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 min-w-[120px] shadow-2xs"
            />

            <input
              type="text"
              placeholder="Post Office"
              value={postOffice}
              onChange={(e) => {
                setPostOffice(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 min-w-[120px] shadow-2xs"
            />

            <input
              type="text"
              placeholder="PIN Code"
              value={pincode}
              onChange={(e) => {
                setPincode(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 min-w-[100px] font-mono shadow-2xs"
            />

            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split('-');
                setSortBy(sb);
                setSortOrder(so);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 font-medium shadow-2xs"
            >
              <option value="total_spend-desc">💰 Highest Spend First</option>
              <option value="total_spend-asc">💰 Lowest Spend First</option>
              <option value="total_orders-desc">📦 Most Orders First</option>
              <option value="average_order_value-desc">📈 Highest AOV First</option>
              <option value="customer_name-asc">👤 Name (A to Z)</option>
              <option value="customer_name-desc">👤 Name (Z to A)</option>
              <option value="district-asc">📍 District (A to Z)</option>
              <option value="district-desc">📍 District (Z to A)</option>
              <option value="post_office-asc">📮 Post Office (A to Z)</option>
              <option value="post_office-desc">📮 Post Office (Z to A)</option>
              <option value="pincode-asc">🔢 PIN Code (0-9)</option>
              <option value="pincode-desc">🔢 PIN Code (9-0)</option>
              <option value="created_at-desc">🕒 Newest Added First</option>
            </select>

            <Button size="sm" type="submit">
              Search
            </Button>

            <button
              type="button"
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="px-2.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs"
            >
              <Filter className="w-3.5 h-3.5 text-indigo-600" />
              <span>More Filters</span>
              {showAdvancedFilters ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-2.5 py-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-medium flex items-center gap-1 transition-colors border border-rose-200"
                title="Reset all filters"
              >
                <RotateCcw className="w-3 h-3" />
                Reset
              </button>
            )}
          </form>

          {/* Advanced Filter Expansion */}
          {showAdvancedFilters && (
            <div className="pt-3 mt-3 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <label className="text-slate-600 block mb-1 font-medium">Min Orders</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 2"
                  value={minOrders}
                  onChange={(e) => {
                    setMinOrders(e.target.value);
                    setPage(1);
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 font-medium">Max Orders</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 50"
                  value={maxOrders}
                  onChange={(e) => {
                    setMaxOrders(e.target.value);
                    setPage(1);
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 font-medium">Min Spend (₹)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 1000"
                  value={minSpend}
                  onChange={(e) => {
                    setMinSpend(e.target.value);
                    setPage(1);
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
                />
              </div>
              <div>
                <label className="text-slate-600 block mb-1 font-medium">Max Spend (₹)</label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 50000"
                  value={maxSpend}
                  onChange={(e) => {
                    setMaxSpend(e.target.value);
                    setPage(1);
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
                />
              </div>
            </div>
          )}
        </div>

        {/* Customer Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-600" />
              Customer Records ({total.toLocaleString('en-IN')})
            </h3>
            <span className="text-xs text-slate-500">Click any row or action icon to inspect customer profile & orders</span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={8} />
            </div>
          ) : customers.length === 0 ? (
            <EmptyState
              title="No customers match your criteria"
              description="Try adjusting your search keywords, district filters, or order/spend ranges."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th
                      onClick={() => handleSort('customer_name')}
                      className="p-3.5 pl-6 cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      Customer {renderSortIcon('customer_name')}
                    </th>
                    <th className="p-3.5">Contact</th>
                    <th
                      onClick={() => handleSort('district')}
                      className="p-3.5 cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      District {renderSortIcon('district')}
                    </th>
                    <th
                      onClick={() => handleSort('post_office')}
                      className="p-3.5 cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      Post Office {renderSortIcon('post_office')}
                    </th>
                    <th
                      onClick={() => handleSort('pincode')}
                      className="p-3.5 cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      PIN {renderSortIcon('pincode')}
                    </th>
                    <th
                      onClick={() => handleSort('total_orders')}
                      className="p-3.5 text-center cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      Orders {renderSortIcon('total_orders')}
                    </th>
                    <th
                      onClick={() => handleSort('total_spend')}
                      className="p-3.5 text-right cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      Total Spend {renderSortIcon('total_spend')}
                    </th>
                    <th
                      onClick={() => handleSort('average_order_value')}
                      className="p-3.5 text-right cursor-pointer hover:text-indigo-600 transition-colors select-none"
                    >
                      AOV {renderSortIcon('average_order_value')}
                    </th>
                    <th className="p-3.5 text-center">RFM Segment</th>
                    <th className="p-3.5 text-right pr-6">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {customers.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => setSelectedCustomerId(c.id)}
                      className="hover:bg-slate-50/90 cursor-pointer transition-colors"
                    >
                      <td className="p-3.5 pl-6">
                        <div className="font-semibold text-slate-900 text-sm">{c.customer_name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">ID #{c.id}</div>
                      </td>

                      <td className="p-3.5">
                        <span className="font-mono text-slate-700">
                          {c.contact_number || c.normalized_contact || '-'}
                        </span>
                      </td>

                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium border border-slate-200/80">
                          {c.district || '-'}
                        </span>
                      </td>

                      <td className="p-3.5">
                        <span className="text-slate-700">
                          {c.post_office || '-'}
                        </span>
                      </td>

                      <td className="p-3.5 font-mono text-indigo-700 font-semibold">
                        {c.pincode || '-'}
                      </td>

                      <td className="p-3.5 text-center">
                        <span className="inline-block px-2.5 py-0.5 rounded-md bg-slate-100 font-semibold text-slate-800 border border-slate-200">
                          {c.total_orders}
                        </span>
                      </td>

                      <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">
                        {formatCurrency(c.total_spend)}
                      </td>

                      <td className="p-3.5 text-right text-slate-700">
                        {formatCurrency(c.average_order_value)}
                      </td>

                      <td className="p-3.5 text-center">
                        {c.rfm_segment ? (
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getRfmSegmentBadgeColor(
                              c.rfm_segment
                            )}`}
                          >
                            {c.rfm_segment}
                          </span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                        {c.rfm_score && (
                          <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                            Score: {c.rfm_score}
                          </div>
                        )}
                      </td>

                      <td
                        className="p-3.5 text-right pr-6"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex items-center justify-end gap-2">
                          <CopyCustomerButton customer={c} size="xs" />
                          <button
                            onClick={() => setSelectedCustomerId(c.id)}
                            className="p-1.5 rounded-lg bg-white hover:bg-slate-50 text-indigo-600 transition-colors border border-slate-300 shadow-2xs"
                            title="Open Customer Profile"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
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

      {/* Customer Profile Modal */}
      <CustomerProfileModal
        customerId={selectedCustomerId}
        isOpen={Boolean(selectedCustomerId)}
        onClose={() => setSelectedCustomerId(null)}
      />
    </div>
  );
};
