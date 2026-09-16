import React, { useEffect, useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Layers,
  History,
  AlertTriangle,
  CheckCircle2,
  Eye,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { Pagination } from '../components/common/Pagination';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { FileUploader } from '../components/upload/FileUploader';
import { ColumnMapper } from '../components/upload/ColumnMapper';
import { ImportPreview } from '../components/upload/ImportPreview';
import { BatchStatusBadge } from '../components/upload/BatchStatusBadge';
import { uploadApi } from '../services/uploadApi';
import { FileAnalysisResponse, UploadBatch } from '../types';
import { formatDate, formatDateTime, formatNumber } from '../utils/formatters';

export const Uploads: React.FC = () => {
  // Wizard steps: 'upload' -> 'mapping' -> 'preview'
  const [currentStep, setCurrentStep] = useState<'upload' | 'mapping' | 'preview'>('upload');
  const [analysisResult, setAnalysisResult] = useState<FileAnalysisResponse | null>(null);
  const [importType, setImportType] = useState<string>('COMBINED');
  const [mappings, setMappings] = useState<Record<string, string | null>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Batch History
  const [batches, setBatches] = useState<UploadBatch[]>([]);
  const [batchPage, setBatchPage] = useState(1);
  const [totalBatches, setTotalBatches] = useState(0);
  const [totalBatchPages, setTotalBatchPages] = useState(1);
  const [loadingBatches, setLoadingBatches] = useState(false);

  // Selected batch for details / error rows inspection
  const [selectedBatch, setSelectedBatch] = useState<UploadBatch | null>(null);

  const fetchBatches = async () => {
    setLoadingBatches(true);
    try {
      const data = await uploadApi.listBatches(batchPage, 10);
      setBatches(data.items);
      setTotalBatches(data.total);
      setTotalBatchPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load upload batches:', err);
    } finally {
      setLoadingBatches(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, [batchPage]);

  const handleFileAnalyzed = (analysis: FileAnalysisResponse) => {
    setAnalysisResult(analysis);
    setImportType(analysis.suggested_import_type);
    setMappings(analysis.auto_mappings);
    setCurrentStep('mapping');
  };

  const handleMappingChange = (field: string, sourceCol: string | null) => {
    setMappings((prev) => ({ ...prev, [field]: sourceCol }));
  };

  const handleConfirmImport = async () => {
    if (!analysisResult) return;
    setIsProcessing(true);
    try {
      const batch = await uploadApi.confirmImport({
        temp_file_id: analysisResult.temp_file_id,
        file_name: analysisResult.file_name,
        import_type: importType,
        column_mapping: mappings,
      });

      setSuccessMessage(
        `Import completed! Successfully processed ${batch.successful_rows} rows (${batch.new_customers} new customers, ${batch.new_orders} new orders).`
      );
      // Reset wizard
      setCurrentStep('upload');
      setAnalysisResult(null);
      fetchBatches();
    } catch (err: any) {
      alert('Import execution error: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const openBatchDetails = async (batchId: number) => {
    try {
      const details = await uploadApi.getBatchDetails(batchId);
      setSelectedBatch(details);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <Header
        title="Spreadsheet Import Engine"
        subtitle="Intelligent Excel & CSV ingestion with column detection, postal enrichment, and duplicate prevention"
      />

      <div className="p-8 max-w-7xl mx-auto space-y-8">
        {/* Success Alert */}
        {successMessage && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs text-emerald-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-emerald-400 hover:text-emerald-200 font-bold ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Wizard Container */}
        <div className="glass-card p-6 rounded-2xl space-y-6 shadow-xs">
          {/* Step Progress Indicators */}
          <div className="flex items-center justify-center space-x-8 text-xs font-semibold border-b border-slate-100 pb-4">
            <div className={`flex items-center gap-2 ${currentStep === 'upload' ? 'text-indigo-600' : 'text-slate-400'}`}>
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${currentStep === 'upload' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                1
              </span>
              <span>Upload Spreadsheet</span>
            </div>

            <div className={`flex items-center gap-2 ${currentStep === 'mapping' ? 'text-indigo-600' : 'text-slate-400'}`}>
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${currentStep === 'mapping' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                2
              </span>
              <span>Column Mapping</span>
            </div>

            <div className={`flex items-center gap-2 ${currentStep === 'preview' ? 'text-indigo-600' : 'text-slate-400'}`}>
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${currentStep === 'preview' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
                3
              </span>
              <span>Preview & Confirm</span>
            </div>
          </div>

          {/* Step 1: Upload */}
          {currentStep === 'upload' && (
            <FileUploader
              onFileAnalyzed={handleFileAnalyzed}
              isLoading={isProcessing}
              setIsLoading={setIsProcessing}
            />
          )}

          {/* Step 2: Mapping */}
          {currentStep === 'mapping' && analysisResult && (
            <ColumnMapper
              detectedColumns={analysisResult.detected_columns}
              mappings={mappings}
              importType={importType}
              onMappingChange={handleMappingChange}
              onImportTypeChange={setImportType}
              onProceedToPreview={() => setCurrentStep('preview')}
              onCancel={() => {
                setCurrentStep('upload');
                setAnalysisResult(null);
              }}
            />
          )}

          {/* Step 3: Preview */}
          {currentStep === 'preview' && analysisResult && (
            <ImportPreview
              fileName={analysisResult.file_name}
              importType={importType}
              totalRows={analysisResult.total_rows}
              detectedColumns={analysisResult.detected_columns}
              mappings={mappings}
              sampleRows={analysisResult.sample_rows}
              validationWarnings={analysisResult.validation_warnings}
              isImporting={isProcessing}
              onConfirmImport={handleConfirmImport}
              onBackToMapping={() => setCurrentStep('mapping')}
              onCancel={() => {
                setCurrentStep('upload');
                setAnalysisResult(null);
              }}
            />
          )}
        </div>

        {/* Upload History Table */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              Upload Batch History ({totalBatches})
            </h3>
            <button
              onClick={fetchBatches}
              className="p-1 rounded bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200 transition-colors border border-slate-200"
              title="Refresh History"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {loadingBatches ? (
            <div className="p-6">
              <LoadingSkeleton rows={5} />
            </div>
          ) : batches.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No previous upload batches recorded yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3.5 pl-6">Batch ID</th>
                    <th className="p-3.5">File Name</th>
                    <th className="p-3.5">Uploaded Date</th>
                    <th className="p-3.5 text-center">Total Rows</th>
                    <th className="p-3.5 text-center">Successful</th>
                    <th className="p-3.5 text-center">Failed</th>
                    <th className="p-3.5 text-center">Duplicates</th>
                    <th className="p-3.5 text-center">Status</th>
                    <th className="p-3.5 text-right pr-6">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {batches.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 pl-6 font-bold text-indigo-600">#{b.id}</td>
                      <td className="p-3.5 font-sans font-medium text-slate-800 truncate max-w-[200px]" title={b.file_name}>
                        {b.file_name}
                      </td>
                      <td className="p-3.5 text-slate-500">{formatDateTime(b.uploaded_date)}</td>
                      <td className="p-3.5 text-center text-slate-800 font-bold">{b.total_rows}</td>
                      <td className="p-3.5 text-center text-emerald-600 font-bold">{b.successful_rows}</td>
                      <td className="p-3.5 text-center text-rose-600 font-bold">{b.failed_rows}</td>
                      <td className="p-3.5 text-center text-amber-600">{b.duplicate_rows}</td>
                      <td className="p-3.5 text-center font-sans">
                        <BatchStatusBadge status={b.status} />
                      </td>
                      <td className="p-3.5 text-right pr-6 font-sans">
                        <button
                          onClick={() => openBatchDetails(b.id)}
                          className="px-2.5 py-1 text-xs rounded bg-white hover:bg-slate-50 text-indigo-600 font-medium transition-colors border border-slate-300 shadow-2xs"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <Pagination
            currentPage={batchPage}
            totalPages={totalBatchPages}
            totalItems={totalBatches}
            pageSize={10}
            onPageChange={setBatchPage}
          />
        </div>
      </div>

      {/* Batch Details & Failed Rows Inspection Modal */}
      {selectedBatch && (
        <Modal
          isOpen={Boolean(selectedBatch)}
          onClose={() => setSelectedBatch(null)}
          maxWidth="4xl"
          title={`Upload Batch #${selectedBatch.id} - ${selectedBatch.file_name}`}
        >
          <div className="space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-500 font-medium block mb-1">Status</span>
                <BatchStatusBadge status={selectedBatch.status} />
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-500 font-medium block mb-1">New Customers</span>
                <span className="text-sm font-bold text-indigo-600">{selectedBatch.new_customers}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-500 font-medium block mb-1">New Orders</span>
                <span className="text-sm font-bold text-cyan-600">{selectedBatch.new_orders}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                <span className="text-slate-500 font-medium block mb-1">New Products</span>
                <span className="text-sm font-bold text-emerald-600">{selectedBatch.new_products}</span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Failed Row Errors ({selectedBatch.failed_row_items?.length || 0})
              </h4>
              {selectedBatch.failed_row_items && selectedBatch.failed_row_items.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {selectedBatch.failed_row_items.map((row) => (
                    <div
                      key={row.id}
                      className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between text-rose-700 font-bold">
                        <span>Row #{row.row_number}</span>
                        <span>Reason: {row.error_reason}</span>
                      </div>
                      {row.suggested_fix && (
                        <div className="text-slate-600 text-[11px]">
                          <strong>Fix:</strong> {row.suggested_fix}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500">No failed rows recorded for this batch.</p>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
