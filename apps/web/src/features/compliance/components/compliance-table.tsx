'use client';

import { useCompliance } from '../hooks/use-compliance';
import { useT } from '@/lib/i18n/context';

export const ComplianceTable = () => {
  const { t } = useT();
  const { data, isLoading, error } = useCompliance();
  const items = (data as any)?.items ?? [];

  if (isLoading) return <div className="p-4 text-center text-sm text-gray-500">{t('compliance.loading')}</div>;
  if (error) return <div className="p-4 text-center text-sm text-red-600">{t('compliance.error')}</div>;

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.regulation')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.document')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.status')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.note')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                {t('compliance.empty')}
              </td>
            </tr>
          ) : (
            items.map((row: any) => (
              <tr key={row.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">{row.regulationType}</td>
                <td className="px-4 py-2 text-gray-700">{row.documentRef || '—'}</td>
                <td className="px-4 py-2 text-gray-700">{row.status}</td>
                <td className="px-4 py-2 text-gray-600 max-w-xs truncate">{row.notes || '—'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
