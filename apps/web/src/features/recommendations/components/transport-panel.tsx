'use client';

import { tokenStore } from '@/lib/auth/token-store';

import { useEffect, useMemo, useState } from 'react';
import { config } from '../../../lib/config';
import { useT } from '@/lib/i18n/context';

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

const VEHICLES = [
  { id: 'van', label: 'Dodávka', consumption: 10 },
  { id: 'rigid', label: 'Nákladné do 12 t', consumption: 20 },
  { id: 'truck', label: 'Kamión', consumption: 28 },
  { id: 'private', label: 'Súkromný / dodávateľ', consumption: 8 },
] as const;

export function TransportPanel({ origin, destination }: Props) {
  const { t } = useT();
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [kind, setKind] = useState<string>('truck');
  const vehicle = useMemo(
    () => VEHICLES.find((v) => v.id === kind) ?? VEHICLES[2],
    [kind],
  );

  useEffect(() => {
    if (!origin || !destination) return;
    const from = origin;
    const to = destination;
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError('');
      try {
        const token = tokenStore.getToken();
        const q =
          'origin=' +
          encodeURIComponent(from) +
          '&destination=' +
          encodeURIComponent(to) +
          '&consumption=' +
          String(vehicle.consumption) +
          '&fuel_price=1.49&roundtrip=true&kind=' +
          encodeURIComponent(vehicle.id);
        const res = await fetch(config.apiBaseUrl + '/recommendations/route?' + q, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: 'Bearer ' + token } : {}),
          },
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(
            typeof body.detail === 'string' ? body.detail : 'HTTP ' + res.status,
          );
        }
        if (!cancelled) setRoute(body as RouteResult);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Výpočet zlyhal');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [origin, destination, vehicle.consumption, vehicle.id]);

  if (!origin || !destination) {
    return (
      <section className="mt-6 rounded-2xl border p-4 text-sm" style={{ borderColor: 'rgba(201,168,76,0.25)', color: '#9a8f7c' }}>
        {t('transport.missingStops')}
      </section>
    );
  }

  return (
    <section className="mt-6 rounded-2xl border p-5" style={{ borderColor: 'rgba(201,168,76,0.25)' }}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: '#c9a84c' }}>
        {t('transport.title')}
      </p>
      <h2 className="mt-1 font-serif text-xl" style={{ color: '#e8d48b' }}>
        {origin} → {destination}
      </h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {VEHICLES.map((v) => (
          <button
            key={v.id}
            type="button"
            onClick={() => setKind(v.id)}
            className="rounded-full border px-3 py-1 text-xs"
            style={{
              borderColor: kind === v.id ? 'rgba(201,168,76,0.9)' : 'rgba(201,168,76,0.3)',
              color: kind === v.id ? '#090807' : '#e8d48b',
              background: kind === v.id ? '#c9a84c' : 'transparent',
            }}
          >
            {v.label}
          </button>
        ))}
      </div>
      {loading ? (
        <p className="mt-3 text-sm" style={{ color: '#9a8f7c' }}>{t('transport.loading')}</p>
      ) : null}
      {error ? (
        <p className="mt-3 text-sm" style={{ color: '#f0bbb0' }}>{error}</p>
      ) : null}
      {route ? (
        <div className="mt-4 space-y-2">
          {(route.options || []).map((opt) => (
            <div
              key={opt.kind + String(opt.distanceKm)}
              className="rounded-xl border p-3 text-sm"
              style={{ borderColor: 'rgba(201,168,76,0.2)', color: '#f3e6c4' }}
            >
              <p className="font-semibold">{opt.label || opt.kind}</p>
              <p>
                {Math.round(opt.distanceKm)} km · {Math.round(opt.durationMin)} min ·{' '}
                {Math.round(opt.totalEur)} €
              </p>
              <p className="text-xs" style={{ color: '#9a8f7c' }}>
                {t('transport.fuel')} {Math.round(opt.fuel?.fuelLiters || 0)} L / {Math.round(opt.fuel?.fuelEur || 0)} €
              </p>
            </div>
          ))}
          {route.mapUrl ? (
            <a className="text-xs underline" href={route.mapUrl} target="_blank" rel="noreferrer">
              {t('transport.map')}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
