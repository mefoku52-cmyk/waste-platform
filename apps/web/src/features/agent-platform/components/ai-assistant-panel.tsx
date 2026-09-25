'use client';

import { useState } from 'react';
import { http } from '@/lib/api/http';

type ChatResponse = {
  status: string;
  reply: string | null;
  source: string;
};

type Props = {
  listingId?: string;
  listingTitle?: string;
};

export function AiAssistantPanel({ listingId, listingTitle }: Props) {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [reply, setReply] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const text = message.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setReply(null);
    setUnavailable(false);
    try {
      const res = await http.post<ChatResponse>('/agent-platform/chat', {
        message: text,
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
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: '#c9a84c' }}>
        AI asistent
      </p>
      <h2 className="mt-1 font-serif text-2xl" style={{ color: '#e8d48b' }}>
        Opýtaj sa na ponuku
      </h2>
      <p className="mt-1 text-sm" style={{ color: '#9a8f7c' }}>
        {listingTitle ? `Kontext: ${listingTitle}` : 'Bez kontextu ponuky.'}
      </p>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Napíš otázku..."
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
          onClick={send}
          disabled={busy || !message.trim()}
          className="rounded-full border px-4 py-1.5 text-sm disabled:opacity-40"
          style={{ borderColor: 'rgba(201,168,76,0.5)', color: '#e8d48b' }}
        >
          {busy ? 'Posielam…' : 'Poslať'}
        </button>
        {listingId ? (
          <span className="text-[10px] uppercase tracking-[0.18em]" style={{ color: '#9a8f7c' }}>
            listing {listingId.slice(0, 8)}
          </span>
        ) : null}
      </div>

      {reply ? (
        <div className="mt-4 rounded-xl border p-4 text-sm whitespace-pre-wrap"
             style={{ borderColor: 'rgba(201,168,76,0.25)', color: '#f3e6c4' }}>
          {reply}
        </div>
      ) : null}

      {unavailable ? (
        <div className="mt-4 rounded-xl border p-3 text-xs"
             style={{ borderColor: 'rgba(196,92,74,0.5)', color: '#f0bbb0' }}>
          AI asistent je momentálne nedostupný (chýba GROQ_API_KEY alebo služba neodpovedá).
        </div>
      ) : null}

      {error ? (
        <p className="mt-2 text-xs" style={{ color: '#f0bbb0' }}>{error}</p>
      ) : null}
    </section>
  );
}
