import { useQuery } from '@tanstack/react-query';
import { listingsApi } from '../api';

export const useMatches = (materialType: string | undefined) =>
  useQuery({
    queryKey: ['listings', 'matches', materialType],
    queryFn: () => listingsApi.getMatches(materialType!),
    enabled: !!materialType && materialType.length > 0,
  });
