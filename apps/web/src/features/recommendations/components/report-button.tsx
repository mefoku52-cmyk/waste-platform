'use client';

import { useState } from 'react';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';
import { useT } from '@/lib/i18n/context';

const REASONS = [
  { id: 'harassment', key: 'report.reasonHarassment' },
  { id: 'fake', key: 'report.reasonFake' },
  { id: 'spam', key: 'report.reasonSpam' },
] as const;

export function ReportButton({
  listingId,
  companyId,
}: {
  listingId?: string;
  companyId?: string;
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState('');

  async function send(reason: string) {
    setErr('');
    const token = tokenStore.getToken();
    const res = await fetch(`${config.apiBaseUrl}/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        eventType: 'user_reported',
        listingId: listingId || null,
        companyId: companyId || null,
        payload: { reason },
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setErr(String(body.detail || body.message || t('report.sendFailed')));
      return;
    }
    setDone(true);
    setOpen(false);
  }

  if (done) {
    return <p className="text-xs text-[#cbb98a]">{t('report.done')}</p>;
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        className="text-xs uppercase tracking-[0.16em] text-[#c45c4a]"
        onClick={() => setOpen((v) => !v)}
      >
        {t('report.button')}
      </button>
      {open && (
        <div className="mt-2 flex flex-wrap gap-2">
          {REASONS.map((r) => (
            <button
              key={r.id}
              type="button"
              className="rounded-full border border-[#c45c4a]/50 px-3 py-1 text-xs text-[#f3ead8]"
              onClick={() => send(r.id)}
            >
              {t(r.key)}
            </button>
          ))}
        </div>
      )}
      {err ? <p className="mt-2 text-xs text-red-300">{err}</p> : null}
    </div>
  );
}
