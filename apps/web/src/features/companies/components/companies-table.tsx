'use client';

import { useCompanies } from '../hooks/use-companies';
import { cn } from '../../../lib/utils/cn';

export const CompaniesTable = () => {
  const { data, isLoading, error } = useCompanies();

  if (isLoading) return <div className="p-4 text-center">Načítavam firmy...</div>;
  if (error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní firiem.</div>;

  // Backend vracia { items: [], meta: {} }
  const companies = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Názov firmy</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">IČO</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Mesto</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {companies.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                Žiadne firmy neboli nájdené.
              </td>
            </tr>
          ) : (
            companies.map((company: any) => (
              <tr key={company.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">
                  {company.legalName || company.name}
                </td>
                <td className="px-4 py-2 text-gray-700">
                  {company.registrationNumber || company.registration_number}
                </td>
                <td className="px-4 py-2 text-gray-700">{company.city}</td>
                <td className="px-4 py-2">
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      company.status === 'verified' || company.verifiedAt
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    )}
                  >
                    {company.status || 'draft'}
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
