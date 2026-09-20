'use client';

import { useQuery } from '@tanstack/react-query';
import { getListingRecommendations } from '../api';

export function useRecommendations(listingId: string | undefined) {
  return useQuery({
    queryKey: ['recommendations', listingId],
    queryFn: () => getListingRecommendations(listingId as string),
    enabled: !!listingId,
    retry: 1,
  });
}
