import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin,
  ChevronRight,
  Search,
  Download,
  Users,
  ShoppingBag,
  ArrowLeft,
  Building,
  Navigation,
  Hash,
  IndianRupee,
  Layers,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  AlertTriangle
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { CustomerProfileModal } from '../components/customer/CustomerProfileModal';
import { analyticsApi } from '../services/analyticsApi';
import { customerApi } from '../services/customerApi';
import { reportApi } from '../services/reportApi';
import { DistrictAnalyticsItem, PincodeAnalyticsItem, Customer } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useDebounce } from '../hooks/useDebounce';

export const GeographicAnalytics: React.FC = () => {
  const navigate = useNavigate();
  // Navigation mode: 'district-drilldown' | 'all-pincodes'
  const [viewMode, setViewMode] = useState<'district-drilldown' | 'all-pincodes'>('district-drilldown');

  // Drill-down levels: 'district' -> 'pincode' -> 'customer'
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);
  const [selectedPincode, setSelectedPincode] = useState<string | null>(null);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);

  // Data states
  const [districts, setDistricts] = useState<DistrictAnalyticsItem[]>([]);
  const [pincodes, setPincodes] = useState<PincodeAnalyticsItem[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  // Sorting
  const [sortField, setSortField] = useState<'revenue' | 'orders' | 'customers' | 'name'>('revenue');
  const [sortAsc, setSortAsc] = useState(false);

  // 1. Fetch District Level Data
  const loadDistricts = async (currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await analyticsApi.getDistricts(currentSearch || undefined);
      setDistricts(data);
    } catch (err) {
      console.error('Failed to load districts:', err);
    } finally {
      setLoading(false);
    }
  };

  // 2. Fetch Pincodes (either for selected district or all pincodes)
  const loadPincodes = async (dist?: string | null, currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await analyticsApi.getPincodes(dist || undefined, currentSearch || undefined);
      setPincodes(data);
    } catch (err) {
      console.error('Failed to load pincodes:', err);
    } finally {
      setLoading(false);
    }
  };

  // 3. Fetch Customers for Selected PIN
  const loadCustomers = async (pin: string) => {
    setLoading(true);
    try {
      const data = await customerApi.list({ pincode: pin, page_size: 100 });
      setCustomers(data.items);
    } catch (err) {
      console.error('Failed to load customers for PIN:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'all-pincodes') {
      if (selectedPincode) {
        loadCustomers(selectedPincode);
      } else {
        loadPincodes(null, debouncedSearch);
      }
    } else {
      if (!selectedDistrict) {
        loadDistricts(debouncedSearch);
      } else if (selectedDistrict && !selectedPincode) {
        loadPincodes(selectedDistrict, debouncedSearch);
      } else if (selectedPincode) {
        loadCustomers(selectedPincode);
      }
    }
  }, [viewMode, selectedDistrict, selectedPincode, debouncedSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (viewMode === 'all-pincodes') {
      if (!selectedPincode) loadPincodes(null, search);
    } else {
      if (!selectedDistrict) loadDistricts(search);
      else if (!selectedPincode) loadPincodes(selectedDistrict, search);
    }
  };

  const handleSortToggle = (field: 'revenue' | 'orders' | 'customers' | 'name') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === 'name');
    }
  };

  const renderSortIcon = (field: 'revenue' | 'orders' | 'customers' | 'name') => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-slate-500 opacity-60 inline-block ml-1" />;
    }
    return sortAsc ? (
      <ArrowUp className="w-3 h-3 text-indigo-400 inline-block ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 text-indigo-400 inline-block ml-1" />
    );
  };

  // Sort helpers
  const sortedDistricts = [...districts].sort((a, b) => {
    if (sortField === 'revenue') return sortAsc ? a.total_revenue - b.total_revenue : b.total_revenue - a.total_revenue;
    if (sortField === 'orders') return sortAsc ? a.total_orders - b.total_orders : b.total_orders - a.total_orders;
    if (sortField === 'customers') return sortAsc ? a.customer_count - b.customer_count : b.customer_count - a.customer_count;
    return sortAsc ? a.district.localeCompare(b.district) : b.district.localeCompare(a.district);
  });

  const sortedPincodes = [...pincodes].sort((a, b) => {
    if (sortField === 'revenue') return sortAsc ? a.total_revenue - b.total_revenue : b.total_revenue - a.total_revenue;
    if (sortField === 'orders') return sortAsc ? a.total_orders - b.total_orders : b.total_orders - a.total_orders;
    if (sortField === 'customers') return sortAsc ? a.customer_count - b.customer_count : b.customer_count - a.customer_count;
    return sortAsc ? a.pincode.localeCompare(b.pincode) : b.pincode.localeCompare(a.pincode);
  });

  // Dynamic context-aware aggregate stats (District or PIN wise)
  let currentRevenue = 0;
  let currentCustomers = 0;
  let currentOrders = 0;
  let contextLabel = 'All Districts';

  if (selectedPincode) {
    contextLabel = `PIN: ${selectedPincode}${selectedDistrict ? ` • ${selectedDistrict}` : ''}`;
    currentCustomers = customers.length;
    currentOrders = customers.reduce((acc, c) => acc + c.total_orders, 0);
    currentRevenue = customers.reduce((acc, c) => acc + c.total_spend, 0);
  } else if (selectedDistrict) {
    contextLabel = `District: ${selectedDistrict}`;
    currentCustomers = pincodes.reduce((acc, p) => acc + p.customer_count, 0);
    currentOrders = pincodes.reduce((acc, p) => acc + p.total_orders, 0);
    currentRevenue = pincodes.reduce((acc, p) => acc + p.total_revenue, 0);
  } else if (viewMode === 'all-pincodes') {
    contextLabel = debouncedSearch ? `Filtered PIN Codes (${sortedPincodes.length})` : `All PIN Codes (${pincodes.length})`;
    currentCustomers = sortedPincodes.reduce((acc, p) => acc + p.customer_count, 0);
    currentOrders = sortedPincodes.reduce((acc, p) => acc + p.total_orders, 0);
    currentRevenue = sortedPincodes.reduce((acc, p) => acc + p.total_revenue, 0);
  } else {
    contextLabel = debouncedSearch ? `Filtered Districts (${sortedDistricts.length})` : `All Districts (${districts.length})`;
    currentCustomers = sortedDistricts.reduce((acc, d) => acc + d.customer_count, 0);
    currentOrders = sortedDistricts.reduce((acc, d) => acc + d.total_orders, 0);
    currentRevenue = sortedDistricts.reduce((acc, d) => acc + d.total_revenue, 0);
  }

  return (
    <div>
      <Header
        title="Geographic Intelligence & Postal Drilldown"
        subtitle="Explore regional penetration: District → PIN Code → Customers → Order History"
        action={
          <Button
            size="sm"
            variant="outline"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => reportApi.downloadGeographic('xlsx')}
          >
            Export Geography
          </Button>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Top Metric Cards - District / PIN Wise */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-4 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200">
              <IndianRupee className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Geographic Revenue</div>
              <div className="text-xl font-bold text-emerald-600">{formatCurrency(currentRevenue)}</div>
              <div className="text-[10px] text-slate-400 font-medium truncate max-w-[200px] mt-0.5">{contextLabel}</div>
            </div>
          </Card>

          <Card className="p-4 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-200">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Mapped Customers</div>
              <div className="text-xl font-bold text-slate-900">{formatNumber(currentCustomers)}</div>
              <div className="text-[10px] text-slate-400 font-medium truncate max-w-[200px] mt-0.5">{contextLabel}</div>
            </div>
          </Card>

          <Card className="p-4 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-200">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Total Orders</div>
              <div className="text-xl font-bold text-slate-900">{formatNumber(currentOrders)}</div>
              <div className="text-[10px] text-slate-400 font-medium truncate max-w-[200px] mt-0.5">{contextLabel}</div>
            </div>
          </Card>
        </div>

        {/* View Mode Toggle & Breadcrumbs */}
        <div className="flex flex-wrap items-center justify-between gap-4 glass-card p-3 rounded-xl border border-slate-200 shadow-xs">
          {/* Breadcrumb Path */}
          <div className="flex items-center gap-2 text-xs font-semibold">
            {viewMode === 'district-drilldown' ? (
              <>
                <button
                  onClick={() => {
                    setSelectedDistrict(null);
                    setSelectedPincode(null);
                  }}
                  className={`flex items-center gap-1.5 transition-colors ${
                    !selectedDistrict ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Navigation className="w-3.5 h-3.5" /> All Districts
                </button>

                {selectedDistrict && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <button
                      onClick={() => setSelectedPincode(null)}
                      className={`transition-colors ${
                        !selectedPincode
                          ? 'text-indigo-600 font-bold'
                          : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      District: {selectedDistrict}
                    </button>
                  </>
                )}

                {selectedPincode && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-indigo-600 font-bold font-mono">
                      PIN: {selectedPincode}
                    </span>
                  </>
                )}
              </>
            ) : (
              <>
                <button
                  onClick={() => setSelectedPincode(null)}
                  className={`flex items-center gap-1.5 transition-colors ${
                    !selectedPincode ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Hash className="w-3.5 h-3.5" /> All PIN Codes
                </button>
                {selectedPincode && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-indigo-600 font-bold font-mono">
                      PIN: {selectedPincode}
                    </span>
                  </>
                )}
              </>
            )}
          </div>

          {/* View Mode Toggle Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setViewMode('district-drilldown');
                setSelectedDistrict(null);
                setSelectedPincode(null);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 border ${
                viewMode === 'district-drilldown'
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
              }`}
            >
              <Building className="w-3.5 h-3.5" /> District Drilldown
            </button>

            <button
              onClick={() => {
                setViewMode('all-pincodes');
                setSelectedDistrict(null);
                setSelectedPincode(null);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 border ${
                viewMode === 'all-pincodes'
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
              }`}
            >
              <Hash className="w-3.5 h-3.5" /> All PIN Codes
            </button>
          </div>
        </div>

        {/* Search filter */}
        <div className="glass-card p-4 rounded-xl shadow-xs">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder={
                  viewMode === 'all-pincodes'
                    ? 'Search by 6-digit PIN code, District name...'
                    : selectedDistrict
                    ? `Search PIN codes in ${selectedDistrict}...`
                    : 'Search districts...'
                }
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
            </div>
            <Button size="sm" type="submit">
              Search
            </Button>
            {search && (
              <Button
                size="sm"
                variant="outline"
                type="button"
                onClick={() => {
                  setSearch('');
                  if (viewMode === 'all-pincodes') loadPincodes(null);
                  else if (!selectedDistrict) loadDistricts();
                  else loadPincodes(selectedDistrict);
                }}
              >
                Clear
              </Button>
            )}
          </form>
        </div>

        {/* Level 1: Districts (in District Drilldown mode) */}
        {viewMode === 'district-drilldown' && !selectedDistrict && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <Building className="w-4 h-4 text-indigo-600" />
                Districts ({sortedDistricts.length})
              </h3>
              <span className="text-xs text-slate-500">Click any district to view its postal PIN codes</span>
            </div>

            {loading ? (
              <div className="p-6">
                <LoadingSkeleton rows={6} />
              </div>
            ) : sortedDistricts.length === 0 ? (
              <EmptyState
                title="No district records"
                description="Import customers with PIN or District data to visualize regional distribution."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th
                        onClick={() => handleSortToggle('name')}
                        className="p-3.5 pl-6 cursor-pointer hover:text-indigo-600 select-none"
                      >
                        District Name {renderSortIcon('name')}
                      </th>
                      <th className="p-3.5">State</th>
                      <th
                        onClick={() => handleSortToggle('customers')}
                        className="p-3.5 text-center cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Customers {renderSortIcon('customers')}
                      </th>
                      <th
                        onClick={() => handleSortToggle('orders')}
                        className="p-3.5 text-center cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Total Orders {renderSortIcon('orders')}
                      </th>
                      <th
                        onClick={() => handleSortToggle('revenue')}
                        className="p-3.5 text-right pr-6 cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Total Revenue {renderSortIcon('revenue')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {sortedDistricts.map((d, idx) => {
                      const isUnknownDist = !d.district || d.district.toLowerCase().includes('unknown') || d.district.toLowerCase().includes('unassigned');
                      return (
                        <tr
                          key={idx}
                          onClick={() => {
                            setSelectedDistrict(d.district);
                            setSelectedPincode(null);
                          }}
                          className="hover:bg-slate-50 cursor-pointer transition-colors group"
                        >
                          <td className="p-3.5 pl-6 font-semibold text-slate-900 flex items-center gap-2">
                            <MapPin className="w-3.5 h-3.5 text-indigo-600 group-hover:scale-110 transition-transform" />
                            {isUnknownDist ? (
                              <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded border border-amber-300 font-semibold text-xs">
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                                {d.district}
                              </span>
                            ) : (
                              <span className="group-hover:text-indigo-600 transition-colors">{d.district}</span>
                            )}
                            {isUnknownDist && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate('/unknown-locations?tab=unknown_district');
                                }}
                                className="ml-2 inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 hover:text-amber-900 bg-amber-100 hover:bg-amber-200 px-2 py-0.5 rounded border border-amber-300 shadow-2xs"
                                title="Resolve in Unknown Location Data session"
                              >
                                Fix Location
                              </button>
                            )}
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400 ml-auto group-hover:text-indigo-600 transition-colors" />
                          </td>

                          <td className="p-3.5 text-slate-600">
                            {d.state || '-'}
                          </td>

                          <td className="p-3.5 text-center font-semibold text-slate-800">
                            {formatNumber(d.customer_count)}
                          </td>

                          <td className="p-3.5 text-center text-slate-600">
                            {formatNumber(d.total_orders)}
                          </td>

                          <td className="p-3.5 text-right font-bold text-emerald-600 pr-6 text-sm">
                            {formatCurrency(d.total_revenue)}
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

        {/* Level 2: PIN Codes (either inside Selected District OR in All PIN Codes mode) */}
        {((viewMode === 'district-drilldown' && selectedDistrict && !selectedPincode) ||
          (viewMode === 'all-pincodes' && !selectedPincode)) && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {viewMode === 'district-drilldown' && (
                  <button
                    onClick={() => setSelectedDistrict(null)}
                    className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                    title="Back to Districts"
                  >
                    <ArrowLeft className="w-4 h-4" />
                  </button>
                )}
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <Hash className="w-4 h-4 text-indigo-600" />
                  {viewMode === 'district-drilldown' ? (
                    <>
                      PIN Codes in <span className="text-indigo-600 font-bold">{selectedDistrict}</span> ({sortedPincodes.length})
                    </>
                  ) : (
                    <>
                      All Postal PIN Codes ({sortedPincodes.length})
                    </>
                  )}
                </h3>
              </div>
              <span className="text-xs text-slate-500">Click a PIN code to view customer profiles</span>
            </div>

            {loading ? (
              <div className="p-6">
                <LoadingSkeleton rows={6} />
              </div>
            ) : sortedPincodes.length === 0 ? (
              <EmptyState title="No PIN codes found" description="No postal PIN data found for this query." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th
                        onClick={() => handleSortToggle('name')}
                        className="p-3.5 pl-6 cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Postal PIN Code {renderSortIcon('name')}
                      </th>
                      <th className="p-3.5">District / Region</th>
                      <th
                        onClick={() => handleSortToggle('customers')}
                        className="p-3.5 text-center cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Customers {renderSortIcon('customers')}
                      </th>
                      <th
                        onClick={() => handleSortToggle('orders')}
                        className="p-3.5 text-center cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Total Orders {renderSortIcon('orders')}
                      </th>
                      <th
                        onClick={() => handleSortToggle('revenue')}
                        className="p-3.5 text-right pr-6 cursor-pointer hover:text-indigo-600 select-none"
                      >
                        Total Revenue {renderSortIcon('revenue')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {sortedPincodes.map((pin, idx) => {
                      const isUnknownPin = !pin.pincode || pin.pincode.toLowerCase().includes('unknown') || pin.pincode === '000000';
                      return (
                        <tr
                          key={idx}
                          onClick={() => setSelectedPincode(pin.pincode)}
                          className="hover:bg-slate-50 cursor-pointer transition-colors group"
                        >
                          <td className="p-3.5 pl-6 font-mono font-bold text-slate-900 flex items-center gap-2">
                            {isUnknownPin ? (
                              <span className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded border border-amber-300 font-semibold text-xs">
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                                {pin.pincode || 'Unknown PIN'}
                              </span>
                            ) : (
                              <span className="bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded border border-indigo-200 group-hover:border-indigo-400 transition-colors">
                                {pin.pincode}
                              </span>
                            )}
                            {isUnknownPin && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate('/unknown-locations?tab=unknown_pincode');
                                }}
                                className="ml-2 inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 hover:text-amber-900 bg-amber-100 hover:bg-amber-200 px-2 py-0.5 rounded border border-amber-300 shadow-2xs"
                                title="Resolve in Unknown Location Data session"
                              >
                                Fix PIN
                              </button>
                            )}
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400 ml-auto group-hover:text-indigo-600 transition-colors" />
                          </td>

                          <td className="p-3.5 text-slate-700 font-medium">
                            {pin.district}
                            {pin.state ? <span className="text-slate-400 ml-1">({pin.state})</span> : null}
                          </td>

                          <td className="p-3.5 text-center font-semibold text-slate-800">
                            {formatNumber(pin.customer_count)}
                          </td>

                          <td className="p-3.5 text-center text-slate-600">
                            {formatNumber(pin.total_orders)}
                          </td>

                          <td className="p-3.5 text-right font-bold text-emerald-600 pr-6 text-sm">
                            {formatCurrency(pin.total_revenue)}
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

        {/* Level 3: Customers for Selected PIN Code */}
        {selectedPincode && (
          <div className="glass-card rounded-xl overflow-hidden shadow-xs">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSelectedPincode(null)}
                  className="p-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                  title="Back to PIN codes"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <h3 className="text-sm font-semibold text-slate-900">
                  Customers in PIN <span className="text-indigo-600 font-mono font-bold">{selectedPincode}</span> ({customers.length})
                </h3>
              </div>
              <span className="text-xs text-slate-500">Click any customer row to inspect full profile & order history</span>
            </div>

            {loading ? (
              <div className="p-6">
                <LoadingSkeleton rows={5} />
              </div>
            ) : customers.length === 0 ? (
              <EmptyState title="No customers in this PIN" />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="p-3.5 pl-6">Customer Name</th>
                      <th className="p-3.5">Contact</th>
                      <th className="p-3.5">Post Office / Address</th>
                      <th className="p-3.5 text-center">Orders</th>
                      <th className="p-3.5 text-right pr-6">Total Spend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {customers.map((c) => (
                      <tr
                        key={c.id}
                        onClick={() => setSelectedCustomerId(c.id)}
                        className="hover:bg-slate-50 cursor-pointer transition-colors"
                      >
                        <td className="p-3.5 pl-6 font-semibold text-slate-900">
                          {c.customer_name}
                        </td>

                        <td className="p-3.5 font-mono text-slate-700">
                          {c.contact_number || '-'}
                        </td>

                        <td className="p-3.5 text-slate-600 max-w-[280px] truncate">
                          {c.post_office ? <span className="text-slate-800 font-semibold mr-1.5">[{c.post_office}]</span> : null}
                          {c.full_address || '-'}
                        </td>

                        <td className="p-3.5 text-center font-bold text-slate-800">
                          {c.total_orders}
                        </td>

                        <td className="p-3.5 text-right font-bold text-emerald-600 pr-6 text-sm">
                          {formatCurrency(c.total_spend)}
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

      <CustomerProfileModal
        customerId={selectedCustomerId}
        isOpen={Boolean(selectedCustomerId)}
        onClose={() => setSelectedCustomerId(null)}
      />
    </div>
  );
};
