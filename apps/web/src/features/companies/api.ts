import { http } from '../../lib/api/http';
import { PaginatedResponse } from '../../lib/types/common';
import { Company } from './types';
import { CompanyInput } from './schemas';

export const companiesApi = {
  getCompanies: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Company>>('/companies', { ...params }),

  getCompany: (id: string) =>
    http.get<Company>(`/companies/${id}`),

  createCompany: (data: CompanyInput) =>
    http.post<Company>('/companies', data),

  updateCompany: (id: string, data: Partial<CompanyInput>) =>
    http.patch<Company>(`/companies/${id}`, data),

  transitionStatus: (id: string, toStatus: string) =>
    http.patch<Company>(`/companies/${id}/status`, { toStatus }),

  setSubscriptionTier: (id: string, tier: 'free' | 'pro' | 'ai') =>
    http.patch<{ data: Company }>(`/companies/${id}/subscription-tier`, { tier }),

  rpoCheck: (ico: string) =>
    http.get<{
      ok: boolean;
      exists: boolean;
      ico: string | null;
      legalName: string | null;
      city: string | null;
      reason: string;
    }>(`/companies/rpo-check?ico=${encodeURIComponent(ico)}`),
};
