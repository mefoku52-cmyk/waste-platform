'use client';

import { useEffect, useRef, useState } from 'react';

import { http } from '@/lib/api/http';
import {
  buildSttUrl,
  createUtteranceTracker,
  KEEPALIVE_IDLE_MS,
  KEEPALIVE_INTERVAL_MS,
  KEEPALIVE_MESSAGE,
  needsKeepAlive,
  parseSttMessage,
  type UtteranceTracker,
} from '@/lib/ai-agent/voice-stt';

type TokenResponse = { access_token: string; expires_in: number };

export type LiveVoiceStatus =
  | 'idle'
  | 'requesting'
  | 'connecting'
  | 'live'
  | 'thinking'
  | 'stopping'
  | 'reconnecting'
  | 'error';

const MAX_RECONNECTS = 2;
const CONNECT_TIMEOUT_MS = 10_000;
/** Po `CloseStream` čakáme na posledné `is_final` výsledky, než spojenie zavrieme. */
const FINAL_FLUSH_WAIT_MS = 1_200;
const RECONNECT_BASE_DELAY_MS = 600;

/**
 * AudioWorklet, ktorý mení mikrofón na surové PCM16 mono.
 * Deepgram `linear16` potrebuje bajty PCM, nie WebM/Opus kontajner.
 */
const PCM_WORKLET_SOURCE = `
class CmepPcmCapture extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const channel = input[0];
    if (!channel || channel.length === 0) return true;
    const pcm = new Int16Array(channel.length);
    for (let i = 0; i < channel.length; i += 1) {
      const sample = Math.max(-1, Math.min(1, channel[i]));
      pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    this.port.postMessage(pcm.buffer, [pcm.buffer]);
    return true;
  }
}
registerProcessor('cmep-pcm-capture', CmepPcmCapture);
`;

type Props = {
  /** Priebežný (ešte nefinálny) prepis — pre dočasný bubble v chate. */
  onInterim?: (text: string) => void;
  /** Dokončená výpoveď — volá sa práve raz a posiela sa do CMEP chatu. */
  onFinalTranscript?: (text: string) => void | Promise<void>;
  onError?: (message: string) => void;
  disabled?: boolean;
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function micErrorMessage(err: unknown): string {
  const name = err instanceof DOMException ? err.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError') {
    return 'Prístup k mikrofónu bol zamietnutý. Povoľ ho v prehliadači a skús znova.';
  }
  if (name === 'NotFoundError' || name === 'OverconstrainedError') {
    return 'Nenašiel sa žiadny mikrofón.';
  }
  if (name === 'NotReadableError' || name === 'AbortError') {
    return 'Mikrofón je obsadený inou aplikáciou.';
  }
  return err instanceof Error && err.message ? err.message : 'Mikrofón sa nepodarilo spustiť.';
}

function closeMessage(event: CloseEvent): string {
  const reason = (event.reason || '').trim();
  if (event.code === 1008) {
    return reason
      ? `Prepis reči odmietol spojenie: ${reason}`
      : 'Prepis reči odmietol spojenie (neplatný token alebo model).';
  }
  if (event.code === 1006) return 'Spojenie s prepisom reči sa prerušilo.';
  if (reason) return `Prepis reči sa ukončil (${event.code}): ${reason}`;
  return `Prepis reči sa ukončil (kód ${event.code}).`;
}

export function VoiceLiveButton({ onInterim, onFinalTranscript, onError, disabled }: Props) {
  const [status, setStatus] = useState<LiveVoiceStatus>('idle');
  const [lastError, setLastError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const nodeRef = useRef<AudioNode | null>(null);
  const sinkRef = useRef<GainNode | null>(null);
  const trackerRef = useRef<UtteranceTracker | null>(null);
  const mutedRef = useRef(false);
  const inTurnRef = useRef(false);
  const stopRequestedRef = useRef(false);
  const reconnectsRef = useRef(0);
  const mountedRef = useRef(true);
  const lastActivityRef = useRef(0);
  const keepAliveTimerRef = useRef<number | null>(null);

  const callbacksRef = useRef({ onInterim, onFinalTranscript, onError });
  useEffect(() => {
    callbacksRef.current = { onInterim, onFinalTranscript, onError };
  }, [onInterim, onFinalTranscript, onError]);

  function setSafeStatus(next: LiveVoiceStatus) {
    if (mountedRef.current) setStatus(next);
  }

  function getTracker(): UtteranceTracker {
    if (!trackerRef.current) trackerRef.current = createUtteranceTracker();
    return trackerRef.current;
  }

  function stopKeepAlive() {
    if (keepAliveTimerRef.current !== null) {
      window.clearInterval(keepAliveTimerRef.current);
      keepAliveTimerRef.current = null;
    }
    lastActivityRef.current = 0;
  }

  /**
   * Drží Deepgram socket nažive, keď nejde zvuk (počas odpovede chatu je mikrofón
   * stlmený a ticho >10 s by spojenie zabilo → ďalšia veta by sa stratila).
   */
  function startKeepAlive() {
    stopKeepAlive();
    lastActivityRef.current = Date.now();
    keepAliveTimerRef.current = window.setInterval(() => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      const now = Date.now();
      if (!needsKeepAlive(lastActivityRef.current, now, KEEPALIVE_IDLE_MS)) return;
      try {
        ws.send(KEEPALIVE_MESSAGE);
        lastActivityRef.current = now;
      } catch {
        /* spojenie medzitým zmizlo — rieši onclose */
      }
    }, KEEPALIVE_INTERVAL_MS);
  }

  /** Uvoľní všetko: WS (bez spätných volaní), audio graf, MediaStream tracky. */
  function releaseAll() {
    stopKeepAlive();
    const ws = wsRef.current;
    if (ws) {
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      try {
        ws.close();
      } catch {
        /* noop */
      }
    }
    wsRef.current = null;

    try {
      sourceRef.current?.disconnect();
    } catch {
      /* noop */
    }
    try {
      nodeRef.current?.disconnect();
    } catch {
      /* noop */
    }
    try {
      sinkRef.current?.disconnect();
    } catch {
      /* noop */
    }
    sourceRef.current = null;
    nodeRef.current = null;
    sinkRef.current = null;

    mediaRef.current?.getTracks().forEach((track) => track.stop());
    mediaRef.current = null;

    const ctx = ctxRef.current;
    ctxRef.current = null;
    if (ctx && ctx.state !== 'closed') {
      void ctx.close().catch(() => {
        /* noop */
      });
    }

    trackerRef.current?.reset();
    mutedRef.current = false;
  }

  function fail(message: string) {
    releaseAll();
    stopRequestedRef.current = false;
    reconnectsRef.current = 0;
    setSafeStatus('error');
    if (mountedRef.current) setLastError(message);
    callbacksRef.current.onError?.(message);
  }

  async function teardown() {
    releaseAll();
    stopRequestedRef.current = false;
    reconnectsRef.current = 0;
    setSafeStatus('idle');
  }

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      releaseAll();
    };
    // releaseAll pracuje len s refmi — prvá inštancia je bezpečná aj pri unmounte.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Mikrofón → PCM16 → `ws.send()`. */
  async function startCapture(): Promise<void> {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      throw new Error('Tento prehliadač nepodporuje prístup k mikrofónu.');
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
    } catch (err) {
      throw new Error(micErrorMessage(err));
    }
    mediaRef.current = stream;

    const Ctx =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) throw new Error('Tento prehliadač nepodporuje spracovanie zvuku.');

    let ctx: AudioContext;
    try {
      // 16 kHz je priamo to, čo Deepgram očakáva; prehliadač si mikrofón resampluje sám.
      ctx = new Ctx({ sampleRate: 16000 });
    } catch {
      ctx = new Ctx();
    }
    ctxRef.current = ctx;
    if (ctx.state === 'suspended') await ctx.resume();
    if (ctx.state !== 'running') {
      // Bez bežiaceho AudioContextu sa PCM nikdy neodošle — nikdy ticho nezlyhaj.
      throw new Error('Prehliadač zablokoval spracovanie zvuku. Klikni na Live ešte raz.');
    }

    const source = ctx.createMediaStreamSource(stream);
    sourceRef.current = source;

    // Node musí byť pripojený k destination, aby ho prehliadač ťahal — ale potichu.
    const sink = ctx.createGain();
    sink.gain.value = 0;
    sink.connect(ctx.destination);
    sinkRef.current = sink;

    const sendChunk = (buffer: ArrayBuffer) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      if (mutedRef.current) return;
      try {
        ws.send(buffer);
        lastActivityRef.current = Date.now();
      } catch {
        /* spojenie medzitým zmizlo — rieši onclose */
      }
    };

    if (ctx.audioWorklet) {
      try {
        const url = URL.createObjectURL(
          new Blob([PCM_WORKLET_SOURCE], { type: 'application/javascript' }),
        );
        try {
          await ctx.audioWorklet.addModule(url);
        } finally {
          URL.revokeObjectURL(url);
        }
        const node = new AudioWorkletNode(ctx, 'cmep-pcm-capture');
        node.port.onmessage = (event: MessageEvent<ArrayBuffer>) => sendChunk(event.data);
        source.connect(node);
        node.connect(sink);
        nodeRef.current = node;
        return;
      } catch {
        // Safari / staršie jadrá — fallback nižšie.
      }
    }

    // Fallback: ScriptProcessorNode (deprecated, ale funguje všade).
    const node = ctx.createScriptProcessor(4096, 1, 1);
    node.onaudioprocess = (event) => {
      const channel = event.inputBuffer.getChannelData(0);
      const pcm = new Int16Array(channel.length);
      for (let i = 0; i < channel.length; i += 1) {
        const sample = Math.max(-1, Math.min(1, channel[i]));
        pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      }
      sendChunk(pcm.buffer);
    };
    source.connect(node);
    node.connect(sink);
    nodeRef.current = node;
  }

  /** Krátkodobý token z nášho backendu + WS handshake (token ide ako subprotocol). */
  async function openSocket(): Promise<WebSocket> {
    const token = await http.post<TokenResponse>('/agent-platform/voice/token', {});
    if (!token?.access_token) {
      throw new Error('Hlasový asistent nevrátil prístupový token.');
    }
    const url = buildSttUrl(ctxRef.current?.sampleRate ?? 16000);

    return await new Promise<WebSocket>((resolve, reject) => {
      let settled = false;
      const ws = new WebSocket(url, ['token', token.access_token]);
      ws.binaryType = 'arraybuffer';

      const timer = window.setTimeout(() => {
        if (settled) return;
        settled = true;
        try {
          ws.close();
        } catch {
          /* noop */
        }
        reject(new Error('Prepis reči sa nepodarilo pripojiť (timeout).'));
      }, CONNECT_TIMEOUT_MS);

      ws.onopen = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timer);
        resolve(ws);
      };
      ws.onerror = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timer);
        reject(new Error('Prepis reči sa nepodarilo pripojiť.'));
      };
      ws.onclose = (event) => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timer);
        reject(new Error(closeMessage(event)));
      };
    });
  }

  /** Jedna dokončená výpoveď → CMEP chat. Počas odpovede mikrofón neposiela (proti ozvene). */
  async function runTurn(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    // Poistka at-most-once: kým beží odpoveď, ďalšie finálne fragmenty sa neposielajú.
    if (inTurnRef.current) return;
    inTurnRef.current = true;
    mutedRef.current = true;
    setSafeStatus('thinking');
    callbacksRef.current.onInterim?.('');
    try {
      await callbacksRef.current.onFinalTranscript?.(trimmed);
    } catch (err) {
      callbacksRef.current.onError?.(
        err instanceof Error ? err.message : 'Hlasová správa sa neodoslala.',
      );
    } finally {
      inTurnRef.current = false;
      mutedRef.current = false;
      if (stopRequestedRef.current) {
        await teardown();
      } else if (wsRef.current?.readyState === WebSocket.OPEN) {
        // „live" tvrdíme len vtedy, keď spojenie naozaj existuje.
        setSafeStatus('live');
      }
    }
  }

  function handleSttMessage(raw: string) {
    const event = parseSttMessage(raw);
    if (event.kind === 'error') {
      fail(event.message);
      return;
    }
    const out = getTracker().push(event);
    if (!out) return;
    if ('final' in out) {
      void runTurn(out.final);
      return;
    }
    callbacksRef.current.onInterim?.(out.interim);
  }

  async function handleClose(event: CloseEvent) {
    stopKeepAlive();
    wsRef.current = null;
    if (stopRequestedRef.current) {
      await teardown();
      return;
    }
    if (reconnectsRef.current < MAX_RECONNECTS) {
      reconnectsRef.current += 1;
      // Fragmenty z mŕtveho socketu nesmie nové spojenie doplniť do jednej vety.
      getTracker().reset();
      setSafeStatus('reconnecting');
      await sleep(RECONNECT_BASE_DELAY_MS * reconnectsRef.current);
      if (stopRequestedRef.current) {
        await teardown();
        return;
      }
      try {
        const ws = await openSocket();
        wsRef.current = ws;
        bindSocket(ws);
        // reconnect counter sa NERESETUJE — max MAX_RECONNECTS pokusov na jedno zapnutie
        setSafeStatus('live');
        return;
      } catch {
        // Skús ešte raz (reconnectsRef sa už zvýšil), inak zlyhaj nižšie.
      }
      await handleClose(event);
      return;
    }
    fail(closeMessage(event));
  }

  function bindSocket(ws: WebSocket) {
    startKeepAlive();
    ws.onmessage = (event) => {
      // STT posiela len JSON; binárne rámce ignorujeme.
      if (typeof event.data !== 'string') return;
      handleSttMessage(event.data);
    };
    ws.onerror = () => {
      // Dôvod dodá onclose (code/reason) — tam sa rozhodne o reconnecte.
    };
    ws.onclose = (event) => {
      void handleClose(event);
    };
  }

  async function start() {
    setLastError(null);
    stopRequestedRef.current = false;
    reconnectsRef.current = 0;
    getTracker().reset();
    setSafeStatus('requesting');
    try {
      await startCapture();
      setSafeStatus('connecting');
      const ws = await openSocket();
      wsRef.current = ws;
      bindSocket(ws);
      setSafeStatus('live');
    } catch (err) {
      fail(err instanceof Error ? err.message : 'Hlasový režim sa nepodarilo spustiť.');
    }
  }

  async function stop() {
    stopRequestedRef.current = true;
    setSafeStatus('stopping');
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      // CloseStream vyžiada posledné finálne výsledky, kým spojenie nezavrieme.
      try {
        ws.send(JSON.stringify({ type: 'CloseStream' }));
      } catch {
        /* noop */
      }
      await sleep(FINAL_FLUSH_WAIT_MS);
    }
    await teardown();
  }

  const active = status !== 'idle' && status !== 'error';
  const pending = status === 'requesting' || status === 'connecting';
  const label =
    status === 'live'
      ? '■ Live'
      : status === 'thinking' || status === 'stopping'
        ? '… Live'
        : status === 'reconnecting'
          ? '↻ Live'
          : '🎧 Live';
  const title =
    status === 'requesting'
      ? 'Pripájam mikrofón…'
      : status === 'connecting'
        ? 'Pripájam prepis reči…'
        : status === 'live'
          ? 'Hovor — prepis ide do CMEP chatu'
          : status === 'thinking'
            ? 'Čakám na odpoveď CMEP…'
            : status === 'stopping'
              ? 'Ukončujem a dopisujem poslednú vetu…'
              : status === 'reconnecting'
                ? 'Obnovujem spojenie…'
                : status === 'error'
                  ? (lastError ?? 'Hlas zlyhal — klikni pre nový pokus')
                  : 'Hlasový režim (Live)';

  return (
    <button
      type="button"
      onClick={() => void (active ? stop() : start())}
      disabled={pending || (disabled === true && !active)}
      aria-label={active ? 'Ukončiť hlasový režim' : 'Začať hlasový režim'}
      aria-pressed={active}
      title={title}
      className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40"
      style={{
        borderColor: active ? '#ef4444' : 'rgba(201,168,76,0.35)',
        color: active ? '#ef4444' : '#c9a84c',
      }}
    >
      {label}
    </button>
  );
}
