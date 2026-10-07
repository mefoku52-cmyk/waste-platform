'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLogout, useCurrentUser, useIsPlatformAdmin } from '@/features/auth';
import { useT } from '@/lib/i18n/context';
import { LanguageSwitcher } from '@/components/language-switcher';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

export function DashboardHeader() {
  const pathname = usePathname();
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const isAdmin = useIsPlatformAdmin();
  const myEmail = String((me as any)?.email || (me as any)?.user?.email || '');
  const { mutateAsync: logout, isPending: logoutPending } = useLogout();

  const isOnDashboard = pathname === '/dashboard';

  return (
    <header
      className="z-40 border-b backdrop-blur-md"
      style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)', background: 'rgba(9,8,7,0.85)' }}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-3">
          <img src="/trc-mark.jpg" alt="TRČ" className="h-16 w-16 rounded-2xl object-cover" />
        </Link>

        {/* Pravá strana: Admin (len pre admina) + jazyk + odhlásiť */}
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

      {/* Späť na prehľad — viditeľné iba mimo /dashboard */}
      {!isOnDashboard && (
        <div className="mx-auto max-w-6xl px-4 pb-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition hover:opacity-90"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
              color: GOLD_BRIGHT,
            }}
          >
            {t('common.backToOverview')}
          </Link>
        </div>
      )}
    </header>
  );
}
