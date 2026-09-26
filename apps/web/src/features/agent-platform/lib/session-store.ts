const KEY = 'cmep_ai_session_id';

function genId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export const aiSessionStore = {
  getSessionId(): string {
    if (typeof window === 'undefined') return '';
    const existing = localStorage.getItem(KEY);
    if (existing && existing.trim()) return existing;
    const fresh = genId();
    localStorage.setItem(KEY, fresh);
    return fresh;
  },

  resetSession(): string {
    if (typeof window === 'undefined') return '';
    const fresh = genId();
    localStorage.setItem(KEY, fresh);
    return fresh;
  },

  clearSession(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(KEY);
  },
};
