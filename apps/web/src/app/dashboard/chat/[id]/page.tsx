'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { FormEvent, useEffect, useRef, useState } from 'react';

import { AppShell } from '@/components/layout/app-shell';
import { useMessages, useMarkRead, useSendMessage } from '@/features/chat';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
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
  const params = useParams<{ id: string }>();
  const id = String(params?.id || '');
  const { t } = useT();
  const [draft, setDraft] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const messagesQuery = useMessages(id) as { data?: unknown; isLoading?: boolean };
  const sendMutation = useSendMessage(id);
  const markReadMutation = useMarkRead();

  const raw = messagesQuery.data as { items?: Message[]; data?: Message[] | { items?: Message[] } } | Message[] | undefined;
  const items = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  useEffect(() => {
    if (id) markReadMutation.mutate(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [items.length]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;

    setErrorMessage('');

    try {
      await sendMutation.mutateAsync(body);
      setDraft('');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t('common.error'));
    }
  }

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link href="/dashboard/chat" className="inline-flex rounded-full border px-3 py-1.5 text-sm" style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}>
          ← {t('common.back')}
        </Link>

        <p className="mt-6 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('chat.conversation')}
        </p>
        <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>{t('chat.title')}</h1>

        <section className="cmep-panel mt-6 rounded-2xl p-4 sm:p-5">
          {messagesQuery.isLoading ? (
            <p className="text-sm" style={{ color: MUTED }}>{t('chat.loading')}</p>
          ) : items.length === 0 ? (
            <p className="py-8 text-center text-sm" style={{ color: MUTED }}>{t('chat.empty')}</p>
          ) : (
            <div className="space-y-3">
              {items.map((message) => {
                const date = message.createdAt || message.created_at;
                const sender = message.senderUserId || message.sender_user_id || '';

                return (
                  <article key={message.id} className="rounded-xl border border-[rgba(201,168,76,0.18)] bg-black/20 p-3">
                    <div className="flex justify-between gap-3 text-xs" style={{ color: MUTED }}>
                      <span className="truncate" style={{ color: GOLD_BRIGHT }}>{sender ? `${sender.slice(0, 8)}…` : t('chat.firm')}</span>
                      <span>{date ? new Date(date).toLocaleString() : ''}</span>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.body || ''}</p>
                  </article>
                );
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <form onSubmit={onSubmit} className="mt-4 grid gap-3">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={t('chat.sendPlaceholder')}
            rows={3}
            disabled={sendMutation.isPending}
            className="rounded-xl border border-[rgba(201,168,76,0.3)] bg-[#100f0c] px-4 py-3 text-sm text-[#f3ead8] outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={sendMutation.isPending || !draft.trim()}
            className="justify-self-start rounded-full border px-4 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ borderColor: 'rgba(201,168,76,0.55)', background: 'rgba(201,168,76,0.12)', color: GOLD_BRIGHT }}
          >
            {sendMutation.isPending ? t('chat.sending') : t('chat.send')}
          </button>
          {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
        </form>
      </div>
    </AppShell>
  );
}
