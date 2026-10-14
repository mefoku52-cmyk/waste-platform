'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { config } from '@/lib/config';
import { getListingRecommendations } from '@/features/recommendations/api';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

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
  const { isLoading: authLoading } = useAuthRequired();
  const isAdmin = useIsPlatformAdmin();
  const listingsQuery = useQuery({ queryKey: ['admin-listings'], queryFn: fetchListings });
  const firstId = listingsQuery.data?.[0]?.id;
  const recQuery = useQuery({
    queryKey: ['admin-rec', firstId],
    queryFn: () => getListingRecommendations(firstId as string),
    enabled: !!firstId,
  });

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: BG, color: FG }}>
        <div className="text-sm" style={{ color: MUTED }}>Načítavam…</div>
      </div>
    );
  }
  if (!isAdmin) return null;

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <DashboardHeader />
      <main className="mx-auto max-w-4xl px-4 py-10">
        <Link
          href="/dashboard/admin"
          className="mb-6 inline-block text-sm"
          style={{ color: GOLD_BRIGHT }}
        >
          ← Späť na admin
        </Link>

        <p
          className="mb-2 text-[11px] uppercase tracking-[0.3em]"
          style={{ color: GOLD }}
        >
          {t('admin.recommendationsKicker')}
        </p>
        <h1
          className="mb-2 text-3xl md:text-4xl"
          style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
        >
          {t('admin.recommendationsTitle')}
        </h1>
        <p className="mb-8 text-sm" style={{ color: MUTED }}>
          Prehľad match-ov. Žiadny auto-deal.
        </p>

        {listingsQuery.error && (
          <p className="mt-4 text-sm text-red-400">
            {(listingsQuery.error as Error).message}
          </p>
        )}

        <ul className="mt-4 space-y-2">
          {(listingsQuery.data || []).map((row) => (
            <li
              key={row.id}
              className="rounded-xl border p-4"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)', background: '#0b0b0b' }}
            >
              <Link
                href={'/dashboard/listings/' + row.id}
                className="font-semibold"
                style={{ color: GOLD_BRIGHT }}
              >
                {row.title || row.id}
              </Link>
              <p className="mt-1 text-xs" style={{ color: MUTED }}>
                {row.materialType} · {row.location}
              </p>
            </li>
          ))}
        </ul>

        {recQuery.data && (
          <section
            className="mt-6 rounded-2xl border p-4"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)' }}
          >
            <p className="text-sm" style={{ color: MUTED }}>
              Prvá ponuka: {recQuery.data.items.length} kandidátov
            </p>
          </section>
        )}
      </main>
      <DashboardFooter />
    </div>
  );
}
