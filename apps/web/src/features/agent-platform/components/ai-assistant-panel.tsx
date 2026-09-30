'use client';

import { useState } from 'react';
import { http } from '@/lib/api/http';
import { useT } from '@/lib/i18n/context';

type ChatResponse = {
  status: string;
  reply: string | null;
  source: string;
};

type Props = {
  listingId?: string;
  listingTitle?: string;
};

const TONES = [
  { id: 'vecny', label: 'Vecný' },
  { id: 'strucny', label: 'Stručný' },
  { id: 'formalny', label: 'Formálny' },
  { id: 'drzy', label: 'Drzý' },
  { id: 'lenivy', label: 'Lenivý' },
] as const;

const TONE_PREFIX: Record<string, string> = {
  vecny: 'Odpovedaj vecne, po slovensky.',
  strucny: 'Odpovedaj velmi strucne, po slovensky.',
  formalny: 'Odpovedaj formalne, po slovensky.',
  drzy: 'Odpovedaj sebaisto a priamo, bez urazok, po slovensky.',
  lenivy: 'Odpovedaj kratko, jednoducho, po slovensky.',
};

export function AiAssistantPanel({ listingId, listingTitle }: Props) {
  const { t } = useT();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [reply, setReply] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [minimized, setMinimized] = useState(false);
  const [tone, setTone] = useState<string>('vecny');

  async function send() {
    const text = message.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setReply(null);
    setUnavailable(false);
    const prefix = TONE_PREFIX[tone] || TONE_PREFIX.vecny;
    const context = listingTitle ? ` Kontext ponuky: ${listingTitle}.` : '';
    try {
      const res = await http.post<ChatResponse>('/agent-platform/chat', {
        message: `\( {prefix} \){context} Otazka: ${text}`,
      });
      if (res?.status === 'ok' && res.reply) {
        setReply(res.reply);
        setMessage('');
      } else {
        setUnavailable(true);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Chyba';
      setError(msg);
      setUnavailable(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="cmep-panel mt-6 rounded-2xl p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.22em]"
            style={{ color: '#c9a84c' }}
          >
            AI asistent
          </p>
          <h2 className="mt-1 font-serif text-2xl" style={{ color: '#e8d48b' }}>
            Opýtaj sa na ponuku
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setReply(null);
              setError(null);
              setUnavailable(false);
            }}
            className="rounded-full border px-2 py-1 text-xs"
            style={{ borderColor: 'rgba(201,168,76,0.4)', color: '#e8d48b' }}
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={() => setMinimized((v) => !v)}
            className="rounded-full border px-2 py-1 text-xs"
            style={{ borderColor: 'rgba(201,168,76,0.4)', color: '#e8d48b' }}
          >
            {minimized ? 'Otvoriť' : 'Minimalizovať'}
          </button>
        </div>
      </div>

      {minimized ? (
        <p className="mt-2 text-sm" style={{ color: '#9a8f7c' }}>
          AI okno je zbalené.
        </p>
      ) : (
        <>
          <p className="mt-1 text-sm" style={{ color: '#9a8f7c' }}>
            {listingTitle ? `Kontext: ${listingTitle}` : 'Bez kontextu ponuky.'}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {TONES.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setTone(item.id)}
                className="rounded-full border px-3 py-1 text-xs"
                style={{
                  borderColor:
                    tone === item.id
                      ? 'rgba(201,168,76,0.9)'
                      : 'rgba(201,168,76,0.3)',
                  color: tone === item.id ? '#090807' : '#e8d48b',
                  background: tone === item.id ? '#c9a84c' : 'transparent',
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t('aiAssistant.placeholder')}
            rows={3}
            disabled={busy}
            className="mt-4 w-full rounded-lg border p-3 text-sm"
            style={{
              borderColor: 'rgba(201,168,76,0.25)',
              background: '#0b0b0b',
              color: '#f3e6c4',
            }}
          />
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={() => void send()}
              disabled={busy || !message.trim()}
              className="rounded-full border px-4 py-1.5 text-sm disabled:opacity-40"
              style={{ borderColor: 'rgba(201,168,76,0.5)', color: '#e8d48b' }}
            >
              {busy ? 'Posielam…' : 'Poslať'}
            </button>
          </div>
          {reply ? (
            <div
              className="mt-4 rounded-xl border p-4 text-sm whitespace-pre-wrap"
              style={{ borderColor: 'rgba(201,168,76,0.25)', color: '#f3e6c4' }}
            >
              {reply}
            </div>
          ) : null}
          {unavailable ? (
            <div
              className="mt-4 rounded-xl border p-3 text-xs"
              style={{ borderColor: 'rgba(196,92,74,0.5)', color: '#f0bbb0' }}
            >
              AI asistent je momentálne nedostupný.
            </div>
          ) : null}
          {error ? (
            <p className="mt-2 text-xs" style={{ color: '#f0bbb0' }}>
              {error}
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
