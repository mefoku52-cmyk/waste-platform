'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export function DashboardFooter() {
  const { t } = useT();
  const year = new Date().getFullYear();

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
              <p className="text-2xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
                CMEP
              </p>
              <p className="text-xs" style={{ color: MUTED }}>
                Circular Materials Exchange Platform
              </p>
            </div>
          </div>
          <p className="text-sm" style={{ color: MUTED }}>
            {t('footer.tagline')}
          </p>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-6 md:grid-cols-3">
          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              {t('footer.marketSection')}
            </p>
            <Link href="/dashboard" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.marketplace')}
            </Link>
            <Link href="/dashboard/listings" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.myListings')}
            </Link>
            <Link href="/dashboard/companies/new" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.addCompany')}
            </Link>
          </div>

          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              {t('footer.legalSection')}
            </p>
            <Link href="/terms" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.terms')}
            </Link>
            <Link href="/privacy" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.privacy')}
            </Link>
            <Link href="/license" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.license')}
            </Link>
            <Link href="/o-nas" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              {t('footer.about')}
            </Link>
          </div>

          <div>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              {t('footer.contactSection')}
            </p>
            <a href="mailto:trc-cmep@gmail.com" className="block py-1 text-sm" style={{ color: GOLD_BRIGHT }}>
              trc-cmep@gmail.com
            </a>
            {!!t('footer.address') && (
              <p className="py-1 text-sm" style={{ color: MUTED }}>
                {t('footer.address')}
              </p>
            )}
            {!!t('footer.country') && (
              <p className="py-1 text-sm" style={{ color: MUTED }}>
                {t('footer.country')}
              </p>
            )}
          </div>
        </div>

        <div
          className="mt-10 flex flex-wrap items-center justify-between gap-2 border-t pt-6 text-xs"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)', color: FAINT }}
        >
          <span>© {year} Radoslav Čornanič · TRČ</span>
          <span>JAZYK: SK</span>
        </div>
      </div>
    </footer>
  );
}
