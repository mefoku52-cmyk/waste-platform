'use client';

import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const DANGER = '#f0bbb0';

type LiveState =
  | 'unavailable'
  | 'ready'
  | 'pending'
  | 'starting'
  | 'room_created'
  | 'live'
  | 'requesting'
  | 'accepted'
  | 'connecting'
  | 'connected'
  | 'interrupted'
  | 'ended'
  | 'error';

/**
 * Presentational prototype for the LIVE streaming section.
 * No API calls — state is driven by props/callbacks in the real integration.
 */
export function LiveStreamingPrototype({
  state,
  busy = false,
  error = null,
  canPublish,
  canRequest,
  canJoin,
  pendingRequest,
  isViewer,
  onStart,
  onRequest,
  onJoin,
  onOpenPublisher,
  onEnd,
  onConsent,
  onCopyInvite,
}: {
  state: LiveState;
  busy?: boolean;
  error?: string | null;
  canPublish: boolean;
  canRequest: boolean;
  canJoin: boolean;
  pendingRequest: boolean;
  isViewer: boolean;
  onStart?: () => void;
  onRequest?: () => void;
  onJoin?: () => void;
  onOpenPublisher?: () => void;
  onEnd?: () => void;
  onConsent?: () => void;
  onCopyInvite?: () => void;
}) {
  const { t } = useT();

  const run = (fn?: () => void) => {
    if (!fn || busy) return;
    fn();
  };

  const badgeColor =
    state === 'live' || state === 'connected'
      ? '#c45c4a'
      : state === 'error'
        ? '#c45c4a'
        : state === 'interrupted'
          ? '#e8d48b'
          : GOLD;

  return (
    <section className="cmep-panel mt-6 rounded-2xl p-5 sm:p-7">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className="rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.15em]"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', color: GOLD }}
        >
          🎥 {t('inspections.title')}
        </span>
        <span
          className="rounded-full px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] font-semibold"
          style={{ background: badgeColor, color: '#090807' }}
        >
          {state === 'live' || state === 'connected' ? 'LIVE' : state}
        </span>
      </div>

      {state === 'unavailable' && (
        <p className="mt-3 text-sm" style={{ color: MUTED }}>
          Živá prezentácia nie je nakonfigurovaná.
        </p>
      )}

      {state === 'ready' && canPublish && (
        <button
          type="button"
          disabled={busy}
          onClick={() => run(onStart)}
          className="mt-4 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
          style={{ background: GOLD, color: '#090807' }}
        >
          {busy ? t('inspections.working') : 'Spustiť LIVE prezentáciu'}
        </button>
      )}

      {state === 'ready' && canRequest && (
        <button
          type="button"
          disabled={busy}
          onClick={() => run(onRequest)}
          className="mt-4 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
          style={{ background: GOLD, color: '#090807' }}
        >
          {busy ? t('inspections.working') : 'Požiadať o pripojenie k LIVE'}
        </button>
      )}

      {pendingRequest && !canPublish && (
        <span
          className="mt-4 inline-block rounded-lg px-3 py-1 text-[11px] font-semibold opacity-60"
          style={{ background: GOLD, color: '#090807' }}
        >
          Žiadosť odoslaná
        </span>
      )}

      {state === 'starting' && (
        <p className="mt-4 text-sm" style={{ color: MUTED }}>
          Vytváram miestnosť…
        </p>
      )}

      {(state === 'live' || state === 'room_created') && canPublish && (
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => run(onOpenPublisher)}
            className="rounded-lg border px-3 py-1.5 text-xs transition disabled:opacity-40"
            style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
          >
            Otvoriť publisher
          </button>
          {onConsent && (
            <button
              type="button"
              disabled={busy}
              onClick={() => run(onConsent)}
              className="rounded-lg border px-3 py-1.5 text-xs transition disabled:opacity-40"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
            >
              Súhlas s nahrávaním
            </button>
          )}
          {onCopyInvite && (
            <button
              type="button"
              disabled={busy}
              onClick={() => run(onCopyInvite)}
              className="rounded-lg border px-3 py-1.5 text-xs transition disabled:opacity-40"
              style={{ borderColor: 'color-mix(in srgb, #c9a84c 40%, transparent)', color: GOLD_BRIGHT }}
            >
              Kopírovať pozvánku
            </button>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={() => run(onEnd)}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold transition disabled:opacity-40"
            style={{ background: DANGER, color: '#090807' }}
          >
            Ukončiť vysielanie
          </button>
        </div>
      )}

      {canJoin && (state === 'live' || state === 'room_created' || state === 'accepted') && (
        <button
          type="button"
          disabled={busy}
          onClick={() => run(onJoin)}
          className="mt-4 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
          style={{ background: GOLD, color: '#090807' }}
        >
          {busy ? t('inspections.working') : 'Pripojiť sa k LIVE'}
        </button>
      )}

      {(state === 'requesting' || state === 'connecting') && (
        <p className="mt-4 text-sm" style={{ color: MUTED }}>
          {state === 'requesting' ? 'Čaká na schválenie vlastníkom…' : 'Pripájam sa…'}
        </p>
      )}

      {state === 'interrupted' && (
        <p className="mt-4 text-sm" style={{ color: GOLD_BRIGHT }}>
          Spojenie prerušené — skúste znova.
        </p>
      )}

      {state === 'ended' && (
        <p className="mt-4 text-sm" style={{ color: MUTED }}>
          Vysielanie ukončené.
        </p>
      )}

      {state === 'error' && (
        <p className="mt-4 text-sm" style={{ color: DANGER }}>
          Chyba pri streamovaní.
        </p>
      )}

      {error && <span className="mt-4 block text-sm" style={{ color: DANGER }}>{error}</span>}
    </section>
  );
}
