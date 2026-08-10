import { useQuery } from '@tanstack/react-query';
import { listingsApi } from '../api';

export const useMarketplace = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['listings', 'marketplace', params],
    queryFn: () => listingsApi.getMarketplace(params),
  });
};
