import { http } from '../../lib/api/http';

export const documentsApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/documents', { ...params }),

  create: (data: {
    title: string;
    documentType: string;
    fileUrl: string;
    companyId: string;
    listingId?: string | null;
  }) => http.post<{ data: any }>('/api/v1/documents', data),
};
