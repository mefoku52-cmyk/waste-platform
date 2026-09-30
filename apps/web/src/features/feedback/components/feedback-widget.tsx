'use client';

import { useState } from 'react';
import { http } from '@/lib/api/http';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#0d0c09';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const OK = '#6ee7a7';
const DANGER = '#f0bbb0';

export function FeedbackWidget() {
  const { data: me } = useCurrentUser();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  if (!me || !(me as any).id) return null;

  async function send() {
    const t = text.trim();
    if (t.length < 3) {
      setErr('Napíš aspoň 3 znaky.');
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      await http.post('/events', {
        eventType: 'user_feedback',
        payload: t.slice(0, 2000),
      });
      setMsg('Ďakujeme! Tvoja pripomienka je u nás.');
      setText('');
      setTimeout(() => {
        setOpen(false);
        setMsg(null);
      }, 2500);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Odoslanie zlyhalo');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {/* Floating button — vlavo dole, aby nekolidoval s AI chatom (vpravo dole) */}
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          title="Čo by si pridal na platforme?"
          className="fixed z-40 rounded-full px-4 py-3 text-sm font-semibold shadow-lg"
          style={{
            left: '16px',
            bottom: '16px',
            background: GOLD,
            color: BG,
            boxShadow: '0 4px 16px rgba(201,168,76,0.35)',
          }}
        >
          💬 Nápad?
        </button>
      ) : null}

      {/* Panel */}
      {open ? (
        <div
          className="fixed z-40 w-80 rounded-2xl border p-4 shadow-2xl"
          style={{
            left: '16px',
            bottom: '16px',
            background: BG,
            borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
            color: FG,
          }}
        >
          <div className="mb-3 flex items-start justify-between">
            <div>
              <p
                className="text-[10px] uppercase tracking-[0.25em]"
                style={{ color: GOLD }}
              >
                FEEDBACK
              </p>
              <p
                className="text-base"
                style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
              >
                Čo by si pridal?
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                setMsg(null);
                setErr(null);
              }}
              className="text-lg leading-none"
              style={{ color: MUTED }}
            >
              ×
            </button>
          </div>

          <p className="mb-3 text-xs" style={{ color: MUTED }}>
            Napíš čo ti chýba, čo by si zlepšil, alebo čo by pomohlo tvojej firme.
          </p>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            maxLength={2000}
            placeholder="Napr. Chýba mi mapa dodávateľov v okolí…"
            className="w-full resize-none rounded-lg border p-3 text-sm outline-none"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
              background: '#0b0b0b',
              color: FG,
            }}
          />

          <div className="mt-3 flex items-center justify-between">
            <span className="text-[10px]" style={{ color: MUTED }}>
              {text.length}/2000
            </span>
            <button
              type="button"
              onClick={() => void send()}
              disabled={busy || text.trim().length < 3}
              className="rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: GOLD, color: BG }}
            >
              {busy ? 'Posielam…' : 'Poslať'}
            </button>
          </div>

          {err ? (
            <p className="mt-2 text-xs" style={{ color: DANGER }}>
              {err}
            </p>
          ) : null}
          {msg ? (
            <p className="mt-2 text-xs" style={{ color: OK }}>
              {msg}
            </p>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
