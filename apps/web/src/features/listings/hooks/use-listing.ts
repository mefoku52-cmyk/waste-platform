import { useQuery } from '@tanstack/react-query';
import { listingsApi } from '../api';

export const useListing = (id: string) => {
  return useQuery({
    queryKey: ['listing', id],
    queryFn: () => listingsApi.getListing(id),
    enabled: !!id,
  });
};
