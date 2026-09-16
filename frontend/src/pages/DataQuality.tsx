import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Filter,
  RefreshCw,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { dataQualityApi } from '../services/dataQualityApi';
import { DataQualityIssue, DataQualitySummary } from '../types';
import { formatDateTime } from '../utils/formatters';

export const DataQuality: React.FC = () => {
  const [summary, setSummary] = useState<DataQualitySummary | null>(null);
  const [issues, setIssues] = useState<DataQualityIssue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [issueType, setIssueType] = useState<string>('');
  const [isResolved, setIsResolved] = useState<boolean | undefined>(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sumData, issData] = await Promise.all([
        dataQualityApi.getSummary(),
        dataQualityApi.listIssues({
          page,
          page_size: pageSize,
          issue_type: issueType || undefined,
          is_resolved: isResolved,
        }),
      ]);
      setSummary(sumData);
      setIssues(issData.items);
      setTotal(issData.total);
      setTotalPages(issData.total_pages);
    } catch (err) {
      console.error('Failed to load data quality:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, issueType, isResolved]);

  const handleResolve = async (issueId: number) => {
    try {
      await dataQualityApi.resolveIssue(issueId);
      loadData();
    } catch (err: any) {
      alert('Error resolving issue: ' + err.message);
    }
  };

  return (
    <div>
      <Header
        title="Data Quality & Integrity Audit"
        subtitle="Detect, monitor, and resolve data anomalies, invalid phones, postal conflicts, and duplicate entries"
        action={
          <Button
            size="sm"
            variant="outline"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => dataQualityApi.downloadIssuesCsv()}
          >
            Export Error Rows (CSV)
          </Button>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* KPI Summary */}
        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="border-rose-200 bg-rose-50/40">
              <span className="text-xs text-slate-600 font-medium block mb-1">Unresolved Anomalies</span>
              <span className="text-2xl font-bold text-rose-600">{summary.unresolved_issues}</span>
              <p className="text-[11px] text-slate-500 mt-1">Requires review or data cleaning</p>
            </Card>

            <Card className="border-emerald-200 bg-emerald-50/40">
              <span className="text-xs text-slate-600 font-medium block mb-1">Resolved Anomalies</span>
              <span className="text-2xl font-bold text-emerald-600">{summary.resolved_issues}</span>
              <p className="text-[11px] text-slate-500 mt-1">Addressed during import or manual audit</p>
            </Card>

            <Card>
              <span className="text-xs text-slate-600 font-medium block mb-1">Total Audit Logs</span>
              <span className="text-2xl font-bold text-slate-900">{summary.total_issues}</span>
              <p className="text-[11px] text-slate-500 mt-1">All recorded validation events</p>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="glass-card p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-xs">
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={issueType}
              onChange={(e) => {
                setIssueType(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
            >
              <option value="">All Issue Categories</option>
              <option value="INVALID_CONTACT">Invalid Mobile Number</option>
              <option value="INVALID_PIN">Invalid PIN Code</option>
              <option value="POSTAL_CONFLICT">Postal Master Conflict</option>
              <option value="MISSING_NAME">Missing Customer Name</option>
              <option value="INVALID_DATE">Invalid Order Date</option>
              <option value="DUPLICATE_ORDER">Duplicate Order ID</option>
            </select>

            <select
              value={isResolved === undefined ? 'all' : String(isResolved)}
              onChange={(e) => {
                const val = e.target.value;
                setIsResolved(val === 'all' ? undefined : val === 'true');
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
            >
              <option value="false">Unresolved Only</option>
              <option value="true">Resolved Only</option>
              <option value="all">All Statuses</option>
            </select>
          </div>

          <button
            onClick={loadData}
            className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors border border-slate-200"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Issues List Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Logged Integrity Issues ({total})
            </h3>
            <span className="text-xs text-slate-500">Non-destructive error records</span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={6} />
            </div>
          ) : issues.length === 0 ? (
            <EmptyState
              title="Clean dataset!"
              description="No data quality issues match the current filter criteria."
              icon={<ShieldCheck className="w-8 h-8 text-emerald-600" />}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3.5 pl-6">Entity / Row</th>
                    <th className="p-3.5">Issue Type</th>
                    <th className="p-3.5">Field</th>
                    <th className="p-3.5">Audit Message & Details</th>
                    <th className="p-3.5">Suggested Remedy</th>
                    <th className="p-3.5">Logged At</th>
                    <th className="p-3.5 text-right pr-6">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {issues.map((iss) => (
                    <tr key={iss.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-mono">
                        <span className="font-bold text-slate-800">{iss.entity_type}</span>
                        {iss.row_number && (
                          <span className="text-slate-400 text-[11px] block">
                            Row #{iss.row_number}
                          </span>
                        )}
                      </td>

                      <td className="p-3.5">
                        <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-bold border border-rose-200 text-[10px]">
                          {iss.issue_type}
                        </span>
                      </td>

                      <td className="p-3.5 font-mono text-slate-700">
                        {iss.field_name}
                      </td>

                      <td className="p-3.5 text-slate-800 max-w-[280px]">
                        <div>{iss.message}</div>
                        {iss.raw_value && (
                          <div className="text-slate-400 font-mono text-[10px] truncate mt-0.5">
                            Raw: "{iss.raw_value}"
                          </div>
                        )}
                      </td>

                      <td className="p-3.5 text-slate-600 max-w-[200px] text-[11px]">
                        {iss.suggested_fix || '-'}
                      </td>

                      <td className="p-3.5 text-slate-500 text-[11px]">
                        {formatDateTime(iss.created_at)}
                      </td>

                      <td className="p-3.5 text-right pr-6">
                        {iss.is_resolved ? (
                          <span className="text-emerald-600 font-semibold text-[11px] flex items-center justify-end gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Resolved
                          </span>
                        ) : (
                          <button
                            onClick={() => handleResolve(iss.id)}
                            className="px-2.5 py-1 text-xs rounded bg-white hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 text-slate-700 font-medium transition-colors border border-slate-300 shadow-2xs"
                          >
                            Mark Resolved
                          </button>
                        )}
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
    </div>
  );
};
