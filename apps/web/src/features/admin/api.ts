import { http } from '../../lib/api/http';
import type {
  AdminCompaniesResponse,
  AdminCompanyDetailResponse,
  AdminStats,
  AdminUserActivityResponse,
  AdminUserSummaryResponse,
  AdminUsersResponse,
} from './types';

export const adminApi = {
  getStats: async () => http.get<AdminStats>('/admin/stats'),

  getUsers: async (_params?: Record<string, unknown>) =>
    http.get<AdminUsersResponse>('/admin/users'),

  listAudit: (params?: Record<string, unknown>) =>
    http.get<{ items: unknown[]; meta: Record<string, unknown> }>('/admin/all', { ...params }),

  listCompanies: (params?: { page?: number; pageSize?: number; status?: string; q?: string }) => {
    const qs = new URLSearchParams();
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    if (params?.status) qs.set('status', params.status);
    if (params?.q) qs.set('q', params.q);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return http.get<AdminCompaniesResponse>(`/admin/companies${suffix}`);
  },

  getCompany: (id: string) =>
    http.get<AdminCompanyDetailResponse>(`/admin/companies/${id}`),

  getUserSummary: async (id: string) =>
    http.get<AdminUserSummaryResponse>(`/admin/users/${id}/summary`),

  getUserActivity: async (id: string, limit = 100) =>
    http.get<AdminUserActivityResponse>(`/admin/users/${id}/activity?limit=${limit}`),

  deleteUser: async (id: string) => http.delete<void>(`/users/${id}`),
};
