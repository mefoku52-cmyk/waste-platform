'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { http } from '@/lib/api/http';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const BG = '#090807';

type Tier = 'top' | 'gold';

type Props = {
  listingId: string;
  promotedUntil?: string | null;
  promotedTier?: string | null;
};

const TIERS: { key: Tier; days: 7 | 30; price: string; label: string; desc: string }[] = [
  { key: 'top', days: 7, price: '5 €', label: 'TOP 7 dní', desc: 'Ponuka bude navrchu 7 dní.' },
  { key: 'top', days: 30, price: '10 €', label: 'TOP 30 dní', desc: 'Ponuka bude navrchu 30 dní.' },
  { key: 'gold', days: 30, price: '30 €', label: 'GOLD 30 dní', desc: 'Zlatý rámik + navrchu 30 dní.' },
];

export function PromoteListingButton({ listingId, promotedUntil, promotedTier }: Props) {
  const { t } = useT();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const isPromoted = Boolean(promotedUntil && new Date(promotedUntil) > new Date());

  async function promote() {
    setBusy(true);
    setErr(null);
    try {
      const t = TIERS[selected];
      await http.post(`/listings/${listingId}/promote`, { days: t.days, tier: t.key });
      setOpen(false);
      router.refresh();
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('listings.promoteExtended.title');
      setErr(msg);
      setBusy(false);
    }
  }

  async function unpromote() {
    setBusy(true);
    setErr(null);
    try {
      await http.post(`/listings/${listingId}/unpromote`, {});
      setOpen(false);
      router.refresh();
    } catch (e) {
      const msg = e instanceof Error ? e.message : t('listings.promoteExtended.title');
      setErr(msg);
      setBusy(false);
    }
  }

  if (isPromoted) {
    return (
      <div className="rounded-2xl border p-4" style={{ borderColor: GOLD, background: 'rgba(201,168,76,0.08)' }}>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: GOLD }}>
          ⭐ {promotedTier === 'gold' ? 'GOLD' : 'TOP'} {t('listings.promoteExtended.active')}
        </p>
        <p className="mt-1 text-xs" style={{ color: MUTED }}>
          {t('listings.promoteExtended.until')} {new Date(promotedUntil as string).toLocaleDateString()}
        </p>
        <button
          type="button"
          onClick={unpromote}
          disabled={busy}
          className="mt-3 rounded-full border px-3 py-1.5 text-xs transition disabled:opacity-50"
          style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: MUTED }}
        >
          {busy ? t('listings.promoteExtended.loading') : t('listings.promoteExtended.remove')}
        </button>
        {err ? <p className="mt-2 text-xs" style={{ color: '#f0bbb0' }}>{err}</p> : null}
      </div>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-full px-4 py-2 text-sm font-semibold transition hover:opacity-90"
        style={{ background: GOLD, color: BG }}
      >
        ⭐ {t('listings.promoteExtended.title')}
      </button>
    );
  }

  return (
    <div className="rounded-2xl border p-4" style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)' }}>
      <p className="text-sm font-medium" style={{ color: GOLD_BRIGHT }}>
        {t('listings.promoteExtended.title')}
      </p>
      <p className="mt-1 text-xs" style={{ color: MUTED }}>
        {t('listings.promoteExtended.desc')}
      </p>

      <div className="mt-3 space-y-2">
        {TIERS.map((t, i) => (
          <button
            key={`${t.key}-${t.days}`}
            type="button"
            onClick={() => setSelected(i)}
            className="flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition"
            style={{
              borderColor: selected === i ? GOLD : 'color-mix(in srgb, #c9a84c 20%, transparent)',
              background: selected === i ? 'rgba(201,168,76,0.1)' : 'transparent',
              color: '#f3ead8',
            }}
          >
            <span>
              <span className="font-semibold">{t.label}</span>
              <span className="ml-2 text-xs" style={{ color: MUTED }}>{t.desc}</span>
            </span>
            <span className="font-semibold" style={{ color: GOLD_BRIGHT }}>{t.price}</span>
          </button>
        ))}
      </div>

      {err ? <p className="mt-2 text-xs" style={{ color: '#f0bbb0' }}>{err}</p> : null}

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={promote}
          disabled={busy}
          className="rounded-full px-4 py-1.5 text-sm font-semibold transition disabled:opacity-50"
          style={{ background: GOLD, color: BG }}
        >
          {busy ? t('listings.promoteExtended.loading') : t('listings.promoteExtended.activate')}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          disabled={busy}
          className="rounded-full border px-4 py-1.5 text-sm transition"
          style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: MUTED }}
        >
          {t('listings.promoteExtended.cancel')}
        </button>
      </div>
    </div>
  );
}
