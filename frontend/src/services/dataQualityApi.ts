import { apiClient } from './api';
import { DataQualityIssue, DataQualitySummary, PaginatedResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const dataQualityApi = {
  getSummary: async (): Promise<DataQualitySummary> => {
    const res = await apiClient.get<DataQualitySummary>('/data-quality/summary');
    return res.data;
  },

  listIssues: async (params: {
    page?: number;
    page_size?: number;
    issue_type?: string;
    entity_type?: string;
    is_resolved?: boolean;
    batch_id?: number;
  }): Promise<PaginatedResponse<DataQualityIssue>> => {
    const res = await apiClient.get<PaginatedResponse<DataQualityIssue>>('/data-quality/issues', { params });
    return res.data;
  },

  resolveIssue: async (issueId: number): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.post<{ success: boolean; message: string }>(`/data-quality/issues/${issueId}/resolve`);
    return res.data;
  },

  downloadIssuesCsv: () => {
    window.open(`${BASE_URL}/data-quality/export`, '_blank');
  }
};
