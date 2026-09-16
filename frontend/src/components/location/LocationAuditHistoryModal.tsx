import React, { useState, useEffect } from 'react';
import {
  History,
  Search,
  ArrowRight,
  ShieldCheck,
  Calendar,
  User,
  Tag
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { LoadingSkeleton } from '../common/LoadingSkeleton';
import { EmptyState } from '../common/EmptyState';
import { Pagination } from '../common/Pagination';
import { LocationAuditLog } from '../../types';
import { locationApi } from '../../services/locationApi';
import { formatDateTime } from '../../utils/formatters';

interface LocationAuditHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId?: number;
}

export const LocationAuditHistoryModal: React.FC<LocationAuditHistoryModalProps> = ({
  isOpen,
  onClose,
  customerId,
}) => {
  const [logs, setLogs] = useState<LocationAuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 15;

  const fetchLogs = async () => {
    if (!isOpen) return;
    setLoading(true);
    try {
      const res = await locationApi.getAuditHistory({
        customer_id: customerId,
        search: search || undefined,
        page,
        page_size: pageSize
      });
      setLogs(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load audit history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [isOpen, customerId, page, search]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Location Correction Audit History"
      maxWidth="4xl"
      actionFooter={
        <div className="flex items-center justify-between w-full">
          <span className="text-xs text-slate-500">Total {total} historical correction entries</span>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <p className="text-xs text-slate-500">
          Immutable log of all manual, postal API, and bulk location updates.
        </p>
        {/* Search bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by customer name, district, PIN code, or author..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full bg-white border border-slate-300 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
          />
        </div>

        {loading ? (
          <LoadingSkeleton rows={5} />
        ) : logs.length === 0 ? (
          <EmptyState
            title="No Location Audits Recorded"
            description="When location data is corrected or enriched, history records will appear here."
            icon={<History className="w-8 h-8 text-slate-400" />}
          />
        ) : (
          <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
                  <tr>
                    <th className="p-3 pl-4">Timestamp</th>
                    <th className="p-3">Customer</th>
                    <th className="p-3">District Change</th>
                    <th className="p-3">PIN / Post Office Change</th>
                    <th className="p-3">Source & Author</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3 pl-4 text-slate-500 whitespace-nowrap text-[11px]">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="p-3 font-semibold text-slate-900">
                        {log.customer_name || `Customer #${log.customer_id}`}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5 font-medium">
                          <span className="text-slate-400 line-through text-[11px]">
                            {log.previous_district || 'Unknown'}
                          </span>
                          <ArrowRight className="w-3 h-3 text-indigo-500" />
                          <span className="text-slate-900 font-semibold">
                            {log.new_district || 'Unassigned'}
                          </span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400 line-through text-[11px] font-mono">
                              {log.previous_pincode || 'Unknown'}
                            </span>
                            <ArrowRight className="w-3 h-3 text-indigo-500" />
                            <span className="text-indigo-700 font-mono font-bold">
                              {log.new_pincode || '—'}
                            </span>
                          </div>
                          {log.new_post_office && (
                            <span className="text-[11px] text-slate-500 block">
                              PO: {log.new_post_office}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex flex-col gap-0.5">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold w-max ${
                            log.correction_source === 'POSTAL_API'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : log.correction_source === 'BULK_UPDATE'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          }`}>
                            {log.correction_source}
                          </span>
                          <span className="text-[11px] text-slate-500">By {log.changed_by}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {totalPages > 1 && (
          <div className="pt-2">
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={total}
              pageSize={pageSize}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>
    </Modal>
  );
};
