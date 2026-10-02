"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { DashboardFooter } from "@/components/layout/dashboard-footer";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { http } from "@/lib/api/http";
import { useAuthRequired, useIsPlatformAdmin } from "@/features/auth";
import { redirect } from "next/navigation";
import { useT } from "@/lib/i18n/context";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const BG = "#090807";
const FG = "#f3ead8";
const MUTED = "#9a8f7c";
const DANGER = "#f0bbb0";
const OK = "#6ee7a7";

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

  const [companyName, setCompanyName] = useState("");
  const [city, setCity] = useState("");
  const [industry, setIndustry] = useState("");
  const [reason, setReason] = useState("");
  const [batchText, setBatchText] = useState("");
  const [email, setEmail] = useState("");

  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

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
  const [pendingSubject, setPendingSubject] = useState<Record<string, string>>(
    {},
  );
  const [selectedPending, setSelectedPending] = useState<
    Record<string, boolean>
  >({});
  const [busySendAll, setBusySendAll] = useState(false);
  const [sendAllProgress, setSendAllProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);

  if (user && !isAdmin) redirect("/dashboard");

  async function loadPending() {
    setBusyPending(true);
    try {
      const res = await http.get<PendingResponse>(
        "/admin/lead-outreach/pending?limit=50",
      );
      setPending(res.items || []);
      const emails: Record<string, string> = {};
      const subjects: Record<string, string> = {};
      const selected: Record<string, boolean> = {};
      for (const it of res.items || []) {
        emails[it.id] = it.email || "";
        subjects[it.id] = it.subject || "";
        selected[it.id] = !!it.email;
      }
      setPendingEmail(emails);
      setPendingSubject(subjects);
      setSelectedPending(selected);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Pending zlyhal");
    } finally {
      setBusyPending(false);
    }
  }

  async function sendPending(item: PendingItem) {
    const to = (pendingEmail[item.id] || "").trim();
    const sub = (pendingSubject[item.id] || item.subject || "").trim();
    const body = (item.body || "").trim();

    if (!to || !to.includes("@")) {
      setErr(`Doplň email pre ${item.company_name}`);
      return;
    }

    if (!sub) {
      setErr(`Chýba predmet pre ${item.company_name}`);
      return;
    }

    if (!body) {
      setErr(`Chýba telo emailu pre ${item.company_name}`);
      return;
    }

    setErr(null);
    setOkMsg(null);
    setBusySendId(item.id);

    try {
      // Vždy najprv ulozime aktualne skontrolovane hodnoty
      // a nastavime kandidatovi APPROVED.
      const approved = await http.post<{
        ok: boolean;
        message: string;
        status: string;
      }>(`/admin/lead-outreach/candidates/${item.id}/approve`, {
        email: to,
        subject: sub,
        body,
      });

      if (!approved.ok) {
        throw new Error(approved.message || "Schválenie kandidáta zlyhalo.");
      }

      // SEND uz nema vlastny recipient/subject/body.
      // Backend pouzije iba schvalene hodnoty z DB.
      const res = await http.post<SendPendingResponse>(
        `/admin/lead-outreach/candidates/${item.id}/send`,
        {},
      );

      if (res.ok) {
        setOkMsg(`Odoslané: ${item.company_name} — ${res.message}`);

        setPending((prev) => prev.filter((x) => x.id !== item.id));
      } else {
        setErr(res.message || "Odoslanie zlyhalo");

        // Ak approve presiel, kandidat ostava APPROVED
        // a zostane v zozname na retry.
        await loadPending();
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Odoslanie zlyhalo");

      // Ak schvalenie preslo a samotne odoslanie zlyhalo,
      // backend ma kandidata v APPROVED.
      try {
        await loadPending();
      } catch {
        // Pôvodnú chybu nechávame používateľovi.
      }
    } finally {
      setBusySendId(null);
    }
  }

  async function sendSelected() {
    const toSend = pending.filter(
      (item) =>
        selectedPending[item.id] &&
        (pendingEmail[item.id] || "").trim().includes("@"),
    );

    if (toSend.length === 0) {
      setErr("Nie je vybraný žiadny kandidát s platným emailom.");
      return;
    }

    setErr(null);
    setOkMsg(null);
    setBusySendAll(true);

    let sent = 0;
    let failed = 0;

    for (let i = 0; i < toSend.length; i++) {
      const item = toSend[i];

      setSendAllProgress({
        current: i + 1,
        total: toSend.length,
      });

      const to = (pendingEmail[item.id] || "").trim();
      const sub = (pendingSubject[item.id] || item.subject || "").trim();
      const body = (item.body || "").trim();

      try {
        if (!to || !to.includes("@")) {
          failed += 1;
          continue;
        }

        if (!sub || !body) {
          failed += 1;
          continue;
        }

        // Najprv ulozit presne skontrolovane udaje
        // a previest kandidata do APPROVED.
        const approved = await http.post<{
          ok: boolean;
          message: string;
          status: string;
        }>(`/admin/lead-outreach/candidates/${item.id}/approve`, {
          email: to,
          subject: sub,
          body,
        });

        if (!approved.ok) {
          failed += 1;
          continue;
        }

        // Send uz pouziva iba data z DB.
        const res = await http.post<SendPendingResponse>(
          `/admin/lead-outreach/candidates/${item.id}/send`,
          {},
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

    // Refresh je dolezity hlavne pri chybe odoslania:
    // APPROVED kandidati zostanu viditelni na retry.
    try {
      await loadPending();
    } catch {
      // Vysledok odoslania uz mame, refresh nie je kriticky.
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
      setErr(e instanceof Error ? e.message : "Skip zlyhal");
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
      .filter(
        (ln) =>
          ln &&
          !ln.toLowerCase().startsWith("nazov") &&
          !ln.toLowerCase().startsWith("názov"),
      );
    const companies = rows
      .slice(0, 30)
      .map((ln) => {
        const parts = ln.split(",").map((x) => x.trim());
        return {
          company_name: parts[0] || "",
          city: parts[1] || "",
          industry: parts[2] || "",
          reason: parts[3] || "Pozvánka na CMEP",
        };
      })
      .filter((c) => c.company_name);
    if (!companies.length) {
      setErr("CSV box je prázdny.");
      return;
    }
    setBusyDraft(true);
    setErr(null);
    setOkMsg(null);
    try {
      const res = await http.post<{
        items?: { company_name: string; subject: string; body: string }[];
        count?: number;
      }>(
        "/admin/lead-outreach/draft-batch",
        { companies },
        { timeoutMs: 60000 },
      );
      const first = res.items?.[0];
      if (first) {
        setCompanyName(first.company_name || "");
        setSubject(first.subject || "");
        setBody(first.body || "");
      }
      setOkMsg(
        "Draftov " +
          String(res.count ?? res.items?.length ?? 0) +
          ". Skontroluj náhľad a pošli.",
      );
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : typeof e === "object" && e && "message" in e
            ? String((e as { message: unknown }).message)
            : "Draft z CSV zlyhal";
      setErr(msg);
    } finally {
      setBusyDraft(false);
    }
  }

  type BackfillResponse = {
    ok: boolean;
    processed: number;
    found: number;
    no_website: number;
    no_email_on_website: number;
    failed: number;
  };
  async function backfillEmails() {
    setErr(null);
    setOkMsg(null);
    setBusyBackfill(true);
    try {
      const res = await http.post<BackfillResponse>(
        "/admin/lead-outreach/backfill-emails?limit=35",
        {},
        { timeoutMs: 120000 },
      );
      setOkMsg(
        "Backfill: spracovane " +
          String(res.processed) +
          ", najdene " +
          String(res.found) +
          ", bez webu " +
          String(res.no_website) +
          ", bez emailu na webe " +
          String(res.no_email_on_website) +
          ", zlyhania " +
          String(res.failed) +
          ".",
      );
      await loadPending();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Backfill zlyhal");
    } finally {
      setBusyBackfill(false);
    }
  }
  async function discoverDaily() {
    setErr(null);
    setOkMsg(null);
    setBusyDiscover(true);
    try {
      const res = await http.post<DiscoverResponse>(
        "/admin/lead-outreach/discover-daily",
        {},
        { timeoutMs: 60000 },
      );
      const items = res.items || [];
      setFound(items);
      setOkMsg(
        `Nájdených ${res.created} firiem, draftov ${res.drafted}. Doplň email a pošli.`,
      );
      if (items[0]) {
        setCompanyName(items[0].company_name || "");
        setCity(items[0].city || "");
        setIndustry(items[0].industry || "");
        setSubject(items[0].subject || "");
        setBody(items[0].body || "");

        await loadPending();
      }
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : typeof e === "object" && e && "message" in e
            ? String((e as { message: unknown }).message)
            : "Hľadanie firiem zlyhalo";
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
      setErr("Zadaj názov firmy.");
      return;
    }
    setBusyDraft(true);
    try {
      const res = await http.post<DraftResponse>("/admin/lead-outreach/draft", {
        company_name: input.company_name.trim(),
        city: input.city?.trim() || undefined,
        industry: input.industry?.trim() || undefined,
        reason: input.reason?.trim() || undefined,
      });
      setSubject(res.subject || "");
      setBody(res.body || "");
      setOkMsg("Návrh pripravený. Skontroluj a klikni Poslať.");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Draft zlyhal");
    } finally {
      setBusyDraft(false);
    }
  }

  async function send() {
    setErr(null);
    setOkMsg(null);
    if (!email.trim() || !email.includes("@")) {
      setErr("Zadaj platný email príjemcu.");
      return;
    }
    if (!subject.trim() || !body.trim()) {
      setErr("Chýba predmet alebo telo emailu.");
      return;
    }
    setBusySend(true);
    try {
      const res = await http.post<SendResponse>("/admin/lead-outreach/send", {
        to: email.trim(),
        subject: subject.trim(),
        body,
      });
      if (res.ok) {
        setOkMsg(res.message || "Email odoslaný.");
      } else {
        setErr(res.message || "Email sa nepodarilo odoslať.");
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Send zlyhal");
    } finally {
      setBusySend(false);
    }
  }

  const inputStyle = {
    borderColor: "color-mix(in srgb, #c9a84c 25%, transparent)",
    background: "#0b0b0b",
    color: FG,
  };

  if (isLoading) {
    return (
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />
        <div
          className="mx-auto max-w-6xl px-4 py-16 text-center"
          style={{ color: MUTED }}
        >
          Načítavam…
        </div>
      </div>
    );
  }
  return (
    <>
        <div
          className="min-h-screen"
          style={{
            background:
              "radial-gradient(circle at top right, rgba(201,168,76,0.09), transparent 32%), #090807",
            color: FG,
          }}
        >
          <DashboardHeader />

          <main className="mx-auto max-w-6xl px-4 py-8 md:px-6 md:py-12">
            {/* HEADER */}
            <div className="mb-8">
              <Link
                href="/dashboard/admin"
                className="mb-5 inline-flex items-center gap-2 text-sm transition-opacity hover:opacity-80"
                style={{ color: MUTED }}
              >
                ← Späť na admin
              </Link>

              <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <div
                    className="mb-2 text-[11px] font-semibold uppercase tracking-[0.32em]"
                    style={{ color: GOLD }}
                  >
                    LEAD OUTREACH
                  </div>

                  <h1
                    className="text-3xl leading-tight md:text-5xl"
                    style={{
                      fontFamily: "DM Serif Display, serif",
                      color: GOLD_BRIGHT,
                    }}
                  >
                    Oslovenie firiem
                  </h1>

                  <p
                    className="mt-3 max-w-2xl text-sm leading-6 md:text-base"
                    style={{ color: MUTED }}
                  >
                    Nájde firmy, pripraví personalizovaný email, doplní dostupné
                    kontakty a nechá posledné rozhodnutie na tebe.
                  </p>
                </div>

                <div
                  className="rounded-2xl border px-4 py-3 text-sm"
                  style={{
                    borderColor: "rgba(201,168,76,0.22)",
                    background: "rgba(255,255,255,0.025)",
                  }}
                >
                  <div
                    className="text-[10px] uppercase tracking-[0.2em]"
                    style={{ color: MUTED }}
                  >
                    Kandidáti
                  </div>
                  <div
                    className="mt-1 text-2xl font-semibold"
                    style={{ color: GOLD_BRIGHT }}
                  >
                    {pending.length}
                  </div>
                </div>
              </div>
            </div>

            {/* GLOBAL STATUS */}
            {err || okMsg ? (
              <div
                className="mb-6 rounded-2xl border px-4 py-3 text-sm"
                style={{
                  borderColor: err
                    ? "rgba(240,187,176,0.35)"
                    : "rgba(110,231,167,0.3)",
                  background: err
                    ? "rgba(240,187,176,0.06)"
                    : "rgba(110,231,167,0.05)",
                  color: err ? DANGER : OK,
                }}
              >
                <div className="flex items-start justify-between gap-4">
                  <span>{err || okMsg}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setErr(null);
                      setOkMsg(null);
                    }}
                    className="shrink-0 text-xs opacity-70 hover:opacity-100"
                  >
                    Zavrieť
                  </button>
                </div>
              </div>
            ) : null}

            {/* AUTOMATION */}
            <section
              className="mb-8 overflow-hidden rounded-3xl border"
              style={{
                borderColor: "rgba(201,168,76,0.3)",
                background:
                  "linear-gradient(135deg, rgba(201,168,76,0.10), rgba(255,255,255,0.025))",
              }}
            >
              <div className="p-5 md:p-7">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                  <div className="max-w-2xl">
                    <div
                      className="mb-2 text-xs font-semibold uppercase tracking-[0.2em]"
                      style={{ color: GOLD }}
                    >
                      Automatický workflow
                    </div>

                    <h2
                      className="text-xl font-semibold md:text-2xl"
                      style={{ color: GOLD_BRIGHT }}
                    >
                      Nájsť firmy → doplniť emaily → pripraviť na odoslanie
                    </h2>

                    <p
                      className="mt-2 text-sm leading-6"
                      style={{ color: MUTED }}
                    >
                      Najprv vytvoríme kandidátov a drafty. Potom dohľadáme
                      chýbajúce firemné emaily. Odoslanie prebehne až po
                      schválení konkrétneho kandidáta.
                    </p>
                  </div>

                  <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => void discoverDaily()}
                      disabled={busyDiscover || busyBackfill}
                      className="inline-flex min-h-11 items-center justify-center rounded-xl px-5 text-sm font-semibold transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
                      style={{ background: GOLD, color: BG }}
                    >
                      {busyDiscover
                        ? "Hľadám firmy…"
                        : "Nájsť 30 nových firiem"}
                    </button>

                    <button
                      type="button"
                      onClick={() => void backfillEmails()}
                      disabled={busyBackfill || busyDiscover}
                      className="inline-flex min-h-11 items-center justify-center rounded-xl border px-5 text-sm font-semibold transition hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-40"
                      style={{
                        borderColor: GOLD,
                        color: GOLD_BRIGHT,
                      }}
                    >
                      {busyBackfill
                        ? "Hľadám emaily…"
                        : "Nájsť chýbajúce emaily"}
                    </button>

                    <button
                      type="button"
                      onClick={() => void loadPending()}
                      disabled={busyPending || busyDiscover || busyBackfill}
                      className="inline-flex min-h-11 items-center justify-center rounded-xl border border-white/10 px-4 text-sm font-semibold transition hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-40"
                      style={{ color: FG }}
                    >
                      {busyPending ? "Obnovujem…" : "Obnoviť"}
                    </button>
                  </div>
                </div>
              </div>
            </section>

            {/* SUMMARY */}
            <div className="mb-8 grid gap-3 sm:grid-cols-3">
              <div
                className="rounded-2xl border p-4"
                style={{
                  borderColor: "rgba(201,168,76,0.2)",
                  background: "rgba(255,255,255,0.025)",
                }}
              >
                <div
                  className="text-[10px] uppercase tracking-[0.18em]"
                  style={{ color: MUTED }}
                >
                  Pripravené
                </div>
                <div
                  className="mt-2 text-2xl font-semibold"
                  style={{ color: GOLD_BRIGHT }}
                >
                  {pending.length}
                </div>
              </div>

              <div
                className="rounded-2xl border p-4"
                style={{
                  borderColor: "rgba(110,231,167,0.18)",
                  background: "rgba(110,231,167,0.025)",
                }}
              >
                <div
                  className="text-[10px] uppercase tracking-[0.18em]"
                  style={{ color: MUTED }}
                >
                  S emailom
                </div>
                <div
                  className="mt-2 text-2xl font-semibold"
                  style={{ color: OK }}
                >
                  {
                    pending.filter((item) =>
                      (pendingEmail[item.id] || "").trim().includes("@"),
                    ).length
                  }
                </div>
              </div>

              <div
                className="rounded-2xl border p-4"
                style={{
                  borderColor: "rgba(240,187,176,0.18)",
                  background: "rgba(240,187,176,0.025)",
                }}
              >
                <div
                  className="text-[10px] uppercase tracking-[0.18em]"
                  style={{ color: MUTED }}
                >
                  Bez emailu
                </div>
                <div
                  className="mt-2 text-2xl font-semibold"
                  style={{ color: DANGER }}
                >
                  {
                    pending.filter(
                      (item) =>
                        !(pendingEmail[item.id] || "").trim().includes("@"),
                    ).length
                  }
                </div>
              </div>
            </div>

            {/* PENDING */}
            <section
              className="mb-8 rounded-3xl border p-5 md:p-7"
              style={{
                borderColor: "rgba(201,168,76,0.28)",
                background: "rgba(201,168,76,0.035)",
              }}
            >
              <div
                className="mb-6 flex flex-col gap-4 border-b pb-5 md:flex-row md:items-center md:justify-between"
                style={{ borderColor: "rgba(255,255,255,0.08)" }}
              >
                <div>
                  <div
                    className="text-[10px] font-semibold uppercase tracking-[0.2em]"
                    style={{ color: GOLD }}
                  >
                    Queue
                  </div>
                  <h2
                    className="mt-1 text-2xl"
                    style={{
                      fontFamily: "DM Serif Display, serif",
                      color: GOLD_BRIGHT,
                    }}
                  >
                    Pripravené na odoslanie
                  </h2>
                  <p className="mt-1 text-xs" style={{ color: MUTED }}>
                    Skontroluj kontakty a obsah. Kandidát sa pri odoslaní najprv
                    uloží ako APPROVED a až potom sa odošle.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => void sendSelected()}
                  disabled={
                    busySendAll ||
                    busyPending ||
                    pending.length === 0 ||
                    pending.filter(
                      (i) =>
                        selectedPending[i.id] &&
                        (pendingEmail[i.id] || "").trim().includes("@"),
                    ).length === 0
                  }
                  className="min-h-11 rounded-xl px-5 text-sm font-semibold transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-35"
                  style={{ background: GOLD, color: BG }}
                >
                  {busySendAll
                    ? `Posielam ${sendAllProgress?.current ?? 0}/${sendAllProgress?.total ?? 0}…`
                    : `Poslať vybrané (${
                        pending.filter(
                          (i) =>
                            selectedPending[i.id] &&
                            (pendingEmail[i.id] || "").trim().includes("@"),
                        ).length
                      })`}
                </button>
              </div>

              {pending.length === 0 ? (
                <div
                  className="rounded-2xl border border-dashed p-8 text-center"
                  style={{
                    borderColor: "rgba(201,168,76,0.2)",
                    background: "rgba(0,0,0,0.18)",
                  }}
                >
                  <div
                    className="text-base font-semibold"
                    style={{ color: FG }}
                  >
                    Žiadni čakajúci kandidáti
                  </div>
                  <p
                    className="mx-auto mt-2 max-w-md text-sm leading-6"
                    style={{ color: MUTED }}
                  >
                    Spusti automatické hľadanie firiem alebo doplnenie emailov.
                    Výsledky sa objavia v tejto sekcii.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {pending.map((item) => {
                    const itemEmail = (pendingEmail[item.id] || "").trim();
                    const hasEmail = itemEmail.includes("@");
                    const selected = !!selectedPending[item.id];
                    const isSending = busySendId === item.id;
                    const isApproved = item.status === "APPROVED";

                    return (
                      <article
                        key={item.id}
                        className="rounded-2xl border p-4 md:p-5"
                        style={{
                          borderColor: selected
                            ? "rgba(201,168,76,0.42)"
                            : "rgba(255,255,255,0.08)",
                          background: selected
                            ? "rgba(201,168,76,0.045)"
                            : "rgba(0,0,0,0.2)",
                        }}
                      >
                        <div className="flex flex-col gap-4">
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                            <div className="flex items-start gap-3">
                              <input
                                type="checkbox"
                                checked={selected}
                                onChange={(e) =>
                                  setSelectedPending((prev) => ({
                                    ...prev,
                                    [item.id]: e.target.checked,
                                  }))
                                }
                                disabled={!hasEmail || busySendAll}
                                className="mt-1 h-5 w-5 accent-[#c9a84c]"
                                title={
                                  hasEmail
                                    ? "Zaradiť do dávky"
                                    : "Najprv doplň platný email"
                                }
                              />

                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <h3
                                    className="text-base font-semibold"
                                    style={{ color: GOLD_BRIGHT }}
                                  >
                                    {item.company_name}
                                  </h3>

                                  <span
                                    className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                                    style={{
                                      background: isApproved
                                        ? "rgba(110,231,167,0.12)"
                                        : "rgba(201,168,76,0.12)",
                                      color: isApproved ? OK : GOLD,
                                    }}
                                  >
                                    {item.status}
                                  </span>
                                </div>

                                <p
                                  className="mt-1 text-xs"
                                  style={{ color: MUTED }}
                                >
                                  {[item.city, item.ico, item.industry]
                                    .filter(Boolean)
                                    .join(" · ") || "Bez doplňujúcich údajov"}
                                </p>
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={() => void skipPending(item)}
                              disabled={busySendAll || isSending}
                              className="self-start text-xs underline underline-offset-2 opacity-60 transition hover:opacity-100 disabled:opacity-30"
                              style={{ color: MUTED }}
                            >
                              Preskočiť
                            </button>
                          </div>

                          <div className="grid gap-3 lg:grid-cols-[1fr_1.5fr]">
                            <div>
                              <label
                                className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.16em]"
                                style={{ color: MUTED }}
                              >
                                Firemný email
                              </label>
                              <input
                                type="email"
                                placeholder={t("admin.phEmail")}
                                value={pendingEmail[item.id] || ""}
                                onChange={(e) =>
                                  setPendingEmail((p) => ({
                                    ...p,
                                    [item.id]: e.target.value,
                                  }))
                                }
                                disabled={busySendAll || isSending}
                                className="h-11 w-full rounded-xl border px-3 text-sm outline-none transition focus:ring-1 focus:ring-[#c9a84c]/50 disabled:opacity-50"
                                style={inputStyle}
                              />
                              {!hasEmail ? (
                                <p
                                  className="mt-1.5 text-xs"
                                  style={{ color: DANGER }}
                                >
                                  Chýba platný email.
                                </p>
                              ) : (
                                <p
                                  className="mt-1.5 text-xs"
                                  style={{ color: OK }}
                                >
                                  Email je pripravený na odoslanie.
                                </p>
                              )}
                            </div>

                            <div>
                              <label
                                className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.16em]"
                                style={{ color: MUTED }}
                              >
                                Predmet
                              </label>
                              <input
                                type="text"
                                placeholder={t("admin.phSubject")}
                                value={pendingSubject[item.id] || ""}
                                onChange={(e) =>
                                  setPendingSubject((p) => ({
                                    ...p,
                                    [item.id]: e.target.value,
                                  }))
                                }
                                disabled={busySendAll || isSending}
                                className="h-11 w-full rounded-xl border px-3 text-sm outline-none transition focus:ring-1 focus:ring-[#c9a84c]/50 disabled:opacity-50"
                                style={inputStyle}
                              />
                            </div>
                          </div>

                          <details
                            className="rounded-xl border"
                            style={{ borderColor: "rgba(255,255,255,0.08)" }}
                          >
                            <summary
                              className="cursor-pointer px-4 py-3 text-xs font-semibold"
                              style={{ color: GOLD_BRIGHT }}
                            >
                              Zobraziť pripravený email
                            </summary>
                            <div
                              className="border-t px-4 py-4"
                              style={{ borderColor: "rgba(255,255,255,0.08)" }}
                            >
                              <div
                                className="mb-2 text-xs"
                                style={{ color: MUTED }}
                              >
                                Predmet:{" "}
                                <span style={{ color: FG }}>
                                  {pendingSubject[item.id] ||
                                    item.subject ||
                                    "(bez predmetu)"}
                                </span>
                              </div>
                              <pre
                                className="max-h-72 overflow-auto whitespace-pre-wrap rounded-xl border p-4 text-xs leading-5"
                                style={{
                                  borderColor: "rgba(201,168,76,0.14)",
                                  background: "#050505",
                                  color: FG,
                                  fontFamily: "inherit",
                                }}
                              >
                                {item.body || "(prázdne)"}
                              </pre>
                            </div>
                          </details>

                          <div
                            className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between"
                            style={{ borderColor: "rgba(255,255,255,0.08)" }}
                          >
                            <div className="text-xs" style={{ color: MUTED }}>
                              {isApproved
                                ? "Kandidát je schválený. Odoslanie môžeš zopakovať."
                                : "Pri odoslaní sa najprv uložia tvoje upravené údaje."}
                            </div>

                            <button
                              type="button"
                              disabled={
                                busySendAll ||
                                isSending ||
                                !hasEmail ||
                                !(
                                  pendingSubject[item.id] ||
                                  item.subject ||
                                  ""
                                ).trim() ||
                                !(item.body || "").trim()
                              }
                              onClick={() => void sendPending(item)}
                              className="min-h-11 rounded-xl px-6 text-sm font-semibold transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-35"
                              style={{ background: GOLD, color: BG }}
                            >
                              {isSending
                                ? "Odosielam…"
                                : isApproved
                                  ? "Poslať znova"
                                  : "Schváliť a poslať"}
                            </button>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            {/* DISCOVERED TODAY */}
            {found.length ? (
              <section
                className="mb-8 rounded-3xl border p-5 md:p-7"
                style={{
                  borderColor: "rgba(201,168,76,0.2)",
                  background: "rgba(255,255,255,0.02)",
                }}
              >
                <div className="mb-4">
                  <div
                    className="text-[10px] font-semibold uppercase tracking-[0.2em]"
                    style={{ color: GOLD }}
                  >
                    Discovery
                  </div>
                  <h2
                    className="mt-1 text-xl"
                    style={{
                      fontFamily: "DM Serif Display, serif",
                      color: GOLD_BRIGHT,
                    }}
                  >
                    Dnešných {found.length} firiem
                  </h2>
                  <p className="mt-1 text-xs" style={{ color: MUTED }}>
                    Kliknutím otvoríš kandidáta v pracovnom formulári.
                  </p>
                </div>

                <div className="grid gap-2 md:grid-cols-2">
                  {found.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="rounded-xl border p-3 text-left text-sm transition hover:bg-white/[0.035]"
                      style={{
                        borderColor: "rgba(255,255,255,0.08)",
                        background: "#0b0b0b",
                      }}
                      onClick={() => {
                        setCompanyName(item.company_name || "");
                        setCity(item.city || "");
                        setIndustry(item.industry || "");
                        setSubject(item.subject || "");
                        setBody(item.body || "");
                        void draftFrom({
                          company_name: item.company_name || "",
                          city: item.city,
                          industry: item.industry,
                          reason: "pozvanka na platformu CMEP",
                        });
                      }}
                    >
                      <span
                        className="font-semibold"
                        style={{ color: GOLD_BRIGHT }}
                      >
                        {item.company_name}
                      </span>
                      <span className="ml-1 text-xs" style={{ color: MUTED }}>
                        · {item.city || "—"} · {item.ico || "bez IČO"}
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            ) : null}

            {/* MANUAL TOOLS */}
            <div className="mb-4">
              <div
                className="text-[10px] font-semibold uppercase tracking-[0.2em]"
                style={{ color: MUTED }}
              >
                Pokročilé nástroje
              </div>
            </div>

            <details
              className="mb-4 rounded-2xl border"
              style={{
                borderColor: "rgba(255,255,255,0.08)",
                background: "rgba(255,255,255,0.018)",
              }}
            >
              <summary
                className="cursor-pointer px-5 py-4 text-sm font-semibold"
                style={{ color: GOLD_BRIGHT }}
              >
                + Pridať firmu manuálne
              </summary>

              <div
                className="border-t p-5 md:p-6"
                style={{ borderColor: "rgba(255,255,255,0.08)" }}
              >
                <div className="grid gap-3 md:grid-cols-2">
                  <input
                    placeholder={t("admin.phCompanyName")}
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="h-11 rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                    style={inputStyle}
                  />
                  <input
                    placeholder={t("admin.phCity")}
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="h-11 rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                    style={inputStyle}
                  />
                  <input
                    placeholder={t("admin.phIndustry")}
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="h-11 rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                    style={inputStyle}
                  />
                  <input
                    placeholder={t("admin.phEmail")}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-11 rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                    style={inputStyle}
                  />
                </div>

                <textarea
                  placeholder="Dôvod kontaktovania (napr. Firma spracúva drevo a mohla by mať záujem o predaj pilín.)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  className="mt-3 w-full resize-none rounded-xl border p-3 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                  style={inputStyle}
                />

                <button
                  type="button"
                  onClick={() =>
                    void draftFrom({
                      company_name: companyName,
                      city,
                      industry,
                      reason,
                    })
                  }
                  disabled={busyDraft || !companyName.trim()}
                  className="mt-4 min-h-11 rounded-xl px-5 text-sm font-semibold disabled:opacity-40"
                  style={{ background: GOLD, color: BG }}
                >
                  {busyDraft ? "Pripravujem…" : "Vygenerovať návrh"}
                </button>
              </div>
            </details>

            <section
              className="mb-4 rounded-2xl border p-5 md:p-6"
              style={{
                borderColor: "rgba(255,255,255,0.08)",
                background: "rgba(255,255,255,0.018)",
              }}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2
                    className="text-base font-semibold"
                    style={{ color: GOLD }}
                  >
                    Dávka z CSV
                  </h2>
                  <p className="mt-1 text-sm" style={{ color: MUTED }}>
                    Hromadné oslovenie do 30 firiem má vlastnú pracovnú stránku.
                  </p>
                </div>

                <Link
                  href="/dashboard/admin/lead-outreach/batch"
                  className="inline-flex min-h-10 items-center justify-center rounded-xl px-5 text-sm font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Otvoriť dávkové oslovenie
                </Link>
              </div>
            </section>

            <details
              className="rounded-2xl border"
              style={{
                borderColor: "rgba(255,255,255,0.08)",
                background: "rgba(255,255,255,0.018)",
              }}
            >
              <summary
                className="cursor-pointer px-5 py-4 text-sm font-semibold"
                style={{ color: GOLD_BRIGHT }}
              >
                Manuálny náhľad a odoslanie jednej firmy
              </summary>

              <div
                className="border-t p-5 md:p-6"
                style={{ borderColor: "rgba(255,255,255,0.08)" }}
              >
                <input
                  placeholder={t("admin.phSubject")}
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="h-11 w-full rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                  style={inputStyle}
                />

                <textarea
                  placeholder={t("admin.phBody")}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={12}
                  className="mt-3 w-full resize-y rounded-xl border p-4 text-sm leading-6 outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                  style={inputStyle}
                />

                <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_auto]">
                  <input
                    type="email"
                    placeholder={t("admin.phEmail")}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-11 rounded-xl border px-4 text-sm outline-none focus:ring-1 focus:ring-[#c9a84c]/50"
                    style={inputStyle}
                  />

                  <button
                    type="button"
                    onClick={() => void send()}
                    disabled={
                      busySend ||
                      !subject.trim() ||
                      !body.trim() ||
                      !email.trim()
                    }
                    className="min-h-11 rounded-xl px-6 text-sm font-semibold disabled:opacity-40"
                    style={{ background: GOLD, color: BG }}
                  >
                    {busySend ? "Odosielam…" : "Poslať email"}
                  </button>
                </div>
              </div>
            </details>
          </main>

          <DashboardFooter />
        </div>
    </>
  );
}
