import { http } from '../../lib/api/http';
import type { AdminStats, AdminUsersResponse } from './types';

export const adminApi = {
  getStats: async () => http.get<AdminStats>('/admin/stats'),

  getUsers: async (_params?: Record<string, unknown>) =>
    http.get<AdminUsersResponse>('/admin/users'),

  listAudit: (params?: Record<string, unknown>) =>
    http.get<{ items: unknown[]; meta: Record<string, unknown> }>('/admin', { ...params }),
};
