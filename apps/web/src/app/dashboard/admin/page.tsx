'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';

function AdminReports({ eventType = 'user_reported' }: { eventType?: string }) {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    const token = tokenStore.getToken();
    fetch(`${config.apiBaseUrl}/events/reports?event_type=${encodeURIComponent(eventType)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.json())
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]));
  }, [eventType]);
  if (!items.length) return <p className="mt-2 text-sm text-[#9a8f7c]">Ziadne zaznamy.</p>;
  return (
    <ul className="mt-3 space-y-2 text-sm text-[#f3ead8]">
      <AdminAnalyticsCard />
      <AdminContactMessages />
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
import { SubscriptionTiersPanel } from '@/features/admin/components/subscription-tiers-panel';
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



function AdminAnalyticsCard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = tokenStore.getToken();
    fetch(`${config.apiBaseUrl}/analytics/admin/stats?days=30`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => setStats(d))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#d4af37]/20 p-5 text-sm text-[#9a8f7c]">
        Nacitavam navstevnost...
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="rounded-2xl border border-[#d4af37]/20 p-5 text-sm text-[#9a8f7c]">
        Statistiky sa nepodarilo nacitat.
      </div>
    );
  }

  const cards = [
    { label: 'Dnes', value: stats.today, sub: `${stats.uniqueToday} unikatnych` },
    { label: 'Vcera', value: stats.yesterday },
    { label: 'Tyzden', value: stats.week },
    { label: 'Mesiac (30d)', value: stats.month },
    { label: 'Spolu', value: stats.total },
  ];

  return (
    <div className="rounded-2xl border border-[#d4af37]/20 p-5">
      <h2 className="mb-4 text-lg font-semibold text-[#f3ead8]">
        Navstevy landing page
      </h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-[#d4af37]/15 p-3">
            <p className="text-[10px] uppercase tracking-widest text-[#9a8f7c]">
              {c.label}
            </p>
            <p className="mt-1 text-2xl font-semibold text-[#e8d48b]">{c.value}</p>
            {c.sub && <p className="mt-1 text-[11px] text-[#9a8f7c]">{c.sub}</p>}
          </div>
        ))}
      </div>

      {stats.topSources && stats.topSources.length > 0 && (
        <div className="mt-5">
          <p className="mb-2 text-xs uppercase tracking-widest text-[#9a8f7c]">
            Top zdroje (30 dni)
          </p>
          <ul className="space-y-1 text-sm text-[#f3ead8]">
            {stats.topSources.map((s: any) => (
              <li key={s.source} className="flex justify-between gap-3 border-b border-[#d4af37]/10 py-1">
                <span className="truncate">{s.source}</span>
                <span className="text-[#e8d48b]">{s.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}



function AdminContactMessages() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = tokenStore.getToken();
    fetch(`${config.apiBaseUrl}/events/reports?event_type=contact_submitted`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#d4af37]/20 p-5 text-sm text-[#9a8f7c]">
        Nacitavam spravy...
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-[#d4af37]/20 p-5">
      <h2 className="mb-4 text-lg font-semibold text-[#f3ead8]">
        Kontaktne spravy z landing page ({items.length})
      </h2>
      {items.length === 0 ? (
        <p className="text-sm text-[#9a8f7c]">Ziadne spravy.</p>
      ) : (
        <ul className="space-y-3">
          {items.map((it) => {
            let payload: any = {};
            try { payload = JSON.parse(it.payload || '{}'); } catch {}
            return (
              <li key={it.id} className="rounded-xl border border-[#d4af37]/15 p-4">
                <div className="flex flex-wrap items-baseline gap-2">
                  <span className="font-semibold text-[#e8d48b]">{payload.name || '—'}</span>
                  <a href={`mailto:${payload.email}`} className="text-sm text-[#d4af37] hover:underline">
                    {payload.email || '—'}
                  </a>
                  {payload.company && (
                    <span className="text-sm text-[#9a8f7c]">· {payload.company}</span>
                  )}
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-[#f3ead8]">{payload.message || ''}</p>
                <p className="mt-2 text-[11px] text-[#6e6658]">
                  {it.createdAt ? new Date(it.createdAt).toLocaleString('sk-SK') : ''}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

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
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-6xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            {t('admin.kicker')}
          </p>
          <h1 className="mb-10 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('admin.title')}
          </h1>

          {/* ŠTATISTIKY */}
          <section className="mb-12 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label={t('admin.statUsers')} value={safeStats.total_users} loading={isLoadingStats} />
            <StatCard label={t('admin.statListings')} value={safeStats.total_listings} loading={isLoadingStats} />
            <StatCard label={t('admin.statCompanies')} value={safeStats.total_companies} loading={isLoadingStats} />
            <StatCard label={t('admin.pending')} value={safeStats.pending_verifications} loading={isLoadingStats} accent />
          </section>

          {/* {t('admin.firmsKicker')} NA OVERENIE */}
          <section className="mb-12">
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              {t('admin.firmsKicker')}
            </p>
            <h2 className="mb-3 text-2xl md:text-3xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
              {t('admin.firmsTitle')}
            </h2>
            <p className="mb-6 text-sm" style={{ color: MUTED }}>
              {t('admin.firmsHintPrefix')}<strong style={{ color: GOLD_BRIGHT }}>{t('admin.verify')}</strong>{t('admin.firmsHintMiddle')}<strong style={{ color: GOLD_BRIGHT }}>{t('admin.reject')}</strong>{t('admin.firmsHintSuffix')}
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
            <h2 className="mb-6 text-2xl md:text-3xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
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
            <h2 className="mb-6 text-2xl md:text-3xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
              {t('admin.historyTitle')}
            </h2>
            <p className="mb-6 text-sm" style={{ color: MUTED }}>
              {t('admin.historyHint')}
            </p>
            <AuditTable />
          </section>

        
      <section className="mt-12">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          {t('admin.subscriptionsKicker', 'PREDPLATNÉ')}
        </p>
        <h2
          className="mb-3 text-2xl md:text-3xl"
          style={{ fontFamily: 'DM Serif Display, serif' }}
        >
          {t('admin.subscriptionsTitle', 'Subscription tiers')}
        </h2>
        <p className="mb-6 text-sm" style={{ color: MUTED }}>
          {t(
            'admin.subscriptionsHint',
            'FREE / PRO / AI. Kliknutím zmeníš tier firmy. Zmena je okamžitá.',
          )}
        </p>
        <div
          className="rounded-2xl border p-5"
          style={{
            borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
            background: 'rgba(201,168,76,0.03)',
          }}
        >
          <SubscriptionTiersPanel />
        </div>
      </section>

      <section className="mt-12">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          AI CONTROL
        </p>
        <h2
          className="mb-3 text-2xl md:text-3xl"
          style={{ fontFamily: 'DM Serif Display, serif' }}
        >
          Riadenie AI a governance
        </h2>
        <p className="mb-4 text-sm" style={{ color: MUTED }}>
          Control mode, security events, alerts, approvals, audit. Len pre platform admina.
        </p>
        <Link
          href="/dashboard/admin/ai-control"
          className="inline-flex rounded-full px-5 py-2 text-sm font-semibold"
          style={{ background: GOLD, color: BG }}
        >
          Otvoriť AI Control →
        </Link>
      </section>

      <section className="mt-12">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          LEAD OUTREACH
        </p>
        <h2
          className="mb-3 text-2xl md:text-3xl"
          style={{ fontFamily: 'DM Serif Display, serif' }}
        >
          Oslovenie firiem
        </h2>
        <p className="mb-4 text-sm" style={{ color: MUTED }}>
          AI pripraví personalizovaný email. Ty skontroluješ a pošleš.
        </p>
        <Link
          href="/dashboard/admin/lead-outreach"
          className="inline-flex rounded-full px-5 py-2 text-sm font-semibold"
          style={{ background: GOLD, color: BG }}
        >
          Otvoriť lead outreach →
        </Link>
      </section>

      <section className="mt-12">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          ODPORÚČANIA
        </p>
        <h2
          className="mb-3 text-2xl md:text-3xl"
          style={{ fontFamily: 'DM Serif Display, serif' }}
        >
          Manažment odporúčaní
        </h2>
        <p className="mb-4 text-sm" style={{ color: MUTED }}>
          Automatické odporúčania materiálov a trás, ktoré systém navrhuje firmám.
        </p>
        <Link
          href="/dashboard/admin/recommendations"
          className="inline-flex rounded-full px-5 py-2 text-sm font-semibold"
          style={{ background: GOLD, color: BG }}
        >
          Otvoriť odporúčania →
        </Link>
      </section>

      <section className="mt-12">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          FEEDBACK OD POUZIVATELOV
        </p>
        <h2
          className="mb-3 text-2xl md:text-3xl"
          style={{ fontFamily: 'DM Serif Display, serif' }}
        >
          Napady a pripomienky
        </h2>
        <p className="mb-4 text-sm" style={{ color: MUTED }}>
          Co by si pouzivatelia priali. Klik na &quot;Nápad?&quot; na dashboarde im to otvori.
        </p>
        <div
          className="rounded-2xl border p-5"
          style={{
            borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
            background: 'rgba(201,168,76,0.03)',
          }}
        >
          <AdminReports eventType="user_feedback" />
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-[#d4af37]/25 p-4">
        <p className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37]">{t('admin.reports')}</p>
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
          fontFamily: 'DM Serif Display, serif',
          color: accent ? '#e8a598' : GOLD_BRIGHT,
        }}
      >
        {loading ? '…' : (value ?? 0)}
      </p>
    </div>
  );
}
