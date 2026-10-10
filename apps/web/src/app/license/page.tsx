'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export default function LicensePage() {
  const { t } = useT();
  const year = new Date().getFullYear();

  return (
    <>
      <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet" />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <header className="border-b" style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}>
          <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: '1.25rem' }}>CMEP</span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/terms" style={{ color: MUTED }}>{t('legal.terms')}</Link>
              <Link href="/privacy" style={{ color: MUTED }}>{t('legal.privacy')}</Link>
              <Link href="/dsa" style={{ color: MUTED }}>DSA</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('legal.kicker')}</p>
          <h1 className="mb-4 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('legal.licenseTitle')}
          </h1>
          <p className="mb-10 text-sm" style={{ color: FAINT }}>
            {t('legal.licenseMeta')} · © {year} Radoslav Čornanič
          </p>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS1')}</h2>
              <ul className="space-y-1">
                <li>{t('legal.licenseS1L1')}</li>
                <li>{t('legal.licenseS1L2')}</li>
                <li>{t('legal.licenseS1L3')}</li>
                <li>{t('legal.licenseS1L4')}</li>
                <li>{t('legal.licenseS1L5')}</li>
                <li>{t('legal.licenseS1L6')}</li>
                <li>{t('legal.licenseS1L7')}</li>
                <li>{t('legal.licenseS1L8')}</li>
                <li>{t('legal.licenseS1L9')}</li>
              </ul>
              <p className="mt-3">{t('legal.licenseS1Intro')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS2')}</h2>
              <p>{t('legal.licenseS2P1')}</p>
              <p className="mt-3">{t('legal.licenseS2P2')}</p>
              <p className="mt-3">{t('legal.licenseS2P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS3')}</h2>
              <p>{t('legal.licenseS3P1')}</p>
              <p className="mt-3">{t('legal.licenseS3P2')}</p>
              <p className="mt-3">{t('legal.licenseS3P3')}</p>
              <p className="mt-3">{t('legal.licenseS3P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS4')}</h2>
              <p>{t('legal.licenseS4P1')}</p>
              <p className="mt-3">{t('legal.licenseS4P2')}</p>
              <p className="mt-3">{t('legal.licenseS4P3')}</p>
              <p className="mt-3">{t('legal.licenseS4P4')}</p>
              <p className="mt-3">{t('legal.licenseS4P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS5')}</h2>
              <p>{t('legal.licenseS5P1')}</p>
              <p className="mt-3">{t('legal.licenseS5P2')}</p>
              <p className="mt-3">{t('legal.licenseS5P3')}</p>
              <p className="mt-3">{t('legal.licenseS5P4')}</p>
              <p className="mt-3">{t('legal.licenseS5P5')}</p>
              <p className="mt-3">{t('legal.licenseS5P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS6')}</h2>
              <p>{t('legal.licenseS6Intro')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.licenseS6L1')}</li>
                <li>{t('legal.licenseS6L2')}</li>
                <li>{t('legal.licenseS6L3')}</li>
                <li>{t('legal.licenseS6L4')}</li>
                <li>{t('legal.licenseS6L5')}</li>
                <li>{t('legal.licenseS6L6')}</li>
                <li>{t('legal.licenseS6L7')}</li>
                <li>{t('legal.licenseS6L8')}</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS7')}</h2>
              <p>{t('legal.licenseS7P1')}</p>
              <p className="mt-3">{t('legal.licenseS7P2')}</p>
              <p className="mt-3">{t('legal.licenseS7P3')}</p>
              <p className="mt-3">{t('legal.licenseS7P4')}</p>
              <p className="mt-3">{t('legal.licenseS7P5')}</p>
              <p className="mt-3">{t('legal.licenseS7P6')}</p>
              <p className="mt-3">{t('legal.licenseS7P7')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS8')}</h2>
              <p>{t('legal.licenseS8P1')}</p>
              <p className="mt-3">{t('legal.licenseS8P2')}</p>
              <p className="mt-3">{t('legal.licenseS8P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS9')}</h2>
              <p>{t('legal.licenseS9P1')}</p>
              <p className="mt-3">{t('legal.licenseS9P2')}</p>
              <p className="mt-3">{t('legal.licenseS9P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS10')}</h2>
              <p>{t('legal.licenseS10P1')}</p>
              <p className="mt-3">{t('legal.licenseS10P2')}</p>
              <p className="mt-3">{t('legal.licenseS10P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS11')}</h2>
              <p>{t('legal.licenseS11Intro')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS12')}</h2>
              <p>{t('legal.licenseS12P1')}</p>
              <p className="mt-3">{t('legal.licenseS12P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS13')}</h2>
              <p>{t('legal.licenseS13P1')}</p>
              <p className="mt-3">{t('legal.licenseS13P2')}</p>
              <p className="mt-3">{t('legal.licenseS13P3')}</p>
              <p className="mt-3">{t('legal.licenseS13P4')}</p>
              <p className="mt-3">{t('legal.licenseS13P5')}</p>
            </section>
          </div>

          <div className="mt-12 flex flex-wrap gap-4 text-sm">
            <Link href="/terms" style={{ color: GOLD_BRIGHT }}>{t('legal.licenseLinkTerms')}</Link>
            <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>{t('legal.licenseLinkPrivacy')}</Link>
          </div>

          <p className="mt-12 pt-8 text-sm" style={{ color: FAINT, borderTop: '1px solid #2a2620' }}>
            © {year} Radoslav Čornanič · TRČ · {t('legal.licenseCopyright')}
          </p>
        </main>
      </div>
    </>
  );
}
