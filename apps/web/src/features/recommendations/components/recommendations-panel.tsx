'use client';

import { useState } from 'react';
import { useRecommendations } from '../hooks/use-recommendations';

const REASON_LABEL: Record<string, string> = {
  verified_buyer: 'overeny odberatel',
  city_in_listing_location: 'mesto je v lokalite ponuky',
  logistics_capability: 'ma logistiku',
  material_accepted: 'prijima material',
  distance_le_50km: 'do 50 km',
  distance_le_150km: 'do 150 km',
};

type Props = {
  listingId: string;
  listingTitle?: string;
  listingLocation?: string;
  materialType?: string;
};

export function RecommendationsPanel({
  listingId,
  listingTitle,
  listingLocation,
  materialType,
}: Props) {
  const { data, isLoading, error } = useRecommendations(listingId);
  const [draft, setDraft] = useState('');

  function makeDraft(name: string) {
    const text =
      'Dobry den, ' +
      name +
      '. Mam zaujem overit odber ponuky "' +
      (listingTitle || listingId) +
      '" (' +
      (materialType || 'material') +
      ', ' +
      (listingLocation || 'lokalita neuvedena') +
      '). Ide o dopyt, nie o uzavrety obchod. Prosim o kratke potvrdenie zaujmu.';
    setDraft(text);
  }

  async function copyDraft() {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
  }

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">
        Odporucania
      </p>
      <h2 className="mt-1 font-serif text-2xl text-[#f3e6c4]">Mozni odberatelia</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">
        Overeni odberatelia z existujucich dat. Obchod sa neuzatvara.
      </p>

      {isLoading && <p className="mt-4 text-sm text-[#cbb98a]">Nacitavam…</p>}
      {error && (
        <p className="mt-4 text-sm text-red-300">
          {(error as Error).message || 'Odporucania sa nepodarilo nacitat'}
        </p>
      )}
      {data && data.items.length === 0 && (
        <p className="mt-4 text-sm text-[#cbb98a]">Ziadni overeni odberatelia.</p>
      )}

      {data && data.items.length > 0 && (
        <ul className="mt-4 space-y-3">
          {data.items.map((item) => (
            <li key={item.companyId} className="rounded-xl border border-[#d4af37]/25 bg-[#0b0b0b] p-4">
              <div className="flex items-baseline justify-between gap-3">
                <p className="font-semibold text-[#f3e6c4]">{item.legalName}</p>
                <p className="text-sm text-[#d4af37]">skore {item.score}</p>
              </div>
              <p className="mt-1 text-sm text-[#9a8b63]">
                {item.city}, {item.countryCode}
              </p>
              <p className="mt-2 text-xs text-[#9a8b63]">
                {item.reasons.map((reason) => REASON_LABEL[reason] || reason).join(' · ')}
              </p>
              <button
                type="button"
                onClick={() => makeDraft(item.legalName)}
                className="mt-3 rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]"
              >
                Navrhnut spravu
              </button>
            </li>
          ))}
        </ul>
      )}

      {draft && (
        <div className="mt-4 rounded-xl border border-[#d4af37]/25 p-4">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37]">Navrh spravy do chatu</p>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="mt-2 h-28 w-full rounded-lg border border-[#d4af37]/20 bg-black p-3 text-sm text-[#f3e6c4]"
          />
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={copyDraft}
              className="rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]"
            >
              Kopirovat
            </button>
            <a
              href="/dashboard/chat"
              className="rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]"
            >
              Otvorit chat
            </a>
          </div>
        </div>
      )}
    </section>
  );
}
