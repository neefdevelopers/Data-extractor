import { apiClient } from './api';
import {
  BusinessDashboardKPIs,
  DistrictAnalyticsItem,
  PincodeAnalyticsItem,
  GlobalFilterState
} from '../types';

export const analyticsApi = {
  getDashboardKPIs: async (filters?: GlobalFilterState): Promise<BusinessDashboardKPIs> => {
    const params: Record<string, any> = {};
    if (filters) {
      if (filters.preset) params.preset = filters.preset;
      if (filters.startDate) params.start_date = filters.startDate;
      if (filters.endDate) params.end_date = filters.endDate;
      if (filters.employeeId) params.employee_id = filters.employeeId;
      if (filters.paymentMode) params.payment_mode = filters.paymentMode;
      if (filters.productId) params.product_id = filters.productId;
      if (filters.district) params.district = filters.district;
      if (filters.pincode) params.pincode = filters.pincode;
      if (filters.rfmSegment) params.rfm_segment = filters.rfmSegment;
      if (filters.orderStatus) params.order_status = filters.orderStatus;
      if (filters.search) params.search = filters.search;
      if (filters.customerId) params.customer_id = filters.customerId;
    }
    const res = await apiClient.get<BusinessDashboardKPIs>('/analytics/dashboard', { params });
    return res.data;
  },

  getDistricts: async (search?: string): Promise<DistrictAnalyticsItem[]> => {
    const res = await apiClient.get<DistrictAnalyticsItem[]>('/analytics/districts', {
      params: { search }
    });
    return res.data;
  },

  getPincodes: async (district?: string, search?: string): Promise<PincodeAnalyticsItem[]> => {
    const res = await apiClient.get<PincodeAnalyticsItem[]>('/analytics/pincodes', {
      params: { district, search }
    });
    return res.data;
  }
};
