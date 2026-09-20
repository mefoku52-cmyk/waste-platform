'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

const PAGE_SIZE = 10;

type Company = {
  id: string;
  legalName?: string;
  city?: string;
  status?: string;
  acceptedMaterialTypes?: string | null;
};

function cleanFilter(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9áäčďéíľĺňóôŕšťúýžÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ,.\-\s]/g, '').slice(0, 64);
}

async function fetchCompanies(page: number): Promise<{ items: Company[]; total: number }> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(config.apiBaseUrl + '/companies?page=' + page + '&pageSize=' + PAGE_SIZE, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'HTTP ' + res.status);
  const items = (body.items || body.data || []) as Company[];
  const total = Number(body.meta?.total ?? body.total ?? items.length);
  return { items: Array.isArray(items) ? items : [], total };
}

export default function CompaniesPage() {
  const { t } = useT();
  const [page, setPage] = useState(1);
  const [material, setMaterial] = useState('');
  const { data, error, isLoading } = useQuery({
    queryKey: ['companies', page],
    queryFn: () => fetchCompanies(page),
  });
  const filter = cleanFilter(material).trim().toLowerCase();
  const items = (data?.items || []).filter((row) =>
    filter ? (row.acceptedMaterialTypes || '').toLowerCase().includes(filter) : true,
  );
  const total = data?.total || 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="min-h-screen bg-[#090807] text-[#f3ead8]">
      <DashboardHeader />
      <div className="mx-auto max-w-4xl p-6">
        <p className="text-[10px] uppercase tracking-[0.2em] text-[#c9a84c]">{t('companies.kicker')}</p>
        <h1 className="mt-1 font-serif text-3xl">{t('companies.title')}</h1>
        <Link href="/dashboard/companies/new" className="mt-3 inline-block text-sm text-[#c9a84c]">
          {t('companies.add')}
        </Link>
        <input
          value={material}
          onChange={(e) => setMaterial(cleanFilter(e.target.value))}
          placeholder={t('companies.filter')}
          maxLength={64}
          className="mt-4 w-full rounded-lg border border-[#c9a84c]/25 bg-black p-2 text-sm"
        />
        {isLoading && <p className="mt-4 text-sm text-[#9a8f7c]">{t('companies.loading')}</p>}
        {error && <p className="mt-4 text-sm text-red-300">{(error as Error).message}</p>}
        <ul className="mt-6 space-y-3">
          {items.map((row) => (
            <li key={row.id} className="rounded-2xl border border-[#c9a84c]/25 p-4">
              <p className="font-semibold">{row.legalName || row.id}</p>
              <p className="text-sm text-[#9a8f7c]">{row.city} · {row.status}</p>
              <p className="text-xs text-[#9a8f7c]">
                {t('companies.materials')}: {row.acceptedMaterialTypes || t('companies.empty')}
              </p>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex items-center gap-3 text-sm">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="text-[#c9a84c] disabled:text-[#6e6658]">
            {t('companies.prev')}
          </button>
          <span>{page} / {pages}</span>
          <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="text-[#c9a84c] disabled:text-[#6e6658]">
            {t('companies.next')}
          </button>
        </div>
      </div>
    </main>
  );
}
