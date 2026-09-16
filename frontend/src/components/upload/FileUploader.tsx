import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '../common/Button';
import { uploadApi } from '../../services/uploadApi';

interface FileUploaderProps {
  onFileAnalyzed: (analysis: any) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileAnalyzed,
  isLoading,
  setIsLoading,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleProcessFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['xlsx', 'xls', 'csv'].includes(ext || '')) {
      setError('Invalid file format. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.');
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      const result = await uploadApi.analyzeFile(file);
      onFileAnalyzed(result);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze uploaded file.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleGenerateSample = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await uploadApi.generateSampleData();
      alert('Sample Indian eCommerce dataset created in uploads/ folder! You can find sample_indian_ecom_data.xlsx in your uploads directory.');
    } catch (err: any) {
      setError(err.message || 'Failed to generate sample data.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
          isDragOver
            ? 'border-indigo-500 bg-indigo-50/70 scale-[1.01]'
            : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50/80 shadow-xs'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleProcessFile(e.target.files[0]);
            }
          }}
        />

        <div className="mx-auto w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 border border-indigo-100">
          <UploadCloud className="w-7 h-7" />
        </div>

        <h3 className="text-base font-bold text-slate-900">
          {isLoading ? 'Analyzing spreadsheet structure...' : 'Drag & drop Excel or CSV file here'}
        </h3>
        <p className="text-xs text-slate-500 mt-1.5 max-w-sm mx-auto leading-relaxed">
          Supports <span className="text-indigo-600 font-semibold">.xlsx</span>,{' '}
          <span className="text-indigo-600 font-semibold">.xls</span>, and{' '}
          <span className="text-indigo-600 font-semibold">.csv</span> with automatic column detection and Indian postal enrichment.
        </p>

        <div className="mt-5">
          <Button
            size="sm"
            variant="secondary"
            isLoading={isLoading}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse Local File
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Quick sample generator */}
      <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl border border-slate-200">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span className="text-xs text-slate-700 font-medium">
            Need test data? Generate synthetic Indian eCommerce dataset with real PINs & orders
          </span>
        </div>
        <Button
          size="xs"
          variant="outline"
          onClick={handleGenerateSample}
          disabled={isLoading}
        >
          Generate Test File
        </Button>
      </div>
    </div>
  );
};
