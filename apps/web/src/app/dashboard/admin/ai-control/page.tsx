'use client';

import { useEffect, useState, useCallback } from 'react';
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

type Tab = 'control' | 'security' | 'alerts' | 'approvals' | 'audit';

type ControlModeResp = { mode: string };
type SecurityEvent = {
  eventId: string;
  kind: string;
  pattern: string;
  source?: string | null;
  actorId?: string | null;
  target?: string | null;
  confidence?: number | null;
  sourceObservationId?: string | null;
  occurredAt?: string | null;
};
type SecurityEventsResp = { items: SecurityEvent[]; count: number };
type Alert = {
  alertId: string;
  category: string;
  severity: string;
  source: string;
  actorId?: string | null;
  event: string;
  status: string;
  createdAt?: string | null;
  assignedTo?: string | null;
  resolution?: string | null;
};
type AlertsResp = { items: Alert[]; count: number };
type Approval = {
  approvalId: string;
  requestedBy: string;
  requestedByType: string;
  action: string;
  target?: string | null;
  reason: string;
  riskLevel: string;
  status: string;
  createdAt?: string | null;
  expiresAt?: string | null;
  decidedBy?: string | null;
  decidedAt?: string | null;
  decisionReason?: string | null;
};
type ApprovalsResp = { items: Approval[]; count: number };
type AuditRow = {
  auditId: string;
  actorId?: string | null;
  actorType: string;
  action: string;
  subjectType?: string | null;
  subjectId?: string | null;
  occurredAt?: string | null;
  success: boolean;
  reason?: string | null;
};
type AuditResp = { items: AuditRow[]; count: number };

const cardStyle = {
  borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
  background: 'rgba(201,168,76,0.03)',
};

const severityColor = (s: string) => {
  switch (s) {
    case 'critical':
      return '#f0a8a0';
    case 'high':
      return '#f0c090';
    case 'medium':
      return GOLD_BRIGHT;
    case 'low':
      return '#9ad0a0';
    default:
      return MUTED;
  }
};

export default function AiControlPage() {
  const { user, isLoading } = useAuthRequired();
  const isAdmin = useIsPlatformAdmin();
  const [tab, setTab] = useState<Tab>('control');

  const [mode, setMode] = useState<string>('…');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const [secEvents, setSecEvents] = useState<SecurityEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);

  const loadMode = useCallback(async () => {
    try {
      const r = await http.get<ControlModeResp>('/agent-platform/control/mode');
      setMode(r.mode || 'unknown');
    } catch {
      setMode('unknown');
    }
  }, []);

  const loadSecurity = useCallback(async () => {
    try {
      const r = await http.get<SecurityEventsResp>('/agent-platform/security/events?limit=50');
      setSecEvents(r.items || []);
    } catch {
      setSecEvents([]);
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      const r = await http.get<AlertsResp>('/agent-platform/alerts?limit=50');
      setAlerts(r.items || []);
    } catch {
      setAlerts([]);
    }
  }, []);

  const loadApprovals = useCallback(async () => {
    try {
      const r = await http.get<ApprovalsResp>('/agent-platform/approvals?limit=50');
      setApprovals(r.items || []);
    } catch {
      setApprovals([]);
    }
  }, []);

  const loadAudit = useCallback(async () => {
    try {
      const r = await http.get<AuditResp>('/agent-platform/audit/recent?limit=100');
      setAudit(r.items || []);
    } catch {
      setAudit([]);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin) return;
    void loadMode();
  }, [isAdmin, loadMode]);

  useEffect(() => {
    if (!isAdmin) return;
    if (tab === 'security') void loadSecurity();
    if (tab === 'alerts') void loadAlerts();
    if (tab === 'approvals') void loadApprovals();
    if (tab === 'audit') void loadAudit();
  }, [tab, isAdmin, loadSecurity, loadAlerts, loadApprovals, loadAudit]);

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

  async function changeMode(action: string, reason: string) {
    setErr(null);
    setOkMsg(null);
    setBusy(true);
    try {
      const r = await http.post<ControlModeResp>('/agent-platform/control/mode', { action, reason });
      setMode(r.mode);
      setOkMsg(`Režim zmenený na ${r.mode}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Zmena režimu zlyhala');
    } finally {
      setBusy(false);
    }
  }

  async function emergency(which: 'activate' | 'release') {
    setErr(null);
    setOkMsg(null);
    setBusy(true);
    try {
      const r = await http.post<{ mode: string }>(
        `/agent-platform/control/emergency/${which}`,
        { action: 'emergency', reason: which === 'activate' ? 'manual activation' : 'manual release' },
      );
      setMode(r.mode);
      setOkMsg(which === 'activate' ? 'Emergencia aktivovaná.' : 'Emergencia zrušená.');
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Emergencia zlyhala');
    } finally {
      setBusy(false);
    }
  }

  async function ackAlert(id: string) {
    setErr(null);
    try {
      await http.post(`/agent-platform/alerts/${id}/ack`, {});
      await loadAlerts();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ack zlyhal');
    }
  }

  async function resolveAlert(id: string) {
    const resolution = window.prompt('Dôvod vyriešenia:');
    if (!resolution) return;
    try {
      await http.post(`/agent-platform/alerts/${id}/resolve`, { resolution });
      await loadAlerts();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Resolve zlyhal');
    }
  }

  async function decideApproval(id: string, kind: 'approve' | 'deny') {
    const reason = window.prompt(kind === 'approve' ? 'Dôvod schválenia:' : 'Dôvod zamietnutia:');
    if (reason === null) return;
    try {
      await http.post(`/agent-platform/approvals/${id}/${kind}`, { reason: reason || 'admin decision' });
      await loadApprovals();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Rozhodnutie zlyhalo');
    }
  }

  return (
    <>
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />

        <main className="mx-auto max-w-6xl px-4 py-10">
          <Link href="/dashboard/admin" className="mb-6 inline-block text-sm" style={{ color: GOLD_BRIGHT }}>
            ← Späť na admin
          </Link>

          <p className="mb-2 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            AI CONTROL · GOVERNANCE
          </p>
          <h1
            className="mb-3 text-3xl md:text-4xl"
            style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
          >
            Riadenie AI a bezpečnosť
          </h1>
          <p className="mb-8 text-sm" style={{ color: MUTED }}>
            Ovládanie režimu AI, bezpečnostné udalosti, alerty, schvaľovanie a audit.
          </p>

          {/* STATUS BAR */}
          <div className="mb-6 flex flex-wrap items-center gap-3 rounded-2xl border p-4" style={cardStyle}>
            <span className="text-sm" style={{ color: MUTED }}>Aktuálny režim:</span>
            <span
              className="rounded-full px-3 py-1 text-sm font-semibold"
              style={{
                background: mode === 'normal' ? 'rgba(110,231,167,0.15)' : 'rgba(240,168,160,0.15)',
                color: mode === 'normal' ? OK : DANGER,
              }}
            >
              ● {mode}
            </span>
            <span className="ml-auto text-xs" style={{ color: MUTED }}>
              {err ? <span style={{ color: DANGER }}>{err}</span> : null}
              {okMsg ? <span style={{ color: OK }}>{okMsg}</span> : null}
            </span>
          </div>

          {/* TABS */}
          <div className="mb-6 flex flex-wrap gap-2">
            {(
              [
                ['control', 'Control'],
                ['security', 'Security'],
                ['alerts', 'Alerts'],
                ['approvals', 'Approvals'],
                ['audit', 'Audit'],
              ] as [Tab, string][]
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className="rounded-full px-4 py-2 text-sm font-semibold transition"
                style={{
                  background: tab === key ? GOLD : 'rgba(201,168,76,0.08)',
                  color: tab === key ? BG : GOLD_BRIGHT,
                  border: `1px solid ${tab === key ? GOLD : 'color-mix(in srgb, #c9a84c 25%, transparent)'}`,
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* CONTROL TAB */}
          {tab === 'control' ? (
            <section className="rounded-2xl border p-5 md:p-6" style={cardStyle}>
              <h2
                className="mb-4 text-xl"
                style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
              >
                Kontrola režimu AI
              </h2>
              <div className="grid gap-3 md:grid-cols-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void changeMode('enable_ai', 'manual enable')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: OK, color: BG }}
                >
                  Aktivovať AI (normal)
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void changeMode('read_only', 'manual read-only')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: GOLD, color: BG }}
                >
                  Read-only
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void changeMode('disable_ai', 'manual disable')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: 'rgba(240,168,160,0.25)', color: DANGER }}
                >
                  Vypnúť AI
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void changeMode('lockdown', 'manual lockdown')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: 'rgba(240,168,160,0.25)', color: DANGER }}
                >
                  Lockdown
                </button>
              </div>

              <h3 className="mt-8 mb-3 text-lg" style={{ color: GOLD_BRIGHT }}>
                Núdzové ovládanie
              </h3>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void emergency('activate')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: DANGER, color: BG }}
                >
                  🚨 Emergency stop
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void emergency('release')}
                  className="rounded-lg px-5 py-3 text-sm font-semibold disabled:opacity-40"
                  style={{ background: GOLD, color: BG }}
                >
                  Obnoviť (release)
                </button>
              </div>
            </section>
          ) : null}

          {/* SECURITY TAB */}
          {tab === 'security' ? (
            <section className="rounded-2xl border p-5 md:p-6" style={cardStyle}>
              <div className="mb-4 flex items-center justify-between">
                <h2
                  className="text-xl"
                  style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                >
                  Bezpečnostné udalosti ({secEvents.length})
                </h2>
                <button
                  type="button"
                  onClick={() => void loadSecurity()}
                  className="rounded-full px-3 py-1 text-xs font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Obnoviť
                </button>
              </div>
              {secEvents.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>
                  Žiadne bezpečnostné udalosti.
                </p>
              ) : (
                <ul className="space-y-2">
                  {secEvents.map((e) => (
                    <li key={e.eventId} className="rounded-xl border p-3 text-sm" style={cardStyle}>
                      <div className="flex items-center justify-between">
                        <span style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>{e.pattern}</span>
                        <span
                          className="rounded-full px-2 py-0.5 text-xs"
                          style={{ background: 'rgba(201,168,76,0.15)', color: GOLD }}
                        >
                          {e.kind}
                        </span>
                      </div>
                      <p className="mt-1 text-xs" style={{ color: MUTED }}>
                        {e.occurredAt || '—'} · actor {e.actorId || '—'}
                        {e.confidence != null ? ` · confidence ${e.confidence.toFixed(2)}` : ''}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}

          {/* ALERTS TAB */}
          {tab === 'alerts' ? (
            <section className="rounded-2xl border p-5 md:p-6" style={cardStyle}>
              <div className="mb-4 flex items-center justify-between">
                <h2
                  className="text-xl"
                  style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                >
                  Alerty ({alerts.length})
                </h2>
                <button
                  type="button"
                  onClick={() => void loadAlerts()}
                  className="rounded-full px-3 py-1 text-xs font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Obnoviť
                </button>
              </div>
              {alerts.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>
                  Žiadne alerty.
                </p>
              ) : (
                <ul className="space-y-2">
                  {alerts.map((a) => (
                    <li key={a.alertId} className="rounded-xl border p-3 text-sm" style={cardStyle}>
                      <div className="flex items-center justify-between">
                        <span style={{ color: severityColor(a.severity), fontWeight: 600 }}>
                          {a.category} · {a.severity}
                        </span>
                        <span className="text-xs" style={{ color: MUTED }}>
                          {a.status}
                        </span>
                      </div>
                      <p className="mt-1 text-xs" style={{ color: FG }}>
                        {a.event}
                      </p>
                      <p className="text-xs" style={{ color: MUTED }}>
                        {a.createdAt || '—'} · actor {a.actorId || '—'}
                      </p>
                      <div className="mt-2 flex gap-2">
                        {a.status === 'open' ? (
                          <button
                            type="button"
                            onClick={() => void ackAlert(a.alertId)}
                            className="rounded-full px-3 py-1 text-xs font-semibold"
                            style={{ background: GOLD, color: BG }}
                          >
                            Acknowledge
                          </button>
                        ) : null}
                        {a.status !== 'resolved' ? (
                          <button
                            type="button"
                            onClick={() => void resolveAlert(a.alertId)}
                            className="rounded-full px-3 py-1 text-xs font-semibold"
                            style={{ background: 'rgba(110,231,167,0.2)', color: OK }}
                          >
                            Resolve
                          </button>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}

          {/* APPROVALS TAB */}
          {tab === 'approvals' ? (
            <section className="rounded-2xl border p-5 md:p-6" style={cardStyle}>
              <div className="mb-4 flex items-center justify-between">
                <h2
                  className="text-xl"
                  style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                >
                  Schválenia ({approvals.length})
                </h2>
                <button
                  type="button"
                  onClick={() => void loadApprovals()}
                  className="rounded-full px-3 py-1 text-xs font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Obnoviť
                </button>
              </div>
              {approvals.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>
                  Žiadne čakajúce schválenia.
                </p>
              ) : (
                <ul className="space-y-2">
                  {approvals.map((p) => (
                    <li key={p.approvalId} className="rounded-xl border p-3 text-sm" style={cardStyle}>
                      <div className="flex items-center justify-between">
                        <span style={{ color: GOLD_BRIGHT, fontWeight: 600 }}>{p.action}</span>
                        <span className="text-xs" style={{ color: severityColor(p.riskLevel) }}>
                          {p.riskLevel}
                        </span>
                      </div>
                      <p className="mt-1 text-xs" style={{ color: FG }}>
                        {p.reason}
                      </p>
                      <p className="text-xs" style={{ color: MUTED }}>
                        requested by {p.requestedBy} · {p.createdAt || '—'} · status {p.status}
                      </p>
                      {p.status === 'pending' ? (
                        <div className="mt-2 flex gap-2">
                          <button
                            type="button"
                            onClick={() => void decideApproval(p.approvalId, 'approve')}
                            className="rounded-full px-3 py-1 text-xs font-semibold"
                            style={{ background: OK, color: BG }}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            onClick={() => void decideApproval(p.approvalId, 'deny')}
                            className="rounded-full px-3 py-1 text-xs font-semibold"
                            style={{ background: 'rgba(240,168,160,0.25)', color: DANGER }}
                          >
                            Deny
                          </button>
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}

          {/* AUDIT TAB */}
          {tab === 'audit' ? (
            <section className="rounded-2xl border p-5 md:p-6" style={cardStyle}>
              <div className="mb-4 flex items-center justify-between">
                <h2
                  className="text-xl"
                  style={{ fontFamily: 'DM Serif Display, serif', color: GOLD_BRIGHT }}
                >
                  Audit agenta ({audit.length})
                </h2>
                <button
                  type="button"
                  onClick={() => void loadAudit()}
                  className="rounded-full px-3 py-1 text-xs font-semibold"
                  style={{ background: GOLD, color: BG }}
                >
                  Obnoviť
                </button>
              </div>
              {audit.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>
                  Žiadne záznamy. (Zapíšu sa pri každej AI tool akcii.)
                </p>
              ) : (
                <ul className="space-y-2">
                  {audit.map((a) => (
                    <li key={a.auditId} className="rounded-xl border p-3 text-sm" style={cardStyle}>
                      <div className="flex items-center justify-between">
                        <span style={{ color: a.success ? OK : DANGER, fontWeight: 600 }}>
                          {a.action}
                        </span>
                        <span className="text-xs" style={{ color: MUTED }}>
                          {a.occurredAt || '—'}
                        </span>
                      </div>
                      <p className="mt-1 text-xs" style={{ color: FG }}>
                        {a.subjectType ? `${a.subjectType}:${a.subjectId || '—'}` : '—'}
                      </p>
                      <p className="text-xs" style={{ color: MUTED }}>
                        actor {a.actorId || '—'} · {a.reason || 'ok'}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}
        </main>

        <DashboardFooter />
      </div>
    </>
  );
}
