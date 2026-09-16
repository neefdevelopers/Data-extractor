import React from 'react';
import { AlertCircle, FolderSearch, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const EmptyState: React.FC<{
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}> = ({
  title = 'No records found',
  description = 'There are no records matching your current filter criteria.',
  icon,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="rounded-full bg-slate-100 p-4 text-slate-500 mb-3 border border-slate-200">
        {icon || <FolderSearch className="w-8 h-8" />}
      </div>
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="mt-1 text-sm text-slate-500 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

export const ErrorState: React.FC<{
  message?: string;
  onRetry?: () => void;
}> = ({ message = 'Failed to load data', onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center rounded-xl bg-rose-50 border border-rose-200">
      <AlertCircle className="w-8 h-8 text-rose-500 mb-2" />
      <h4 className="text-sm font-semibold text-rose-700">{message}</h4>
      {onRetry && (
        <Button
          size="sm"
          variant="secondary"
          icon={<RefreshCw className="w-3.5 h-3.5" />}
          onClick={onRetry}
          className="mt-3"
        >
          Try Again
        </Button>
      )}
    </div>
  );
};

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="space-y-3 animate-pulse py-2">
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="h-10 bg-slate-100 rounded-lg w-full" />
      ))}
    </div>
  );
};
