'use client';

import { useReceivedInquiries, useSentInquiries } from '../hooks/use-inquiries';

type Props = { mode: 'received' | 'sent' };

export const InquiriesTable = ({ mode }: Props) => {
  const received = useReceivedInquiries();
  const sent = useSentInquiries();
  const q = mode === 'received' ? received : sent;

  if (q.isLoading) return <div className="p-4 text-center">Načítavam dopyty...</div>;
  if (q.error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní dopytov.</div>;

  const items = (q.data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Správa</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">E-mail</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Telefón</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                {mode === 'received' ? 'Žiadne prijaté dopyty.' : 'Žiadne odoslané dopyty.'}
              </td>
            </tr>
          ) : (
            items.map((inq: any) => (
              <tr key={inq.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-900 max-w-xs truncate">{inq.message}</td>
                <td className="px-4 py-2 text-gray-700">{inq.contactEmail}</td>
                <td className="px-4 py-2 text-gray-700">{inq.contactPhone || '—'}</td>
                <td className="px-4 py-2">
                  <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                    {inq.status}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
