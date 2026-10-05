'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { ListingForm } from '@/features/listings';
import { listingsApi } from '@/features/listings/api';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

type ImageLike = string | { url?: string; imageUrl?: string; image_url?: string; photoUrl?: string; photo_url?: string };

function pickImage(item: ImageLike | ImageLike[] | null | undefined): string | null {
  if (!item) return null;
  if (typeof item === 'string') return item;
  if (Array.isArray(item)) {
    for (const entry of item) {
      const url = pickImage(entry);
      if (url) return url;
    }
    return null;
  }
  return (
    item.imageUrl ||
    item.image_url ||
    item.url ||
    item.photoUrl ||
    item.photo_url ||
    null
  );
}

export default function EditListingPage() {
  const { t } = useT();
  const params = useParams();
  const router = useRouter();
  const listingId = String(params?.id || '');

  const { data, isLoading, error } = useQuery({
    queryKey: ['listing', listingId],
    queryFn: () => listingsApi.getListing(listingId),
    enabled: Boolean(listingId),
  });

  const [initialData, setInitialData] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!data) return;
    const raw = data as any;
    const entity = raw?.data ?? raw;

    setInitialData({
      title: entity.title || '',
      materialType: entity.materialType || entity.material_type || '',
      quantity: Number(entity.quantity ?? 0) || 0,
      unit: entity.unit || 'kg',
      price:
        entity.price !== null && entity.price !== undefined
          ? Number(entity.price)
          : undefined,
      currency: entity.currency || 'EUR',
      condition: entity.condition || 'použité',
      location: entity.location || '',
      companyId: entity.companyId || entity.company_id || '',
      description: entity.description || '',
      imageUrl: pickImage(entity.imageUrl ?? entity.image_url ?? entity.images) || '',
    });
  }, [data]);

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div
        className="min-h-screen"
        style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}
      >
        <DashboardHeader />

        <main className="mx-auto max-w-2xl px-4 py-10">
          <p
            className="mb-3 text-[11px] uppercase tracking-[0.3em]"
            style={{ color: GOLD }}
          >
            {t('listings.edit') || 'UPRAVIŤ PONUKU'}
          </p>

          <h1
            className="mb-8 text-4xl leading-tight tracking-[-0.02em] md:text-5xl"
            style={{ fontFamily: 'DM Serif Display, serif' }}
          >
            Upraviť ponuku
          </h1>

          {isLoading ? (
            <p style={{ color: MUTED }}>Načítavam…</p>
          ) : error ? (
            <div
              className="rounded-2xl border p-5"
              style={{ borderColor: 'rgba(196,92,74,0.35)' }}
            >
              <p className="text-sm" style={{ color: '#c45c4a' }}>
                Ponuku sa nepodarilo načítať.
              </p>
              <button
                type="button"
                className="mt-3 text-sm underline"
                style={{ color: GOLD }}
                onClick={() => router.back()}
              >
                Späť
              </button>
            </div>
          ) : !initialData ? (
            <p style={{ color: MUTED }}>Pripravujem formulár…</p>
          ) : (
            <ListingForm
              listingId={listingId}
              initialData={initialData as any}
            />
          )}
        </main>

        <DashboardFooter />
      </div>
    </>
  );
}
