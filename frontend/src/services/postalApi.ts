import { apiClient } from './api';
import { PostalMaster, PostalOffice } from '../types';

export const postalApi = {
  getByPincode: async (pincode: string): Promise<PostalMaster> => {
    const res = await apiClient.get<PostalMaster>(`/postal/pincode/${pincode}`);
    return res.data;
  },

  searchOffices: async (query: string): Promise<PostalOffice[]> => {
    const res = await apiClient.get<PostalOffice[]>('/postal/search-offices', {
      params: { q: query }
    });
    return res.data;
  }
};
