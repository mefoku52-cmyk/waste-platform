'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { useT } from '@/lib/i18n/context';
import { useMarketplace } from '@/features/listings';
import { http } from '@/lib/api/http';
import { SignedImage } from '@/features/uploads/components/signed-image';

type Listing = {
  id: string;
  title: string;
  company: string;
  location: string;
  category: string;
  quantity: string;
  published: string;
  note: string;
  transport: string;
  images: string[];
  promotedUntil?: string | null;
  promoted_until?: string | null;
  promotedTier?: string | null;
  promoted_tier?: string | null;
};

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const PAGE_SIZE = 6;

const categorySkMap: Record<string, string> = {
  all: 'Všetko',
  wood: 'Drevo',
  metal: 'Kov',
  paper: 'Papier',
  plastics: 'Plasty',
  bio: 'Bioodpad',
};

const DASHBOARD_MATERIALS = [
  {
    key: 'wood',
    img: 'https://images.unsplash.com/photo-1542621334-a254cf47733d?w=800&q=80',
    labelKey: 'drevo',
  },
  {
    key: 'metal',
    img: 'https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=800&q=80',
    labelKey: 'kov',
  },
  {
    key: 'paper',
    img: 'https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=800&q=80',
    labelKey: 'papier',
  },
  {
    key: 'plastics',
    img: 'https://images.unsplash.com/photo-1618363010061-a42f6e39e3d8?w=800&q=80',
    labelKey: 'plasty',
  },
  {
    key: 'bio',
    img: 'https://images.unsplash.com/photo-1611843467160-25afb8df1074?w=800&q=80',
    labelKey: 'bioodpad',
  },
] as const;

function fixImageUrl(value: string | null | undefined): string | null {
  if (!value) return null;

  let url = String(value).trim();
  if (!url) return null;

  url = url.replace(/\/api\/v1\/api\/v1\//g, '/api/v1/');

  if (/^https?:\/\//.test(url)) {
    return url;
  }

  const base = (
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    'https://waste-platform.onrender.com/api/v1'
  ).replace(/\/api\/v1\/?$/, '');

  if (url.startsWith('/api/v1/')) {
    return base + url;
  }

  if (url.startsWith('/')) {
    return base + '/api/v1' + url;
  }

  return null;
}

function makeFormatRelative(
  t: (key: string, fallback?: string) => string,
) {
  return (iso: string | null | undefined): string => {
    if (!iso) return '—';

    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return '—';

    const diff = Date.now() - date.getTime();
    const day = 86_400_000;

    if (diff < day) return t('dashboard.dateToday');
    if (diff < 2 * day) return t('dashboard.dateYesterday');

    const days = Math.floor(diff / day);

    if (days < 7) {
      return t('dashboard.dateDaysAgo').replace('{n}', String(days));
    }

    return date.toLocaleDateString();
  };
}

export default function DashboardPage() {
  const { t } = useT();
  const formatRelative = useMemo(() => makeFormatRelative(t), [t]);

  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [location, setLocation] = useState('');
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<Record<string, string>>({});

  const {
    data: apiResp,
    isLoading,
    error,
  } = useMarketplace();

  const { data: companiesResp } = useQuery({
    queryKey: ['companies-for-dashboard'],
    queryFn: () => http.get<any>('/companies'),
  });

  const companiesMap = useMemo(() => {
    const raw: any = companiesResp;
    const items: any[] = Array.isArray(raw)
      ? raw
      : raw?.data ?? raw?.items ?? [];

    const map: Record<string, string> = {};

    for (const company of items) {
      const name =
        company.tradingName ||
        company.trading_name ||
        company.legalName ||
        company.legal_name ||
        company.name ||
        '';

      if (company.id && name) {
        map[String(company.id)] = String(name);
      }
    }

    return map;
  }, [companiesResp]);

  const listings: Listing[] = useMemo(() => {
    const raw: any = apiResp;

    const items: any[] = Array.isArray(raw)
      ? raw
      : raw?.data ?? raw?.items ?? [];

    return items.map((item: any) => ({
      id: String(item.id),
      title: item.title ?? t('dashboard.titleNoName'),
      company:
        item.company?.name ??
        item.companyName ??
        companiesMap[String(item.companyId ?? item.company_id ?? '')] ??
        t('dashboard.companyUnknown'),
      location: item.location ?? '—',
      category:
        item.materialType ??
        item.material_type ??
        item.category ??
        '—',
      quantity:
        [item.quantity, item.unit].filter(Boolean).join(' ') || '—',
      published: formatRelative(item.createdAt ?? item.created_at),
      note: item.description ?? '',
      transport: item.transport ?? '—',
      images: [
        fixImageUrl(item.imageUrl ?? item.image_url),
      ].filter(Boolean) as string[],
      promotedUntil: item.promotedUntil ?? item.promoted_until ?? null,
      promotedTier: item.promotedTier ?? item.promoted_tier ?? null,
    }));
  }, [apiResp, companiesMap, t, formatRelative]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const normalizedLocation = location.trim().toLowerCase();
    const selectedCategory = categorySkMap[category];

    return listings.filter((item) => {
      const searchable = [
        item.title,
        item.company,
        item.location,
        item.category,
        item.note,
        item.transport,
      ]
        .join(' ')
        .toLowerCase();

      const matchesQuery =
        normalizedQuery === '' || searchable.includes(normalizedQuery);

      const matchesCategory =
        category === 'all' ||
        item.category.toLowerCase() === selectedCategory.toLowerCase();

      const matchesLocation =
        normalizedLocation === '' ||
        item.location.toLowerCase().includes(normalizedLocation);

      return matchesQuery && matchesCategory && matchesLocation;
    });
  }, [query, category, location, listings]);

  const pageCount = Math.max(
    1,
    Math.ceil(filtered.length / PAGE_SIZE),
  );

  const currentPageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

  function changeCategory(next: string) {
    setCategory(next);
    setPage(1);
    setOpenId(null);
  }

  function changePage(next: number) {
    if (next < 1 || next > pageCount) return;

    setPage(next);
    setOpenId(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <section className="mb-12">
          <div
            className="rounded-3xl border p-6 md:p-10"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
              background: 'linear-gradient(135deg, rgba(201,168,76,0.08) 0%, rgba(9,8,7,0) 60%)',
            }}
          >
            <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              {t('dashboard.welcome.eyebrow')}
            </p>

            <h2
              className="mb-4 text-4xl leading-[1.05] tracking-[-0.02em] md:text-5xl"
              style={{ color: GOLD_BRIGHT, fontFamily: 'DM Serif Display, serif' }}
            >
              {t('dashboard.welcome.title')}
            </h2>

            <p className="max-w-2xl text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              {t('dashboard.welcome.desc')}
            </p>

            <p
              className="mt-8 text-2xl italic leading-snug md:text-3xl"
              style={{ color: GOLD_BRIGHT, fontFamily: 'DM Serif Display, serif' }}
            >
              {t('dashboard.motto.headline')}
            </p>

            <p className="mt-3 max-w-2xl text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              {t('dashboard.motto.subline')}
            </p>
          </div>
        </section>

        <section className="mb-8">
          <div className="grid gap-3 md:grid-cols-[1.4fr_0.7fr_auto]">
            <input
              type="search"
              placeholder={t('dashboard.searchPlaceholder')}
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              className="h-14 rounded-md border bg-transparent px-5 text-base outline-none"
              style={{
                borderColor:
                  'color-mix(in srgb, #c9a84c 30%, transparent)',
                color: FG,
              }}
            />

            <input
              type="text"
              placeholder={t('dashboard.locationPlaceholder')}
              value={location}
              onChange={(event) => {
                setLocation(event.target.value);
                setPage(1);
              }}
              className="h-14 rounded-md border bg-transparent px-5 text-base outline-none"
              style={{
                borderColor:
                  'color-mix(in srgb, #c9a84c 30%, transparent)',
                color: FG,
              }}
            />

            <button
              type="button"
              onClick={() => setPage(1)}
              className="h-14 rounded-md px-8 text-base font-semibold"
              style={{
                background: GOLD,
                color: BG,
              }}
            >
              {t('dashboard.searchBtn')}
            </button>
          </div>
        </section>

        <section className="mb-10">
          <div className="flex flex-wrap gap-3">
            <Link
              href="/dashboard/companies/new"
              className="rounded-2xl border px-4 py-3 text-sm"
              style={{
                borderColor: GOLD,
                color: GOLD_BRIGHT,
              }}
            >
              {t('dashboard.addCompany')}
            </Link>

            <Link
              href="/dashboard/listings/new"
              className="rounded-2xl border px-4 py-3 text-sm"
              style={{
                borderColor: GOLD,
                color: GOLD_BRIGHT,
              }}
            >
              {t('dashboard.addListing')}
            </Link>

            <Link
              href="/dashboard/documents/new"
              className="rounded-2xl border px-4 py-3 text-sm"
              style={{
                borderColor: GOLD,
                color: GOLD_BRIGHT,
              }}
            >
              {t('dashboard.addDocument')}
            </Link>
          </div>
        </section>

        <section className="mb-10">
          <div className="flex flex-col gap-4">
            {DASHBOARD_MATERIALS.map((material) => {
              const active = category === material.key;

              return (
                <button
                  key={material.key}
                  type="button"
                  onClick={() =>
                    changeCategory(active ? 'all' : material.key)
                  }
                  className="group relative overflow-hidden rounded-2xl border text-left transition-colors"
                  style={{
                    borderColor: active
                      ? GOLD
                      : 'color-mix(in srgb, #c9a84c 20%, transparent)',
                    aspectRatio: '21/9',
                  }}
                >
                  <img
                    src={material.img}
                    alt={t(
                      `dashboard.materials.${material.labelKey}.label`,
                    )}
                    className="absolute inset-0 h-full w-full object-cover transition-opacity"
                    style={{
                      opacity: active ? 0.85 : 0.5,
                    }}
                  />

                  <div
                    className="absolute inset-0"
                    style={{
                      background:
                        'linear-gradient(to top, rgba(9,8,7,0.95) 0%, rgba(9,8,7,0.5) 50%, transparent 100%)',
                    }}
                  />

                  <div className="absolute bottom-0 left-0 right-0 p-3 md:p-4">
                    <p
                      className="text-2xl md:text-3xl"
                      style={{
                        color: active ? GOLD : GOLD_BRIGHT,
                        fontFamily: 'DM Serif Display, serif',
                      }}
                    >
                      {t(
                        `dashboard.materials.${material.labelKey}.label`,
                      )}
                    </p>

                    <p
                      className="mt-1.5 text-xs leading-snug md:text-sm"
                      style={{ color: MUTED }}
                    >
                      {t(
                        `dashboard.materials.${material.labelKey}.desc`,
                      )}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {category !== 'all' && (
            <button
              type="button"
              onClick={() => changeCategory('all')}
              className="mt-3 text-sm underline underline-offset-4"
              style={{ color: MUTED }}
            >
              {t('dashboard.clearFilter')} ·{' '}
              {categorySkMap[category] || category}
            </button>
          )}
        </section>

        <section
          className="mb-6 flex flex-wrap items-center justify-between gap-4 border-t pt-8"
          style={{
            borderColor:
              'color-mix(in srgb, #c9a84c 15%, transparent)',
          }}
        >
          <div style={{ color: MUTED }}>
            {isLoading ? (
              <span>{t('common.loading')}</span>
            ) : error ? (
              <span style={{ color: '#c45c4a' }}>
                {t('dashboard.loadError')}{' '}
                {(error as any)?.message ||
                  t('dashboard.loadErrorUnknown')}
              </span>
            ) : (
              <>
                <strong style={{ color: FG }}>
                  {filtered.length}
                </strong>{' '}
                {t('dashboard.activeListings')}
              </>
            )}
          </div>

          <Link
            href="/dashboard/listings"
            className="rounded-full border px-4 py-2 text-sm"
            style={{
              borderColor:
                'color-mix(in srgb, #c9a84c 45%, transparent)',
              color: GOLD_BRIGHT,
            }}
          >
            {t('dashboard.viewAll')}
          </Link>
        </section>

        <section>
          {currentPageItems.length === 0 && !isLoading ? (
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
                {t('dashboard.notFound')}
              </h3>

              <p
                className="mt-2 text-sm"
                style={{ color: MUTED }}
              >
                {t('dashboard.notFoundHint')}
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {currentPageItems.map((item) => {
                const isOpen = openId === item.id;
                const heroImage =
                  selectedImage[item.id] || item.images[0];

                return (
                  <article
                    key={item.id}
                    className="overflow-hidden rounded-2xl border transition-colors"
                    style={{
                      borderColor:
                        'color-mix(in srgb, #c9a84c 20%, transparent)',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() =>
                        setOpenId(isOpen ? null : item.id)
                      }
                      className="w-full text-left"
                      aria-expanded={isOpen}
                    >
                      {heroImage ? (
                        <div className="relative aspect-[16/10] w-full">
                          <SignedImage
                            src={heroImage}
                            alt={item.title}
                            className="h-full w-full object-cover opacity-90"
                          />

                          <div
                            className="absolute inset-0"
                            style={{
                              background:
                                'linear-gradient(to top, rgba(9,8,7,0.95) 0%, rgba(9,8,7,0.3) 40%, transparent 75%)',
                            }}
                          />

                          <div className="absolute bottom-0 left-0 right-0 p-5">
                            <p
                              className="text-[10px] uppercase tracking-[0.25em]"
                              style={{ color: GOLD }}
                            >
                              {item.category}
                            </p>

                            <h3
                              className="mt-1 text-2xl leading-tight"
                              style={{
                                fontFamily: 'DM Serif Display, serif',
                                color: GOLD_BRIGHT,
                              }}
                            >
                              {item.title}
                            </h3>
                          </div>
                        </div>
                      ) : (
                        <div
                          className="relative min-h-[120px] w-full"
                          style={{ background: '#12100e' }}
                        >
                          <div className="absolute bottom-0 left-0 right-0 p-5">
                            <p
                              className="text-[10px] uppercase tracking-[0.25em]"
                              style={{ color: GOLD }}
                            >
                              {item.category}
                            </p>

                            <h3
                              className="mt-1 text-2xl leading-tight"
                              style={{
                                fontFamily: 'DM Serif Display, serif',
                                color: GOLD_BRIGHT,
                              }}
                            >
                              {item.title}
                            </h3>
                          </div>
                        </div>
                      )}

                      <div className="p-5">
                        <p
                          className="line-clamp-2 text-sm"
                          style={{ color: MUTED }}
                        >
                          {item.note || '—'}
                        </p>

                        <div
                          className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs"
                          style={{ color: FAINT }}
                        >
                          <span>{item.company}</span>
                          <span>· {item.location}</span>
                          <span>· {item.quantity}</span>
                          <span>· {item.published}</span>
                        </div>
                      </div>
                    </button>

                    {isOpen && (
                      <div
                        className="border-t p-5"
                        style={{
                          borderColor:
                            'color-mix(in srgb, #c9a84c 15%, transparent)',
                        }}
                      >
                        <dl className="grid gap-3 text-sm">
                          {[
                            [t('dashboard.company'), item.company],
                            [t('dashboard.location'), item.location],
                            [t('dashboard.category'), item.category],
                            [t('dashboard.quantity'), item.quantity],
                            [t('dashboard.transport'), item.transport],
                            [t('dashboard.published'), item.published],
                          ].map(([label, value]) => (
                            <div
                              key={String(label)}
                              className="grid grid-cols-[130px_1fr] gap-3 border-b pb-2"
                              style={{
                                borderColor:
                                  'color-mix(in srgb, #c9a84c 10%, transparent)',
                              }}
                            >
                              <dt style={{ color: FAINT }}>
                                {label}
                              </dt>
                              <dd
                                style={{
                                  color: FG,
                                  fontWeight: 500,
                                }}
                              >
                                {value}
                              </dd>
                            </div>
                          ))}
                        </dl>

                        {item.images.length > 1 && (
                          <div className="mt-4 flex gap-2">
                            {item.images.map((image) => (
                              <button
                                key={image}
                                type="button"
                                onClick={() =>
                                  setSelectedImage((previous) => ({
                                    ...previous,
                                    [item.id]: image,
                                  }))
                                }
                                className="rounded-md border p-0"
                                style={{
                                  borderColor:
                                    heroImage === image
                                      ? GOLD
                                      : 'transparent',
                                }}
                              >
                                <SignedImage
                                  src={image}
                                  alt=""
                                  className="h-16 w-16 rounded-md object-cover"
                                />
                              </button>
                            ))}
                          </div>
                        )}

                        <Link
                          href={`/dashboard/listings/${item.id}`}
                          className="mt-5 inline-block rounded-md px-5 py-2.5 text-sm font-semibold"
                          style={{
                            background: GOLD,
                            color: BG,
                          }}
                        >
                          {t('dashboard.contactCompany')}
                        </Link>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {pageCount > 1 && (
          <nav
            className="mt-10 flex items-center justify-between border-t pt-6"
            style={{
              borderColor:
                'color-mix(in srgb, #c9a84c 15%, transparent)',
            }}
            aria-label="Pagination"
          >
            <button
              type="button"
              onClick={() => changePage(page - 1)}
              disabled={page === 1}
              className="rounded-md border px-4 py-2 text-sm disabled:opacity-40"
              style={{
                borderColor:
                  'color-mix(in srgb, #c9a84c 30%, transparent)',
                color: FG,
              }}
            >
              {t('dashboard.prev')}
            </button>

            <div className="flex gap-2">
              {Array.from(
                { length: pageCount },
                (_, index) => index + 1,
              ).map((number) => (
                <button
                  key={number}
                  type="button"
                  onClick={() => changePage(number)}
                  className="h-10 w-10 rounded-md border text-sm"
                  style={{
                    borderColor:
                      number === page
                        ? GOLD
                        : 'color-mix(in srgb, #c9a84c 25%, transparent)',
                    background:
                      number === page ? GOLD : 'transparent',
                    color: number === page ? BG : FG,
                  }}
                >
                  {number}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => changePage(page + 1)}
              disabled={page === pageCount}
              className="rounded-md border px-4 py-2 text-sm disabled:opacity-40"
              style={{
                borderColor:
                  'color-mix(in srgb, #c9a84c 30%, transparent)',
                color: FG,
              }}
            >
              {t('dashboard.next')}
            </button>
          </nav>
        )}
      </div>
    </AppShell>
  );
}
