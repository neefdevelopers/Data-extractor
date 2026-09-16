import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { RFMSegmentSummary } from '../../types';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface RfmMatrixChartProps {
  segments: RFMSegmentSummary[];
  metric?: 'count' | 'revenue';
}

export const RfmMatrixChart: React.FC<RfmMatrixChartProps> = ({
  segments,
  metric = 'count',
}) => {
  if (!segments || segments.length === 0) {
    return (
      <div className="flex items-center justify-center h-56 text-xs text-slate-500">
        No RFM segments calculated yet.
      </div>
    );
  }

  const chartData = segments.map((s) => ({
    name: s.segment_name,
    value: metric === 'count' ? s.customer_count : s.total_revenue,
    color: s.color_code || '#6366f1',
    percentage: s.percentage,
    revenue: s.total_revenue,
    count: s.customer_count,
  }));

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="name"
            stroke="#64748b"
            fontSize={10}
            angle={-25}
            textAnchor="end"
            tickLine={false}
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) =>
              metric === 'revenue' ? `₹${(val / 1000).toFixed(0)}k` : val
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              borderColor: '#e2e8f0',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#0f172a',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            formatter={(val: any, _, item: any) => [
              metric === 'revenue'
                ? formatCurrency(Number(val))
                : `${formatNumber(Number(val))} Customers (${item.payload.percentage}%)`,
              'Value',
            ]}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
