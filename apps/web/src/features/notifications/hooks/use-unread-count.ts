import { useQuery } from '@tanstack/react-query';
import { notificationsApi } from '../api';

export const useUnreadNotifications = () => {
  return useQuery({
    queryKey: ['notifications-unread'],
    queryFn: () => notificationsApi.unreadCount(),
    refetchInterval: 10000,
  });
};
