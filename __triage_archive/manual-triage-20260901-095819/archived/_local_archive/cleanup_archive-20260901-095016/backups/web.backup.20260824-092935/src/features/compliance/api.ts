import { http } from '../../lib/api/http';

export const complianceApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/compliance', { ...params }),

  create: (data: {
    companyId: string;
    regulationType: string;
    documentRef?: string | null;
    notes?: string | null;
  }) => http.post<{ data: any }>('/api/v1/compliance', data),
};
