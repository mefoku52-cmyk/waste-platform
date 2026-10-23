'use client';

import Link from 'next/link';
import { useState } from 'react';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { useAdminCompanies } from '@/features/admin';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

const PAGE_SIZE = 20;

export default function AdminCompaniesPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const { data, isLoading, error } = useAdminCompanies({
    page,
    pageSize: PAGE_SIZE,
    q: search || undefined,
    status: status || undefined,
  });

  const total = data?.meta.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <DashboardHeader />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p
              className="mb-2 text-[11px] uppercase tracking-[0.3em]"
              style={{ color: GOLD }}
            >
              Administrácia
            </p>
            <h1 className="text-3xl md:text-4xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
              Firmy
            </h1>
          </div>
          <Link
            href="/dashboard/admin"
            className="rounded-full border px-4 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD }}
          >
            Späť na admin
          </Link>
        </div>

        <form
          className="mb-5 flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setSearch(q.trim());
          }}
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Názov, IČO alebo e-mail"
            className="min-w-[220px] flex-1 rounded-xl border bg-transparent px-3 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.3)' }}
          />
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="rounded-xl border bg-[#12100c] px-3 py-2 text-sm"
            style={{ borderColor: 'rgba(201,168,76,0.3)' }}
          >
            <option value="">Všetky stavy</option>
            <option value="draft">Draft</option>
            <option value="verification_submitted">Čaká na overenie</option>
            <option value="verified">Overená</option>
            <option value="rejected">Zamietnutá</option>
            <option value="suspended">Pozastavená</option>
          </select>
          <button
            type="submit"
            className="rounded-full px-4 py-2 text-sm font-semibold"
            style={{ background: GOLD, color: '#090807' }}
          >
            Hľadať
          </button>
        </form>

        {isLoading ? (
          <p className="py-10 text-center text-sm" style={{ color: MUTED }}>
            Načítavam firmy…
          </p>
        ) : error ? (
          <p className="py-10 text-center text-sm" style={{ color: '#e8a598' }}>
            Firmy sa nepodarilo načítať.
          </p>
        ) : !data?.items.length ? (
          <p className="py-10 text-center text-sm" style={{ color: MUTED }}>
            Žiadne firmy.
          </p>
        ) : (
          <div
            className="overflow-x-auto rounded-2xl border"
            style={{ borderColor: 'rgba(201,168,76,0.25)' }}
          >
            <table className="min-w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(201,168,76,0.15)' }}>
                  {['Firma', 'IČO', 'Stav', 'Mesto', 'Fotky', ''].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.2em]"
                      style={{ color: GOLD }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr
                    key={c.id}
                    style={{ borderBottom: '1px solid rgba(201,168,76,0.08)' }}
                  >
                    <td className="px-4 py-3">
                      <p style={{ color: FG }}>{c.tradingName || c.legalName}</p>
                      <p className="text-xs" style={{ color: MUTED }}>
                        {c.email || '—'}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: MUTED }}>
                      {c.registrationNumber}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: MUTED }}>
                      {c.status}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: MUTED }}>
                      {c.city || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: MUTED }}>
                      {c.photoCount}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/dashboard/admin/companies/${c.id}`}
                        className="rounded-full border px-3 py-1 text-xs"
                        style={{ borderColor: 'rgba(201,168,76,0.4)', color: GOLD }}
                      >
                        Detail
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-5 flex items-center justify-between text-sm" style={{ color: MUTED }}>
          <span>
            {total} firiem · strana {page} / {pages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-full border px-3 py-1 disabled:opacity-40"
              style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD }}
            >
              Predchádzajúca
            </button>
            <button
              type="button"
              disabled={page >= pages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-full border px-3 py-1 disabled:opacity-40"
              style={{ borderColor: 'rgba(201,168,76,0.35)', color: GOLD }}
            >
              Ďalšia
            </button>
          </div>
        </div>
      </main>
      <DashboardFooter />
    </div>
  );
}
