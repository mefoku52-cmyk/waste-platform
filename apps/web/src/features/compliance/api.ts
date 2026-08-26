import { http } from '../../lib/api/http';

export const complianceApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/compliance', { ...params }),

  create: (data: {
    companyId: string;
    regulationType: string;
    documentRef?: string | null;
    notes?: string | null;
  }) => http.post<{ data: any }>('/compliance', data),
};
