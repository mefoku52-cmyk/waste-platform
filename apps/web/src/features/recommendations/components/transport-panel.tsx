'use client';

import { useMemo, useState } from 'react';

type Props = { origin?: string; destination?: string };

export function TransportPanel({ origin, destination }: Props) {
  const [dest, setDest] = useState(destination || '');
  const [km, setKm] = useState('80');
  const [rate, setRate] = useState('1.35');

  const result = useMemo(() => {
    const distance = Number(km);
    const perKm = Number(rate);
    if (!Number.isFinite(distance) || !Number.isFinite(perKm) || distance <= 0) return null;
    const freight = distance * perKm;
    const handling = 45;
    return { freight, handling, total: freight + handling };
  }, [km, rate]);

  const mapQ = encodeURIComponent((origin || 'Slovensko') + ' to ' + (dest || 'Slovensko'));
  const mapSrc = 'https://www.openstreetmap.org/search?query=' + encodeURIComponent(dest || origin || 'Slovensko');

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">Preprava</p>
      <h2 className="mt-1 font-serif text-2xl">Odhad trasy a ceny</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">Podklad. Objednavku prepravy system nevytvara.</p>
      <div className="mt-4 grid gap-3 text-sm">
        <label>Od<input value={origin || ''} readOnly className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2 text-[#cbb98a]" /></label>
        <label>Do<input value={dest} onChange={(e) => setDest(e.target.value)} placeholder="Mesto odberatela" className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2" /></label>
        <label>Km<input value={km} onChange={(e) => setKm(e.target.value)} className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2" /></label>
        <label>Eur / km<input value={rate} onChange={(e) => setRate(e.target.value)} className="mt-1 w-full rounded-lg border border-[#d4af37]/20 bg-[#0b0b0b] p-2" /></label>
      </div>
      {result && (
        <div className="mt-4 text-sm text-[#cbb98a]">
          <p>Preprava: {result.freight.toFixed(2)} EUR</p>
          <p>Nakladka: {result.handling.toFixed(2)} EUR</p>
          <p className="text-[#d4af37]">Odhad spolu: {result.total.toFixed(2)} EUR</p>
          <p className="mt-2">{(origin || '?') + ' → ' + (dest || '?')}</p>
        </div>
      )}
      <a href={'https://www.google.com/maps/dir/' + mapQ} target="_blank" rel="noreferrer" className="mt-4 inline-block rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]">
        Otvorit mapu trasy
      </a>
      <iframe title="mapa" className="mt-4 h-56 w-full rounded-xl border border-[#d4af37]/20" src={mapSrc} />
    </section>
  );
}
