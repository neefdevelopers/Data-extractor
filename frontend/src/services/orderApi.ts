import { apiClient } from './api';
import { Order, PaginatedResponse } from '../types';

export const orderApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    customer_id?: number;
    employee_id?: number;
    product_id?: number;
    payment_mode?: string;
    order_status?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<Order>> => {
    const res = await apiClient.get<PaginatedResponse<Order>>('/orders', { params });
    return res.data;
  },

  getById: async (id: number): Promise<Order> => {
    const res = await apiClient.get<Order>(`/orders/${id}`);
    return res.data;
  }
};
