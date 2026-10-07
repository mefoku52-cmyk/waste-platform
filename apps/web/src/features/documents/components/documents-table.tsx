'use client';

import { useDocuments } from '../hooks/use-documents';
import { useT } from '@/lib/i18n/context';

export const DocumentsTable = () => {
  const { t } = useT();
  const { data, isLoading, error } = useDocuments();
  const items = (data as any)?.items ?? [];

  if (isLoading) {
    return <div className="p-4 text-center text-sm text-gray-500">{t('documents.tableLoading')}</div>;
  }
  if (error) {
    return <div className="p-4 text-center text-sm text-red-600">{t('documents.tableError')}</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.title')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('documents.typeCol')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.status')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.file')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                {t('documents.empty')}
              </td>
            </tr>
          ) : (
            items.map((doc: any) => (
              <tr key={doc.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">{doc.title}</td>
                <td className="px-4 py-2 text-gray-700">{doc.documentType || doc.document_type}</td>
                <td className="px-4 py-2 text-gray-700">{doc.status}</td>
                <td className="px-4 py-2">
                  {(doc.fileUrl || doc.file_url) ? (
                    <a
                      href={doc.fileUrl || doc.file_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {t('documents.open')}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
