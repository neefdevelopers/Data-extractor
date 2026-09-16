import React, { useEffect, useState } from 'react';
import { UserCheck, Search, Download, TrendingUp, Users, ShoppingBag } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Button } from '../components/common/Button';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { employeeApi } from '../services/employeeApi';
import { reportApi } from '../services/reportApi';
import { Employee } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useDebounce } from '../hooks/useDebounce';

export const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [status, setStatus] = useState('');
  const [sortBy, setSortBy] = useState('total_revenue');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchEmployees = async (currentPage = page, currentSearch = debouncedSearch) => {
    setLoading(true);
    try {
      const data = await employeeApi.list({
        page: currentPage,
        page_size: pageSize,
        search: currentSearch || undefined,
        status: status || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setEmployees(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to fetch employees:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees(page, debouncedSearch);
  }, [page, debouncedSearch, status, sortBy, sortOrder]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEmployees(1, search);
  };

  return (
    <div>
      <Header
        title="Sales & Employee Analytics"
        subtitle="Evaluate sales representative performance, revenue generation, and order volumes"
        action={
          <Button
            size="sm"
            variant="outline"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => reportApi.downloadEmployees('xlsx')}
          >
            Export Employees
          </Button>
        }
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Filters */}
        <div className="glass-card p-4 rounded-xl space-y-3 shadow-xs">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search employee name or code..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
              />
            </div>

            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>

            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split('-');
                setSortBy(sb);
                setSortOrder(so);
                setPage(1);
              }}
              className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-2xs"
            >
              <option value="total_revenue-desc">Highest Revenue First</option>
              <option value="total_orders-desc">Most Orders First</option>
              <option value="customer_count-desc">Most Customers First</option>
              <option value="employee_name-asc">Name (A-Z)</option>
            </select>

            <Button size="sm" type="submit">
              Filter
            </Button>
          </form>
        </div>

        {/* Employee Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-indigo-600" />
              Sales Representative Performance ({total})
            </h3>
            <span className="text-xs text-slate-500">Calculated from actual qualifying orders</span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={6} />
            </div>
          ) : employees.length === 0 ? (
            <EmptyState
              title="No employees found"
              description="Assign sales reps to orders or upload order spreadsheets with employee headers."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3.5 pl-6">Employee</th>
                    <th className="p-3.5">Code</th>
                    <th className="p-3.5 text-center">Status</th>
                    <th className="p-3.5 text-center">Orders</th>
                    <th className="p-3.5 text-center">Customers</th>
                    <th className="p-3.5 text-right">Total Revenue</th>
                    <th className="p-3.5 text-right">AOV</th>
                    <th className="p-3.5 text-right pr-6">COD / Prepaid Split</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {employees.map((emp) => (
                    <tr key={emp.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-semibold text-slate-900">
                        {emp.employee_name}
                      </td>

                      <td className="p-3.5 font-mono text-slate-600">
                        {emp.employee_code || '-'}
                      </td>

                      <td className="p-3.5 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {emp.status}
                        </span>
                      </td>

                      <td className="p-3.5 text-center font-bold text-slate-800">
                        {emp.total_orders}
                      </td>

                      <td className="p-3.5 text-center text-slate-600">
                        {emp.customer_count}
                      </td>

                      <td className="p-3.5 text-right font-bold text-emerald-600 text-sm">
                        {formatCurrency(emp.total_revenue)}
                      </td>

                      <td className="p-3.5 text-right text-slate-700">
                        {formatCurrency(emp.average_order_value)}
                      </td>

                      <td className="p-3.5 text-right pr-6 text-[11px]">
                        <span className="text-amber-700 font-medium">COD: {formatCurrency(emp.cod_revenue)}</span>
                        <span className="text-slate-300 mx-1.5">•</span>
                        <span className="text-blue-700 font-medium">Prepaid: {formatCurrency(emp.prepaid_revenue)}</span>
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
