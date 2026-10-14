import { http } from '../../lib/api/http';

export const notificationsApi = {
  list: (params?: Record<string, any>) =>
    http.get<{ items: any[]; meta: any }>('/notifications', { ...params }),

  unreadCount: () =>
    http.get<{ unread: number }>('/notifications/unread-count'),

  markRead: (id: string) =>
    http.post(`/notifications/${encodeURIComponent(id)}/mark-read`),
};
