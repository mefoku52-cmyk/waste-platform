'use client';

import { useEffect, useRef, useState } from 'react';

import { http } from '@/lib/api/http';

type TokenResponse = { access_token: string; expires_in: number };

type Props = {
  onTranscript?: (role: 'user' | 'ai', text: string) => void;
  onError?: (message: string) => void;
};

// Deepgram Voice Agent WS endpoint (nastavený s Groq LLM + TTS Aura-2).
// Konfigurácia sa posiela v Settings správe hneď po otvorení WS.
const DG_WS_URL = 'wss://agent.deepgram.com/v1/agent/converse';

export function VoiceLiveButton({ onTranscript, onError }: Props) {
  const [active, setActive] = useState(false);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'live' | 'error'>('idle');
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const playbackQueueRef = useRef<AudioBufferSourceNode[]>([]);

  useEffect(() => {
    return () => {
      // Cleanup pri unmount
      try { wsRef.current?.close(); } catch { /* noop */ }
      mediaRef.current?.getTracks().forEach((t) => t.stop());
      try { audioCtxRef.current?.close(); } catch { /* noop */ }
    };
  }, []);

  async function start() {
    setStatus('connecting');
    try {
      // 1. Získaj krátkodobý Deepgram token z nášho backendu
      const tok = await http.post<TokenResponse>('/agent-platform/voice/token', {});
      if (!tok?.access_token) throw new Error('Token chýba');

      // 2. Mikrofón
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRef.current = stream;

      // 3. AudioContext pre prehrávanie odpovedí
      const ctx = new (window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      audioCtxRef.current = ctx;

      // 4. WebSocket na Deepgram
      const ws = new WebSocket(`${DG_WS_URL}?model=nova-3&language=sk`, [
        'token',
        tok.access_token,
      ]);
      wsRef.current = ws;
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        // Settings — Voice Agent konfigurácia
        // audio: linear16 @ 16kHz (Deepgram preferuje pre STT/TTS)
        ws.send(
          JSON.stringify({
            type: 'Settings',
            audio: {
              input: { encoding: 'linear16', sample_rate: 16000 },
              output: { encoding: 'linear16', sample_rate: 24000, container: 'none' },
            },
            agent: {
              language: 'sk',
              listen: { model: 'nova-3' },
              think: {
                provider: { type: 'groq', model: 'openai/gpt-oss-120b' },
                prompt:
                  'Si hlasový asistent pre CMEP (trc-cmep.sk) — slovenský B2B marketplace s obehovými materiálmi. ' +
                  'Odpovedaj po slovensky, stručne, priateľsky. Pomáhaj s ponukami, firmami, materiálmi.',
              },
              speak: { model: 'aura-2' },
            },
          }),
        );
        setStatus('live');
        setActive(true);
      };

      ws.onmessage = (ev) => {
        if (typeof ev.data === 'string') {
          try {
            const msg = JSON.parse(ev.data);
            if (msg.type === 'ConversationText' && msg.role && msg.content) {
              onTranscript?.(msg.role === 'user' ? 'user' : 'ai', msg.content);
            }
          } catch { /* ignore */ }
          return;
        }
        // Binárne audio → prehraj
        if (ev.data instanceof ArrayBuffer && audioCtxRef.current) {
          const pcm = new Int16Array(ev.data);
          const float = new Float32Array(pcm.length);
          for (let i = 0; i < pcm.length; i++) float[i] = pcm[i] / 32768;
          const buf = audioCtxRef.current.createBuffer(1, float.length, 24000);
          buf.copyToChannel(float, 0);
          const src = audioCtxRef.current.createBufferSource();
          src.buffer = buf;
          src.connect(audioCtxRef.current.destination);
          src.start();
          playbackQueueRef.current.push(src);
          src.onended = () => {
            playbackQueueRef.current = playbackQueueRef.current.filter((s) => s !== src);
          };
        }
      };

      ws.onerror = () => {
        setStatus('error');
        onError?.('Spojenie s hlasovým asistentom zlyhalo.');
      };

      ws.onclose = () => {
        setActive(false);
        setStatus('idle');
      };

      // 5. Streamuj mikrofón do WS
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      recorderRef.current = recorder;
      recorder.ondataavailable = async (e) => {
        if (!e.data.size) return;
        if (ws.readyState !== WebSocket.OPEN) return;
        // Deepgram očakáva linear16 @ 16kHz. WebM opus nepôjde priamo.
        // Pre prototyp posielame raw — Deepgram to odmietne, ale vieme debugovať.
        const arr = await e.data.arrayBuffer();
        ws.send(arr);
      };
      recorder.start(250);
    } catch (err) {
      setStatus('error');
      onError?.(err instanceof Error ? err.message : 'Chyba pri spustení.');
    }
  }

  function stop() {
    try { recorderRef.current?.stop(); } catch { /* noop */ }
    mediaRef.current?.getTracks().forEach((t) => t.stop());
    try { wsRef.current?.close(); } catch { /* noop */ }
    setActive(false);
    setStatus('idle');
  }

  return (
    <button
      type="button"
      onClick={() => (active ? stop() : void start())}
      aria-label={active ? 'Ukončiť hlasový hovor' : 'Začať hlasový hovor'}
      className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40"
      style={{
        borderColor: active ? '#ef4444' : 'rgba(201,168,76,0.35)',
        color: active ? '#ef4444' : '#c9a84c',
      }}
      title={status === 'connecting' ? 'Pripájam…' : status === 'live' ? 'Naživo' : 'Hlasový hovor'}
    >
      {active ? '■ Live' : '🎧 Live'}
    </button>
  );
}
