const KEY = 'cmep_ai_persona';

export type Persona = 'bystry' | 'drzy' | 'lenivy' | 'op';

const DEFAULT: Persona = 'bystry';
const ALLOWED: readonly Persona[] = ['bystry', 'drzy', 'lenivy', 'op'];

export const personaStore = {
  get(): Persona {
    if (typeof window === 'undefined') return DEFAULT;
    const raw = localStorage.getItem(KEY);
    if (raw && (ALLOWED as readonly string[]).includes(raw)) return raw as Persona;
    return DEFAULT;
  },
  set(p: Persona): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(KEY, p);
  },
};
