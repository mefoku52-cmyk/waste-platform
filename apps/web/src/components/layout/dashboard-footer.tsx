'use client';

import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export function DashboardFooter() {
  return (
    <footer
      className="border-t"
      style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}
    >
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <img src="/trc-mark.jpg" alt="TRČ" className="h-12 w-12 rounded-full object-cover" />
            <div>
              <p className="text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>
                CMEP
              </p>
              <p className="text-xs" style={{ color: MUTED }}>
                Circular Materials Exchange Platform
              </p>
            </div>
          </div>
          <p className="text-sm" style={{ color: MUTED }}>
            Súkromná burza. Overené firmy. Skryté kontakty.
          </p>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-6 md:grid-cols-3">
          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              TRH
            </p>
            <Link href="/dashboard" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Trhovisko
            </Link>
            <Link href="/dashboard/listings" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Moje ponuky
            </Link>
            <Link href="/dashboard/companies/new" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Pridať firmu
            </Link>
          </div>

          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              PRÁVNE
            </p>
            <Link href="/terms" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Obchodné podmienky
            </Link>
            <Link href="/privacy" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Ochrana údajov
            </Link>
            <Link href="/license" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              Licencia
            </Link>
          </div>

          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              KONTAKT
            </p>
            <a href="mailto:orlovic1611@gmail.com" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              orlovic1611@gmail.com
            </a>
            <p className="py-1 text-sm" style={{ color: MUTED }}>
              Ulič 63, 067 67 Ulič
            </p>
            <p className="py-1 text-sm" style={{ color: MUTED }}>
              Slovenská republika
            </p>
          </div>
        </div>

        <div
          className="mt-10 flex flex-wrap items-center justify-between gap-2 border-t pt-6 text-xs"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)', color: FAINT }}
        >
          <span>© {new Date().getFullYear()} Radoslav Čornanič · TRČ</span>
          <span>JAZYK: SK</span>
        </div>
      </div>
    </footer>
  );
}
