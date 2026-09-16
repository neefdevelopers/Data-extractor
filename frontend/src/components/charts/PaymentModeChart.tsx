import React, { useState } from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { PaymentModeBreakdown } from '../../types';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface PaymentModeChartProps {
  data: PaymentModeBreakdown[];
  metricType?: 'revenue' | 'orders';
}

const COLORS = ['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];

export const PaymentModeChart: React.FC<PaymentModeChartProps> = ({
  data,
  metricType: initialMetricType = 'revenue',
}) => {
  const [metricType, setMetricType] = useState<'revenue' | 'orders'>(initialMetricType);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-slate-500">
        No payment breakdown data available.
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: item.payment_mode,
    value: metricType === 'revenue' ? item.revenue : item.order_count,
    percentage: metricType === 'revenue' ? item.percentage_revenue : item.percentage_orders,
    revenue: item.revenue,
    orders: item.order_count,
    aov: item.average_order_value || (item.order_count > 0 ? item.revenue / item.order_count : 0),
  }));

  const codItem = data.find((d) => d.payment_mode.toUpperCase() === 'COD');
  const prepaidItem = data.find((d) => d.payment_mode.toUpperCase() === 'PREPAID');

  return (
    <div className="space-y-4">
      {/* Metric Mode Toggle */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <span className="text-xs font-semibold text-slate-700">Distribution Basis</span>
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
          <button
            onClick={() => setMetricType('revenue')}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              metricType === 'revenue'
                ? 'bg-white text-indigo-600 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            By Revenue
          </button>
          <button
            onClick={() => setMetricType('orders')}
            className={`px-2.5 py-1 rounded-md transition-all font-medium ${
              metricType === 'orders'
                ? 'bg-white text-indigo-600 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            By Orders
          </button>
        </div>
      </div>

      {/* Donut Chart */}
      <div style={{ width: '100%', height: 210 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={78}
              paddingAngle={4}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.name === 'COD' ? '#f59e0b' : '#3b82f6'}
                />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || payload.length === 0) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-lg text-xs space-y-1 min-w-[150px]">
                    <div className="font-bold text-slate-900 flex items-center justify-between border-b border-slate-100 pb-1">
                      <span>{d.name}</span>
                      <span className="text-slate-500 font-semibold">{d.percentage}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Revenue:</span>
                      <span className="font-bold text-slate-800">{formatCurrency(d.revenue)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Orders:</span>
                      <span className="font-bold text-slate-800">{formatNumber(d.orders)}</span>
                    </div>
                    <div className="flex justify-between text-[11px] pt-1 border-t border-slate-100">
                      <span className="text-slate-500">AOV:</span>
                      <span className="font-semibold text-slate-700">{formatCurrency(d.aov)}</span>
                    </div>
                  </div>
                );
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={30}
              formatter={(value, entry: any) => (
                <span className="text-xs text-slate-700 font-medium">
                  {value} ({entry.payload.percentage}%)
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Comparison Mini-Stats */}
      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
        <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200/80 space-y-1">
          <div className="flex items-center justify-between font-bold text-amber-900">
            <span>COD</span>
            <span>{codItem ? `${codItem.percentage_revenue}% rev` : '0%'}</span>
          </div>
          <div className="text-amber-800 font-semibold text-sm">
            {codItem ? formatCurrency(codItem.revenue) : '₹0'}
          </div>
          <div className="text-[11px] text-amber-700 flex items-center justify-between">
            <span>{codItem?.order_count || 0} orders</span>
            <span>AOV: {codItem ? formatCurrency(codItem.average_order_value || (codItem.order_count > 0 ? codItem.revenue / codItem.order_count : 0)) : '₹0'}</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-blue-50/60 border border-blue-200/80 space-y-1">
          <div className="flex items-center justify-between font-bold text-blue-900">
            <span>PREPAID</span>
            <span>{prepaidItem ? `${prepaidItem.percentage_revenue}% rev` : '0%'}</span>
          </div>
          <div className="text-blue-800 font-semibold text-sm">
            {prepaidItem ? formatCurrency(prepaidItem.revenue) : '₹0'}
          </div>
          <div className="text-[11px] text-blue-700 flex items-center justify-between">
            <span>{prepaidItem?.order_count || 0} orders</span>
            <span>AOV: {prepaidItem ? formatCurrency(prepaidItem.average_order_value || (prepaidItem.order_count > 0 ? prepaidItem.revenue / prepaidItem.order_count : 0)) : '₹0'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
