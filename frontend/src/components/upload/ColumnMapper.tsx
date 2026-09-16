import React from 'react';
import { ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../common/Button';

interface ColumnMapperProps {
  detectedColumns: string[];
  mappings: Record<string, string | null>;
  importType: string;
  onMappingChange: (field: string, sourceCol: string | null) => void;
  onImportTypeChange: (type: string) => void;
  onProceedToPreview: () => void;
  onCancel: () => void;
}

const FIELD_DEFINITIONS = [
  { key: 'customer_name', label: 'Customer Name', category: 'Customer', required: true },
  { key: 'contact_number', label: 'Mobile / Phone Number', category: 'Customer', required: false },
  { key: 'full_address', label: 'Full Street Address', category: 'Customer', required: false },
  { key: 'pincode', label: '6-digit PIN Code', category: 'Customer', required: false },
  { key: 'post_office', label: 'Post Office', category: 'Customer', required: false },
  { key: 'district', label: 'District', category: 'Customer', required: false },
  { key: 'state', label: 'State', category: 'Customer', required: false },

  { key: 'order_number', label: 'Order ID / Invoice No', category: 'Order', required: false },
  { key: 'order_date', label: 'Order Date', category: 'Order', required: false },
  { key: 'payment_mode', label: 'Payment Mode (COD/PREPAID)', category: 'Order', required: false },
  { key: 'order_status', label: 'Order Status', category: 'Order', required: false },
  { key: 'total_amount', label: 'Order Total Amount', category: 'Order', required: false },
  { key: 'employee_name', label: 'Assigned Sales Employee', category: 'Order', required: false },

  { key: 'product_name', label: 'Product Name', category: 'Product', required: false },
  { key: 'sku', label: 'Product SKU', category: 'Product', required: false },
  { key: 'category', label: 'Product Category', category: 'Product', required: false },
  { key: 'price', label: 'Unit Price', category: 'Product', required: false },
  { key: 'quantity', label: 'Quantity', category: 'Product', required: false },
];

export const ColumnMapper: React.FC<ColumnMapperProps> = ({
  detectedColumns,
  mappings,
  importType,
  onMappingChange,
  onImportTypeChange,
  onProceedToPreview,
  onCancel,
}) => {
  return (
    <div className="space-y-6">
      {/* Import Type Selector */}
      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">Dataset Target Type</h4>
          <p className="text-xs text-slate-500">Select what entities this spreadsheet contains</p>
        </div>
        <div className="flex items-center gap-2">
          {['COMBINED', 'CUSTOMER', 'ORDER', 'PRODUCT'].map((type) => (
            <button
              key={type}
              onClick={() => onImportTypeChange(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                importType === type
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-300'
              }`}
            >
              {type === 'COMBINED' ? 'Combined (Customer + Orders)' : type}
            </button>
          ))}
        </div>
      </div>

      {/* Column Mapping Grid */}
      <div className="glass-card rounded-xl p-5 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h4 className="text-sm font-semibold text-slate-900">Configure Column Mapping</h4>
          <span className="text-xs text-slate-500">
            Detected {detectedColumns.length} headers in uploaded file
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FIELD_DEFINITIONS.map((field) => {
            const mappedHeader = mappings[field.key] || '';
            const isMapped = Boolean(mappedHeader);

            return (
              <div
                key={field.key}
                className="bg-slate-50/80 p-3.5 rounded-xl border border-slate-200 flex items-center justify-between gap-3"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-slate-800 truncate">
                      {field.label}
                    </span>
                    {field.required && (
                      <span className="text-[10px] text-rose-500 font-bold">*</span>
                    )}
                  </div>
                  <span className="text-[10px] text-indigo-600 font-medium">
                    {field.category}
                  </span>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                  <select
                    value={mappedHeader}
                    onChange={(e) => onMappingChange(field.key, e.target.value || null)}
                    className={`bg-white border text-xs rounded-lg px-2.5 py-1.5 max-w-[170px] truncate focus:outline-none shadow-2xs ${
                      isMapped
                        ? 'border-indigo-500 text-indigo-700 font-semibold'
                        : 'border-slate-300 text-slate-500'
                    }`}
                  >
                    <option value="">-- Unmapped --</option>
                    {detectedColumns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button size="sm" onClick={onProceedToPreview}>
          Continue to Preview (20–50 Sample Rows)
        </Button>
      </div>
    </div>
  );
};
