import React from 'react';
import { FolderSearch } from 'lucide-react';

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
        {icon || <FolderSearch className="w-8 h-8 text-slate-400" />}
      </div>
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <p className="mt-1 text-sm text-slate-500 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
