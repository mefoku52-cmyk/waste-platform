'use client';

import { useEffect, useRef, useState } from 'react';
import { listingsApi, type AiDraftData } from '../api';
import { useT } from '@/lib/i18n/context';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';
import { personaStore, type Persona } from '@/features/agent-platform/lib/persona-store';
import { PersonaPicker } from '@/features/agent-platform/components/persona-picker';

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
  const [typed, setTyped] = useState('');
  const [persona, setPersona] = useState<Persona>('bystry');
  const bufferRef = useRef('');
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    setPersona(personaStore.get());
  }, []);

  // A4: typing efekt — postupne prelevame buffer do zobrazeneho textu
  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => {
      const buf = bufferRef.current;
      if (buf.length > 0) {
        const step = Math.min(3, buf.length);
        setTyped((prev) => prev + buf.slice(0, step));
        bufferRef.current = buf.slice(step);
      }
    }, 30);
    return () => window.clearInterval(timer);
  }, [busy]);

  function stop() {
    abortRef.current?.abort();
    setBusy(false);
  }

  async function generate() {
    const text = prompt.trim();
    if (text.length < 3) {
      setErr(t('listings.aiDraft.tooShort'));
      return;
    }
    setBusy(true);
    setErr(null);
    setTyped('');
    bufferRef.current = '';
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const token = tokenStore.getToken();
      const res = await fetch(`${config.apiBaseUrl}/listings/ai-draft/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ prompt: text, persona }),
        signal: controller.signal,
      });

      // FIX bug #1: BE vracia 409 (ConflictDomainError), nie 403
      if (res.status === 409) {
        throw { status: 409, message: 'ai_tier_required' };
      }
      if (!res.ok || !res.body) {
        throw { status: res.status, message: 'stream_failed' };
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let leftover = '';

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        leftover += decoder.decode(value, { stream: true });
        const lines = leftover.split('\n');
        leftover = lines.pop() ?? '';
        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;
          let event: any;
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }
          if (event.error) throw { status: 0, message: event.error };
          if (event.delta) bufferRef.current += event.delta;
          if (event.done && event.listing) {
            onGenerated(event.listing as AiDraftData);
            setLastProvider(event.provider ?? 'groq');
          }
        }
      }
    } catch (e: any) {
      if (e?.name === 'AbortError' || e?.message === 'AbortError') {
        // Stop tlacidlo — ticho
      } else if (e?.status === 409) {
        setErr(t('listings.aiDraft.tierRequired'));
      } else {
        // A2.4 fallback: klasicky ne-stream endpoint
        try {
          const res = await listingsApi.aiDraft(text, persona);
          onGenerated(res.data);
          setLastProvider(res.provider);
        } catch (e2: any) {
          const s2 = e2?.status;
          setErr(
            s2 === 409
              ? t('listings.aiDraft.tierRequired')
              : e2?.message || t('listings.aiDraft.error'),
          );
        }
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
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

      <div className="mt-3 flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider" style={{ color: MUTED }}>
          Persona
        </span>
        <PersonaPicker
          current={persona}
          onChange={(p) => {
            setPersona(p);
            personaStore.set(p);
          }}
        />
      </div>

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

      {busy ? (
        <div className="mt-3 rounded-xl border p-3 text-sm" style={{ borderColor: 'rgba(201,168,76,0.25)', background: BG }}>
          <p style={{ color: MUTED }}>
            <span style={{ color: GOLD }}>✦</span> AI píše
            <span className="animate-pulse">▌</span>
          </p>
          <p className="mt-1 whitespace-pre-wrap" style={{ color: FG }}>
            {typed}
          </p>
          <div className="mt-2 h-1 w-full overflow-hidden rounded" style={{ background: 'rgba(201,168,76,0.15)' }}>
            <div className="h-1 animate-pulse rounded" style={{ width: '40%', background: GOLD }} />
          </div>
          <button
            type="button"
            onClick={stop}
            className="mt-2 rounded-full px-3 py-1 text-xs font-semibold"
            style={{ border: `1px solid ${GOLD}`, color: GOLD }}
          >
            Stop
          </button>
        </div>
      ) : null}

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
