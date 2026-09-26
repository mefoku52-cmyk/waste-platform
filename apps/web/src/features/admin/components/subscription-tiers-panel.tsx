'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { companiesApi } from '@/features/companies/api';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';
const OK = '#6ee7a7';

const TIERS = ['free', 'pro', 'ai'] as const;
type Tier = (typeof TIERS)[number];

const TIER_LABEL: Record<Tier, string> = {
  free: 'FREE',
  pro: 'PRO',
  ai: 'AI',
};

const TIER_COLOR: Record<Tier, string> = {
  free: MUTED,
  pro: GOLD_BRIGHT,
  ai: OK,
};

function normalizeTier(value: unknown): Tier {
  const v = String(value ?? 'free').toLowerCase().trim();
  return (TIERS as readonly string[]).includes(v) ? (v as Tier) : 'free';
}

export function SubscriptionTiersPanel() {
  const qc = useQueryClient();
  const [err, setErr] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ['admin-companies-for-tiers'],
    queryFn: () => companiesApi.getCompanies({ page: 1, pageSize: 100 }),
  });

  const mutation = useMutation({
    mutationFn: ({ id, tier }: { id: string; tier: Tier }) =>
      companiesApi.setSubscriptionTier(id, tier),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['admin-companies-for-tiers'] });
      await qc.invalidateQueries({ queryKey: ['companies'] });
      await qc.invalidateQueries({ queryKey: ['auth-user'] });
    },
    onError: (e) => {
      setErr(e instanceof Error ? e.message : 'Zmena tieru zlyhala');
    },
  });

  const items = (query.data as any)?.items ?? [];

  if (query.isLoading) {
    return (
      <p className="py-6 text-sm" style={{ color: MUTED }}>
        Načítavam firmy…
      </p>
    );
  }
  if (query.error) {
    return (
      <p className="py-6 text-sm" style={{ color: DANGER }}>
        Chyba: {(query.error as Error).message}
      </p>
    );
  }

  return (
    <div>
      {err ? (
        <p className="mb-3 text-sm" style={{ color: DANGER }}>
          {err}
        </p>
      ) : null}

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr
              style={{
                borderBottom: `1px solid color-mix(in srgb, #c9a84c 25%, transparent)`,
              }}
            >
              <th
                className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: GOLD }}
              >
                Firma
              </th>
              <th
                className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: GOLD }}
              >
                IČO
              </th>
              <th
                className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: GOLD }}
              >
                Status
              </th>
              <th
                className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: GOLD }}
              >
                Tier
              </th>
              <th
                className="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: GOLD }}
              >
                Zmena
              </th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center" style={{ color: MUTED }}>
                  Žiadne firmy.
                </td>
              </tr>
            ) : (
              items.map((c: any) => {
                const currentTier = normalizeTier(c.subscriptionTier);
                const isBusy =
                  mutation.isPending && mutation.variables?.id === String(c.id);

                return (
                  <tr
                    key={c.id}
                    style={{
                      borderBottom:
                        '1px solid color-mix(in srgb, #c9a84c 12%, transparent)',
                    }}
                  >
                    <td className="px-3 py-3 font-medium" style={{ color: FG }}>
                      {c.legalName || c.tradingName || '—'}
                    </td>
                    <td className="px-3 py-3" style={{ color: MUTED }}>
                      {c.registrationNumber || '—'}
                    </td>
                    <td className="px-3 py-3" style={{ color: MUTED }}>
                      {c.status || '—'}
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className="inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider"
                        style={{
                          background: 'color-mix(in srgb, #c9a84c 15%, transparent)',
                          color: TIER_COLOR[currentTier],
                        }}
                      >
                        {TIER_LABEL[currentTier]}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex gap-2">
                        {TIERS.map((t) => (
                          <button
                            key={t}
                            type="button"
                            disabled={isBusy || t === currentTier}
                            onClick={() =>
                              mutation.mutate({ id: String(c.id), tier: t })
                            }
                            className="rounded-full border px-3 py-1 text-xs font-semibold transition disabled:opacity-40"
                            style={{
                              borderColor:
                                t === currentTier
                                  ? GOLD
                                  : 'color-mix(in srgb, #c9a84c 30%, transparent)',
                              background:
                                t === currentTier
                                  ? 'color-mix(in srgb, #c9a84c 20%, transparent)'
                                  : 'transparent',
                              color: t === currentTier ? GOLD_BRIGHT : FG,
                            }}
                          >
                            {TIER_LABEL[t]}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
