'use client';

import { tokenStore } from '@/lib/auth/token-store';

import Link from 'next/link';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { PremiumHero } from '@/components/layout/premium-hero';
import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

const PAGE_SIZE = 10;
const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type Company = {
  id: string;
  legalName?: string;
  tradingName?: string;
  city?: string;
  status?: string;
  acceptedMaterialTypes?: string | null;
};

function cleanFilter(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9áäčďéíľĺňóôŕšťúýžÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ,.\-\s]/g, '').slice(0, 64);
}

async function fetchCompanies(page: number): Promise<{ items: Company[]; total: number }> {
  const token = tokenStore.getToken();
  const res = await fetch(`${config.apiBaseUrl}/companies?page=${page}&pageSize=${PAGE_SIZE}&directory=true`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }

  const items = (body.items || body.data || []) as Company[];
  return {
    items: Array.isArray(items) ? items : [],
    total: Number(body.meta?.total ?? body.total ?? items.length),
  };
}

export default function CompaniesPage() {
  const { t } = useT();
  const [page, setPage] = useState(1);
  const [material, setMaterial] = useState('');

  const query = useQuery({
    queryKey: ['companies', page],
    queryFn: () => fetchCompanies(page),
  });

  const filter = cleanFilter(material).trim().toLowerCase();
  const items = (query.data?.items || []).filter((row) =>
    filter ? (row.acceptedMaterialTypes || '').toLowerCase().includes(filter) : true,
  );
  const total = query.data?.total || 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <AppShell>
      <PremiumHero
        kicker={t('companies.kicker')}
        title={t('companies.title')}
        subtitle={t('companies.heroSubtitle')}
        imageUrl="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
      />
      <div className="mx-auto w-full max-w-5xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="flex justify-end">
          <Link href="/dashboard/companies/new" className="rounded-full border px-4 py-2 text-sm" style={{ borderColor: 'rgba(201,168,76,0.48)', color: GOLD_BRIGHT }}>
            + {t('companies.add')}
          </Link>
        </div>

        <input
          value={material}
          onChange={(event) => setMaterial(cleanFilter(event.target.value))}
          placeholder={t('companies.filter')}
          maxLength={64}
          className="mt-6 w-full rounded-xl border border-[rgba(201,168,76,0.28)] bg-[#100f0c] px-4 py-3 text-sm text-[#f3ead8] outline-none"
        />

        {query.isLoading ? <p className="mt-5 text-sm" style={{ color: MUTED }}>{t('companies.loading')}</p> : null}
        {query.error ? <p className="mt-5 text-sm text-red-300">{query.error instanceof Error ? query.error.message : t('common.error')}</p> : null}

        <ul className="mt-6 space-y-3">
          {items.map((row) => (
            <li key={row.id}>
              <Link
                href={`/dashboard/companies/${row.id}`}
                className="cmep-card block rounded-2xl p-4 transition-colors hover:bg-[#14110a]"
                style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
              >
                <p className="font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                  {row.tradingName || row.legalName || row.id}
                </p>
                <p className="mt-1 text-sm" style={{ color: MUTED }}>
                  {[row.city, row.status].filter(Boolean).join(' · ') || '—'}
                </p>
                <p className="mt-3 text-xs" style={{ color: MUTED }}>
                  {t('companies.materials')}: {row.acceptedMaterialTypes || t('companies.empty')}
                </p>
              </Link>
            </li>
          ))}
        </ul>

        <div className="mt-6 flex items-center gap-3 text-sm">
          <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="rounded-full border px-3 py-1.5 disabled:opacity-40" style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}>
            {t('companies.prev')}
          </button>
          <span style={{ color: MUTED }}>{page} / {pages}</span>
          <button type="button" disabled={page >= pages} onClick={() => setPage((value) => value + 1)} className="rounded-full border px-3 py-1.5 disabled:opacity-40" style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD_BRIGHT }}>
            {t('companies.next')}
          </button>
        </div>
      </div>
    </AppShell>
  );
}
