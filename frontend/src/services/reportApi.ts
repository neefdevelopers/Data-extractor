import { apiClient } from './api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const reportApi = {
  downloadCustomers: (params?: {
    format?: 'xlsx' | 'csv';
    search?: string;
    district?: string;
    post_office?: string;
    pincode?: string;
    rfm_segment?: string;
    min_orders?: number;
    max_orders?: number;
    min_spend?: number;
    max_spend?: number;
    sort_by?: string;
    sort_order?: string;
  }) => {
    const q = new URLSearchParams();
    q.append('format', params?.format || 'xlsx');
    if (params?.search) q.append('search', params.search);
    if (params?.district) q.append('district', params.district);
    if (params?.post_office) q.append('post_office', params.post_office);
    if (params?.pincode) q.append('pincode', params.pincode);
    if (params?.rfm_segment) q.append('rfm_segment', params.rfm_segment);
    if (params?.min_orders !== undefined) q.append('min_orders', String(params.min_orders));
    if (params?.max_orders !== undefined) q.append('max_orders', String(params.max_orders));
    if (params?.min_spend !== undefined) q.append('min_spend', String(params.min_spend));
    if (params?.max_spend !== undefined) q.append('max_spend', String(params.max_spend));
    if (params?.sort_by) q.append('sort_by', params.sort_by);
    if (params?.sort_order) q.append('sort_order', params.sort_order);

    window.open(`${BASE_URL}/reports/customers?${q.toString()}`, '_blank');
  },

  downloadOrders: (format: 'xlsx' | 'csv' = 'xlsx', payment_mode?: string, order_status?: string, start_date?: string, end_date?: string) => {
    const params = new URLSearchParams();
    params.append('format', format);
    if (payment_mode) params.append('payment_mode', payment_mode);
    if (order_status) params.append('order_status', order_status);
    if (start_date) params.append('start_date', start_date);
    if (end_date) params.append('end_date', end_date);
    window.open(`${BASE_URL}/reports/orders?${params.toString()}`, '_blank');
  },

  downloadRfm: (format: 'xlsx' | 'csv' = 'xlsx') => {
    window.open(`${BASE_URL}/reports/rfm?format=${format}`, '_blank');
  },

  downloadGeographic: (format: 'xlsx' | 'csv' = 'xlsx', filters?: Record<string, any>) => {
    const params = new URLSearchParams();
    params.append('format', format);
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          params.append(k, String(v));
        }
      });
    }
    window.open(`${BASE_URL}/reports/geographic?${params.toString()}`, '_blank');
  },

  downloadPincodes: (format: 'xlsx' | 'csv' = 'xlsx', filters?: Record<string, any>) => {
    const params = new URLSearchParams();
    params.append('format', format);
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          params.append(k, String(v));
        }
      });
    }
    window.open(`${BASE_URL}/reports/pincodes?${params.toString()}`, '_blank');
  },

  downloadPostOffices: (format: 'xlsx' | 'csv' = 'xlsx', filters?: Record<string, any>) => {
    const params = new URLSearchParams();
    params.append('format', format);
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          params.append(k, String(v));
        }
      });
    }
    window.open(`${BASE_URL}/reports/post-offices?${params.toString()}`, '_blank');
  },

  downloadProducts: (format: 'xlsx' | 'csv' = 'xlsx') => {
    window.open(`${BASE_URL}/reports/products?format=${format}`, '_blank');
  },

  downloadEmployees: (format: 'xlsx' | 'csv' = 'xlsx') => {
    window.open(`${BASE_URL}/reports/employees?format=${format}`, '_blank');
  },
};
