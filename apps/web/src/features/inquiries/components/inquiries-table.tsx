'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useReceivedInquiries, useSentInquiries } from '../hooks/use-inquiries';
import { inquiriesApi } from '../api';

type Props = { mode: 'received' | 'sent' };

const statusClass = (status: string) => {
  if (status === 'answered') return 'bg-green-100 text-green-800';
  if (status === 'closed') return 'bg-gray-200 text-gray-700';
  return 'bg-amber-100 text-amber-800';
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

  if (q.isLoading) return <div className="p-4 text-center">Načítavam dopyty...</div>;
  if (q.error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní dopytov.</div>;

  const items = (q.data as any)?.items ?? [];
  const colSpan = mode === 'received' ? 6 : 5;

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      {mutation.isError && (
        <div className="bg-red-50 px-4 py-2 text-sm text-red-700">Nepodarilo sa zmeniť status.</div>
      )}
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Ponuka</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Správa</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">E-mail</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Telefón</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
            {mode === 'received' && (
              <th className="px-4 py-2 text-left font-medium text-gray-900">Akcie</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <tr>
              <td colSpan={colSpan} className="px-4 py-8 text-center text-gray-500">
                {mode === 'received' ? 'Žiadne prijaté dopyty.' : 'Žiadne odoslané dopyty.'}
              </td>
            </tr>
          ) : (
            items.map((inq: any) => (
              <tr key={inq.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">
                  {inq.listingTitle || '—'}
                </td>
                <td className="px-4 py-2 text-gray-900 max-w-xs truncate">{inq.message}</td>
                <td className="px-4 py-2 text-gray-700">{inq.contactEmail}</td>
                <td className="px-4 py-2 text-gray-700">{inq.contactPhone || '—'}</td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass(
                      inq.status
                    )}`}
                  >
                    {inq.status}
                  </span>
                </td>
                {mode === 'received' && (
                  <td className="px-4 py-2 space-x-2 whitespace-nowrap">
                    {inq.status !== 'answered' && (
                      <button
                        type="button"
                        disabled={mutation.isPending}
                        onClick={() => mutation.mutate({ id: inq.id, status: 'answered' })}
                        className="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        Odpovedané
                      </button>
                    )}
                    {inq.status !== 'closed' && (
                      <button
                        type="button"
                        disabled={mutation.isPending}
                        onClick={() => mutation.mutate({ id: inq.id, status: 'closed' })}
                        className="rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-700 disabled:opacity-50"
                      >
                        Uzavrieť
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
