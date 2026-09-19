'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { useMessages, useSendMessage, useMarkRead } from '@/features/chat';
import { useParams } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

type Message = {
  id: string;
  body?: string;
  senderUserId?: string;
  sender_user_id?: string;
  createdAt?: string;
  created_at?: string;
};

export default function ChatThreadPage() {
  const params = useParams();
  const id = String(params?.id || '');
  const [draft, setDraft] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useMessages(id);
  const sendMutation = useSendMessage(id);
  const markReadMutation = useMarkRead();

  // Auto-scroll na koniec pri nových správach
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [data]);

  // Mark as read pri otvorení
  useEffect(() => {
    if (id) {
      markReadMutation.mutate(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const raw: any = data;
  const items: Message[] = Array.isArray(raw)
    ? raw
    : raw?.items ?? raw?.data?.items ?? raw?.data ?? [];

  const onSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = draft.trim();
    if (!body) return;
    setErrorMsg(null);
    try {
      await sendMutation.mutateAsync(body);
      setDraft('');
    } catch (err: any) {
      setErrorMsg(err?.message || 'Odoslanie zlyhalo');
    }
  };

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto flex max-w-4xl flex-col px-4 py-10">
          <div className="mb-6 flex items-center gap-3">
            <Link
              href="/dashboard/chat"
              className="text-sm underline underline-offset-4"
              style={{ color: MUTED }}
            >
              ← Späť
            </Link>
          </div>
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            KONVERZÁCIA
          </p>
          <h1 className="mb-8 text-3xl md:text-4xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Chat
          </h1>

          <div
            className="flex-1 space-y-3 overflow-y-auto rounded-2xl border p-5"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)',
              minHeight: '50vh',
              maxHeight: '65vh',
            }}
          >
            {isLoading ? (
              <p style={{ color: MUTED }}>Načítavam…</p>
            ) : items.length === 0 ? (
              <p className="text-center text-sm" style={{ color: MUTED }}>
                Zatiaľ žiadne správy.
              </p>
            ) : (
              items.map((m) => {
                const body = m.body ?? '';
                const at = m.createdAt ?? m.created_at;
                const sender = m.senderUserId ?? m.sender_user_id ?? '';
                return (
                  <div
                    key={m.id}
                    className="rounded-xl border p-3"
                    style={{
                      borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)',
                      background: 'rgba(201,168,76,0.03)',
                    }}
                  >
                    <div className="flex items-center justify-between text-xs" style={{ color: MUTED }}>
                      <span style={{ color: GOLD_BRIGHT }}>{sender.slice(0, 8)}…</span>
                      {at && <span>{new Date(at).toLocaleString()}</span>}
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm" style={{ color: FG }}>
                      {body}
                    </p>
                  </div>
                );
              })
            )}
            <div ref={bottomRef} />
          </div>

          {errorMsg && (
            <p className="mt-3 text-sm" style={{ color: '#e8a598' }}>
              {errorMsg}
            </p>
          )}

          <form onSubmit={onSend} className="mt-4 grid gap-3">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Napíš správu…"
              rows={3}
              disabled={sendMutation.isPending}
              className="rounded-md border bg-transparent px-4 py-3 outline-none disabled:opacity-50"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            />
            <button
              type="submit"
              disabled={sendMutation.isPending || !draft.trim()}
              className="justify-self-start rounded-md px-6 py-3 text-sm font-semibold disabled:opacity-50"
              style={{ background: GOLD, color: BG }}
            >
              {sendMutation.isPending ? 'Odosielam…' : 'Odoslať'}
            </button>
          </form>
        </main>

        <DashboardFooter />
      </div>
    </>
  );
}
