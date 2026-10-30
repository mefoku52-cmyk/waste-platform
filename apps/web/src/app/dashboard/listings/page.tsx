'use client';

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { PremiumHero } from '@/components/layout/premium-hero';
import { AppShell } from '@/components/layout/app-shell';
import { useListings, useMarketplace } from '@/features/listings';
import { useState, useEffect } from 'react';
import { http } from '@/lib/api/http';
import { useT } from '@/lib/i18n/context';
import { SignedImage } from '@/features/uploads/components/signed-image';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const LISTING_STATUS_LABEL: Record<
  string,
  { labelKey: string; color: string; bg: string }
> = {
  draft: {
    labelKey: 'listings.statusLabel.draft',
    color: '#9a8f7c',
    bg: 'rgba(110,102,88,0.15)',
  },
  published: {
    labelKey: 'listings.statusLabel.published',
    color: '#5fd17a',
    bg: 'rgba(46,160,67,0.15)',
  },
  reserved: {
    labelKey: 'listings.statusLabel.reserved',
    color: '#e8d48b',
    bg: 'rgba(201,168,76,0.15)',
  },
  completed: {
    labelKey: 'listings.statusLabel.completed',
    color: '#8fa8d0',
    bg: 'rgba(80,120,180,0.15)',
  },
  archived: {
    labelKey: 'listings.statusLabel.archived',
    color: '#a8a8a8',
    bg: 'rgba(80,80,80,0.20)',
  },
};

const COMPANY_STATUS_WARN: Record<string, string> = {
  draft: 'listings.companyWarn.draft',
  verification_submitted: 'listings.companyWarn.verification_submitted',
  rejected: 'listings.companyWarn.rejected',
  suspended: 'listings.companyWarn.suspended',
  inactive: 'listings.companyWarn.inactive',
};

type Listing = {
  id: string;
  title?: string;
  imageUrl?: string | null;
  image_url?: string | null;
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
  const { t } = useT();
  const [mine, setMine] = useState(true);
  const searchParams = useSearchParams();

  useEffect(() => {
    if (searchParams.get('tab') === 'marketplace') {
      setMine(false);
    }
  }, [searchParams]);
  const own = useListings() as {
    data?: unknown;
    isLoading?: boolean;
    error?: unknown;
  };
  const market = useMarketplace() as {
    data?: unknown;
    isLoading?: boolean;
    error?: unknown;
  };
  const selected = mine ? own : market;
  const { data, isLoading, error } = selected;

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
  const warningKey = COMPANY_STATUS_WARN[companyStatus];

  return (
    <AppShell>
      <PremiumHero
        kicker="PONUKY"
        title="Ponuky"
        subtitle="Prehľad vašich ponúk a materiálov na platforme."
        bgImage="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop"
      />
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        {!isVerified && warningKey && (
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
              {t(warningKey)}
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
              {t('listings.section')}
            </p>

            <h1
              className="text-4xl leading-tight tracking-[-0.02em] md:text-5xl"
              style={{ fontFamily: 'DM Serif Display, serif' }}
            >
              {t('listings.title')}
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
            {t('listings.add')}
            </Link>
            <div className="flex gap-1 rounded-full border p-1" style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)' }}>
              <button
                type="button"
                onClick={() => setMine(true)}
                className="rounded-full px-4 py-2 text-sm font-semibold transition"
                style={{
                  background: mine ? GOLD : 'transparent',
                  color: mine ? '#090807' : GOLD,
                }}
              >
                {t('listingTabs.mine')}
              </button>
              <button
                type="button"
                id="tab-marketplace" onClick={() => setMine(false)}
                className="rounded-full px-4 py-2 text-sm font-semibold transition"
                style={{
                  background: !mine ? GOLD : 'transparent',
                  color: !mine ? '#090807' : GOLD,
                }}
              >
                {t('listingTabs.marketplace')}
              </button>
            </div>
        </div>

        {isLoading ? (
          <p style={{ color: MUTED }}>{t('listings.loading')}</p>
        ) : error ? (
          <div
            className="rounded-2xl border p-6"
            style={{
              borderColor:
                'color-mix(in srgb, #c45c4a 35%, transparent)',
            }}
          >
            <p className="text-sm" style={{ color: '#c45c4a' }}>
              {t('listings.loadFailed')}
            </p>

            <p
              className="mt-2 text-xs"
              style={{ color: MUTED }}
            >
              {String((error as any)?.message || t('listings.unknownError'))}
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
              {t('listingEmpty.title')}
            </h3>

            <p
              className="mt-2 text-sm"
              style={{ color: MUTED }}
            >
              {t('listingEmpty.hint')}
            </p>
          </div>
        ) : (
          <ul className="grid gap-4 md:grid-cols-2">
            {items.map((item) => {
              const status = String(item.status || 'draft');
              const statusMeta = LISTING_STATUS_LABEL[status];

              return (
                <li key={item.id}>
                  <div
                    className="flex gap-4 rounded-2xl border p-5 transition-colors hover:bg-white/5"
                    style={{
                      borderColor:
                        'color-mix(in srgb, #c9a84c 25%, transparent)',
                    }}
                  >
                    <Link
                      href={`/dashboard/listings/${item.id}`}
                      className="min-w-0 flex-1 block"
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
                          {statusMeta?.labelKey ? t(statusMeta.labelKey) : status}
                        </span>
                      </div>
                    </Link>

                    {(item.imageUrl || item.image_url) ? (
                      <Link
                        href={`/dashboard/listings/${item.id}`}
                        className="flex-shrink-0 self-center"
                      >
                        <SignedImage
                          src={item.imageUrl || item.image_url || null}
                          alt={item.title || 'Ponuka'}
                          className="h-16 w-16 rounded-xl object-cover sm:h-24 sm:w-24"
                        />
                      </Link>
                    ) : null}

                    <div className="flex flex-shrink-0 flex-col items-center justify-center gap-2 self-center">
                      <Link
                        href={`/dashboard/listings/${item.id}/edit`}
                        className="rounded-lg border px-3 py-1.5 text-xs font-semibold transition hover:bg-white/5"
                        style={{
                          borderColor:
                            'color-mix(in srgb, #c9a84c 45%, transparent)',
                          color: GOLD_BRIGHT,
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        Upraviť
                      </Link>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
