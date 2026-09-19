'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUnreadNotifications } from '@/features/notifications';
import { useLogout, useCurrentUser, useIsPlatformAdmin } from '@/features/auth';
import { useT } from '@/lib/i18n/context';
import { LanguageSwitcher } from '@/components/language-switcher';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

const NAV_KEYS = ['overview', 'listings', 'marketplace', 'matches', 'companies', 'documents', 'chat'] as const;

const NAV_HREFS: Record<string, string | undefined> = {
  overview: '/dashboard',
  listings: '/dashboard/listings',
  companies: '/dashboard/companies',
  documents: '/dashboard/documents',
  chat: '/dashboard/chat',
};

export function DashboardHeader() {
  const pathname = usePathname();
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const { data: unreadData } = useUnreadNotifications();
  const unreadChat = Number((unreadData as any)?.unread || 0);
  const isAdmin = useIsPlatformAdmin();
  const myEmail = String((me as any)?.email || (me as any)?.user?.email || '');
  const { mutateAsync: logout, isPending: logoutPending } = useLogout();

  return (
    <header
      className="sticky top-0 z-40 border-b backdrop-blur-md"
      style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)', background: 'rgba(9,8,7,0.85)' }}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href="/dashboard" className="flex items-center gap-3">
          <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
          <div className="hidden sm:block">
            <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              CMEP · OBEHOVÉ MATERIÁLY
            </p>
            <p className="text-lg leading-none" style={{ fontFamily: 'Fraunces, serif' }}>
              Trhovisko
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/listings"
            className="hidden rounded-md border px-4 py-2 text-sm font-semibold sm:inline-flex"
            style={{ borderColor: GOLD, color: GOLD_BRIGHT }}
          >
            Moje ponuky
          </Link>
          <span className="hidden text-sm md:inline" style={{ color: MUTED }}>
            {myEmail || '—'}
          </span>
          {isAdmin && (
            <Link
              href="/dashboard/admin"
              className="rounded-md border px-3 py-1.5 text-xs font-semibold"
              style={{ borderColor: GOLD, color: GOLD_BRIGHT }}
            >
              ⚙ Admin
            </Link>
          )}
          <LanguageSwitcher />
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
            className="text-sm underline underline-offset-4"
            style={{ color: MUTED }}
          >
            {logoutPending ? '...' : t('dashboard.logout')}
          </button>
        </div>
      </div>

      <nav className="mx-auto flex max-w-6xl flex-wrap gap-5 px-4 pb-3">
        {NAV_KEYS.map((k) => {
          const href = NAV_HREFS[k];
          const label = t('dashboard.nav.' + k, k === 'chat' ? 'Chat' : k);
          const active = href && pathname === href;
          if (href) {
            return (
              <Link
                key={k}
                href={href}
                className="text-sm transition-colors hover:opacity-80"
                style={{ color: active ? GOLD_BRIGHT : FG }}
              >
                {label}
                {k === 'chat' && unreadChat > 0 && (
                  <span
                    className="ml-1.5 inline-flex items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-bold"
                    style={{ background: '#c45c4a', color: FG }}
                  >
                    {unreadChat}
                  </span>
                )}
              </Link>
            );
          }
          return (
            <span key={k} className="text-sm" style={{ color: MUTED }}>
              {label}
            </span>
          );
        })}
      </nav>
    </header>
  );
}
