/**
 * Deepgram streaming STT (nova-3) — protokolová vrstva pre "Live" hlasové tlačidlo.
 *
 * Čisté funkcie bez prehliadača, aby sa správa výsledkov dala unit-testovať.
 * Audio ide do Deepgramu priamo z prehliadača, ale odpoveď a hlas idú cez
 * existujúci CMEP chat (`/agent-platform/chat` s `voice_response: true`).
 */

export const STT_WS_BASE = 'wss://api.deepgram.com/v1/listen';
export const STT_MODEL = 'nova-3';
export const STT_LANGUAGE = 'sk';

/** Sample rate, ktorý reálne posielame, musí sedieť s `sample_rate` v URL. */
export function buildSttUrl(sampleRate: number): string {
  const rate = Number.isFinite(sampleRate) && sampleRate > 0 ? Math.round(sampleRate) : 16000;
  const params = new URLSearchParams({
    model: STT_MODEL,
    language: STT_LANGUAGE,
    encoding: 'linear16',
    sample_rate: String(rate),
    channels: '1',
    interim_results: 'true',
    endpointing: '800',
    utterance_end_ms: '1200',
    vad_events: 'true',
    smart_format: 'true',
    punctuate: 'true',
  });
  return `${STT_WS_BASE}?${params.toString()}`;
}

export type SttEvent =
  | { kind: 'interim'; text: string }
  | { kind: 'final'; text: string; endsUtterance: boolean }
  | { kind: 'utterance_end' }
  | { kind: 'error'; message: string }
  | { kind: 'ignore' };

type RawMessage = {
  type?: string;
  is_final?: boolean;
  speech_final?: boolean;
  description?: string;
  message?: string;
  channel?: { alternatives?: Array<{ transcript?: string }> };
};

export function parseSttMessage(raw: string): SttEvent {
  let msg: RawMessage;
  try {
    msg = JSON.parse(raw) as RawMessage;
  } catch {
    return { kind: 'ignore' };
  }
  if (!msg || typeof msg !== 'object') return { kind: 'ignore' };

  if (msg.type === 'Results') {
    const text = (msg.channel?.alternatives?.[0]?.transcript ?? '').trim();
    if (msg.is_final === true) {
      // `speech_final` = Deepgram po endpointingu uzavrel výpoveď.
      return { kind: 'final', text, endsUtterance: msg.speech_final === true };
    }
    return { kind: 'interim', text };
  }
  if (msg.type === 'UtteranceEnd') return { kind: 'utterance_end' };
  if (msg.type === 'Error') {
    const message = (msg.description || msg.message || '').trim();
    return { kind: 'error', message: message || 'Prepis reči zlyhal.' };
  }
  // Welcome / Metadata / SpeechStarted / CloseStream a iné — nič robiť.
  return { kind: 'ignore' };
}

export type TrackerOutput =
  | { interim: string }
  | { final: string }
  | null;

export type UtteranceTracker = {
  /** Spracuj udalosť; vráti `final` práve raz na dokončenú výpoveď. */
  push: (event: SttEvent, now?: number) => TrackerOutput;
  /** Aktuálny text výpovede (finálne fragmenty + priebežný), pre UI. */
  interimText: () => string;
  reset: () => void;
};

function joinParts(parts: string[]): string {
  return parts
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
    .join(' ');
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim();
}

/**
 * Zbiera `is_final` fragmenty do pending bufferu a vydá celú výpoveď raz —
 * buď na `speech_final`, alebo na `UtteranceEnd` (niekedy príde oboje).
 * Dedupe okno chráni pred dvojitým odoslaním tej istej výpovede do chatu,
 * ale dovoľuje zopakovať tú istú vetu neskôr.
 */
export function createUtteranceTracker(dedupeWindowMs = 3000): UtteranceTracker {
  let pending: string[] = [];
  let interim = '';
  let lastSent = { text: '', at: 0 };

  const interimText = () => joinParts([...pending, interim]);

  const takeFinal = (now: number): TrackerOutput => {
    const text = joinParts(pending);
    pending = [];
    interim = '';
    if (!text) return { interim: '' };
    const key = normalize(text);
    if (lastSent.text === key && now - lastSent.at < dedupeWindowMs) {
      return { interim: '' };
    }
    lastSent = { text: key, at: now };
    return { final: text };
  };

  return {
    interimText,
    reset() {
      pending = [];
      interim = '';
    },
    push(event, now = Date.now()) {
      if (event.kind === 'interim') {
        interim = event.text;
        return { interim: interimText() };
      }
      if (event.kind === 'final') {
        if (event.text) pending.push(event.text);
        interim = '';
        return event.endsUtterance ? takeFinal(now) : { interim: interimText() };
      }
      if (event.kind === 'utterance_end') return takeFinal(now);
      return null;
    },
  };
}
