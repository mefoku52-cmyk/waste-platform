import { useQuery } from '@tanstack/react-query';

import { adminApi } from '../api';

export const useAdminCompanies = (params: {
  page?: number;
  pageSize?: number;
  status?: string;
  q?: string;
}) =>
  useQuery({
    queryKey: ['admin-companies', params],
    queryFn: () => adminApi.listCompanies(params),
  });

export const useAdminCompany = (id: string | undefined) =>
  useQuery({
    queryKey: ['admin-company', id],
    queryFn: () => adminApi.getCompany(id!),
    enabled: Boolean(id),
  });
