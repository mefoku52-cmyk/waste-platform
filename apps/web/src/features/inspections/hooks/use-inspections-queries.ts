'use client';

import { useQuery } from '@tanstack/react-query';
import { http } from '@/lib/api/http';

export const useActiveInspection = (listingId?: string | null) =>
  useQuery({
    queryKey: ['inspection-active', listingId],
    queryFn: () => http.get<any>(listingId ? `/inspections?listingId=${encodeURIComponent(listingId)}` : '/inspections'),
    enabled: !!listingId,
    refetchInterval: 5000,
    retry: 1,
  });
