import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api';

export const useCompanies = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['companies', params],
    queryFn: () => companiesApi.getCompanies(params),
  });
};
