'use client';

import { useMemo, useState } from 'react';

type Props = { origin?: string };

export function TransportPanel({ origin }: Props) {
  const [destination, setDestination] = useState('');
  const [km, setKm] = useState('80');
  const [rate, setRate] = useState('1.35');

  const result = useMemo(() => {
    const distance = Number(km);
    const perKm = Number(rate);
    if (!Number.isFinite(distance) || !Number.isFinite(perKm) || distance <= 0) return null;
    const freight = distance * perKm;
    const handling = 45;
    const total = freight + handling;
    return { freight, handling, total };
  }, [km, rate]);

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">
        Preprava
      </p>
      <h2 className="mt-1 font-serif text-2xl">Odhad trasy a ceny</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">
        Iba podklad. Objednavku prepravy bot nevytvara.
      </p>
      <div className="mt-4 grid gap-3 text-sm">
        <label>
          Od
          <input
            value={origin || ''}
            readOnly
            className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2 text-[#cbb98a]"
          />
        </label>
        <label>
          Do
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Mesto odberatela / prekladisko"
            className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2"
          />
        </label>
        <label>
          Km (odhad)
          <input
            value={km}
            onChange={(e) => setKm(e.target.value)}
            className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2"
          />
        </label>
        <label>
          Eur / km
          <input
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2"
          />
        </label>
      </div>
      {result && (
        <div className="mt-4 text-sm text-[#cbb98a]">
          <p>Preprava: {result.freight.toFixed(2)} EUR</p>
          <p>Nakladka: {result.handling.toFixed(2)} EUR</p>
          <p className="text-[#d4af37]">Odhad spolu: {result.total.toFixed(2)} EUR</p>
          {destination ? <p className="mt-2">Trasa: {(origin || '?') + ' → ' + destination}</p> : null}
        </div>
      )}
    </section>
  );
}
