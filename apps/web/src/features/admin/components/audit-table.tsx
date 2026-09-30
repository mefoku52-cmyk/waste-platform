'use client';

import { useAudit } from '../hooks/use-audit';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

type AuditEntry = {
  id: string;
  actorUserId?: string;
  action?: string;
  targetType?: string;
  targetId?: string | null;
  details?: string | null;
  status?: string;
  createdAt?: string;
};

const ACTION_LABEL: Record<string, string> = {
  'company.status_changed': 'Zmena stavu firmy',
  'listing.published':      'Publikovanie ponuky',
  'listing.created':        'Vytvorenie ponuky',
  'company.verified':       'Overenie firmy',
  'company.suspended':      'Pozastavenie firmy',
};

function formatDate(iso?: string): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString('sk-SK', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export const AuditTable = () => {
  const { data, isLoading, error } = useAudit();

  if (isLoading) {
    return <div className="py-6 text-center text-sm" style={{ color: MUTED }}>Načítavam audit…</div>;
  }

  if (error) {
    return <div className="py-6 text-center text-sm" style={{ color: '#e8a598' }}>Audit sa nepodarilo načítať.</div>;
  }

  const raw: any = data;
  const items: AuditEntry[] = Array.isArray(raw)
    ? raw
    : raw?.items ?? raw?.data?.items ?? raw?.data ?? [];

  if (items.length === 0) {
    return (
      <div className="py-10 text-center text-sm" style={{ color: MUTED }}>
        Žiadne audit záznamy.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
      <table className="min-w-full text-sm" style={{ color: FG }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(201,168,76,0.15)' }}>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.date')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.action')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.target')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.details')}</th>
            <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.2em] font-semibold" style={{ color: GOLD }}>{t('tables.status')}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((entry) => (
            <tr key={entry.id} style={{ borderBottom: '1px solid rgba(201,168,76,0.08)' }}>
              <td className="px-4 py-3 whitespace-nowrap" style={{ color: MUTED, fontSize: '12px' }}>
                {formatDate(entry.createdAt)}
              </td>
              <td className="px-4 py-3" style={{ color: GOLD_BRIGHT }}>
                {ACTION_LABEL[entry.action || ''] || entry.action || '—'}
              </td>
              <td className="px-4 py-3" style={{ color: MUTED, fontSize: '12px' }}>
                {entry.targetType || '—'}
                {entry.targetId ? (
                  <span style={{ color: FAINT }}> · {String(entry.targetId).slice(0, 8)}…</span>
                ) : null}
              </td>
              <td className="px-4 py-3 text-xs" style={{ color: MUTED }}>
                {entry.details || '—'}
              </td>
              <td className="px-4 py-3">
                <span
                  className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em]"
                  style={{
                    background: entry.status === 'success' ? 'rgba(46,160,67,0.15)' : 'rgba(196,92,74,0.15)',
                    color: entry.status === 'success' ? '#5fd17a' : '#e8a598',
                  }}
                >
                  {entry.status || 'success'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
