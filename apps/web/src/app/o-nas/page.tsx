'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const FAQ_KEYS = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6'] as const;

export default function AboutPage() {
  const { t } = useT();
  const year = new Date().getFullYear();

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <header
          className="border-b"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
        >
          <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: '1.25rem' }}>CMEP</span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/" style={{ color: MUTED }}>{t('common.back')}</Link>
              <Link href="/login" style={{ color: MUTED }}>{t('common.login')}</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            {t('about.eyebrow')}
          </p>
          <h1 className="mb-6 text-4xl leading-tight md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            {t('about.title')}
          </h1>
          <p className="mb-12 text-base leading-relaxed" style={{ color: MUTED }}>
            {t('about.intro')}
          </p>

          <section className="mb-12">
            <h2 className="mb-4 text-2xl" style={{ fontFamily: 'DM Serif Display, serif' }}>{t('about.firmSection')}</h2>
            <div className="space-y-3 text-base" style={{ color: MUTED }}>
              <p><strong style={{ color: FG }}>{t('about.operator')}:</strong> Radoslav Čornanič</p>
              <p><strong style={{ color: FG }}>{t('about.ico')}:</strong> 51745666</p>
              <p><strong style={{ color: FG }}>{t('about.focus')}:</strong> {t('about.focusText')}</p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="mb-4 text-2xl" style={{ fontFamily: 'DM Serif Display, serif' }}>{t('about.contactSection')}</h2>
            <div className="space-y-3 text-base" style={{ color: MUTED }}>
              <p>
                <strong style={{ color: FG }}>{t('about.email')}:</strong>{' '}
                <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a>
              </p>
              <p>
                <strong style={{ color: FG }}>{t('about.phone')}:</strong>{' '}
                <a href="tel:+421910617338" style={{ color: GOLD_BRIGHT }}>+421 910 617 338</a>
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="mb-6 text-2xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
              {t('about.faqSection')}
            </h2>
            <div className="space-y-3">
              {FAQ_KEYS.map((k) => (
                <details
                  key={k}
                  className="rounded-2xl border p-5"
                  style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
                >
                  <summary className="cursor-pointer text-lg" style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}>
                    {t(`about.faq.${k}.q`)}
                  </summary>
                  <p className="mt-3 text-sm leading-relaxed" style={{ color: MUTED }}>
                    {t(`about.faq.${k}.a`)}
                  </p>
                </details>
              ))}
            </div>
          </section>

          <section className="border-t pt-8" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              {t('about.legalSection')}
            </p>
            <div className="flex flex-wrap gap-4 text-sm">
              <Link href="/terms" style={{ color: GOLD_BRIGHT }}>{t('about.terms')}</Link>
              <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>{t('about.privacy')}</Link>
              <Link href="/license" style={{ color: GOLD_BRIGHT }}>{t('about.license')}</Link>
            </div>
          </section>

          <p className="mt-12 text-xs" style={{ color: FAINT }}>
            © {year} Radoslav Čornanič · TRČ · {t('about.copyright')}
          </p>
        </main>
      </div>
    </>
  );
}
