import { http } from '../../lib/api/http';

type AdminStatsResponse = {
  total_users?: number;
  total_listings?: number;
  total_companies?: number;
  pending_verifications?: number;
};

type AdminUsersResponse = {
  data?: any[];
};

export const adminApi = {
  getStats: async () => http.get<AdminStatsResponse>('/api/v1/admin/stats'),
  getUsers: async (_params?: Record<string, any>) => http.get<AdminUsersResponse>('/api/v1/admin/users'),

  listAudit: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/admin', { ...params }),
};
