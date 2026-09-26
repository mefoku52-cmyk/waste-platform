'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { listingsApi } from '../api';

const DANGER = '#c45c4a';
const DANGER_TEXT = '#f0bbb0';
const MUTED = '#9a8f7c';

export function DeleteListingButton({ listingId }: { listingId: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function confirmDelete() {
    setBusy(true);
    setErr(null);
    try {
      await listingsApi.deleteListing(listingId);
      router.push('/dashboard/listings');
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Chyba pri mazaní';
      setErr(msg);
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-full border px-4 py-2 text-sm font-medium transition hover:opacity-80"
        style={{ borderColor: DANGER, color: DANGER_TEXT }}
      >
        Zmazať ponuku
      </button>
    );
  }

  return (
    <div
      className="rounded-2xl border p-4"
      style={{ borderColor: DANGER, background: 'rgba(196,92,74,0.08)' }}
    >
      <p className="text-sm font-medium" style={{ color: DANGER_TEXT }}>
        Naozaj zmazať túto ponuku?
      </p>
      <p className="mt-1 text-xs" style={{ color: MUTED }}>
        Akcia sa nedá vrátiť.
      </p>

      {err ? (
        <p className="mt-2 text-xs" style={{ color: DANGER_TEXT }}>{err}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={confirmDelete}
          disabled={busy}
          className="rounded-full px-4 py-1.5 text-sm font-semibold transition disabled:opacity-50"
          style={{ background: DANGER, color: '#fff' }}
        >
          {busy ? 'Mažem…' : 'Áno, zmazať'}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          disabled={busy}
          className="rounded-full border px-4 py-1.5 text-sm transition disabled:opacity-50"
          style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: MUTED }}
        >
          Zrušiť
        </button>
      </div>
    </div>
  );
}
