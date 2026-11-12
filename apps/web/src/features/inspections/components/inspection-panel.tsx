'use client';

import { useCallback, useState } from 'react';
import { useT } from '@/lib/i18n/context';
import { useQueryClient } from '@tanstack/react-query';
import { inspectionsApi } from '../api';
import { useActiveInspection } from '../hooks/use-inspections-queries';
import { inspectionStateLabel } from '../state-label';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';

/**
 * Panel živej obhliadky pre chat a stranu ponuky.
 *
 * - publisher (vlastník firmy): spustenie obhliadky, opätovné otvorenie
 *   publisher stránky, pozvanie druhého účastníka (link), súhlas s nahrávaním
 *   a ukončenie obhliadky — tokeny, Inspection ID a Room ID prenáša platforma
 *   automaticky v URL.
 * - viewer (druhá strana): pripojenie cez viewer URL (token + Room ID).
 * Žiadne ručné kopírovanie tokenov / Offer ID / Company ID / Inspection ID / Room ID.
 */
export const InspectionPanel = ({ threadId, listingId }: { threadId?: string | null; listingId?: string | null }) => {
  const { t } = useT();
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { data } = useActiveInspection(listingId ?? undefined);

  if (!listingId) return null;
  const active = (data as any)?.inspection ?? null;
  const canPublish = Boolean((data as any)?.canPublish);
  const canJoin = Boolean((data as any)?.canJoin);
  const isViewer = Boolean((data as any)?.isViewer);
  const state = active?.state ?? null;

  const openUrl = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  const callApi = useCallback(async (fn: () => Promise<any>, errorKey?: string) => {
    setBusy(true);
    setErr(null);
    try {
      const res = await fn();
      await qc.invalidateQueries({ queryKey: ['inspection-active', listingId] });
      return res;
    } catch (e: any) {
      setErr(e?.message || t(errorKey || 'inspections.startFailed'));
    } finally {
      setBusy(false);
    }
  }, [listingId, qc, t]);

  const startInspection = async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await inspectionsApi.create(listingId!);
      openUrl(res.publishUrl);
      await qc.invalidateQueries({ queryKey: ['inspection-active', listingId] });
    } catch (e: any) {
      setErr(e?.message || t('inspections.startFailed'));
    } finally {
      setBusy(false);
    }
  };

  const reopen = async () => {
    if (!active) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await inspectionsApi.publisherLink(active.id);
      openUrl(res.publishUrl);
    } catch (e: any) {
      setErr(e?.message || t('inspections.reopenFailed'));
    } finally {
      setBusy(false);
    }
  };

  const joinInspection = async () => {
    if (!active) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await inspectionsApi.join({
        inspectionId: active.id,
        threadId: threadId ?? undefined,
        waitRoomSeconds: 8,
      });
      openUrl(res.viewerUrl);
      await qc.invalidateQueries({ queryKey: ['inspection-active', listingId] });
    } catch (e: any) {
      setErr(e?.message || t('inspections.joinFailed'));
    } finally {
      setBusy(false);
    }
  };

  const inviteCopy = async () => {
    if (!active) return;
    const inviteUrl = `${window.location.origin}/obhliadka/${active.id}`;
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: nastavíme do inputu? len ignorujeme — moderné prehliadače majú clipboard API
    }
  };

  const endInspection = async () => {
    if (!active) return;
    if (!window.confirm(t('inspections.endConfirm'))) return;
    setBusy(true);
    setErr(null);
    try {
      await inspectionsApi.end(active.id);
    } catch (e: any) {
      setErr(e?.message || t('inspections.endFailed'));
    } finally {
      setBusy(false);
    }
  };

  const grantConsent = async () => {
    if (!active) return;
    setBusy(true);
    setErr(null);
    try {
      await inspectionsApi.grantRecordingConsent(active.id);
    } catch (e: any) {
      setErr(e?.message || t('inspections.startFailed'));
    } finally {
      setBusy(false);
    }
  };

  const stateText = state
    ? `${t('inspections.state')}: ${t(`inspections.state_${inspectionStateLabel(state)}`)}`
    : null;
  const roomReady = active?.roomId ? t('inspections.roomReady') : null;

  return (
    <div
      className="flex flex-wrap items-center gap-2 border-b px-4 py-2 text-xs sm:px-5"
      style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}
    >
      <span
        className="rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.15em]"
        style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', color: GOLD }}
      >
        🎥 {t('inspections.title')}
      </span>

      {!active && canPublish && (
        <button
          type="button"
          disabled={busy}
          onClick={startInspection}
          className="rounded-lg px-3 py-1 text-[11px] font-semibold transition disabled:opacity-40"
          style={{ background: GOLD, color: '#090807' }}
        >
          {busy ? t('inspections.working') : t('inspections.start')}
        </button>
      )}

      {!active && !canPublish && (
        <span style={{ color: MUTED }}>{t('inspections.none')}</span>
      )}

      {active && state !== 'ended' && (
        <>
          {stateText && <span style={{ color: MUTED }}>{stateText}</span>}
          {roomReady && <span style={{ color: GOLD_BRIGHT }}>{roomReady}</span>}

          {active.ownerUserId && canPublish && (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={reopen}
                className="rounded-lg border px-3 py-1 text-[11px] transition disabled:opacity-40"
                style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
              >
                {busy ? t('inspections.working') : t('inspections.openPublisher')}
              </button>

              {!active.consentToRecord && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={grantConsent}
                  className="rounded-lg border px-3 py-1 text-[10px] transition disabled:opacity-40"
                  style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
                >
                  {t('inspections.consent')}
                </button>
              )}

              <button
                type="button"
                disabled={busy || copied}
                onClick={inviteCopy}
                className="rounded-lg border px-3 py-1 text-[11px] transition disabled:opacity-40"
                style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
              >
                {copied ? t('inspections.inviteCopied') : t('inspections.invite')}
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={endInspection}
                className="rounded-lg px-3 py-1 text-[11px] font-semibold transition disabled:opacity-40"
                style={{ background: DANGER, color: '#090807' }}
              >
                {t('inspections.end')}
              </button>
            </>
          )}

          {active && (canJoin || isViewer) && (
            <button
              type="button"
              disabled={busy}
              onClick={joinInspection}
              className="rounded-lg px-3 py-1 text-[11px] font-semibold transition disabled:opacity-40"
              style={{ background: GOLD, color: '#090807' }}
            >
              {busy ? t('inspections.working') : t('inspections.join')}
            </button>
          )}
        </>
      )}

      {active && state === 'ended' && (
        <span style={{ color: MUTED }}>{t('inspections.ended')}</span>
      )}

      {err && <span style={{ color: DANGER }}>{err}</span>}
    </div>
  );
};
