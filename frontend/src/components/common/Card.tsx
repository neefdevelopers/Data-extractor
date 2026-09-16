import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  interactive = false,
  onClick
}) => {
  return (
    <div
      onClick={onClick}
      className={`rounded-xl ${
        interactive ? 'glass-card-interactive cursor-pointer' : 'glass-card'
      } p-5 ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-800">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex items-center space-x-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
