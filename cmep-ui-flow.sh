#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/waste-platform"
WEB="$ROOT/apps/web"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$ROOT/backups/cmep-ui-flow-$STAMP"

cd "$ROOT"

if [ ! -d "$WEB/src" ]; then
  echo "MISSING: $WEB/src"
  exit 1
fi

mkdir -p "$BACKUP"

backup() {
  local file="$1"
  if [ -f "$file" ]; then
    mkdir -p "$BACKUP/$(dirname "$file")"
    cp "$file" "$BACKUP/$file"
    echo "BACKUP $file"
  fi
}

write_file() {
  local file="$1"
  mkdir -p "$(dirname "$file")"
  cat > "$file"
  echo "WROTE $file"
}

echo "=== CMEP UI FLOW ==="
echo "Backup: $BACKUP"

backup "apps/web/src/app/globals.css"
backup "apps/web/src/components/layout/app-shell.tsx"
backup "apps/web/src/components/layout/dashboard-header.tsx"
backup "apps/web/src/components/layout/dashboard-footer.tsx"
backup "apps/web/src/app/dashboard/page.tsx"
backup "apps/web/src/app/dashboard/listings/page.tsx"
backup "apps/web/src/app/dashboard/listings/[id]/page.tsx"
backup "apps/web/src/app/dashboard/companies/page.tsx"
backup "apps/web/src/app/dashboard/documents/page.tsx"
backup "apps/web/src/app/dashboard/inquiries/page.tsx"
backup "apps/web/src/app/dashboard/chat/page.tsx"
backup "apps/web/src/app/dashboard/chat/[id]/page.tsx"
backup "apps/web/src/features/listings/types.ts"
backup "apps/web/src/features/listings/api.ts"
backup "apps/web/src/lib/i18n/messages/sk.json"
backup "apps/web/src/lib/i18n/messages/en.json"
backup "apps/web/src/lib/i18n/messages/ru.json"
backup "apps/web/src/lib/i18n/messages/fr.json"
backup "apps/web/src/lib/i18n/messages/de.json"

cat > apps/web/src/app/globals.css <<'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --cmep-bg: #090807;
  --cmep-panel: #100f0c;
  --cmep-panel-soft: rgba(18, 16, 11, 0.92);
  --cmep-text: #f3ead8;
  --cmep-muted: #9a8f7c;
  --cmep-gold: #c9a84c;
  --cmep-gold-bright: #e8d48b;
  --cmep-line: rgba(201, 168, 76, 0.24);
}

* {
  box-sizing: border-box;
}

html {
  min-height: 100%;
  background: var(--cmep-bg);
  scroll-behavior: smooth;
}

body {
  min-width: 320px;
  min-height: 100dvh;
  margin: 0;
  overflow-x: hidden;
  overflow-y: auto;
  color: var(--cmep-text);
  background:
    radial-gradient(circle at 10% -10%, rgba(201, 168, 76, 0.08), transparent 30rem),
    radial-gradient(circle at 100% 10%, rgba(201, 168, 76, 0.04), transparent 28rem),
    var(--cmep-bg);
  font-family: Arial, Helvetica, sans-serif;
}

button,
a,
input,
textarea,
select {
  -webkit-tap-highlight-color: transparent;
}

button,
a {
  touch-action: manipulation;
}

img {
  max-width: 100%;
}

.cmep-page {
  min-height: 100dvh;
  overflow: visible;
  background: transparent;
}

.cmep-main {
  min-height: auto;
  overflow: visible;
}

.cmep-panel {
  border: 1px solid var(--cmep-line);
  background: var(--cmep-panel-soft);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
}

.cmep-card {
  border: 1px solid var(--cmep-line);
  background: rgba(14, 13, 10, 0.95);
  transition:
    border-color 160ms ease,
    transform 160ms ease,
    background 160ms ease;
}

.cmep-card:hover {
  border-color: rgba(232, 212, 139, 0.62);
  background: rgba(22, 20, 14, 0.98);
}

.cmep-card:active {
  transform: scale(0.995);
}

.cmep-muted {
  color: var(--cmep-muted);
}

.cmep-gold {
  color: var(--cmep-gold-bright);
}

@media (max-width: 767px) {
  .cmep-page,
  .cmep-main {
    min-height: auto;
  }

  body {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
EOF

cat > apps/web/src/components/layout/app-shell.tsx <<'EOF'
'use client';

import { ReactNode } from 'react';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="cmep-page">
      <DashboardHeader />
      <main className="cmep-main">{children}</main>
      <DashboardFooter />
    </div>
  );
}
EOF

cat > apps/web/src/app/dashboard/page.tsx <<'EOF'
'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

export default function DashboardPage() {
  const { t } = useT();

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
              {t('dashboard.market')}
            </p>
            <h1 className="mt-2 font-serif text-3xl leading-tight sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('dashboard.title')}
            </h1>
            <p className="mt-2 max-w-xl text-sm leading-6" style={{ color: MUTED }}>
              {t('dashboard.subline')}
            </p>
          </div>

          <Link
            href="/dashboard/listings/new"
            className="rounded-full border px-4 py-2 text-sm font-semibold"
            style={{
              borderColor: 'rgba(201,168,76,0.55)',
              background: 'rgba(201,168,76,0.12)',
              color: GOLD_BRIGHT,
            }}
          >
            + {t('dashboard.addListing')}
          </Link>
        </div>

        <section className="cmep-panel rounded-2xl p-4 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                {t('dashboard.market')}
              </p>
              <h2 className="mt-1 font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>
                {t('dashboard.searchTitle')}
              </h2>
              <p className="mt-2 text-sm leading-6" style={{ color: MUTED }}>
                {t('dashboard.sectionNote')}
              </p>
            </div>

            <Link
              href="/dashboard/listings"
              className="rounded-full border px-4 py-2 text-sm"
              style={{ borderColor: 'rgba(201,168,76,0.45)', color: GOLD_BRIGHT }}
            >
              {t('dashboard.viewAll')}
            </Link>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/listings/page.tsx <<'EOF'
'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { useListings } from '@/features/listings';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type ListingRow = {
  id: string;
  title?: string | null;
  materialType?: string | null;
  material_type?: string | null;
  quantity?: number | string | null;
  unit?: string | null;
  location?: string | null;
  status?: string | null;
  description?: string | null;
  imageUrl?: string | null;
  image_url?: string | null;
  photoUrl?: string | null;
  photo_url?: string | null;
  images?: unknown;
  photos?: unknown;
};

function firstImage(row: ListingRow): string | null {
  const direct = row.imageUrl || row.image_url || row.photoUrl || row.photo_url;
  if (typeof direct === 'string' && direct.trim()) return direct;

  const gallery = Array.isArray(row.images)
    ? row.images
    : Array.isArray(row.photos)
      ? row.photos
      : [];

  for (const item of gallery) {
    if (typeof item === 'string' && item.trim()) return item;
    if (item && typeof item === 'object') {
      const candidate = item as Record<string, unknown>;
      for (const key of ['url', 'imageUrl', 'image_url', 'photoUrl', 'photo_url']) {
        if (typeof candidate[key] === 'string' && candidate[key].trim()) {
          return candidate[key] as string;
        }
      }
    }
  }

  return null;
}

function getItems(raw: unknown): ListingRow[] {
  if (Array.isArray(raw)) return raw as ListingRow[];
  if (raw && typeof raw === 'object') {
    const value = raw as Record<string, unknown>;
    if (Array.isArray(value.items)) return value.items as ListingRow[];
    if (Array.isArray(value.data)) return value.data as ListingRow[];
    if (value.data && typeof value.data === 'object' && Array.isArray((value.data as Record<string, unknown>).items)) {
      return (value.data as Record<string, unknown>).items as ListingRow[];
    }
  }
  return [];
}

export default function ListingsPage() {
  const { t } = useT();
  const query = useListings() as { data?: unknown; isLoading?: boolean; error?: unknown };
  const items = getItems(query.data);

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-5xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
              {t('listings.mySection')}
            </p>
            <h1 className="mt-2 font-serif text-3xl leading-tight sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('listings.myTitle')}
            </h1>
            <p className="mt-2 text-sm leading-6" style={{ color: MUTED }}>
              {t('listings.myListingsSubtitle')}
            </p>
          </div>

          <Link
            href="/dashboard/listings/new"
            className="rounded-full border px-4 py-2 text-sm font-semibold"
            style={{
              borderColor: 'rgba(201,168,76,0.55)',
              background: 'rgba(201,168,76,0.12)',
              color: GOLD_BRIGHT,
            }}
          >
            + {t('listings.addButton')}
          </Link>
        </div>

        {query.isLoading ? (
          <p className="text-sm" style={{ color: MUTED }}>{t('dashboard.loadingListings')}</p>
        ) : query.error ? (
          <div className="rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-[#f0bbb0]">
            {query.error instanceof Error ? query.error.message : t('dashboard.loadFailed')}
          </div>
        ) : items.length === 0 ? (
          <section className="cmep-panel rounded-2xl px-5 py-14 text-center">
            <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>
              {t('listings.empty')}
            </h2>
            <p className="mt-2 text-sm" style={{ color: MUTED }}>
              {t('listings.emptyHint')}
            </p>
          </section>
        ) : (
          <ul className="space-y-3">
            {items.map((row) => {
              const material = row.materialType || row.material_type || t('listings.material');
              const photo = firstImage(row);
              const quantity = row.quantity === null || row.quantity === undefined
                ? null
                : `${row.quantity}${row.unit ? ` ${row.unit}` : ''}`;

              return (
                <li key={row.id}>
                  <Link
                    href={`/dashboard/listings/${row.id}`}
                    className="cmep-card flex min-h-[126px] overflow-hidden rounded-2xl"
                    aria-label={`${t('dashboard.detail')}: ${row.title || row.id}`}
                  >
                    <div className="flex min-w-0 flex-1 flex-col justify-between p-4 sm:p-5">
                      <div className="min-w-0">
                        <p className="truncate text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: GOLD }}>
                          {material}
                        </p>
                        <h2 className="mt-1 truncate font-serif text-xl sm:text-2xl" style={{ color: GOLD_BRIGHT }}>
                          {row.title || t('dashboard.titleNoName')}
                        </h2>
                        {row.description ? (
                          <p className="mt-2 line-clamp-2 text-sm leading-5" style={{ color: MUTED }}>
                            {row.description}
                          </p>
                        ) : null}
                      </div>

                      <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs" style={{ color: MUTED }}>
                        {quantity ? <span>{t('listings.quantity')}: {quantity}</span> : null}
                        {row.location ? <span>{row.location}</span> : null}
                        {row.status ? <span>{row.status}</span> : null}
                      </div>
                    </div>

                    <div className="relative w-[39%] min-w-[124px] max-w-[220px] border-l border-[rgba(201,168,76,0.18)] bg-[#14120d]">
                      {photo ? (
                        <img
                          src={photo}
                          alt={row.title || material || t('listings.detailTitle')}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center p-3 text-center text-[10px] uppercase tracking-[0.16em]" style={{ color: MUTED }}>
                          {t('listingMedia.noPhoto')}
                        </div>
                      )}
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
EOF

cat > apps/web/src/app/dashboard/listings/[id]/page.tsx <<'EOF'
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';
import { RecommendationsPanel } from '@/features/recommendations/components/recommendations-panel';
import { TransportPanel } from '@/features/recommendations/components/transport-panel';
import { FreightPanel } from '@/features/recommendations/components/freight-panel';
import { postListingViewed } from '@/features/recommendations/api';
import { ListingInquiryButton } from '@/features/inquiries/components/listing-inquiry-button';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type ImageLike = string | {
  id?: string;
  url?: string;
  imageUrl?: string;
  image_url?: string;
  photoUrl?: string;
  photo_url?: string;
};

type ListingData = {
  id: string;
  title?: string | null;
  materialType?: string | null;
  material_type?: string | null;
  quantity?: number | string | null;
  unit?: string | null;
  location?: string | null;
  status?: string | null;
  description?: string | null;
  imageUrl?: string | null;
  image_url?: string | null;
  photoUrl?: string | null;
  photo_url?: string | null;
  images?: ImageLike[] | null;
  photos?: ImageLike[] | null;
  company?: {
    legalName?: string | null;
    tradingName?: string | null;
    city?: string | null;
    status?: string | null;
    acceptedMaterialTypes?: string | null;
  } | null;
  companyName?: string | null;
  company_name?: string | null;
  companyCity?: string | null;
  company_city?: string | null;
};

function imageUrl(item: ImageLike): string | null {
  if (typeof item === 'string') return item.trim() || null;
  if (!item) return null;

  for (const key of ['url', 'imageUrl', 'image_url', 'photoUrl', 'photo_url'] as const) {
    const value = item[key];
    if (typeof value === 'string' && value.trim()) return value;
  }

  return null;
}

function getGallery(data: ListingData): string[] {
  const all: ImageLike[] = [
    data.imageUrl || '',
    data.image_url || '',
    data.photoUrl || '',
    data.photo_url || '',
    ...(Array.isArray(data.images) ? data.images : []),
    ...(Array.isArray(data.photos) ? data.photos : []),
  ];

  return Array.from(new Set(all.map(imageUrl).filter((url): url is string => Boolean(url))));
}

async function fetchListing(listingId: string): Promise<ListingData> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(`${config.apiBaseUrl}/listings/${listingId}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }

  return (body.data ?? body) as ListingData;
}

export default function ListingDetailPage() {
  const params = useParams<{ id: string }>();
  const listingId = String(params?.id || '');
  const { t } = useT();
  const [destination, setDestination] = useState('');
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => fetchListing(listingId),
    enabled: Boolean(listingId),
    retry: 1,
  });

  useEffect(() => {
    if (listingId) void postListingViewed(listingId);
  }, [listingId]);

  const data = query.data;
  const gallery = useMemo(() => (data ? getGallery(data) : []), [data]);
  const title = data?.title || t('dashboard.titleNoName');
  const material = data?.materialType || data?.material_type || t('listings.material');
  const companyName = data?.company?.tradingName
    || data?.company?.legalName
    || data?.companyName
    || data?.company_name;
  const companyCity = data?.company?.city || data?.companyCity || data?.company_city;

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link
          href="/dashboard/listings"
          className="inline-flex rounded-full border px-3 py-1.5 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}
        >
          ← {t('common.back')}
        </Link>

        {query.isLoading ? (
          <p className="mt-8 text-sm" style={{ color: MUTED }}>{t('dashboard.loadingListings')}</p>
        ) : query.error ? (
          <div className="mt-8 rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-[#f0bbb0]">
            {query.error instanceof Error ? query.error.message : t('dashboard.loadFailed')}
          </div>
        ) : data ? (
          <>
            <section className="mt-6 overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.28)] bg-[#0f0e0a]">
              {gallery[0] ? (
                <button
                  type="button"
                  className="block aspect-[16/9] w-full bg-[#17140d]"
                  onClick={() => setSelectedPhoto(gallery[0])}
                  aria-label={t('listingMedia.openPhoto')}
                >
                  <img src={gallery[0]} alt={title} className="h-full w-full object-cover" />
                </button>
              ) : (
                <div className="flex aspect-[16/9] items-center justify-center bg-[#17140d] text-xs uppercase tracking-[0.2em]" style={{ color: MUTED }}>
                  {t('listingMedia.noPhoto')}
                </div>
              )}

              <div className="p-5 sm:p-7">
                <p className="text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
                  {material}
                </p>
                <h1 className="mt-2 font-serif text-3xl leading-tight sm:text-5xl" style={{ color: GOLD_BRIGHT }}>
                  {title}
                </h1>

                <div className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
                  <div className="cmep-panel rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>{t('listings.quantity')}</p>
                    <p className="mt-1">{data.quantity ?? '—'} {data.unit || ''}</p>
                  </div>
                  <div className="cmep-panel rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>{t('listings.location')}</p>
                    <p className="mt-1">{data.location || '—'}</p>
                  </div>
                  <div className="cmep-panel rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>{t('listings.status')}</p>
                    <p className="mt-1">{data.status || '—'}</p>
                  </div>
                </div>

                {data.description ? (
                  <p className="mt-5 whitespace-pre-wrap text-sm leading-6" style={{ color: MUTED }}>
                    {data.description}
                  </p>
                ) : null}

                <div className="mt-6">
                  <ListingInquiryButton listingId={listingId} listingTitle={title} />
                </div>
              </div>
            </section>

            {gallery.length > 1 ? (
              <section className="mt-6">
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                  {t('listingMedia.gallery')}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {gallery.map((photo, index) => (
                    <button
                      key={`${photo}-${index}`}
                      type="button"
                      className="overflow-hidden rounded-xl border border-[rgba(201,168,76,0.25)] bg-[#17140d]"
                      onClick={() => setSelectedPhoto(photo)}
                      aria-label={`${t('listingMedia.openPhoto')} ${index + 1}`}
                    >
                      <img src={photo} alt={`${title} ${index + 1}`} className="aspect-square h-full w-full object-cover" />
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {companyName ? (
              <section className="cmep-panel mt-6 rounded-2xl p-5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                  {t('listingMedia.companySection')}
                </p>
                <h2 className="mt-2 font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>
                  {companyName}
                </h2>
                {companyCity ? <p className="mt-1 text-sm" style={{ color: MUTED }}>{companyCity}</p> : null}
                {data.company?.acceptedMaterialTypes ? (
                  <p className="mt-3 text-sm" style={{ color: MUTED }}>
                    {t('listingMedia.acceptedMaterials')}: {data.company.acceptedMaterialTypes}
                  </p>
                ) : null}
              </section>
            ) : null}

            <RecommendationsPanel
              listingId={listingId}
              listingTitle={data.title || undefined}
              listingLocation={data.location || undefined}
              materialType={data.materialType || data.material_type || undefined}
              onPickDestination={setDestination}
            />
            <TransportPanel origin={data.location || undefined} destination={destination} />
            <FreightPanel near={destination || data.location || undefined} />
          </>
        ) : null}
      </div>

      {selectedPhoto ? (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4"
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedPhoto(null)}
        >
          <button
            type="button"
            className="absolute right-4 top-4 rounded-full border border-white/30 px-3 py-1 text-sm text-white"
            onClick={() => setSelectedPhoto(null)}
          >
            × {t('common.close')}
          </button>
          <img
            src={selectedPhoto}
            alt={title}
            className="max-h-[88dvh] max-w-full rounded-xl object-contain"
            onClick={(event) => event.stopPropagation()}
          />
        </div>
      ) : null}
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/companies/page.tsx <<'EOF'
'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

const PAGE_SIZE = 10;
const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type Company = {
  id: string;
  legalName?: string;
  tradingName?: string;
  city?: string;
  status?: string;
  acceptedMaterialTypes?: string | null;
};

function cleanFilter(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9áäčďéíľĺňóôŕšťúýžÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ,.-s]/g, '').slice(0, 64);
}

async function fetchCompanies(page: number): Promise<{ items: Company[]; total: number }> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(`${config.apiBaseUrl}/companies?page=${page}&pageSize=${PAGE_SIZE}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }

  const items = (body.items || body.data || []) as Company[];
  return {
    items: Array.isArray(items) ? items : [],
    total: Number(body.meta?.total ?? body.total ?? items.length),
  };
}

export default function CompaniesPage() {
  const { t } = useT();
  const [page, setPage] = useState(1);
  const [material, setMaterial] = useState('');

  const query = useQuery({
    queryKey: ['companies', page],
    queryFn: () => fetchCompanies(page),
  });

  const filter = cleanFilter(material).trim().toLowerCase();
  const items = (query.data?.items || []).filter((row) =>
    filter ? (row.acceptedMaterialTypes || '').toLowerCase().includes(filter) : true,
  );
  const total = query.data?.total || 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-5xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
              {t('companies.kicker')}
            </p>
            <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('companies.title')}
            </h1>
          </div>
          <Link href="/dashboard/companies/new" className="rounded-full border px-4 py-2 text-sm" style={{ borderColor: 'rgba(201,168,76,0.48)', color: GOLD_BRIGHT }}>
            + {t('companies.add')}
          </Link>
        </div>

        <input
          value={material}
          onChange={(event) => setMaterial(cleanFilter(event.target.value))}
          placeholder={t('companies.filter')}
          maxLength={64}
          className="mt-6 w-full rounded-xl border border-[rgba(201,168,76,0.28)] bg-[#100f0c] px-4 py-3 text-sm text-[#f3ead8] outline-none"
        />

        {query.isLoading ? <p className="mt-5 text-sm" style={{ color: MUTED }}>{t('companies.loading')}</p> : null}
        {query.error ? <p className="mt-5 text-sm text-red-300">{query.error instanceof Error ? query.error.message : t('common.error')}</p> : null}

        <ul className="mt-6 space-y-3">
          {items.map((row) => (
            <li key={row.id} className="cmep-card rounded-2xl p-4">
              <p className="font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                {row.tradingName || row.legalName || row.id}
              </p>
              <p className="mt-1 text-sm" style={{ color: MUTED }}>
                {[row.city, row.status].filter(Boolean).join(' · ') || '—'}
              </p>
              <p className="mt-3 text-xs" style={{ color: MUTED }}>
                {t('companies.materials')}: {row.acceptedMaterialTypes || t('companies.empty')}
              </p>
            </li>
          ))}
        </ul>

        <div className="mt-6 flex items-center gap-3 text-sm">
          <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="rounded-full border px-3 py-1.5 disabled:opacity-40" style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}>
            {t('companies.prev')}
          </button>
          <span style={{ color: MUTED }}>{page} / {pages}</span>
          <button type="button" disabled={page >= pages} onClick={() => setPage((value) => value + 1)} className="rounded-full border px-3 py-1.5 disabled:opacity-40" style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}>
            {t('companies.next')}
          </button>
        </div>
      </div>
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/documents/page.tsx <<'EOF'
'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { useDocuments } from '@/features/documents';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

export default function DocumentsPage() {
  const { t } = useT();
  const query = useDocuments() as { data?: unknown; isLoading?: boolean };
  const raw = query.data as { data?: unknown[]; items?: unknown[] } | unknown[] | undefined;
  const items = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-5xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
              {t('documents.section')}
            </p>
            <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('documents.title')}
            </h1>
          </div>
          <Link href="/dashboard/documents/new" className="rounded-full border px-4 py-2 text-sm" style={{ borderColor: 'rgba(201,168,76,0.48)', color: GOLD_BRIGHT }}>
            + {t('documents.addButton')}
          </Link>
        </div>

        {query.isLoading ? (
          <p className="text-sm" style={{ color: MUTED }}>{t('common.loading')}</p>
        ) : items.length === 0 ? (
          <section className="cmep-panel rounded-2xl px-5 py-14 text-center">
            <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('documents.empty')}</h2>
            <p className="mt-2 text-sm" style={{ color: MUTED }}>{t('documents.emptyHint')}</p>
          </section>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {(items as Array<Record<string, unknown>>).map((document) => (
              <li key={String(document.id || document.title || Math.random())} className="cmep-card rounded-2xl p-5">
                <p className="font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                  {String(document.title || document.name || t('documents.docTitle'))}
                </p>
                <p className="mt-2 text-sm" style={{ color: MUTED }}>
                  {String(document.document_type || document.documentType || '—')}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/inquiries/page.tsx <<'EOF'
'use client';

import { AppShell } from '@/components/layout/app-shell';
import { InquiriesTable } from '@/features/inquiries/components/inquiries-table';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';

export default function InquiriesPage() {
  const { t } = useT();

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('inquiries.section')}
        </p>
        <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
          {t('inquiries.title')}
        </h1>

        <section className="mt-7">
          <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('inquiries.received')}</h2>
          <div className="mt-4 overflow-x-auto">
            <InquiriesTable mode="received" />
          </div>
        </section>

        <section className="mt-10">
          <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('inquiries.sent')}</h2>
          <div className="mt-4 overflow-x-auto">
            <InquiriesTable mode="sent" />
          </div>
        </section>
      </div>
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/chat/page.tsx <<'EOF'
'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { ChatDraftBanner } from '@/features/recommendations/components/chat-draft-banner';
import { ReportButton } from '@/features/recommendations/components/report-button';
import { useThreads } from '@/features/chat';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type Thread = {
  id: string;
  lastMessage?: string | null;
  unreadCount?: number;
  subject?: string;
};

export default function ChatPage() {
  const { t } = useT();
  const query = useThreads() as { data?: unknown; isLoading?: boolean; error?: unknown };
  const raw = query.data as { items?: Thread[]; data?: Thread[] | { items?: Thread[] } } | Thread[] | undefined;
  const items = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <ChatDraftBanner />

        <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
              {t('chat.section')}
            </p>
            <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('chat.title')}
            </h1>
          </div>
          <ReportButton />
        </div>

        <div className="mt-7">
          {query.isLoading ? (
            <p className="text-sm" style={{ color: MUTED }}>{t('chat.loading')}</p>
          ) : query.error ? (
            <p className="rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-red-200">
              {t('chat.loadError')}
            </p>
          ) : items.length === 0 ? (
            <section className="cmep-panel rounded-2xl px-5 py-14 text-center">
              <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('chat.empty')}</h2>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>{t('chat.emptyHint')}</p>
            </section>
          ) : (
            <ul className="space-y-3">
              {items.map((thread) => {
                const unread = Number(thread.unreadCount || 0);
                return (
                  <li key={thread.id}>
                    <Link href={`/dashboard/chat/${thread.id}`} className="cmep-card block rounded-2xl p-4 sm:p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <h2 className="truncate font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                            {thread.subject || t('chat.firm')}
                          </h2>
                          <p className="mt-2 line-clamp-2 text-sm leading-5" style={{ color: MUTED }}>
                            {thread.lastMessage || '—'}
                          </p>
                        </div>
                        {unread > 0 ? (
                          <span className="rounded-full bg-[#c45c4a] px-2 py-0.5 text-xs font-bold text-white">{unread}</span>
                        ) : null}
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}
EOF

cat > apps/web/src/app/dashboard/chat/[id]/page.tsx <<'EOF'
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { FormEvent, useEffect, useRef, useState } from 'react';

import { AppShell } from '@/components/layout/app-shell';
import { useMessages, useMarkRead, useSendMessage } from '@/features/chat';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type Message = {
  id: string;
  body?: string;
  senderUserId?: string;
  sender_user_id?: string;
  createdAt?: string;
  created_at?: string;
};

export default function ChatThreadPage() {
  const params = useParams<{ id: string }>();
  const id = String(params?.id || '');
  const { t } = useT();
  const [draft, setDraft] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const messagesQuery = useMessages(id) as { data?: unknown; isLoading?: boolean };
  const sendMutation = useSendMessage(id);
  const markReadMutation = useMarkRead();

  const raw = messagesQuery.data as { items?: Message[]; data?: Message[] | { items?: Message[] } } | Message[] | undefined;
  const items = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  useEffect(() => {
    if (id) markReadMutation.mutate(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [items.length]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;

    setErrorMessage('');

    try {
      await sendMutation.mutateAsync(body);
      setDraft('');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t('common.error'));
    }
  }

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link href="/dashboard/chat" className="inline-flex rounded-full border px-3 py-1.5 text-sm" style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}>
          ← {t('common.back')}
        </Link>

        <p className="mt-6 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('chat.conversation')}
        </p>
        <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>{t('chat.title')}</h1>

        <section className="cmep-panel mt-6 rounded-2xl p-4 sm:p-5">
          {messagesQuery.isLoading ? (
            <p className="text-sm" style={{ color: MUTED }}>{t('chat.loading')}</p>
          ) : items.length === 0 ? (
            <p className="py-8 text-center text-sm" style={{ color: MUTED }}>{t('chat.empty')}</p>
          ) : (
            <div className="space-y-3">
              {items.map((message) => {
                const date = message.createdAt || message.created_at;
                const sender = message.senderUserId || message.sender_user_id || '';

                return (
                  <article key={message.id} className="rounded-xl border border-[rgba(201,168,76,0.18)] bg-black/20 p-3">
                    <div className="flex justify-between gap-3 text-xs" style={{ color: MUTED }}>
                      <span className="truncate" style={{ color: GOLD_BRIGHT }}>{sender ? `${sender.slice(0, 8)}…` : t('chat.firm')}</span>
                      <span>{date ? new Date(date).toLocaleString() : ''}</span>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.body || ''}</p>
                  </article>
                );
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <form onSubmit={onSubmit} className="mt-4 grid gap-3">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={t('chat.sendPlaceholder')}
            rows={3}
            disabled={sendMutation.isPending}
            className="rounded-xl border border-[rgba(201,168,76,0.3)] bg-[#100f0c] px-4 py-3 text-sm text-[#f3ead8] outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={sendMutation.isPending || !draft.trim()}
            className="justify-self-start rounded-full border px-4 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ borderColor: 'rgba(201,168,76,0.55)', background: 'rgba(201,168,76,0.12)', color: GOLD_BRIGHT }}
          >
            {sendMutation.isPending ? t('chat.sending') : t('chat.send')}
          </button>
          {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
        </form>
      </div>
    </AppShell>
  );
}
EOF

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path("apps/web/src/lib/i18n/messages")

patches = {
    "sk": {
        "common": {
            "close": "Zavrieť",
        },
        "dashboard": {
            "subline": "Prehľad trhu, aktívnych ponúk a kontaktov na jednom mieste.",
        },
        "chat": {
            "loadError": "Konverzácie sa nepodarilo načítať.",
            "sending": "Odosielam…",
        },
        "inquiries": {
            "section": "DOPYTY",
            "title": "Dopyty",
            "received": "Prijaté",
            "sent": "Odoslané",
        },
        "listingMedia": {
            "noPhoto": "Bez fotografie",
            "gallery": "Fotogaléria",
            "openPhoto": "Otvoriť fotografiu",
            "companySection": "Firma",
            "acceptedMaterials": "Akceptované materiály",
        },
    },
    "en": {
        "common": {
            "close": "Close",
        },
        "dashboard": {
            "subline": "An overview of the market, active listings and contacts in one place.",
        },
        "chat": {
            "loadError": "Conversations could not be loaded.",
            "sending": "Sending…",
        },
        "inquiries": {
            "section": "INQUIRIES",
            "title": "Inquiries",
            "received": "Received",
            "sent": "Sent",
        },
        "listingMedia": {
            "noPhoto": "No photo",
            "gallery": "Photo gallery",
            "openPhoto": "Open photo",
            "companySection": "Company",
            "acceptedMaterials": "Accepted materials",
        },
    },
    "ru": {
        "common": {
            "close": "Закрыть",
        },
        "dashboard": {
            "subline": "Обзор рынка, активных предложений и контактов в одном месте.",
        },
        "chat": {
            "loadError": "Не удалось загрузить диалоги.",
            "sending": "Отправка…",
        },
        "inquiries": {
            "section": "ЗАПРОСЫ",
            "title": "Запросы",
            "received": "Полученные",
            "sent": "Отправленные",
        },
        "listingMedia": {
            "noPhoto": "Без фотографии",
            "gallery": "Фотогалерея",
            "openPhoto": "Открыть фотографию",
            "companySection": "Компания",
            "acceptedMaterials": "Принимаемые материалы",
        },
    },
    "fr": {
        "common": {
            "close": "Fermer",
        },
        "dashboard": {
            "subline": "Une vue d’ensemble du marché, des annonces actives et des contacts.",
        },
        "chat": {
            "loadError": "Impossible de charger les conversations.",
            "sending": "Envoi…",
        },
        "inquiries": {
            "section": "DEMANDES",
            "title": "Demandes",
            "received": "Reçues",
            "sent": "Envoyées",
        },
        "listingMedia": {
            "noPhoto": "Aucune photo",
            "gallery": "Galerie photos",
            "openPhoto": "Ouvrir la photo",
            "companySection": "Entreprise",
            "acceptedMaterials": "Matériaux acceptés",
        },
    },
    "de": {
        "common": {
            "close": "Schließen",
        },
        "dashboard": {
            "subline": "Markt, aktive Angebote und Kontakte auf einen Blick.",
        },
        "chat": {
            "loadError": "Unterhaltungen konnten nicht geladen werden.",
            "sending": "Wird gesendet…",
        },
        "inquiries": {
            "section": "ANFRAGEN",
            "title": "Anfragen",
            "received": "Eingegangen",
            "sent": "Gesendet",
        },
        "listingMedia": {
            "noPhoto": "Kein Foto",
            "gallery": "Fotogalerie",
            "openPhoto": "Foto öffnen",
            "companySection": "Unternehmen",
            "acceptedMaterials": "Akzeptierte Materialien",
        },
    },
}

def merge(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict):
            existing = target.get(key)
            if not isinstance(existing, dict):
                existing = {}
                target[key] = existing
            merge(existing, value)
        else:
            target[key] = value

for locale, patch in patches.items():
    path = root / f"{locale}.json"
    if not path.exists():
        raise SystemExit(f"MISSING LOCALE: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    merge(data, patch)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "
", encoding="utf-8")
    print("UPDATED", path)
PY

echo
echo "=== VERIFY JSON ==="
python3 - <<'PY'
import json
from pathlib import Path

for path in sorted(Path("apps/web/src/lib/i18n/messages").glob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
    print("JSON OK", path)
PY

echo
echo "=== TYPECHECK ==="
if [ -d "$WEB/node_modules" ]; then
  (
    cd "$WEB"
    npm run typecheck
  )
else
  echo "SKIPPED: apps/web/node_modules does not exist."
  echo "Run later: cd ~/waste-platform/apps/web && npm install && npm run typecheck"
fi

echo
echo "=== CHANGED FILES ==="
git status --short

echo
echo "DONE"
echo "Backup is here: $BACKUP"
echo "Review changes with: cd "$ROOT" && git diff -- apps/web/src"
