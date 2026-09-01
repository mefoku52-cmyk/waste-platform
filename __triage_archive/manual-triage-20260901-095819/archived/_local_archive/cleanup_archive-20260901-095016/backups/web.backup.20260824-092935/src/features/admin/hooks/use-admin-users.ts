import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';

export const useAdminUsers = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['admin-users', params],
    queryFn: () => adminApi.getUsers(params),
  });
};
