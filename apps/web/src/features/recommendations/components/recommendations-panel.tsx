'use client';

import { useRecommendations } from '../hooks/use-recommendations';

const REASON_LABEL: Record<string, string> = {
  verified_buyer: 'overený odberateľ',
  city_in_listing_location: 'mesto je v lokalite ponuky',
  logistics_capability: 'má logistiku',
};

export function RecommendationsPanel({ listingId }: { listingId: string }) {
  const { data, isLoading, error } = useRecommendations(listingId);

  return (
    <section className="mt-6 rounded-2xl border border-slate-700/80 bg-slate-950/95 p-6">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-300">
        Odporúčania
      </p>
      <h2 className="mt-1 text-xl font-bold text-white">Možní odberatelia</h2>
      <p className="mt-1 text-sm text-slate-400">
        Overení odberatelia z existujúcich dát. Obchod sa neuzatvára.
      </p>

      {isLoading && <p className="mt-4 text-sm text-slate-300">Načítavam…</p>}

      {error && (
        <p className="mt-4 text-sm text-red-200">
          {(error as Error).message || 'Odporúčania sa nepodarilo načítať'}
        </p>
      )}

      {data && data.items.length === 0 && (
        <p className="mt-4 text-sm text-slate-300">Žiadni overení odberatelia.</p>
      )}

      {data && data.items.length > 0 && (
        <ul className="mt-4 space-y-3">
          {data.items.map((item) => (
            <li key={item.companyId} className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <div className="flex items-baseline justify-between gap-3">
                <p className="font-semibold text-white">{item.legalName}</p>
                <p className="text-sm text-emerald-300">skóre {item.score}</p>
              </div>
              <p className="mt-1 text-sm text-slate-400">
                {item.city}, {item.countryCode}
              </p>
              <p className="mt-2 text-xs text-slate-400">
                {item.reasons.map((reason) => REASON_LABEL[reason] || reason).join(' · ')}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
