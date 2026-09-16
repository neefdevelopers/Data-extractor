import React from 'react';
import { AlertTriangle, CheckCircle2, FileSpreadsheet, Layers } from 'lucide-react';
import { Button } from '../common/Button';

interface ImportPreviewProps {
  fileName: string;
  importType: string;
  totalRows: number;
  detectedColumns: string[];
  mappings: Record<string, string | null>;
  sampleRows: Record<string, any>[];
  validationWarnings: string[];
  isImporting: boolean;
  onConfirmImport: () => void;
  onBackToMapping: () => void;
  onCancel: () => void;
}

export const ImportPreview: React.FC<ImportPreviewProps> = ({
  fileName,
  importType,
  totalRows,
  detectedColumns,
  mappings,
  sampleRows,
  validationWarnings,
  isImporting,
  onConfirmImport,
  onBackToMapping,
  onCancel,
}) => {
  const mappedCount = Object.values(mappings).filter(Boolean).length;
  const unmappedCount = detectedColumns.length - mappedCount;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-xs text-slate-500 font-medium block mb-1">File Name</span>
          <span className="text-sm font-bold text-slate-800 truncate block" title={fileName}>
            {fileName}
          </span>
        </div>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-xs text-slate-500 font-medium block mb-1">Total Spreadsheet Rows</span>
          <span className="text-lg font-bold text-indigo-600">{totalRows}</span>
        </div>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-xs text-slate-500 font-medium block mb-1">Mapped Columns</span>
          <span className="text-lg font-bold text-emerald-600">
            {mappedCount} <span className="text-xs text-slate-400 font-normal">/ {detectedColumns.length}</span>
          </span>
        </div>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-xs text-slate-500 font-medium block mb-1">Target Mode</span>
          <span className="text-sm font-bold text-purple-600">{importType}</span>
        </div>
      </div>

      {/* Warnings alert if any */}
      {validationWarnings && validationWarnings.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-1">
          <div className="flex items-center gap-2 text-amber-800 text-xs font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-600" /> Validation Warnings & Notes:
          </div>
          <ul className="text-xs text-amber-700 list-disc list-inside space-y-0.5">
            {validationWarnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Sample Rows Table Preview */}
      <div className="glass-card rounded-xl overflow-hidden shadow-xs">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
            Sample Data Preview (First {sampleRows.length} Rows)
          </h4>
          <span className="text-xs text-slate-500">Review before database ingestion</span>
        </div>

        <div className="overflow-x-auto max-h-[380px]">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-50/95 backdrop-blur z-10 border-b border-slate-200 text-slate-500 font-semibold">
              <tr>
                <th className="p-3 w-12 text-slate-400">#</th>
                {detectedColumns.map((col) => {
                  const targetKey = Object.keys(mappings).find((k) => mappings[k] === col);
                  return (
                    <th key={col} className="p-3 whitespace-nowrap min-w-[120px]">
                      <div className="text-slate-700">{col}</div>
                      {targetKey && (
                        <div className="text-[10px] text-indigo-600 font-medium mt-0.5">
                          → {targetKey}
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {sampleRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3 text-slate-400">{idx + 1}</td>
                  {detectedColumns.map((col) => (
                    <td key={col} className="p-3 text-slate-700 truncate max-w-[200px]" title={String(row[col] ?? '')}>
                      {String(row[col] ?? '') || <span className="text-slate-300">-</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onCancel} disabled={isImporting}>
            Cancel
          </Button>
          <Button variant="secondary" size="sm" onClick={onBackToMapping} disabled={isImporting}>
            Adjust Column Mapping
          </Button>
        </div>

        <Button
          size="md"
          variant="primary"
          isLoading={isImporting}
          icon={<CheckCircle2 className="w-4 h-4" />}
          onClick={onConfirmImport}
        >
          Confirm & Ingest into PostgreSQL
        </Button>
      </div>
    </div>
  );
};
