import { useQuery } from '@tanstack/react-query';
import { listingsApi } from '../api';

export const useListings = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['listings', params],
    queryFn: () => listingsApi.getListings(params),
  });
};
