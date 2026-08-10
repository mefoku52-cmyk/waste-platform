import { http } from '../../lib/api/http';
import { PaginatedResponse } from '../../lib/types/common';
import { Company } from './types';
import { CompanyInput } from './schemas';

export const companiesApi = {
  getCompanies: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Company>>('/api/v1/companies', { ...params }),

  getCompany: (id: string) =>
    http.get<Company>(`/api/v1/companies/${id}`),

  createCompany: (data: CompanyInput) =>
    http.post<Company>('/api/v1/companies', data),

  updateCompany: (id: string, data: Partial<CompanyInput>) =>
    http.patch<Company>(`/api/v1/companies/${id}`, data),

  verifyCompany: (id: string) =>
    http.post<Company>(`/api/v1/companies/${id}/verify`, {}),
};
