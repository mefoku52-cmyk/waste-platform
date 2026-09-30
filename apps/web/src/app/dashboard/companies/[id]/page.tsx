'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const OK = '#5fd17a';
const DANGER = '#e8a598';

type CompanyData = {
  id: string;
  status?: string | null;
  legalName?: string | null;
  tradingName?: string | null;
  registrationNumber?: string | null;
  taxIdentifier?: string | null;
  vatIdentifier?: string | null;
  subscriptionTier?: string | null;
  companyType?: string | null;
  email?: string | null;
  phone?: string | null;
  websiteUrl?: string | null;
  countryCode?: string | null;
  addressLine1?: string | null;
  addressLine2?: string | null;
  city?: string | null;
  postalCode?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  sellerCapability?: boolean | null;
  buyerCapability?: boolean | null;
  logisticsCapability?: boolean | null;
  acceptedMaterialTypes?: string | null;
  verifiedAt?: string | null;
  createdAt?: string | null;
};

type CompanyContacts = {
  companyId: string;
  revealed: boolean;
  reason: string;
  email: string | null;
  phone: string | null;
  websiteUrl: string | null;
};

async function fetchCompanyContacts(id: string): Promise<CompanyContacts> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(`${config.apiBaseUrl}/companies/${id}/contacts`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }
  return body as CompanyContacts;
}

async function fetchCompany(id: string): Promise<CompanyData> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(`${config.apiBaseUrl}/companies/${id}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }
  return (body.data ?? body) as CompanyData;
}

function statusLabel(status?: string | null): { label: string; color: string } {
  switch (status) {
    case 'verified':
      return { label: 'Overená', color: OK };
    case 'verification_submitted':
      return { label: 'Čaká na overenie', color: GOLD_BRIGHT };
    case 'rejected':
      return { label: 'Zamietnutá', color: DANGER };
    case 'suspended':
      return { label: 'Pozastavená', color: DANGER };
    case 'inactive':
      return { label: 'Neaktívna', color: MUTED };
    case 'draft':
    default:
      return { label: status || '—', color: MUTED };
  }
}

function tierLabel(tier?: string | null): string {
  if (!tier) return 'FREE';
  return tier.toUpperCase();
}

function capability(label: string, value: boolean | null | undefined) {
  const enabled = Boolean(value);
  return (
    <div className="cmep-panel rounded-xl p-3">
      <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
        {label}
      </p>
      <p className="mt-1 text-sm" style={{ color: enabled ? OK : MUTED }}>
        {enabled ? '✓ Áno' : '— Nie'}
      </p>
    </div>
  );
}

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const companyId = String(params?.id || '');
  const me = useCurrentUser();
  const { t } = useT();

  const query = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompany(companyId),
    enabled: Boolean(companyId),
    retry: 1,
  });

  const contactsQuery = useQuery({
    queryKey: ['company-contacts', companyId],
    queryFn: () => fetchCompanyContacts(companyId),
    enabled: Boolean(companyId),
    retry: 0,
  });

  const data = query.data;
  const displayName = data?.tradingName || data?.legalName || companyId;
  const status = statusLabel(data?.status);

  // Je to vlastna firma?
  const myCompanyIds = ((me.data as any)?.memberships || [])
    .map((m: any) => String(m?.companyId || m?.company_id || '').toLowerCase().trim())
    .filter(Boolean);
  const isMyCompany = Boolean(
    companyId && myCompanyIds.includes(companyId.toLowerCase().trim())
  );

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link
          href="/dashboard/companies"
          className="inline-flex rounded-full border px-3 py-1.5 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}
        >
          ← {t('common.back')}
        </Link>

        {query.isLoading ? (
          <p className="mt-8 text-sm" style={{ color: MUTED }}>Načítavam…</p>
        ) : query.error ? (
          <div className="mt-8 rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-[#f0bbb0]">
            {query.error instanceof Error ? query.error.message : 'Chyba načítania'}
          </div>
        ) : data ? (
          <>
            {/* HLAVICKA */}
            <section className="mt-6 overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.28)] bg-[#0f0e0a] p-5 sm:p-7">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
                    PROFIL FIRMY
                  </p>
                  <h1
                    className="mt-2 font-serif text-3xl leading-tight sm:text-4xl"
                    style={{ color: GOLD_BRIGHT }}
                  >
                    {displayName}
                  </h1>
                  {data.tradingName && data.legalName && data.tradingName !== data.legalName ? (
                    <p className="mt-1 text-sm" style={{ color: MUTED }}>
                      {data.legalName}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span
                    className="rounded-full px-3 py-1 text-xs font-semibold"
                    style={{
                      background: 'color-mix(in srgb, currentColor 15%, transparent)',
                      color: status.color,
                    }}
                  >
                    ● {status.label}
                  </span>
                  <span
                    className="rounded-full px-3 py-1 text-xs font-semibold"
                    style={{
                      background: 'rgba(201,168,76,0.12)',
                      color: GOLD_BRIGHT,
                    }}
                  >
                    {tierLabel(data.subscriptionTier)}
                  </span>
                </div>
              </div>
            </section>

            {/* INFO */}
            <section className="mt-6">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                ZÁKLADNÉ ÚDAJE
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="cmep-panel rounded-xl p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>IČO</p>
                  <p className="mt-1">{data.registrationNumber || '—'}</p>
                </div>
                <div className="cmep-panel rounded-xl p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>DIČ</p>
                  <p className="mt-1">{data.taxIdentifier || '—'}</p>
                </div>
                <div className="cmep-panel rounded-xl p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>IČ DPH</p>
                  <p className="mt-1">{data.vatIdentifier || '—'}</p>
                </div>
                <div className="cmep-panel rounded-xl p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>Typ</p>
                  <p className="mt-1">{data.companyType || '—'}</p>
                </div>
              </div>
            </section>

            {/* ADRESA */}
            <section className="mt-6">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                ADRESA
              </p>
              <div className="cmep-panel rounded-xl p-4 text-sm">
                <p>{data.addressLine1 || '—'}</p>
                {data.addressLine2 ? <p>{data.addressLine2}</p> : null}
                <p>
                  {[data.postalCode, data.city].filter(Boolean).join(' ') || '—'}
                </p>
                <p style={{ color: MUTED }}>{data.countryCode || '—'}</p>
              </div>
            </section>

            {/* KONTAKTY */}
            <section className="mt-6">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                KONTAKTY
              </p>

              {contactsQuery.isLoading ? (
                <div className="cmep-panel rounded-xl p-4 text-sm" style={{ color: MUTED }}>
                  Načítavam…
                </div>
              ) : contactsQuery.error ? (
                <div className="cmep-panel rounded-xl p-4 text-sm" style={{ color: MUTED }}>
                  Kontakty sa nepodarilo načítať.
                </div>
              ) : contactsQuery.data?.revealed ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="cmep-panel rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>{t('tables.email')}</p>
                    <p className="mt-1 text-sm">
                      {contactsQuery.data.email ? (
                        <a href={`mailto:${contactsQuery.data.email}`} style={{ color: GOLD_BRIGHT }}>
                          {contactsQuery.data.email}
                        </a>
                      ) : '—'}
                    </p>
                  </div>
                  <div className="cmep-panel rounded-xl p-3">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>{t('tables.phone')}</p>
                    <p className="mt-1 text-sm">{contactsQuery.data.phone || '—'}</p>
                  </div>
                  <div className="cmep-panel rounded-xl p-3 sm:col-span-2">
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>Web</p>
                    <p className="mt-1 text-sm">
                      {contactsQuery.data.websiteUrl ? (
                        <a
                          href={contactsQuery.data.websiteUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: GOLD_BRIGHT }}
                        >
                          {contactsQuery.data.websiteUrl}
                        </a>
                      ) : '—'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="cmep-panel rounded-xl p-5 text-sm">
                  <p style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>
                    🔒 Kontakty sú skryté
                  </p>
                  <p className="mt-2" style={{ color: MUTED }}>
                    {contactsQuery.data?.reason === 'no_relationship'
                      ? 'Kontakty sa odhalia, keď medzi vami a touto firmou vznikne dopyt a druhá strana naň odpovie.'
                      : 'Kontakty nie sú dostupné.'}
                  </p>
                  <div className="mt-4">
                    <Link
                      href="/dashboard/listings"
                      className="inline-flex rounded-full px-4 py-2 text-sm font-semibold"
                      style={{ background: GOLD, color: '#090807' }}
                    >
                      Nájsť ponuku tejto firmy →
                    </Link>
                  </div>
                </div>
              )}
            </section>

            {/* CAPABILITIES */}
            <section className="mt-6">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                ROLA NA TRHU
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                {capability('Predávajúci', data.sellerCapability)}
                {capability('Nakupujúci', data.buyerCapability)}
                {capability('Logistika', data.logisticsCapability)}
              </div>
            </section>

            {/* MATERIALY */}
            {data.acceptedMaterialTypes ? (
              <section className="mt-6">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                  AKCEPTOVANÉ MATERIÁLY
                </p>
                <div className="cmep-panel rounded-xl p-4 text-sm">
                  {data.acceptedMaterialTypes}
                </div>
              </section>
            ) : null}

            {/* AKCIE */}
            {isMyCompany ? (
              <section className="mt-6">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
                  SPRÁVA FIRMY
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/dashboard/listings"
                    className="rounded-full px-4 py-2 text-sm font-semibold"
                    style={{ background: GOLD, color: '#090807' }}
                  >
                    Moje ponuky
                  </Link>
                  <Link
                    href="/dashboard/companies"
                    className="rounded-full border px-4 py-2 text-sm font-semibold"
                    style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD_BRIGHT }}
                  >
                    Všetky firmy
                  </Link>
                </div>
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
