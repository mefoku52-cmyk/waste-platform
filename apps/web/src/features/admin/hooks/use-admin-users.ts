import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';
import type { AdminUsersResponse } from '../types';

export const useAdminUsers = (params?: Record<string, unknown>) => {
  return useQuery<AdminUsersResponse>({
    queryKey: ['admin-users', params],
    queryFn: () => adminApi.getUsers(params),
  });
};
