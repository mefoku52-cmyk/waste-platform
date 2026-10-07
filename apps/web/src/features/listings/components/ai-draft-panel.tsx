'use client';

import { useState } from 'react';
import { listingsApi, type AiDraftData } from '../api';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const BG = '#0b0b0b';
const FG = '#f3ead8';
const OK = '#5fd17a';
const DANGER = '#f0bbb0';

type Props = {
  onGenerated: (data: AiDraftData) => void;
};

export function AiDraftPanel({ onGenerated }: Props) {
  const { t } = useT();
  const [prompt, setPrompt] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastProvider, setLastProvider] = useState<string | null>(null);

  async function generate() {
    const text = prompt.trim();
    if (text.length < 3) {
      setErr(t('listings.aiDraft.tooShort'));
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const res = await listingsApi.aiDraft(text);
      onGenerated(res.data);
      setLastProvider(res.provider);
    } catch (e: any) {
      const status = e?.status;
      if (status === 403) {
        setErr(t('listings.aiDraft.tierRequired'));
      } else {
        setErr(e?.message || t('listings.aiDraft.error'));
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="mb-6 rounded-2xl border p-4 sm:p-5"
      style={{ borderColor: 'rgba(201,168,76,0.35)', background: 'rgba(201,168,76,0.04)' }}
    >
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
        {t('listings.aiDraft.kicker')}
      </p>
      <h3 className="text-lg" style={{ color: GOLD_BRIGHT, fontFamily: 'DM Serif Display, serif' }}>
        {t('listings.aiDraft.title')}
      </h3>
      <p className="mt-1 text-sm" style={{ color: MUTED }}>
        {t('listings.aiDraft.desc')}
      </p>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        maxLength={2000}
        placeholder={t('listings.aiDraft.placeholder')}
        disabled={busy}
        className="mt-3 w-full resize-none rounded-xl border p-3 text-sm outline-none"
        style={{ borderColor: 'rgba(201,168,76,0.25)', background: BG, color: FG }}
      />

      <div className="mt-3 flex items-center justify-between gap-3">
        <span className="text-[10px]" style={{ color: MUTED }}>
          {prompt.length}/2000
        </span>
        <button
          type="button"
          onClick={generate}
          disabled={busy || prompt.trim().length < 3}
          className="rounded-full px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
          style={{ background: GOLD, color: '#090807' }}
        >
          {busy ? t('listings.aiDraft.generating') : `✨ ${t('listings.aiDraft.button')}`}
        </button>
      </div>

      {err ? (
        <p className="mt-3 text-xs" style={{ color: DANGER }}>
          {err}
        </p>
      ) : null}
      {lastProvider === 'fallback' && !err ? (
        <p className="mt-3 text-xs" style={{ color: OK }}>
          {t('listings.aiDraft.fallbackUsed')}
        </p>
      ) : null}
    </div>
  );
}
