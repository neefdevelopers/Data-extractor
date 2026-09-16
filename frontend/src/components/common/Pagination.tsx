import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}) => {
  if (totalPages <= 1) return null;

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="flex items-center justify-between px-6 py-3 bg-slate-50/70 border-t border-slate-200 text-xs text-slate-500">
      <div>
        Showing <span className="font-semibold text-slate-800">{startItem}</span> to{' '}
        <span className="font-semibold text-slate-800">{endItem}</span> of{' '}
        <span className="font-semibold text-slate-800">{totalItems.toLocaleString('en-IN')}</span> results
      </div>
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="inline-flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none transition-colors border border-slate-300 shadow-2xs"
        >
          <ChevronLeft className="w-3.5 h-3.5" /> Previous
        </button>
        <span className="px-2 font-semibold text-slate-700">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="inline-flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none transition-colors border border-slate-300 shadow-2xs"
        >
          Next <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
