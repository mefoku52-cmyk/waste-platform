'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';
import { http } from '@/lib/api/http';
import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';
import { redirect } from 'next/navigation';
import { useT } from '@/lib/i18n/context';

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

type PendingItem = {
  id: string;
  company_name: string;
  ico?: string | null;
  city?: string | null;
  industry?: string | null;
  email?: string | null;
  subject?: string | null;
  body?: string | null;
  status: string;
  created_at?: string | null;
};
type PendingResponse = { count: number; items: PendingItem[] };
type SendPendingResponse = { ok: boolean; message: string; status: string };

export default function LeadOutreachPage() {
  const { t } = useT();
  const { user, isLoading } = useAuthRequired();
  const isAdmin = useIsPlatformAdmin();

  const [companyName, setCompanyName] = useState('');
  const [city, setCity] = useState('');
  const [industry, setIndustry] = useState('');
  const [reason, setReason] = useState('');
  const [batchText, setBatchText] = useState('');
  const [email, setEmail] = useState('');

  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');

  const [busyDraft, setBusyDraft] = useState(false);
  const [busySend, setBusySend] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [busyDiscover, setBusyDiscover] = useState(false);
  const [busyBackfill, setBusyBackfill] = useState(false);
  const [found, setFound] = useState<DiscoverItem[]>([]);

  // Pending (pripravene na odoslanie z DB)
  const [pending, setPending] = useState<PendingItem[]>([]);
  const [busyPending, setBusyPending] = useState(false);
  const [busySendId, setBusySendId] = useState<string | null>(null);
  const [pendingEmail, setPendingEmail] = useState<Record<string, string>>({});
  const [pendingSubject, setPendingSubject] = useState<Record<string, string>>({});
  const [selectedPending, setSelectedPending] = useState<Record<string, boolean>>({});
  const [busySendAll, setBusySendAll] = useState(false);
  const [sendAllProgress, setSendAllProgress] = useState<{ current: number; total: number } | null>(null);

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


  async function loadPending() {
    setBusyPending(true);
    try {
      const res = await http.get<PendingResponse>('/admin/lead-outreach/pending?limit=50');
      setPending(res.items || []);
      const emails: Record<string, string> = {};
      const subjects: Record<string, string> = {};
      const selected: Record<string, boolean> = {};
      for (const it of res.items || []) {
        emails[it.id] = it.email || '';
        subjects[it.id] = it.subject || '';
        selected[it.id] = !!it.email;
      }
      setPendingEmail(emails);
      setPendingSubject(subjects);
      setSelectedPending(selected);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Pending zlyhal');
    } finally {
      setBusyPending(false);
    }
  }

  async function sendPending(item: PendingItem) {
    const to = (pendingEmail[item.id] || '').trim();
    const sub = (pendingSubject[item.id] || item.subject || '').trim();
    if (!to || !to.includes('@')) {
      setErr(`Doplň email pre ${item.company_name}`);
      return;
    }
    if (!sub) {
      setErr(`Chýba predmet pre ${item.company_name}`);
      return;
    }
    if (!item.body) {
      setErr(`Chýba telo emailu pre ${item.company_name}`);
      return;
    }
    setErr(null);
    setOkMsg(null);
    setBusySendId(item.id);
    try {
      const res = await http.post<SendPendingResponse>(
        `/admin/lead-outreach/candidates/${item.id}/send`,
        { to, subject: sub, body: item.body },
      );
      if (res.ok) {
        setOkMsg(`Odoslané: ${item.company_name} — ${res.message}`);
        setPending((prev) => prev.filter((x) => x.id !== item.id));
      } else {
        setErr(res.message || 'Odoslanie zlyhalo');
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Send zlyhal');
    } finally {
      setBusySendId(null);
    }
  }

  async function sendSelected() {
    const toSend = pending.filter(
      (item) => selectedPending[item.id] && (pendingEmail[item.id] || '').includes('@'),
    );
    if (toSend.length === 0) {
      setErr('Nie je vybraný žiadny kandidát s platným emailom.');
      return;
    }
    setErr(null);
    setOkMsg(null);
    setBusySendAll(true);
    let sent = 0;
    let failed = 0;
    for (let i = 0; i < toSend.length; i++) {
      const item = toSend[i];
      setSendAllProgress({ current: i + 1, total: toSend.length });
      const to = (pendingEmail[item.id] || '').trim();
      const sub = (pendingSubject[item.id] || item.subject || '').trim();
      try {
        const res = await http.post<SendPendingResponse>(
          `/admin/lead-outreach/candidates/${item.id}/send`,
          { to, subject: sub, body: item.body || '' },
        );
        if (res.ok) {
          sent += 1;
          setPending((prev) => prev.filter((x) => x.id !== item.id));
        } else {
          failed += 1;
        }
      } catch {
        failed += 1;
      }
    }
    setSendAllProgress(null);
    setBusySendAll(false);
    setOkMsg(
      failed === 0
        ? `Odoslaných ${sent} z ${toSend.length}.`
        : `Odoslaných ${sent} z ${toSend.length}. Zlyhalo: ${failed}.`,
    );
  }

  async function skipPending(item: PendingItem) {
    setErr(null);
    try {
      await http.post(`/admin/lead-outreach/candidates/${item.id}/skip`, {});
      setPending((prev) => prev.filter((x) => x.id !== item.id));
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Skip zlyhal');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void loadPending();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  async function draftFromCsv() {
    const rows = batchText
      .split(/\n/)
      .map((ln) => ln.trim())
      .filter((ln) => ln && !ln.toLowerCase().startsWith('nazov') && !ln.toLowerCase().startsWith('názov'));
    const companies = rows.slice(0, 30).map((ln) => {
      const parts = ln.split(',').map((x) => x.trim());
      return {
        company_name: parts[0] || '',
        city: parts[1] || '',
        industry: parts[2] || '',
        reason: parts[3] || 'Pozvánka na CMEP',
      };
    }).filter((c) => c.company_name);
    if (!companies.length) {
      setErr('CSV box je prázdny.');
      return;
    }
    setBusyDraft(true);
    setErr(null);
    setOkMsg(null);
    try {
      const res = await http.post<{ items?: { company_name: string; subject: string; body: string }[]; count?: number }>(
        '/admin/lead-outreach/draft-batch',
        { companies },
        { timeoutMs: 60000 },
      );
      const first = res.items?.[0];
      if (first) {
        setCompanyName(first.company_name || '');
        setSubject(first.subject || '');
        setBody(first.body || '');
      }
      setOkMsg('Draftov ' + String(res.count ?? res.items?.length ?? 0) + '. Skontroluj náhľad a pošli.');
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : typeof e === 'object' && e && 'message' in e
            ? String((e as { message: unknown }).message)
            : 'Draft z CSV zlyhal';
      setErr(msg);
    } finally {
      setBusyDraft(false);
    }
  }

  type BackfillResponse = {
    ok: boolean; processed: number; found: number;
    no_website: number; no_email_on_website: number; failed: number;
  };
  async function backfillEmails() {
    setErr(null); setOkMsg(null); setBusyBackfill(true);
    try {
      const res = await http.post<BackfillResponse>('/admin/lead-outreach/backfill-emails?limit=35', {}, { timeoutMs: 120000 });
      setOkMsg('Backfill: spracovane ' + String(res.processed) + ', najdene ' + String(res.found) + ', bez webu ' + String(res.no_website) + ', bez emailu na webe ' + String(res.no_email_on_website) + ', zlyhania ' + String(res.failed) + '.');
      await loadPending();
    } catch (e) { setErr(e instanceof Error ? e.message : 'Backfill zlyhal'); }
    finally { setBusyBackfill(false); }
  }
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
      const msg =
        e instanceof Error
          ? e.message
          : typeof e === 'object' && e && 'message' in e
            ? String((e as { message: unknown }).message)
            : 'Hľadanie firiem zlyhalo';
      setErr(msg);
    } finally {
      setBusyDiscover(false);
    }
  }

  async function draftFrom(input: {
    company_name: string;
    city?: string | null;
    industry?: string | null;
    reason?: string | null;
  }) {
    setErr(null);
    setOkMsg(null);
    if (!input.company_name.trim()) {
      setErr('Zadaj názov firmy.');
      return;
    }
    setBusyDraft(true);
    try {
      const res = await http.post<DraftResponse>('/admin/lead-outreach/draft', {
        company_name: input.company_name.trim(),
        city: input.city?.trim() || undefined,
        industry: input.industry?.trim() || undefined,
        reason: input.reason?.trim() || undefined,
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

          {/* ═══════════════════════════════════════════════════ */}
          {/* PENDING — pripravene na odoslanie                    */}
          {/* ═══════════════════════════════════════════════════ */}
          <section
            className="mb-8 rounded-2xl border p-5"
            style={{
              borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)',
              background: 'rgba(201,168,76,0.05)',
            }}
          >
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2
                  className="text-xl"
                  style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                >
                  Pripravené na odoslanie ({pending.length})
                </h2>
                <p className="mt-1 text-xs" style={{ color: MUTED }}>
                  Začiarkni kandidátov a klikni Poslať vybrané. Alebo uprav jednotlivé pole pred odoslaním.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void loadPending()}
                  disabled={busyPending || busySendAll}
                  className="rounded-full px-3 py-1 text-xs font-semibold disabled:opacity-40"
                  style={{ background: 'transparent', color: GOLD_BRIGHT, border: '1px solid ' + GOLD }}
                >
                  {busyPending ? 'Obnovujem…' : 'Obnoviť'}
                </button>
                <button
                  type="button"
                  onClick={() => void sendSelected()}
                  disabled={busySendAll || busyPending || pending.length === 0}
                  className="rounded-full px-4 py-1 text-xs font-semibold disabled:opacity-40"
                  style={{ background: GOLD, color: BG }}
                >
                  {busySendAll
                    ? `Posielam ${sendAllProgress?.current ?? 0}/${sendAllProgress?.total ?? 0}…`
                    : `Poslať vybrané (${pending.filter((i) => selectedPending[i.id] && (pendingEmail[i.id] || '').includes('@')).length})`}
                </button>
              </div>
            </div>

            {pending.length === 0 ? (
              <p className="text-sm" style={{ color: MUTED }}>
                Žiadne čakajúce drafty. Automaticky sa naplnia o 7:15 (alebo klikni „Nájsť 30 nových firiem“ nižšie).
              </p>
            ) : (
              <ul className="space-y-3">
                {pending.map((item) => (
                  <li
                    key={item.id}
                    className="rounded-xl border p-4"
                    style={{
                      borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
                      background: '#0b0b0b',
                    }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={!!selectedPending[item.id]}
                          onChange={(e) =>
                            setSelectedPending((prev) => ({ ...prev, [item.id]: e.target.checked }))
                          }
                          disabled={!(pendingEmail[item.id] || '').includes('@')}
                          className="mt-1 h-4 w-4 accent-[#c9a84c]"
                          title={
                            (pendingEmail[item.id] || '').includes('@')
                              ? 'Zaradiť do dávky'
                              : 'Chýba platný email'
                          }
                        />
                        <div>
                          <p style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>
                            {item.company_name}
                          </p>
                          <p className="text-xs" style={{ color: MUTED }}>
                            {[item.city, item.ico, item.industry].filter(Boolean).join(' · ')}
                          </p>
                          {!(pendingEmail[item.id] || '').includes('@') ? (
                            <p className="mt-1 text-xs" style={{ color: DANGER }}>
                              Chýba platný email — doplň ho nižšie.
                            </p>
                          ) : null}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void skipPending(item)}
                        className="text-xs underline"
                        style={{ color: MUTED }}
                      >
                        Preskočiť
                      </button>
                    </div>

                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      <input
                        type="email"
                        placeholder={t('admin.phEmail')}
                        value={pendingEmail[item.id] || ''}
                        onChange={(e) =>
                          setPendingEmail((p) => ({ ...p, [item.id]: e.target.value }))
                        }
                        className="h-10 rounded-lg border px-3 text-sm outline-none"
                        style={inputStyle}
                      />
                      <input
                        type="text"
                        placeholder={t('admin.phSubject')}
                        value={pendingSubject[item.id] || ''}
                        onChange={(e) =>
                          setPendingSubject((p) => ({ ...p, [item.id]: e.target.value }))
                        }
                        className="h-10 rounded-lg border px-3 text-sm outline-none"
                        style={inputStyle}
                      />
                    </div>

                    <details className="mt-3">
                      <summary
                        className="cursor-pointer text-xs"
                        style={{ color: GOLD_BRIGHT }}
                      >
                        Zobraziť telo emailu
                      </summary>
                      <pre
                        className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border p-3 text-xs"
                        style={{
                          borderColor: 'rgba(201,168,76,0.2)',
                          background: '#050505',
                          color: FG,
                        }}
                      >
                        {item.body || '(prázdne)'}
                      </pre>
                    </details>

                    <div className="mt-3 flex justify-end">
                      <button
                        type="button"
                        disabled={busySendId === item.id}
                        onClick={() => void sendPending(item)}
                        className="rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
                        style={{ background: GOLD, color: BG }}
                      >
                        {busySendId === item.id ? 'Posielam…' : 'Poslať email'}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

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
            <button
              type="button"
              onClick={() => void backfillEmails()}
              disabled={busyBackfill}
              className="inline-flex rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: 'transparent', color: GOLD_BRIGHT, border: '1px solid #c9a84c' }}
            >
              {busyBackfill ? 'Hľadám emaily…' : 'Nájsť emaily'}
            </button>
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
                      void draftFrom({
                        company_name: item.company_name || '',
                        city: item.city,
                        industry: item.industry,
                        reason: 'pozvanka na platformu CMEP',
                      });
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

          <details className="mb-6 rounded-2xl border p-5 md:p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
            <summary
              className="cursor-pointer text-sm font-semibold"
              style={{ color: GOLD_BRIGHT }}
            >
              + Pridať firmu manuálne (jednorazový draft)
            </summary>
            <div className="mt-4">
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  placeholder={t('admin.phCompanyName')}
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="h-12 rounded-lg border px-4 text-sm outline-none"
                  style={inputStyle}
                />
                <input
                  placeholder={t('admin.phCity')}
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="h-12 rounded-lg border px-4 text-sm outline-none"
                  style={inputStyle}
                />
                <input
                  placeholder={t('admin.phIndustry')}
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="h-12 rounded-lg border px-4 text-sm outline-none"
                  style={inputStyle}
                />
                <input
                  placeholder={t('admin.phEmail')}
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
                onClick={() => void draftFrom({ company_name: companyName, city, industry, reason })}
                disabled={busyDraft || !companyName.trim()}
                className="mt-4 rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
                style={{ background: GOLD, color: BG }}
              >
                {busyDraft ? 'Pripravujem…' : 'Vygenerovať návrh'}
              </button>
            </div>
          </details>

          <section
            className="mt-6 rounded-2xl border p-5 md:p-6"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
          >
            <h2 className="text-lg font-semibold" style={{ color: GOLD }}>
              Dávka z CSV
            </h2>
            <p className="mt-2 text-sm" style={{ color: MUTED }}>
              Pre hromadné oslovenie (max 30 firiem) použi samostatnú stránku.
            </p>
            <Link
              href="/dashboard/admin/lead-outreach/batch"
              className="mt-4 inline-block rounded-full px-5 py-2 text-sm font-semibold"
              style={{ background: GOLD, color: BG }}
            >
              Otvoriť dávkové oslovenie
            </Link>
          </section>

          <details className="mt-6 rounded-2xl border p-5 md:p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
            <summary
              className="cursor-pointer text-sm font-semibold"
              style={{ color: GOLD_BRIGHT }}
            >
              2. Manuálny náhľad a odoslanie (len pre jednu firmu)
            </summary>
            <div className="mt-4">
              <input
                placeholder={t('admin.phSubject')}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="h-12 w-full rounded-lg border px-4 text-sm outline-none"
                style={inputStyle}
              />
              <textarea
                placeholder={t('admin.phBody')}
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
                {busySend ? 'Odosielam…' : 'Poslať email'}
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
            </div>
          </details>
        </main>

        <DashboardFooter />
      </div>
    </>
  );
}
