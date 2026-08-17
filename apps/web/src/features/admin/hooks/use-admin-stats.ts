import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';

type AdminStats = {
  total_users?: number;
  total_listings?: number;
  total_companies?: number;
  pending_verifications?: number;
};

export const useAdminStats = () => {
  return useQuery<AdminStats>({
    queryKey: ['admin-stats'],
    queryFn: () => adminApi.getStats(),
  });
};
