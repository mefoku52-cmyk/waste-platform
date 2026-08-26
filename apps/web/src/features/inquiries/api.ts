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
    http.post<{ data: any }>('/inquiries', data),

  getReceived: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/inquiries/received', { ...params }),

  getSent: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/inquiries/sent', { ...params }),

  updateStatus: (id: string, status: 'open' | 'answered' | 'closed') =>
    http.patch<{ data: any }>(`/inquiries/${id}/status`, { status }),
};
