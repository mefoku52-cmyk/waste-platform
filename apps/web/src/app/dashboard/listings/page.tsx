'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useListings } from '@/features/listings';
import { http } from '@/lib/api/http';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const LISTING_STATUS_LABEL: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  draft: {
    label: 'Draft',
    color: '#9a8f7c',
    bg: 'rgba(110,102,88,0.15)',
  },
  published: {
    label: 'Zverejnená',
    color: '#5fd17a',
    bg: 'rgba(46,160,67,0.15)',
  },
  reserved: {
    label: 'Rezervovaná',
    color: '#e8d48b',
    bg: 'rgba(201,168,76,0.15)',
  },
  completed: {
    label: 'Dokončená',
    color: '#8fa8d0',
    bg: 'rgba(80,120,180,0.15)',
  },
  archived: {
    label: 'Archivovaná',
    color: '#a8a8a8',
    bg: 'rgba(80,80,80,0.20)',
  },
};

const COMPANY_STATUS_WARN: Record<string, string> = {
  draft:
    'Firma je v koncepte. Požiadajte o overenie, aby ste mohli publikovať ponuky.',
  verification_submitted:
    'Firma čaká na overenie administrátorom. Publikovanie bude dostupné po schválení.',
  rejected:
    'Firma bola zamietnutá. Skontrolujte údaje a pošlite novú žiadosť o overenie.',
  suspended:
    'Firma je pozastavená. Kontaktujte administrátora platformy.',
  inactive:
    'Firma je neaktívna. Publikovanie nie je možné.',
};

type Listing = {
  id: string;
  title?: string;
  description?: string;
  material_type?: string;
  materialType?: string;
  location?: string;
  quantity?: number | string;
  unit?: string;
  status?: string | null;
  created_at?: string;
  createdAt?: string;
};

export default function MyListingsPage() {
  const {
    data,
    isLoading,
    error,
  } = useListings() as {
    data?: unknown;
    isLoading?: boolean;
    error?: unknown;
  };

  const { data: companiesData } = useQuery({
    queryKey: ['companies', 'my'],
    queryFn: () => http.get<any>('/companies'),
  });

  const raw: any = data;

  const items: Listing[] = Array.isArray(raw)
    ? raw
    : raw?.data ?? raw?.items ?? [];

  const myCompany = (() => {
    const companies =
      (companiesData as any)?.items ??
      (companiesData as any)?.data ??
      companiesData;

    if (Array.isArray(companies) && companies.length > 0) {
      return companies[0];
    }

    return null;
  })();

  const companyStatus = String(myCompany?.status || 'draft');
  const isVerified = companyStatus === 'verified';
  const warningMessage = COMPANY_STATUS_WARN[companyStatus];

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        {!isVerified && warningMessage && (
          <div
            className="mb-8 rounded-2xl border p-5"
            style={{
              borderColor:
                'color-mix(in srgb, #c9a84c 40%, transparent)',
              background: 'rgba(201,168,76,0.06)',
            }}
          >
            <p
              className="mb-1 text-[10px] uppercase tracking-[0.25em]"
              style={{ color: GOLD }}
            >
              Stav firmy: {companyStatus}
            </p>

            <p
              className="text-sm leading-relaxed"
              style={{ color: FG }}
            >
              {warningMessage}
            </p>

            {companyStatus === 'draft' && (
              <Link
                href="/dashboard/companies/new"
                className="mt-3 inline-block text-sm underline underline-offset-4"
                style={{ color: GOLD_BRIGHT }}
              >
                Požiadať o overenie firmy →
              </Link>
            )}
          </div>
        )}

        <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p
              className="mb-3 text-[11px] uppercase tracking-[0.3em]"
              style={{ color: GOLD }}
            >
              MOJE PONUKY
            </p>

            <h1
              className="text-4xl leading-tight tracking-[-0.02em] md:text-5xl"
              style={{ fontFamily: 'DM Serif Display, serif' }}
            >
              Ponuky
            </h1>
          </div>

          <Link
            href="/dashboard/listings/new"
            className="rounded-md px-6 py-3 text-sm font-semibold"
            style={{
              background: GOLD,
              color: '#090807',
            }}
          >
            + Pridať ponuku
          </Link>
        </div>

        {isLoading ? (
          <p style={{ color: MUTED }}>Načítavam…</p>
        ) : error ? (
          <div
            className="rounded-2xl border p-6"
            style={{
              borderColor:
                'color-mix(in srgb, #c45c4a 35%, transparent)',
            }}
          >
            <p className="text-sm" style={{ color: '#c45c4a' }}>
              Nepodarilo sa načítať ponuky.
            </p>

            <p
              className="mt-2 text-xs"
              style={{ color: MUTED }}
            >
              {String((error as any)?.message || 'Neznáma chyba')}
            </p>
          </div>
        ) : items.length === 0 ? (
          <div
            className="rounded-2xl border py-16 text-center"
            style={{
              borderColor:
                'color-mix(in srgb, #c9a84c 20%, transparent)',
            }}
          >
            <h3
              className="text-2xl"
              style={{ fontFamily: 'DM Serif Display, serif' }}
            >
              Zatiaľ žiadne ponuky
            </h3>

            <p
              className="mt-2 text-sm"
              style={{ color: MUTED }}
            >
              Pridaj svoju prvú ponuku a oslov zákazníkov.
            </p>
          </div>
        ) : (
          <ul className="grid gap-4 md:grid-cols-2">
            {items.map((item) => {
              const status = String(item.status || 'draft');
              const statusMeta = LISTING_STATUS_LABEL[status];

              return (
                <li key={item.id}>
                  <Link
                    href={`/dashboard/listings/${item.id}`}
                    className="block rounded-2xl border p-5 transition-colors hover:bg-white/5"
                    style={{
                      borderColor:
                        'color-mix(in srgb, #c9a84c 25%, transparent)',
                    }}
                  >
                    <p
                      className="text-[10px] uppercase tracking-[0.25em]"
                      style={{ color: GOLD }}
                    >
                      {item.material_type ||
                        item.materialType ||
                        '—'}
                    </p>

                    <h3
                      className="mt-2 text-2xl"
                      style={{
                        fontFamily: 'DM Serif Display, serif',
                        color: GOLD_BRIGHT,
                      }}
                    >
                      {item.title || 'Ponuka'}
                    </h3>

                    <p
                      className="mt-2 line-clamp-2 text-sm"
                      style={{ color: MUTED }}
                    >
                      {item.description || '—'}
                    </p>

                    <div
                      className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs"
                      style={{ color: FAINT }}
                    >
                      <span>{item.location || '—'}</span>

                      <span>
                        {item.quantity || '—'} {item.unit || ''}
                      </span>

                      <span
                        className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em]"
                        style={{
                          background:
                            statusMeta?.bg ||
                            'rgba(110,102,88,0.15)',
                          color:
                            statusMeta?.color ||
                            '#9a8f7c',
                        }}
                      >
                        {statusMeta?.label || status}
                      </span>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
