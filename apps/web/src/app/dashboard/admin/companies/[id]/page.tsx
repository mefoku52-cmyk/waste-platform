'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { useAdminCompany } from '@/features/admin';
import { SignedImage } from '@/features/uploads/components/signed-image';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b py-2 text-sm" style={{ borderColor: 'rgba(201,168,76,0.1)' }}>
      <span style={{ color: MUTED }}>{label}</span>
      <span className="text-right" style={{ color: FG }}>{value ?? '—'}</span>
    </div>
  );
}

function formatDate(iso: string | null | undefined) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('sk-SK');
  } catch {
    return iso;
  }
}

export default function AdminCompanyDetailPage() {
  const params = useParams();
  const id = typeof params?.id === 'string' ? params.id : undefined;
  const { data, isLoading, error } = useAdminCompany(id);
  const company = data?.data;

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <DashboardHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              Administrácia · firma
            </p>
            <h1 className="text-3xl md:text-4xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
              {company?.tradingName || company?.legalName || 'Firma'}
            </h1>
          </div>
          <Link
            href="/dashboard/admin/companies"
            className="rounded-full border px-4 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD }}
          >
            Späť na firmy
          </Link>
        </div>

        {isLoading ? (
          <p className="py-10 text-center text-sm" style={{ color: MUTED }}>Načítavam firmu…</p>
        ) : error || !company ? (
          <p className="py-10 text-center text-sm" style={{ color: '#e8a598' }}>
            Firma sa nepodarilo načítať.
          </p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="cmep-panel rounded-2xl p-5">
              <h2 className="mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>Údaje firmy</h2>
              <Row label="Stav" value={company.status} />
              <Row label="Právny názov" value={company.legalName} />
              <Row label="Obchodný názov" value={company.tradingName} />
              <Row label="IČO" value={company.registrationNumber} />
              <Row label="DIČ" value={company.taxIdentifier} />
              <Row label="IČ DPH" value={company.vatIdentifier} />
              <Row label="E-mail" value={company.email} />
              <Row label="Telefón" value={company.phone} />
              <Row label="Web" value={company.websiteUrl} />
              <Row
                label="Adresa"
                value={[company.addressLine1, company.addressLine2, company.postalCode, company.city]
                  .filter(Boolean)
                  .join(', ')}
              />
              <Row label="Krajina" value={company.countryCode} />
              <Row label="Typ" value={company.companyType} />
              <Row label="Tarifa" value={company.subscriptionTier} />
              <Row label="Predajca" value={company.sellerCapability ? 'áno' : 'nie'} />
              <Row label="Kupujúci" value={company.buyerCapability ? 'áno' : 'nie'} />
              <Row label="Logistika" value={company.logisticsCapability ? 'áno' : 'nie'} />
              <Row label="Vytvorená" value={formatDate(company.createdAt)} />
              <Row label="Overená" value={formatDate(company.verifiedAt)} />
            </section>

            <section className="space-y-6">
              <div className="cmep-panel rounded-2xl p-5">
                <h2 className="mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>Verejná stránka</h2>
                <Row label="Stav" value={company.pageStatus || 'neexistuje'} />
                <Row label="Slug" value={company.pageSlug} />
                <Row label="Verejný e-mail" value={company.publicEmail} />
                <Row label="Verejný telefón" value={company.publicPhone} />
                {company.pageStatus === 'published' && company.pageSlug ? (
                  <Link
                    href={`/firma/${company.pageSlug}`}
                    className="mt-3 inline-block text-sm underline"
                    style={{ color: GOLD }}
                  >
                    Otvoriť verejnú stránku
                  </Link>
                ) : null}
              </div>

              <div className="cmep-panel rounded-2xl p-5">
                <h2 className="mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>Počty</h2>
                <Row label="Fotky" value={company.counts.photos ?? 0} />
                <Row label="Členovia" value={company.counts.memberships ?? 0} />
                <Row label="Ponuky" value={company.counts.listings ?? 0} />
                <Row label="Dopyty" value={company.counts.inquiries ?? 0} />
              </div>
            </section>

            <section className="cmep-panel rounded-2xl p-5">
              <h2 className="mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>Kontakty / členovia</h2>
              {company.memberships.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>Žiadni členovia.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {company.memberships.map((m) => (
                    <li key={m.userId} className="rounded-xl border p-3" style={{ borderColor: 'rgba(201,168,76,0.15)' }}>
                      <p style={{ color: FG }}>
                        {[m.firstName, m.lastName].filter(Boolean).join(' ') || m.email || m.userId}
                        {m.isPrimaryContact ? ' · hlavný kontakt' : ''}
                      </p>
                      <p className="text-xs" style={{ color: MUTED }}>
                        {m.email || '—'} · {m.role} · {m.status}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="cmep-panel rounded-2xl p-5">
              <h2 className="mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>Fotogaléria</h2>
              {company.photos.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>Žiadne fotky.</p>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  {company.photos.map((p) => (
                    <div key={p.id} className="overflow-hidden rounded-xl border" style={{ borderColor: 'rgba(201,168,76,0.15)' }}>
                      <SignedImage
                        src={p.fileUrl}
                        alt={p.altText || p.caption || ''}
                        className="h-36 w-full object-cover"
                      />
                      <p className="p-2 text-xs" style={{ color: MUTED }}>
                        {p.caption || '—'}{p.isPrimary ? ' · hlavná' : ''}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
      <DashboardFooter />
    </div>
  );
}
