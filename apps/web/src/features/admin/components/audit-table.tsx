'use client';

import { useAudit } from '../hooks/use-audit';

export const AuditTable = () => {
  const { data, isLoading, error } = useAudit();
  const items = (data as any)?.items ?? [];

  if (isLoading) {
    return <div className="p-4 text-center text-sm text-gray-500">Načítavam audit...</div>;
  }
  if (error) {
    return <div className="p-4 text-center text-sm text-red-600">Audit sa nepodarilo načítať.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Akcia</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Typ</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Detail</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                Žiadne audit záznamy.
              </td>
            </tr>
          ) : (
            items.map((row: any) => (
              <tr key={row.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">{row.action}</td>
                <td className="px-4 py-2 text-gray-700">{row.targetType || row.target_type}</td>
                <td className="px-4 py-2 text-gray-600 max-w-xs truncate">{row.details || '—'}</td>
                <td className="px-4 py-2 text-gray-700">{row.status}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
