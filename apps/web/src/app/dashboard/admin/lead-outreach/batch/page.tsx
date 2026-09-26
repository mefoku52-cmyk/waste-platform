'use client';

import { useState } from 'react';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { http } from '@/lib/api/http';
import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';
const OK = '#6ee7a7';

type BatchDraftItem = {
  company_name: string;
  city: string | null;
  industry: string | null;
  subject: string;
  body: string;
};

type BatchDraftResponse = {
  count: number;
  items: BatchDraftItem[];
};

type DraftWithMeta = BatchDraftItem & {
  email: string;
  selected: boolean;
  sent: boolean;
  err?: string;
};

export default function LeadOutreachBatchPage() {
  const { user, isLoading } = useAuthRequired();
  const isAdmin = useIsPlatformAdmin();

  const [raw, setRaw] = useState('');
  const [busy, setBusy] = useState(false);
  const [busySend, setBusySend] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<DraftWithMeta[]>([]);

  if (isLoading) {
    return (
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />
        <div className="mx-auto max-w-6xl px-4 py-16 text-center" style={{ color: MUTED }}>
          Načítavam…
        </div>
      </div>
    );
  }
  if (user && !isAdmin) redirect('/dashboard');

  function parseInput(): { company_name: string; city?: string; industry?: string; email: string }[] {
    return raw
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(',').map((p) => p.trim());
        return {
          company_name: parts[0] || '',
          city: parts[1] || undefined,
          industry: parts[2] || undefined,
          email: parts[3] || '',
        };
      })
      .filter((c) => c.company_name && c.email);
  }

  async function generateDrafts() {
    setErr(null);
    setOkMsg(null);
    setDrafts([]);
    const parsed = parseInput();
    if (parsed.length === 0) {
      setErr('Vlož aspoň jednu firmu v tvare: Názov, Mesto, Odvetvie, email@firma.sk');
      return;
    }
    if (parsed.length > 30) {
      setErr(`Max 30 firiem na batch. Máš ${parsed.length}.`);
      return;
    }
    setBusy(true);
    try {
      const res = await http.post<BatchDraftResponse>('/admin/lead-outreach/draft-batch', {
        companies: parsed.map((c) => ({
          company_name: c.company_name,
          city: c.city,
          industry: c.industry,
        })),
      });
      const withMeta: DraftWithMeta[] = (res.items || []).map((item, i) => ({
        ...item,
        email: parsed[i]?.email || '',
        selected: true,
        sent: false,
      }));
      setDrafts(withMeta);
      setOkMsg(`Pripravených ${withMeta.length} draftov. Skontroluj a klikni Poslať vybrané.`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Generovanie zlyhalo');
    } finally {
      setBusy(false);
    }
  }

  function updateDraft(i: number, patch: Partial<DraftWithMeta>) {
    setDrafts((prev) => prev.map((d, idx) => (idx === i ? { ...d, ...patch } : d)));
  }

  async function sendSelected() {
    setErr(null);
    setOkMsg(null);
    const toSend = drafts.filter((d) => d.selected && !d.sent && d.email);
    if (toSend.length === 0) {
      setErr('Nič nie je vybrané.');
      return;
    }
    setBusySend(true);
    let sent = 0;
    for (let i = 0; i < drafts.length; i++) {
      const d = drafts[i];
      if (!d.selected || d.sent || !d.email) continue;
      try {
        await http.post('/admin/lead-outreach/send', {
          to: d.email,
          subject: d.subject,
          body: d.body,
        });
        updateDraft(i, { sent: true, err: undefined });
        sent++;
      } catch (e) {
        updateDraft(i, { err: e instanceof Error ? e.message : 'Chyba' });
      }
    }
    setBusySend(false);
    setOkMsg(`Odoslaných ${sent} z ${toSend.length}.`);
  }

  const inputStyle = {
    borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
    background: '#0b0b0b',
    color: FG,
  };

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <DashboardHeader />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <Link
          href="/dashboard/admin/lead-outreach"
          className="mb-6 inline-block text-sm"
          style={{ color: GOLD_BRIGHT }}
        >
          ← Späť na lead outreach
        </Link>

        <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          BATCH OUTREACH
        </p>
        <h1
          className="mb-4 text-3xl md:text-4xl"
          style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
        >
          Dávkové oslovenie
        </h1>
        <p className="mb-8 text-sm" style={{ color: MUTED }}>
          Vlož zoznam firiem (max 30). Formát každého riadku:
          <br />
          <code style={{ color: GOLD_BRIGHT }}>Názov, Mesto, Odvetvie, email@firma.sk</code>
        </p>

        <section
          className="rounded-2xl border p-5 md:p-6"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
        >
          <textarea
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            rows={10}
            placeholder={`DrevoSK s.r.o., Ulic, Drevospracovanie, info@drevosk.sk
KovoSrot Snina s.r.o., Snina, Kovošrot, kontakt@kovosrot.sk
...`}
            className="w-full resize-y rounded-lg border p-3 text-sm outline-none"
            style={inputStyle}
          />

          <button
            type="button"
            onClick={() => void generateDrafts()}
            disabled={busy || !raw.trim()}
            className="mt-4 rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
            style={{ background: GOLD, color: BG }}
          >
            {busy ? 'Pripravujem…' : '✨ Vygenerovať drafty'}
          </button>

          {err ? <p className="mt-3 text-sm" style={{ color: DANGER }}>{err}</p> : null}
          {okMsg ? <p className="mt-3 text-sm" style={{ color: OK }}>{okMsg}</p> : null}
        </section>

        {drafts.length > 0 ? (
          <section className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2
                className="text-xl"
                style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
              >
                Drafty ({drafts.length})
              </h2>
              <button
                type="button"
                onClick={() => void sendSelected()}
                disabled={busySend}
                className="rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
                style={{ background: GOLD, color: BG }}
              >
                {busySend ? 'Posielam…' : '📤 Poslať vybrané'}
              </button>
            </div>

            {drafts.map((d, i) => (
              <div
                key={`${d.company_name}-${i}`}
                className="rounded-2xl border p-4"
                style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
              >
                <div className="mb-2 flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={d.selected}
                    disabled={d.sent}
                    onChange={(e) => updateDraft(i, { selected: e.target.checked })}
                  />
                  <p className="text-sm font-semibold" style={{ color: FG }}>
                    {d.company_name}
                  </p>
                  <p className="text-xs" style={{ color: MUTED }}>
                    {d.email}
                  </p>
                  {d.sent ? (
                    <span className="ml-auto text-xs" style={{ color: OK }}>✓ odoslané</span>
                  ) : null}
                </div>

                <input
                  value={d.subject}
                  onChange={(e) => updateDraft(i, { subject: e.target.value })}
                  className="h-10 w-full rounded-lg border px-3 text-sm outline-none"
                  style={inputStyle}
                />
                <textarea
                  value={d.body}
                  onChange={(e) => updateDraft(i, { body: e.target.value })}
                  rows={6}
                  className="mt-2 w-full resize-y rounded-lg border p-3 text-sm outline-none"
                  style={inputStyle}
                />
                {d.err ? <p className="mt-2 text-xs" style={{ color: DANGER }}>{d.err}</p> : null}
              </div>
            ))}
          </section>
        ) : null}
      </main>
      <DashboardFooter />
    </div>
  );
}
