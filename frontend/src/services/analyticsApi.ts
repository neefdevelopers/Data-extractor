import { apiClient } from './api';
import {
  BusinessDashboardKPIs,
  DistrictAnalyticsItem,
  PincodeAnalyticsItem,
  PostOfficeAnalyticsItem,
  GeographicSummaryKPIs,
  GlobalFilterState
} from '../types';

export interface GeographicFilterParams extends Partial<GlobalFilterState> {
  districtId?: number;
  postOffice?: string;
  sortBy?: 'revenue' | 'orders';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
}

function buildFilterParams(filters?: GeographicFilterParams): Record<string, any> {
  const params: Record<string, any> = {};
  if (!filters) return params;

  if (filters.preset) params.preset = filters.preset;
  if (filters.startDate) params.start_date = filters.startDate;
  if (filters.endDate) params.end_date = filters.endDate;
  if (filters.employeeId) params.employee_id = filters.employeeId;
  if (filters.paymentMode) params.payment_mode = filters.paymentMode;
  if (filters.productId) params.product_id = filters.productId;
  if (filters.district) params.district = filters.district;
  if (filters.districtId) params.district_id = filters.districtId;
  if (filters.pincode) params.pincode = filters.pincode;
  if (filters.postOffice) params.post_office = filters.postOffice;
  if (filters.rfmSegment) params.rfm_segment = filters.rfmSegment;
  if (filters.orderStatus) params.order_status = filters.orderStatus;
  if (filters.search) params.search = filters.search;
  if (filters.customerId) params.customer_id = filters.customerId;
  if (filters.sortBy) params.sort_by = filters.sortBy;
  if (filters.sortOrder) params.sort_order = filters.sortOrder;
  if (filters.limit) params.limit = filters.limit;

  return params;
}

export const analyticsApi = {
  getDashboardKPIs: async (filters?: GlobalFilterState): Promise<BusinessDashboardKPIs> => {
    const params = buildFilterParams(filters);
    const res = await apiClient.get<BusinessDashboardKPIs>('/analytics/dashboard', { params });
    return res.data;
  },

  getGeographicOverview: async (filters?: GeographicFilterParams): Promise<GeographicSummaryKPIs> => {
    const params = buildFilterParams(filters);
    const res = await apiClient.get<GeographicSummaryKPIs>('/analytics/geographic/overview', { params });
    return res.data;
  },

  getGeographicDistricts: async (filters?: GeographicFilterParams): Promise<DistrictAnalyticsItem[]> => {
    const params = buildFilterParams(filters);
    const res = await apiClient.get<DistrictAnalyticsItem[]>('/analytics/geographic/district', { params });
    return res.data;
  },

  getGeographicPincodes: async (filters?: GeographicFilterParams): Promise<PincodeAnalyticsItem[]> => {
    const params = buildFilterParams(filters);
    const res = await apiClient.get<PincodeAnalyticsItem[]>('/analytics/geographic/pincode', { params });
    return res.data;
  },

  getGeographicPostOffices: async (filters?: GeographicFilterParams): Promise<PostOfficeAnalyticsItem[]> => {
    const params = buildFilterParams(filters);
    const res = await apiClient.get<PostOfficeAnalyticsItem[]>('/analytics/geographic/post-office', { params });
    return res.data;
  },

  getDistricts: async (filters?: GeographicFilterParams | string): Promise<DistrictAnalyticsItem[]> => {
    const params = typeof filters === 'string' ? { search: filters } : buildFilterParams(filters);
    const res = await apiClient.get<DistrictAnalyticsItem[]>('/analytics/districts', { params });
    return res.data;
  },

  getPincodes: async (district?: string, search?: string, filters?: GeographicFilterParams): Promise<PincodeAnalyticsItem[]> => {
    const params = buildFilterParams({ ...filters, district, search });
    const res = await apiClient.get<PincodeAnalyticsItem[]>('/analytics/pincodes', { params });
    return res.data;
  }
};

