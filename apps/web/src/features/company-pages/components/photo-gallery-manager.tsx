'use client';

import { useRef, useState } from 'react';

import { SignedImage } from '@/features/uploads/components/signed-image';
import { uploadFile } from '@/features/uploads/api';
import { useT } from '@/lib/i18n/context';

import {
  useAddCompanyPhoto,
  useCompanyPhotoQuota,
  useCompanyPhotos,
  useDeleteCompanyPhoto,
  useReorderCompanyPhotos,
  useSetPrimaryCompanyPhoto,
  useUpdateCompanyPhoto,
} from '../hooks/use-company-page';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const DANGER = '#e8a598';

const MAX_PHOTOS = 10;

type Props = { companyId: string };

export function PhotoGalleryManager({ companyId }: Props) {
  const { t } = useT();
  const photosQuery = useCompanyPhotos(companyId);
  const quotaQuery = useCompanyPhotoQuota(companyId);
  const add = useAddCompanyPhoto(companyId);
  const update = useUpdateCompanyPhoto(companyId);
  const remove = useDeleteCompanyPhoto(companyId);
  const reorder = useReorderCompanyPhotos(companyId);
  const setPrimary = useSetPrimaryCompanyPhoto(companyId);

  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const photos = photosQuery.data ?? [];
  const quota = quotaQuery.data;
  const uploadedThisYear = quota?.uploadedThisYear ?? photos.length;
  const quotaPerYear = quota?.quotaPerYear ?? MAX_PHOTOS;
  const remaining = quota?.remainingThisYear ?? Math.max(0, quotaPerYear - uploadedThisYear);
  const full = remaining <= 0;

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const uploaded = await uploadFile(file);
      await add.mutateAsync({ fileUrl: uploaded.url });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('companyPage.gallery.uploadFailed'));
    } finally {
      setUploading(false);
    }
  }

  function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= photos.length) return;
    const ids = photos.map((p) => p.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];
    reorder.mutate(ids);
  }

  const busy =
    add.isPending || remove.isPending || reorder.isPending || setPrimary.isPending || update.isPending;

  return (
    <section className="mt-6">
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('companyPage.gallery.title')}
        </p>
        <span className="text-xs" style={{ color: MUTED }}>
          {uploadedThisYear} / {quotaPerYear} tento rok · zostáva {remaining}
        </span>
      </div>

      <p className="mb-3 text-xs" style={{ color: MUTED }}>
        {t('companyPage.gallery.hint')} Kvóta sa obnovuje každý kalendárny rok.
      </p>

      {error ? (
        <div className="mb-3 rounded-xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-3 text-sm text-[#f0bbb0]">
          {error}
        </div>
      ) : null}

      {photosQuery.isLoading ? (
        <p className="text-sm" style={{ color: MUTED }}>{t('tables.loading')}</p>
      ) : photos.length === 0 ? (
        <p className="text-sm" style={{ color: MUTED }}>{t('companyPage.gallery.empty')}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {photos.map((photo, index) => (
            <div
              key={photo.id}
              className="cmep-panel overflow-hidden rounded-xl"
            >
              <div className="relative">
                <SignedImage
                  src={photo.fileUrl}
                  alt={photo.altText || photo.caption || ''}
                  className="h-40 w-full object-cover"
                />
                {photo.isPrimary ? (
                  <span
                    className="absolute left-2 top-2 rounded-full px-2 py-0.5 text-[10px] font-semibold"
                    style={{ background: GOLD, color: '#090807' }}
                  >
                    {t('companyPage.gallery.primary')}
                  </span>
                ) : null}
              </div>
              <div className="space-y-2 p-3">
                <input
                  className="w-full rounded-md border bg-transparent px-2 py-1 text-sm"
                  style={{ borderColor: 'rgba(201,168,76,0.3)', color: 'inherit' }}
                  placeholder={t('companyPage.gallery.caption')}
                  defaultValue={photo.caption ?? ''}
                  onBlur={(e) => {
                    const value = e.target.value;
                    if (value !== (photo.caption ?? '')) {
                      update.mutate({ photoId: photo.id, caption: value });
                    }
                  }}
                />
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <button
                    type="button"
                    disabled={busy || index === 0}
                    onClick={() => move(index, -1)}
                    className="rounded-full border px-2 py-1 disabled:opacity-40"
                    style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    disabled={busy || index === photos.length - 1}
                    onClick={() => move(index, 1)}
                    className="rounded-full border px-2 py-1 disabled:opacity-40"
                    style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}
                  >
                    ↓
                  </button>
                  {!photo.isPrimary ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => setPrimary.mutate(photo.id)}
                      className="rounded-full border px-2 py-1 disabled:opacity-40"
                      style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}
                    >
                      {t('companyPage.gallery.makePrimary')}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => remove.mutate(photo.id)}
                    className="ml-auto rounded-full border px-2 py-1 disabled:opacity-40"
                    style={{ borderColor: 'rgba(232,165,152,0.4)', color: DANGER }}
                  >
                    {t('companyPage.gallery.delete')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4">
        <input
          ref={fileInput}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          className="hidden"
          onChange={onPickFile}
        />
        <button
          type="button"
          disabled={full || uploading}
          onClick={() => fileInput.current?.click()}
          className="rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-50"
          style={{ background: GOLD, color: '#090807' }}
        >
          {uploading
            ? t('companyPage.gallery.uploading')
            : full
              ? t('companyPage.gallery.full')
              : t('companyPage.gallery.add')}
        </button>
      </div>
    </section>
  );
}
