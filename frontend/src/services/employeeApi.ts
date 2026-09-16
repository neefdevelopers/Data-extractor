import { apiClient } from './api';
import { Employee, PaginatedResponse } from '../types';

export const employeeApi = {
  list: async (params: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse<Employee>> => {
    const res = await apiClient.get<PaginatedResponse<Employee>>('/employees', { params });
    return res.data;
  }
};
