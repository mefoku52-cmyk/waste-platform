'use client';

import { useEffect, useRef, useState } from 'react';
import { config } from '@/lib/config';
import { tokenStore } from '@/lib/auth/token-store';
import { useRouter } from 'next/navigation';

import { http } from '@/lib/api/http';
import { useMyTier } from '@/features/companies/hooks/use-my-tier';
import { aiSessionStore } from '../lib/session-store';
import { personaStore, type Persona } from '../lib/persona-store';
import { PersonaPicker } from './persona-picker';
import { VoiceLiveButton } from './voice-live-button';
import { AiUpgradePanel } from './ai-upgrade-panel';
import { useT } from '@/lib/i18n/context';
import { cmepAI } from '@/lib/ai-agent/dispatcher';
import { getPageContext } from '@/lib/ai-agent/page-context';

type Msg = { role: 'user' | 'ai'; text: string; audioBase64?: string };

// Browser SpeechSynthesis — hlas zariadenia (SK/EN/DE/...)
function speakText(text: string, lang?: string): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang || 'sk-SK';
    u.rate = 1.0;
    u.pitch = 1.0;
    window.speechSynthesis.speak(u);
  } catch {
    /* noop */
  }
}


type ClientAction = { name: string; args: Record<string, unknown> };

type ChatResponse = {
  status: string;
  reply: string | null;
  source: string;
  session_id?: string;
  tool_calls?: unknown[];
  client_actions?: ClientAction[];
  audio_base64?: string | null;
};

type Props = {
  listingId?: string;
  listingTitle?: string;
};

export function AiChatWidget({ listingId, listingTitle }: Props) {
  const { t } = useT();
  const { tier, isLoading: tierLoading, companyId } = useMyTier();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [persona, setPersona] = useState<Persona>('bystry');
  const [toast, setToast] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    setSessionId(aiSessionStore.getSessionId());
    setPersona(personaStore.get());
  }, []);

  // Client-side action handlers registrácia (navigate, show_toast).
  useEffect(() => {
    const unregNavigate = cmepAI.register('navigate', (args) => {
      const url = typeof args.url === 'string' ? args.url : '';
      // Interné relatívne odkazy len — žiadne externé URL ani protocol-relative.
      if (!url.startsWith('/') || url.startsWith('//')) return;
      router.push(url);
    });
    const unregToast = cmepAI.register('show_toast', (args) => {
      const message = typeof args.message === 'string' ? args.message.trim() : '';
      if (!message) return;
      setToast(message);
    });
    return () => {
      unregNavigate();
      unregToast();
    };
  }, [router]);

  // Toast auto-dismiss.
  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([
        {
          role: 'ai',
          text: listingTitle
            ? `Ahoj. Pýtaj sa ma na ponuku "${listingTitle}". S čím pomôžem?`
            : 'Ahoj. S čím ti pomôžem?',
        },
      ]);
    }
  }, [open, listingTitle, messages.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  function startNewConversation() {
    const fresh = aiSessionStore.resetSession();
    setSessionId(fresh);
    setMessages([
      {
        role: 'ai',
        text: 'Nová konverzácia. S čím ti pomôžem?',
      },
    ]);
  }

  async function send(textOverride?: string, voiceResponse = false, voiceLanguage?: string) {
    const text = (textOverride ?? input).trim();
    if (!text || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    setBusy(true);
    try {
      const pageCtx = getPageContext();
      const res = await http.post<ChatResponse>(
        '/agent-platform/chat',
        {
          message: text,
          session_id: sessionId || undefined,
          listing_id: listingId || undefined,
          persona: persona || undefined,
          page_context: pageCtx,
          voice_response: voiceResponse,
          voice_language: voiceLanguage,
        },
        { timeoutMs: 60000 },
      );
      if (res?.session_id && res.session_id !== sessionId) {
        setSessionId(res.session_id);
      }

      // Comet-style: vykonaj client actions lokálne
      if (Array.isArray(res?.client_actions) && res.client_actions.length > 0) {
        const notes: string[] = [];
        for (const action of res.client_actions) {
          // Špeciálne: open_* akcie spracuje router priamo
          const nm = action.name;
          const ar = action.args || {};
          if (nm === 'open_listing') {
            router.push(`/dashboard/listings/${String(ar.listing_id || '')}`);
            notes.push(`✓ Otvoril som ponuku`);
            continue;
          }
          if (nm === 'open_company') {
            router.push(`/dashboard/companies/${String(ar.company_id || '')}`);
            notes.push(`✓ Otvoril som firmu`);
            continue;
          }
          if (nm === 'open_new_listing') {
            router.push('/dashboard/listings/new');
            notes.push(`✓ Otvoril som formulár novej ponuky`);
            continue;
          }
          if (nm === 'open_listings_list') {
            router.push('/dashboard/listings');
            notes.push(`✓ Otvoril som zoznam ponúk`);
            continue;
          }
          if (nm === 'open_companies') {
            router.push('/dashboard/companies');
            notes.push(`✓ Otvoril som zoznam firiem`);
            continue;
          }
          if (nm === 'open_dashboard') {
            router.push('/dashboard');
            notes.push(`✓ Otvoril som dashboard`);
            continue;
          }
          if (nm === 'open_inquiries') {
            router.push('/dashboard/inquiries');
            notes.push(`✓ Otvoril som dopyty`);
            continue;
          }

          const ev = await cmepAI.dispatch(nm, ar);
          if (ev.status === 'ok') {
            if (action.name === 'fill_form_field') {
              const f = String(action.args?.field || '');
              const v = action.args?.value;
              notes.push(`✓ Vyplnil som ${f}: ${String(v)}`);
            } else if (action.name === 'navigate') {
              notes.push(`✓ Presmeroval som ťa na ${String(action.args?.url || '')}`);
            } else if (action.name === 'highlight_field') {
              notes.push(`✓ Zvýraznil som pole ${String(action.args?.field || '')}`);
            }
            // show_toast sa zobrazuje ako plávajúci toast (viď nižšie),
            // preto sa nepridáva aj ako textová poznámka v chate.
          }
        }

        if (notes.length > 0) {
          setMessages((m) => [
            ...m,
            { role: 'ai', text: res.reply as string || '', audioBase64: res.audio_base64 || undefined },
            { role: 'ai', text: notes.join('\n') },
          ]);
        } else if (res?.reply) {
          setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);
        }
      } else if (res?.status === 'ok' && res.reply) {
        if (voiceResponse) speakText(res.reply as string, voiceLanguage);
        setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);
      } else if (!res?.reply) {
        setMessages((m) => [
          ...m,
          {
            role: 'ai',
            text: 'Nepodarilo sa mi odpovedať, skús to znova.',
          },
        ]);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Chyba spojenia';
      setMessages((m) => [...m, { role: 'ai', text: `Chyba: ${msg}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function toggleVoiceRecording() {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop();
      return;
    }
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessages((m) => [...m, { role: 'ai', text: 'Tento prehliadač nepodporuje nahrávanie hlasu.' }]);
      return;
    }

    let stream: MediaStream | undefined;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferred = 'audio/webm;codecs=opus';
      const mimeType = MediaRecorder.isTypeSupported(preferred) ? preferred : undefined;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream?.getTracks().forEach((track) => track.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        void (async () => {
          if (!blob.size) return;
          setTranscribing(true);
          try {
            const token = tokenStore.getToken();
            if (!token) throw new Error('Prihlásenie vypršalo. Prihlás sa znova.');
            const form = new FormData();
            form.append('audio', blob, 'recording.webm');
            const response = await fetch(`${config.apiBaseUrl}/agent-platform/voice/transcribe`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              body: form,
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data.detail || 'Prepis hlasu sa nepodaril.');
            if (!data.text) throw new Error('V nahrávke sa nenašla reč.');
            setInput(data.text);
            await send(data.text, true, data.language || undefined);
          } catch (error: unknown) {
            const message = error instanceof Error ? error.message : 'Prepis hlasu sa nepodaril.';
            setMessages((m) => [...m, { role: 'ai', text: `Chyba: ${message}` }]);
          } finally {
            setTranscribing(false);
          }
        })();
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (error: unknown) {
      stream?.getTracks().forEach((track) => track.stop());
      const message = error instanceof Error ? error.message : 'Mikrofón sa nepodarilo spustiť.';
      setMessages((m) => [...m, { role: 'ai', text: `Mikrofón: ${message}` }]);
    }
  }

  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  if (tierLoading) {
    return null;
  }
  if (tier === 'free' || tier === 'unknown') {
    return <AiUpgradePanel reason={tier} companyId={companyId} />;
  }

  return (
    <>
      {!open && (
        <button
          type="button"
          onClick={() => { setOpen(true); setMinimized(false); }}
          aria-label={t('chatWidget.ariaOpen')}
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-2xl transition hover:scale-105"
          style={{ background: '#c9a84c', color: '#0b0b0b' }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {open && (
        <div
          className="fixed bottom-6 right-6 z-50 flex h-[440px] w-[330px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border shadow-2xl"
          style={{ borderColor: 'rgba(201,168,76,0.35)', background: '#0b0b0b' }}
        >
          <div
            className="flex items-center justify-between border-b px-4 py-3"
            style={{ borderColor: 'rgba(201,168,76,0.25)' }}
          >
            <div>
              <p
                className="text-[10px] font-semibold uppercase tracking-[0.22em]"
                style={{ color: '#c9a84c' }}
              >
                AI asistent
              </p>
              <p className="text-xs" style={{ color: '#9a8f7c' }}>
                {listingTitle ? listingTitle.slice(0, 40) : 'CMEP'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <PersonaPicker
                current={persona}
                onChange={(p) => {
                  setPersona(p);
                  personaStore.set(p);
                }}
              />
              <button
                type="button"
                onClick={startNewConversation}
                className="rounded-full px-2 py-1 text-xs"
                style={{ color: '#9a8f7c' }}
                aria-label="Nová konverzácia"
                title="Nová konverzácia"
              >
                ⟲
              </button>
              <button
                type="button"
                onClick={() => setMinimized((v) => !v)}
                aria-label="minimalizovat"
              >
                {minimized ? '+' : '–'}
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-full px-2 text-lg"
                style={{ color: '#9a8f7c' }}
                aria-label="Zavrieť"
              >
                ×
              </button>
            </div>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
            {!minimized && messages.map((m, i) => (
              <div
                key={i}
                className={`max-w-[85%] whitespace-pre-wrap break-words rounded-xl px-3 py-2 text-sm ${
                  m.role === 'user' ? 'ml-auto' : ''
                }`}
                style={
                  m.role === 'user'
                    ? { background: '#c9a84c', color: '#0b0b0b' }
                    : { background: '#17140d', color: '#f3e6c4' }
                }
              >
                {m.text}
              </div>
            ))}
            {(busy || transcribing) && (
              <div
                className="max-w-[85%] rounded-xl px-3 py-2 text-sm"
                style={{ background: '#17140d', color: '#9a8f7c' }}
              >
                {transcribing ? 'Prepisujem hlas…' : 'píšem…'}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {!minimized && (
          <div className="border-t p-3" style={{ borderColor: 'rgba(201,168,76,0.25)' }}>
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Napíš správu… (Enter = odoslať)"
                rows={1}
                disabled={busy || transcribing}
                className="flex-1 resize-none rounded-lg border p-2 text-sm"
                style={{
                  borderColor: 'rgba(201,168,76,0.25)',
                  background: '#0b0b0b',
                  color: '#f3e6c4',
                  maxHeight: '100px',
                }}
              />
              <button
                type="button"
                onClick={() => void toggleVoiceRecording()}
                disabled={busy || transcribing}
                aria-label={recording ? 'Zastaviť nahrávanie' : 'Nahrať hlasovú správu'}
                aria-pressed={recording}
                className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40"
                style={{ borderColor: recording ? '#ef4444' : 'rgba(201,168,76,0.35)', color: recording ? '#ef4444' : '#c9a84c' }}
              >
                {recording ? '■' : '🎙'}
              </button>
              <VoiceLiveButton
                onTranscript={(role, text) => {
                  setMessages((m) => [...m, { role: role === 'user' ? 'user' : 'ai', text }]);
                }}
                onError={(msg) => {
                  setMessages((m) => [...m, { role: 'ai', text: `Hlas: ${msg}` }]);
                }}
              />
              <button
                type="button"
                onClick={() => void send()}
                disabled={busy || !input.trim()}
                className="rounded-lg px-3 py-2 text-sm font-semibold disabled:opacity-40"
                style={{ background: '#c9a84c', color: '#0b0b0b' }}
              >
                ➤
              </button>
            </div>
          </div>
          )}
        </div>
      )}

      {toast && (
        <div
          role="status"
          className="fixed bottom-24 right-6 z-[60] max-w-xs rounded-lg px-4 py-2 text-sm shadow-2xl"
          style={{ background: '#17140d', color: '#f3e6c4', border: '1px solid rgba(201,168,76,0.35)' }}
        >
          {toast}
        </div>
      )}
    </>
  );
}
