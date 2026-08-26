import { http } from '../../lib/api/http';

export const documentsApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/documents', { ...params }),

  create: (data: {
    title: string;
    documentType: string;
    fileUrl: string;
    companyId: string;
    listingId?: string | null;
  }) => http.post<{ data: any }>('/documents', data),
};
