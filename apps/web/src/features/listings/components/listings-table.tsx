'use client';

import { useListings } from '../hooks/use-listings';
import { cn } from '../../../lib/utils/cn';

export const ListingsTable = () => {
  const { data, isLoading, error } = useListings();

  if (isLoading) return <div className="p-4 text-center">Načítavam ponuky...</div>;
  if (error) return <div className="p-4 text-red-500 text-center">Chyba pri načítaní dát.</div>;

  const listings = (data as any)?.items ?? [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Názov</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Množstvo</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Jednotka</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {listings.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                Žiadne ponuky neboli nájdené.
              </td>
            </tr>
          ) : (
            listings.map((listing: any) => (
              <tr key={listing.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">{listing.title}</td>
                <td className="px-4 py-2 text-gray-700">{listing.quantity ?? listing.amount}</td>
                <td className="px-4 py-2 text-gray-700">{listing.unit}</td>
                <td className="px-4 py-2">
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      listing.status === 'active' || listing.status === 'published'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
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
