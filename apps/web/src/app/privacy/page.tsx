'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export default function PrivacyPage() {
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
              <Link href="/license" style={{ color: MUTED }}>{t('legal.license')}</Link>
              <Link href="/dsa" style={{ color: MUTED }}>DSA</Link>
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
              <p>{t('legal.privacyS1P1')}</p>
              <p className="mt-3">{t('legal.privacyS1P2')}</p>
              <p className="mt-3">{t('legal.privacyS1P3')}</p>
              <p className="mt-3">{t('legal.privacyS1P4')}</p>
              <p className="mt-3">{t('legal.privacyS1P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS2')}</h2>
              <p>{t('legal.privacyS2P1')}</p>
              <ul className="mt-3 space-y-1">
                <li>{t('legal.privacyS2L1')}</li>
                <li>{t('legal.privacyS2L2')}</li>
                <li>{t('legal.privacyS2L3')}</li>
                <li>{t('legal.privacyS2L4')}</li>
                <li>{t('legal.privacyS2L5')}</li>
                <li>{t('legal.privacyS2L6')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS2P2')}</p>
              <p className="mt-3">{t('legal.privacyS2P3')}</p>
              <p className="mt-3">{t('legal.privacyS2P4')}</p>
              <p className="mt-3">{t('legal.privacyS2P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS3')}</h2>
              <p>{t('legal.privacyS3P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS3L1')}</li>
                <li>{t('legal.privacyS3L2')}</li>
                <li>{t('legal.privacyS3L3')}</li>
                <li>{t('legal.privacyS3L4')}</li>
                <li>{t('legal.privacyS3L5')}</li>
                <li>{t('legal.privacyS3L6')}</li>
                <li>{t('legal.privacyS3L7')}</li>
                <li>{t('legal.privacyS3L8')}</li>
                <li>{t('legal.privacyS3L9')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS3P2')}</p>
              <p className="mt-3">{t('legal.privacyS3P3')}</p>
              <p className="mt-3">{t('legal.privacyS3P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS4')}</h2>
              <p>{t('legal.privacyS4P1')}</p>
              <ul className="mt-3 space-y-1">
                <li>{t('legal.privacyS4L1')}</li>
                <li>{t('legal.privacyS4L2')}</li>
                <li>{t('legal.privacyS4L3')}</li>
                <li>{t('legal.privacyS4L4')}</li>
                <li>{t('legal.privacyS4L5')}</li>
                <li>{t('legal.privacyS4L6')}</li>
                <li>{t('legal.privacyS4L7')}</li>
                <li>{t('legal.privacyS4L8')}</li>
                <li>{t('legal.privacyS4L9')}</li>
                <li>{t('legal.privacyS4L10')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS4P2')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS4L11')}</li>
                <li>{t('legal.privacyS4L12')}</li>
                <li>{t('legal.privacyS4L13')}</li>
                <li>{t('legal.privacyS4L14')}</li>
                <li>{t('legal.privacyS4L15')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS4P3')}</p>
              <p className="mt-3">{t('legal.privacyS4P4')}</p>
              <p className="mt-3">{t('legal.privacyS4P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS5')}</h2>
              <p>{t('legal.privacyS5P1')}</p>
              <p className="mt-3">{t('legal.privacyS5P2')}</p>
              <p className="mt-3">{t('legal.privacyS5P3')}</p>
              <p className="mt-3">{t('legal.privacyS5P4')}</p>
              <p className="mt-3">{t('legal.privacyS5P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS6')}</h2>
              <p>{t('legal.privacyS6P1')}</p>
              <p className="mt-3">{t('legal.privacyS6P2')}</p>
              <p className="mt-3">{t('legal.privacyS6P3')}</p>
              <p className="mt-3">{t('legal.privacyS6P4')}</p>
              <p className="mt-3">{t('legal.privacyS6P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS7')}</h2>
              <p>{t('legal.privacyS7P1')}</p>
              <p className="mt-3">{t('legal.privacyS7P2')}</p>
              <p className="mt-3">{t('legal.privacyS7P3')}</p>
              <p className="mt-3">{t('legal.privacyS7P4')}</p>
              <p className="mt-3">{t('legal.privacyS7P5')}</p>
              <p className="mt-3">{t('legal.privacyS7P6')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS8')}</h2>
              <p>{t('legal.privacyS8P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS8L1')}</li>
                <li>{t('legal.privacyS8L2')}</li>
                <li>{t('legal.privacyS8L3')}</li>
                <li>{t('legal.privacyS8L4')}</li>
                <li>{t('legal.privacyS8L5')}</li>
                <li>{t('legal.privacyS8L6')}</li>
                <li>{t('legal.privacyS8L7')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS8P2')}</p>
              <p className="mt-3">{t('legal.privacyS8P3')}</p>
              <p className="mt-3">{t('legal.privacyS8P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS9')}</h2>
              <p>{t('legal.privacyS9P1')}</p>
              <p className="mt-3">{t('legal.privacyS9P2')}</p>
              <p className="mt-3">{t('legal.privacyS9P3')}</p>
              <p className="mt-3">{t('legal.privacyS9P4')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS10')}</h2>
              <p>{t('legal.privacyS10P1')}</p>
              <p className="mt-3">{t('legal.privacyS10P2')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS10L1')}</li>
                <li>{t('legal.privacyS10L2')}</li>
                <li>{t('legal.privacyS10L3')}</li>
                <li>{t('legal.privacyS10L4')}</li>
                <li>{t('legal.privacyS10L5')}</li>
                <li>{t('legal.privacyS10L6')}</li>
                <li>{t('legal.privacyS10L7')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS10P3')}</p>
              <p className="mt-3">{t('legal.privacyS10P4')}</p>
              <p className="mt-3">{t('legal.privacyS10P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS11')}</h2>
              <p>{t('legal.privacyS11P1')}</p>
              <p className="mt-3">{t('legal.privacyS11P2')}</p>
              <p className="mt-3">{t('legal.privacyS11P3')}</p>
              <p className="mt-3">{t('legal.privacyS11P4')}</p>
              <p className="mt-3">{t('legal.privacyS11P5')}</p>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      <th className="border-b p-2 text-left" style={{ borderColor: '#2a2620', color: FG }}>Názov</th>
                      <th className="border-b p-2 text-left" style={{ borderColor: '#2a2620', color: FG }}>Poskytovateľ</th>
                      <th className="border-b p-2 text-left" style={{ borderColor: '#2a2620', color: FG }}>Účel</th>
                      <th className="border-b p-2 text-left" style={{ borderColor: '#2a2620', color: FG }}>Typ</th>
                      <th className="border-b p-2 text-left" style={{ borderColor: '#2a2620', color: FG }}>Expirácia</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr><td className="border-b p-2" style={{ borderColor: '#1a1612' }}>{t('legal.privacyS11P8')}</td></tr>
                  </tbody>
                </table>
              </div>

              <p className="mt-4">{t('legal.privacyS11P11')}</p>
              <p className="mt-3">{t('legal.privacyS11P12')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS12')}</h2>
              <p>{t('legal.privacyS12P1')}</p>
              <p className="mt-3">{t('legal.privacyS12P2')}</p>
              <p className="mt-3">{t('legal.privacyS12P3')}</p>
              <p className="mt-3">{t('legal.privacyS12P4')}</p>
              <p className="mt-3">{t('legal.privacyS12P5')}</p>
              <p className="mt-3">{t('legal.privacyS12P6')}</p>
              <p className="mt-3">{t('legal.privacyS12P7')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS13')}</h2>
              <p>{t('legal.privacyS13P1')}</p>
              <p className="mt-3">{t('legal.privacyS13P2')}</p>
              <p className="mt-3">{t('legal.privacyS13P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS14')}</h2>
              <p>{t('legal.privacyS14P1')}</p>
              <p className="mt-3">{t('legal.privacyS14P2')}</p>
              <p className="mt-3">{t('legal.privacyS14P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS15')}</h2>
              <p>{t('legal.privacyS15P1')}</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>{t('legal.privacyS15L1')}</li>
                <li>{t('legal.privacyS15L2')}</li>
                <li>{t('legal.privacyS15L3')}</li>
                <li>{t('legal.privacyS15L4')}</li>
                <li>{t('legal.privacyS15L5')}</li>
                <li>{t('legal.privacyS15L6')}</li>
                <li>{t('legal.privacyS15L7')}</li>
                <li>{t('legal.privacyS15L8')}</li>
                <li>{t('legal.privacyS15L9')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS15P2')}</p>
              <p className="mt-3">{t('legal.privacyS15P3')}</p>
              <p className="mt-3">{t('legal.privacyS15P4')}</p>
              <p className="mt-3">{t('legal.privacyS15P5')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS16')}</h2>
              <p>{t('legal.privacyS16P1')}</p>
              <p className="mt-3">{t('legal.privacyS16P2')}</p>
              <ul className="mt-3 space-y-1">
                <li><strong style={{ color: FG }}>{t('legal.privacyS16L1')}</strong></li>
                <li>{t('legal.privacyS16L2')}</li>
                <li>{t('legal.privacyS16L3')}</li>
                <li>{t('legal.privacyS16L4')}</li>
              </ul>
              <p className="mt-3">{t('legal.privacyS16P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS17')}</h2>
              <p>{t('legal.privacyS17P1')}</p>
              <p className="mt-3">{t('legal.privacyS17P2')}</p>
              <p className="mt-3">{t('legal.privacyS17P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS18')}</h2>
              <p>{t('legal.privacyS18P1')}</p>
              <p className="mt-3">{t('legal.privacyS18P2')}</p>
              <p className="mt-3">{t('legal.privacyS18P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS19')}</h2>
              <p>{t('legal.privacyS19P1')}</p>
              <p className="mt-3">{t('legal.privacyS19P2')}</p>
              <p className="mt-3">{t('legal.privacyS19P3')}</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>{t('legal.privacyS20')}</h2>
              <p>{t('legal.privacyS20P1')}</p>
              <p className="mt-3">{t('legal.privacyS20P2')}</p>
              <p className="mt-3">{t('legal.privacyS20P3')}</p>
              <p className="mt-3">{t('legal.privacyS20P4')}</p>
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
