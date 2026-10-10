'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export default function TermsPage() {
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
              <Link href="/privacy" style={{ color: MUTED }}>{t('legal.privacy')}</Link>
              <Link href="/license" style={{ color: MUTED }}>{t('legal.license')}</Link>
              <Link href="/dsa" style={{ color: MUTED }}>DSA</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('legal.kicker')}</p>
          <h1 className="mb-10 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('legal.termsTitle')}
          </h1>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS1')}</h2>
              <p>{t('legal.termsS1P1')}</p>
              <ul className="mt-3 space-y-1">
                <li>{t('legal.termsS1L1')}</li>
                <li>{t('legal.termsS1L2')}</li>
                <li>{t('legal.termsS1L3')}</li>
                <li>{t('legal.termsS1L4')}</li>
                <li>{t('legal.termsS1L5')}</li>
                <li>{t('legal.termsS1L6')}</li>
                <li>{t('legal.termsS1L7')}</li>
                <li>{t('legal.termsS1L8')}</li>
                <li>{t('legal.termsS1L9')}</li>
              </ul>
              <p className="mt-3">{t('legal.termsS1P2')}</p>
              <p className="mt-3">{t('legal.termsS1P3')}</p>
              <p className="mt-3">{t('legal.termsS1P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS2')}</h2>
              <p>{t('legal.termsS2P1')}</p>
              <p className="mt-3">{t('legal.termsS2P2')}</p>
              <p className="mt-3">{t('legal.termsS2P3')}</p>
              <p className="mt-3">{t('legal.termsS2P4')}</p>
              <p className="mt-3">{t('legal.termsS2P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS3')}</h2>
              <p>{t('legal.termsS3P1')}</p>
              <p className="mt-3">{t('legal.termsS3P2')}</p>
              <p className="mt-3">{t('legal.termsS3P3')}</p>
              <p className="mt-3">{t('legal.termsS3P4')}</p>
              <p className="mt-3">{t('legal.termsS3P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS4')}</h2>
              <p>{t('legal.termsS4P1')}</p>
              <p className="mt-3">{t('legal.termsS4P2')}</p>
              <p className="mt-3">{t('legal.termsS4P3')}</p>
              <p className="mt-3">{t('legal.termsS4P4')}</p>
              <p className="mt-3">{t('legal.termsS4P5')}</p>
              <p className="mt-3">{t('legal.termsS4P6')}</p>
              <p className="mt-3">{t('legal.termsS4P7')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS5')}</h2>
              <p>{t('legal.termsS5P1')}</p>
              <p className="mt-3">{t('legal.termsS5P2')}</p>
              <p className="mt-3">{t('legal.termsS5P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS6')}</h2>
              <p>{t('legal.termsS6P1')}</p>
              <p className="mt-3">{t('legal.termsS6P2')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.termsS6L1')}</li>
                <li>{t('legal.termsS6L2')}</li>
                <li>{t('legal.termsS6L3')}</li>
                <li>{t('legal.termsS6L4')}</li>
                <li>{t('legal.termsS6L5')}</li>
                <li>{t('legal.termsS6L6')}</li>
                <li>{t('legal.termsS6L7')}</li>
                <li>{t('legal.termsS6L8')}</li>
                <li>{t('legal.termsS6L9')}</li>
                <li>{t('legal.termsS6L10')}</li>
              </ul>
              <p className="mt-3">{t('legal.termsS6P3')}</p>
              <p className="mt-3">{t('legal.termsS6P4')}</p>
              <p className="mt-3">{t('legal.termsS6P5')}</p>
              <p className="mt-3">{t('legal.termsS6P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS7')}</h2>
              <p>{t('legal.termsS7P1')}</p>
              <p className="mt-3">{t('legal.termsS7P2')}</p>
              <p className="mt-3">{t('legal.termsS7P3')}</p>
              <p className="mt-3">{t('legal.termsS7P4')}</p>
              <p className="mt-3">{t('legal.termsS7P5')}</p>
              <p className="mt-3">{t('legal.termsS7P6')}</p>
              <p className="mt-3">{t('legal.termsS7P7')}</p>
              <p className="mt-3">{t('legal.termsS7P8')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS8')}</h2>
              <p>{t('legal.termsS8P1')}</p>
              <p className="mt-3">{t('legal.termsS8P2')}</p>
              <p className="mt-3">{t('legal.termsS8P3')}</p>
              <p className="mt-3">{t('legal.termsS8P4')}</p>
              <p className="mt-3">{t('legal.termsS8P5')}</p>
              <p className="mt-3">{t('legal.termsS8P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS9')}</h2>
              <p>{t('legal.termsS9P1')}</p>
              <p className="mt-3">{t('legal.termsS9P2')}</p>
              <p className="mt-3">{t('legal.termsS9P3')}</p>
              <p className="mt-3">{t('legal.termsS9P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS10')}</h2>
              <p>{t('legal.termsS10P1')}</p>
              <p className="mt-3">{t('legal.termsS10P2')}</p>
              <p className="mt-3">{t('legal.termsS10P3')}</p>
              <p className="mt-3">{t('legal.termsS10P4')}</p>
              <p className="mt-3">{t('legal.termsS10P5')}</p>
              <p className="mt-3">{t('legal.termsS10P6')}</p>
              <p className="mt-3">{t('legal.termsS10P7')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS11')}</h2>
              <p>{t('legal.termsS11P1')}</p>
              <p className="mt-3">{t('legal.termsS11P2')}</p>
              <p className="mt-3">{t('legal.termsS11P3')}</p>
              <p className="mt-3">{t('legal.termsS11P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS12')}</h2>
              <p>{t('legal.termsS12P1')}</p>
              <p className="mt-3">{t('legal.termsS12P2')}</p>
              <p className="mt-3">{t('legal.termsS12P3')}</p>
              <p className="mt-3">{t('legal.termsS12P4')}</p>
              <p className="mt-3">{t('legal.termsS12P5')}</p>
              <p className="mt-3">{t('legal.termsS12P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS13')}</h2>
              <p>{t('legal.termsS13P1')}</p>
              <p className="mt-3">{t('legal.termsS13P2')}</p>
              <p className="mt-3">{t('legal.termsS13P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS14')}</h2>
              <p>{t('legal.termsS14P1')}</p>
              <p className="mt-3">{t('legal.termsS14P2')}</p>
              <p className="mt-3">{t('legal.termsS14P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS15')}</h2>
              <p>{t('legal.termsS15P1')}</p>
              <p className="mt-3">{t('legal.termsS15P2')}</p>
              <p className="mt-3">{t('legal.termsS15P3')}</p>
              <p className="mt-3">{t('legal.termsS15P4')}</p>
              <p className="mt-3">{t('legal.termsS15P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS16')}</h2>
              <p>{t('legal.termsS16P1')}</p>
              <p className="mt-3">{t('legal.termsS16P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.termsS17')}</h2>
              <p>{t('legal.termsS17P1')}</p>
              <p className="mt-3">{t('legal.termsS17P2')}</p>
              <p className="mt-3">{t('legal.termsS17P3')}</p>
              <p className="mt-3">{t('legal.termsS17P4')}</p>
            </section>
          </div>

          <p className="mt-12 pt-8 text-sm" style={{ color: FAINT, borderTop: '1px solid #2a2620' }}>
            © {year} Radoslav Čornanič · TRČ · CMEP
          </p>
        </main>
      </div>
    </>
  );
}
