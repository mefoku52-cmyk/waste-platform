'use client';

import { useCallback, useState } from 'react';
import { useT } from '@/lib/i18n/context';
import { useQueryClient } from '@tanstack/react-query';
import { inspectionsApi } from '../api';
import { chatApi } from '../../chat/api';
import { useActiveInspection } from '../hooks/use-inspections-queries';
import { LiveStreamingPrototype } from './live-streaming-prototype';

const STREAM_REQUEST_MARKER = '[STREAM_REQUEST]';
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

  const active = (data as any)?.inspection ?? null;
  const canPublish = Boolean((data as any)?.canPublish);
  const canJoin = Boolean((data as any)?.canJoin);
  const isViewer = Boolean((data as any)?.isViewer);
  const canRequest = Boolean((data as any)?.canRequest);
  const pendingRequest = Boolean((data as any)?.pendingRequest);
  const requestThreadId = (data as any)?.requestThreadId ?? threadId ?? null;
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

  if (!listingId) return null;

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

  const requestStream = async () => {
    const tid = requestThreadId;
    if (!tid) {
      setErr(t('inspections.startFailed'));
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await chatApi.sendMessage(tid, STREAM_REQUEST_MARKER);
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
      await qc.invalidateQueries({ queryKey: ['inspection-active', listingId] });
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
      await qc.invalidateQueries({ queryKey: ['inspection-active', listingId] });
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

  const liveState = (() => {
    if (!active) {
      if (pendingRequest && !canPublish) return 'pending' as const;
      return 'ready' as const;
    }
    switch (state) {
      case 'created':
        return active.roomId ? ('room_created' as const) : ('starting' as const);
      case 'room_created':
        return 'live' as const;
      case 'requested':
        return isViewer ? ('requesting' as const) : ('live' as const);
      case 'accepted':
        return isViewer ? ('connecting' as const) : ('live' as const);
      case 'live':
        return isViewer ? ('connected' as const) : ('live' as const);
      case 'ended':
        return 'ended' as const;
      default:
        return 'error' as const;
    }
  })();

  return (
    <LiveStreamingPrototype
      state={liveState}
      busy={busy}
      error={err}
      canPublish={canPublish}
      canRequest={canRequest}
      canJoin={canJoin}
      pendingRequest={pendingRequest}
      isViewer={isViewer}
      onStart={canPublish && !active ? startInspection : undefined}
      onRequest={!canPublish && canRequest ? requestStream : undefined}
      onJoin={active && (canJoin || isViewer) ? joinInspection : undefined}
      onOpenPublisher={active && canPublish ? reopen : undefined}
      onEnd={active && canPublish ? endInspection : undefined}
      onConsent={active && canPublish && !active.consentToRecord ? grantConsent : undefined}
      onCopyInvite={active && canPublish ? inviteCopy : undefined}
    />
  );
};
