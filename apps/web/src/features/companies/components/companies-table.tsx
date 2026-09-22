
async function checkRpoBeforeVerify(ico?: string | null) {
  const raw = (ico || "").trim();
  if (!raw) return "IČO chýba. RPO sa neda overit.";
  try {
    const mod = await import("../api");
    const api = (mod as any).companiesApi || (mod as any).companyApi;
    const res = await api.rpoCheck(raw);
    if (!res.exists) {
      if (res.reason === "ico_invalid") return "IČO je neplatné (musi mat 8 cislic). RPO: neexistuje.";
      if (res.reason === "not_found") return "IČO " + (res.ico || raw) + " v RPO neexistuje.";
      return "RPO overenie zlyhalo (" + res.reason + ").";
    }
    return "RPO OK: " + (res.legalName || "") + (res.city ? " · " + res.city : "");
  } catch (e: any) {
    return "RPO sa nepodarilo overit.";
  }
}

'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCompanies } from '../hooks/use-companies';
import { companiesApi } from '../api';
import { cn } from '../../../lib/utils/cn';
import { useIsPlatformAdmin } from '../../auth/hooks/use-is-platform-admin';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const STATUS_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  draft:                  { bg: 'rgba(110,102,88,0.15)', text: '#9a8f7c', label: 'Draft' },
  verification_submitted: { bg: 'rgba(201,168,76,0.15)', text: '#e8d48b', label: 'Čaká na overenie' },
  verified:               { bg: 'rgba(46,160,67,0.15)',  text: '#5fd17a', label: 'Overená' },
  rejected:               { bg: 'rgba(196,92,74,0.15)',  text: '#e8a598', label: 'Zamietnutá' },
  suspended:              { bg: 'rgba(196,92,74,0.20)',  text: '#f0b8a8', label: 'Pozastavená' },
  inactive:               { bg: 'rgba(80,80,80,0.20)',   text: '#a8a8a8', label: 'Neaktívna' },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLE[status] ?? STATUS_STYLE.draft;
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: s.bg, color: s.text }}
    >
      {s.label}
    </span>
  );
}

function ActionButton({
  onClick,
  disabled,
  variant,
  children,
}: {
  onClick: () => void;
  disabled: boolean;
  variant: 'primary' | 'danger' | 'warn';
  children: React.ReactNode;
}) {
  const styles = {
    primary: { background: '#2ea043', color: '#fff' },
    danger: { background: '#c45c4a', color: '#fff' },
    warn: { background: GOLD, color: '#090807' },
  }[variant];

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="rounded px-3 py-1 text-xs font-semibold disabled:opacity-50 transition-opacity hover:opacity-90"
      style={styles}
    >
      {children}
    </button>
  );
}

import { AcceptedMaterialsCell } from './accepted-materials-cell';
export const CompaniesTable = () => {
  const { t } = useT();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useCompanies();
  const isAdmin = useIsPlatformAdmin();

  const mutation = useMutation({
    mutationFn: ({ id, toStatus }: { id: string; toStatus: string }) =>
      (async () => {
        if (toStatus === 'verified') {
          const msg = await checkRpoBeforeVerify(ico);
          window.alert(msg);
        }
        return companiesApi.transitionStatus(id, toStatus);
      })(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  });

  if (isLoading) return <div className="p-4 text-center" style={{ color: MUTED }}>{t('tables.loading')}</div>;
  if (error) return <div className="p-4 text-center" style={{ color: '#e8a598' }}>{t('tables.error')}</div>;

  const companies = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
      {mutation.isError && (
        <div className="px-4 py-2 text-sm" style={{ background: 'rgba(196,92,74,0.12)', color: '#e8a598' }}>
          {(mutation.error as any)?.message || t('tables.adminOnly')}
        </div>
      )}

      <table className="min-w-full text-sm" style={{ color: FG }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(201,168,76,0.15)' }}>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.companyName')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.ico')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.city')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>Material</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.status')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.actions')}</th>
          </tr>
        </thead>
        <tbody>
          {companies.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-10 text-center text-sm" style={{ color: MUTED }}>
                {t('tables.empty')}
              </td>
            </tr>
          ) : (
            companies.map((company: any) => {
              const status = company.status || 'draft';
              return (
                <tr key={company.id} style={{ borderBottom: '1px solid rgba(201,168,76,0.08)' }}>
                  <td className="px-4 py-3 font-medium" style={{ color: FG }}>
                    {company.legalName || company.name}
                  </td>
                  <td className="px-4 py-3" style={{ color: MUTED }}>
                    {company.registrationNumber || company.registration_number}
                  </td>
                  <td className="px-4 py-3" style={{ color: MUTED }}>{company.city}</td>
                  <td className="px-4 py-3"><AcceptedMaterialsCell id={company.id} value={company.acceptedMaterialTypes || company.accepted_material_types} /></td>
                  <td className="px-4 py-3">
                    <StatusBadge status={status} />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex flex-wrap gap-2">
                      {/* OWNER akcie (pre všetkých, backend kontroluje) */}
                      {status === 'draft' && (
                        <ActionButton
                          variant="warn"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: company.id, toStatus: 'verification_submitted' })}
                        >
                          {t('tables.requestVerify')}
                        </ActionButton>
                      )}

                      {/* ADMIN akcie */}
                      {isAdmin && status === 'verification_submitted' && (
                        <>
                          <ActionButton
                            variant="primary"
                            disabled={mutation.isPending}
                            onClick={() => mutation.mutate({ id: company.id, toStatus: 'verified', ico: company.taxIdentifier || company.tax_identifier })}
                          >
                            Overiť
                          </ActionButton>
                          <ActionButton
                            variant="danger"
                            disabled={mutation.isPending}
                            onClick={() => mutation.mutate({ id: company.id, toStatus: 'rejected' })}
                          >
                            Zamietnuť
                          </ActionButton>
                        </>
                      )}

                      {isAdmin && status === 'verified' && (
                        <ActionButton
                          variant="danger"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: company.id, toStatus: 'suspended' })}
                        >
                          Pozastaviť
                        </ActionButton>
                      )}

                      {isAdmin && status === 'suspended' && (
                        <ActionButton
                          variant="primary"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: company.id, toStatus: 'verified', ico: company.taxIdentifier || company.tax_identifier })}
                        >
                          Reaktivovať
                        </ActionButton>
                      )}

                      {isAdmin && status === 'rejected' && (
                        <ActionButton
                          variant="warn"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: company.id, toStatus: 'draft' })}
                        >
                          Obnoviť do draft
                        </ActionButton>
                      )}

                      {isAdmin && status === 'inactive' && (
                        <ActionButton
                          variant="primary"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: company.id, toStatus: 'verified', ico: company.taxIdentifier || company.tax_identifier })}
                        >
                          Aktivovať
                        </ActionButton>
                      )}

                      {!isAdmin && status === 'verification_submitted' && (
                        <span className="text-xs" style={{ color: GOLD_BRIGHT }}>
                          {t('tables.awaitingAdmin')}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {isAdmin && (
        <div className="border-t px-4 py-2 text-xs" style={{ borderColor: 'rgba(201,168,76,0.15)', color: FAINT }}>
          {t('tables.adminMode')}
        </div>
      )}
    </div>
  );
};
