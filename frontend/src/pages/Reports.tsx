import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  Users,
  ShoppingBag,
  Package,
  UserCheck,
  MapPin,
  Flame,
  FileText
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { reportApi } from '../services/reportApi';

export const Reports: React.FC = () => {
  const [format, setFormat] = useState<'xlsx' | 'csv'>('xlsx');

  const REPORT_TYPES = [
    {
      id: 'customers',
      title: 'Customer Master Directory',
      description: 'Full customer records with contact, postal address, total lifetime spend, order count, and RFM scores.',
      icon: Users,
      action: () => reportApi.downloadCustomers({ format }),
    },
    {
      id: 'orders',
      title: 'Order Transactions Ledger',
      description: 'Complete order history with dates, revenue eligibility, COD/prepaid payment modes, customer IDs, and sales rep assignments.',
      icon: ShoppingBag,
      action: () => reportApi.downloadOrders(format),
    },
    {
      id: 'rfm',
      title: 'RFM Segment Intelligence',
      description: 'Calculated Recency, Frequency, Monetary values, quintile scores (1-5), and segment classifications.',
      icon: Flame,
      action: () => reportApi.downloadRfm(format),
    },
    {
      id: 'geographic',
      title: 'Geographic Regional Analytics',
      description: 'State and district aggregations of customer count, order volumes, and regional sales revenues.',
      icon: MapPin,
      action: () => reportApi.downloadGeographic(format),
    },
    {
      id: 'products',
      title: 'Product Catalog Sales Report',
      description: 'SKU-level performance, total units sold, gross sales revenue, and percentage revenue contribution.',
      icon: Package,
      action: () => reportApi.downloadProducts(format),
    },
    {
      id: 'employees',
      title: 'Sales Representative Performance',
      description: 'Staff member order conversions, revenue generated, COD vs prepaid collections, and average order values.',
      icon: UserCheck,
      action: () => reportApi.downloadEmployees(format),
    },
  ];

  return (
    <div>
      <Header
        title="Reports & Local Data Exports"
        subtitle="Generate formatted Excel (.xlsx) and CSV spreadsheets directly from local PostgreSQL database"
      />

      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Format Selector */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-2xs">
          <div>
            <h4 className="text-sm font-semibold text-slate-900">Select Export Format</h4>
            <p className="text-xs text-slate-500">All generated files are saved locally in exports/ directory</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFormat('xlsx')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                format === 'xlsx'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-300'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" /> Microsoft Excel (.xlsx)
            </button>
            <button
              onClick={() => setFormat('csv')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                format === 'csv'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-300'
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> Comma-Separated (.csv)
            </button>
          </div>
        </div>

        {/* Report Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {REPORT_TYPES.map((rep) => {
            const Icon = rep.icon;
            return (
              <Card key={rep.id} className="flex flex-col justify-between">
                <div>
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 border border-indigo-100">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 mb-1">{rep.title}</h4>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4">{rep.description}</p>
                </div>

                <Button
                  size="sm"
                  variant="secondary"
                  icon={<Download className="w-3.5 h-3.5" />}
                  onClick={rep.action}
                  className="w-full justify-center"
                >
                  Download {format.toUpperCase()}
                </Button>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};
