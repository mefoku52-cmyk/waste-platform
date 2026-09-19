'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { useListings } from '@/features/listings';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

type Listing = {
  id: string;
  title?: string;
  description?: string;
  material_type?: string;
  materialType?: string;
  location?: string;
  quantity?: number | string;
  unit?: string;
  status?: string;
  created_at?: string;
  createdAt?: string;
};

export default function MyListingsPage() {
  const { data, isLoading } = useListings();
  const raw: any = data;
  const items: Listing[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-6xl px-4 py-10">
          <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
                MOJE PONUKY
              </p>
              <h1 className="text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
                Ponuky
              </h1>
            </div>
            <Link
              href="/dashboard/listings/new"
              className="rounded-md px-6 py-3 text-sm font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              + Pridať ponuku
            </Link>
          </div>

          {isLoading ? (
            <p style={{ color: MUTED }}>Načítavam…</p>
          ) : items.length === 0 ? (
            <div
              className="rounded-2xl border py-16 text-center"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
            >
              <h3 className="text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>
                Zatiaľ žiadne ponuky
              </h3>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>
                Pridaj svoju prvú ponuku a oslov zákazníkov.
              </p>
            </div>
          ) : (
            <ul className="grid gap-4 md:grid-cols-2">
              {items.map((item) => (
                <li key={item.id}>
                  <Link
                    href={`/dashboard/listings/${item.id}`}
                    className="block rounded-2xl border p-5 transition-colors hover:bg-white/5"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
                  >
                    <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
                      {item.material_type || item.materialType || '—'}
                    </p>
                    <h3 className="mt-2 text-2xl" style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}>
                      {item.title || 'Ponuka'}
                    </h3>
                    <p className="mt-2 line-clamp-2 text-sm" style={{ color: MUTED }}>
                      {item.description || '—'}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ color: FAINT }}>
                      <span>{item.location || '—'}</span>
                      <span>
                        {item.quantity || '—'} {item.unit || ''}
                      </span>
                      <span>{item.status || '—'}</span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>
    </>
  );
}
