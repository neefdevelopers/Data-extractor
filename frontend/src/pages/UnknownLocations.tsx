import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  MapPin,
  Building,
  AlertTriangle,
  History,
  Search,
  RotateCcw,
  Edit3,
  Layers,
  CheckSquare,
  Square,
  Sparkles,
  CheckCircle2,
  FileSpreadsheet,
  ArrowUpRight,
  HelpCircle,
  Hash
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { Pagination } from '../components/common/Pagination';
import { EditLocationModal } from '../components/location/EditLocationModal';
import { BulkLocationModal } from '../components/location/BulkLocationModal';
import { LocationAuditHistoryModal } from '../components/location/LocationAuditHistoryModal';
import { locationApi } from '../services/locationApi';
import { UnknownLocationSummary, UnknownLocationRecord } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useDebounce } from '../hooks/useDebounce';

export const UnknownLocations: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'all';

  const [activeTab, setActiveTab] = useState<'all' | 'unknown_pincode' | 'unknown_district'>(
    initialTab === 'unknown_pincode' || initialTab === 'unknown_district' ? initialTab : 'all'
  );

  const [summary, setSummary] = useState<UnknownLocationSummary | null>(null);
  const [records, setRecords] = useState<UnknownLocationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Pagination
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Selection & Bulk Actions
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);

  // Edit Single Record Modal
  const [editingRecord, setEditingRecord] = useState<UnknownLocationRecord | null>(null);

  // Audit History Modal
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  // Synchronize tab state with searchParams
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'unknown_pincode' || tabParam === 'unknown_district') {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const handleTabChange = (tab: 'all' | 'unknown_pincode' | 'unknown_district') => {
    setActiveTab(tab);
    setSearchParams(tab === 'all' ? {} : { tab });
    setPage(1);
    setSelectedIds([]);
  };

  const loadSummary = async () => {
    try {
      const data = await locationApi.getSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load location summary:', err);
    }
  };

  const loadRecords = async () => {
    setLoading(true);
    try {
      const data = await locationApi.getUnknownRecords({
        filter_type: activeTab,
        search: debouncedSearch || undefined,
        page,
        page_size: pageSize
      });
      setRecords(data.items);
      setTotalRecords(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load unknown location records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    loadRecords();
  }, [activeTab, debouncedSearch, page]);

  const handleSelectAll = () => {
    if (selectedIds.length === records.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(records.map((r) => r.id));
    }
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleCorrectionSuccess = () => {
    loadSummary();
    loadRecords();
    setSelectedIds([]);
  };

  return (
    <div>
      <Header
        title="Unknown Location Data"
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAuditModalOpen(true)}
              className="flex items-center gap-1.5 shadow-2xs"
            >
              <History className="w-3.5 h-3.5 text-indigo-600" />
              <span>Audit History</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                loadSummary();
                loadRecords();
              }}
              className="flex items-center gap-1.5 shadow-2xs"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-600" />
              <span>Refresh</span>
            </Button>
          </div>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Top 4 KPI Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Unresolved */}
            <Card className="relative overflow-hidden border-indigo-200 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Total Unresolved Records</span>
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <AlertTriangle className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                  {formatNumber(summary.total_unresolved)}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">Unique customer profiles</p>
              </div>
            </Card>

            {/* Unknown Pincode */}
            <Card
              className={`relative overflow-hidden shadow-2xs cursor-pointer transition-all ${
                activeTab === 'unknown_pincode' ? 'ring-2 ring-amber-500 border-amber-300' : ''
              }`}
              onClick={() => handleTabChange('unknown_pincode')}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Unknown Pincode</span>
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                  <Hash className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-amber-600 tracking-tight">
                  {formatNumber(summary.unknown_pincode_count)}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">Missing 6-digit PIN</p>
              </div>
            </Card>

            {/* Unknown District */}
            <Card
              className={`relative overflow-hidden shadow-2xs cursor-pointer transition-all ${
                activeTab === 'unknown_district' ? 'ring-2 ring-rose-500 border-rose-300' : ''
              }`}
              onClick={() => handleTabChange('unknown_district')}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Unknown District</span>
                <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                  <Building className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-rose-600 tracking-tight">
                  {formatNumber(summary.unknown_district_count)}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">Unassigned district</p>
              </div>
            </Card>

            {/* Both Unknown */}
            <Card className="relative overflow-hidden shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Both Unknown</span>
                <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
                  <HelpCircle className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-purple-600 tracking-tight">
                  {formatNumber(summary.both_unknown_count)}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">No PIN & No District</p>
              </div>
            </Card>
          </div>
        )}

        {/* Main Content Area */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs border border-slate-200">
          {/* Tabs and Search Toolbar */}
          <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4">
            {/* Category Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium">
              {[
                { label: 'All Unknown Records', value: 'all' },
                { label: 'Unknown Pincode', value: 'unknown_pincode' },
                { label: 'Unknown District', value: 'unknown_district' },
              ].map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => handleTabChange(tab.value as any)}
                  className={`px-3 py-1.5 rounded-md transition-all font-semibold ${
                    activeTab === tab.value
                      ? 'bg-white text-indigo-700 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search and Bulk Action */}
            <div className="flex items-center gap-3">
              {selectedIds.length > 0 && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsBulkModalOpen(true)}
                  className="flex items-center gap-1.5 shadow-2xs animate-in fade-in"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Bulk Update ({selectedIds.length})</span>
                </Button>
              )}

              <div className="relative min-w-[280px]">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search customer, phone, address..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
                />
              </div>
            </div>
          </div>

          {/* Table of Records */}
          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={6} />
            </div>
          ) : records.length === 0 ? (
            <div className="p-12">
              <EmptyState
                title="No Unknown Locations Found"
                description={
                  debouncedSearch
                    ? `No matching records found for query "${debouncedSearch}".`
                    : 'All customer records have verified District and Pincode information!'
                }
                icon={<CheckCircle2 className="w-8 h-8 text-emerald-500" />}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/90 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
                  <tr>
                    <th className="p-3 pl-4 w-10">
                      <button onClick={handleSelectAll} className="text-slate-500 hover:text-indigo-600">
                        {selectedIds.length === records.length && records.length > 0 ? (
                          <CheckSquare className="w-4 h-4 text-indigo-600" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>
                    </th>
                    <th className="p-3">Customer Information</th>
                    <th className="p-3">Address on File</th>
                    <th className="p-3">District</th>
                    <th className="p-3">Pincode</th>
                    <th className="p-3">Orders & Spend</th>
                    <th className="p-3 text-right pr-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((r) => {
                    const isSelected = selectedIds.includes(r.id);
                    return (
                      <tr
                        key={r.id}
                        className={`hover:bg-slate-50/80 transition-colors ${
                          isSelected ? 'bg-indigo-50/40' : ''
                        }`}
                      >
                        <td className="p-3 pl-4">
                          <button onClick={() => handleToggleSelect(r.id)} className="text-slate-400">
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-indigo-600" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        </td>

                        <td className="p-3">
                          <div className="space-y-0.5">
                            <span className="font-semibold text-slate-900 block">{r.customer_name}</span>
                            <span className="text-slate-500 text-[11px] block">
                              {r.contact_number || r.normalized_contact || 'No Contact'}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">ID #{r.id}</span>
                          </div>
                        </td>

                        <td className="p-3 max-w-xs">
                          <p className="text-slate-600 text-[11px] line-clamp-2 leading-relaxed">
                            {r.full_address || '—'}
                          </p>
                          {r.post_office && (
                            <span className="text-[10px] text-slate-500 font-medium block mt-0.5">
                              PO: {r.post_office}
                            </span>
                          )}
                        </td>

                        <td className="p-3">
                          {r.district ? (
                            <span className="font-semibold text-slate-900">{r.district}</span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                              Unknown District
                            </span>
                          )}
                        </td>

                        <td className="p-3">
                          {r.pincode ? (
                            <span className="font-bold text-slate-900 font-mono tracking-wider">
                              {r.pincode}
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                              Unknown PIN
                            </span>
                          )}
                        </td>

                        <td className="p-3">
                          <div className="space-y-0.5 text-[11px]">
                            <span className="font-bold text-slate-800 block">
                              {formatCurrency(r.total_spend)}
                            </span>
                            <span className="text-slate-500">{r.total_orders} Orders</span>
                          </div>
                        </td>

                        <td className="p-3 text-right pr-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingRecord(r)}
                            className="inline-flex items-center gap-1.5 shadow-2xs font-semibold text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 border-indigo-200"
                          >
                            <Edit3 className="w-3 h-3" />
                            <span>Edit Location</span>
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Showing {records.length} of {totalRecords} unresolved records
              </span>
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                totalItems={totalRecords}
                pageSize={pageSize}
                onPageChange={setPage}
              />
            </div>
          )}
        </div>
      </div>

      {/* Edit Location Modal */}
      <EditLocationModal
        isOpen={Boolean(editingRecord)}
        onClose={() => setEditingRecord(null)}
        record={editingRecord}
        onSuccess={handleCorrectionSuccess}
      />

      {/* Bulk Location Correction Modal */}
      <BulkLocationModal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        selectedIds={selectedIds}
        onSuccess={handleCorrectionSuccess}
      />

      {/* Location Audit History Modal */}
      <LocationAuditHistoryModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
      />
    </div>
  );
};
