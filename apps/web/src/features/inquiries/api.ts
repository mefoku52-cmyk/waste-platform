import { http } from '../../lib/api/http';

export type InquiryCreateInput = {
  listingId: string;
  companyId: string;
  message: string;
  contactEmail: string;
  contactPhone?: string;
};

export const inquiriesApi = {
  create: (data: InquiryCreateInput) =>
    http.post<{ data: any }>('/api/v1/inquiries', data),

  getReceived: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/inquiries/received', { ...params }),

  getSent: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/inquiries/sent', { ...params }),

  updateStatus: (id: string, status: 'open' | 'answered' | 'closed') =>
    http.patch<{ data: any }>(`/api/v1/inquiries/${id}/status`, { status }),
};
