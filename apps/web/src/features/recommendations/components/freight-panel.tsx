'use client';

import { tokenStore } from '@/lib/auth/token-store';

import { useQuery } from '@tanstack/react-query';
import { config } from '../../../lib/config';
import { useT } from '@/lib/i18n/context';

type Carrier = {
  name: string;
  lat: number;
  lon: number;
  source: string;
};

async function fetchCarriers(near: string): Promise<Carrier[]> {
  const token = tokenStore.getToken();
  const res = await fetch(
    config.apiBaseUrl + '/recommendations/carriers?near=' + encodeURIComponent(near),
    {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
    },
  );
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : 'HTTP ' + res.status);
  }
  return (body.items || []) as Carrier[];
}

export function FreightPanel({ near }: { near?: string }) {
  const { t } = useT();
  const enabled = !!near;
  const { data, isLoading, error } = useQuery({
    queryKey: ['company-carriers', near],
    queryFn: () => fetchCarriers(near as string),
    enabled,
  });

  return (
    <section className="mt-6 rounded-2xl border border-[#d4af37]/35 bg-black p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">{t('freight.kicker')}</p>
      <h2 className="mt-1 font-serif text-2xl">{t('freight.title')}</h2>
      <p className="mt-1 text-sm text-[#cbb98a]">
        {t('freight.firmsWithLogistics')} {near || t('freight.destination')}. {t('freight.notOrder')}
      </p>
      {!near && <p className="mt-4 text-sm text-[#cbb98a]">{t('freight.pendingCity')}</p>}
      {isLoading && <p className="mt-4 text-sm text-[#cbb98a]">{t('freight.loading')}</p>}
      {error && <p className="mt-4 text-sm text-red-300">{(error as Error).message}</p>}
      {data && data.length === 0 && <p className="mt-4 text-sm text-[#cbb98a]">{t('freight.empty')}</p>}
      <ul className="mt-4 space-y-2">
        {(data || []).map((row) => (
          <li key={row.name + row.lat} className="rounded-xl border border-[#d4af37]/25 p-3">
            <p className="font-semibold">{row.name}</p>
            <p className="text-xs text-[#9a8b63]">{row.lat.toFixed(4)}, {row.lon.toFixed(4)} · {row.source}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
