import { apiClient } from './api';
import {
  UnknownLocationSummary,
  UnknownLocationRecord,
  LocationCorrectionRequest,
  BulkLocationCorrectionRequest,
  LocationAuditLog,
  PaginatedResponse,
  Customer
} from '../types';

export const locationApi = {
  getSummary: async (): Promise<UnknownLocationSummary> => {
    const res = await apiClient.get<UnknownLocationSummary>('/locations/unknown-summary');
    return res.data;
  },

  getUnknownRecords: async (params: {
    filter_type?: 'all' | 'unknown_pincode' | 'unknown_district' | 'both';
    search?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<UnknownLocationRecord>> => {
    const res = await apiClient.get<PaginatedResponse<UnknownLocationRecord>>('/locations/unknown-records', { params });
    return res.data;
  },

  correctLocation: async (customerId: number, payload: LocationCorrectionRequest): Promise<Customer> => {
    const res = await apiClient.put<Customer>(`/locations/correct/${customerId}`, payload);
    return res.data;
  },

  bulkCorrectLocations: async (payload: BulkLocationCorrectionRequest): Promise<{ updated_count: number; message: string }> => {
    const res = await apiClient.post<{ updated_count: number; message: string }>('/locations/bulk-correct', payload);
    return res.data;
  },

  getAuditHistory: async (params?: {
    customer_id?: number;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<LocationAuditLog>> => {
    const res = await apiClient.get<PaginatedResponse<LocationAuditLog>>('/locations/audit-history', { params });
    return res.data;
  }
};
