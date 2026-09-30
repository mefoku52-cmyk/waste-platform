'use client';

import { useQuery } from '@tanstack/react-query';
import { config } from '@/lib/config';
import { getListingRecommendations } from '@/features/recommendations/api';
import { useT } from '@/lib/i18n/context';

type ListingRow = { id: string; title: string; materialType?: string; location?: string };

async function fetchListings(): Promise<ListingRow[]> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(config.apiBaseUrl + '/listings', {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error('Listings request failed');
  const rows = (body.items || body.data || body) as ListingRow[];
  return Array.isArray(rows) ? rows : [];
}

export default function AdminRecommendationsPage() {
  const { t } = useT();
  const listingsQuery = useQuery({ queryKey: ['admin-listings'], queryFn: fetchListings });
  const firstId = listingsQuery.data?.[0]?.id;
  const recQuery = useQuery({
    queryKey: ['admin-rec', firstId],
    queryFn: () => getListingRecommendations(firstId as string),
    enabled: !!firstId,
  });

  return (
    <main className="mx-auto w-full max-w-4xl bg-[#070707] p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">{t('admin.recommendationsKicker')}</p>
      <h1 className="mt-1 font-serif text-3xl">{t('admin.recommendationsTitle')}</h1>
      <p className="mt-2 text-sm text-[#cbb98a]">Prehlad match-ov. Ziadny auto-deal.</p>
      {listingsQuery.error && <p className="mt-4 text-red-300">{(listingsQuery.error as Error).message}</p>}
      <ul className="mt-4 space-y-2">
        {(listingsQuery.data || []).map((row) => (
          <li key={row.id} className="rounded-xl border border-[#d4af37]/25 p-3">
            <a href={'/dashboard/listings/' + row.id} className="text-[#d4af37]">{row.title || row.id}</a>
            <p className="text-xs text-[#9a8b63]">{row.materialType} · {row.location}</p>
          </li>
        ))}
      </ul>
      {recQuery.data && (
        <section className="mt-6 rounded-2xl border border-[#d4af37]/35 p-4">
          <p className="text-sm text-[#cbb98a]">Prva ponuka: {recQuery.data.items.length} kandidatov</p>
        </section>
      )}
    </main>
  );
}
