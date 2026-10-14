import Link from 'next/link';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

// Server component (NIE 'use client'): klientsky not-found boundary sa streamuje,
// takže notFound() by vrátil stav 200 (soft-404). Serverová verzia vracia 404.
export const metadata = {
  title: 'Stránka neexistuje · CMEP',
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center"
      style={{ background: BG, color: FG }}
    >
      <p className="text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
        404
      </p>
      <h1
        className="text-2xl md:text-3xl"
        style={{ fontFamily: 'DM Serif Display, serif' }}
      >
        Táto stránka neexistuje
      </h1>
      <p className="max-w-md text-sm" style={{ color: MUTED }}>
        Odkaz, ktorý si otvoril, nevedie na žiadnu stránku. Vráť sa na úvodnú
        stránku alebo do svojho dashboardu.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link
          href="/"
          className="rounded-full px-5 py-2 text-sm font-semibold"
          style={{ background: GOLD, color: BG }}
        >
          Úvodná stránka
        </Link>
        <Link
          href="/dashboard"
          className="rounded-full px-5 py-2 text-sm font-semibold"
          style={{ background: 'transparent', color: FG, border: `1px solid ${MUTED}` }}
        >
          Dashboard
        </Link>
      </div>
    </div>
  );
}
