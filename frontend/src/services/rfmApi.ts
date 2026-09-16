import { apiClient } from './api';
import { RFMDashboardData } from '../types';

export const rfmApi = {
  getDashboard: async (): Promise<RFMDashboardData> => {
    const res = await apiClient.get<RFMDashboardData>('/rfm/dashboard');
    return res.data;
  },

  recalculate: async (): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.post<{ success: boolean; message: string }>('/rfm/recalculate', null, {
      timeout: 300000,
    });
    return res.data;
  }
};
