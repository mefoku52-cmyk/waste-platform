import { http } from '../../lib/api/http';
import type {
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

  getUserSummary: async (id: string) =>
    http.get<AdminUserSummaryResponse>(`/admin/users/${id}/summary`),

  getUserActivity: async (id: string, limit = 100) =>
    http.get<AdminUserActivityResponse>(`/admin/users/${id}/activity?limit=${limit}`),

  deleteUser: async (id: string) => http.delete<void>(`/users/${id}`),
};
