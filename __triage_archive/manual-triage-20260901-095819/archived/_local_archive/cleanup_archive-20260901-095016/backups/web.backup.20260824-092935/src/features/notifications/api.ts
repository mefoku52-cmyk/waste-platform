import { http } from '../../lib/api/http';

export const notificationsApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/api/v1/notifications', { ...params }),
};
