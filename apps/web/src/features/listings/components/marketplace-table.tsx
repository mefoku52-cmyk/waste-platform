'use client';

import { useRouter } from 'next/navigation';
import { useMarketplace } from '../hooks/use-marketplace';
import { cn } from '../../../lib/utils/cn';
import { useT } from '@/lib/i18n/context';

export const MarketplaceTable = () => {
  const { t } = useT();
  const { data, isLoading, error } = useMarketplace();
  const router = useRouter();

  if (isLoading) return <div className="p-4 text-center">Načítavam trhovisko...</div>;
  if (error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní trhoviska.</div>;

  const listings = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.title')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.quantity')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.unit')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.location')}</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.status')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {listings.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                Žiadne cudzie publikované ponuky.
              </td>
            </tr>
          ) : (
            listings.map((listing: any) => (
              <tr
                key={listing.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => router.push(`/dashboard/listings/${listing.id}`)}
              >
                <td className="px-4 py-2 font-medium text-gray-900">{listing.title}</td>
                <td className="px-4 py-2 text-gray-700">{listing.quantity ?? listing.amount}</td>
                <td className="px-4 py-2 text-gray-700">{listing.unit}</td>
                <td className="px-4 py-2 text-gray-700">{listing.location || '—'}</td>
                <td className="px-4 py-2">
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      'bg-green-100 text-green-800'
                    )}
                  >
                    {listing.status}
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
