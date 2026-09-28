'use client';

import { useState } from 'react';
import Link from 'next/link';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { http } from '@/lib/api/http';
import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';
import { redirect } from 'next/navigation';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';
const OK = '#6ee7a7';

type DraftResponse = { subject: string; body: string };
type SendResponse = { ok: boolean; message: string };
type DiscoverItem = {
  id: string;
  company_name: string;
  ico?: string | null;
  city?: string | null;
  industry?: string | null;
  subject?: string | null;
  body?: string | null;
};
type DiscoverResponse = {
  ok: boolean;
  picked: number;
  created: number;
  drafted: number;
  failed: number;
  items?: DiscoverItem[];
};

export default function LeadOutreachPage() {
  const { user, isLoading } = useAuthRequired();
  const isAdmin = useIsPlatformAdmin();

  const [companyName, setCompanyName] = useState('');
  const [city, setCity] = useState('');
  const [industry, setIndustry] = useState('');
  const [reason, setReason] = useState('');
  const [email, setEmail] = useState('');

  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');

  const [busyDraft, setBusyDraft] = useState(false);
  const [busySend, setBusySend] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [busyDiscover, setBusyDiscover] = useState(false);
  const [found, setFound] = useState<DiscoverItem[]>([]);

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

  async function discoverDaily() {
    setErr(null);
    setOkMsg(null);
    setBusyDiscover(true);
    try {
      const res = await http.post<DiscoverResponse>(
        '/admin/lead-outreach/discover-daily',
        {},
        { timeoutMs: 60000 },
      );
      const items = res.items || [];
      setFound(items);
      setOkMsg(
        `Nájdených ${res.created} firiem, draftov ${res.drafted}. Doplň email a pošli.`,
      );
      if (items[0]) {
        setCompanyName(items[0].company_name || '');
        setCity(items[0].city || '');
        setIndustry(items[0].industry || '');
        setSubject(items[0].subject || '');
        setBody(items[0].body || '');
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Hľadanie firiem zlyhalo');
    } finally {
      setBusyDiscover(false);
    }
  }

  async function draft() {
    setErr(null);
    setOkMsg(null);
    if (!companyName.trim()) {
      setErr('Zadaj názov firmy.');
      return;
    }
    setBusyDraft(true);
    try {
      const res = await http.post<DraftResponse>('/admin/lead-outreach/draft', {
        company_name: companyName.trim(),
        city: city.trim() || undefined,
        industry: industry.trim() || undefined,
        reason: reason.trim() || undefined,
      });
      setSubject(res.subject || '');
      setBody(res.body || '');
      setOkMsg('Návrh pripravený. Skontroluj a klikni Poslať.');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Draft zlyhal');
    } finally {
      setBusyDraft(false);
    }
  }

  async function send() {
    setErr(null);
    setOkMsg(null);
    if (!email.trim() || !email.includes('@')) {
      setErr('Zadaj platný email príjemcu.');
      return;
    }
    if (!subject.trim() || !body.trim()) {
      setErr('Chýba predmet alebo telo emailu.');
      return;
    }
    setBusySend(true);
    try {
      const res = await http.post<SendResponse>('/admin/lead-outreach/send', {
        to: email.trim(),
        subject: subject.trim(),
        body,
      });
      if (res.ok) {
        setOkMsg(res.message || 'Email odoslaný.');
      } else {
        setErr(res.message || 'Email sa nepodarilo odoslať.');
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Send zlyhal');
    } finally {
      setBusySend(false);
    }
  }

  const inputStyle = {
    borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
    background: '#0b0b0b',
    color: FG,
  };

  return (
    <>
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />

        <main className="mx-auto max-w-4xl px-4 py-10">
          <Link
            href="/dashboard/admin"
            className="mb-6 inline-block text-sm"
            style={{ color: GOLD_BRIGHT }}
          >
            ← Späť na admin
          </Link>

          <p
            className="mb-2 text-[11px] uppercase tracking-[0.3em]"
            style={{ color: GOLD }}
          >
            LEAD OUTREACH
          </p>
          <h1
            className="mb-4 text-3xl md:text-4xl"
            style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
          >
            Oslovenie firiem
          </h1>
          <p className="mb-8 text-sm" style={{ color: MUTED }}>
            AI pripraví personalizovaný email. Ty skontroluješ a pošleš.
            Jeden email = jedno kliknutie. Žiadny hromadný send.
          </p>

          <div className="mb-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void discoverDaily()}
              disabled={busyDiscover}
              className="inline-flex rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: GOLD, color: BG }}
            >
              {busyDiscover ? 'Hľadám…' : 'Nájsť 30 nových firiem'}
            </button>
            <Link
              href="/dashboard/admin/lead-outreach/batch"
              className="inline-flex rounded-full px-5 py-2 text-sm font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              📦 Dávkové oslovenie (max 30)
            </Link>
          </div>
          {found.length ? (
            <section
              className="mb-6 rounded-2xl border p-5"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
            >
              <h2
                className="mb-3 text-xl"
                style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
              >
                Dnešných {found.length} firiem
              </h2>
              <div className="grid gap-2">
                {found.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="rounded-lg border px-3 py-2 text-left text-sm"
                    style={inputStyle}
                    onClick={() => {
                      setCompanyName(item.company_name || '');
                      setCity(item.city || '');
                      setIndustry(item.industry || '');
                      setSubject(item.subject || '');
                      setBody(item.body || '');
                    }}
                  >
                    <span style={{ color: GOLD_BRIGHT }}>{item.company_name}</span>
                    <span style={{ color: MUTED }}>
                      {' '}
                      · {item.city || '—'} · {item.ico || 'bez IČO'}
                    </span>
                  </button>
                ))}
              </div>
            </section>
          ) : null}

          <section
            className="rounded-2xl border p-5 md:p-6"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
          >
            <h2
              className="mb-4 text-xl"
              style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
            >
              1. Firma
            </h2>

            <div className="grid gap-3 md:grid-cols-2">
              <input
                placeholder="Názov firmy *"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="h-12 rounded-lg border px-4 text-sm outline-none"
                style={inputStyle}
              />
              <input
                placeholder="Mesto"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="h-12 rounded-lg border px-4 text-sm outline-none"
                style={inputStyle}
              />
              <input
                placeholder="Odvetvie (napr. drevospracovanie)"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="h-12 rounded-lg border px-4 text-sm outline-none"
                style={inputStyle}
              />
              <input
                placeholder="Email príjemcu *"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-12 rounded-lg border px-4 text-sm outline-none"
                style={inputStyle}
              />
            </div>

            <textarea
              placeholder="Dôvod kontaktovania (napr. Firma spracúva drevo a mohla by mať záujem o predaj pilín.)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="mt-3 w-full resize-none rounded-lg border p-3 text-sm outline-none"
              style={inputStyle}
            />

            <button
              type="button"
              onClick={() => void draft()}
              disabled={busyDraft || !companyName.trim()}
              className="mt-4 rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: GOLD, color: BG }}
            >
              {busyDraft ? 'Pripravujem…' : '✨ Vygenerovať návrh'}
            </button>
          </section>

          <section
            className="mt-6 rounded-2xl border p-5 md:p-6"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
          >
            <h2
              className="mb-4 text-xl"
              style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
            >
              2. Náhľad a odoslanie
            </h2>

            <input
              placeholder="Predmet"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="h-12 w-full rounded-lg border px-4 text-sm outline-none"
              style={inputStyle}
            />
            <textarea
              placeholder="Telo emailu"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              className="mt-3 w-full resize-y rounded-lg border p-3 text-sm outline-none"
              style={inputStyle}
            />

            <button
              type="button"
              onClick={() => void send()}
              disabled={busySend || !subject.trim() || !body.trim() || !email.trim()}
              className="mt-4 rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: GOLD, color: BG }}
            >
              {busySend ? 'Odosielam…' : '📤 Poslať email'}
            </button>

            {err ? (
              <p className="mt-3 text-sm" style={{ color: DANGER }}>
                {err}
              </p>
            ) : null}
            {okMsg ? (
              <p className="mt-3 text-sm" style={{ color: OK }}>
                {okMsg}
              </p>
            ) : null}
          </section>
        </main>

        <DashboardFooter />
      </div>
    </>
  );
}
