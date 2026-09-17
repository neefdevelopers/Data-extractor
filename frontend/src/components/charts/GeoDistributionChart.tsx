import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { DistrictAnalyticsItem } from '../../types';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface GeoDistributionChartProps {
  districts: DistrictAnalyticsItem[];
  limit?: number;
}

export const GeoDistributionChart: React.FC<GeoDistributionChartProps> = ({
  districts,
  limit = 8,
}) => {
  const activeDistricts = (districts || []).filter(
    (d) => d.district && d.district.trim() !== '' && (d.total_revenue > 0 || d.total_orders > 0)
  );

  if (!activeDistricts || activeDistricts.length === 0) {
    return (
      <div className="flex items-center justify-center h-56 text-xs text-slate-500">
        No geographic data available.
      </div>
    );
  }

  const chartData = activeDistricts.slice(0, limit).map((d) => ({
    name: d.district,
    revenue: d.total_revenue,
    orders: d.total_orders,
    customers: d.customer_count,
  }));

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 20, left: 30, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
          <XAxis
            type="number"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#475569"
            fontSize={11}
            tickLine={false}
            axisLine={false}
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
            formatter={(val: any, name: any, item: any) => [
              `${formatCurrency(Number(val))} (${item.payload.orders} orders, ${item.payload.customers} customers)`,
              'Revenue',
            ]}
          />
          <Bar dataKey="revenue" fill="#6366f1" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
