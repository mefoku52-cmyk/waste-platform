'use client';

import { useQuery } from '@tanstack/react-query';
import { config } from '../../../lib/config';

type CompanyRow = {
  id: string;
  legalName: string;
  city: string;
  countryCode?: string;
  logisticsCapability?: boolean;
  companyType?: string;
};

async function fetchCompanies(): Promise<CompanyRow[]> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(config.apiBaseUrl + '/companies', {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error('Companies request failed');
  const rows = (body.items || body.data || body) as CompanyRow[];
  return Array.isArray(rows) ? rows : [];
}

export function FreightPanel() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['freight-companies'],
    queryFn: fetchCompanies,
  });
  const carriers = (data || []).filter(
    (row) => row.logisticsCapability || row.companyType === 'logistics_partner',
  );

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">Spedicia</p>
      <h2 className="mt-1 font-serif text-2xl">Dopravcovia v platforme</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">Len firmy s logistikou. Ziadna objednavka.</p>
      {isLoading && <p className="mt-4 text-sm text-[#cbb98a]">Nacitavam…</p>}
      {error && <p className="mt-4 text-sm text-red-300">{(error as Error).message}</p>}
      {carriers.length === 0 && !isLoading && (
        <p className="mt-4 text-sm text-[#cbb98a]">Ziadny dopravca s logisticsCapability.</p>
      )}
      <ul className="mt-4 space-y-2">
        {carriers.map((row) => (
          <li key={row.id} className="rounded-xl border border-[#d4af37]/25 p-3">
            <p className="font-semibold">{row.legalName}</p>
            <p className="text-xs text-[#9a8b63]">{row.city} {row.countryCode || ''}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
