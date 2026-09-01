import { useQuery } from '@tanstack/react-query';
import { complianceApi } from '../api';

export const useCompliance = () =>
  useQuery({
    queryKey: ['compliance'],
    queryFn: () => complianceApi.list(),
  });
