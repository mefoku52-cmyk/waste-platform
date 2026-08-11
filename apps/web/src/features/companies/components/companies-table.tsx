'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCompanies } from '../hooks/use-companies';
import { companiesApi } from '../api';
import { cn } from '../../../lib/utils/cn';

export const CompaniesTable = () => {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useCompanies();

  const mutation = useMutation({
    mutationFn: ({ id, toStatus }: { id: string; toStatus: string }) =>
      companiesApi.transitionStatus(id, toStatus),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  });

  if (isLoading) return <div className="p-4 text-center">Načítavam firmy...</div>;
  if (error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní firiem.</div>;

  const companies = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      {mutation.isError && (
        <div className="bg-red-50 px-4 py-2 text-sm text-red-700">
          Prechod stavu zlyhal (skontroluj povolenú cestu draft → verification_submitted → verified).
        </div>
      )}
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Názov firmy</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">IČO</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Mesto</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Akcie</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {companies.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
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
                      company.status === 'verified'
                        ? 'bg-blue-100 text-blue-800'
                        : company.status === 'verification_submitted'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-gray-100 text-gray-800'
                    )}
                  >
                    {company.status || 'draft'}
                  </span>
                </td>
                <td className="px-4 py-2 space-x-2 whitespace-nowrap">
                  {company.status === 'draft' && (
                    <button
                      type="button"
                      disabled={mutation.isPending}
                      onClick={() =>
                        mutation.mutate({ id: company.id, toStatus: 'verification_submitted' })
                      }
                      className="rounded bg-amber-600 px-2 py-1 text-xs text-white hover:bg-amber-700 disabled:opacity-50"
                    >
                      Na overenie
                    </button>
                  )}
                  {company.status === 'verification_submitted' && (
                    <button
                      type="button"
                      disabled={mutation.isPending}
                      onClick={() => mutation.mutate({ id: company.id, toStatus: 'verified' })}
                      className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      Overiť
                    </button>
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
