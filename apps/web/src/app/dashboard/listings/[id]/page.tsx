'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { config } from '../../../../lib/config';
import { RecommendationsPanel } from '../../../../features/recommendations/components/recommendations-panel';
import { TransportPanel } from '../../../../features/recommendations/components/transport-panel';
import { FreightPanel } from '../../../../features/recommendations/components/freight-panel';

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
  const res = await fetch(config.apiBaseUrl + '/listings/' + listingId, {
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
  const [destination, setDestination] = useState('');
  const { data, isLoading, error } = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => fetchListing(listingId as string),
    enabled: !!listingId,
    retry: 1,
  });

  if (!listingId) return <p className="p-6 text-[#d4af37]">Chyba ID ponuky.</p>;

  return (
    <main className="mx-auto w-full max-w-3xl bg-[#070707] p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">Ponuka</p>
      <h1 className="mt-1 font-serif text-3xl">{data?.title || 'Ponuka'}</h1>
      <p className="mt-1 font-mono text-xs text-[#9a8b63]">{listingId}</p>
      {isLoading && <p className="mt-4 text-sm text-[#cbb98a]">Nacitavam ponuku…</p>}
      {error && <p className="mt-4 text-sm text-red-300">{(error as Error).message}</p>}
      {data && (
        <div className="mt-4 rounded-2xl border border-[#d4af37]/35 bg-black p-5 text-sm">
          <p>Material: {data.materialType}</p>
          <p>Mnozstvo: {data.quantity} {data.unit}</p>
          <p>Lokalita: {data.location}</p>
          <p>Stav: {data.status}</p>
          {data.description ? <p className="mt-2 text-[#cbb98a]">{data.description}</p> : null}
        </div>
      )}
      <RecommendationsPanel
        listingId={listingId}
        listingTitle={data?.title}
        listingLocation={data?.location}
        materialType={data?.materialType}
        onPickDestination={setDestination}
      />
      <TransportPanel origin={data?.location} destination={destination} />
      <FreightPanel near={destination || data?.location} />
    </main>
  );
}
