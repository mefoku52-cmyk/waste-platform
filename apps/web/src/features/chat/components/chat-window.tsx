'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { useMessages, useThread } from '../hooks/use-chat-queries';
import { chatApi } from '../api';
import { useCurrentUser } from '../../auth/hooks/use-current-user';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';

function formatTime(iso: string, t: (k: string) => string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const sameDay =
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate();
    const y = new Date(now);
    y.setDate(now.getDate() - 1);
    const isYesterday =
      d.getFullYear() === y.getFullYear() &&
      d.getMonth() === y.getMonth() &&
      d.getDate() === y.getDate();
    const hm = d.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
    if (sameDay) return `${t('chat.today')} ${hm}`;
    if (isYesterday) return `${t('chat.yesterday')} ${hm}`;
    return d.toLocaleDateString() + ' ' + hm;
  } catch {
    return '';
  }
}

export const ChatWindow = ({ threadId }: { threadId: string }) => {
  const { t } = useT();
  const qc = useQueryClient();
  const { data: thread } = useThread(threadId);
  const { data: msgs, isLoading } = useMessages(threadId);
  const { data: me } = useCurrentUser();
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const myId = String((me as any)?.id || (me as any)?.user?.id || '');

  useEffect(() => {
    chatApi.markRead(threadId).catch(() => {});
  }, [threadId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const send = async () => {
    if (!text.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      await chatApi.sendMessage(threadId, text.trim());
      setText('');
      await qc.invalidateQueries({ queryKey: ['chat-messages', threadId] });
      await qc.invalidateQueries({ queryKey: ['chat-threads'] });
    } catch (e: any) {
      setErr(e?.message || t('chat.sendFailed'));
    } finally {
      setBusy(false);
    }
  };

  const items = (msgs as any)?.items ?? [];
  const subject = (thread as any)?.data?.subject || t('chat.conversation');

  return (
    <div
      className="flex h-full flex-col overflow-hidden rounded-2xl border"
      style={{
        borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
        background: 'rgba(9,8,7,0.6)',
      }}
    >
      {/* HEADER */}
      <div
        className="flex items-center gap-3 border-b px-4 py-3 sm:px-5"
        style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
      >
        <Link
          href="/dashboard/chat"
          className="inline-flex h-9 w-9 items-center justify-center rounded-full border text-sm"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
          aria-label={t('chat.back')}
        >
          ←
        </Link>
        <div className="min-w-0 flex-1">
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.22em]"
            style={{ color: GOLD }}
          >
            {t('chat.withCompany')}
          </p>
          <h2
            className="truncate font-serif text-lg leading-tight sm:text-xl"
            style={{ color: GOLD_BRIGHT }}
          >
            {subject}
          </h2>
        </div>
        <div
          className="hidden rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.15em] sm:inline-block"
          style={{
            borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
            color: MUTED,
          }}
        >
          🔒 {t('landing.hiddenContacts')}
        </div>
      </div>

      {/* INFO LINE */}
      <div
        className="border-b px-4 py-2 text-[11px] leading-snug sm:px-5"
        style={{
          borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)',
          color: MUTED,
        }}
      >
        {t('chat.contactHidden')}
      </div>

      {/* MESSAGES */}
      <div className="flex-1 space-y-1 overflow-y-auto px-4 py-4 sm:px-5">
        {isLoading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="h-12 w-2/3 animate-pulse rounded-2xl"
                style={{ background: 'rgba(201,168,76,0.08)' }}
              />
            ))}
            <p className="text-center text-xs" style={{ color: MUTED }}>
              {t('chat.loadingMessages')}
            </p>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div
              className="mb-3 flex h-14 w-14 items-center justify-center rounded-full border-2"
              style={{
                borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)',
                color: GOLD,
                fontFamily: 'DM Serif Display, serif',
                fontSize: '1.5rem',
              }}
            >
              💬
            </div>
            <p className="font-serif text-lg" style={{ color: GOLD_BRIGHT }}>
              {t('chat.emptyMessages')}
            </p>
            <p className="mt-1 text-xs" style={{ color: MUTED }}>
              {t('chat.emptyMessagesHint')}
            </p>
          </div>
        ) : (
          items.map((m: any, idx: number) => {
            const mine = String(m.senderUserId) === myId;
            const prev = idx > 0 ? items[idx - 1] : null;
            const sameSender =
              !!prev && String(prev.senderUserId) === String(m.senderUserId);
            return (
              <div key={m.id} className={sameSender ? 'mt-1' : 'mt-4'}>
                <div
                  className={
                    'max-w-[78%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ' +
                    (mine ? 'ml-auto' : 'mr-auto')
                  }
                  style={
                    mine
                      ? {
                          background: `linear-gradient(135deg, ${GOLD} 0%, ${GOLD_BRIGHT} 100%)`,
                          color: '#090807',
                        }
                      : {
                          background: 'rgba(201,168,76,0.08)',
                          border: '1px solid color-mix(in srgb, #c9a84c 30%, transparent)',
                          color: FG,
                        }
                  }
                >
                  {!sameSender && (
                    <div
                      className={
                        'mb-1 text-[10px] font-semibold uppercase tracking-wider ' +
                        (mine ? 'text-right' : 'text-left')
                      }
                      style={{ color: mine ? 'rgba(9,8,7,0.75)' : GOLD }}
                    >
                      {mine ? 'Vy' : 'Druhá firma'}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap break-words">{m.body}</div>
                  <div
                    className={
                      'mt-1 text-[10px] ' + (mine ? 'text-right' : 'text-left')
                    }
                    style={{ color: mine ? 'rgba(9,8,7,0.65)' : MUTED }}
                  >
                    {formatTime(m.createdAt, t)}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* INPUT */}
      <div
        className="border-t p-3 sm:p-4"
        style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
      >
        {err && (
          <div className="mb-2 text-xs" style={{ color: DANGER }}>
            {err}
          </div>
        )}
        <div className="flex items-end gap-2">
          <textarea
            rows={2}
            placeholder={t('chat.placeholderShort')}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            className="flex-1 resize-none rounded-xl border px-3 py-2 text-sm outline-none"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
              background: '#0b0b0b',
              color: FG,
            }}
          />
          <button
            type="button"
            disabled={busy || !text.trim()}
            onClick={send}
            className="rounded-xl px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
            style={{ background: GOLD, color: '#090807' }}
          >
            {busy ? t('chat.sending') : t('chat.send')}
          </button>
        </div>
      </div>
    </div>
  );
};
