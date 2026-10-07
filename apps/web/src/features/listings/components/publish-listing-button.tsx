'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { listingsApi } from '../api';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const BG = '#090807';
const MUTED = '#9a8f7c';
const OK = '#5fd17a';
const DANGER = '#f0bbb0';

export function PublishListingButton({ listingId }: { listingId: string }) {
  const { t } = useT();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function publish() {
    setBusy(true);
    setErr(null);
    setOk(false);
    try {
      await listingsApi.publishListing(listingId);
      setOk(true);
      router.refresh();
    } catch (e: any) {
      setErr(e?.message || t('listings.publish.error'));
      setBusy(false);
    }
  }

  if (ok) {
    return (
      <div className="rounded-2xl border p-3 text-sm" style={{ borderColor: OK, color: OK }}>
        {t('listings.publish.success')}
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={publish}
        disabled={busy}
        className="rounded-full px-4 py-2 text-sm font-semibold transition hover:opacity-90 disabled:opacity-50"
        style={{ background: GOLD, color: BG }}
      >
        {busy ? t('listings.publish.sending') : `🚀 ${t('listings.publish.button')}`}
      </button>
      {err ? (
        <p className="mt-2 text-xs" style={{ color: DANGER }}>
          {err}
        </p>
      ) : null}
    </div>
  );
}
