'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { ChatDraftBanner } from '@/features/recommendations/components/chat-draft-banner';
import { ReportButton } from '@/features/recommendations/components/report-button';
import { useThreads } from '@/features/chat';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type Thread = {
  id: string;
  lastMessage?: string | null;
  unreadCount?: number;
  subject?: string;
};

export default function ChatPage() {
  const { t } = useT();
  const query = useThreads() as { data?: unknown; isLoading?: boolean; error?: unknown };
  const raw = query.data as { items?: Thread[]; data?: Thread[] | { items?: Thread[] } } | Thread[] | undefined;
  const items = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <ChatDraftBanner />

        <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
              {t('chat.section')}
            </p>
            <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('chat.title')}
            </h1>
          </div>
          <ReportButton />
        </div>

        <div className="mt-7">
          {query.isLoading ? (
            <p className="text-sm" style={{ color: MUTED }}>{t('chat.loading')}</p>
          ) : query.error ? (
            <p className="rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-red-200">
              {t('chat.loadError')}
            </p>
          ) : items.length === 0 ? (
            <section className="cmep-panel rounded-2xl px-5 py-14 text-center">
              <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('chat.empty')}</h2>
              <p className="mt-2 text-sm" style={{ color: MUTED }}>{t('chat.emptyHint')}</p>
            </section>
          ) : (
            <ul className="space-y-3">
              {items.map((thread) => {
                const unread = Number(thread.unreadCount || 0);
                return (
                  <li key={thread.id}>
                    <Link href={`/dashboard/chat/${thread.id}`} className="cmep-card block rounded-2xl p-4 sm:p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <h2 className="truncate font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                            {thread.subject || t('chat.firm')}
                          </h2>
                          <p className="mt-2 line-clamp-2 text-sm leading-5" style={{ color: MUTED }}>
                            {thread.lastMessage || '—'}
                          </p>
                        </div>
                        {unread > 0 ? (
                          <span className="rounded-full bg-[#c45c4a] px-2 py-0.5 text-xs font-bold text-white">{unread}</span>
                        ) : null}
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}
