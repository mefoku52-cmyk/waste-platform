import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { siteBaseUrl, siteBaseUrlFromEnv } from '@/lib/site';

import { PublicContactForm } from '@/features/company-pages/components/public-contact-form';
import { fetchPublicCompanyPage } from '@/features/company-pages/server';
import type { PublicCompanyPage } from '@/features/company-pages/types';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

// Dynamické (fetch s cache: 'no-store') — vždy čerstvé dáta.
export const dynamic = 'force-dynamic';

type Params = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { slug } = await params;
  const page = await fetchPublicCompanyPage(slug);
  if (!page) {
    // notFound() tu (nie len v page) — inak streamovaná odpoveď už poslala 200
    // a neznámy slug by vrátil soft-404 (stav 200). Toto vráti skutočnú 404.
    notFound();
  }

  const base = await siteBaseUrl();
  const url = `${base}/firma/${page.slug}`;
  const title = page.seoTitle || `${page.displayName}${page.tagline ? ` — ${page.tagline}` : ''}`;
  const description =
    page.seoDescription ||
    page.aboutShort ||
    `Profil firmy ${page.displayName} na CMEP — obehové materiály.`;

  const ogImage = page.company.logoUrl || page.photos[0]?.url || undefined;

  return {
    title: `${title} · CMEP`,
    description,
    alternates: { canonical: url },
    openGraph: {
      type: 'website',
      url,
      title: `${title} · CMEP`,
      description,
      siteName: 'CMEP',
      images: ogImage ? [{ url: `${base}${ogImage}` }] : undefined,
    },
    twitter: {
      card: 'summary_large_image',
      title: `${title} · CMEP`,
      description,
      images: ogImage ? [`${base}${ogImage}`] : undefined,
    },
  };
}

function Stars({ value }: { value: number }) {
  const rounded = Math.round(value);
  return (
    <span aria-label={`${value} / 5`} style={{ color: GOLD }}>
      {'★'.repeat(Math.max(0, Math.min(5, rounded)))}
      <span style={{ color: '#4a4438' }}>{'★'.repeat(Math.max(0, 5 - rounded))}</span>
    </span>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p
      className="mb-3 text-[11px] font-semibold uppercase tracking-[0.24em]"
      style={{ color: GOLD }}
    >
      {children}
    </p>
  );
}

function buildJsonLd(page: PublicCompanyPage, base: string) {
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: page.displayName,
    url: `${base}/firma/${page.slug}`,
    ...(page.company.logoUrl ? { logo: `${base}${page.company.logoUrl}` } : {}),
    ...(page.publicEmail ? { email: page.publicEmail } : {}),
    ...(page.publicPhone ? { telephone: page.publicPhone } : {}),
    ...(page.publicWebsite ? { sameAs: [page.publicWebsite] } : {}),
    ...(page.aboutShort ? { description: page.aboutShort } : {}),
    address: {
      '@type': 'PostalAddress',
      ...(page.company.city ? { addressLocality: page.company.city } : {}),
      ...(page.company.countryCode ? { addressCountry: page.company.countryCode } : {}),
    },
  };
  if (page.ratingCount > 0 && page.ratingAverage != null) {
    data.aggregateRating = {
      '@type': 'AggregateRating',
      ratingValue: page.ratingAverage,
      reviewCount: page.ratingCount,
      bestRating: 5,
      worstRating: 1,
    };
  }
  return data;
}

export default async function PublicCompanyPage({ params }: Params) {
  const { slug } = await params;
  const page = await fetchPublicCompanyPage(slug);
  if (!page) notFound();

  const base = siteBaseUrlFromEnv();
  const jsonLd = buildJsonLd(page, base);
  const hero = page.photos.find((p) => p.isPrimary) || page.photos[0] || null;

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div
        className="min-h-screen"
        style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}
      >
        <header
          className="border-b"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
        >
          <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: '1.25rem' }}>
                CMEP
              </span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/" style={{ color: MUTED }}>
                Domov
              </Link>
              <Link href="/login" style={{ color: MUTED }}>
                Prihlásiť
              </Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-4 py-10">
          {/* HERO */}
          <section className="overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.28)] bg-[#0f0e0a]">
            {hero ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={hero.url}
                alt={hero.altText || page.displayName}
                loading="lazy"
                className="h-56 w-full object-cover sm:h-72"
              />
            ) : null}
            <div className="p-6 sm:p-8">
              <div className="flex flex-wrap items-start gap-5">
                {page.company.logoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={page.company.logoUrl}
                    alt={`${page.displayName} logo`}
                    className="h-20 w-20 rounded-xl object-cover"
                  />
                ) : null}
                <div className="min-w-[220px] flex-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h1
                      className="text-3xl leading-tight sm:text-4xl"
                      style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                    >
                      {page.displayName}
                    </h1>
                    {page.company.verified ? (
                      <span
                        className="rounded-full px-3 py-1 text-xs font-semibold"
                        style={{ background: 'rgba(95,209,122,0.14)', color: '#5fd17a' }}
                      >
                        ✓ Overená firma
                      </span>
                    ) : null}
                  </div>
                  {page.tagline ? (
                    <p className="mt-2 text-base" style={{ color: MUTED }}>
                      {page.tagline}
                    </p>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm" style={{ color: MUTED }}>
                    {page.area || page.company.city ? (
                      <span>📍 {[page.area, page.company.city, page.company.countryCode].filter(Boolean).join(', ')}</span>
                    ) : null}
                    {page.ratingCount > 0 && page.ratingAverage != null ? (
                      <span className="flex items-center gap-2">
                        <Stars value={page.ratingAverage} />
                        {page.ratingAverage.toFixed(1)} ({page.ratingCount})
                      </span>
                    ) : null}
                  </div>
                  {(page.company.sellerCapability ||
                    page.company.buyerCapability ||
                    page.company.logisticsCapability) && (
                    <div className="mt-4 flex flex-wrap gap-2 text-xs">
                      {page.company.sellerCapability ? <Badge>Predávajúci</Badge> : null}
                      {page.company.buyerCapability ? <Badge>Kupujúci</Badge> : null}
                      {page.company.logisticsCapability ? <Badge>Logistika</Badge> : null}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* O NÁS */}
          {(page.aboutShort || page.aboutLong) && (
            <section className="mt-8">
              <SectionTitle>O firme</SectionTitle>
              <div className="cmep-panel rounded-xl p-5 text-sm leading-relaxed" style={{ color: FG }}>
                {page.aboutShort ? <p className="whitespace-pre-line">{page.aboutShort}</p> : null}
                {page.aboutLong ? (
                  <p className="mt-3 whitespace-pre-line" style={{ color: MUTED }}>
                    {page.aboutLong}
                  </p>
                ) : null}
              </div>
            </section>
          )}

          {/* SLUŽBY / ZAMERANIE */}
          {(page.services || page.specialization || page.certifications) && (
            <section className="mt-8 grid gap-4 sm:grid-cols-2">
              {page.services ? (
                <InfoCard title="Služby">{page.services}</InfoCard>
              ) : null}
              {page.specialization ? (
                <InfoCard title="Zameranie">{page.specialization}</InfoCard>
              ) : null}
              {page.certifications ? (
                <InfoCard title="Certifikáty">{page.certifications}</InfoCard>
              ) : null}
            </section>
          )}

          {/* PREVÁDZKA */}
          {(page.openingHours || page.languages || page.categories) && (
            <section className="mt-8">
              <SectionTitle>Prevádzka</SectionTitle>
              <div className="grid gap-3 sm:grid-cols-3">
                {page.openingHours ? <Fact label="Otváracie hodiny" value={page.openingHours} /> : null}
                {page.languages ? <Fact label="Jazyky" value={page.languages} /> : null}
                {page.categories ? <Fact label="Kategórie" value={page.categories} /> : null}
              </div>
            </section>
          )}

          {/* GALÉRIA */}
          {page.photos.length > 0 && (
            <section className="mt-8">
              <SectionTitle>Galéria</SectionTitle>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {page.photos.map((photo, i) => (
                  <figure key={`${photo.url}-${i}`} className="cmep-panel overflow-hidden rounded-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={photo.url}
                      alt={photo.altText || photo.caption || page.displayName}
                      loading="lazy"
                      className="h-44 w-full object-cover"
                    />
                    {photo.caption ? (
                      <figcaption className="p-2 text-xs" style={{ color: MUTED }}>
                        {photo.caption}
                      </figcaption>
                    ) : null}
                  </figure>
                ))}
              </div>
            </section>
          )}

          {/* PONUKY */}
          {page.listings.length > 0 && (
            <section className="mt-8">
              <SectionTitle>Aktuálne ponuky</SectionTitle>
              <div className="grid gap-3 sm:grid-cols-2">
                {page.listings.map((listing) => (
                  <div key={listing.id} className="cmep-panel overflow-hidden rounded-xl">
                    {listing.imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={listing.imageUrl}
                        alt={listing.title}
                        loading="lazy"
                        className="h-36 w-full object-cover"
                      />
                    ) : null}
                    <div className="p-4">
                      <p className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                        {listing.title}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs" style={{ color: MUTED }}>
                        {listing.materialType ? <span>{listing.materialType}</span> : null}
                        {listing.quantity != null ? (
                          <span>
                            {listing.quantity} {listing.unit || ''}
                          </span>
                        ) : null}
                        {listing.price != null ? (
                          <span>
                            {listing.price} {listing.currency || ''}
                          </span>
                        ) : null}
                        {listing.location ? <span>📍 {listing.location}</span> : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* RECENZIE */}
          {page.ratingCount > 0 && (
            <section className="mt-8">
              <SectionTitle>Hodnotenia ({page.ratingCount})</SectionTitle>
              <div className="cmep-panel rounded-xl p-5">
                <div className="flex items-center gap-3">
                  <span className="text-3xl" style={{ color: GOLD_BRIGHT }}>
                    {page.ratingAverage?.toFixed(1)}
                  </span>
                  <div>
                    <Stars value={page.ratingAverage ?? 0} />
                    <p className="text-xs" style={{ color: MUTED }}>
                      {page.ratingCount} hodnotení
                    </p>
                  </div>
                </div>
                <div className="mt-4 space-y-3">
                  {page.reviews.map((review) => (
                    <div
                      key={review.id}
                      className="rounded-lg border p-3"
                      style={{ borderColor: 'rgba(201,168,76,0.18)' }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <Stars value={review.rating} />
                        {review.createdAt ? (
                          <span className="text-xs" style={{ color: MUTED }}>
                            {new Date(review.createdAt).toLocaleDateString('sk-SK')}
                          </span>
                        ) : null}
                      </div>
                      {review.title ? (
                        <p className="mt-1 text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                          {review.title}
                        </p>
                      ) : null}
                      {review.body ? (
                        <p className="mt-1 text-sm" style={{ color: MUTED }}>
                          {review.body}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* KONTAKT */}
          {(page.publicEmail || page.publicPhone || page.publicWebsite) && (
            <section className="mt-8">
              <SectionTitle>Kontakt</SectionTitle>
              <div className="cmep-panel grid gap-3 rounded-xl p-5 text-sm sm:grid-cols-2">
                {page.publicEmail ? (
                  <p>
                    <span style={{ color: MUTED }}>E-mail: </span>
                    <a href={`mailto:${page.publicEmail}`} style={{ color: GOLD_BRIGHT }}>
                      {page.publicEmail}
                    </a>
                  </p>
                ) : null}
                {page.publicPhone ? (
                  <p>
                    <span style={{ color: MUTED }}>Telefón: </span>
                    <a href={`tel:${page.publicPhone}`} style={{ color: GOLD_BRIGHT }}>
                      {page.publicPhone}
                    </a>
                  </p>
                ) : null}
                {page.publicWebsite ? (
                  <p className="sm:col-span-2">
                    <span style={{ color: MUTED }}>Web: </span>
                    <a
                      href={page.publicWebsite}
                      target="_blank"
                      rel="noopener noreferrer nofollow"
                      style={{ color: GOLD_BRIGHT }}
                    >
                      {page.publicWebsite}
                    </a>
                  </p>
                ) : null}
              </div>
            </section>
          )}

          {/* KONTAKTNÝ FORMULÁR */}
          <section className="mt-8">
            <SectionTitle>Napíšte firme</SectionTitle>
            <PublicContactForm slug={page.slug} />
          </section>

          <p className="mt-10 text-center text-xs" style={{ color: MUTED }}>
            Profil na platforme CMEP · Obehové materiály
          </p>
        </main>
      </div>
    </>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="rounded-full px-2.5 py-1"
      style={{ background: 'rgba(201,168,76,0.12)', color: GOLD_BRIGHT }}
    >
      {children}
    </span>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="cmep-panel rounded-xl p-5">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: GOLD }}>
        {title}
      </p>
      <p className="mt-2 whitespace-pre-line text-sm" style={{ color: FG }}>
        {children}
      </p>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="cmep-panel rounded-xl p-4">
      <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: MUTED }}>
        {label}
      </p>
      <p className="mt-1 text-sm">{value}</p>
    </div>
  );
}
