'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { useDocuments } from '@/features/documents';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function DocumentsPage() {
  const { data, isLoading } = useDocuments() as any;
  const raw: any = data;
  const items: any[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

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
                DOKUMENTY
              </p>
              <h1 className="text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
                Dokumenty
              </h1>
            </div>
            <Link
              href="/dashboard/documents/new"
              className="rounded-md px-6 py-3 text-sm font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              + Pridať dokument
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
                Zatiaľ žiadne dokumenty
              </h3>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>
                Nahraj dokumenty, ktoré chceš zdieľať s firmami.
              </p>
            </div>
          ) : (
            <ul className="grid gap-3 md:grid-cols-2">
              {items.map((d) => (
                <li
                  key={d.id}
                  className="rounded-2xl border p-5"
                  style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
                >
                  <p className="text-lg" style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}>
                    {d.title || d.name || 'Dokument'}
                  </p>
                  <p className="mt-1 text-sm" style={{ color: MUTED }}>
                    {d.document_type || d.documentType || '—'}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>
    </>
  );
}
