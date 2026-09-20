'use client';

import { useEffect, useState } from 'react';
import { config } from '../../../lib/config';

type Props = { origin?: string; destination?: string };
type Option = {
  kind: string;
  label: string;
  distanceKm: number;
  durationMin: number;
  extraEur: number;
  totalEur: number;
  fuel: { fuelLiters: number; fuelEur: number; chargeableKm: number };
};
type RouteResult = {
  bestKind: string;
  mapUrl: string;
  origin: { label: string };
  destination: { label: string };
  options: Option[];
};

export function TransportPanel({ origin, destination }: Props) {
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!origin || !destination) return;
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError('');
      try {
        const token = localStorage.getItem('accessToken');
        const q =
          'origin=' + encodeURIComponent(origin) +
          '&destination=' + encodeURIComponent(destination) +
          '&consumption=28&fuel_price=1.49&roundtrip=true';
        const res = await fetch(config.apiBaseUrl + '/recommendations/route?' + q, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: 'Bearer ' + token } : {}),
          },
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(typeof body.detail === 'string' ? body.detail : 'HTTP ' + res.status);
        }
        if (!cancelled) setRoute(body as RouteResult);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Vypocet zlyhal');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [origin, destination]);

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">Preprava</p>
      <h2 className="mt-1 font-serif text-2xl">Auto trasa</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">
        {origin || '?'} → {destination || 'caka na odberatela'}
      </p>
      {loading && <p className="mt-3 text-sm text-[#cbb98a]">Pocitam OSRM…</p>}
      {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      {route && (
        <div className="mt-4 space-y-3 text-sm">
          {route.options.map((opt) => (
            <div key={opt.kind} className="rounded-xl border border-[#d4af37]/25 p-3">
              <p className="text-[#d4af37]">{opt.label}{opt.kind === route.bestKind ? ' · odporucane' : ''}</p>
              <p>{opt.distanceKm} km · {opt.durationMin} min</p>
              <p>Nafta {opt.fuel.fuelLiters} l / {opt.fuel.fuelEur} EUR</p>
              {opt.extraEur ? <p>Znamka {opt.extraEur} EUR</p> : null}
              <p>Spolu {opt.totalEur} EUR</p>
            </div>
          ))}
          <a href={route.mapUrl} target="_blank" rel="noreferrer" className="inline-block rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]">
            Navigacia
          </a>
        </div>
      )}
    </section>
  );
}
