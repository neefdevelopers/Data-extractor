import { apiClient } from './api';
import { SystemSettings } from '../types';

export const settingsApi = {
  getSettings: async (): Promise<SystemSettings> => {
    const res = await apiClient.get<SystemSettings>('/settings');
    return res.data;
  },

  updateRevenueRules: async (rules: SystemSettings['revenue_rules']): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.put<{ success: boolean; message: string }>('/settings/revenue-rules', rules);
    return res.data;
  }
};
