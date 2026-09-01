import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api';

export const useCompany = (id: string) => {
  return useQuery({
    queryKey: ['company', id],
    queryFn: () => companiesApi.getCompany(id),
    enabled: !!id,
  });
};
