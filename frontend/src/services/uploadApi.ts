import { apiClient } from './api';
import { FileAnalysisResponse, UploadBatch, PaginatedResponse } from '../types';

export const uploadApi = {
  analyzeFile: async (file: File): Promise<FileAnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<FileAnalysisResponse>('/uploads/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
    return res.data;
  },

  confirmImport: async (payload: {
    temp_file_id: string;
    file_name: string;
    import_type: string;
    column_mapping: Record<string, string | null>;
    update_existing?: boolean;
  }): Promise<UploadBatch> => {
    const res = await apiClient.post<UploadBatch>('/uploads/confirm', payload, {
      timeout: 600000, // 10 minutes timeout for large datasets
    });
    return res.data;
  },

  listBatches: async (page: number = 1, page_size: number = 20): Promise<PaginatedResponse<UploadBatch>> => {
    const res = await apiClient.get<PaginatedResponse<UploadBatch>>('/uploads', {
      params: { page, page_size }
    });
    return res.data;
  },

  getBatchDetails: async (batchId: number): Promise<UploadBatch> => {
    const res = await apiClient.get<UploadBatch>(`/uploads/${batchId}`);
    return res.data;
  },

  generateSampleData: async (): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.post<{ success: boolean; message: string }>('/uploads/generate-sample', null, {
      timeout: 300000,
    });
    return res.data;
  }
};
