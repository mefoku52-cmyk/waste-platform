'use client';

import { config } from '@/lib/config';

const ANON_KEY = 'cmep_anonymous_id';
const UTM_KEY = 'cmep_utm';


// Meta Pixel helper — volá iba ak fbq existuje (init v layout.tsx)
function metaTrack(event: 'PageView' | 'ViewContent', data?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  const w = window as unknown as { fbq?: (...args: unknown[]) => void };
  if (typeof w.fbq !== 'function') return;
  try {
    if (data) w.fbq('track', event, data);
    else w.fbq('track', event);
  } catch {
    /* tiché zlyhanie — tracking nikdy nesmie rozbiť UI */
  }
}

export function getAnonymousId(): string {
  if (typeof window === 'undefined') return '';
  let id = localStorage.getItem(ANON_KEY);
  if (!id) {
    id =
      (typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = (Math.random() * 16) | 0;
            return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
          }));
    localStorage.setItem(ANON_KEY, id);
  }
  return id;
}

type FirstTouch = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  landing_page: string;
  referrer: string | null;
};

const UTM_FIELDS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'] as const;

export function captureFirstTouch(): FirstTouch {
  if (typeof window === 'undefined') {
    return { landing_page: '/', referrer: null };
  }
  const stored = sessionStorage.getItem(UTM_KEY);
  if (stored) {
    try {
      return JSON.parse(stored) as FirstTouch;
    } catch {
      /* fallthrough */
    }
  }
  const params = new URLSearchParams(window.location.search);
  const ft: FirstTouch = {
    landing_page: window.location.pathname + (window.location.search || ''),
    referrer: document.referrer || null,
  };
  for (const f of UTM_FIELDS) {
    const v = params.get(f);
    if (v) ft[f] = v;
  }
  sessionStorage.setItem(UTM_KEY, JSON.stringify(ft));
  return ft;
}

function getCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : undefined;
}

export type TrackExtras = {
  entity_type?: string;
  entity_id?: string;
  company_id?: string;
};

export async function track(event_type: string, extras: TrackExtras = {}): Promise<void> {
  if (typeof window === 'undefined') return;
  const ft = captureFirstTouch();
  const body: Record<string, unknown> = {
    event_type,
    entity_type: extras.entity_type || 'acquisition',
    anonymous_id: getAnonymousId(),
    landing_page: ft.landing_page,
    referrer: ft.referrer || undefined,
  };
  if (extras.entity_id) body.entity_id = extras.entity_id;
  if (extras.company_id) body.company_id = extras.company_id;
  for (const f of UTM_FIELDS) {
    if (ft[f]) body[f] = ft[f];
  }
  const fbp = getCookie('_fbp');
  const fbc = getCookie('_fbc');
  if (fbp) body.fbp = fbp;
  if (fbc) body.fbc = fbc;

  try {
    metaTrack(event_type === 'landing_view' ? 'ViewContent' : 'PageView');

    await fetch(`${config.apiBaseUrl}/analytics/acquisition/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      keepalive: true,
    });
  } catch {
    /* analytics must never break UI */
  }
}
