'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useListings } from '../hooks/use-listings';
import { useCompanies } from '../../companies/hooks/use-companies';
import { listingsApi } from '../api';
import { cn } from '../../../lib/utils/cn';
import { useT } from "@/lib/i18n/context";

export const ListingsTable = () => {
  const { t } = useT();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useListings();
  const { data: companiesData } = useCompanies();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const companies = (companiesData as any)?.items ?? [];
  const verified =
    companies.length > 0 && companies.every((c: any) => c.status === 'verified')
      ? true
      : companies.some((c: any) => c.status === 'verified');

  // map companyId → status
  const companyStatusById: Record<string, string> = {};
  for (const c of companies) {
    if (c.id) companyStatusById[String(c.id)] = c.status || 'draft';
  }

  const handlePublish = async (id: string, companyId?: string) => {
    setActionError(null);
    const st = companyId ? companyStatusById[String(companyId)] : undefined;
    const can =
      st === 'verified' ||
      (!companyId && verified);
    if (!can) {
      setActionError('Publikovať môže len overená firma (status verified). Najprv over firmu.');
      return;
    }
    setBusyId(id);
    try {
      await listingsApi.publishListing(id);
      await queryClient.invalidateQueries({ queryKey: ['listings'] });
      await queryClient.invalidateQueries({ queryKey: ['marketplace'] });
    } catch (e: any) {
      setActionError(e?.message || 'Publikácia zlyhala.');
    } finally {
      setBusyId(null);
    }
  };

  if (isLoading) return <div className="p-4 text-center">{t('tables.loading')}</div>;
  if (error) return <div className="p-4 text-red-500 text-center">{t('tables.error')}</div>;

  const listings = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      {actionError && (
        <div className="bg-red-50 px-4 py-2 text-sm text-red-600">{actionError}</div>
      )}
      {!verified && companies.length > 0 && (
        <div className="bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Firma ešte nie je overená — publikovanie je zablokované, kým nebude status{' '}
          <strong>verified</strong>.
        </div>
      )}
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Názov</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Množstvo</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Jednotka</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Akcie</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {listings.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                {t('tables.empty')}
              </td>
            </tr>
          ) : (
            listings.map((listing: any) => {
              const st = companyStatusById[String(listing.companyId)] || '';
              const canPublish = st === 'verified' || (!st && verified);
              return (
                <tr
                  key={listing.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/dashboard/listings/${listing.id}`)}
                >
                  <td className="px-4 py-2 font-medium text-gray-900">{listing.title}</td>
                  <td className="px-4 py-2 text-gray-700">
                    {listing.quantity ?? listing.amount}
                  </td>
                  <td className="px-4 py-2 text-gray-700">{listing.unit}</td>
                  <td className="px-4 py-2">
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        listing.status === 'published' || listing.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      )}
                    >
                      {listing.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {listing.status === 'draft' && (
                      <button
                        type="button"
                        disabled={busyId === listing.id || !canPublish}
                        title={
                          !canPublish
                            ? t('tables.companyMustBeVerified')
                            : t('tables.publishToMarketplace')
                        }
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePublish(listing.id, listing.companyId);
                        }}
                        className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        {busyId === listing.id ? '...' : t('tables.publish')}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
