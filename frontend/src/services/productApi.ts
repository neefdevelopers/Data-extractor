import { apiClient } from './api';
import { Product, PaginatedResponse } from '../types';

export const productApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    search?: string;
    category?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<Product>> => {
    const res = await apiClient.get<PaginatedResponse<Product>>('/products', { params });
    return res.data;
  }
};
