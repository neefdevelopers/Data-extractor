import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Customer } from '../../types';

interface CopyCustomerButtonProps {
  customer: Customer;
  className?: string;
  size?: 'xs' | 'sm' | 'md';
}

export const CopyCustomerButton: React.FC<CopyCustomerButtonProps> = ({
  customer,
  className = '',
  size = 'sm',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const lines = [
      'CUSTOMER DETAILS',
      '----------------------------',
      `Name: ${customer.customer_name || ''}`,
      `Phone: ${customer.contact_number || customer.normalized_contact || ''}`,
      `Address: ${customer.full_address || ''}`,
      `Post Office: ${customer.post_office || ''}`,
      `District: ${customer.district || ''}`,
      `State: ${customer.state || ''}`,
      `PIN Code: ${customer.pincode || ''}`,
      '',
      'CUSTOMER METRICS',
      '----------------------------',
      `Total Orders: ${customer.total_orders ?? 0}`,
      `Total Spend: ₹${Number(customer.total_spend || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      `Average Order Value: ₹${Number(customer.average_order_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
      `RFM Segment: ${customer.rfm_segment || 'N/A'}`,
      `RFM Score: ${customer.rfm_score || 'N/A'}`,
      `First Order: ${customer.first_order_date ? new Date(customer.first_order_date).toLocaleDateString('en-IN') : 'N/A'}`,
      `Last Order: ${customer.last_order_date ? new Date(customer.last_order_date).toLocaleDateString('en-IN') : 'N/A'}`,
    ];

    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const sizeStyles = {
    xs: 'px-2 py-0.5 text-xs',
    sm: 'px-2.5 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  return (
    <button
      onClick={handleCopy}
      title="Copy address details to clipboard"
      className={`inline-flex items-center gap-1.5 rounded-lg font-medium transition-all ${
        copied
          ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 shadow-2xs'
          : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-2xs'
      } ${sizeStyles[size]} ${className}`}
    >
      {copied ? (
        <>
          <Check className="w-3.5 h-3.5 text-emerald-400" />
          <span>Copied!</span>
        </>
      ) : (
        <>
          <Copy className="w-3.5 h-3.5 text-slate-400" />
          <span>Copy Details</span>
        </>
      )}
    </button>
  );
};
