'use client';
import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function PrivacyPage() {
  const { t } = useT();
  const today = new Date().toLocaleDateString();

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
              <Link href="/license" style={{ color: MUTED }}>{t('legal.license')}</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('legal.kicker')}</p>
          <h1 className="mb-10 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('legal.privacyTitle')}
          </h1>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS1')}</h2>
              <p>{t('legal.privacyS1Intro')}</p>
              <ul className="mt-3 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS2')}</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS2L1')}</li>
                <li>{t('legal.privacyS2L2')}</li>
                <li>{t('legal.privacyS2L3')}</li>
                <li>{t('legal.privacyS2L4')}</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS3')}</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS3L1')}</li>
                <li>{t('legal.privacyS3L2')}</li>
                <li>{t('legal.notifications')}</li>
                <li>{t('legal.security')}</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS4')}</h2>
              <p>{t('legal.privacyS4P1')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS5')}</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.rightAccess')}</li>
                <li>{t('legal.rightCorrect')}</li>
                <li>{t('legal.privacyS5L1')}</li>
                <li>{t('legal.rightObject')}</li>
                <li>{t('legal.privacyS5L2')}</li>
              </ul>
              <p className="mt-3">
                {t('legal.privacyS5P1a')} <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a>{t('legal.privacyS5P1b')}
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS6')}</h2>
              <p>{t('legal.privacyS6P1')}</p>
            </section>

            <p className="pt-8 text-sm" style={{ color: '#6e6658' }}>
              {t('legal.privacyUpdated')} {today}
            </p>
          </div>
        </main>
      </div>
    </>
  );
}
