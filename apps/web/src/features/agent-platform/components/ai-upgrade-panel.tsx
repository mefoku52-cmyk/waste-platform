'use client';

import { useState } from 'react';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#0b0b0b';
const FG = '#f3e6c4';
const MUTED = '#9a8f7c';

type Props = {
  reason?: 'free' | 'unknown' | string;
};

export function AiUpgradePanel({ reason = 'free' }: Props) {
  const { t } = useT();
  const [open, setOpen] = useState(false);

  const noCompany = reason === 'unknown';

  return (
    <>
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="AI asistent (PRO)"
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-2xl transition hover:scale-105"
          style={{ background: '#17140d', color: GOLD, border: `1px solid ${GOLD}` }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            <circle cx="18" cy="6" r="4" fill="#c9a84c" stroke="none" />
          </svg>
        </button>
      ) : (
        <div
          className="fixed bottom-6 right-6 z-50 flex w-[360px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border shadow-2xl"
          style={{ borderColor: 'rgba(201,168,76,0.35)', background: BG }}
        >
          <div
            className="flex items-center justify-between border-b px-4 py-3"
            style={{ borderColor: 'rgba(201,168,76,0.25)' }}
          >
            <div>
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.22em]"
                style={{ color: GOLD }}
              >
                AI asistent
              </p>
              <p className="text-xs" style={{ color: MUTED }}>
                {noCompany ? 'Vyžaduje firmu' : 'PRO predplatné'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full px-2 text-lg"
              style={{ color: MUTED }}
              aria-label="Zavrieť"
            >
              ×
            </button>
          </div>

          <div className="space-y-4 p-4">
            {noCompany ? (
              <>
                <p className="text-sm leading-relaxed" style={{ color: FG }}>
                  {t('aiUpgrade.onlyForCompanies')}
                  Najprv si vytvor firmu a over ju.
                </p>
                <a
                  href="/dashboard/companies/new"
                  className="inline-flex rounded-full px-4 py-2 text-sm font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Vytvoriť firmu
                </a>
              </>
            ) : (
              <>
                <p className="text-sm leading-relaxed" style={{ color: FG }}>
                  AI asistent je dostupný v <strong>PRO</strong> alebo{' '}
                  <strong>AI</strong> predplatnom.
                </p>
                <p className="text-sm" style={{ color: GOLD_BRIGHT }}>
                  PRO · 29 €/mesiac
                </p>
                <ul className="space-y-1 text-xs" style={{ color: MUTED }}>
                  <li>· Neobmedzený počet ponúk</li>
                  <li>· AI asistent s vyhľadávaním</li>
                  <li>· Predikcie a odporúčania</li>
                </ul>
                <div className="pt-2">
                  <a
                    href="mailto:trc-cmep@gmail.com?subject=CMEP%20PRO%20upgrade"
                    className="inline-flex rounded-full px-4 py-2 text-sm font-semibold"
                    style={{ background: GOLD, color: BG }}
                  >
                    Kontaktovať · Upgrade na PRO
                  </a>
                </div>
                <p className="text-[11px]" style={{ color: MUTED }}>
                  Online platba (GoPay) — pripravujeme.
                </p>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
