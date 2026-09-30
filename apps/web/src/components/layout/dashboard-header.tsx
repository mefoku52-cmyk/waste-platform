'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUnreadCount } from '@/features/chat';
import { useLogout, useCurrentUser, useIsPlatformAdmin } from '@/features/auth';
import { useT } from '@/lib/i18n/context';
import { LanguageSwitcher } from '@/components/language-switcher';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

const NAV_KEYS = ['overview', 'listings', 'companies', 'documents', 'inquiries', 'chat'] as const;

const NAV_HREFS: Record<string, string | undefined> = {
  overview: '/dashboard',
  listings: '/dashboard/listings',
  companies: '/dashboard/companies',
  documents: '/dashboard/documents',
  inquiries: '/dashboard/inquiries',
  chat: '/dashboard/chat',
};

const NAV_LABEL_KEYS: Record<string, string> = {
  overview: 'nav.overview',
  listings: 'nav.listings',
  companies: 'nav.companies',
  documents: 'nav.documents',
  inquiries: 'nav.inquiries',
  chat: 'nav.chat',
};

export function DashboardHeader() {
  const pathname = usePathname();
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const { data: unreadData } = useUnreadCount();
  const unreadChat = Number((unreadData as any)?.unread || 0);
  const isAdmin = useIsPlatformAdmin();
  const myEmail = String((me as any)?.email || (me as any)?.user?.email || '');
  const { mutateAsync: logout, isPending: logoutPending } = useLogout();

  return (
    <header
      className="z-40 border-b backdrop-blur-md"
      style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)', background: 'rgba(9,8,7,0.85)' }}
    >
      {/* Horná lišta: logo + PREČO CMEP text (VRÁTENÉ) */}
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href="/dashboard" className="flex max-w-xl items-start gap-3">
          <img src="/trc-mark.jpg" alt="TRČ" className="h-16 w-16 rounded-2xl object-cover" />
          <div className="rounded-2xl border px-3 py-2" style={{ borderColor: "color-mix(in srgb, #c9a84c 35%, transparent)" }}>
            <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>{t('nav.whyKicker')}</p>
            <p className="mt-1 text-sm leading-snug" style={{ fontFamily: "DM Serif Display, serif", color: GOLD_BRIGHT }}>
              CMEP — Circular Materials Exchange Platform.
            </p>
            <p className="mt-2 text-[11px] leading-relaxed" style={{ color: MUTED }}>
              {t('nav.whyDesc')}
            </p>
          </div>
        </Link>

        <div className="flex flex-wrap items-center gap-2">
          {isAdmin && (
            <Link
              href="/dashboard/admin"
              className="rounded-full border px-3 py-1.5 text-xs font-semibold"
              style={{ borderColor: GOLD, color: GOLD_BRIGHT }}
            >
              ⚙ Admin
            </Link>
          )}
          <LanguageSwitcher />
          {myEmail ? (
            <span className="hidden text-xs sm:inline" style={{ color: MUTED }}>
              {myEmail}
            </span>
          ) : null}
          <button
            type="button"
            onClick={async () => {
              try {
                await logout(undefined as any);
              } finally {
                window.location.href = '/login';
              }
            }}
            disabled={logoutPending}
            className="rounded-full border px-3 py-1.5 text-xs"
            style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: MUTED }}
          >
            {logoutPending ? '...' : t('dashboard.logout')}
          </button>
        </div>
      </div>

      {/* Navigácia: LEN pills (bez akčných tlačidiel, tie sú už dole) */}
      <nav className="mx-auto max-w-6xl px-4 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          {NAV_KEYS.map((k) => {
            const href = NAV_HREFS[k];
            if (!href) return null;
            const label = t(NAV_LABEL_KEYS[k] || k);
            const active = pathname === href || pathname.startsWith(href + '/');
            return (
              <Link
                key={k}
                href={href}
                className="inline-flex items-center gap-1.5 rounded-full border px-4 py-1.5 text-sm font-medium transition-all hover:opacity-90"
                style={{
                  borderColor: active ? GOLD : 'color-mix(in srgb, #c9a84c 30%, transparent)',
                  background: active ? 'color-mix(in srgb, #c9a84c 15%, transparent)' : 'transparent',
                  color: active ? GOLD_BRIGHT : FG,
                }}
              >
                {label}
                {k === 'chat' && unreadChat > 0 && (
                  <span
                    className="inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold"
                    style={{ background: '#c45c4a', color: FG }}
                  >
                    {unreadChat}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
