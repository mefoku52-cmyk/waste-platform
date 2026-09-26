'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { RecommendationsPanel } from '@/features/recommendations/components/recommendations-panel';
import { TransportPanel } from '@/features/recommendations/components/transport-panel';
import { FreightPanel } from '@/features/recommendations/components/freight-panel';
import { postListingViewed } from '@/features/recommendations/api';
import { ListingInquiryButton } from '@/features/inquiries/components/listing-inquiry-button';
import { DeleteListingButton } from '@/features/listings/components/delete-listing-button';
import { PromoteListingButton } from '@/features/listings/components/promote-listing-button';

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
    id?: string | null;
    legalName?: string | null;
    tradingName?: string | null;
    city?: string | null;
    status?: string | null;
    acceptedMaterialTypes?: string | null;
  } | null;
  companyId?: string | null;
  company_id?: string | null;
  companyName?: string | null;
  company_name?: string | null;
  companyCity?: string | null;
  company_city?: string | null;
  promotedUntil?: string | null;
  promoted_until?: string | null;
  promotedTier?: string | null;
  promoted_tier?: string | null;
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
  const me = useCurrentUser();
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

  const myCompanyId = String((me.data as any)?.memberships?.[0]?.companyId || '');
  const listingCompanyId = String(
    (data as any)?.companyId || (data as any)?.company_id || (data as any)?.company?.id || ''
  );
  const isOwner = Boolean(myCompanyId && listingCompanyId && myCompanyId === listingCompanyId);

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
                  {isOwner ? (
                    <div className="mt-3">
                      <PromoteListingButton
                        listingId={listingId}
                        promotedUntil={(data as any).promotedUntil || (data as any).promoted_until || null}
                        promotedTier={(data as any).promotedTier || (data as any).promoted_tier || null}
                      />
                    </div>
                  ) : null}
                  {isOwner ? (
                    <div className="mt-3">
                      <DeleteListingButton listingId={listingId} />
                    </div>
                  ) : null}
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
