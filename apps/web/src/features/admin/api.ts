import { http } from '../../lib/api/http';

export const adminApi = {
  listAudit: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/admin/', { ...params }),
};
