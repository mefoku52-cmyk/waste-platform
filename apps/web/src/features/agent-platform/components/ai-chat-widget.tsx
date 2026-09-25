'use client';

import { useEffect, useRef, useState } from 'react';
import { http } from '@/lib/api/http';

type Msg = { role: 'user' | 'ai'; text: string };
type ChatResponse = { status: string; reply: string | null; source: string };

type Props = {
  listingId?: string;
  listingTitle?: string;
};

export function AiChatWidget({ listingId, listingTitle }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([
        {
          role: 'ai',
          text: listingTitle
            ? `Ahoj. Pýtaj sa ma na ponuku "${listingTitle}". S čím pomôžem?`
            : 'Ahoj. S čím ti pomôžem?',
        },
      ]);
    }
  }, [open, listingTitle, messages.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    setBusy(true);
    try {
      const res = await http.post<ChatResponse>('/agent-platform/chat', { message: text });
      if (res?.status === 'ok' && res.reply) {
        setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);
      } else {
        setMessages((m) => [
          ...m,
          { role: 'ai', text: 'AI je momentálne nedostupná (chýba GROQ_API_KEY alebo služba neodpovedá).' },
        ]);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Chyba spojenia';
      setMessages((m) => [...m, { role: 'ai', text: `Chyba: ${msg}` }]);
    } finally {
      setBusy(false);
    }
  }

  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  return (
    <>
      {/* Plavajuce tlacidlo vpravo dole */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Otvoriť AI chat"
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-2xl transition hover:scale-105"
          style={{ background: '#c9a84c', color: '#0b0b0b' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {/* Chat okno */}
      {open && (
        <div
          className="fixed bottom-6 right-6 z-50 flex h-[520px] w-[360px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border shadow-2xl"
          style={{ borderColor: 'rgba(201,168,76,0.35)', background: '#0b0b0b' }}
        >
          {/* Hlavicka */}
          <div className="flex items-center justify-between border-b px-4 py-3"
               style={{ borderColor: 'rgba(201,168,76,0.25)' }}>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: '#c9a84c' }}>
                AI asistent
              </p>
              <p className="text-xs" style={{ color: '#9a8f7c' }}>
                {listingTitle ? listingTitle.slice(0, 40) : 'CMEP'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full px-2 text-lg"
              style={{ color: '#9a8f7c' }}
              aria-label="Zavrieť"
            >
              ×
            </button>
          </div>

          {/* Spravy */}
          <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`max-w-[85%] whitespace-pre-wrap break-words rounded-xl px-3 py-2 text-sm ${
                  m.role === 'user' ? 'ml-auto' : ''
                }`}
                style={
                  m.role === 'user'
                    ? { background: '#c9a84c', color: '#0b0b0b' }
                    : { background: '#17140d', color: '#f3e6c4' }
                }
              >
                {m.text}
              </div>
            ))}
            {busy && (
              <div className="max-w-[85%] rounded-xl px-3 py-2 text-sm"
                   style={{ background: '#17140d', color: '#9a8f7c' }}>
                píšem…
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Vstup */}
          <div className="border-t p-3" style={{ borderColor: 'rgba(201,168,76,0.25)' }}>
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Napíš správu… (Enter = odoslať)"
                rows={1}
                disabled={busy}
                className="flex-1 resize-none rounded-lg border p-2 text-sm"
                style={{
                  borderColor: 'rgba(201,168,76,0.25)',
                  background: '#0b0b0b',
                  color: '#f3e6c4',
                  maxHeight: '100px',
                }}
              />
              <button
                type="button"
                onClick={() => void send()}
                disabled={busy || !input.trim()}
                className="rounded-lg px-3 py-2 text-sm font-semibold disabled:opacity-40"
                style={{ background: '#c9a84c', color: '#0b0b0b' }}
              >
                ➤
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
