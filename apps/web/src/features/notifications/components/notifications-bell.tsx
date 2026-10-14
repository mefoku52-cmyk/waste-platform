'use client';

import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { useNotifications } from '@/features/notifications/hooks/use-notifications';
import { useUnreadNotifications } from '@/features/notifications/hooks/use-unread-count';
import { notificationsApi } from '@/features/notifications/api';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

export function NotificationsBell() {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { data: unreadData } = useUnreadNotifications();
  const { data, isLoading } = useNotifications();
  const unread = Number((unreadData as any)?.unread ?? 0);
  const items = (data as any)?.items ?? [];

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const markRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread'] });
    } catch {
      // ticho — chyba sieťe nesmie zrútiť dropdown
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label={t('notifications.title')}
        onClick={() => setOpen((v) => !v)}
        className="relative rounded-full border px-3 py-1.5 text-sm"
        style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: '#f3ead8' }}
      >
        🔔
        {unread > 0 && (
          <span
            className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[10px] font-bold"
            style={{ background: GOLD, color: '#090807' }}
          >
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border shadow-2xl"
          style={{ background: 'rgba(14,12,10,0.98)', borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
        >
          <div className="flex items-center justify-between border-b px-4 py-3" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
            <h2 className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
              {t('notifications.title')}
            </h2>
            <span className="text-xs" style={{ color: MUTED }}>{items.length}</span>
          </div>

          {isLoading ? (
            <div className="px-4 py-6 text-center text-sm" style={{ color: MUTED }}>
              {t('notifications.loading')}
            </div>
          ) : items.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm" style={{ color: MUTED }}>
              {t('notifications.empty')}
            </div>
          ) : (
            <ul className="max-h-80 divide-y overflow-y-auto" style={{ borderColor: 'color-mix(in srgb, #9a8f7c 12%, transparent)' }}>
              {items.map((n: any) => {
                const isRead = n.isRead ?? n.is_read;
                return (
                  <li key={n.id}>
                    <button
                      type="button"
                      onClick={() => !isRead && markRead(n.id)}
                      className="w-full px-4 py-3 text-left transition hover:bg-white/5"
                      style={{ opacity: isRead ? 0.6 : 1 }}
                    >
                      <div className="text-sm font-medium" style={{ color: '#f3ead8' }}>{n.title}</div>
                      <div className="mt-0.5 text-xs" style={{ color: MUTED }}>{n.message}</div>
                      <div className="mt-1 text-[10px] uppercase tracking-wide" style={{ color: isRead ? MUTED : GOLD }}>
                        {n.type}
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}