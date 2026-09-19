'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { useListing } from '@/features/listings';
import { useParams } from 'next/navigation';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function ListingDetailPage() {
  const params = useParams();
  const id = String(params?.id || '');
  const { data, isLoading } = useListing(id) as any;

  const item: any = data ?? {};

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-4xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            PONUKA
          </p>

          {isLoading ? (
            <p style={{ color: MUTED }}>Načítavam…</p>
          ) : (
            <>
              <h1 className="mb-4 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
                {item.title || 'Ponuka'}
              </h1>
              <p className="mb-8 text-base" style={{ color: MUTED }}>
                {item.description || '—'}
              </p>

              <dl className="grid gap-4 md:grid-cols-2">
                {[
                  ['Materiál', item.material_type ?? item.materialType ?? '—'],
                  ['Lokalita', item.location ?? '—'],
                  ['Množstvo', `${item.quantity ?? '—'} ${item.unit ?? ''}`],
                  ['Status', item.status ?? '—'],
                  ['Doprava', item.transport ?? '—'],
                  ['Vytvorené', item.created_at ?? item.createdAt ?? '—'],
                ].map(([k, v]) => (
                  <div
                    key={String(k)}
                    className="rounded-xl border p-4"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
                  >
                    <dt className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
                      {k}
                    </dt>
                    <dd className="mt-1 text-base" style={{ color: FG }}>
                      {String(v)}
                    </dd>
                  </div>
                ))}
              </dl>
            </>
          )}
        </main>
      </div>
    </>
  );
}
