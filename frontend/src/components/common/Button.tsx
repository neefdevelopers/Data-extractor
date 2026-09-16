import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'success' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses = {
    xs: 'px-2.5 py-1 text-xs',
    sm: 'px-3 py-1.5 text-xs font-medium',
    md: 'px-4 py-2 text-sm font-medium',
    lg: 'px-5 py-2.5 text-base font-semibold',
  };

  const variantClasses = {
    primary:
      'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm shadow-indigo-600/20 active:scale-[0.98]',
    secondary:
      'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-2xs active:scale-[0.98]',
    outline:
      'bg-transparent hover:bg-slate-100 text-slate-700 border border-slate-300 active:scale-[0.98]',
    danger:
      'bg-rose-600 hover:bg-rose-700 text-white shadow-sm shadow-rose-600/20 active:scale-[0.98]',
    success:
      'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20 active:scale-[0.98]',
    ghost:
      'bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-transparent',
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 disabled:pointer-events-none gap-2 ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : (
        icon && <span className="inline-flex shrink-0">{icon}</span>
      )}
      {children}
    </button>
  );
};
