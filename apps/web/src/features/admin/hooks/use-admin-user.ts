import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api';
import type {
  AdminUserActivityResponse,
  AdminUserSummaryResponse,
} from '../types';

export const useAdminUserSummary = (id: string | undefined) => {
  return useQuery<AdminUserSummaryResponse>({
    queryKey: ['admin-user-summary', id],
    queryFn: () => adminApi.getUserSummary(id as string),
    enabled: !!id,
  });
};

export const useAdminUserActivity = (id: string | undefined, limit = 100) => {
  return useQuery<AdminUserActivityResponse>({
    queryKey: ['admin-user-activity', id, limit],
    queryFn: () => adminApi.getUserActivity(id as string, limit),
    enabled: !!id,
  });
};

export const useAdminDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminApi.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
  });
};
