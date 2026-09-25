'use client';
import { useEffect, useState } from 'react';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';

function AdminReports() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    const token = tokenStore.getToken();
    fetch(`${config.apiBaseUrl}/events/reports`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.json())
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]));
  }, []);
  if (!items.length) return <p className="mt-2 text-sm text-[#9a8f7c]">Ziadne nahlasenia.</p>;
  return (
    <ul className="mt-3 space-y-2 text-sm text-[#f3ead8]">
      {items.map((it) => (
        <li key={it.id} className="rounded-xl border border-[#d4af37]/20 p-3">
          <p>{it.payload || it.eventType}</p>
          <p className="text-xs text-[#9a8f7c]">{it.createdAt} · user {it.actorUserId}</p>
        </li>
      ))}
    </ul>
  );
}


import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';
import { useAdminStats } from '@/features/admin';
import { AdminUsersTable, AuditTable } from '@/features/admin';
import { CompaniesTable } from '@/features/companies';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { redirect } from 'next/navigation';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function AdminPage() {
  const { user, isLoading } = useAuthRequired();
  const isPlatformAdmin = useIsPlatformAdmin();
  const { data: stats, isLoading: isLoadingStats } = useAdminStats();
  const { t } = useT();

  const safeStats = (stats || {}) as {
    total_users?: number;
    total_listings?: number;
    total_companies?: number;
    pending_verifications?: number;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />
        <div className="mx-auto max-w-6xl px-4 py-16 text-center" style={{ color: MUTED }}>
          {t('admin.loading')}
        </div>
      </div>
    );
  }

  if (user && !isPlatformAdmin) {
    redirect('/dashboard');
  }

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-6xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            {t('admin.kicker')}
          </p>
          <h1 className="mb-10 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            {t('admin.title')}
          </h1>

          {/* ŠTATISTIKY */}
          <section className="mb-12 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Používatelia" value={safeStats.total_users} loading={isLoadingStats} />
            <StatCard label="Ponuky" value={safeStats.total_listings} loading={isLoadingStats} />
            <StatCard label="Firmy" value={safeStats.total_companies} loading={isLoadingStats} />
            <StatCard label="{t('admin.pending')}" value={safeStats.pending_verifications} loading={isLoadingStats} accent />
          </section>

          {/* {t('admin.firmsKicker')} NA OVERENIE */}
          <section className="mb-12">
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              {t('admin.firmsKicker')}
            </p>
            <h2 className="mb-3 text-2xl md:text-3xl" style={{ fontFamily: 'Fraunces, serif' }}>
              {t('admin.firmsTitle')}
            </h2>
            <p className="mb-6 text-sm" style={{ color: MUTED }}>
              Firmy, ktoré požiadali o overenie. Klikni <strong style={{ color: GOLD_BRIGHT }}>Overiť</strong> pre schválenie alebo <strong style={{ color: GOLD_BRIGHT }}>Zamietnuť</strong> pre odmietnutie.
            </p>
            <div
              className="rounded-2xl border p-5"
              style={{
                borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
                background: 'rgba(201,168,76,0.03)',
              }}
            >
              <CompaniesTable />
            </div>
          </section>

          {/* {t('admin.usersKicker')} */}
          <section className="mb-12">
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              {t('admin.usersKicker')}
            </p>
            <h2 className="mb-6 text-2xl md:text-3xl" style={{ fontFamily: 'Fraunces, serif' }}>
              {t('admin.usersTitle')}
            </h2>
            <div
              className="rounded-2xl border p-5"
              style={{
                borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
                background: 'rgba(201,168,76,0.03)',
              }}
            >
              <AdminUsersTable />
            </div>
          </section>

          {/* AUDIT {t('admin.historyKicker')} */}
          <section className="mb-12">
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              {t('admin.historyKicker')}
            </p>
            <h2 className="mb-6 text-2xl md:text-3xl" style={{ fontFamily: 'Fraunces, serif' }}>
              {t('admin.historyTitle')}
            </h2>
            <p className="mb-6 text-sm" style={{ color: MUTED }}>
              {t('admin.historyHint')}
            </p>
            <AuditTable />
          </section>

        
      <section className="mt-8 rounded-2xl border border-[#d4af37]/25 p-4">
        <p className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37]">Nahlasenia</p>
        <AdminReports />
      </section>
    </main>

      <DashboardFooter />
      </div>
    </>
  );
}

function StatCard({
  label,
  value,
  loading,
  accent = false,
}: {
  label: string;
  value?: number;
  loading: boolean;
  accent?: boolean;
}) {
  return (
    <div
      className="rounded-2xl border p-5"
      style={{
        borderColor: accent
          ? 'color-mix(in srgb, #c45c4a 40%, transparent)'
          : 'color-mix(in srgb, #c9a84c 25%, transparent)',
        background: accent ? 'rgba(196,92,74,0.05)' : 'rgba(201,168,76,0.03)',
      }}
    >
      <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: MUTED }}>
        {label}
      </p>
      <p
        className="mt-2 text-3xl md:text-4xl"
        style={{
          fontFamily: 'Fraunces, serif',
          color: accent ? '#e8a598' : GOLD_BRIGHT,
        }}
      >
        {loading ? '…' : (value ?? 0)}
      </p>
    </div>
  );
}
