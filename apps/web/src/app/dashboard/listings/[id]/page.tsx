'use client';

import { useParams } from 'next/navigation';
import { RecommendationsPanel } from '../../../../features/recommendations/components/recommendations-panel';

export default function ListingDetailPage() {
  const params = useParams<{ id: string }>();
  const listingId = params?.id;

  if (!listingId) {
    return <p className="p-6 text-slate-300">Chýba ID ponuky.</p>;
  }

  return (
    <main className="mx-auto w-full max-w-3xl p-6">
      <h1 className="text-2xl font-bold text-white">Ponuka</h1>
      <p className="mt-1 text-sm text-slate-400">{listingId}</p>
      <RecommendationsPanel listingId={listingId} />
    </main>
  );
}
