'use client';
import { http } from '@/lib/api/http';

import { useState } from 'react';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#0b0b0b';
const FG = '#f3e6c4';
const MUTED = '#9a8f7c';

type Props = {
  reason?: 'free' | 'unknown' | string;
  companyId?: string;
};

export function AiUpgradePanel({ reason = 'free', companyId = '' }: Props) {
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
                {t('aiUpgrade.title')}
              </p>
              <p className="text-xs" style={{ color: MUTED }}>
                {noCompany ? t('aiUpgrade.requiresCompany') : t('aiUpgrade.proPrice')}
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
                </p>
                <a
                  href="/dashboard/companies/new"
                  className="inline-flex rounded-full px-4 py-2 text-sm font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  {t('aiUpgrade.createCompany')}
                </a>
              </>
            ) : (
              <>
                <p className="text-sm leading-relaxed" style={{ color: FG }}>
                  {t('aiUpgrade.descPro')} <strong>PRO</strong> {t('aiUpgrade.or')}{' '}
                  <strong>AI</strong> {t('aiUpgrade.planSuffix')}
                </p>
                <p className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                  {t('aiUpgrade.proPrice')}
                </p>
                <p className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                  {t('aiUpgrade.aiPrice')}
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
                    {t('aiUpgrade.contactBtn')}
                  </a>
                </div>
                <p className="text-[11px]" style={{ color: MUTED }}>
                  {t('aiUpgrade.onlinePayment')}
                    <button
                      type="button"
                      className="mt-2 block rounded-full px-4 py-2 text-sm"
                      onClick={() => {
                        void http.post<{ gw_url?: string }>("/billing/checkout", { company_id: companyId, tier: "pro" })
                          .then((r) => { if (r.gw_url) window.location.href = r.gw_url; })
                          .catch(() => { window.alert(t('aiUpgrade.gopayError')); });
                      }}
                    >
                      {t('aiUpgrade.gopayBtn')}
                    </button>
                </p>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
