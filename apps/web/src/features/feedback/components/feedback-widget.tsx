'use client';

import { useState } from 'react';
import { http } from '@/lib/api/http';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#0d0c09';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const OK = '#6ee7a7';
const DANGER = '#f0bbb0';

export function FeedbackWidget() {
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  if (!me || !(me as any).id) return null;

  async function send() {
    const trimmed = text.trim();
    if (trimmed.length < 3) {
      setErr(t('feedback.errorShort'));
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      await http.post('/events', {
        eventType: 'user_feedback',
        payload: trimmed.slice(0, 2000),
      });
      setMsg(t('feedback.thanks'));
      setText('');
      setTimeout(() => {
        setOpen(false);
        setMsg(null);
      }, 2500);
    } catch (e) {
      setErr(e instanceof Error ? e.message : t('feedback.error'));
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
          title={t('feedback.tooltip')}
          className="fixed z-40 rounded-full px-4 py-3 text-sm font-semibold shadow-lg"
          style={{
            left: '16px',
            bottom: '16px',
            background: GOLD,
            color: BG,
            boxShadow: '0 4px 16px rgba(201,168,76,0.35)',
          }}
        >
          {t('feedback.button')}
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
                {t('feedback.widgetTitle')}
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
            {t('feedback.desc')}
          </p>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            maxLength={2000}
            placeholder={t('feedback.placeholder')}
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
              {busy ? t('feedback.sending') : t('feedback.send')}
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
