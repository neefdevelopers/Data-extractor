export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹0.00';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0';
  return new Intl.NumberFormat('en-IN').format(val);
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function getRfmSegmentBadgeColor(segment?: string): string {
  switch (segment) {
    case 'Champions':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'Loyal Customers':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'Potential Loyalists':
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    case 'New Customers':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'At Risk':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'Dormant Customers':
      return 'bg-orange-50 text-orange-700 border-orange-200';
    case 'Lost Customers':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
}

export function getStatusBadgeColor(status?: string): string {
  const st = (status || '').toUpperCase();
  if (st === 'DELIVERED' || st === 'COMPLETED' || st === 'SUCCESS') {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }
  if (st === 'CANCELLED' || st === 'FAILED') {
    return 'bg-rose-50 text-rose-700 border-rose-200';
  }
  if (st === 'RETURNED' || st === 'REFUNDED') {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  }
  if (st === 'PROCESSING' || st === 'PENDING') {
    return 'bg-sky-50 text-sky-700 border-sky-200';
  }
  if (st === 'PARTIALLY_COMPLETED') {
    return 'bg-orange-50 text-orange-700 border-orange-200';
  }
  return 'bg-slate-100 text-slate-700 border-slate-200';
}
