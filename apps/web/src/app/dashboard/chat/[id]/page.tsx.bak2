'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { useQuery } from '@tanstack/react-query';
import { http } from '@/lib/api/http';
import { useParams } from 'next/navigation';
import { useState } from 'react';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

type Message = {
  id: string;
  body?: string;
  content?: string;
  sender_name?: string;
  senderName?: string;
  created_at?: string;
  createdAt?: string;
};

export default function ChatThreadPage() {
  const params = useParams();
  const id = String(params?.id || '');
  const [draft, setDraft] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['chat-thread', id],
    queryFn: () => http.get<any>(`/chat/threads/${id}/messages`),
    enabled: !!id,
  });

  const raw: any = data;
  const items: Message[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto flex max-w-4xl flex-col px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            KONVERZÁCIA
          </p>
          <h1 className="mb-8 text-3xl md:text-4xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Chat
          </h1>

          <div
            className="flex-1 space-y-3 rounded-2xl border p-5"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)', minHeight: '50vh' }}
          >
            {isLoading ? (
              <p style={{ color: MUTED }}>Načítavam…</p>
            ) : items.length === 0 ? (
              <p className="text-center text-sm" style={{ color: MUTED }}>
                Zatiaľ žiadne správy.
              </p>
            ) : (
              items.map((m) => {
                const body = m.body ?? m.content ?? '';
                const sender = m.sender_name ?? m.senderName ?? 'Firma';
                const at = m.created_at ?? m.createdAt;
                return (
                  <div key={m.id} className="rounded-xl border p-3"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)', background: 'rgba(201,168,76,0.03)' }}>
                    <div className="flex items-center justify-between text-xs" style={{ color: MUTED }}>
                      <span style={{ color: GOLD_BRIGHT }}>{sender}</span>
                      {at && <span>{new Date(at).toLocaleString('sk-SK')}</span>}
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm" style={{ color: FG }}>
                      {body}
                    </p>
                  </div>
                );
              })
            )}
          </div>

          <form
            onSubmit={(e) => { e.preventDefault(); setDraft(''); }}
            className="mt-4 grid gap-3"
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Napíš správu…"
              rows={3}
              className="rounded-md border bg-transparent px-4 py-3 outline-none"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }}
            />
            <button
              type="submit"
              className="justify-self-start rounded-md px-6 py-3 text-sm font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              Odoslať
            </button>
          </form>
        </main>

      <DashboardFooter />
      </div>
    </>
  );
}
