import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';

export const useAdminStats = () => {
  return useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
  });
};
