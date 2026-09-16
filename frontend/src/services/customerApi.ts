import { apiClient } from './api';
import { Customer, CustomerDetail, Order, PaginatedResponse } from '../types';

export const customerApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
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
  }): Promise<PaginatedResponse<Customer>> => {
    const res = await apiClient.get<PaginatedResponse<Customer>>('/customers', { params });
    return res.data;
  },

  getById: async (id: number): Promise<CustomerDetail> => {
    const res = await apiClient.get<CustomerDetail>(`/customers/${id}`);
    return res.data;
  },

  getOrders: async (id: number, page: number = 1, page_size: number = 20): Promise<PaginatedResponse<Order>> => {
    const res = await apiClient.get<PaginatedResponse<Order>>(`/customers/${id}/orders`, {
      params: { page, page_size }
    });
    return res.data;
  }
};
