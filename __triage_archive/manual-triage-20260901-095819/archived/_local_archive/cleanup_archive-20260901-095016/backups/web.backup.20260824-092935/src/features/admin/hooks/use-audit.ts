import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';

export const useAudit = () =>
  useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => adminApi.listAudit(),
  });
