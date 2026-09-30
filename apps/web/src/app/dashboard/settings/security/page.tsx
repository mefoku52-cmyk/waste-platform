'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { http } from '@/lib/api/http';
import { useAuthRequired } from '@/features/auth';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const DANGER = '#e8a598';
const OK = '#5fd17a';
const BG = '#090807';
const FG = '#f3ead8';

type Status = { enabled: boolean; verifiedAt?: string | null };
type SetupResp = { secret: string; otpauthUri: string; qrSvg: string };
type VerifyResp = { ok: boolean; backupCodes: string[] };

const cardStyle = {
  borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
  background: 'rgba(201,168,76,0.03)',
};

export default function SecuritySettingsPage() {
  const { user, isLoading } = useAuthRequired();
  const qc = useQueryClient();

  const [setupData, setSetupData] = useState<SetupResp | null>(null);
  const [code, setCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const status = useQuery({
    queryKey: ['2fa-status'],
    queryFn: () => http.get<Status>('/auth/2fa/status'),
    enabled: Boolean(user),
  });

  const startSetup = useMutation({
    mutationFn: () => http.post<SetupResp>('/auth/2fa/setup', {}),
    onSuccess: (data) => {
      setSetupData(data);
      setErr(null);
      setOk(null);
      setCode('');
    },
    onError: (e) => setErr(e instanceof Error ? e.message : 'Setup zlyhal'),
  });

  const verify = useMutation({
    mutationFn: (c: string) => http.post<VerifyResp>('/auth/2fa/verify', { code: c }),
    onSuccess: (data) => {
      setBackupCodes(data.backupCodes || []);
      setSetupData(null);
      setOk('2FA je aktívna. Ulož si backup kódy na bezpečné miesto!');
      setErr(null);
      setCode('');
      qc.invalidateQueries({ queryKey: ['2fa-status'] });
    },
    onError: (e) => setErr(e instanceof Error ? e.message : 'Nesprávny kód'),
  });

  const disable = useMutation({
    mutationFn: (c: string) => http.post<VerifyResp>('/auth/2fa/disable', { code: c }),
    onSuccess: () => {
      setOk('2FA bola vypnutá.');
      setErr(null);
      setCode('');
      setBackupCodes(null);
      qc.invalidateQueries({ queryKey: ['2fa-status'] });
    },
    onError: (e) => setErr(e instanceof Error ? e.message : 'Nesprávny kód'),
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="min-h-screen" style={{ background: BG, color: MUTED }}>
          <p className="p-8 text-center">Načítavam…</p>
        </div>
      </AppShell>
    );
  }

  const enabled = status.data?.enabled ?? false;

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-3xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link
          href="/dashboard"
          className="inline-flex rounded-full border px-3 py-1.5 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}
        >
          ← Späť na dashboard
        </Link>

        <p className="mt-6 text-[10px] font-semibold uppercase tracking-[0.24em]" style={{ color: GOLD }}>
          NASTAVENIA ÚČTU
        </p>
        <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
          Bezpečnosť
        </h1>

        {/* STATUS */}
        <section className="mt-6 rounded-2xl border p-5" style={cardStyle}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                Dvojfaktorové overenie (2FA)
              </p>
              <p className="mt-1 text-xs" style={{ color: MUTED }}>
                6-ciferný kód z Google Authenticator alebo Authy
              </p>
            </div>
            <span
              className="rounded-full px-3 py-1 text-xs font-semibold"
              style={{
                background: enabled ? 'rgba(110,231,167,0.15)' : 'rgba(201,168,76,0.12)',
                color: enabled ? OK : MUTED,
              }}
            >
              ● {enabled ? 'Aktívna' : 'Vypnutá'}
            </span>
          </div>

          {ok ? <p className="mt-4 text-sm" style={{ color: OK }}>{ok}</p> : null}
          {err ? <p className="mt-4 text-sm" style={{ color: DANGER }}>{err}</p> : null}

          {/* VYPNUTA - tlacidlo zapnut */}
          {!enabled && !setupData ? (
            <button
              type="button"
              onClick={() => startSetup.mutate()}
              disabled={startSetup.isPending}
              className="mt-4 rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ background: GOLD, color: BG }}
            >
              {startSetup.isPending ? 'Pripravujem…' : 'Zapnúť 2FA'}
            </button>
          ) : null}

          {/* SETUP - QR kod + verifikacia */}
          {setupData ? (
            <div className="mt-5">
              <p className="text-sm" style={{ color: FG }}>
                Naskenuj QR kód v Google Authenticator:
              </p>
              <div
                className="mt-3 inline-block rounded-xl border p-3"
                style={{ background: '#fff', borderColor: 'rgba(201,168,76,0.3)' }}
                dangerouslySetInnerHTML={{ __html: setupData.qrSvg }}
              />
              <p className="mt-3 text-xs" style={{ color: MUTED }}>
                Alebo zadaj manuálne: <code style={{ color: GOLD_BRIGHT }}>{setupData.secret}</code>
              </p>

              <div className="mt-5">
                <label className="text-xs uppercase tracking-[0.18em]" style={{ color: MUTED }}>
                  ZADAJ 6-CIFERNÝ KÓD
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                  maxLength={6}
                  className="mt-2 block w-full max-w-xs rounded-lg border px-4 py-2 text-sm outline-none"
                  style={{
                    borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
                    background: '#0b0b0b',
                    color: FG,
                  }}
                />
              </div>

              <div className="mt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => verify.mutate(code)}
                  disabled={verify.isPending || code.length !== 6}
                  className="rounded-full px-5 py-2 text-sm font-semibold disabled:opacity-40"
                  style={{ background: OK, color: BG }}
                >
                  {verify.isPending ? 'Overujem…' : 'Aktivovať 2FA'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSetupData(null);
                    setCode('');
                  }}
                  className="rounded-full border px-5 py-2 text-sm"
                  style={{ borderColor: 'rgba(201,168,76,0.3)', color: MUTED }}
                >
                  Zrušiť
                </button>
              </div>
            </div>
          ) : null}

          {/* BACKUP KODY */}
          {backupCodes && backupCodes.length ? (
            <div
              className="mt-6 rounded-xl border p-4"
              style={{ background: 'rgba(201,168,76,0.06)', borderColor: 'rgba(201,168,76,0.3)' }}
            >
              <p className="text-sm font-semibold" style={{ color: GOLD_BRIGHT }}>
                ⚠️ Backup kódy (zobrazia sa len raz)
              </p>
              <p className="mt-1 text-xs" style={{ color: MUTED }}>
                Ulož si ich. Môžeš ich použiť namiesto TOTP, ak stratíš telefón.
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-sm">
                {backupCodes.map((c) => (
                  <div
                    key={c}
                    className="rounded-lg border px-3 py-2"
                    style={{ borderColor: 'rgba(201,168,76,0.2)', color: GOLD_BRIGHT }}
                  >
                    {c}
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* AKTIVNA - tlacidlo vypnut */}
          {enabled ? (
            <div className="mt-6 border-t pt-5" style={{ borderColor: 'rgba(201,168,76,0.15)' }}>
              <p className="text-sm" style={{ color: MUTED }}>
                Vypnutie 2FA vyžaduje aktuálny 6-ciferný kód.
              </p>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456 alebo XXXX-XXXX"
                maxLength={16}
                className="mt-3 block w-full max-w-xs rounded-lg border px-4 py-2 text-sm outline-none"
                style={{
                  borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)',
                  background: '#0b0b0b',
                  color: FG,
                }}
              />
              <button
                type="button"
                onClick={() => disable.mutate(code)}
                disabled={disable.isPending || code.length < 6}
                className="mt-3 rounded-full border px-5 py-2 text-sm font-semibold disabled:opacity-40"
                style={{ borderColor: 'rgba(240,168,160,0.5)', color: DANGER }}
              >
                {disable.isPending ? 'Vypínam…' : 'Vypnúť 2FA'}
              </button>
            </div>
          ) : null}
        </section>

        <p className="mt-6 text-xs" style={{ color: MUTED }}>
          Tip: Pre admin účet odporúčame 2FA vždy zapnutú.
        </p>
      </div>
    </AppShell>
  );
}
