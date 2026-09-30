'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useReceivedInquiries, useSentInquiries } from '../hooks/use-inquiries';
import { inquiriesApi } from '../api';
import { useT } from '@/lib/i18n/context';

type Props = { mode: 'received' | 'sent' };

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const statusStyle = (status: string): { bg: string; color: string; label: string } => {
  if (status === 'answered') return { bg: 'rgba(110,231,167,0.15)', color: '#6ee7a7', label: 'Odpovedané' };
  if (status === 'closed') return { bg: 'rgba(154,143,124,0.15)', color: MUTED, label: 'Uzavreté' };
  return { bg: 'rgba(201,168,76,0.18)', color: GOLD_BRIGHT, label: 'Čaká' };
};

export const InquiriesTable = ({ mode }: Props) => {
  const queryClient = useQueryClient();
  const received = useReceivedInquiries();
  const sent = useSentInquiries();
  const q = mode === 'received' ? received : sent;

  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'answered' | 'closed' }) =>
      inquiriesApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] });
    },
  });

  if (q.isLoading) {
    return (
      <p className="py-8 text-center text-sm" style={{ color: MUTED }}>
        Načítavam dopyty…
      </p>
    );
  }
  if (q.error) {
    return (
      <p className="py-8 text-center text-sm" style={{ color: '#f0bbb0' }}>
        Chyba pri načítaní dopytov.
      </p>
    );
  }

  const items = (q.data as any)?.items ?? [];
  const colSpan = mode === 'received' ? 6 : 5;

  return (
    <div className="overflow-x-auto">
      {mutation.isError && (
        <p className="mb-3 text-sm" style={{ color: '#f0bbb0' }}>
          Nepodarilo sa zmeniť status.
        </p>
      )}

      {items.length === 0 ? (
        <p className="py-8 text-center text-sm" style={{ color: MUTED }}>
          {mode === 'received' ? 'Žiadne prijaté dopyty.' : 'Žiadne odoslané dopyty.'}
        </p>
      ) : (
        <table className="min-w-full text-sm">
          <thead>
            <tr style={{ borderBottom: `1px solid color-mix(in srgb, #c9a84c 25%, transparent)` }}>
              <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>{t('tables.title')}</th>
              <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>{t('tables.note')}</th>
              <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>E-mail</th>
              <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>{t('tables.phone')}</th>
              <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>{t('tables.status')}</th>
              {mode === 'received' && (
                <th className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]" style={{ color: GOLD }}>{t('tables.actions')}</th>
              )}
            </tr>
          </thead>
          <tbody>
            {items.map((inq: any) => {
              const st = statusStyle(inq.status);
              return (
                <tr
                  key={inq.id}
                  className="transition-colors"
                  style={{ borderBottom: '1px solid color-mix(in srgb, #c9a84c 12%, transparent)' }}
                >
                  <td className="px-3 py-4 font-medium" style={{ color: FG }}>
                    {inq.listingTitle || '—'}
                  </td>
                  <td className="max-w-xs truncate px-3 py-4" style={{ color: MUTED }}>
                    {inq.message}
                  </td>
                  <td className="px-3 py-4" style={{ color: MUTED }}>
                    {inq.contactEmail}
                  </td>
                  <td className="px-3 py-4" style={{ color: MUTED }}>
                    {inq.contactPhone || '—'}
                  </td>
                  <td className="px-3 py-4">
                    <span
                      className="inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider"
                      style={{ background: st.bg, color: st.color }}
                    >
                      {st.label}
                    </span>
                  </td>
                  {mode === 'received' && (
                    <td className="space-x-2 whitespace-nowrap px-3 py-4">
                      {inq.status !== 'answered' && (
                        <button
                          type="button"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: inq.id, status: 'answered' })}
                          className="rounded-full px-3 py-1.5 text-xs font-semibold transition disabled:opacity-50"
                          style={{ background: GOLD, color: '#090807' }}
                        >
                          Odpovedané
                        </button>
                      )}
                      {inq.status !== 'closed' && (
                        <button
                          type="button"
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ id: inq.id, status: 'closed' })}
                          className="rounded-full border px-3 py-1.5 text-xs font-semibold transition disabled:opacity-50"
                          style={{ borderColor: 'color-mix(in srgb, #9a8f7c 40%, transparent)', color: MUTED }}
                        >
                          Uzavrieť
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};
