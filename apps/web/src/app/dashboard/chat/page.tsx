'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { useT } from '@/lib/i18n/context';
import { useQuery } from '@tanstack/react-query';
import { http } from '@/lib/api/http';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

type Thread = {
  id: string;
  counterpart_name?: string;
  listing_title?: string;
  last_message?: string;
  unread_count?: number;
};

export default function ChatPage() {
  const { t } = useT();
  const { data, isLoading } = useQuery({
    queryKey: ['chat-threads'],
    queryFn: () => http.get<any>('/chat/threads'),
  });

  const raw: any = data;
  const items: Thread[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-4xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            {t('chat.section')}
          </p>
          <h1 className="mb-10 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            {t('chat.title')}
          </h1>

          {isLoading ? (
            <p style={{ color: MUTED }}>{t('chat.loading')}</p>
          ) : items.length === 0 ? (
            <div
              className="rounded-2xl border py-16 text-center"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
            >
              <h3 className="text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>
                {t('chat.empty')}
              </h3>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>
                {t('chat.emptyHint')}
              </p>
            </div>
          ) : (
            <ul className="space-y-3">
              {items.map((thread) => (
                <li key={thread.id}>
                  <Link
                    href={`/dashboard/chat/${thread.id}`}
                    className="block rounded-2xl border p-5 transition-colors hover:bg-white/5"
                    style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <p className="text-lg" style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}>
                          {thread.counterpart_name || t('chat.firm')}
                        </p>
                        {thread.listing_title && (
                          <p className="mt-1 text-xs" style={{ color: FAINT }}>
                            Re: {thread.listing_title}
                          </p>
                        )}
                        <p className="mt-2 line-clamp-1 text-sm" style={{ color: MUTED }}>
                          {thread.last_message || '—'}
                        </p>
                      </div>
                      {thread.unread_count && thread.unread_count > 0 ? (
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-bold"
                          style={{ background: '#c45c4a', color: FG }}
                        >
                          {thread.unread_count}
                        </span>
                      ) : null}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </main>

      <DashboardFooter />
      </div>
    </>
  );
}
