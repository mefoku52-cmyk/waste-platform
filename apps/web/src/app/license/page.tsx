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
              <Link href="/privacy" style={{ color: MUTED }}>{t('legal.privacy')}</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('legal.kicker')}</p>
          <h1 className="mb-4 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('legal.licenseTitle')}
          </h1>
          <p className="mb-10 text-sm" style={{ color: FAINT }}>
            {t('legal.licenseMeta')} {today} · © {year} Radoslav Čornanič
          </p>

          <div className="space-y-10 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS1')}</h2>
              <p>
                {t('legal.licenseS1P1a')} <strong style={{ color: FG }}>CMEP</strong> {t('legal.licenseS1P1b')} <strong style={{ color: GOLD_BRIGHT }}>{t('legal.licenseS1P1c')}</strong> {t('legal.licenseS1P1d')}
              </p>
              <ul className="mt-4 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
              <p className="mt-4">{t('legal.licenseS1P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS2')}</h2>
              <p>{t('legal.licenseS2Intro')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.licenseS2L1')}</li>
                <li>{t('legal.licenseS2L2')}</li>
                <li>{t('legal.licenseS2L3')}</li>
                <li>{t('legal.licenseS2L4')}</li>
                <li>{t('legal.noDbSchema')}</li>
                <li>{t('legal.licenseS2L5')}</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS3')}</h2>
              <p>
                {t('legal.licenseS3P1a')} <strong style={{ color: FG }}>{t('legal.licenseS3P1b')}</strong> {t('legal.licenseS3P1c')}
              </p>
              <p className="mt-3">{t('legal.licenseS3P2a')} <strong style={{ color: FG }}>{t('legal.licenseS3P2b')}</strong> {t('legal.licenseS3P2c')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.licenseS3L1')}</li>
                <li>{t('legal.noReverse')}</li>
                <li>{t('legal.licenseS3L2')}</li>
                <li>{t('legal.licenseS3L3')}</li>
                <li>{t('legal.noDerived')}</li>
                <li>{t('legal.noBypass')}</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS4')}</h2>
              <p>
                {t('legal.licenseS4P1a')} <strong style={{ color: FG }}>{t('legal.licenseS4P1b')}</strong> {t('legal.licenseS4P1c')} <strong style={{ color: FG }}>{t('legal.licenseS4P1d')}</strong> {t('legal.licenseS4P1e')}
              </p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.viewContent')}</li>
                <li>{t('legal.storeContent')}</li>
                <li>{t('legal.notifyContent')}</li>
              </ul>
              <p className="mt-3">{t('legal.licenseS4P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS5')}</h2>
              <p>
                {t('legal.licenseS5P1a')} <strong style={{ color: FG }}>{t('legal.licenseS5P1b')}</strong> {t('legal.licenseS5P1c')} <strong style={{ color: FG }}>{t('legal.licenseS5P1d')}</strong>.
              </p>
              <p className="mt-3">{t('legal.licenseS5P2')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS6')}</h2>
              <p>{t('legal.licenseS6Intro')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li><strong style={{ color: FG }}>Next.js</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>React</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>FastAPI</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>PostgreSQL</strong> — PostgreSQL License</li>
                <li><strong style={{ color: FG }}>Redis / Valkey</strong> — BSD-3-Clause</li>
                <li><strong style={{ color: FG }}>Tailwind CSS</strong> — MIT License</li>
              </ul>
              <p className="mt-3">{t('legal.licenseS6P2a')} <strong style={{ color: FG }}>{t('legal.licenseS6P2b')}</strong> {t('legal.licenseS6P2c')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS7')}</h2>
              <p>
                {t('legal.licenseS7P1a')} <strong style={{ color: FG }}>Unsplash</strong> {t('legal.licenseS7P1b')}
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS8')}</h2>
              <p>
                {t('legal.licenseS8P1a')} <strong style={{ color: FG }}>{t('legal.licenseS8P1b')}</strong> {t('legal.licenseS8P1c')}
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS9')}</h2>
              <p>
                {t('legal.licenseS9P1a')} <strong style={{ color: FG }}>{t('legal.licenseS9P1b')}</strong>{t('legal.licenseS9P1c')}
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS10')}</h2>
              <p>{t('legal.licenseS10Intro')}</p>
              <ul className="mt-3 space-y-1">
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.licenseS11')}</h2>
              <p>{t('legal.licenseS11P1a')} {today} {t('legal.licenseS11P1b')}</p>
              <p className="mt-3">{t('legal.licenseS11P2')}</p>
            </section>

            <p className="pt-8 text-sm" style={{ color: FAINT }}>
              © {year} Radoslav Čornanič · TRČ · {t('legal.licenseCopyright')}
            </p>

            <div className="mt-10 flex flex-wrap gap-4 text-sm">
              <Link href="/terms" style={{ color: GOLD_BRIGHT }}>{t('legal.licenseLinkTerms')}</Link>
              <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>{t('legal.licenseLinkPrivacy')}</Link>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
