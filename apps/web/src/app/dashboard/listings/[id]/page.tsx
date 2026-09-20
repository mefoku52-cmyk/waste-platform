'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { config } from '../../../../lib/config';
import { RecommendationsPanel } from '../../../../features/recommendations/components/recommendations-panel';

type ListingData = {
  id: string;
  title: string;
  materialType: string;
  quantity: number;
  unit: string;
  location: string;
  status: string;
  description?: string | null;
};

async function fetchListing(listingId: string): Promise<ListingData> {
  const token = localStorage.getItem('accessToken');
  const base = config.apiBaseUrl;
  const url = base + '/listings/' + listingId;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : 'Listing request failed';
    throw new Error(detail);
  }
  return (body.data ?? body) as ListingData;
}

export default function ListingDetailPage() {
  const params = useParams<{ id: string }>();
  const listingId = params?.id;

  const { data, isLoading, error } = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => fetchListing(listingId as string),
    enabled: !!listingId,
    retry: 1,
  });

  if (!listingId) {
    return <p className="p-6 text-slate-300">Chýba ID ponuky.</p>;
  }

  return (
    <main className="mx-auto w-full max-w-3xl p-6">
      <h1 className="text-2xl font-bold text-white">{data?.title || 'Ponuka'}</h1>
      <p className="mt-1 text-sm text-slate-400">{listingId}</p>

      {isLoading && <p className="mt-4 text-sm text-slate-300">Načítavam ponuku…</p>}
      {error && <p className="mt-4 text-sm text-red-200">{(error as Error).message}</p>}

      {data && (
        <div className="mt-4 rounded-2xl border border-slate-700/80 bg-slate-950/95 p-6 text-sm text-slate-200">
          <p>Materiál: {data.materialType}</p>
          <p>Množstvo: {data.quantity} {data.unit}</p>
          <p>Lokalita: {data.location}</p>
          <p>Stav: {data.status}</p>
          {data.description ? <p className="mt-2 text-slate-400">{data.description}</p> : null}
        </div>
      )}

      <RecommendationsPanel listingId={listingId} />
    </main>
  );
}
