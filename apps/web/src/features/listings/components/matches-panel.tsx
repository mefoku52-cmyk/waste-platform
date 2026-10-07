'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMatches } from '../hooks/use-matches';
import { Input } from '../../../components/ui/input';
import { Button } from '../../../components/ui/button';
import { useT } from '@/lib/i18n/context';

export const MatchesPanel = () => {
  const { t } = useT();
  const [material, setMaterial] = useState('kov');
  const [query, setQuery] = useState('kov');
  const { data, isLoading, error, refetch } = useMatches(query);
  const router = useRouter();
  const items = (data as any)?.items ?? [];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-end">
        <div className="flex-1 min-w-[160px]">
          <label className="mb-1 block text-xs text-gray-500">{t('tables.materialType')}</label>
          <Input
            value={material}
            onChange={(e) => setMaterial(e.target.value)}
            placeholder={t('listings.form.materialPlaceholder')}
          />
        </div>
        <Button
          type="button"
          size="sm"
          onClick={() => {
            setQuery(material.trim());
            setTimeout(() => refetch(), 0);
          }}
        >
          {t('listings.matchesExtended.title')}
        </Button>
      </div>

      {isLoading && <div className="text-sm text-gray-500">{t('listings.matchesExtended.loading')}</div>}
      {error && <div className="text-sm text-red-600">{t('listings.matchesExtended.error')}</div>}

      {!isLoading && !error && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.title')}</th>
                <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.material')}</th>
                <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.location')}</th>
                <th className="px-4 py-2 text-left font-medium text-gray-900">{t('tables.quantity')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    {t('listings.empty')} „{query}“.
                  </td>
                </tr>
              ) : (
                items.map((listing: any) => (
                  <tr
                    key={listing.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => router.push(`/dashboard/listings/${listing.id}`)}
                  >
                    <td className="px-4 py-2 font-medium text-gray-900">{listing.title}</td>
                    <td className="px-4 py-2 text-gray-700">{listing.materialType}</td>
                    <td className="px-4 py-2 text-gray-700">{listing.location}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {listing.quantity} {listing.unit}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
