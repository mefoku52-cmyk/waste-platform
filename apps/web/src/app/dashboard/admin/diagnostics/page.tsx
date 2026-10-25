'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';

type CheckResult = {
  http: number;
  data: Record<string, unknown>;
};

type Diagnostics = {
  health: CheckResult;
  readiness: CheckResult;
};

export default function DiagnosticsPage() {
  const [result, setResult] = useState<Diagnostics | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [updated, setUpdated] = useState('');
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timedOut = false;

    const timer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 25000);

    async function load() {
      setLoading(true);
      setError('');
      setResult(null);
      setStatus(null);
      setUpdated('');

      try {
        const token = tokenStore.getToken();
        if (!token) {
          throw new Error('Chyba prihlasenie. Prihlas sa znova.');
        }

        const base = config.apiBaseUrl.endsWith('/')
          ? config.apiBaseUrl.slice(0, -1)
          : config.apiBaseUrl;
        const response = await fetch(`${base}/ops/details`, {
          headers: {
            Accept: 'application/json',
            Authorization: `Bearer ${token}`,
          },
          cache: 'no-store',
          signal: controller.signal,
        });

        if (!active) return;
        setStatus(response.status);

        if (response.status === 401) {
          throw new Error('Prihlasenie nie je platne. Prihlas sa znova.');
        }
        if (response.status === 403) {
          throw new Error('Diagnostika je dostupna iba platformovemu administratorovi.');
        }
        if (response.status !== 200 && response.status !== 503) {
          throw new Error(`Diagnostika vratila HTTP ${response.status}.`);
        }

        const data: unknown = await response.json();

        if (
          !data ||
          typeof data !== 'object' ||
          !('health' in data) ||
          !('readiness' in data) ||
          !data.health ||
          typeof data.health !== 'object' ||
          !('http' in data.health) ||
          !('data' in data.health) ||
          !data.readiness ||
          typeof data.readiness !== 'object' ||
          !('http' in data.readiness) ||
          !('data' in data.readiness)
        ) {
          throw new Error('Server vratil necakany format diagnostiky.');
        }

        if (active) {
          setResult(data as Diagnostics);
          setUpdated(new Date().toLocaleString('sk-SK'));
        }
      } catch (caught) {
        if (!active) return;
        setError(
          timedOut
            ? 'Server neodpovedal do 25 sekund.'
            : caught instanceof Error
              ? caught.message
              : 'Diagnostiku sa nepodarilo nacitat.',
        );
      } finally {
        window.clearTimeout(timer);
        if (active) setLoading(false);
      }
    }

    void load();

    return () => {
      active = false;
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [refresh]);

  return (
    <main className="min-h-screen bg-[#090807] px-4 py-10 text-[#f3ead8]">
      <div className="mx-auto max-w-6xl space-y-6">
        <Link
          href="/dashboard/admin"
          className="text-sm text-[#e8d48b] underline"
        >
          Spat do administracie
        </Link>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold">Diagnostika platformy</h1>
          <button
            type="button"
            disabled={loading}
            onClick={() => setRefresh((value) => value + 1)}
            className="rounded-xl border border-[#c9a84c]/40 px-4 py-2 disabled:opacity-50"
          >
            {loading ? 'Nacitavam...' : 'Obnovit'}
          </button>
        </div>

        <p className="text-sm text-[#9a8f7c]">
          Chranena diagnostika. Interne podrobnosti nezdielaj verejne.
        </p>

        <div aria-live="polite" role="status">
          {loading && <p>Nacitavam aktualny stav...</p>}
          {error && <p className="text-red-300">{error}</p>}
          {!loading && result && (
            <p className={status === 200 ? 'text-green-300' : 'text-amber-300'}>
              {status === 200
                ? 'Kontroly presli.'
                : 'Niektora kontrola nepresla. Podrobnosti su nizsie.'}
              {' '}Aktualizovane: {updated}
            </p>
          )}
        </div>

        {result && (
          <div className="grid gap-5 lg:grid-cols-2">
            {([
              ['Zdravie sluzby', result.health],
              ['Pripravenost a zavislosti', result.readiness],
            ] as const).map(([label, check]) => (
              <section
                key={label}
                className="min-w-0 rounded-2xl border border-[#c9a84c]/25 p-5"
              >
                <h2 className="mb-3 text-lg font-semibold">
                  {label} · HTTP {check.http}
                </h2>
                <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-words text-xs text-[#e8d48b]">
                  {JSON.stringify(check.data, null, 2)}
                </pre>
              </section>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
