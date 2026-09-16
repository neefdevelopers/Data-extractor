import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { DateWiseMetric } from '../../types';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface RevenueTrendChartProps {
  data: DateWiseMetric[];
  height?: number;
}

export const RevenueTrendChart: React.FC<RevenueTrendChartProps> = ({
  data,
  height = 320,
}) => {
  const [viewMode, setViewMode] = useState<'both' | 'revenue' | 'orders'>('both');

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-xs text-slate-500">
        No date-wise trend data available for selected period.
      </div>
    );
  }

  // Calculate summary stats
  const totalRev = data.reduce((acc, d) => acc + d.revenue, 0);
  const totalOrds = data.reduce((acc, d) => acc + d.orders, 0);
  const maxDay = data.reduce((max, d) => (d.revenue > max.revenue ? d : max), data[0]);

  return (
    <div className="space-y-4">
      {/* Header controls & summary stats */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-100">
        <div className="flex items-center gap-4 text-xs">
          <div>
            <span className="text-slate-400 block text-[10px]">Peak Day ({maxDay.date})</span>
            <span className="font-bold text-slate-800">{formatCurrency(maxDay.revenue)}</span>
          </div>
          <div className="h-6 w-px bg-slate-200" />
          <div>
            <span className="text-slate-400 block text-[10px]">Daily Avg</span>
            <span className="font-bold text-slate-800">
              {formatCurrency(totalRev / (data.length || 1))}
            </span>
          </div>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
          <button
            onClick={() => setViewMode('both')}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              viewMode === 'both'
                ? 'bg-white text-indigo-600 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Both (Dual Axis)
          </button>
          <button
            onClick={() => setViewMode('revenue')}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              viewMode === 'revenue'
                ? 'bg-white text-indigo-600 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Revenue (₹)
          </button>
          <button
            onClick={() => setViewMode('orders')}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              viewMode === 'orders'
                ? 'bg-white text-cyan-600 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Orders (Count)
          </button>
        </div>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="ordersGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            
            {(viewMode === 'both' || viewMode === 'revenue') && (
              <YAxis
                yAxisId="rev"
                stroke="#6366f1"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
              />
            )}

            {(viewMode === 'both' || viewMode === 'orders') && (
              <YAxis
                yAxisId="ord"
                orientation={viewMode === 'both' ? 'right' : 'left'}
                stroke="#0891b2"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
            )}

            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || payload.length === 0) return null;
                const d = payload[0].payload as DateWiseMetric;
                return (
                  <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-lg text-xs space-y-1.5 min-w-[170px]">
                    <div className="font-bold text-slate-900 border-b border-slate-100 pb-1 flex items-center justify-between">
                      <span>{label}</span>
                      <span className="text-[10px] text-slate-400 font-normal">Trajectory</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-indigo-600 font-medium flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-indigo-500" /> Revenue:
                      </span>
                      <span className="font-bold text-slate-800">{formatCurrency(d.revenue)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-cyan-600 font-medium flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-cyan-500" /> Orders:
                      </span>
                      <span className="font-bold text-slate-800">{formatNumber(d.orders)}</span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                      <span className="text-slate-500">Day AOV:</span>
                      <span className="font-semibold text-slate-700">{formatCurrency(d.aov)}</span>
                    </div>
                  </div>
                );
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            
            {(viewMode === 'both' || viewMode === 'revenue') && (
              <Area
                yAxisId="rev"
                type="monotone"
                dataKey="revenue"
                name="Revenue (₹)"
                stroke="#6366f1"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#revenueGrad)"
              />
            )}

            {(viewMode === 'both' || viewMode === 'orders') && (
              <Area
                yAxisId="ord"
                type="monotone"
                dataKey="orders"
                name="Order Count"
                stroke="#06b6d4"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#ordersGrad)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
