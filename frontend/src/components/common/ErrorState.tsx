import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const ErrorState: React.FC<{
  message?: string;
  onRetry?: () => void;
}> = ({ message = 'Failed to load data', onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center rounded-xl bg-rose-500/5 border border-rose-500/20">
      <AlertCircle className="w-8 h-8 text-rose-400 mb-2" />
      <h4 className="text-sm font-semibold text-rose-300">{message}</h4>
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
