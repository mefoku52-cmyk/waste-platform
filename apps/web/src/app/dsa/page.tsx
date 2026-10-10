'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export default function DsaPage() {
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
              <Link href="/license" style={{ color: MUTED }}>{t('legal.license')}</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('legal.kicker')}</p>
          <h1 className="mb-4 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('legal.dsaTitle')}
          </h1>
          <p className="mb-10 text-sm" style={{ color: FAINT }}>
            {t('legal.dsaMeta')} · © {year} Radoslav Čornanič
          </p>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS1')}</h2>
              <p>{t('legal.dsaS1P1')}</p>
              <p className="mt-3">{t('legal.dsaS1P2')}</p>
              <p className="mt-3">{t('legal.dsaS1P3')}</p>
              <p className="mt-3">{t('legal.dsaS1P4')}</p>
              <p className="mt-3">{t('legal.dsaS1P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS2')}</h2>
              <p>{t('legal.dsaS2P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS2L1')}</li>
                <li>{t('legal.dsaS2L2')}</li>
                <li>{t('legal.dsaS2L3')}</li>
                <li>{t('legal.dsaS2L4')}</li>
                <li>{t('legal.dsaS2L5')}</li>
                <li>{t('legal.dsaS2L6')}</li>
                <li>{t('legal.dsaS2L7')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS2P2')}</p>
              <p className="mt-3">{t('legal.dsaS2P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS3')}</h2>
              <p>{t('legal.dsaS3P1')}</p>
              <p className="mt-2 font-mono text-sm"><a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>{t('legal.dsaS3P2')}</a></p>
              <p className="mt-3">{t('legal.dsaS3P3')}</p>
              <p className="mt-3">{t('legal.dsaS3P4')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS3L1')}</li>
                <li>{t('legal.dsaS3L2')}</li>
                <li>{t('legal.dsaS3L3')}</li>
                <li>{t('legal.dsaS3L4')}</li>
                <li>{t('legal.dsaS3L5')}</li>
                <li>{t('legal.dsaS3L6')}</li>
                <li>{t('legal.dsaS3L7')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS3P5')}</p>
              <p className="mt-3">{t('legal.dsaS3P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS4')}</h2>
              <p>{t('legal.dsaS4P1')}</p>
              <p className="mt-3">{t('legal.dsaS4P2')}</p>
              <p className="mt-3">{t('legal.dsaS4P3')}</p>
              <p className="mt-3">{t('legal.dsaS4P4')}</p>
              <p className="mt-3">{t('legal.dsaS4P5')}</p>
              <p className="mt-3">{t('legal.dsaS4P6')}</p>
              <p className="mt-3">{t('legal.dsaS4P7')}</p>
              <p className="mt-3">{t('legal.dsaS4P8')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS5')}</h2>
              <p>{t('legal.dsaS5P1')}</p>
              <p className="mt-3">{t('legal.dsaS5P2')}</p>
              <p className="mt-2 font-mono text-sm"><a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>{t('legal.dsaS5P3')}</a></p>
              <p className="mt-3">{t('legal.dsaS5P4')}</p>
              <p className="mt-3">{t('legal.dsaS5P5')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS5L1')}</li>
                <li>{t('legal.dsaS5L2')}</li>
                <li>{t('legal.dsaS5L3')}</li>
                <li>{t('legal.dsaS5L4')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS5P6')}</p>
              <p className="mt-3">{t('legal.dsaS5P7')}</p>
              <p className="mt-3">{t('legal.dsaS5P8')}</p>
              <p className="mt-3">{t('legal.dsaS5P9')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS6')}</h2>
              <p>{t('legal.dsaS6P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS6L1')}</li>
                <li>{t('legal.dsaS6L2')}</li>
                <li>{t('legal.dsaS6L3')}</li>
                <li>{t('legal.dsaS6L4')}</li>
                <li>{t('legal.dsaS6L5')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS6P2')}</p>
              <p className="mt-3">{t('legal.dsaS6P3')}</p>
              <p className="mt-3">{t('legal.dsaS6P4')}</p>
              <p className="mt-3">{t('legal.dsaS6P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS7')}</h2>
              <p>{t('legal.dsaS7P1')}</p>
              <p className="mt-3">{t('legal.dsaS7P2')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS7L1')}</li>
                <li>{t('legal.dsaS7L2')}</li>
                <li>{t('legal.dsaS7L3')}</li>
                <li>{t('legal.dsaS7L4')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS7P3')}</p>
              <p className="mt-3">{t('legal.dsaS7P4')}</p>
              <p className="mt-3">{t('legal.dsaS7P5')}</p>
              <p className="mt-3">{t('legal.dsaS7P6')}</p>
              <p className="mt-3">{t('legal.dsaS7P7')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS8')}</h2>
              <p>{t('legal.dsaS8P1')}</p>
              <p className="mt-3">{t('legal.dsaS8P2')}</p>
              <p className="mt-3">{t('legal.dsaS8P3')}</p>
              <p className="mt-3">{t('legal.dsaS8P4')}</p>
              <p className="mt-3">{t('legal.dsaS8P5')}</p>
              <p className="mt-3">{t('legal.dsaS8P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS9')}</h2>
              <p>{t('legal.dsaS9P1')}</p>
              <p className="mt-3">{t('legal.dsaS9P2')}</p>
              <p className="mt-3">{t('legal.dsaS9P3')}</p>
              <p className="mt-3">{t('legal.dsaS9P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS10')}</h2>
              <p>{t('legal.dsaS10P1')}</p>
              <p className="mt-3">{t('legal.dsaS10P2')}</p>
              <p className="mt-3">{t('legal.dsaS10P3')}</p>
              <p className="mt-3">{t('legal.dsaS10P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS11')}</h2>
              <p>{t('legal.dsaS11P1')}</p>
              <p className="mt-3">{t('legal.dsaS11P2')}</p>
              <p className="mt-3">{t('legal.dsaS11P3')}</p>
              <p className="mt-3">{t('legal.dsaS11P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS12')}</h2>
              <p>{t('legal.dsaS12P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.dsaS12L1')}</li>
                <li>{t('legal.dsaS12L2')}</li>
                <li>{t('legal.dsaS12L3')}</li>
              </ul>
              <p className="mt-3">{t('legal.dsaS12P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS13')}</h2>
              <p>{t('legal.dsaS13P1')}</p>
              <p className="mt-3">{t('legal.dsaS13P2')}</p>
              <p className="mt-3">{t('legal.dsaS13P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.dsaS14')}</h2>
              <p>{t('legal.dsaS14P1')}</p>
              <p className="mt-3">{t('legal.dsaS14P2')}</p>
              <p className="mt-3">{t('legal.dsaS14P3')}</p>
            </section>
          </div>

          <div className="mt-12 flex flex-wrap gap-4 text-sm">
            <Link href="/terms" style={{ color: GOLD_BRIGHT }}>Obchodné podmienky →</Link>
            <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>Ochrana údajov →</Link>
            <Link href="/license" style={{ color: GOLD_BRIGHT }}>Licencia →</Link>
          </div>

          <p className="mt-12 pt-8 text-sm" style={{ color: FAINT, borderTop: '1px solid #2a2620' }}>
            © {year} Radoslav Čornanič · TRČ · CMEP
          </p>
        </main>
      </div>
    </>
  );
}
